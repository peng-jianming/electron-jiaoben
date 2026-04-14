"""
可组合的图色识别底层：不依赖 JSON 元素配置，可在任务里自由拼装。
含：图片/字库找图、YOLO、OCR 找字、拟人滑动与四阶段循环滑动。
动作管理器内部同样调用本模块的找图逻辑，避免两套实现。
"""
from __future__ import annotations

import math
import random
import time
from typing import Any, Callable

import cv2
import numpy as np
from PIL import Image

日志回调类型 = Callable[[str], None] | None


def _写日志(日志回调: 日志回调类型, 消息: str) -> None:
    if 日志回调:
        日志回调(消息)


def 字库找图(
    大图: Any,
    字库名: str,
    字库集合: dict,
    相似度: float = 0.9,
    区域: str = "",
    日志回调: 日志回调类型 = None,
) -> dict | None:
    """点阵/字库匹配。返回含 目标x/目标y/目标宽/目标高 等字段的字典，未找到返回 None。"""
    if 字库名 not in 字库集合:
        _写日志(日志回调, f"未找到字库: {字库名}")
        return None

    字库数据列表 = 字库集合[字库名]
    if not 字库数据列表:
        _写日志(日志回调, f"字库 {字库名} 的条目列表为空")
        return None

    if isinstance(大图, Image.Image):
        大图图像 = 大图.convert("RGB")
    else:
        大图图像 = Image.open(大图).convert("RGB")
    大图数组 = np.array(大图图像)

    if 大图数组 is None:
        return None

    大图高, 大图宽 = 大图数组.shape[:2]
    x, y, 宽, 高 = [int(v) for v in 区域.split(",")] if 区域 else [0, 0, 0, 0]

    if x == 0 and y == 0 and 宽 == 0 and 高 == 0:
        搜索区域 = 大图数组
        偏移x, 偏移y = 0, 0
    else:
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if 宽 <= 0:
            宽 = 大图宽 - x
        if 高 <= 0:
            高 = 大图高 - y

        裁剪x = max(0, x)
        裁剪y = max(0, y)
        裁剪宽 = min(宽, 大图宽 - 裁剪x)
        裁剪高 = min(高, 大图高 - 裁剪y)

        if 裁剪宽 <= 0 or 裁剪高 <= 0:
            return None

        搜索区域 = 大图数组[裁剪y : 裁剪y + 裁剪高, 裁剪x : 裁剪x + 裁剪宽]
        偏移x, 偏移y = 裁剪x, 裁剪y

    for 索引, 字库数据 in enumerate(字库数据列表):
        模板掩码 = 字库数据["模板掩码"]
        白点数量 = 字库数据["总数量"]
        小图宽 = 字库数据["宽度"]
        小图高 = 字库数据["高度"]
        目标偏移x = 字库数据["目标偏移x"]
        目标偏移y = 字库数据["目标偏移y"]
        目标偏移宽 = 字库数据["目标偏移宽"]
        目标偏移高 = 字库数据["目标偏移高"]

        if 小图高 > 搜索区域.shape[0] or 小图宽 > 搜索区域.shape[1]:
            continue

        颜色容差列表 = 字库数据["颜色容差列表"]

        搜索二值化结果 = np.zeros(
            (搜索区域.shape[0], 搜索区域.shape[1]), dtype=np.uint8
        )

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
        H, W = 搜索掩码.shape[:2]
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
        最小值, 最大值, 最小位置, 最大位置 = cv2.minMaxLoc(分数)

        if 最大值 >= 相似度:
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

    return None


