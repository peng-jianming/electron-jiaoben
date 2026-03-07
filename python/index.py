"""
群控图色脚本 Python 后端入口
通过 Socket.IO 与 Electron 前端通信
方案 B：Socket 回调只入队，由单独 worker 线程串行处理，与任务管理器锁模型兼容。
"""

import socketio
import threading
from queue import Queue
from 设置 import 服务器地址, 最大线程数
from core.线程控制器 import 线程控制器类
from core.ADB控制器 import ADB控制器类
from core.任务管理器 import 任务管理器类, 发现所有任务模块

class 主程序:
    def __init__(self):
        self._客户端 = None
        self.消息队列 = Queue()
        self.初始化客户端()

    def 初始化客户端(self):
        """初始化 Socket.IO 客户端"""
        if self._客户端 is None:
            self._客户端 = socketio.Client()

            @self._客户端.on("message")
            def 收到消息(数据):
                """只做基本校验并入队，不执行逻辑，避免阻塞 socket 线程。"""
                print(f"收到来自 Electron 的消息: {数据}")
                if isinstance(数据, dict) and 数据.get("类型"):
                    self.消息队列.put((数据.get("类型"), 数据))
                else:
                    print("忽略无效消息: 需为 dict 且包含 类型")

            @self._客户端.on("connect")
            def 连接成功():
                """Socket 连接/重连后，若 worker 已就绪则立即通知前端。"""
                self.发送到Electron("backend-ready", True)

        # 启动 worker 线程，串行处理队列中的 开始/结束/暂停 等
        if not any(t.name == "socket-worker" for t in threading.enumerate()):
            worker = threading.Thread(target=self.客户端消息队列处理, name="socket-worker")
            worker.start()

        if not self._客户端.connected:
            try:
                self._客户端.connect(服务器地址)
                print(f"Socket.IO 客户端已连接到: {服务器地址}")
            except Exception as e:
                print(f"Socket.IO 连接失败: {e}")

    def 客户端消息队列处理(self):
        """单独线程：从队列取消息，按类型串行根据 线程Key 调用 线程控制器的 启动线程/停止线程/暂停线程/恢复线程 。"""
        self.线程控制器 = 线程控制器类(最大线程数量=最大线程数, 回调函数=任务管理器类, 打印回调函数=self.更新数据)
        while True:
            try:
                类型, 数据 = self.消息队列.get()
                任务函数映射 = {
                    "开始任务": self.线程控制器.启动线程,
                    "结束任务": lambda 线程key=None, 任务函数参数集合=None: self.线程控制器.停止线程(线程key),
                    "暂停任务": lambda 线程key=None, 任务函数参数集合=None: self.线程控制器.暂停线程(线程key),
                    "恢复任务": lambda 线程key=None, 任务函数参数集合=None: self.线程控制器.恢复线程(线程key),
                    "获取设备列表": lambda 线程key=None, 任务函数参数集合=None: self.获取设备列表(),
                    "获取任务列表": lambda 线程key=None, 任务函数参数集合=None: self.获取任务列表(),
                }
                设备ID = 数据.get("设备ID")
                数据.update({"更新数据": lambda 字段=None, 数据=None: self.更新数据(设备ID, 字段, 数据) })
                if 类型 in 任务函数映射:
                    任务函数映射[类型](线程key=设备ID, 任务函数参数集合=数据)
                else:
                    print(f"未知消息类型: {类型}")
            except Exception as e:
                print(f"Worker 处理消息异常: {e}")
            finally:
                self.消息队列.task_done()

    def 发送到Electron(self, 前端接收事件名, 数据):
        """向 Electron 发送数据"""
        try:
            data = {
                "cmd": "controller/example/从后端接收数据",
                "args": {"事件名": 前端接收事件名, "数据": 数据},
            }
            self._客户端.emit("socket-channel", data)

        except socketio.exceptions.ConnectionError as e:
            print(f"连接错误: {e}")
            return None
        except Exception as e:
            print(f"发送数据错误: {e}")
            return None

    def 获取设备列表(self):
        adb = ADB控制器类()
        数据列表 = adb.获取设备列表()
        self.发送到Electron("device-list", 数据列表)

    def 获取任务列表(self):
        任务列表 = 发现所有任务模块()
        self.发送到Electron("task-list", list(任务列表.keys()))

    def 更新数据(self, 设备ID, 字段, 数据):
        if 字段 == '日志':
            print(f"设备 {设备ID}: {数据}")
        self.发送到Electron("device-status-update", {
            "设备ID": 设备ID,
            字段: 数据,
        })


if __name__ == "__main__":
    主程序()
