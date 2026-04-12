import os
import time
import base64
import traceback
import tempfile
import socket
import subprocess

import cv2
import numpy as np
from matchImg import opencv模板匹配, opencv彩图模板匹配, opencv字库找图


def _构造事件结果(event: str, message: dict):
    """统一的返回结构，供主程序转发到前端。"""
    return {"prop": event, "message": message}


def _发送图片库结果(items=None, error=None):
    """图片库相关操作的通用结果结构。"""
    return _构造事件结果(
        "image-library",
        {
            "success": error is None,
            "items": items or [],
            **({"error": error} if error else {}),
        },
    )


def 加载图片库(data):
    """
    加载 .npz 图片库文件，将其中的图片转为 base64 返回。
    返回: {"event": "image-library", "message": {...}}
    """
    try:
        npz_path = data.get("npzPath") or data.get("path")
        if not npz_path:
            return _发送图片库结果(error="未提供图片库文件路径")

        if not os.path.isfile(npz_path):
            return _发送图片库结果(error=f"图片库文件不存在: {npz_path}")

        try:
            archive = np.load(npz_path, allow_pickle=True)
        except Exception as e:
            return _发送图片库结果(error=f"加载图片库失败: {e}")

        items = []
        for name in archive.files:
            try:
                arr = archive[name]
                if arr is None:
                    continue

                img = np.array(arr)

                # 只接受二维或三维图像
                if img.ndim == 2:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                elif img.ndim == 3:
                    if img.shape[2] == 1:
                        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                    elif img.shape[2] == 4:
                        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    elif img.shape[2] != 3:
                        # 不支持的通道数，跳过
                        continue
                else:
                    continue

                # 归一化到 uint8
                if img.dtype != np.uint8:
                    img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
                    img = img.astype(np.uint8)

                h, w = img.shape[:2]
                success, buffer = cv2.imencode(
                    ".png", img, [cv2.IMWRITE_PNG_COMPRESSION, 1]
                )
                if not success:
                    continue

                items.append(
                    {
                        "name": str(name),
                        "width": int(w),
                        "height": int(h),
                        "channels": int(img.shape[2]) if img.ndim == 3 else 1,
                        "image": base64.b64encode(buffer).decode("utf-8"),
                    }
                )
            except Exception as e:
                print(f"处理图片库条目失败: {name}, 错误: {e}")
                continue

        if not items:
            return _发送图片库结果(items=[], error="图片库中没有有效的图片数据")
        else:
            return _发送图片库结果(items=items)

    except Exception as e:
        traceback.print_exc()
        return _发送图片库结果(error=str(e))


def 保存图片库(data):
    """
    根据前端表格数据重写 .npz 图片库文件。
    成功/失败仅通过 success + error 告知前端。
    """
    try:
        npz_path = data.get("npzPath") or data.get("path")
        items = data.get("items") or []

        if not npz_path:
            return _发送图片库结果(error="保存图片库失败: 未提供图片库文件路径")

        arrays = {}
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or f"image_{idx + 1}")
            image_b64 = item.get("image")
            if not image_b64:
                continue

            try:
                img_bytes = base64.b64decode(image_b64)
                img_arr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
            except Exception as e:
                print(f"保存图片库失败: 解码图片失败: {e}")
                continue

            if img is None:
                print("保存图片库失败: 无法解码图片")
                continue

            if img.ndim == 2:
                img_to_save = img
            elif img.ndim == 3:
                if img.shape[2] == 1:
                    img_to_save = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                elif img.shape[2] == 3:
                    img_to_save = img
                elif img.shape[2] == 4:
                    img_to_save = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                else:
                    print(f"保存图片库失败: 不支持的通道数: {img.shape[2]}")
                    continue
            else:
                print(f"保存图片库失败: 不支持的维度: {img.ndim}")
                continue

            if img_to_save.dtype != np.uint8:
                img_to_save = cv2.normalize(img_to_save, None, 0, 255, cv2.NORM_MINMAX)
                img_to_save = img_to_save.astype(np.uint8)

            arrays[name] = img_to_save

        try:
            np.savez_compressed(npz_path, **arrays)
            print(f"保存图片库成功: {npz_path}, 共 {len(arrays)} 张图片")
            # 返回一个简单成功标记即可
            return _构造事件结果(
                "image-library-saved",
                {"success": True, "path": npz_path, "count": len(arrays)},
            )
        except Exception as e:
            print(f"保存图片库失败: 写入 npz 失败: {e}")
            return _发送图片库结果(error=f"保存图片库失败: 写入 npz 失败: {e}")

    except Exception as e:
        traceback.print_exc()
        return _发送图片库结果(error=f"保存图片库出现异常: {e}")


