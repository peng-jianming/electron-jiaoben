"""
设备控制器 - 封装所有设备操作功能
"""

import os
import random
import time
import socketio
from PIL import Image
from io import BytesIO

from .ADB控制器 import ADB控制器类
from 设置 import 服务器地址, 缓存目录


class 设备控制器类:
    """设备控制器，封装所有设备操作功能"""

    def __init__(self, 设备ID):
        """
        初始化设备控制器

        参数:
            设备ID: 设备ID
        """
        self.设备ID = 设备ID
        self.adb = ADB控制器类(设备ID) 

    def 截图到内存(self):
        """
        截图并直接返回 PIL Image 对象

        返回:
            PIL Image 对象，失败返回 None
        """
        try:
            图像字节 = self.adb.截图到内存()
            if 图像字节 is None:
                return None

            图像 = Image.open(BytesIO(图像字节))
            return 图像.convert("RGB")
        except Exception:
            print("内存截图失败")
            return None

    def 截图到本地(self):
        """截图保存到本地"""
        os.makedirs(缓存目录, exist_ok=True)
        保存路径 = os.path.join(缓存目录, f"{self.设备ID}.png")
        return self.adb.截图(保存路径)

    def 精确点击(self, x, y):
        if x and y:
            self.adb.模拟点击(x, y, (0, 0.3))

    def 随机点击(self, 区域):
        """随机点击，区域格式: "x,y,w,h" """
        if 区域:
            x, y, 宽, 高 = [int(v) for v in 区域.split(",")]
            随机x = random.randint(x, x + 宽)
            随机y = random.randint(y, y + 高)
            self.adb.模拟点击(随机x, 随机y, (0, 0.3))

    def 滑动(self, 起始区域, 结束区域):
        self.adb.拟人滑动_区域(起始区域, 结束区域)