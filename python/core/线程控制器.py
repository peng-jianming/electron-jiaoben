import threading
import time
# import time
from .自定义线程 import PyThread

class 线程控制器类:
    """
    线程控制器，最好是统一使用同一个实例，当循环滚号时不会出错。
    """
    lock = threading.Lock()

    def __init__(self, 回调函数, 最大线程数量=999, 线程结束后回调函数=None, 打印回调函数=None, 所有线程结束后回调函数=None):
        """
        :param thread_max_num:最大线程数量
        :param 回调函数:回调函数，回调自动填写参数num
        :param 线程结束后回调函数:调用停止线程后，在回调清理函数，回调自动填写参数num
        :param 打印回调函数: 是否指定打印回调函数，默认为print，指定则需要有两个参数:线程key,content
        """
        self.线程集合 = {}  # {线程key:线程对象}
        self._批量启动线程对象 = None  # 批量启动线程对象

        self.最大线程数 = 最大线程数量  # 最大线程数量
        self.回调函数 = 回调函数  # 回调函数，参数必须为num
        if 线程结束后回调函数 is None:
            self.线程结束后回调函数 = lambda 线程key: None
        else:
            self.线程结束后回调函数 = 线程结束后回调函数
        if 打印回调函数 is None:
            self.打印回调函数 = print
        else:
            self.打印回调函数 = 打印回调函数
        if 所有线程结束后回调函数 is None:
            self.所有线程结束后回调函数 = lambda: None
        else:
            self.所有线程结束后回调函数 = 所有线程结束后回调函数

    def 设置最大线程数(self, 最大线程数):
        """设置最大线程数量"""
        self.最大线程数 = 最大线程数

    def _执行线程(self, func, 线程key, 任务函数参数集合):
        func(任务函数参数集合)
        if self.线程集合.pop(线程key, None) is not None:
            self.线程结束后回调函数(线程key)

    def 获取线程(self, 线程key):
        """获取线程对象"""
        return self.线程集合.get(线程key)

    def 启动线程(self, 线程key, 任务函数参数集合):
        """
        :param 线程key: 可以是表格行号，也可以是模拟器ID，只需要一个不重复的序号即可
        :return:
            0:无法启动线程，当前线程已达到最大数量，
            1:线程运行中，
            2:线程启动成功
        """
        当前线程数量 = len(self.线程集合)
        if 当前线程数量 >= self.最大线程数:
            self.打印回调函数(线程key, "日志", f"无法启动线程，当前线程已达到最大数量:{self.最大线程数}")
            return 0
        线程对象 = self.线程集合.get(线程key)

        if 线程对象 and 线程对象.is_alive():
            self.打印回调函数(线程key, "日志", f"线程运行中")
            return 1
        else:
            self.打印回调函数(线程key, "日志", f"线程启动")
            self.线程集合[线程key] = PyThread(target=self._执行线程, args=(self.回调函数, 线程key, 任务函数参数集合))
            self.线程集合[线程key].start()
            return 2

    def 停止线程(self, 线程key):
        """
        :param 线程key: 可以是表格行号，也可以是模拟器ID，只需要一个不重复的序号即可
        :return:
            0:无法停止线程，当前线程不存在，
            1:线程已经停止
        """
        线程对象 = self.线程集合.get(线程key)
        if 线程对象 and 线程对象.is_alive():
            if getattr(线程对象, '_pause_state', False):
                线程对象.resume()
            线程对象.TerminateThread()
            if self.lock.locked():  # 解锁,防止死锁
                self.lock.release()
            self.打印回调函数(线程key, "日志", f"线程停止")
            if 线程对象.is_alive():
                self.打印回调函数(线程key, "日志", f"线程停止失败，强制清理状态")
            self.线程集合.pop(线程key, None)
            self.线程结束后回调函数(线程key)
            return 1
        else:
            self.打印回调函数(线程key, "日志", "线程不存在")
            self.线程集合.pop(线程key, None)
            return 0

    def 暂停线程(self, 线程key):
        线程对象 = self.线程集合.get(线程key)
        if 线程对象 and 线程对象.is_alive():
            线程对象.pause()
            self.打印回调函数(线程key, "日志", "线程暂停")
            return 1
        else:
            self.打印回调函数(线程key, "日志", f"无法暂停线程，当前线程不存在")
            return 0

    def 恢复线程(self, 线程key):
        线程对象 = self.线程集合.get(线程key)
        if 线程对象 and 线程对象.is_alive():
            线程对象.resume()
            self.打印回调函数(线程key, "日志", f"线程恢复")
            return 1
        else:
            self.打印回调函数(线程key, "日志", f"无法恢复线程，当前线程不存在")
            return 0

    def _批量启动(self, 线程编号列表, 间隔秒数):
        """
        0:
        1:
        2:
        :param 线程编号列表:
        :param 间隔秒数:
        :return:
        """
        已等待秒数 = 0

        def 延迟并更新状态(起始索引, 已等待秒数):
            for _ in range(间隔秒数):
                time.sleep(1)
                已等待秒数 += 1
                # 更新剩余线程待启动状态
                for 线程编号 in 线程编号列表[起始索引:]:
                    self.打印回调函数(线程编号, f"待%d启动" % (线程编号 * 间隔秒数 - 已等待秒数,))
            return 已等待秒数
        # 先更新线程待启动状态

        for 线程编号 in 线程编号列表:
            self.打印回调函数(线程编号, f"待%d启动" % (线程编号 * 间隔秒数,))
        for 索引, 线程编号 in enumerate(线程编号列表):
            res = self.启动线程(线程编号)
            if res == 0:  # 无法启动线程，当前线程已达到最大数量,直接阻塞并等待
                self.打印回调函数(线程编号, f"当前线程已达到最大数量:{self.最大线程数},线程等待中...")
                while True:
                    time.sleep(1)
                    if len(self.线程集合) < self.最大线程数:
                        break
                self.启动线程(线程编号)
                已等待秒数 = 延迟并更新状态(索引, 已等待秒数)
            elif res == 1:  # 线程运行中,直接忽略
                continue
            elif res == 2:  # 线程启动成功
                if 索引 + 1 >= len(线程编号列表):
                    break
                已等待秒数 = 延迟并更新状态(索引 + 1, 已等待秒数)
                continue
            else:
                raise f"_start_all 未知错误res"
        # 等线程全部执行完成，在回调函数
        while True:
            time.sleep(0.1)
            if not len(self.线程集合):
                break
        # 回调函数
        self.所有线程结束后回调函数()

    def 批量启动线程(self, 线程编号列表, 间隔秒数):
        if self._批量启动线程对象 and self._批量启动线程对象.is_alive():
            self.打印回调函数(线程编号列表[0], "正在批量启动线程，请勿重复操作")
            return 0
        else:
            self._批量启动线程对象 = PyThread(target=self._批量启动, args=(线程编号列表, 间隔秒数))
            self._批量启动线程对象.start()
            self.打印回调函数(线程编号列表[0], "批量启动线程启动")
            return 1

    def 停止全部线程(self):
        if self._批量启动线程对象 and self._批量启动线程对象.is_alive():
            self._批量启动线程对象.stop()
            self._批量启动线程对象 = None
            print("停止滚号线程")
        # 停止线程（用快照避免与任务线程并发 pop 时出现空集合竞态）
        while True:
            编号列表 = list(self.线程集合.keys())
            if not 编号列表:
                break
            self.停止线程(编号列表[0])
        return 1

    def 暂停全部线程(self):
        for 编号 in list(self.线程集合.keys()):
            self.暂停线程(编号)

    def 恢复全部线程(self):
        for 编号 in list(self.线程集合.keys()):
            self.恢复线程(编号)
