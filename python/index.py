import socketio
import time
import cv2
import numpy as np
import base64
import os
import traceback
import threading

# Socket.IO 客户端实例
_client = None

# 存储当前加载的图像（numpy 数组格式）
_current_image = None  # 原图
_current_image_filtered = None  # 颜色过滤后的图像
_current_image_binary = None  # 二值化后的图像


def handle_upload_image(data):
    """
    处理图像上传请求（首次上传时调用）

    参数:
        data: 包含图像路径的数据字典
            - path: 图像文件的路径
    """
    global _current_image, _current_image_filtered

    try:
        image_path = data.get("path")

        if not image_path:
            print("错误: 未提供图像路径")
            send_image_result(error="未提供图像路径")
            return

        # 验证文件是否存在
        if not os.path.exists(image_path):
            print(f"错误: 图像文件不存在: {image_path}")
            send_image_result(error=f"图像文件不存在: {image_path}")
            return

        # 使用 numpy 读取文件内容，然后用 OpenCV 解码
        # 这样可以避免 OpenCV 无法读取包含中文字符路径的问题
        try:
            # 以二进制模式读取文件
            with open(image_path, "rb") as f:
                image_data = f.read()

            # 将字节数据转换为 numpy 数组
            nparr = np.frombuffer(image_data, np.uint8)

            # 使用 OpenCV 解码图像
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        except Exception as e:
            print(f"读取图像文件时出错: {e}")
            send_image_result(error=f"读取图像文件时出错: {str(e)}")
            return

        if img is None:
            print(f"错误: 无法解码图像文件: {image_path}")
            send_image_result(error=f"无法解码图像文件: {image_path}")
            return

        # 保存图像到全局变量（清除之前的过滤结果）
        _current_image = img
        _current_image_filtered = None

        print(f"图像已从路径加载到内存: {image_path}")

        # 发送原图回 Electron
        send_image_result(processed_image=img)

    except Exception as e:
        print(f"上传图像时出错: {e}")
        traceback.print_exc()
        send_image_result(error=str(e))


def parse_color_filter(color_str):
    """
    解析颜色过滤字符串
    格式: '191919-203040' 或 '191919'
    返回: (base_color_bgr, tolerance_bgr) 或 None
    """
    try:
        if "-" in color_str:
            base_hex, tolerance_hex = color_str.split("-", 1)
        else:
            base_hex = color_str
            tolerance_hex = "000000"

        # 解析基础颜色（RGB格式，需要转换为BGR）
        if len(base_hex) != 6:
            return None

        base_r = int(base_hex[0:2], 16)
        base_g = int(base_hex[2:4], 16)
        base_b = int(base_hex[4:6], 16)
        base_color_bgr = (base_b, base_g, base_r)  # OpenCV使用BGR格式

        # 解析色偏（RGB格式，需要转换为BGR）
        if len(tolerance_hex) != 6:
            tolerance_bgr = (0, 0, 0)
        else:
            tolerance_r = int(tolerance_hex[0:2], 16)
            tolerance_g = int(tolerance_hex[2:4], 16)
            tolerance_b = int(tolerance_hex[4:6], 16)
            tolerance_bgr = (tolerance_b, tolerance_g, tolerance_r)  # OpenCV使用BGR格式

        return (base_color_bgr, tolerance_bgr)
    except Exception as e:
        print(f"解析颜色过滤字符串失败: {color_str}, 错误: {e}")
        return None


def apply_color_filter_to_image(img, keep_colors, filter_colors):
    """
    对图像应用颜色过滤

    参数:
        img: 输入图像（BGR格式）
        keep_colors: 保留的颜色列表，格式 ['191919-203040', ...]
        filter_colors: 过滤的颜色列表，格式 ['191919-203040', ...]

    返回:
        过滤后的图像
    """
    if img is None:
        return None

    result = img.copy()
    mask = np.ones((img.shape[0], img.shape[1]), dtype=np.uint8) * 255

    # 处理保留颜色：创建保留颜色的掩码
    if keep_colors:
        keep_mask = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
        for color_str in keep_colors:
            color_info = parse_color_filter(color_str)
            if color_info:
                base_color, tolerance = color_info
                lower = np.array(
                    [
                        max(0, base_color[0] - tolerance[0]),
                        max(0, base_color[1] - tolerance[1]),
                        max(0, base_color[2] - tolerance[2]),
                    ]
                )
                upper = np.array(
                    [
                        min(255, base_color[0] + tolerance[0]),
                        min(255, base_color[1] + tolerance[1]),
                        min(255, base_color[2] + tolerance[2]),
                    ]
                )
                color_mask = cv2.inRange(img, lower, upper)
                keep_mask = cv2.bitwise_or(keep_mask, color_mask)

        # 只保留指定颜色的区域
        mask = cv2.bitwise_and(mask, keep_mask)

    # 处理过滤颜色：从掩码中移除这些颜色
    if filter_colors:
        for color_str in filter_colors:
            color_info = parse_color_filter(color_str)
            if color_info:
                base_color, tolerance = color_info
                lower = np.array(
                    [
                        max(0, base_color[0] - tolerance[0]),
                        max(0, base_color[1] - tolerance[1]),
                        max(0, base_color[2] - tolerance[2]),
                    ]
                )
                upper = np.array(
                    [
                        min(255, base_color[0] + tolerance[0]),
                        min(255, base_color[1] + tolerance[1]),
                        min(255, base_color[2] + tolerance[2]),
                    ]
                )
                filter_mask = cv2.inRange(img, lower, upper)
                # 将过滤颜色的区域设为0（黑色）
                mask = cv2.bitwise_and(mask, cv2.bitwise_not(filter_mask))

    # 应用掩码：将不保留的区域设为黑色
    result = cv2.bitwise_and(result, result, mask=mask)

    return result


