import threading
import time
import traceback
from collections import deque
import os
import uuid
from io import BytesIO

import cv2
import numpy as np
from PIL import Image

from 设置 import 缓存图片目录, 洪水填充缓存图片目录
from .图像处理后端 import 图像处理后端类


_flood_fill_stop_event = threading.Event()


class 洪水填充后端类:
    """
    专门负责洪水填充相关逻辑：
    - 基于已有的缓存图片（与图像处理模块复用 imageId）
    - 提供一次性洪水填充结果给前端预览
    - 提供在新窗口中播放洪水填充动画的能力
    """

    def __init__(self, 通信管理器, 图像处理后端实例: 图像处理后端类):
        self._通信管理器 = 通信管理器
        # 复用图像处理后端实例中的加载方法
        self._图像处理后端 = 图像处理后端实例

    # ========== 基础工具 ==========

    def _ensure_dir(self, dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
        except Exception:
            pass

    def _cv2_to_dataurl(self, img):
        return self._图像处理后端._cv2_to_dataurl(img)

    def _load_image_by_id(self, image_id, image_source="flood"):
        if not image_id:
            raise ValueError("缺少 image_id")

        if image_source == "processing":
            # 保持兼容：当输入来自图像处理模块时，仍然去图像处理缓存目录取
            return self._图像处理后端._load_image_by_id(image_id)

        # 默认从洪水填充专用缓存目录加载
        self._ensure_dir(洪水填充缓存图片目录)
        file_path = os.path.join(洪水填充缓存图片目录, f"{image_id}.png")
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"洪水填充图片缓存不存在: image_id={image_id} path={file_path}"
            )

        try:
            pil_img = Image.open(file_path).convert("RGB")
            img_rgb = np.array(pil_img)
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        except Exception as e:
            raise ValueError(f"洪水填充缓存图片读取失败: {e}")

        return img_bgr

    def _save_image_bytes(self, img_bytes):
        self._ensure_dir(洪水填充缓存图片目录)
        image_id = uuid.uuid4().hex
        file_path = os.path.join(洪水填充缓存图片目录, f"{image_id}.png")
        try:
            pil_img = Image.open(BytesIO(img_bytes)).convert("RGB")
            pil_img.save(file_path, format="PNG")
        except Exception as e:
            raise ValueError(f"洪水填充图片解码失败: {e}")
        return image_id

    # ========== 洪水填充核心算法（一步到位结果） ==========

    def _flood_fill(self, img, seed_point, fill_color=(255, 255, 255)):
        """
        简化版洪水填充：直接返回最终结果，不做中途回调。
        img: BGR 图
        seed_point: (x, y)
        """
        if img is None:
            return None

        h, w = img.shape[:2]
        x, y = seed_point

        if not (0 <= x < w and 0 <= y < h):
            return None

        result = img.copy()
        seed_color = img[y, x].copy()
        fill_color_arr = np.array(fill_color, dtype=np.uint8)

        if np.array_equal(seed_color, fill_color_arr):
            return result

        queue = deque([(x, y)])
        visited = np.zeros((h, w), dtype=bool)
        visited[y, x] = True
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while queue:
            px, py = queue.popleft()
            if np.array_equal(result[py, px], seed_color):
                result[py, px] = fill_color_arr

                for dx, dy in directions:
                    nx, ny = px + dx, py + dy
                    if 0 <= nx < w and 0 <= ny < h and not visited[ny, nx]:
                        if np.array_equal(result[ny, nx], seed_color):
                            visited[ny, nx] = True
                            queue.append((nx, ny))
        return result

    # ========== 对前端暴露的方法 ==========

    def 处理上传图片(self, 数据):
        """
        洪水填充 tab 上传图片时调用（独立缓存）：
        - 类型：洪水填充上传缓存
        - 参数：{ 图片路径: str }
        - 返回事件：flood-image-uploaded { imageId, preview }
        """
        try:
            payload = 数据 or {}
            图片路径 = payload.get("图片路径")
            if not 图片路径 or not isinstance(图片路径, str):
                raise ValueError("未收到有效的图片路径")
            if not os.path.exists(图片路径):
                raise FileNotFoundError(f"图片路径不存在: {图片路径}")

            try:
                pil_img = Image.open(图片路径).convert("RGB")
            except Exception as e:
                raise ValueError(f"从路径读取图片失败: {e}")

            buf = BytesIO()
            pil_img.save(buf, format="PNG")
            image_id = self._save_image_bytes(buf.getvalue())

            img_rgb = np.array(pil_img)
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            preview_dataurl = self._cv2_to_dataurl(img_bgr)

            self._通信管理器.发送到Electron(
                "flood-image-uploaded",
                {"imageId": image_id, "preview": preview_dataurl},
            )
        except Exception as e:
            print(f"处理洪水填充上传图片异常: {e}")
            traceback.print_exc()

    def 处理洪水填充(self, 数据):
        """
        前端请求一次性洪水填充结果：
        - 类型：洪水填充
        - 参数：{ imageId, x, y }
        - 返回事件：flood-fill-result { image: dataUrl }
        """
        try:
            payload = 数据 or {}
            image_id = payload.get("imageId")
            image_source = payload.get("imageSource") or payload.get("image_source") or "flood"
            x = payload.get("x")
            y = payload.get("y")

            if image_id is None:
                raise ValueError("洪水填充缺少 imageId")
            if x is None or y is None:
                raise ValueError("洪水填充缺少起始点坐标")

            img = self._load_image_by_id(image_id, image_source=image_source)
            print("11111")
            result = self._flood_fill(img, (int(x), int(y)))
            if result is None:
                raise ValueError("洪水填充失败")

            dataurl = self._cv2_to_dataurl(result)
            self._通信管理器.发送到Electron(
                "flood-fill-result",
                {"image": dataurl},
            )
        except Exception as e:
            print(f"处理洪水填充异常: {e}")
            traceback.print_exc()
            try:
                self._通信管理器.发送到Electron(
                    "flood-fill-error",
                    {"message": str(e)},
                )
            except Exception:
                pass

    def 处理洪水填充动画(self, 数据):
        """
        在一个 OpenCV 窗口中播放洪水填充动画：
        - 类型：洪水填充动画
        - 参数：{ imageId, x, y }
        - 行为：在新窗口中显示填充过程，用于调试闭合情况
        """
        global _flood_fill_stop_event
        try:
            payload = 数据 or {}
            image_id = payload.get("imageId")
            image_source = payload.get("imageSource") or payload.get("image_source") or "flood"
            x = int(payload.get("x", 0))
            y = int(payload.get("y", 0))

            if image_id is None:
                raise ValueError("洪水填充动画缺少 imageId")

            base_img = self._load_image_by_id(image_id, image_source=image_source)
            if base_img is None:
                print("洪水填充动画：无法加载基础图像")
                return

            if len(base_img.shape) == 2:
                base_img = cv2.cvtColor(base_img, cv2.COLOR_GRAY2BGR)

            # 停止之前的动画
            _flood_fill_stop_event.set()
            time.sleep(0.1)
            _flood_fill_stop_event.clear()

            def run_animation():
                try:
                    h, w = base_img.shape[:2]
                    if not (0 <= x < w and 0 <= y < h):
                        print("起始点超出图像范围")
                        return

                    result = base_img.copy()
                    seed_color = base_img[y, x].copy()
                    fill_color = np.array([255, 255, 255], dtype=np.uint8)

                    if np.array_equal(seed_color, fill_color):
                        print("起始点颜色与填充颜色相同")
                        return

                    queue = deque([(x, y)])
                    visited = np.zeros((h, w), dtype=bool)
                    visited[y, x] = True
                    filled_count = 0
                    batch_size = 100
                    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

                    window_name = "洪水填充动画"
                    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                    max_size = 800
                    scale = min(max_size / w, max_size / h, 1.0)
                    win_w, win_h = int(w * scale), int(h * scale)
                    cv2.resizeWindow(window_name, win_w, win_h)

                    def is_window_closed():
                        try:
                            return cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1
                        except Exception:
                            return True

                    while queue:
                        if _flood_fill_stop_event.is_set() or is_window_closed():
                            print("洪水填充动画已中断")
                            _flood_fill_stop_event.set()
                            break

                        px, py = queue.popleft()

                        if np.array_equal(result[py, px], seed_color):
                            result[py, px] = fill_color
                            filled_count += 1

                            for dx, dy in directions:
                                nx, ny = px + dx, py + dy
                                if 0 <= nx < w and 0 <= ny < h and not visited[ny, nx]:
                                    if np.array_equal(result[ny, nx], seed_color):
                                        visited[ny, nx] = True
                                        queue.append((nx, ny))

                            if filled_count % batch_size == 0:
                                cv2.imshow(window_name, result)
                                key = cv2.waitKey(1)
                                if key == 27 or key == ord("q") or is_window_closed():
                                    _flood_fill_stop_event.set()
                                    break

                    if not _flood_fill_stop_event.is_set() and not is_window_closed():
                        cv2.imshow(window_name, result)
                        print(f"洪水填充动画完成，共填充 {filled_count} 个像素")
                        print("按任意键关闭窗口...")
                        while True:
                            key = cv2.waitKey(100)
                            if key != -1 or is_window_closed():
                                break

                    try:
                        cv2.destroyWindow(window_name)
                    except Exception:
                        pass
                except Exception as e:
                    traceback.print_exc()
                    try:
                        cv2.destroyAllWindows()
                    except Exception:
                        pass

            t = threading.Thread(target=run_animation, daemon=True)
            t.start()
        except Exception as e:
            print(f"处理洪水填充动画异常: {e}")
            traceback.print_exc()

