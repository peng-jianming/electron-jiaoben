"""
群控图色脚本 Python 后端入口
通过 Socket.IO 与 Electron 前端通信
"""

import socketio
import time
from 任务 import 获取任务管理器
from 配置.设置 import 服务器地址
from 核心.ADB控制器 import ADB控制器类

# Socket.IO 客户端实例
_客户端 = None


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


def 获取设备列表(数据):
    adb = ADB控制器类()
    数据列表 = adb.获取设备列表()
    发送到Electron("device-list", 数据列表)


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
            print(f"收到来自 Electron 的消息: {数据}")
            if isinstance(数据, dict):
                处理函数 = {
                    "开始任务": 开始任务,
                    "结束任务": 结束任务,
                    "获取设备列表": 获取设备列表,
                }.get(数据.get("类型"))
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
