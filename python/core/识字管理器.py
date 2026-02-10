"""
识字管理器 - 基于 PaddleOCR 的图片文字识别（全局单例，避免重复加载模型）
"""

import os

import cv2
import numpy as np

# 将模型缓存到不含中文的路径，避免 "parse empty input JSON" 等路径编码问题
_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".paddle_cache")
os.makedirs(_cache_dir, exist_ok=True)
os.environ["PADDLE_PDX_CACHE_HOME"] = _cache_dir
# 跳过模型源连通性检查，加快启动
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

from paddleocr import PaddleOCR  # noqa: E402

_ocr = None

def get_ocr():
    global _ocr
    if _ocr is None:
        # 只在第一次调用时初始化
        # enable_mkldnn=False：避免 CPU 上 New IR + OneDNN 的 NotImplementedError
        _ocr = PaddleOCR(
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                    enable_mkldnn=False,
                )
    return _ocr

class 识字管理器类:
    """对图片做 OCR，返回识别结果列表。可与设备控制器.截图到内存() 配合使用。"""
    def __init__(self, 截图上下文=None):
        self._截图上下文 = 截图上下文
        get_ocr()

    def 识别(self, x=None, y=None, w=None, h=None, 是否新截图 = False):
        """
        对传入的图片做 OCR，可选区域识别；未传区域时识别全图。

        :param image_input: PIL Image (RGB)，即 设备控制器.截图到内存() 的 return 格式（非路径）
        :param x: 区域左上角 x，不传则全图
        :param y: 区域左上角 y，不传则全图
        :param w: 区域宽度，不传则全图
        :param h: 区域高度，不传则全图
        :return: [{"结果": "识别文字", "x": 左上x, "y": 左上y, "w": 宽度, "h": 高度}, ...]，坐标为相对当前输入区域的坐标
        """
        if 是否新截图:
            self._截图上下文.新轮次()
        img = self._截图上下文.获取截图()
        if x is not None and y is not None and w is not None and h is not None:
            img = img.crop((x, y, x + w, y + h))

        # PaddleOCR 更推荐传入 OpenCV BGR 格式的 ndarray，这里从 PIL 转换
        img_np = np.array(img)
        if img_np.ndim == 3 and img_np.shape[2] == 3:
            img_input = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        else:
            # 灰度或其他通道数，直接使用
            img_input = img_np

        result = _ocr.predict(input=img_input)
        out = []
        for page in result:
            texts = page.get("rec_texts", [])
            boxes = page.get("rec_boxes", [])
            for i, text in enumerate(texts):
                box = boxes[i] if i < len(boxes) else [0, 0, 0, 0]
                x1, y1, x2, y2 = box[0], box[1], box[2], box[3]
                out.append({
                    "结果": text,
                    "x": int(x1),
                    "y": int(y1),
                    "w": int(x2 - x1),
                    "h": int(y2 - y1),
                })
        return out
