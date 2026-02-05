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
        self._上次操作目标 = None
        self._上次操作时间 = 0
        self._操作冷却秒数 = 8
        self._初始化客户端()

    def 是否允许操作(self, 目标标识):
        """
        判断是否允许对当前目标进行操作。
        8 秒内对同一目标不重复操作，同一时间只记录一个目标。

        参数:
            目标标识: 用于区分不同操作目标的字符串（如查找字符串、分类名等）

        返回:
            bool: True 表示允许操作，False 表示 8 秒内已操作过同一目标，应跳过
        """
        if 目标标识 is None:
            return True
        现在 = time.time()
        if self._上次操作目标 is None:
            return True
        if self._上次操作目标 != 目标标识:
            return True
        if 现在 - self._上次操作时间 >= self._操作冷却秒数:
            return True
        
        self.写入日志(f"8 秒内对同一目标不重复操作: {目标标识}")
        return False

    def 记录操作(self, 目标标识):
        """
        记录已对某目标执行操作，用于 8 秒内同目标不重复操作。

        参数:
            目标标识: 与 是否允许操作 使用的同一标识
        """
        if 目标标识 is not None:
            self._上次操作目标 = 目标标识
            self._上次操作时间 = time.time()

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
            self.写入日志("内存截图失败")
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
            except Exception:
                self.写入日志("Socket.IO 连接失败")

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

        except socketio.exceptions.ConnectionError:
            self.写入日志("连接错误")
            return None
        except Exception:
            self.写入日志("发送数据错误")
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

    def 写入日志(self, 日志):
        # print(日志)
        状态数据 = {"设备ID": self.设备ID, "日志": 日志}
        self.发送到Electron("device-status-update", 状态数据)

    def 随机误触(self, 屏幕宽=1280, 屏幕高=720, 安全边距=50):
        """
        执行随机误触操作，模拟人为误操作
        
        参数:
            屏幕宽: 屏幕宽度，默认1280
            屏幕高: 屏幕高度，默认720
            安全边距: 屏幕边缘安全距离，避免点到系统区域
        """
        # 在安全区域内生成随机坐标
        随机x = random.randint(安全边距, 屏幕宽 - 安全边距)
        随机y = random.randint(安全边距, 屏幕高 - 安全边距)
        
        # 随机延迟，模拟人的反应时间
        延迟 = random.uniform(0.1, 0.5)
        time.sleep(延迟)
        
        self.写入日志(f"[误触模拟] 随机点击位置: ({随机x}, {随机y})")
        self.adb.模拟点击(随机x, 随机y, (0, 0.2))

    def 随机空白滑动(self, 屏幕宽=1280, 屏幕高=720):
        """
        执行随机短滑动，模拟人为无意识滑动
        
        参数:
            屏幕宽: 屏幕宽度
            屏幕高: 屏幕高度
        """
        # 生成起始点（屏幕中心区域）
        起始x = random.randint(屏幕宽 // 3, 屏幕宽 * 2 // 3)
        起始y = random.randint(屏幕高 // 3, 屏幕高 * 2 // 3)
        
        # 生成短距离滑动偏移（10-50像素）
        偏移x = random.randint(-50, 50)
        偏移y = random.randint(-50, 50)
        
        结束x = max(50, min(屏幕宽 - 50, 起始x + 偏移x))
        结束y = max(50, min(屏幕高 - 50, 起始y + 偏移y))
        
        # 随机滑动时间（200-500ms）
        滑动时间 = random.randint(200, 500)
        
        self.写入日志(f"[误触模拟] 随机滑动: ({起始x}, {起始y}) -> ({结束x}, {结束y})")
        self.adb.滑动(起始x, 起始y, 结束x, 结束y, 滑动时间)

    def 随机等待(self, 最小秒=0.5, 最大秒=2.0):
        """
        执行随机等待，模拟人的思考/犹豫时间
        
        参数:
            最小秒: 最小等待时间
            最大秒: 最大等待时间
        """
        等待时间 = random.uniform(最小秒, 最大秒)
        self.写入日志(f"[误触模拟] 随机等待: {等待时间:.2f}秒")
        time.sleep(等待时间)