def 保存图片到图片库(data):
    """
    将一张图片保存/追加到 .npz 图片库文件中。
    返回 image-library-saved 事件，前端可根据需要刷新。
    """
    try:
        npz_path = data.get("npzPath") or data.get("path")
        image_b64 = data.get("image")
        name = str(data.get("name") or f"image_{int(time.time())}")

        if not npz_path:
            return _发送图片库结果(error="保存图片到图片库失败: 未提供 npzPath")
        if not image_b64:
            return _发送图片库结果(error="保存图片到图片库失败: 未提供 image 数据")

        # 解码图片
        try:
            img_bytes = base64.b64decode(image_b64)
            img_arr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(img_arr, cv2.IMREAD_UNCHANGED)
        except Exception as e:
            return _发送图片库结果(error=f"保存图片到图片库失败: 解码图片失败: {e}")

        if img is None:
            return _发送图片库结果(error="保存图片到图片库失败: 无法解码图片")

        # 只接受二维或三维图像，其他情况尝试转换到三通道
        if img.ndim == 2:
            img_to_save = img
        elif img.ndim == 3:
            # 统一转换为 BGR 三通道存储
            if img.shape[2] == 1:
                img_to_save = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif img.shape[2] == 3:
                img_to_save = img
            elif img.shape[2] == 4:
                img_to_save = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            else:
                return _发送图片库结果(
                    error=f"保存图片到图片库失败: 不支持的通道数: {img.shape[2]}"
                )
        else:
            return _发送图片库结果(
                error=f"保存图片到图片库失败: 不支持的维度: {img.ndim}"
            )

        # 归一化到 uint8
        if img_to_save.dtype != np.uint8:
            img_to_save = cv2.normalize(img_to_save, None, 0, 255, cv2.NORM_MINMAX)
            img_to_save = img_to_save.astype(np.uint8)

        # 读取已有 npz 内容（如果存在）
        arrays = {}
        if os.path.isfile(npz_path):
            try:
                archive = np.load(npz_path, allow_pickle=True)
                for key in archive.files:
                    arrays[key] = archive[key]
            except Exception as e:
                print(f"保存图片到图片库: 加载现有图片库失败，将创建新的文件: {e}")

        # 同名键自动追加短后缀，支持同一配置项存多张图片
        original_name = name
        counter = 1
        while name in arrays:
            name = f"{original_name}_{counter}"
            counter += 1
        arrays[name] = img_to_save

        # 保存为压缩 npz
        try:
            np.savez_compressed(npz_path, **arrays)
            print(
                f"保存图片到图片库成功: {npz_path} -> {name} (shape={img_to_save.shape})"
            )
            return _构造事件结果(
                "image-library-saved",
                {"success": True, "path": npz_path, "name": name},
            )
        except Exception as e:
            return _发送图片库结果(error=f"保存图片到图片库失败: 写入 npz 失败: {e}")

    except Exception as e:
        traceback.print_exc()
        return _发送图片库结果(error=f"保存图片到图片库出现异常: {e}")


