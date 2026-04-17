import socketio
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

# 不进入主消息队列的类型：避免被字库匹配、图片库加载等长任务拖住导致截图长时间无响应
_旁路消息类型 = frozenset({"capture_screenshot"})


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
        # 单 worker：与主队列并行的截图通道，内部再用 ADB 锁与设备命令串行
        self._旁路线程池 = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="python-bypass"
        )

        self._客户端 = socketio.Client()
        self._注册事件()
        self._连接服务器()
        self._启动消息处理线程()

    def _注册事件(self):

        @self._客户端.on("python-message")
        def 收到消息(数据):
            if isinstance(数据, dict) and 数据.get("type"):
                类型 = 数据.get("type")
                # 避免打印整包（大图 base64 会拖慢控制台）
                print(f"收到来自 Electron 的消息 type={类型}")
                if 类型 in _旁路消息类型:
                    self._旁路线程池.submit(self._执行旁路消息, 类型, 数据)
                else:
                    self._消息队列.put((类型, 数据))
            else:
                print("忽略无效消息: 需为 dict 且包含 type")

        @self._客户端.on("connect")
        def 连接成功():
            print("连接成功")

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

    def _执行旁路消息(self, 类型, 数据):
        try:
            if self._消息处理回调:
                self._消息处理回调(类型, 数据)
        except Exception as e:
            print(f"旁路消息处理异常 ({类型}): {e}")
            traceback.print_exc()

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

    def 发送到Electron(self, 数据):
        """
        供上层统一调用的发送接口。

        这里简单地以事件名为 channel，把数据原样发给 Electron，
        具体约定可以在前端统一处理。
        """
        try:
            # print("发送数据:", 数据)
            self._客户端.emit("socket-channel", {"cmd": "controller/example/receiveProcessedImage", "args": 数据})
        except Exception as e:
            print(f"发送到Electron 失败: {e}")