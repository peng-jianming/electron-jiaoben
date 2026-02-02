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
from 配置.设置 import 服务器地址, 缓存目录


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
        self._socketio客户端 = None
        self._初始化客户端()

    def 写入日志(self, 信息):
        """写入日志"""
        self.发送到Electron("logs", 信息)

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
        except Exception as e:
            print(f"内存截图失败: {e}")
            return None

    def 截图到本地(self):
        """截图保存到本地"""
        os.makedirs(缓存目录, exist_ok=True)
        保存路径 = os.path.join(缓存目录, f"{self.设备ID}.png")
        return self.adb.截图(保存路径)

    def ADB点击(self, x, y):
        """ADB点击"""
        if x and y:
            self.adb.模拟点击(x, y, (0, 0.3))

    def 随机ADB点击(self, x, y, 宽, 高):
        """随机ADB点击"""
        if x and y and 宽 and 高:
            随机x = random.randint(x, x + 宽)
            随机y = random.randint(y, y + 高)
            self.adb.模拟点击(随机x, 随机y, (0, 0.3))

    def _初始化客户端(self):
        """初始化 Socket.IO 客户端"""
        if not hasattr(self, "_socketio客户端") or self._socketio客户端 is None:
            self._socketio客户端 = socketio.Client()

        if not self._socketio客户端.connected:
            try:
                self._socketio客户端.connect(服务器地址)
            except Exception as e:
                print(f"Socket.IO 连接失败: {e}")

        return self._socketio客户端

    def 发送到Electron(self, 前端接收事件名, 数据):
        """向 Electron 发送数据"""
        try:
            客户端 = self._初始化客户端()
            data = {
                "cmd": "controller/example/从后端接收数据",
                "args": {"事件名": 前端接收事件名, "数据": 数据},
            }
            客户端.emit("socket-channel", data)

        except socketio.exceptions.ConnectionError as e:
            print(f"连接错误: {e}")
            return None
        except Exception as e:
            print(f"发送数据错误: {e}")
            return None

    def 更新设备状态(self, **kwargs):
        """
        更新设备状态到前端
        
        参数:
            **kwargs: 可选参数，支持以下字段：
                - 当前任务: 当前正在执行的任务名称
                - 下一任务: 下一个待执行的任务名称
                - 金币: 当前金币数量
                - 等级: 当前等级
                - 其他自定义字段
        """
        状态数据 = {"设备ID": self.设备ID}
        状态数据.update(kwargs)
        self.发送到Electron("device-status-update", 状态数据)
