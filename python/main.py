"""
群控图色脚本 Python 后端入口
通过 Socket.IO 与 Electron 前端通信
方案 B：Socket 回调只入队，由单独 worker 线程串行处理，与任务管理器锁模型兼容。
"""

import socketio
import time
import threading
from queue import Queue
from core.任务管理器 import 获取任务管理器, 发现所有任务模块
from 设置 import 服务器地址
from core.ADB控制器 import ADB控制器类


# Socket.IO 客户端实例
_客户端 = None

# 消息队列：Socket 回调只入队，worker 线程从中取消息串行处理
_消息队列 = Queue()


def 开始任务(数据):
    """
    启动任务队列（按顺序执行多个任务）

    消息格式:
    {
        "类型": "开始",
        "设备": "设备",
        "任务队列": ["shimen", "baotu"]  // 任务类型列表
    }
    """
    设备ID = 数据.get("设备ID")
    任务队列 = 数据.get("任务队列")

    if not 设备ID:
        print("错误: 缺少 设备ID 参数")
        return

    if not isinstance(任务队列, list) or not 任务队列:
        print("错误: 任务队列 必须是非空列表")
        return

    成功 = 获取任务管理器().启动任务队列(设备ID, 任务队列)
    状态 = "成功" if 成功 else "失败"
    print(f"{状态}启动任务队列: 设备={设备ID}, 队列={任务队列}")


def 结束任务(数据):
    """
    结束任务队列

    消息格式:
    {
        "类型": "结束",
        "设备ID": "设备ID"
    }
    """
    设备ID = 数据.get("设备ID")
    if not 设备ID:
        print("错误: 缺少 设备ID")
        return

    成功 = 获取任务管理器().结束任务(设备ID)
    状态 = "成功结束" if 成功 else "结束失败"
    print(f"{状态}设备的所有任务: 设备={设备ID}")


def 暂停任务(数据):
    """
    暂停任务

    消息格式:
    {
        "类型": "暂停任务",
        "设备ID": "设备ID"
    }
    """
    设备ID = 数据.get("设备ID")
    if not 设备ID:
        print("错误: 缺少 设备ID")
        return

    成功 = 获取任务管理器().暂停任务(设备ID)
    状态 = "成功暂停" if 成功 else "暂停失败"
    print(f"{状态}设备任务: 设备={设备ID}")


def 恢复任务(数据):
    """
    恢复任务

    消息格式:
    {
        "类型": "恢复任务",
        "设备ID": "设备ID"
    }
    """
    设备ID = 数据.get("设备ID")
    if not 设备ID:
        print("错误: 缺少 设备ID")
        return

    成功 = 获取任务管理器().恢复任务(设备ID)
    状态 = "成功恢复" if 成功 else "恢复失败"
    print(f"{状态}设备任务: 设备={设备ID}")


def 获取设备列表(数据):
    adb = ADB控制器类()
    数据列表 = adb.获取设备列表()
    发送到Electron("device-list", 数据列表)


def 获取任务列表(数据):
    任务列表 = 发现所有任务模块()
    发送到Electron("task-list", list(任务列表.keys()))


# 类型 -> 处理函数（供 worker 使用，定义于所有处理函数之后）
_类型到处理函数 = {
    "开始任务": 开始任务,
    "结束任务": 结束任务,
    "暂停任务": 暂停任务,
    "恢复任务": 恢复任务,
    "获取设备列表": 获取设备列表,
    "获取任务列表": 获取任务列表,
}


def _worker_循环():
    """单独线程：从队列取消息，按类型串行调用 开始/结束/暂停 等，与任务管理器锁兼容。"""
    while True:
        try:
            类型, 数据 = _消息队列.get()
            if 类型 is None:  # 可选的退出哨兵
                break
            处理函数 = _类型到处理函数.get(类型)
            if 处理函数:
                处理函数(数据)
            else:
                print(f"未知消息类型: {类型}")
        except Exception as e:
            print(f"Worker 处理消息异常: {e}")
        finally:
            _消息队列.task_done()


def 发送到Electron(前端接收事件名, 数据):
    """向 Electron 发送数据"""
    try:
        global _客户端
        data = {
            "cmd": "controller/example/从后端接收数据",
            "args": {"事件名": 前端接收事件名, "数据": 数据},
        }
        _客户端.emit("socket-channel", data)

    except socketio.exceptions.ConnectionError as e:
        print(f"连接错误: {e}")
        return None
    except Exception as e:
        print(f"发送数据错误: {e}")
        return None


def 初始化客户端(url=None):
    """初始化 Socket.IO 客户端"""
    global _客户端
    url = url or 服务器地址

    if _客户端 is None:
        _客户端 = socketio.Client()

        @_客户端.on("message")
        def 收到消息(数据):
            """只做基本校验并入队，不执行逻辑，避免阻塞 socket 线程。"""
            print(f"收到来自 Electron 的消息: {数据}")
            if isinstance(数据, dict) and 数据.get("类型"):
                _消息队列.put((数据.get("类型"), 数据))
            else:
                print("忽略无效消息: 需为 dict 且包含 类型")

    # 启动 worker 线程，串行处理队列中的 开始/结束/暂停 等
    if not any(t.name == "socket-worker" for t in threading.enumerate()):
        _worker = threading.Thread(target=_worker_循环, name="socket-worker", daemon=True)
        _worker.start()

    if not _客户端.connected:
        try:
            _客户端.connect(url)
            print(f"Socket.IO 客户端已连接到: {url}")
        except Exception as e:
            print(f"Socket.IO 连接失败: {e}")

    return _客户端


if __name__ == "__main__":
    初始化客户端()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n程序退出")
