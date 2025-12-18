import socketio
import time

# Socket.IO 客户端实例
_client = None

def send_to_electron(prop, message, method='controller/example/hello', url='http://127.0.0.1:7070'):
    """
    向 Electron 发送数据
    
    参数:
        prop: 修改字段名
        message: 修改字段的值
        method: 控制器方法路径，默认为 'controller/example/hello'
        url: Socket.IO 服务器地址，默认为 'http://127.0.0.1:7070'
    
    返回:
        response: Electron 返回的响应数据
    """
    try:
        global _client
        if _client is None:
            _client = socketio.Client()

        client = _client
        
        # 如果未连接，则连接
        if not client.connected:
            client.connect(url)
        
        # 通信频道固定为 'socket-channel'
        channel = 'socket-channel'
        
        # 构建发送数据：{prop, message}
        params = {
            'prop': prop,
            'message': message
        }
        
        # 发送数据格式：{ cmd: method, args: ... }
        # 注意：electron-egg 框架期望的是 'args' 而不是 'params'
        data = {
            'cmd': method,
            'args': params
        }
        
        # 使用 emit 发送数据，通过回调接收响应
        # python-socketio 的 emit 方法支持 callback 参数
        response_data = None
        response_received = False
        
        def callback(*args):
            nonlocal response_data, response_received
            # 回调可能接收多个参数，取第一个作为响应数据
            response_data = args[0] if args else None
            response_received = True
        
        client.emit(channel, data, callback=callback)
        
        # 等待响应（最多等待10秒）
        timeout = 10
        start_time = time.time()
        while not response_received and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if not response_received:
            print("等待响应超时")
            return None
        
        return response_data
        
    except socketio.exceptions.ConnectionError as e:
        print(f"连接错误: {e}")
        return None
    except Exception as e:
        print(f"发送数据错误: {e}")
        return None



if __name__ == "__main__":
    send_to_electron("test", "hello")