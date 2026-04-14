"""
动作管理器 - 图像识别和点击操作
"""
import random
import time
import math

from . import 图色工具


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
        self.类型 = 配置.get("类型")
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

    def _识别日志(self, 消息: str) -> None:
        self.更新数据("日志", 消息)

    def 查找(self, 新截图=False):
        """执行查找"""
        if not self.查找字符串:
            return self
        if 新截图:
            self._截图上下文.新轮次()
        截图 =  self.大图路径 if self.大图路径 else self._截图上下文.获取截图()
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0

        if 截图:
            if self.类型 == "图片":
                结果 = 图色工具.灰度找图(
                    截图,
                    self.查找字符串,
                    self.图片库集合,
                    self.相似度,
                    self.查找区域,
                    self._识别日志,
                )
                if 结果:
                    self.x = 结果["x"]
                    self.y = 结果["y"]
                    self.w = 结果["w"]
                    self.h = 结果["h"]
            
            elif self.类型 == "彩图":
                结果 = 图色工具.彩图找图(
                    截图,
                    self.查找字符串,
                    self.图片库集合,
                    self.相似度,
                    self.查找区域,
                    self._识别日志,
                )
                if 结果:
                    self.x = 结果["x"]
                    self.y = 结果["y"]
                    self.w = 结果["w"]
                    self.h = 结果["h"]

            elif self.类型 == "点阵":
                结果 = 图色工具.字库找图(
                    截图,
                    self.查找字符串,
                    self.字库集合,
                    self.相似度,
                    self.查找区域,
                    self._识别日志,
                )
                if 结果:
                    self.x = 结果["目标x"]
                    self.y = 结果["目标y"]
                    self.w = 结果["目标宽"]
                    self.h = 结果["目标高"]
            elif self.类型 == "yolo":
                if self.模型 is None:
                    self.更新数据("日志", "未加载模型")
                结果 = 图色工具.yolo检测(截图, self.模型, self.相似度)
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
        self.图片库集合 = 图片库集合
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

    def 找到则点击(self, 延时=(0.5, 1), 日志=None, 新截图=False) -> bool:
        return self.查找(新截图).点击(日志, 延时).是否找到()

    def 直接点击(self, 延时=(0.5, 1), 日志=None) -> bool:
        return self.点击(日志, 延时).是否找到()
