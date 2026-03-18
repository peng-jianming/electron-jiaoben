import base64
import json
import os
import uuid
from io import BytesIO

import cv2
import numpy as np
from PIL import Image
from 设置 import 缓存图片目录, 图像处理参数配置路径
from core.ADB控制器 import ADB控制器类


def _get_morph_kernel(kernel_size, kernel_shape):
    """根据参数获取形态学核"""
    shape_map = {
        "rect": cv2.MORPH_RECT,
        "cross": cv2.MORPH_CROSS,
        "ellipse": cv2.MORPH_ELLIPSE,
    }
    cv_shape = shape_map.get(kernel_shape, cv2.MORPH_RECT)
    return cv2.getStructuringElement(cv_shape, (kernel_size, kernel_size))


def 对图像应用膨胀(img, kernel_size=3, iterations=1, kernel_shape="rect"):
    """对图像应用膨胀操作"""
    if img is None:
        return None
    kernel = _get_morph_kernel(kernel_size, kernel_shape)
    return cv2.dilate(img, kernel, iterations=iterations)


def 对图像应用腐蚀(img, kernel_size=3, iterations=1, kernel_shape="rect"):
    """对图像应用腐蚀操作"""
    if img is None:
        return None
    kernel = _get_morph_kernel(kernel_size, kernel_shape)
    return cv2.erode(img, kernel, iterations=iterations)


def 应用颜色过滤(img, rows):
    """
    根据 rows 进行颜色过滤，返回新的图像
    rows: [ { baseColor: '#RRGGBB', offset: 'RRGGBB' } ]
    """
    if img is None:
        return None

    # 没有配置任何颜色时，直接返回原图
    if not rows:
        return img

    # 确保是 BGR 三通道
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    h, w = img.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)

    for row in rows:
        if not isinstance(row, dict):
            continue
        base_color = row.get("baseColor") or ""
        offset = row.get("offset") or ""

        # baseColor 形如 '#RRGGBB'，去掉 '#'
        if isinstance(base_color, str):
            base_color = base_color.lstrip("#")
        if not (isinstance(base_color, str) and len(base_color) == 6):
            continue

        # offset 形如 'RRGGBB'（其实三个通道相同），长度不对则视为 0 偏移
        if not (isinstance(offset, str) and len(offset) == 6):
            offset = "000000"

        base_bgr = tuple(int(base_color[i : i + 2], 16) for i in (4, 2, 0))
        tol_bgr = tuple(int(offset[i : i + 2], 16) for i in (4, 2, 0))

        lower = np.array(
            [max(0, base_bgr[i] - tol_bgr[i]) for i in range(3)],
            dtype=np.uint8,
        )
        upper = np.array(
            [min(255, base_bgr[i] + tol_bgr[i]) for i in range(3)],
            dtype=np.uint8,
        )

        color_mask = cv2.inRange(img, lower, upper)
        mask = cv2.bitwise_or(mask, color_mask)

    # 只保留落在任意颜色范围内的像素
    return cv2.bitwise_and(img, img, mask=mask)


