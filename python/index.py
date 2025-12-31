import socketio
from task_manager import get_task_manager

# Socket.IO 客户端实例
_client = None


def start(data):
    """
    启动任务队列（按顺序执行多个任务）
    
    消息格式:
    {
        "type": "start",
        "device_id": "设备ID",
        "task_queue": ["shimen", "baotu"]  // 任务类型列表，即使只有一个任务也用列表格式，如 ["shimen"]
    }
    """
    device_id = data.get("device_id")
    task_queue = data.get("task_queue")
    
    if not device_id:
        print("错误: 缺少 device_id")
        return
    
    if not isinstance(task_queue, list) or not task_queue:
        print("错误: task_queue 必须是非空列表")
        return
    
    success = get_task_manager().start_task_queue(device_id, task_queue)
    status = "成功" if success else "失败"
    print(f"{status}启动任务队列: 设备={device_id}, 队列={task_queue}")


def stop(data):
    """
    停止任务队列
    
    消息格式:
    {
        "type": "stop",
        "device_id": "设备ID"
    }
    注意: 停止操作会停止该设备的所有任务（包括整个任务队列）
    """
    device_id = data.get("device_id")
    if not device_id:
        print("错误: 缺少 device_id")
        return
    
    success = get_task_manager().stop_task(device_id)
    status = "成功停止" if success else "停止失败"
    print(f"{status}设备的所有任务: 设备={device_id}")


def init_client(url="http://127.0.0.1:7070"):
    """初始化 Socket.IO 客户端"""
    global _client
    if _client is None:
        _client = socketio.Client()

        @_client.on("python-message")
        def on_message(data):
            print(f"收到来自 Electron 的消息: {data}")
            if isinstance(data, dict):
                handler = {"start": start, "stop": stop}.get(data.get("type"))
                if handler:
                    handler(data)

    if not _client.connected:
        try:
            _client.connect(url)
            print(f"Socket.IO 客户端已连接到: {url}")
        except Exception as e:
            print(f"Socket.IO 连接失败: {e}")

    return _client


if __name__ == "__main__":
    init_client()
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n程序退出")