def handle_process_image(data):
    """
    统一的图像处理函数，按照流程处理：颜色过滤 -> 二值化

    参数:
        data: 包含处理参数的数据字典
            - enableColorFilter: 是否启用颜色过滤
            - keepColors: 保留的颜色列表（当启用颜色过滤时）
            - filterColors: 过滤的颜色列表（当启用颜色过滤时）
            - enableBinary: 是否启用二值化
            - threshold: 二值化阈值（当启用二值化时）
    """
    global _current_image, _current_image_filtered, _current_image_binary

    try:
        if _current_image is None:
            print("错误: 未加载图像，请先上传图像")
            send_image_result(error="未加载图像，请先上传图像")
            return

        source_image = _current_image  # 从原图开始

        # 步骤1: 处理颜色过滤
        enable_color_filter = data.get("enableColorFilter", False)

        if enable_color_filter:
            keep_colors = data.get("keepColors", [])
            filter_colors = data.get("filterColors", [])

            # 只有当有有效颜色时才应用过滤
            if keep_colors or filter_colors:
                filtered_img = apply_color_filter_to_image(
                    _current_image, keep_colors, filter_colors
                )

                if filtered_img is None:
                    print("错误: 颜色过滤失败")
                    send_image_result(error="颜色过滤失败")
                    return

                source_image = filtered_img
                _current_image_filtered = filtered_img

                print(f"颜色过滤完成，保留: {keep_colors}, 过滤: {filter_colors}")
            else:
                # 启用了但没有效颜色，清除过滤
                _current_image_filtered = None
        else:
            _current_image_filtered = None

        # 步骤2: 处理二值化
        enable_binary = data.get("enableBinary", False)

        if enable_binary:
            threshold_value = data.get("threshold", 127)

            # 使用当前源图像进行二值化
            source_gray = cv2.cvtColor(source_image, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(
                source_gray, threshold_value, 255, cv2.THRESH_BINARY
            )
            source_image = binary
            _current_image_binary = binary
            print(f"二值化处理完成，阈值: {threshold_value}")
        else:
            # 未启用二值化，发送当前源图像（原图或过滤后的图）
            _current_image_binary = None
            print("图像处理完成（无二值化）")

        send_image_result(processed_image=source_image)
    except Exception as e:
        print(f"处理图像时出错: {e}")
        traceback.print_exc()
        send_image_result(error=str(e))


def flood_fill_step_by_step(img, seed_point, fill_color=(255, 255, 255), speed_ms=100):
    """
    逐步洪水填充算法，支持动画效果
    
    参数:
        img: 输入图像（BGR格式）
        seed_point: 种子点坐标 (x, y)
        fill_color: 填充颜色 (B, G, R)
        speed_ms: 每次更新的间隔（毫秒）
    
    返回:
        填充后的图像
    """
    if img is None:
        return None
    
    h, w = img.shape[:2]
    x, y = seed_point
    
    # 检查种子点是否在图像范围内
    if x < 0 or x >= w or y < 0 or y >= h:
        return None
    
    # 创建结果图像的副本
    result = img.copy()
    
    # 获取种子点的颜色
    seed_color = tuple(map(int, img[y, x]))
    
    # 如果种子点颜色已经是填充颜色，直接返回
    if seed_color == fill_color:
        return result
    
    # 使用队列进行广度优先搜索
    from collections import deque
    queue = deque([(x, y)])
    visited = np.zeros((h, w), dtype=np.uint8)
    visited[y, x] = 1
    
    # 填充计数器
    filled_count = 0
    batch_size = max(1, w * h // 1000)  # 每批填充的像素数
    
    while queue:
        # 处理一批像素
        batch = []
        for _ in range(min(batch_size, len(queue))):
            if queue:
                batch.append(queue.popleft())
        
        for px, py in batch:
            # 检查当前像素是否应该填充
            current_color = tuple(map(int, result[py, px]))
            if current_color == seed_color:
                result[py, px] = fill_color
                filled_count += 1
                
                # 添加相邻像素到队列
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = px + dx, py + dy
                    if 0 <= nx < w and 0 <= ny < h and visited[ny, nx] == 0:
                        neighbor_color = tuple(map(int, result[ny, nx]))
                        if neighbor_color == seed_color:
                            visited[ny, nx] = 1
                            queue.append((nx, ny))
        
        # 发送中间结果
        if filled_count % batch_size == 0 or len(queue) == 0:
            send_image_result(processed_image=result)
            time.sleep(speed_ms / 1000.0)  # 转换为秒
    
    return result


def handle_flood_fill(data):
    """
    处理洪水填充请求
    
    参数:
        data: 包含洪水填充参数的数据字典
            - x: 种子点x坐标
            - y: 种子点y坐标
            - speed: 填充速度（毫秒）
    """
    global _current_image, _current_image_filtered, _current_image_binary
    
    try:
        # 确定使用哪个图像进行填充
        source_image = _current_image_binary if _current_image_binary is not None else (
            _current_image_filtered if _current_image_filtered is not None else _current_image
        )
        
        if source_image is None:
            print("错误: 未加载图像")
            send_image_result(error="未加载图像")
            return
        
        x = data.get("x", 0)
        y = data.get("y", 0)
        speed_ms = data.get("speed", 100)
        
        # 检查图像类型
        if len(source_image.shape) == 2:
            # 灰度图，转换为BGR
            source_image_bgr = cv2.cvtColor(source_image, cv2.COLOR_GRAY2BGR)
            fill_color = (255, 255, 255)  # 白色填充
        else:
            source_image_bgr = source_image.copy()
            fill_color = (255, 255, 255)  # 白色填充
        
        print(f"开始洪水填充，种子点: ({x}, {y}), 速度: {speed_ms}ms")
        
        # 执行逐步洪水填充
        filled_image = flood_fill_step_by_step(
            source_image_bgr, 
            (x, y), 
            fill_color=fill_color,
            speed_ms=speed_ms
        )
        
        if filled_image is None:
            print("错误: 洪水填充失败")
            send_image_result(error="洪水填充失败")
            return
        
        print("洪水填充完成")
        
    except Exception as e:
        print(f"洪水填充时出错: {e}")
        traceback.print_exc()
        send_image_result(error=str(e))


def send_image_result(processed_image=None, error=None):
    """
    发送图像处理结果到 Electron（公共方法）

    参数:
        image: 原图或过滤后的图像（numpy 数组），可选
        processed_image: 处理后的图像（numpy 数组），可选
        threshold: 阈值值，可选
        error: 错误信息，可选
    """
    message = {"success": error is None}

    if error:
        message["error"] = error
    else:
        if processed_image is not None:
            encode_params = [cv2.IMWRITE_PNG_COMPRESSION, 0]  # 0 = 无压缩，保持原始质量
            _, buffer = cv2.imencode(".png", processed_image, encode_params)
            img = base64.b64encode(buffer).decode("utf-8")
            message["processedImage"] = img

    send_to_electron(
        prop="image-processed",
        message=message,
        method="controller/example/receiveProcessedImage",
    )


def init_client(url="http://127.0.0.1:7070"):
    """
    初始化 Socket.IO 客户端并设置事件监听器

    参数:
        url: Socket.IO 服务器地址，默认为 'http://127.0.0.1:7070'
    """
    global _client
    if _client is None:
        _client = socketio.Client()

        # 监听来自 Electron 的消息（在连接前设置）
        # 使用自定义事件名 'python-message' 来接收消息
        @_client.on("python-message")
        def on_message(data):
            """
            接收来自 Electron 的消息

            参数:
                data: Electron 发送的数据
            """
            print(f"收到来自 Electron 的消息: {data}")
            # 处理不同类型的消息
            if isinstance(data, dict):
                message_type = data.get("type")

                # 处理图像上传请求
                if message_type == "upload_image":
                    handle_upload_image(data)
                # 统一的图像处理请求
                elif message_type == "process_image":
                    handle_process_image(data)
                # 洪水填充请求
                elif message_type == "flood_fill":
                    handle_flood_fill(data)

    client = _client

    # 如果未连接，则连接
    if not client.connected:
        client.connect(url)

    return client


def send_to_electron(
    prop,
    message,
    method="controller/example/receiveProcessedImage",
    url="http://127.0.0.1:7070",
):
    """
    向 Electron 发送数据

    参数:
        prop: 修改字段名
        message: 修改字段的值
        method: 控制器方法路径，默认为 'controller/example/receiveProcessedImage'
        url: Socket.IO 服务器地址，默认为 'http://127.0.0.1:7070'

    返回:
        response: Electron 返回的响应数据
    """
    try:
        global _client
        # 初始化客户端（如果还未初始化）
        client = init_client(url)

        # 通信频道固定为 'socket-channel'
        channel = "socket-channel"

        # 构建发送数据：{prop, message}
        params = {"prop": prop, "message": message}

        # 发送数据格式：{ cmd: method, args: ... }
        # 注意：electron-egg 框架期望的是 'args' 而不是 'params'
        data = {"cmd": method, "args": params}

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
    # 初始化客户端并设置监听器
    init_client()

    # 保持程序运行以接收消息
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序退出")
        if _client and _client.connected:
            _client.disconnect()
