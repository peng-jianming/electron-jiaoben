"""
可组合的图色识别底层：不依赖 JSON 元素配置，可在任务里自由拼装。
含：图片/字库找图、YOLO、OCR 找字、拟人滑动与四阶段循环滑动。
动作管理器内部同样调用本模块的找图逻辑，避免两套实现。
"""

from typing import Any

import cv2
import numpy as np
from PIL import Image
from tkinter import messagebox
    

def 根据区域裁剪(图像数组: np.ndarray, 区域: str = "") -> tuple[np.ndarray, int, int] | None:
    """按区域裁剪图像，返回(搜索区域, 偏移x, 偏移y)。区域无效时返回 None。"""
    图高, 图宽 = 图像数组.shape[:2]
    x, y, 宽, 高 = [int(v) for v in 区域.split(",")] if 区域 else [0, 0, 0, 0]

    if x == 0 and y == 0 and 宽 == 0 and 高 == 0:
        return 图像数组, 0, 0

    x = max(0, x)
    y = max(0, y)
    if 宽 <= 0:
        宽 = 图宽 - x
    if 高 <= 0:
        高 = 图高 - y

    裁剪x = max(0, x)
    裁剪y = max(0, y)
    裁剪宽 = min(宽, 图宽 - 裁剪x)
    裁剪高 = min(高, 图高 - 裁剪y)
    if 裁剪宽 <= 0 or 裁剪高 <= 0:
        return None

    搜索区域 = 图像数组[裁剪y : 裁剪y + 裁剪高, 裁剪x : 裁剪x + 裁剪宽]
    return 搜索区域, 裁剪x, 裁剪y


def 字库核心找图(
    搜索区域: np.ndarray,
    字库数据: dict,
    偏移x: int = 0,
    偏移y: int = 0,
    相似度: float = 0.9,
) -> dict | None:
    """单字库条目的核心匹配函数。"""
    模板掩码 = 字库数据["模板掩码"]
    白点数量 = 字库数据["总数量"]
    小图宽 = 字库数据["宽度"]
    小图高 = 字库数据["高度"]
    目标偏移x = 字库数据["目标偏移x"]
    目标偏移y = 字库数据["目标偏移y"]
    目标偏移宽 = 字库数据["目标偏移宽"]
    目标偏移高 = 字库数据["目标偏移高"]

    if 小图高 > 搜索区域.shape[0] or 小图宽 > 搜索区域.shape[1]:
        return None

    颜色容差列表 = 字库数据["颜色容差列表"]
    搜索二值化结果 = np.zeros((搜索区域.shape[0], 搜索区域.shape[1]), dtype=np.uint8)

    for 颜色容差 in 颜色容差列表:
        基础颜色 = 颜色容差["基础颜色"]
        容差 = 颜色容差["容差"]
        下限 = (基础颜色 - 容差).clip(0, 255).astype(np.uint8)
        上限 = (基础颜色 + 容差).clip(0, 255).astype(np.uint8)
        搜索二值化 = cv2.inRange(搜索区域, 下限, 上限)
        搜索二值化结果 = np.bitwise_or(搜索二值化结果, 搜索二值化)

    搜索掩码 = (搜索二值化结果 == 255).astype(np.uint8)
    匹配结果 = cv2.matchTemplate(搜索掩码, 模板掩码, cv2.TM_CCORR)

    搜索积分图 = cv2.integral(搜索掩码)
    h, w = 模板掩码.shape[:2]
    结果高, 结果宽 = 匹配结果.shape

    A = 搜索积分图[0:结果高, 0:结果宽]
    B = 搜索积分图[0:结果高, w : w + 结果宽]
    C = 搜索积分图[h : h + 结果高, 0:结果宽]
    D = 搜索积分图[h : h + 结果高, w : w + 结果宽]

    搜索点数矩阵 = D - B - C + A
    精确度 = 匹配结果 / (搜索点数矩阵 + 1e-5)
    召回率 = 匹配结果 / (白点数量 + 1e-5)
    分数 = 2 * 精确度 * 召回率 / (精确度 + 召回率 + 1e-5)
    _, 最大值, _, 最大位置 = cv2.minMaxLoc(分数)

    if 最大值 < 相似度:
        return None

    return {
        "原始x": 最大位置[0] + 偏移x,
        "原始y": 最大位置[1] + 偏移y,
        "原始宽": 小图宽,
        "原始高": 小图高,
        "目标x": 最大位置[0] + 偏移x + 目标偏移x,
        "目标y": 最大位置[1] + 偏移y + 目标偏移y,
        "目标宽": 目标偏移宽,
        "目标高": 目标偏移高,
        "相似度": float(最大值),
    }


