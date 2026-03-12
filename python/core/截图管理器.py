"""
截图管理器 - 同一轮次复用截图
"""
import time
from 设置 import 调试耗时


class 截图管理器类:
    """截图上下文管理器，同一轮次复用截图"""

    def __init__(self, 控制器):
        """
        初始化截图管理器

        参数:
            控制器: 设备控制器实例
        """
        self._控制器 = 控制器
        self._当前截图 = None

    def 新轮次(self):
        """开始新一轮检测，清除缓存的截图"""
        self._当前截图 = None

    def 获取截图(self):
        """懒加载截图，同轮次内复用"""
        if self._当前截图 is None:
            if 调试耗时:
                开始 = time.perf_counter()
            self._当前截图 = self._控制器.截图到内存()
            if 调试耗时:
                耗时 = (time.perf_counter() - 开始) * 1000
                print(f"[耗时] 截图: {耗时:.0f}ms")
        return self._当前截图
