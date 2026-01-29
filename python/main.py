"""
群控图色脚本 Python 后端入口
通过 Socket.IO 与 Electron 前端通信
"""
import socketio
import time
from 任务 import 获取任务管理器
from 配置.设置 import 服务器地址

# Socket.IO 客户端实例
_客户端 = None


def 启动任务(数据):
    """
    启动任务队列（按顺序执行多个任务）

    消息格式:
    {
        "type": "start",
        "device_id": "设备ID",
        "task_queue": ["shimen", "baotu"]  // 任务类型列表
    }
    """
    设备ID = 数据.get("device_id")
    任务队列 = 数据.get("task_queue")

    if not 设备ID:
        print("错误: 缺少 device_id")
        return

    if not isinstance(任务队列, list) or not 任务队列:
        print("错误: task_queue 必须是非空列表")
        return

    成功 = 获取任务管理器().启动任务队列(设备ID, 任务队列)
    状态 = "成功" if 成功 else "失败"
    print(f"{状态}启动任务队列: 设备={设备ID}, 队列={任务队列}")


def 停止任务(数据):
    """
    停止任务队列

    消息格式:
    {
        "type": "stop",
        "device_id": "设备ID"
    }
    """
    设备ID = 数据.get("device_id")
    if not 设备ID:
        print("错误: 缺少 device_id")
        return

    成功 = 获取任务管理器().停止任务(设备ID)
    状态 = "成功停止" if 成功 else "停止失败"
    print(f"{状态}设备的所有任务: 设备={设备ID}")


def 初始化客户端(url=None):
    """初始化 Socket.IO 客户端"""
    global _客户端
    url = url or 服务器地址

    if _客户端 is None:
        _客户端 = socketio.Client()

        @_客户端.on("python-message")
        def 收到消息(数据):
            print(f"收到来自 Electron 的消息: {数据}")
            if isinstance(数据, dict):
                处理函数 = {"start": 启动任务, "stop": 停止任务}.get(数据.get("type"))
                if 处理函数:
                    处理函数(数据)

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