def 图片库模板匹配(data):
    """
    使用图片库中的模板进行 OpenCV 模板匹配。
    仅支持前端提供：
      - templateImages: 模板图片数组，元素为 {name, image}
      - largeImage:    大图 base64
      - matchMode:     可选，"gray"（默认，灰度相关匹配）或 "color"（BGR 三通道平方差匹配）
    返回事件: image-match-result
    """
    try:
        template_images = data.get("templateImages") or []
        large_b64 = data.get("largeImage")
        region = data.get("region") or None
        similarity_threshold = float(data.get("similarity", 0.8))
        match_mode = str(data.get("matchMode") or "gray").strip().lower()

        if not isinstance(template_images, list) or not template_images:
            return _构造事件结果(
                "image-match-result",
                {"success": False, "error": "缺少模板图片数据"},
            )

        # 解码大图：优先使用前端传入的 base64，否则自动截图

        large_img = None
        if large_b64:
            try:
                large_bytes = base64.b64decode(large_b64)
                large_arr = np.frombuffer(large_bytes, np.uint8)
                large_img = cv2.imdecode(large_arr, cv2.IMREAD_COLOR)
            except Exception as e:
                return _构造事件结果(
                    "image-match-result",
                    {"success": False, "error": f"解码大图失败: {e}"},
                )
        else:
            # 未传入大图，则尝试使用当前设备自动截图
            if not _current_device_id:
                return _构造事件结果(
                    "image-match-result",
                    {
                        "success": False,
                        "error": "未选择设备，请上传大图或连接设备后截图",
                    },
                )
            controller = ADBController(device_id=_current_device_id)
            img_bytes = controller.截图到内存()
            if not img_bytes:
                return _构造事件结果(
                    "image-match-result",
                    {"success": False, "error": "自动截图失败"},
                )
            try:
                large_arr = np.frombuffer(img_bytes, np.uint8)
                large_img = cv2.imdecode(large_arr, cv2.IMREAD_COLOR)
            except Exception as e:
                return _构造事件结果(
                    "image-match-result",
                    {"success": False, "error": f"解码截图失败: {e}"},
                )

        if large_img is None:
            return _构造事件结果(
                "image-match-result",
                {"success": False, "error": "无法获取大图"},
            )

        # 解析区域
        region_tuple = (0, 0, 0, 0)
        if region:
            region_tuple = (
                int(region.get("x", 0)),
                int(region.get("y", 0)),
                int(region.get("w", 0)),
                int(region.get("h", 0)),
            )

        # 逐个模板匹配：命中一个达到阈值即返回，不再继续
        match = None
        matched_template_name = ""
        best_similarity = -1.0
        for idx, item in enumerate(template_images):
            if not isinstance(item, dict):
                continue
            cur_name = str(item.get("name") or "")
            cur_b64 = item.get("image")
            if not cur_b64:
                continue
            try:
                tmpl_bytes = base64.b64decode(cur_b64)
                tmpl_arr = np.frombuffer(tmpl_bytes, np.uint8)
                template_img = cv2.imdecode(tmpl_arr, cv2.IMREAD_COLOR)
            except Exception as e:
                print(f"解码模板图片失败 idx={idx}, name={cur_name}, err={e}")
                continue
            if template_img is None:
                continue
            if match_mode == "color":
                cur_match = opencv彩图模板匹配(
                    large_img, template_img, region=region_tuple
                )
            else:
                cur_match = opencv模板匹配(
                    large_img, template_img, region=region_tuple
                )
            if not cur_match:
                continue
            cur_similarity = float(cur_match.get("similarity", 0))
            if cur_similarity > best_similarity:
                best_similarity = cur_similarity
            if cur_similarity >= similarity_threshold:
                match = cur_match
                matched_template_name = cur_name
                break

        if not match:
            if best_similarity >= 0:
                return _构造事件结果(
                    "image-match-result",
                    {
                        "success": False,
                        "error": f"未找到满足阈值的匹配，最高相似度: {best_similarity:.4f} < 阈值 {similarity_threshold:.4f}",
                    },
                )
            return _构造事件结果(
                "image-match-result",
                {"success": False, "error": "未找到匹配位置"},
            )

        # 绘制结果矩形
        x = int(match["x"])
        y = int(match["y"])
        w = int(match["w"])
        h = int(match["h"])

        result_image = large_img.copy()
        cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # 显示相似度文本
        sim_text = f"Sim: {match['similarity']:.4f}"
        text_x, text_y = x, max(y - 10, 20)
        (text_width, text_height), baseline = cv2.getTextSize(
            sim_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
        )
        cv2.rectangle(
            result_image,
            (text_x - 5, text_y - text_height - 5),
            (text_x + text_width + 5, text_y + baseline + 5),
            (0, 255, 0),
            -1,
        )
        cv2.putText(
            result_image,
            sim_text,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            2,
        )

        ok, buffer = cv2.imencode(".png", result_image)
        if not ok:
            return _构造事件结果(
                "image-match-result",
                {"success": False, "error": "编码结果图片失败"},
            )

        message = {
            "success": True,
            "result": match,
            "resultImage": base64.b64encode(buffer).decode("utf-8"),
            "matchedTemplateName": matched_template_name,
        }
        return _构造事件结果("image-match-result", message)

    except Exception as e:
        traceback.print_exc()
        return _构造事件结果(
            "image-match-result",
            {"success": False, "error": str(e)},
        )


