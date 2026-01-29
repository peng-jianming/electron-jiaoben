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

    def _初始化客户端(self, url=None):
        """初始化 Socket.IO 客户端"""
        url = url or 服务器地址
        if not hasattr(self, "_socketio客户端") or self._socketio客户端 is None:
            self._socketio客户端 = socketio.Client()

        if not self._socketio客户端.connected:
            try:
                self._socketio客户端.connect(url)
            except Exception as e:
                print(f"Socket.IO 连接失败: {e}")

        return self._socketio客户端

    def 发送到Electron(
        self,
        属性,
        消息,
        方法="controller/example/changeProp",
        url=None,
        等待响应=True,
    ):
        """向 Electron 发送数据"""
        url = url or 服务器地址
        try:
            客户端 = self._初始化客户端(url)
            数据 = {
                "cmd": 方法,
                "args": {"deviceId": self.设备ID, "prop": 属性, "message": 消息},
            }

            if not 等待响应:
                客户端.emit("socket-channel", 数据)
                return None

            响应数据 = None
            已收到响应 = False

            def 回调(*args):
                nonlocal 响应数据, 已收到响应
                响应数据 = args[0] if args else None
                已收到响应 = True

            客户端.emit("socket-channel", 数据, callback=回调)

            # 等待响应（最多10秒）
            开始时间 = time.time()
            while not 已收到响应 and (time.time() - 开始时间) < 10:
                time.sleep(0.1)

            if not 已收到响应:
                print("等待响应超时")
                return None

            return 响应数据

        except socketio.exceptions.ConnectionError as e:
            print(f"连接错误: {e}")
            return None
        except Exception as e:
            print(f"发送数据错误: {e}")
            return None
