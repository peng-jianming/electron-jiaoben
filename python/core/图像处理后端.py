import base64
import os
import uuid
from io import BytesIO

import cv2
import numpy as np
from PIL import Image
from 设置 import 资源目录


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
        # 缓存目录：<资源目录>/image_cache
        self._缓存目录 = os.path.join(资源目录, "image_cache")
        os.makedirs(self._缓存目录, exist_ok=True)

    # ========== 基础工具 ==========

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
        file_path = os.path.join(self._缓存目录, f"{image_id}.png")
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
        file_path = os.path.join(self._缓存目录, f"{image_id}.png")

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
                else:
                    raise ValueError(f"未知步骤类型: {step_type}")

            result_dataurl = self._cv2_to_dataurl(img)
            self._通信管理器.发送到Electron(
                "image-processing-result", {"image": result_dataurl}
            )
        except Exception as e:
            print(f"图像处理流水线异常: {e}")

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