def 字库匹配(data):
    """
    字库匹配处理函数（精简版）。
    仅支持前端提供：
      - fontLibraryInfoArray: 字库信息数组
      - largeImage:           大图 base64
    返回事件: font-library-match-result
    """
    try:
        font_library_info_array = data.get("fontLibraryInfoArray")
        large_image_base64 = data.get("largeImage")
        region = data.get("region")
        similarity = float(data.get("similarity", 0.8))

        if (
            not font_library_info_array
            or not isinstance(font_library_info_array, list)
            or len(font_library_info_array) == 0
        ):
            return _构造事件结果(
                "font-library-match-result",
                {"success": False, "error": "缺少字库信息数组"},
            )

        # 处理大图：如果没有提供，则自动从当前设备截图
        large_image_path = None
        large_image_bytes = None
        if not large_image_base64:
            if not _current_device_id:
                return _构造事件结果(
                    "font-library-match-result",
                    {"success": False, "error": "未选择设备，无法自动截图"},
                )
            print(f"未提供大图，自动截图设备: {_current_device_id}")
            controller = ADBController(device_id=_current_device_id)
            large_image_bytes = controller.截图到内存()
            if not large_image_bytes:
                return _构造事件结果(
                    "font-library-match-result",
                    {"success": False, "error": "自动截图失败"},
                )
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as large_file:
                large_file.write(large_image_bytes)
                large_image_path = large_file.name
            print(f"截图已保存到临时文件: {large_image_path}")
        else:
            # 将 base64 转换为临时文件
            large_image_bytes = base64.b64decode(large_image_base64)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as large_file:
                large_file.write(large_image_bytes)
                large_image_path = large_file.name

        try:
            region_tuple = (0, 0, 0, 0)
            if region:
                region_tuple = (
                    int(region.get("x", 0)),
                    int(region.get("y", 0)),
                    int(region.get("w", 0)),
                    int(region.get("h", 0)),
                )

            print(
                f"字库匹配 - 开始查找，相似度阈值: {similarity}, 字库数量: {len(font_library_info_array)}"
            )
            result = opencv字库找图(
                large_image_path=large_image_path,
                font_library_info_array=font_library_info_array,
                region=region_tuple,
                similarity=similarity,
            )
            print(f"字库匹配 - 查找结果: {result}")

            if result is None:
                return _构造事件结果(
                    "font-library-match-result",
                    {"success": False, "error": "未找到匹配位置"},
                )

            # 读取大图用于绘制结果：优先使用内存中的 bytes，避免路径编码问题
            large_image = None
            if large_image_bytes:
                try:
                    arr = np.frombuffer(large_image_bytes, np.uint8)
                    large_image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                except Exception as e:
                    print(f"解码大图失败: {e}")

            if large_image is None:
                # 退回到从磁盘读取（理论上应该很少用到）
                large_image = cv2.imread(large_image_path)
                if large_image is None:
                    return _构造事件结果(
                        "font-library-match-result",
                        {"success": False, "error": "无法读取大图"},
                    )

            # 在结果图片上绘制匹配位置
            result_image = large_image.copy()

            x = int(result["x"])
            y = int(result["y"])
            w = int(result["w"])
            h = int(result["h"])
            cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

            similarity_text = f"Similarity: {result['similarity']:.4f}"
            text_x = x
            text_y = max(y - 10, 20)
            (text_width, text_height), baseline = cv2.getTextSize(
                similarity_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
            )
            cv2.rectangle(
                result_image,
                (text_x - 5, text_y - text_height - 5),
                (text_x + text_width + 5, text_y + baseline + 5),
                (0, 255, 0),
                -1,
            )
            cv2.putText(
                result_image,
                similarity_text,
                (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),
                2,
            )

            ok, buffer = cv2.imencode(".png", result_image)
            if not ok:
                return _构造事件结果(
                    "font-library-match-result",
                    {"success": False, "error": "编码结果图片失败"},
                )

            message = {
                "success": True,
                "result": result,
                "resultImage": base64.b64encode(buffer).decode("utf-8"),
            }
            return _构造事件结果("font-library-match-result", message)

        finally:
            try:
                os.unlink(large_image_path)
            except Exception:
                pass

    except Exception as e:
        traceback.print_exc()
        return _构造事件结果(
            "font-library-match-result",
            {"success": False, "error": str(e)},
        )