class 图像处理后端类:
    """
    图像处理 tab 专用后端：
    - 接收前端上传的图片并缓存到本地，生成 image_id
    - 根据 image_id + 步骤列表进行 OpenCV 流水线处理
    """

    def __init__(self, 通信管理器):
        self._通信管理器 = 通信管理器
        # 当前已选中的 ADB 设备 ID
        self._当前设备ID = None
        # 复用的 ADB 控制器实例
        self._adb控制器 = None
        # 后端实例化后，尝试将上一次保存的流水线参数回显给前端
        try:
            self._回显已保存的流水线参数()
        except Exception as e:
            # 回显失败不影响后续正常流程
            print(f"回显流水线参数失败: {e}")

    # ========== ADB 相关内部工具 ==========

    def _获取_adb控制器(self, 设备ID=None):
        """
        获取（或创建）一个指定设备 ID 的 ADB 控制器
        """
        if 设备ID is None:
            设备ID = self._当前设备ID
        if not 设备ID:
            return None

        # 如果已有且设备 ID 一致，直接复用
        if self._adb控制器 and getattr(self._adb控制器, "设备ID", None) == 设备ID:
            return self._adb控制器

        self._adb控制器 = ADB控制器类(设备ID=设备ID)
        return self._adb控制器

    def _dataurl_to_bytes(self, data_url):
        if not isinstance(data_url, str) or "," not in data_url:
            raise ValueError("无效的图片数据")
        _, b64 = data_url.split(",", 1)
        return base64.b64decode(b64)

    def _cv2_to_dataurl(self, img):
        success, buf = cv2.imencode(".png", img)
        if not success:
            raise ValueError("图片编码失败")
        b64 = base64.b64encode(buf.tobytes()).decode("ascii")
        return "data:image/png;base64," + b64

    def _load_image_by_id(self, image_id):
        if not image_id:
            raise ValueError("缺少 image_id")
        file_path = os.path.join(缓存图片目录, f"{image_id}.png")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"图片缓存不存在: image_id={image_id} path={file_path}")

        try:
            # 使用 PIL 从磁盘读取，再转为 OpenCV 使用的 BGR 格式 ndarray
            pil_img = Image.open(file_path).convert("RGB")
            img_rgb = np.array(pil_img)
            # OpenCV 默认使用 BGR 排列
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        except Exception as e:
            raise ValueError(f"缓存图片读取失败: {e}")

        return img_bgr

    def _save_image_bytes(self, img_bytes):
        image_id = uuid.uuid4().hex
        file_path = os.path.join(缓存图片目录, f"{image_id}.png")

        try:
            # 使用 PIL 从字节流解码并保存，避免 cv2.imwrite 在部分环境下保存失败
            pil_img = Image.open(BytesIO(img_bytes))
            # 统一转为 RGB，再以 PNG 格式写入磁盘
            pil_img = pil_img.convert("RGB")
            pil_img.save(file_path, format="PNG")
        except Exception as e:
            raise ValueError(f"图片解码失败: {e}")

        return image_id

    # ========== 对外接口 ==========

    def 处理上传图片(self, 数据):
        """
        前端上传图片时调用：
        - 参数：{ 图片路径: str }
        - 返回事件：image-uploaded { imageId, preview }
        """
        try:
            payload = 数据 or {}
            图片路径 = payload.get("图片路径")
            if not 图片路径 or not isinstance(图片路径, str):
                raise ValueError("未收到有效的图片路径")
            if not os.path.exists(图片路径):
                raise FileNotFoundError(f"图片路径不存在: {图片路径}")

            # 从本地路径读取图片并缓存为统一格式
            try:
                pil_img = Image.open(图片路径).convert("RGB")
            except Exception as e:
                raise ValueError(f"从路径读取图片失败: {e}")

            # 生成缓存文件
            buf = BytesIO()
            pil_img.save(buf, format="PNG")
            image_id = self._save_image_bytes(buf.getvalue())

            # 预览图依旧以 dataUrl 形式返回给前端（尺寸较小，可接受）
            img_rgb = np.array(pil_img)
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            preview_dataurl = self._cv2_to_dataurl(img_bgr)

            self._通信管理器.发送到Electron(
                "image-uploaded", {"imageId": image_id, "preview": preview_dataurl}
            )
        except Exception as e:
            print(f"处理上传图片异常: {e}")

    def 处理获取ADB设备列表(self, 数据):
        """
        前端请求 ADB 设备列表：
        - 类型：获取ADB设备列表
        - 返回事件：adb-devices { devices: [deviceId, ...] }
        """
        try:
            控制器 = ADB控制器类()
            设备列表 = 控制器.获取设备列表() or []
            self._通信管理器.发送到Electron(
                "adb-devices",
                {"devices": 设备列表},
            )
        except Exception as e:
            print(f"获取 ADB 设备列表异常: {e}")
            self._通信管理器.发送到Electron(
                "adb-devices",
                {"devices": [], "error": str(e)},
            )

    def 处理连接ADB设备(self, 数据):
        """
        前端在设备列表中选择一个设备并点击连接：
        - 类型：连接ADB设备
        - 参数：{ 设备ID: str }
        - 返回事件：adb-device-connected { success, deviceId, message? }
        """
        try:
            payload = 数据 or {}
            设备ID = payload.get("设备ID") or payload.get("deviceId")
            if not 设备ID:
                raise ValueError("缺少设备ID")

            self._当前设备ID = 设备ID
            控制器 = self._获取_adb控制器(设备ID)
            if 控制器 is None:
                raise ValueError("创建 ADB 控制器失败")

            已连接 = 控制器.检查连接()
            if not 已连接:
                raise RuntimeError("设备未处于可用状态，请检查 ADB 连接")

            self._通信管理器.发送到Electron(
                "adb-device-connected",
                {"success": True, "deviceId": 设备ID},
            )
        except Exception as e:
            print(f"连接 ADB 设备异常: {e}")
            self._通信管理器.发送到Electron(
                "adb-device-connected",
                {"success": False, "deviceId": None, "message": str(e)},
            )

    def 处理ADB截图(self, 数据):
        """
        前端点击“截图”按钮：
        - 类型：ADB截图
        - 参数：{ 设备ID?: str }，若不传则使用当前已连接设备
        - 行为：调用 ADB 截图，直接缓存成 imageId，并复用原有 image-uploaded 事件
        """
        try:
            payload = 数据 or {}
            设备ID = payload.get("设备ID") or self._当前设备ID
            if not 设备ID:
                raise ValueError("尚未选择 ADB 设备")

            控制器 = self._获取_adb控制器(设备ID)
            if 控制器 is None:
                raise ValueError("创建 ADB 控制器失败")

            png_bytes = 控制器.截图到内存()
            if not png_bytes:
                raise RuntimeError("ADB 截图失败")

            # 先缓存到本地并生成 image_id
            image_id = self._save_image_bytes(png_bytes)

            # 生成预览 dataUrl，复用现有前端逻辑
            pil_img = Image.open(BytesIO(png_bytes)).convert("RGB")
            img_rgb = np.array(pil_img)
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            preview_dataurl = self._cv2_to_dataurl(img_bgr)

            self._通信管理器.发送到Electron(
                "image-uploaded", {"imageId": image_id, "preview": preview_dataurl}
            )
        except Exception as e:
            print(f"ADB 截图异常: {e}")

    def 处理图像处理流水线(self, 数据):
        """
        前端点击“处理”时调用：
        - 参数：{ imageId, 步骤: [ { type, params } ] }，可选 图片 作为兜底
        - 返回事件：image-processing-result { image: dataUrl }
        """
        try:
            payload = 数据 or {}
            image_id = payload.get("imageId")
            步骤列表 = payload.get("步骤") or []

            img = self._load_image_by_id(image_id)

            for step in 步骤列表:
                if not isinstance(step, dict):
                    continue
                step_type = step.get("type")
                params = step.get("params") or {}

                if step_type == "二值化":
                    threshold = params.get("threshold", 127)
                    try:
                        threshold = int(threshold)
                    except Exception:
                        threshold = 127
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    _, img = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
                elif step_type == "颜色过滤":
                    list = params.get("list") or []
                    img = 应用颜色过滤(img, list)
                elif step_type in ("膨胀", "腐蚀"):
                    kernel_size = params.get("kernelSize", 3)
                    iterations = params.get("iterations", 1)
                    kernel_shape = params.get("kernelShape", "rect")

                    try:
                        kernel_size = int(kernel_size)
                    except Exception:
                        kernel_size = 3
                    try:
                        iterations = int(iterations)
                    except Exception:
                        iterations = 1

                    if kernel_size < 1:
                        kernel_size = 1
                    if kernel_size % 2 == 0:
                        kernel_size += 1
                    if iterations < 1:
                        iterations = 1

                    if step_type == "膨胀":
                        img = 对图像应用膨胀(
                            img,
                            kernel_size=kernel_size,
                            iterations=iterations,
                            kernel_shape=kernel_shape,
                        )
                    else:
                        img = 对图像应用腐蚀(
                            img,
                            kernel_size=kernel_size,
                            iterations=iterations,
                            kernel_shape=kernel_shape,
                        )
                else:
                    raise ValueError(f"未知步骤类型: {step_type}")

            result_dataurl = self._cv2_to_dataurl(img)

            # 成功得到结果后，保存当前流水线参数到 JSON 文件
            try:
                self._保存流水线参数到文件(步骤列表)
            except Exception as e:
                # 仅记录错误，不中断正常结果返回
                print(f"保存流水线参数失败: {e}")

            self._通信管理器.发送到Electron(
                "image-processing-result", {"image": result_dataurl}
            )
        except Exception as e:
            print(f"图像处理流水线异常: {e}")

    def _保存流水线参数到文件(self, 步骤列表):
        """
        将当前流水线参数保存到 <仓库根>/data/lineParams.json 中
        """
        if not isinstance(步骤列表, list):
            步骤列表 = []

        data = {"steps": 步骤列表}
        with open(图像处理参数配置路径, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _回显已保存的流水线参数(self):
        """
        后端启动时，将已经保存的流水线参数通过 socket 推送给前端，用于页面初始化时回显。
        """
        if not os.path.exists(图像处理参数配置路径):
            return

        with open(图像处理参数配置路径, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                return

        steps = data.get("steps") or []
        if not isinstance(steps, list):
            return

        # 直接将原始 steps 列表发给前端，由前端自己处理 id 等前端字段
        self._通信管理器.发送到Electron(
            "image-processing-pipeline-params",
            {"steps": steps},
        )

    def 处理颜色过滤(self, 数据):
        """
        前端颜色过滤模块调用：
        - 参数：{ imageId: str, rows: [ { baseColor: '#RRGGBB', offset: 'RRGGBB' } ] }
        - 行为：根据颜色列表生成掩码，只保留在指定颜色±偏色范围内的像素
        - 当前用途：给颜色过滤组件调试用，不影响主预览
        """
        try:
            payload = 数据 or {}
            image_id = payload.get("imageId")
            rows = payload.get("rows") or []

            if not image_id:
                raise ValueError("处理颜色过滤时缺少 imageId")

            # 从缓存中加载原始图片并应用颜色过滤
            img = self._load_image_by_id(image_id)
            result_img = 应用颜色过滤(img, rows)

            result_dataurl = self._cv2_to_dataurl(result_img)
            self._通信管理器.发送到Electron(
                "color-filter-preview", {"image": result_dataurl}
            )
        except Exception as e:
            print(f"处理颜色过滤异常: {e}")