def 灰度核心找图(
    搜索区域: np.ndarray,
    模板项: dict,
    偏移x: int = 0,
    偏移y: int = 0,
    相似度: float = 0.9,
) -> dict | None:
    """单模板项的灰度匹配核心函数。"""
    模板 = 模板项.get("当前图片数据")
    if 模板 is None or not hasattr(模板, "shape"):
        return None

    目标偏移x = int(模板项.get("目标偏移x", 0))
    目标偏移y = int(模板项.get("目标偏移y", 0))
    目标偏移宽 = 模板项.get("目标偏移宽")
    目标偏移高 = 模板项.get("目标偏移高")

    if len(模板.shape) == 2:
        搜索图 = cv2.cvtColor(搜索区域, cv2.COLOR_BGR2GRAY)
        模板图 = np.asarray(模板, dtype=np.uint8)
    else:
        模板图 = np.asarray(模板, dtype=np.uint8)
        if 模板图.shape[2] != 搜索区域.shape[2]:
            搜索图 = cv2.cvtColor(搜索区域, cv2.COLOR_BGR2GRAY)
            模板图 = cv2.cvtColor(模板图, cv2.COLOR_BGR2GRAY)
        else:
            搜索图 = 搜索区域

    if 模板图.shape[0] > 搜索图.shape[0] or 模板图.shape[1] > 搜索图.shape[1]:
        return None

    匹配结果 = cv2.matchTemplate(搜索图, 模板图, cv2.TM_CCOEFF_NORMED)
    _, 最大值, _, 最大位置 = cv2.minMaxLoc(匹配结果)
    if 最大值 < 相似度:
        return None

    模板高, 模板宽 = 模板图.shape[:2]
    if 目标偏移宽 is None:
        目标偏移宽 = 模板宽
    if 目标偏移高 is None:
        目标偏移高 = 模板高

    return {
        "原始x": 最大位置[0] + 偏移x,
        "原始y": 最大位置[1] + 偏移y,
        "原始宽": 模板宽,
        "原始高": 模板高,
        "x": 最大位置[0] + 偏移x + int(目标偏移x),
        "y": 最大位置[1] + 偏移y + int(目标偏移y),
        "w": int(目标偏移宽),
        "h": int(目标偏移高),
        "相似度": float(最大值),
    }


