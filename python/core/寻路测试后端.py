import base64
import os
import traceback
import uuid
from io import BytesIO

import cv2
import numpy as np
from PIL import Image

from 设置 import 寻路测试缓存图片目录
from .图像处理后端 import 图像处理后端类


def _ensure_dir(dir_path):
    try:
        os.makedirs(dir_path, exist_ok=True)
    except Exception:
        pass


class 寻路测试后端类:
    def __init__(self, 通信管理器, 图像处理后端实例: 图像处理后端类):
        self._通信管理器 = 通信管理器
        self._图像处理后端 = 图像处理后端实例

        # 记录当前用于模板匹配的原始地图 imageId
        self._current_image_id = None

    def _cv2_to_dataurl(self, img):
        return self._图像处理后端._cv2_to_dataurl(img)

    def _save_image_bytes(self, img_bytes):
        _ensure_dir(寻路测试缓存图片目录)
        image_id = uuid.uuid4().hex
        file_path = os.path.join(寻路测试缓存图片目录, f"{image_id}.png")
        pil_img = Image.open(BytesIO(img_bytes)).convert("RGB")
        pil_img.save(file_path, format="PNG")
        return image_id

    def _load_image_by_id(self, image_id):
        if not image_id:
            raise ValueError("缺少 imageId")

        _ensure_dir(寻路测试缓存图片目录)
        file_path = os.path.join(寻路测试缓存图片目录, f"{image_id}.png")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"寻路测试缓存图片不存在: imageId={image_id} path={file_path}")

        pil_img = Image.open(file_path).convert("RGB")
        img_rgb = np.array(pil_img)
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        return img_bgr

    # ===== 对前端暴露：上传（原始地图）=====
    def 处理上传图片(self, 数据):
        """
        - 类型：寻路测试上传缓存
        - 参数：{ 图片路径, requestId? }
        - 返回事件：path-finding-test-image-uploaded { imageId, preview, requestId? }
        """
        try:
            payload = 数据 or {}
            图片路径 = payload.get("图片路径")
            request_id = payload.get("requestId")
            if not 图片路径 or not isinstance(图片路径, str):
                raise ValueError("未收到有效的图片路径")
            if not os.path.exists(图片路径):
                raise FileNotFoundError(f"图片路径不存在: {图片路径}")

            pil_img = Image.open(图片路径).convert("RGB")
            buf = BytesIO()
            pil_img.save(buf, format="PNG")
            image_id = self._save_image_bytes(buf.getvalue())

            img_rgb = np.array(pil_img)
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            preview_dataurl = self._cv2_to_dataurl(img_bgr)

            self._current_image_id = image_id

            self._通信管理器.发送到Electron(
                "path-finding-test-image-uploaded",
                {"imageId": image_id, "preview": preview_dataurl, "requestId": request_id},
            )
        except Exception as e:
            print(f"处理寻路测试上传图片异常: {e}")
            traceback.print_exc()

    def 处理上传base64图片(self, 数据):
        """
        - 类型：寻路测试上传base64缓存
        - 参数：{ dataUrl, requestId? }
        - 返回事件：path-finding-test-image-uploaded { imageId, preview, requestId? }
        """
        try:
            payload = 数据 or {}
            data_url = payload.get("dataUrl") or payload.get("data_url") or ""
            request_id = payload.get("requestId")
            if not data_url or not isinstance(data_url, str):
                raise ValueError("未收到有效的 dataUrl")

            if "," in data_url:
                _, b64 = data_url.split(",", 1)
            else:
                b64 = data_url

            img_bytes = base64.b64decode(b64, validate=False)
            image_id = self._save_image_bytes(img_bytes)

            img_bgr = self._load_image_by_id(image_id)
            preview_dataurl = self._cv2_to_dataurl(img_bgr)

            self._current_image_id = image_id

            self._通信管理器.发送到Electron(
                "path-finding-test-image-uploaded",
                {"imageId": image_id, "preview": preview_dataurl, "requestId": request_id},
            )
        except Exception as e:
            print(f"处理寻路测试上传base64图片异常: {e}")
            traceback.print_exc()

    # ===== 对前端暴露：小地图模板匹配 =====
    def 处理小地图匹配(self, 数据):
        """
        - 类型：图像处理小地图（被动触发）
        - 返回事件：path-finding-test-match-map-frame { image, score, topLeft, center, size }
        """
        try:
            if not self._current_image_id:
                return

            payload = 数据 or {}
            data_url = (
                payload.get("dataUrl")
                or payload.get("data_url")
                or payload.get("image")
                or ""
            )
            if not data_url or not isinstance(data_url, str):
                return

            # 解析 dataUrl 为 OpenCV BGR 图像
            try:
                if "," in data_url:
                    _, b64 = data_url.split(",", 1)
                else:
                    b64 = data_url
                img_bytes = base64.b64decode(b64, validate=False)
                pil_img = Image.open(BytesIO(img_bytes)).convert("RGB")
                mini_rgb = np.array(pil_img)
                mini_bgr = cv2.cvtColor(mini_rgb, cv2.COLOR_RGB2BGR)
            except Exception:
                return

            big_bgr = self._load_image_by_id(self._current_image_id)
            if big_bgr is None or mini_bgr is None:
                return

            big_h, big_w = big_bgr.shape[:2]
            mini_h, mini_w = mini_bgr.shape[:2]
            if big_h <= 0 or big_w <= 0 or mini_h <= 0 or mini_w <= 0:
                return
            if mini_h > big_h or mini_w > big_w:
                return

            big_gray = cv2.cvtColor(big_bgr, cv2.COLOR_BGR2GRAY)
            mini_gray = cv2.cvtColor(mini_bgr, cv2.COLOR_BGR2GRAY)

            res = cv2.matchTemplate(big_gray, mini_gray, cv2.TM_CCOEFF_NORMED)
            _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(res)

            # 相似度过低则忽略
            if max_val < 0.3:
                return

            top_left = max_loc
            bottom_right = (top_left[0] + mini_w, top_left[1] + mini_h)
            center = (top_left[0] + mini_w // 2, top_left[1] + mini_h // 2)

            vis = big_bgr.copy()
            cv2.rectangle(vis, top_left, bottom_right, (0, 0, 255), 2)
            cv2.circle(vis, center, 4, (0, 255, 255), -1)

            dataurl = self._cv2_to_dataurl(vis)
            self._通信管理器.发送到Electron(
                "path-finding-test-match-map-frame",
                {
                    "image": dataurl,
                    "score": float(max_val),
                    "topLeft": [int(top_left[0]), int(top_left[1])],
                    "center": [int(center[0]), int(center[1])],
                    "size": [int(mini_w), int(mini_h)],
                },
            )
        except Exception as e:
            print(f"寻路测试小地图模板匹配异常: {e}")
            traceback.print_exc()
            try:
                self._通信管理器.发送到Electron("path-finding-test-error", {"message": str(e)})
            except Exception:
                pass

