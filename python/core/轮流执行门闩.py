"""
多账号任务线程之间的「单执行」轮流门闩：同一时刻仅一个线程跑状态机的一整轮，
下一轮交给列表中的下一个账号，避免多窗口键鼠/前台操作争抢。

使用前由 任务管理器.运行 在账号线程内 注册；结束或线程停止时 注销（可重复调用）。
"""

import threading

from 设置 import 启用轮流单执行


class 轮流执行门闩类:
    def __init__(self):
        self._条件变量 = threading.Condition(threading.Lock())
        self._参与者列表: list = []
        self._轮到索引 = 0

    def 注册(self, 键):
        if not 启用轮流单执行 or 键 is None:
            return
        with self._条件变量:
            if 键 not in self._参与者列表:
                self._参与者列表.append(键)
            self._条件变量.notify_all()

    def 注销(self, 键):
        if not 启用轮流单执行 or 键 is None:
            return
        with self._条件变量:
            if 键 not in self._参与者列表:
                return
            索引 = self._参与者列表.index(键)
            人数 = len(self._参与者列表)
            持权位置 = self._轮到索引 % 人数
            self._参与者列表.pop(索引)
            剩余人数 = len(self._参与者列表)
            if 剩余人数 == 0:
                self._轮到索引 = 0
            else:
                if 索引 < 持权位置:
                    self._轮到索引 -= 1
                self._轮到索引 %= 剩余人数
            self._条件变量.notify_all()

    def 等待轮到(self, 键):
        if not 启用轮流单执行 or 键 is None:
            return
        with self._条件变量:
            if 键 not in self._参与者列表:
                return
            while True:
                人数 = len(self._参与者列表)
                if 人数 <= 1:
                    return
                当前键 = self._参与者列表[self._轮到索引 % 人数]
                if 当前键 == 键:
                    return
                self._条件变量.wait(timeout=0.05)

    def 结束本轮让出(self, 键):
        if not 启用轮流单执行 or 键 is None:
            return
        with self._条件变量:
            人数 = len(self._参与者列表)
            if 人数 <= 1:
                return
            当前键 = self._参与者列表[self._轮到索引 % 人数]
            if 当前键 != 键:
                return
            self._轮到索引 = (self._轮到索引 + 1) % 人数
            self._条件变量.notify_all()


全局轮流门闩 = 轮流执行门闩类()