def 图片找图(
    大图: Any,
    图片名: str,
    图片库集合: dict,
    相似度: float = 0.9,
    区域: str = "",
    日志回调: 日志回调类型 = None,
) -> dict | None:
    """模板匹配。返回目标 x/y/w/h/相似度，未找到返回 None。"""
    if 图片名 not in 图片库集合:
        _写日志(日志回调, f"未找到图片库: {图片名}")
        return None

    模板列表 = 图片库集合[图片名]
    if not isinstance(模板列表, list) or not 模板列表:
        _写日志(日志回调, f"图片库 {图片名} 的模板列表无效")
        return None

    if isinstance(大图, Image.Image):
        大图数组 = np.array(大图.convert("RGB"))
        大图数组 = cv2.cvtColor(大图数组, cv2.COLOR_RGB2BGR)
    else:
        大图数组 = np.array(Image.open(大图).convert("RGB"))
        大图数组 = cv2.cvtColor(大图数组, cv2.COLOR_RGB2BGR)

    if 大图数组 is None:
        return None

    大图高, 大图宽 = 大图数组.shape[:2]
    x, y, 宽, 高 = [int(v) for v in 区域.split(",")] if 区域 else [0, 0, 0, 0]

    if x == 0 and y == 0 and 宽 == 0 and 高 == 0:
        搜索区域 = 大图数组
        偏移x, 偏移y = 0, 0
    else:
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if 宽 <= 0:
            宽 = 大图宽 - x
        if 高 <= 0:
            高 = 大图高 - y
        裁剪x = max(0, x)
        裁剪y = max(0, y)
        裁剪宽 = min(宽, 大图宽 - 裁剪x)
        裁剪高 = min(高, 大图高 - 裁剪y)
        if 裁剪宽 <= 0 or 裁剪高 <= 0:
            return None
        搜索区域 = 大图数组[裁剪y : 裁剪y + 裁剪高, 裁剪x : 裁剪x + 裁剪宽]
        偏移x, 偏移y = 裁剪x, 裁剪y

    for 模板项 in 模板列表:
        if isinstance(模板项, dict):
            模板 = 模板项.get("当前图片数据")
            目标偏移x = int(模板项.get("目标偏移x", 0))
            目标偏移y = int(模板项.get("目标偏移y", 0))
            目标偏移宽 = 模板项.get("目标偏移宽")
            目标偏移高 = 模板项.get("目标偏移高")
        else:
            raise ValueError(f"图片库 {图片名} 的模板项 {模板项} 格式错误")

        if 模板 is None or not hasattr(模板, "shape"):
            continue

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
                模板图 = 模板图

        if 模板图.shape[0] > 搜索图.shape[0] or 模板图.shape[1] > 搜索图.shape[1]:
            continue

        匹配结果 = cv2.matchTemplate(搜索图, 模板图, cv2.TM_CCOEFF_NORMED)
        最小值, 最大值, 最小位置, 最大位置 = cv2.minMaxLoc(匹配结果)

        if 最大值 >= 相似度:
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
    return None





def yolo检测(图像: Any, 模型: Any, 置信度阈值: float = 0.6) -> list[dict]:
    """与动作管理器一致的检测列表结构；模型为 None 时返回空列表。"""
    if 模型 is None:
        return []

    结果列表 = 模型(图像, conf=置信度阈值, verbose=False)
    检测结果 = []

    for 结果 in 结果列表:
        边界框 = 结果.boxes
        if 边界框 is None:
            continue

        for i in range(len(边界框)):
            xywh = 边界框.xywh[i].tolist()
            x, y, w, h = xywh
            置信度 = float(边界框.conf[i])
            类别ID = int(边界框.cls[i])
            分类名 = 模型.names[类别ID]

            检测 = {
                "分类名": 分类名,
                "置信度": 置信度,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
            }
            检测结果.append(检测)

    return 检测结果


def 解析查找结果矩形(结果: dict | None) -> tuple[int, int, int, int] | None:
    """统一 图片找图 与 字库找图 的返回，得到 (x, y, w, h)。"""
    if not 结果:
        return None
    if "目标x" in 结果:
        return (
            int(结果["目标x"]),
            int(结果["目标y"]),
            int(结果["目标宽"]),
            int(结果["目标高"]),
        )
    return (int(结果["x"]), int(结果["y"]), int(结果["w"]), int(结果["h"]))


