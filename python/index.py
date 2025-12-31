import socketio
from task_manager import get_task_manager

# Socket.IO 客户端实例
_client = None


def start(data):
    """
    启动任务
    
    消息格式:
    {
        "type": "start",
        "device_id": "设备ID",
        "task_type": "baotu" 或 "shimen"
    }
    """
    device_id = data.get("device_id")
    task_type = data.get("task_type")
    
    if not device_id:
        print("错误: 缺少 device_id")
        return
    
    if not task_type:
        print("错误: 缺少 task_type")
        return
    
    task_manager = get_task_manager()
    success = task_manager.start_task(device_id, task_type)
    
    if success:
        print(f"成功启动任务: 设备={device_id}, 类型={task_type}")
    else:
        print(f"启动任务失败: 设备={device_id}, 类型={task_type}")


def stop(data):
    """
    停止任务
    
    消息格式:
    {
        "type": "stop",
        "device_id": "设备ID",
        "task_type": "baotu" 或 "shimen" (可选，如果不提供则停止该设备的所有任务)
    }
    """
    device_id = data.get("device_id")
    task_type = data.get("task_type")  # 可选
    
    if not device_id:
        print("错误: 缺少 device_id")
        return
    
    task_manager = get_task_manager()
    success = task_manager.stop_task(device_id, task_type)
    
    if success:
        if task_type:
            print(f"成功停止任务: 设备={device_id}, 类型={task_type}")
        else:
            print(f"成功停止设备的所有任务: 设备={device_id}")
    else:
        print(f"停止任务失败: 设备={device_id}, 类型={task_type}")


def init_client(url="http://127.0.0.1:7070"):
    """初始化 Socket.IO 客户端"""
    global _client
    if _client is None:
        _client = socketio.Client()

        @_client.on("python-message")
        def on_message(data):
            print(f"收到来自 Electron 的消息: {data}")
            if not isinstance(data, dict):
                return

            handlers = {
                "start": start,
                "stop": stop,
            }
            
            handler = handlers.get(data.get("type"))
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
    # 保持程序运行
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n程序退出")