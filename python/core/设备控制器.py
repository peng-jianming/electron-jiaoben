"""
设备控制器 - 封装所有设备操作功能
"""

import os
import random
import struct
import numpy as np
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

    def _raw字节转图像(self, raw字节):
        """将 screencap raw RGBA 字节转为 PIL Image (RGB)"""
        if not raw字节 or len(raw字节) <= 12:
            return None
        try:
            宽, 高, _ = struct.unpack("<III", raw字节[:12])
            预期长度 = 宽 * 高 * 4
            像素字节 = raw字节[12:12 + 预期长度]
            if 宽 > 0 and 高 > 0 and len(像素字节) >= 预期长度:
                像素数组 = np.frombuffer(像素字节, dtype=np.uint8).reshape((高, 宽, 4))
                return Image.fromarray(像素数组, mode="RGBA").convert("RGB")
        except Exception:
            pass
        return None

    def 截图到内存(self):
        """
        截图并直接返回 PIL Image 对象。
        优先级: socket raw → subprocess raw → subprocess PNG

        返回:
            PIL Image 对象，失败返回 None
        """
        try:
            # 1) 最快: socket 直连 ADB server，无子进程开销
            raw字节 = self.adb.截图到内存_socket()
            图像 = self._raw字节转图像(raw字节)
            if 图像:
                return 图像

            # 2) 次快: subprocess raw（兜底）
            raw字节 = self.adb.截图到内存_快速原始()
            图像 = self._raw字节转图像(raw字节)
            if 图像:
                return 图像

            # 3) 最慢: subprocess PNG（最终兜底）
            图像字节 = self.adb.截图到内存()
            if 图像字节 is None:
                return None
            图像 = Image.open(BytesIO(图像字节))
            图像.load()
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


    def 启动应用(self, 包名):
        return self.adb.启动应用(包名)