def 按矩形随机点击(
    控制器: Any,
    x: int,
    y: int,
    w: int,
    h: int,
) -> None:
    控制器.随机点击(f"{x},{y},{w},{h}")


def 从查找结果随机点击(控制器: Any, 结果: dict | None) -> bool:
    """根据 图片找图 / 字库找图 的返回值点击；无效结果返回 False。"""
    矩形 = 解析查找结果矩形(结果)
    if not 矩形:
        return False
    x, y, w, h = 矩形
    if not w or not h:
        return False
    按矩形随机点击(控制器, x, y, w, h)
    return True


def 解析区域四元组(区域: str | None) -> tuple[int, int, int, int] | None:
    """\"x,y,w,h\" → 四元组；空串或 None 表示不裁剪（全图）。"""
    if 区域 is None or not str(区域).strip():
        return None
    parts = [p.strip() for p in str(区域).split(",")]
    if len(parts) != 4:
        return None
    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))
    except ValueError:
        return None


def 识别文字(
    截图上下文: Any,
    是否新截图: bool = False,
    区域: str | None = None,
) -> list[dict]:
    """
    OCR，返回与 识字管理器.识别 相同结构：
    [{"结果": str, "x", "y", "w", "h"}, ...]
    """
    from .识字管理器 import 识字管理器类

    mgr = 识字管理器类(截图上下文)
    parsed = 解析区域四元组(区域)
    if parsed:
        x, y, w, h = parsed
        return mgr.识别(x=x, y=y, w=w, h=h, 是否新截图=是否新截图)
    return mgr.识别(是否新截图=是否新截图)


def 筛选含文字(
    条目列表: list[dict],
    子串: str,
    *,
    去空白: bool = True,
) -> list[dict]:
    """保留「结果」字段中包含 子串 的条目。"""
    if not 子串:
        return list(条目列表)
    key = 子串.strip() if 去空白 else 子串
    out = []
    for item in 条目列表:
        文本 = item.get("结果", "")
        if 去空白:
            文本 = str(文本).strip()
        if key in 文本:
            out.append(item)
    return out


def 取首条含文字(
    条目列表: list[dict],
    子串: str,
    **kwargs: Any,
) -> dict | None:
    行 = 筛选含文字(条目列表, 子串, **kwargs)
    return 行[0] if 行 else None


def 点击文字块(
    控制器: Any,
    条目: dict | None,
) -> bool:
    """点击 OCR 条目对应的矩形（随机点）。"""
    if not 条目:
        return False
    try:
        x, y, w, h = int(条目["x"]), int(条目["y"]), int(条目["w"]), int(条目["h"])
    except (KeyError, TypeError, ValueError):
        return False
    if w <= 0 or h <= 0:
        return False
    按矩形随机点击(控制器, x, y, w, h)
    return True


def 拟人滑动(
    控制器: Any,
    起始区域: str,
    结束区域: str,
    日志回调: 日志回调类型 = None,
    日志消息: str | None = None,
) -> None:
    """同 设备控制器.滑动：在两块 \"x,y,w,h\" 区域之间拟人滑动一次。"""
    if 起始区域 and 结束区域:
        控制器.滑动(起始区域, 结束区域)
    if 日志消息:
        _写日志(日志回调, 日志消息)


