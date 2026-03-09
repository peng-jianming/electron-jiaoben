import socketio
import threading
import traceback
from queue import Queue

class 通信管理器类:
    """
    封装 Socket.IO 客户端连接、事件注册、消息队列处理以及发送到 Electron 前端。

    - 内部维护一个消息队列和工作线程
    - 收到前端 message 时，放入队列，由工作线程调用【消息处理回调】
    - 通过 连接成功回调 在连接建立后通知上层（例如发送 backend-ready）
    """

    def __init__(self, 服务器地址, 消息处理回调):
        self._服务器地址 = 服务器地址
        self._消息处理回调 = 消息处理回调

        self._消息队列 = Queue()

        self._客户端 = socketio.Client()
        self._注册事件()
        self._连接服务器()
        self._启动消息处理线程()

    def _注册事件(self):
        @self._客户端.on("message")
        def 收到消息(数据):
            print(f"收到来自 Electron 的消息: {数据}")
            if isinstance(数据, dict) and 数据.get("类型"):
                self._消息队列.put((数据.get("类型"), 数据))
            else:
                print("忽略无效消息: 需为 dict 且包含 类型")

        @self._客户端.on("connect")
        def 连接成功():
            self.发送到Electron("backend-ready", True)

    def _启动消息处理线程(self):
        """启动后台工作线程，按顺序处理消息队列。"""
        if any(t.name == "socket-worker" for t in threading.enumerate()):
            return
        worker = threading.Thread(target=self._消息队列处理, name="socket-worker")
        worker.start()

    def _消息队列处理(self):
        while True:
            try:
                类型, 数据 = self._消息队列.get()
                if self._消息处理回调:
                    self._消息处理回调(类型, 数据)
                else:
                    print("未设置消息处理回调，丢弃消息")
            except Exception as e:
                print(f"Worker 处理消息异常: {e}")
                traceback.print_exc()
            finally:
                self._消息队列.task_done()

    def _连接服务器(self):
        if self._客户端.connected:
            return
        try:
            self._客户端.connect(self._服务器地址)
            print(f"Socket.IO 客户端已连接到: {self._服务器地址}")
        except Exception as e:
            print(f"Socket.IO 连接失败: {e}")

    def 发送原始(self, 事件名, 数据):
        """向前端发送原始 Socket.IO 消息。"""
        try:
            self._客户端.emit(事件名, 数据)
        except Exception as e:
            print(f"发送 Socket 数据错误: {e}")

    def 发送到Electron(self, 前端接收事件名, 数据):
        """封装统一的数据格式并通过 socket-channel 发送到 Electron。"""
        payload = {
            "cmd": "controller/example/从后端接收数据",
            "args": {"事件名": 前端接收事件名, "数据": 数据},
        }
        self.发送原始("socket-channel", payload)

