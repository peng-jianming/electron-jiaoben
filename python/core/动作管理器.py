"""
动作管理器 - 图像识别和点击操作
"""
import random
import time
import math
import cv2
import numpy as np
from PIL import Image


class 动作管理器类:
    """动作管理器，处理图像识别和点击操作"""

    def __init__(self, 配置, 控制器, 截图上下文, 更新数据):
        """
        初始化动作管理器

        参数:
            配置: 配置字典
            控制器: 设备控制器
            截图上下文: 截图上下文管理器
        """
        self.控制器 = 控制器
        self.更新数据 = 更新数据
        self._截图上下文 = 截图上下文
        self.当前界面 = 配置.get("当前界面")
        self.方式 = 配置.get("方式")
        self.查找字符串 = 配置.get("查找字符串")
        self.分类名 = 配置.get("分类名")
        self.大图路径 = 配置.get("大图路径")
        self.相似度 = 配置.get("相似度", 0.9)
        self.查找区域 = 配置.get("查找区域", "")
        self.偏移点击区域 = 配置.get("偏移点击区域", "")
        self.点击区域 = 配置.get("点击区域", "")
        self.固定点击区域 = 配置.get("固定点击区域", "")
        self.误触区域 = 配置.get("误触区域", "")
        self.字库集合 = {}
        self.图片库集合 = {}
        self.模型 = None
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0
        self.上次点击时间 = 0
        self.点击间隔 = None

    def 查找(self):
        """执行查找"""
        if not self.查找字符串:
            return self

        截图 =  self.大图路径 if self.大图路径 else self._截图上下文.获取截图()
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0

        if 截图:
            if self.方式 == "图片":
                结果 = self._图片找图(
                    截图, self.查找字符串, self.相似度, self.查找区域
                )
                if 结果:
                    self.x = 结果["x"]
                    self.y = 结果["y"]
                    self.w = 结果["w"]
                    self.h = 结果["h"]

            elif self.方式 == "点阵":
                结果 = self._字库找图(
                    截图, self.查找字符串, self.相似度, self.查找区域
                )
                if 结果:
                    self.x = 结果["目标x"]
                    self.y = 结果["目标y"]
                    self.w = 结果["目标宽"]
                    self.h = 结果["目标高"]
            elif self.方式 == "yolo":
                结果 = self._yolo检测(截图, self.相似度)
                if len(结果):
                    区域值 = [int(v) for v in self.查找区域.split(",")] if self.查找区域 else [0, 0, 0, 0]
                    rx, ry = 区域值[0], 区域值[1]
                    for r in 结果:
                        if r["分类名"] == self.分类名:
                            self.x = rx + math.ceil(r["x"])
                            self.y = ry + math.ceil(r["y"])
                            self.w = math.floor(r["w"])
                            self.h = math.floor(r["h"])
                            break
        return self

    def 点击(self, 日志=None, 延时=(1, 3)):
        if self.是否找到():
            # 点击间隔内不能重复点击
            if self.点击间隔 and time.time() - self.上次点击时间 < self.点击间隔:
                return self
            if self.固定点击区域:
                self.控制器.随机点击(self.固定点击区域)
            elif self.偏移点击区域:
                self.偏移点击(self.偏移点击区域)
            elif self.点击区域:
                self.控制器.随机点击(self.点击区域)
            else:
                self.控制器.随机点击(f"{self.x},{self.y},{self.w},{self.h}")
            if 日志:
                self.更新数据("日志", f"{self.当前界面}: {日志}")
            time.sleep(random.uniform(*延时))
            self.上次点击时间 = time.time()
        return self

    def 偏移点击(self, 区域):
        """偏移点击，区域格式: "ox,oy,w,h" 或 "ox,oy" """
        if self.是否找到() and 区域:
            部分 = [int(v) for v in 区域.split(",")]
            ox, oy = 部分[0], 部分[1]
            if len(部分) == 4 and 部分[2] and 部分[3]:
                self.控制器.随机点击(f"{self.x + ox},{self.y + oy},{部分[2]},{部分[3]}")
            else:
                self.控制器.精确点击(self.x + ox, self.y + oy)
        return self

    def 设置查找区域(self, 查找区域):
        """设置查找区域"""
        self.查找区域 = 查找区域 or ""
        return self

    def 设置大图路径(self, 路径):
        """设置大图路径"""
        self.大图路径 = 路径
        return self

    def 设置点击频率(self, 间隔):
        """设置点击频率, 单位: 秒"""
        self.点击间隔 = 间隔
        return self

    def 设置字库(self, 字库集合):
        self.字库集合 = 字库集合
        return self

    def 设置图片库(self, 图片库集合):
        self.图片库集合 = 图片库集合 or {}
        return self

    def 设置模型(self, 模型):
        """设置模型"""
        self.模型 = 模型
        return self

    def 是否找到(self):
        if self.固定点击区域: 
            return True
        else:  
            return bool(self.x and self.y)

    def 找到则点击(self, 延时=(0.5, 1), 日志=None) -> bool:
        return self.查找().点击(日志, 延时).是否找到()

    def 直接点击(self, 延时=(0.5, 1), 日志=None) -> bool:
        return self.点击(日志, 延时).是否找到()

    def _字库找图(self, 大图, 字库名, 相似度=0.9, 区域=""):
        """根据字库名字进行颜色偏色找图，区域格式: "x,y,w,h" """
        if 字库名 not in self.字库集合:
            self.更新数据("日志", f"未找到字库: {字库名}")
            return None

        字库数据列表 = self.字库集合[字库名]
        if not 字库数据列表:
            self.更新数据("日志", f"字库 {字库名} 的条目列表为空")
            return None

        # 读取大图
        if isinstance(大图, Image.Image):
            大图图像 = 大图.convert("RGB")
        else:
            大图图像 = Image.open(大图).convert("RGB")
        大图数组 = np.array(大图图像)

        if 大图数组 is None:
            return None

        大图高, 大图宽 = 大图数组.shape[:2]
        x, y, 宽, 高 = [int(v) for v in 区域.split(",")] if 区域 else [0, 0, 0, 0]

        # 判断是否指定了检测区域
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

            搜索区域 = 大图数组[裁剪y: 裁剪y + 裁剪高, 裁剪x: 裁剪x + 裁剪宽]
            偏移x, 偏移y = 裁剪x, 裁剪y

        # 遍历所有同名字库条目
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
            B = 搜索积分图[0:结果高, w: w + 结果宽]
            C = 搜索积分图[h: h + 结果高, 0:结果宽]
            D = 搜索积分图[h: h + 结果高, w: w + 结果宽]

            搜索点数矩阵 = D - B - C + A
            精确度 = 匹配结果 / (搜索点数矩阵 + 1e-5)
            召回率 = 匹配结果 / (白点数量 + 1e-5)
            分数 = 2 * 精确度 * 召回率 / (精确度 + 召回率 + 1e-5)
            最小值, 最大值, 最小位置, 最大位置 = cv2.minMaxLoc(分数)

            # self.更新数据("日志", f"字库找图 - 字库名: {字库名}, 条目索引: {索引}/{len(字库数据列表) - 1}, 相似度: {最大值:.4f}, 位置: {最大位置}")

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

    def _yolo检测(self, 图像, 置信度阈值=0.6):
        """使用YOLOv8模型检测图片中的目标"""
        if self.模型 is None:
            self.更新数据("日志", "未加载模型")
            return []

        结果列表 = self.模型(图像, conf=置信度阈值, verbose=False)
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
                分类名 = self.模型.names[类别ID]

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

    def _图片找图(self, 大图, 图片名, 相似度=0.9, 区域=""):
        """根据图片库中的模板名进行模板匹配找图，区域格式: "x,y,w,h"。"""
        if 图片名 not in self.图片库集合:
            self.更新数据("日志", f"未找到图片库: {图片名}")
            return None

        模板 = self.图片库集合[图片名]
        if 模板 is None or not hasattr(模板, 'shape'):
            self.更新数据("日志", f"图片库 {图片名} 的模板无效")
            return None

        # 大图转 numpy
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
            搜索区域 = 大图数组[裁剪y: 裁剪y + 裁剪高, 裁剪x: 裁剪x + 裁剪宽]
            偏移x, 偏移y = 裁剪x, 裁剪y

        # 模板与搜索区域通道一致（灰度或 BGR）
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
            return None

        匹配结果 = cv2.matchTemplate(搜索图, 模板图, cv2.TM_CCOEFF_NORMED)
        最小值, 最大值, 最小位置, 最大位置 = cv2.minMaxLoc(匹配结果)

        if 最大值 >= 相似度:
            模板高, 模板宽 = 模板图.shape[:2]
            return {
                "x": 最大位置[0] + 偏移x,
                "y": 最大位置[1] + 偏移y,
                "w": 模板宽,
                "h": 模板高,
                "相似度": float(最大值),
            }
        return None