def 按循环滑动四阶段(
    控制器: Any,
    起始区域: str,
    结束区域: str,
    上下文: dict,
    计数键: str = "图色滑动循环次数",
    每阶段次数: int = 3,
    日志回调: 日志回调类型 = None,
    日志消息: str | None = None,
) -> None:
    """
    与 界面管理器.滑动区域操作类.按循环滑动 相同节奏：
    反向×N → 正向×N → 正向×N → 反向×N（N=每阶段次数）。
    """
    每阶段次数 = max(1, int(每阶段次数))
    次数 = 上下文.get(计数键, 0)
    阶段 = (次数 // 每阶段次数) % 4
    if 阶段 in (0, 3):
        控制器.滑动(结束区域, 起始区域)
    else:
        控制器.滑动(起始区域, 结束区域)
    上下文[计数键] = 次数 + 1
    if 日志消息:
        _写日志(日志回调, 日志消息)


class 图色工具包类:
    """
    在任务中组合使用：持有字库/图片库/模型/控制器与可选截图上下文。
    例：包 = 环境.创建图色工具包()；包.获取截图并找图("某模板名", 区域="100,100,200,200")
    """

    def __init__(
        self,
        字库集合: dict | None,
        图片库集合: dict | None,
        检测模型: Any,
        控制器: Any,
        截图上下文: Any | None = None,
        更新数据: Any | None = None,
        日志前缀: str = "",
    ):
        self.字库集合 = 字库集合 or {}
        self.图片库集合 = 图片库集合 or {}
        self.检测模型 = 检测模型
        self.控制器 = 控制器
        self._截图上下文 = 截图上下文
        self._更新数据 = 更新数据
        self._日志前缀 = 日志前缀

    def _日志(self, 消息: str) -> None:
        if self._更新数据:
            if self._日志前缀:
                self._更新数据("日志", f"{self._日志前缀}: {消息}")
            else:
                self._更新数据("日志", 消息)

    def 当前截图(self, 新轮次: bool = False) -> Any:
        if self._截图上下文 is None:
            raise RuntimeError("图色工具包未绑定截图上下文")
        if 新轮次:
            self._截图上下文.新轮次()
        return self._截图上下文.获取截图()

    def 图片找图(
        self,
        图片名: str,
        大图: Any | None = None,
        相似度: float = 0.9,
        区域: str = "",
        新截图: bool = False,
    ) -> dict | None:
        图 = 大图 if 大图 is not None else self.当前截图(新截图)
        return 图片找图(
            图,
            图片名,
            self.图片库集合,
            相似度,
            区域,
            self._日志,
        )

    def 字库找图(
        self,
        字库名: str,
        大图: Any | None = None,
        相似度: float = 0.9,
        区域: str = "",
        新截图: bool = False,
    ) -> dict | None:
        图 = 大图 if 大图 is not None else self.当前截图(新截图)
        return 字库找图(
            图,
            字库名,
            self.字库集合,
            相似度,
            区域,
            self._日志,
        )

    def yolo检测(
        self,
        图像: Any | None = None,
        置信度阈值: float = 0.6,
        新截图: bool = False,
    ) -> list[dict]:
        图 = 图像 if 图像 is not None else self.当前截图(新截图)
        return yolo检测(图, self.检测模型, 置信度阈值)

    def 取某分类检测框(
        self,
        分类名: str,
        图像: Any | None = None,
        置信度阈值: float = 0.6,
        查找区域: str = "",
        新截图: bool = False,
    ) -> tuple[int, int, int, int] | None:
        """
        在 yolo 结果中按分类名取第一个框，可选区域偏移 (rx,ry,0,0) 与 动作管理器 行为一致。
        返回 (x, y, w, h) 像素矩形，未找到返回 None。
        """
        列表 = self.yolo检测(图像, 置信度阈值, 新截图)
        if not 列表:
            return None
        区域值 = [int(v) for v in 查找区域.split(",")] if 查找区域 else [0, 0, 0, 0]
        rx, ry = 区域值[0], 区域值[1]
        for r in 列表:
            if r["分类名"] == 分类名:
                return (
                    rx + math.ceil(r["x"]),
                    ry + math.ceil(r["y"]),
                    math.floor(r["w"]),
                    math.floor(r["h"]),
                )
        return None

    def 点击查找结果(
        self,
        结果: dict | None,
        日志: str | None = None,
        延时: tuple[float, float] = (1, 3),
    ) -> bool:
        ok = 从查找结果随机点击(self.控制器, 结果)
        if ok and 日志 and self._更新数据:
            self._日志(日志)
        if ok:
            time.sleep(random.uniform(*延时))
        return ok

    def 找图并点击(
        self,
        图片名: str,
        相似度: float = 0.9,
        区域: str = "",
        日志: str | None = None,
        新截图: bool = False,
        延时: tuple[float, float] = (0.5, 1),
    ) -> bool:
        结果 = self.图片找图(图片名, 相似度=相似度, 区域=区域, 新截图=新截图)
        return self.点击查找结果(结果, 日志=日志, 延时=延时)

    def 识别文字(
        self,
        区域: str | None = None,
        新截图: bool = False,
    ) -> list[dict]:
        if self._截图上下文 is None:
            raise RuntimeError("图色工具包未绑定截图上下文")
        return 识别文字(self._截图上下文, 是否新截图=新截图, 区域=区域)

    def 筛选含文字(self, 条目列表: list[dict], 子串: str, **kwargs: Any) -> list[dict]:
        return 筛选含文字(条目列表, 子串, **kwargs)

    def 取首条含文字(self, 条目列表: list[dict], 子串: str, **kwargs: Any) -> dict | None:
        return 取首条含文字(条目列表, 子串, **kwargs)

    def 点击文字块(
        self,
        条目: dict | None,
        日志: str | None = None,
        延时: tuple[float, float] = (0.5, 1),
    ) -> bool:
        ok = 点击文字块(self.控制器, 条目)
        if ok and 日志:
            self._日志(日志)
        if ok:
            time.sleep(random.uniform(*延时))
        return ok

    def 找含字并点击(
        self,
        子串: str,
        区域: str | None = None,
        新截图: bool = False,
        日志: str | None = None,
        延时: tuple[float, float] = (0.5, 1),
        **筛选参数,
    ) -> bool:
        列表 = self.识别文字(区域=区域, 新截图=新截图)
        条目 = 取首条含文字(列表, 子串, **筛选参数)
        return self.点击文字块(条目, 日志=日志, 延时=延时)

    def 拟人滑动(
        self,
        起始区域: str,
        结束区域: str,
        日志: str | None = None,
    ) -> None:
        拟人滑动(
            self.控制器,
            起始区域,
            结束区域,
            self._日志 if self._更新数据 else None,
            日志,
        )

    def 按字典拟人滑动(self, 区域配置: dict, 日志: str | None = None) -> None:
        """区域配置含 起始区域、结束区域 键，与 界面配置.json 里 滑动区域 单项结构一致。"""
        self.拟人滑动(区域配置["起始区域"], 区域配置["结束区域"], 日志=日志)

    def 按循环滑动(
        self,
        起始区域: str,
        结束区域: str,
        上下文: dict,
        计数键: str = "图色滑动循环次数",
        每阶段次数: int = 3,
        日志: str | None = None,
    ) -> None:
        按循环滑动四阶段(
            self.控制器,
            起始区域,
            结束区域,
            上下文,
            计数键=计数键,
            每阶段次数=每阶段次数,
            日志回调=self._日志 if self._更新数据 else None,
            日志消息=日志,
        )

    def 按字典循环滑动(
        self,
        区域配置: dict,
        上下文: dict,
        计数键: str = "图色滑动循环次数",
        每阶段次数: int = 3,
        日志: str | None = None,
    ) -> None:
        self.按循环滑动(
            区域配置["起始区域"],
            区域配置["结束区域"],
            上下文,
            计数键=计数键,
            每阶段次数=每阶段次数,
            日志=日志,
        )

    def 字库找图并点击(
        self,
        字库名: str,
        相似度: float = 0.9,
        区域: str = "",
        日志: str | None = None,
        新截图: bool = False,
        延时: tuple[float, float] = (0.5, 1),
    ) -> bool:
        结果 = self.字库找图(字库名, 相似度=相似度, 区域=区域, 新截图=新截图)
        return self.点击查找结果(结果, 日志=日志, 延时=延时)