def 彩图核心找图(
    搜索区: np.ndarray,
    模板项: dict,
    偏移x: int = 0,
    偏移y: int = 0,
    相似度: float = 0.9,
) -> dict | None:
    """单模板项的彩图匹配核心函数。"""
    模板 = 模板项.get("当前图片数据")
    if 模板 is None or not hasattr(模板, "shape"):
        return None
    模板图 = np.asarray(模板, dtype=np.uint8)
    目标偏移x = int(模板项.get("目标偏移x", 0))
    目标偏移y = int(模板项.get("目标偏移y", 0))
    目标偏移宽 = 模板项.get("目标偏移宽")
    目标偏移高 = 模板项.get("目标偏移高")
    误差满分标尺 = 40.0
    极低误差免清晰度_RMSE上限 = 12.0

    维模 = 模板图.shape
    if len(维模) == 2 or (len(维模) == 3 and 维模[2] == 1):
        模板BGR = cv2.cvtColor(模板图, cv2.COLOR_GRAY2BGR)
    elif len(维模) == 3 and 维模[2] == 4:
        模板BGR = cv2.cvtColor(模板图, cv2.COLOR_BGRA2BGR)
    else:
        模板BGR = 模板图
    模板高, 模板宽 = 模板BGR.shape[:2]

    if 模板高 > 搜索区.shape[0] or 模板宽 > 搜索区.shape[1]:
        return None

    方差和图 = np.sum(
        [
            cv2.matchTemplate(大, 小, cv2.TM_SQDIFF)
            for 大, 小 in zip(cv2.split(搜索区), cv2.split(模板BGR))
        ],
        axis=0,
    )

    最小方差和, _, 最佳, _ = cv2.minMaxLoc(方差和图)
    px, py = int(最佳[0]), int(最佳[1])

    像素数 = float(模板高 * 模板宽 * 3)
    均方根误差 = float(np.sqrt(max(0.0, float(最小方差和) / 像素数)))
    按误差相似度 = max(0.0, min(1.0, 1.0 - (均方根误差 / 误差满分标尺) ** 2))

    结果高, 结果宽 = 方差和图.shape
    半高, 半宽 = max(模板高 // 2, 2), max(模板宽 // 2, 2)
    遮蔽 = 方差和图.astype(np.float64, copy=True)
    遮蔽[
        max(0, py - 半高) : min(结果高, py + 半高 + 1),
        max(0, px - 半宽) : min(结果宽, px + 半宽 + 1),
    ] = np.inf
    外围 = 遮蔽[np.isfinite(遮蔽)]
    if 外围.size == 0:
        清晰度 = 1.0
    else:
        次小 = float(np.min(外围))
        清晰度 = max(0.0, min(1.0, (次小 - float(最小方差和)) / (次小 + 1e-12)))

    if 均方根误差 <= 极低误差免清晰度_RMSE上限:
        相似度值 = float(max(0.0, min(1.0, 按误差相似度)))
    else:
        相似度值 = float(max(0.0, min(1.0, 按误差相似度 * np.sqrt(清晰度))))

    if 相似度值 < 相似度:
        return None

    if 目标偏移宽 is None:
        目标偏移宽 = int(模板宽)
    if 目标偏移高 is None:
        目标偏移高 = int(模板高)

    return {
        "原始x": px + 偏移x,
        "原始y": py + 偏移y,
        "原始宽": int(模板宽),
        "原始高": int(模板高),
        "x": px + 偏移x + int(目标偏移x),
        "y": py + 偏移y + int(目标偏移y),
        "w": int(目标偏移宽),
        "h": int(目标偏移高),
        "相似度": float(相似度值),
    }


def 字库找图(
    大图: Any,
    字库名: str,
    字库集合: dict,
    相似度: float = 0.9,
    区域: str = "",
) -> dict | None:
    """点阵/字库匹配。返回含 目标x/目标y/目标宽/目标高 等字段的字典，未找到返回 None。"""
    if 字库名 not in 字库集合:
        messagebox.showinfo("图色工具", f"未找到字库: {字库名}")
        return None

    字库数据列表 = 字库集合[字库名]
    if not 字库数据列表:
        messagebox.showinfo("图色工具", f"字库 {字库名} 的条目列表为空")
        return None

    if isinstance(大图, Image.Image):
        大图图像 = 大图.convert("RGB")
    else:
        大图图像 = Image.open(大图).convert("RGB")
    大图数组 = np.array(大图图像)

    if 大图数组 is None:
        return None

    裁剪结果 = 根据区域裁剪(大图数组, 区域)
    if 裁剪结果 is None:
        return None
    搜索区域, 偏移x, 偏移y = 裁剪结果

    for 字库数据 in 字库数据列表:
        匹配结果 = 字库核心找图(搜索区域, 字库数据, 偏移x, 偏移y, 相似度)
        if 匹配结果 is not None:
            return 匹配结果

    return None


def 灰度找图(
    大图: Any,
    图片名: str,
    图片库集合: dict,
    相似度: float = 0.9,
    区域: str = "",
) -> dict | None:
    """模板匹配。返回目标 x/y/w/h/相似度，未找到返回 None。"""
    if 图片名 not in 图片库集合:
        messagebox.showinfo("图色工具", f"未找到图片库: {图片名}")
        return None

    模板列表 = 图片库集合[图片名]
    if not isinstance(模板列表, list) or not 模板列表:
        messagebox.showinfo("图色工具", f"图片库 {图片名} 的模板列表无效")
        return None

    if isinstance(大图, Image.Image):
        大图数组 = np.array(大图.convert("RGB"))
        大图数组 = cv2.cvtColor(大图数组, cv2.COLOR_RGB2BGR)
    else:
        大图数组 = np.array(Image.open(大图).convert("RGB"))
        大图数组 = cv2.cvtColor(大图数组, cv2.COLOR_RGB2BGR)

    if 大图数组 is None:
        return None

    裁剪结果 = 根据区域裁剪(大图数组, 区域)
    if 裁剪结果 is None:
        return None
    搜索区域, 偏移x, 偏移y = 裁剪结果

    for 模板项 in 模板列表:
        if not isinstance(模板项, dict):
            raise ValueError(f"图片库 {图片名} 的模板项 {模板项} 格式错误")
        匹配结果 = 灰度核心找图(搜索区域, 模板项, 偏移x, 偏移y, 相似度)
        if 匹配结果 is not None:
            return 匹配结果
    return None


def 彩图找图(
    大图: Any,
    图片名: str,
    图片库集合: dict,
    相似度: float = 0.9,
    区域: str = "",
) -> dict | None:
    """基于彩图模板匹配的找图。返回结构与 灰度找图 保持一致。"""
    if 图片名 not in 图片库集合:
        messagebox.showinfo("图色工具", f"未找到图片库: {图片名}")
        return None

    模板列表 = 图片库集合[图片名]
    if not isinstance(模板列表, list) or not 模板列表:
        messagebox.showinfo("图色工具", f"图片库 {图片名} 的模板列表无效")
        return None

    if isinstance(大图, Image.Image):
        大图数组 = np.array(大图.convert("RGB"))
        大图数组 = cv2.cvtColor(大图数组, cv2.COLOR_RGB2BGR)
    else:
        大图数组 = np.array(Image.open(大图).convert("RGB"))
        大图数组 = cv2.cvtColor(大图数组, cv2.COLOR_RGB2BGR)

    if 大图数组 is None:
        return None

    维大 = 大图数组.shape
    if len(维大) == 2 or (len(维大) == 3 and 维大[2] == 1):
        大图BGR = cv2.cvtColor(大图数组, cv2.COLOR_GRAY2BGR)
    elif len(维大) == 3 and 维大[2] == 4:
        大图BGR = cv2.cvtColor(大图数组, cv2.COLOR_BGRA2BGR)
    else:
        大图BGR = 大图数组

    裁剪结果 = 根据区域裁剪(大图BGR, 区域)
    if 裁剪结果 is None:
        return None
    搜索区, 偏移x, 偏移y = 裁剪结果

    for 模板项 in 模板列表:
        if not isinstance(模板项, dict):
            raise ValueError(f"图片库 {图片名} 的模板项 {模板项} 格式错误")
        匹配结果 = 彩图核心找图(搜索区, 模板项, 偏移x, 偏移y, 相似度)
        if 匹配结果 is not None:
            return 匹配结果
    return None
