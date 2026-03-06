import ctypes
import threading
import time
from ctypes import wintypes
kernel32 = ctypes.windll.kernel32

class ConsoleColors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'


def printDebug(_string: str):
    print(ConsoleColors.GREEN + _string + ConsoleColors.RESET)

class PyThread(threading.Thread):

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, *, daemon=True):
        super().__init__(group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)
        self._pause_state = False  # 线程暂停状态

    def pause(self):
        if self.is_alive():
            thread_handle = self._get_handle()  # 打开线程获取句柄
            kernel32.SuspendThread(thread_handle)
            kernel32.CloseHandle(thread_handle)  # 关闭句柄，并不是关闭线程
            printDebug(f"已暂停线程{self.ident}")
            self._pause_state = True
        else:
            printDebug(f"线程不存在或者已暂停,无需暂停线程{self.ident}")

    def resume(self):
        if self._pause_state:
            thread_handle = self._get_handle()
            kernel32.ResumeThread(thread_handle)
            kernel32.CloseHandle(thread_handle)
            self._pause_state = False
            printDebug(f"已恢复线程{self.ident}")
        else:
            printDebug(f"线程不存在或者运行中，无需恢复{self.ident}")

    def stop(self):
        if not self.is_alive():
            printDebug(f"线程已停止,无法再次停止{self.ident}")
            return
        exc = ctypes.py_object(SystemExit)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.ident), exc)
        time.sleep(0.01)
        if res == 0:
            raise ValueError("找不到线程ID")
        elif res == 1:
            printDebug(f"停止线程{self.ident}")
            self._is_stopped = True
        elif res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, None)
            raise SystemError("线程已停止")
        time.sleep(0.1)

    def TerminateThread(self):
        handle = self._get_handle()
        kernel32.TerminateThread(handle, 0)
        if self.__waitforsingleobject():
            kernel32.CloseHandle(handle)  # 关闭句柄，并不是关闭线程
            self._is_stopped = True
            printDebug(f"已杀死线程:{self.ident}")
        else:
            printDebug(f"杀死线程失败:{self.ident}")

    def _get_handle(self):
        handle = kernel32.OpenThread(ctypes.c_ulong(0x1 | 0x2), ctypes.c_bool(False), ctypes.c_ulong(self.ident))
        return handle

    def __thread_state(self):
        state_id = wintypes.DWORD()
        handle = self._get_handle()
        if ctypes.windll.kernel32.GetExitCodeThread(handle, ctypes.byref(state_id)):
            return state_id.value
        return 0

    def __waitforsingleobject(self):
        self.__WaitForSingleObject = ctypes.windll.kernel32.WaitForSingleObject
        self.__WaitForSingleObject.argtypes = wintypes.HANDLE, wintypes.DWORD
        self.__WaitForSingleObject.restype = wintypes.DWORD
        self.__WaitForSingleObject(self._get_handle(), 1000)  # 等待线程关闭
        if self.__thread_state() == 0:  # 确认退出
            return True




if __name__ == "__main__":
    def worker():
        i = 0
        while True:
            printDebug(f"工作中：{i}")
            i += 1
            time.sleep(1)

    def demo_pythread():
        t = PyThread(target=worker, name="demo-thread")
        t2 = PyThread(target=worker, name="demo-thread")
        t3 = PyThread(target=worker, name="demo-thread")
        t.start()              # 启动线程
        t2.start()              # 启动线程
        t3.start()              # 启动线程
        time.sleep(6)

        t.pause()              # 暂停
        time.sleep(3)

        t.resume()             # 恢复
        time.sleep(3)

        t.stop()               # 正常停止（抛 SystemExit 让线程退出）
        # 或者：t.TerminateThread()  # 强制杀死（不建议常用）


    demo_pythread()