# ==================== 设备管理（迁移自旧入口） ====================

_current_device_id = None


def 获取设备列表(data):
    """
    获取当前已连接的 ADB 设备列表。
    返回事件: device-list
    """
    global _current_device_id
    try:
        adb_path = r"C:\platform-tools\adb.exe"
        result = subprocess.run(
            f'"{adb_path}" devices',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or "获取设备列表失败"
            print(error_msg)
            return _构造事件结果(
                "device-list",
                {
                    "success": False,
                    "devices": [],
                    "currentDeviceId": _current_device_id,
                    "error": error_msg,
                },
            )

        devices = []
        lines = result.stdout.strip().splitlines()
        # 第一行为 "List of devices attached"
        for line in lines[1:]:
            if "\t" in line:
                device_id, status = line.split("\t", 1)
                device_id = device_id.strip()
                if device_id:
                    devices.append(device_id)

        print(f"已检测到设备: {devices}")
        return _构造事件结果(
            "device-list",
            {
                "success": True,
                "devices": devices,
                "currentDeviceId": _current_device_id,
            },
        )
    except Exception as e:
        traceback.print_exc()
        return _构造事件结果(
            "device-list",
            {
                "success": False,
                "devices": [],
                "currentDeviceId": _current_device_id,
                "error": str(e),
            },
        )


def 设置当前设备(data):
    """
    设置当前使用的设备 ID。
    返回事件: device-selected
    """
    global _current_device_id
    try:
        device_id = data.get("deviceId") or data.get("device_id")
        if device_id:
            _current_device_id = str(device_id)
            print(f"当前连接设备已设置为: {_current_device_id}")
        else:
            _current_device_id = None
            print("当前连接设备已清空")

        return _构造事件结果(
            "device-selected",
            {
                "success": True,
                "currentDeviceId": _current_device_id,
            },
        )
    except Exception as e:
        traceback.print_exc()
        return _构造事件结果(
            "device-selected",
            {
                "success": False,
                "currentDeviceId": _current_device_id,
                "error": str(e),
            },
        )


class ADBController:
    """ADB 控制器类，封装截图功能（精简版）。"""

    def __init__(self, device_id=None):
        self.device_id = device_id
        self._adb_prefix = self._build_adb_prefix()
        self._adb_host = "127.0.0.1"
        self._adb_port = 5037

    def _build_adb_prefix(self):
        adb_path = r"C:\platform-tools\adb.exe"
        if self.device_id:
            return f'"{adb_path}" -s {self.device_id}'
        return f'"{adb_path}"'

    # ====================== ADB Socket 协议（与 index.py 同步） ======================
    def _adb_socket_connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((self._adb_host, self._adb_port))
        return sock

    def _adb_send(self, sock, cmd: str):
        payload = cmd.encode("utf-8")
        sock.sendall(f"{len(payload):04x}".encode("utf-8") + payload)

    def _adb_read_status(self, sock):
        status = sock.recv(4)
        if status == b"OKAY":
            return True, ""
        if status == b"FAIL":
            length = int(sock.recv(4), 16)
            return False, sock.recv(length).decode("utf-8", errors="replace")
        return False, f"未知状态: {status!r}"

    def _adb_recv_all(self, sock):
        chunks = []
        while True:
            try:
                data = sock.recv(65536)
                if not data:
                    break
                chunks.append(data)
            except socket.timeout:
                break
        return b"".join(chunks)

    def _raw字节转png(self, raw_bytes):
        """将 screencap raw RGBA 字节转为 PNG 字节"""
        if not raw_bytes or len(raw_bytes) <= 12:
            return None
        try:
            width, height, _ = np.frombuffer(raw_bytes[:12], dtype="<u4")
            expected_len = int(width) * int(height) * 4
            pixel_bytes = raw_bytes[12:12 + expected_len]
            if width <= 0 or height <= 0 or len(pixel_bytes) < expected_len:
                return None

            rgba = np.frombuffer(pixel_bytes, dtype=np.uint8).reshape((int(height), int(width), 4))
            bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
            ok, buffer = cv2.imencode(".png", bgr, [cv2.IMWRITE_PNG_COMPRESSION, 1])
            if ok:
                return buffer.tobytes()
            return None
        except Exception:
            return None

    def 截图到内存_socket(self):
        """通过 ADB socket 协议获取 raw RGBA 截图（12 字节头 + 像素数据）。"""
        sock = None
        try:
            sock = self._adb_socket_connect()

            if self.device_id:
                self._adb_send(sock, f"host:transport:{self.device_id}")
            else:
                self._adb_send(sock, "host:transport-any")
            ok, _ = self._adb_read_status(sock)
            if not ok:
                return None

            self._adb_send(sock, "exec:screencap")
            ok, _ = self._adb_read_status(sock)
            if not ok:
                return None

            data = self._adb_recv_all(sock)
            if data and len(data) > 12:
                return data
            return None
        except Exception:
            return None
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass

    def 截图到内存_快速原始(self):
        """使用 subprocess + raw screencap（无 -p）获取原始截图数据。"""
        try:
            adb_path = r"C:\platform-tools\adb.exe"
            cmd = [adb_path]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            cmd.extend(["exec-out", "screencap"])

            result = subprocess.run(
                cmd,
                shell=False,
                capture_output=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout and len(result.stdout) > 12:
                return result.stdout
            return None
        except Exception:
            return None

    def 截图到内存(self):
        """
        截图并直接返回 PNG 图像数据，失败返回 None。
        优先级: socket raw → subprocess raw → subprocess PNG
        """
        try:
            # 1) 最快: socket raw
            raw_bytes = self.截图到内存_socket()
            img_bytes = self._raw字节转png(raw_bytes)
            if img_bytes:
                print("1111111")
                return img_bytes

            # 2) 次快: subprocess raw
            raw_bytes = self.截图到内存_快速原始()
            img_bytes = self._raw字节转png(raw_bytes)
            if img_bytes:
                return img_bytes

            # 3) 最慢: subprocess PNG（兜底）
            result = subprocess.run(
                f"{self._adb_prefix} exec-out screencap -p",
                shell=True,
                capture_output=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout
            return None
        except Exception as e:
            print(f"截图失败: {e}")
            return None


def 截图当前设备(data):
    """
    对当前连接的设备执行截图。
    返回事件: device-screenshot
    """
    global _current_device_id
    try:
        source = data.get("source", "left-panel")

        if not _current_device_id:
            print("尚未选择当前设备，无法截图")
            return _构造事件结果(
                "device-screenshot",
                {
                    "success": False,
                    "currentDeviceId": _current_device_id,
                    "error": "未选择设备",
                    "source": source,
                },
            )

        controller = ADBController(device_id=_current_device_id)
        img_bytes = controller.截图到内存()
        if not img_bytes:
            return _构造事件结果(
                "device-screenshot",
                {
                    "success": False,
                    "currentDeviceId": _current_device_id,
                    "error": "截图失败",
                    "source": source,
                },
            )

        message = {
            "success": True,
            "currentDeviceId": _current_device_id,
            "image": base64.b64encode(img_bytes).decode("utf-8"),
            "source": source,
        }
        return _构造事件结果("device-screenshot", message)
    except Exception as e:
        traceback.print_exc()
        return _构造事件结果(
            "device-screenshot",
            {
                "success": False,
                "currentDeviceId": _current_device_id,
                "error": str(e),
                "source": data.get("source", "left-panel"),
            },
        )
