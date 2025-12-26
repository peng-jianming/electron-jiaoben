import socketio
import time
import cv2
import numpy as np
import base64
import os
import traceback
import threading
from collections import deque

# Socket.IO 客户端实例
_client = None

# 存储当前加载的图像（numpy 数组格式）
_current_image = None  # 原图
_current_image_filtered = None  # 颜色过滤后的图像
_current_image_binary = None  # 二值化后的图像
_current_image_flood_filled = None  # 洪水填充后的图像

# 洪水填充控制标志
_flood_fill_running = False
_flood_fill_stop_event = threading.Event()


def 上传图片(data):
    """处理图像上传请求"""
    global _current_image, _current_image_filtered, _current_image_binary, _current_image_flood_filled

    try:
        image_path = data.get("path")

        if not image_path:
            send_image_result(error="未提供图像路径")
            return

        if not os.path.exists(image_path):
            send_image_result(error=f"图像文件不存在: {image_path}")
            return

        # 使用 numpy 读取文件避免中文路径问题
        try:
            with open(image_path, "rb") as f:
                nparr = np.frombuffer(f.read(), np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as e:
            send_image_result(error=f"读取图像文件时出错: {str(e)}")
            return

        if img is None:
            send_image_result(error=f"无法解码图像文件: {image_path}")
            return

        _current_image = img
        _current_image_filtered = None
        _current_image_binary = None
        _current_image_flood_filled = None
        print(f"图像已加载: {image_path}")
        send_image_result(processed_image=img)

    except Exception as e:
        traceback.print_exc()
        send_image_result(error=str(e))


def 解析颜色过滤字符串(color_str):
    """
    解析颜色过滤字符串
    格式: '191919-203040' 或 '191919'
    返回: (base_color_bgr, tolerance_bgr) 或 None
    """
    try:
        parts = color_str.split("-", 1)
        base_hex = parts[0]
        tolerance_hex = parts[1] if len(parts) > 1 else "000000"

        if len(base_hex) != 6:
            return None

        # 解析RGB并转换为BGR
        base_bgr = tuple(int(base_hex[i:i+2], 16) for i in (4, 2, 0))
        
        if len(tolerance_hex) != 6:
            tolerance_bgr = (0, 0, 0)
        else:
            tolerance_bgr = tuple(int(tolerance_hex[i:i+2], 16) for i in (4, 2, 0))

        return (base_bgr, tolerance_bgr)
    except Exception as e:
        print(f"解析颜色过滤字符串失败: {color_str}, 错误: {e}")
        return None


def 计算颜色范围的上下界(base_color, tolerance):
    """计算颜色范围的上下界"""
    lower = np.array([max(0, base_color[i] - tolerance[i]) for i in range(3)])
    upper = np.array([min(255, base_color[i] + tolerance[i]) for i in range(3)])
    return lower, upper


def 对图像应用颜色过滤(img, keep_colors, filter_colors):
    """对图像应用颜色过滤"""
    if img is None:
        return None

    result = img.copy()
    mask = np.ones((img.shape[0], img.shape[1]), dtype=np.uint8) * 255

    # 处理保留颜色
    if keep_colors:
        keep_mask = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
        for color_str in keep_colors:
            color_info = 解析颜色过滤字符串(color_str)
            if color_info:
                lower, upper = 计算颜色范围的上下界(*color_info)
                color_mask = cv2.inRange(img, lower, upper)
                keep_mask = cv2.bitwise_or(keep_mask, color_mask)
        mask = cv2.bitwise_and(mask, keep_mask)

    # 处理过滤颜色
    for color_str in (filter_colors or []):
        color_info = 解析颜色过滤字符串(color_str)
        if color_info:
            lower, upper = 计算颜色范围的上下界(*color_info)
            filter_mask = cv2.inRange(img, lower, upper)
            mask = cv2.bitwise_and(mask, cv2.bitwise_not(filter_mask))

    return cv2.bitwise_and(result, result, mask=mask)


def 处理图片流程(data):
    """统一的图像处理函数：颜色过滤 -> 二值化"""
    global _current_image_filtered, _current_image_binary, _current_image_flood_filled

    try:
        if _current_image is None:
            send_image_result(error="未加载图像，请先上传图像")
            return

        source_image = _current_image
        _current_image_filtered = None
        _current_image_binary = None
        _current_image_flood_filled = None

        # 步骤1: 颜色过滤
        if data.get("enableColorFilter"):
            keep_colors = data.get("keepColors", [])
            filter_colors = data.get("filterColors", [])

            if keep_colors or filter_colors:
                filtered_img = 对图像应用颜色过滤(_current_image, keep_colors, filter_colors)
                if filtered_img is None:
                    send_image_result(error="颜色过滤失败")
                    return
                source_image = filtered_img
                _current_image_filtered = filtered_img
                print(f"颜色过滤完成，保留: {keep_colors}, 过滤: {filter_colors}")

        # 步骤2: 二值化
        if data.get("enableBinary"):
            threshold_value = data.get("threshold", 127)
            gray = cv2.cvtColor(source_image, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
            source_image = binary
            _current_image_binary = binary
            print(f"二值化处理完成，阈值: {threshold_value}")

        send_image_result(processed_image=source_image)

    except Exception as e:
        traceback.print_exc()
        send_image_result(error=str(e))


def 逐步洪水填充算法(img, seed_point, fill_color=(255, 255, 255), batch_size=100):
    """逐步洪水填充算法，支持动画效果"""
    if img is None:
        return None

    h, w = img.shape[:2]
    x, y = seed_point

    if not (0 <= x < w and 0 <= y < h):
        return None

    result = img.copy()
    seed_color = img[y, x].copy()
    fill_color_arr = np.array(fill_color, dtype=np.uint8)

    if np.array_equal(seed_color, fill_color_arr):
        return result

    queue = deque([(x, y)])
    visited = np.zeros((h, w), dtype=bool)
    visited[y, x] = True
    filled_count = 0
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def should_stop():
        return _flood_fill_stop_event.is_set()

    while queue:
        if should_stop():
            print("洪水填充已被中断")
            return None

        px, py = queue.popleft()

        if np.array_equal(result[py, px], seed_color):
            result[py, px] = fill_color_arr
            filled_count += 1

            for dx, dy in directions:
                nx, ny = px + dx, py + dy
                if 0 <= nx < w and 0 <= ny < h and not visited[ny, nx]:
                    if np.array_equal(result[ny, nx], seed_color):
                        visited[ny, nx] = True
                        queue.append((nx, ny))

            if filled_count % batch_size == 0:
                time.sleep(0.05)
                if should_stop():
                    return None
                send_image_result(processed_image=result, use_fast_encode=True)

    if should_stop():
        return None

    send_image_result(processed_image=result)
    return result


def 洪水填充线程函数(source_image_bgr, x, y, fill_color, batch_size):
    """洪水填充线程函数"""
    global _flood_fill_running, _current_image_flood_filled

    try:
        print(f"开始洪水填充，种子点: ({x}, {y}), 批量大小: {batch_size}")
        filled_image = 逐步洪水填充算法(
            source_image_bgr, (x, y), fill_color=fill_color, batch_size=batch_size
        )
        _flood_fill_running = False

        if filled_image is None and not _flood_fill_stop_event.is_set():
            send_image_result(error="洪水填充失败")
        elif filled_image is not None:
            _current_image_flood_filled = filled_image
            print("洪水填充完成")

    except Exception as e:
        _flood_fill_running = False
        traceback.print_exc()
        send_image_result(error=str(e))


def 洪水填充(data):
    """处理洪水填充请求"""
    global _flood_fill_running

    try:
        if _flood_fill_running:
            _flood_fill_stop_event.set()
            time.sleep(0.05)

        _flood_fill_stop_event.clear()
        _flood_fill_running = True

        # 确定使用哪个图像
        if _current_image_binary is not None:
            source_image = _current_image_binary
        elif _current_image_filtered is not None:
            source_image = _current_image_filtered
        else:
            source_image = _current_image

        if source_image is None:
            send_image_result(error="未加载图像")
            _flood_fill_running = False
            return

        x, y = data.get("x", 0), data.get("y", 0)
        batch_size = data.get("batchSize", 100)

        # 转换为BGR格式
        if len(source_image.shape) == 2:
            source_image_bgr = cv2.cvtColor(source_image, cv2.COLOR_GRAY2BGR)
        else:
            source_image_bgr = source_image.copy()

        thread = threading.Thread(
            target=洪水填充线程函数,
            args=(source_image_bgr, x, y, (255, 255, 255), batch_size),
            daemon=True
        )
        thread.start()

    except Exception as e:
        _flood_fill_running = False
        traceback.print_exc()
        send_image_result(error=str(e))


def 清除洪水填充(data):
    """清除洪水填充并重新处理图像"""
    global _current_image_flood_filled
    
    try:
        _flood_fill_stop_event.set()
        _current_image_flood_filled = None
        print("正在停止洪水填充...")
        处理图片流程(data)
        print("洪水填充已清除")
    except Exception as e:
        traceback.print_exc()
        send_image_result(error=str(e))


def 保存图片(data):
    """保存当前处理后的图片"""
    try:
        save_path = data.get("savePath")
        if not save_path:
            send_save_result(error="未提供保存路径")
            return

        # 确定要保存的图片：优先级 洪水填充 > 二值化 > 颜色过滤 > 原图
        image_to_save = None
        if _current_image_flood_filled is not None:
            image_to_save = _current_image_flood_filled
            print("保存洪水填充后的图片")
        elif _current_image_binary is not None:
            # 二值化图片需要转换为BGR格式
            image_to_save = cv2.cvtColor(_current_image_binary, cv2.COLOR_GRAY2BGR)
            print("保存二值化后的图片")
        elif _current_image_filtered is not None:
            image_to_save = _current_image_filtered
            print("保存颜色过滤后的图片")
        elif _current_image is not None:
            image_to_save = _current_image
            print("保存原图")
        else:
            send_save_result(error="没有可保存的图片")
            return

        # 确保保存目录存在
        save_dir = os.path.dirname(save_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # 保存图片（支持中文路径）
        _, ext = os.path.splitext(save_path)
        ext = ext.lower() if ext else ".png"
        
        success, buffer = cv2.imencode(ext, image_to_save)
        if success:
            with open(save_path, "wb") as f:
                f.write(buffer)
            print(f"图片已保存: {save_path}")
            send_save_result(success=True, path=save_path)
        else:
            send_save_result(error="编码图片失败")

    except Exception as e:
        traceback.print_exc()
        send_save_result(error=str(e))


def send_save_result(success=False, path=None, error=None):
    """发送保存结果到 Electron"""
    message = {"success": success}
    if path:
        message["path"] = path
    if error:
        message["error"] = error
    
    send_to_electron(
        prop="image-saved",
        message=message,
        wait_response=True,
    )


def send_image_result(processed_image=None, error=None, use_fast_encode=False):
    """发送图像处理结果到 Electron"""
    if use_fast_encode and _flood_fill_stop_event.is_set():
        return

    message = {"success": error is None}

    if error:
        message["error"] = error
    elif processed_image is not None:
        if use_fast_encode:
            _, buffer = cv2.imencode(".jpg", processed_image, [cv2.IMWRITE_JPEG_QUALITY, 70])
        else:
            _, buffer = cv2.imencode(".png", processed_image, [cv2.IMWRITE_PNG_COMPRESSION, 0])

        if use_fast_encode and _flood_fill_stop_event.is_set():
            return

        message["processedImage"] = base64.b64encode(buffer).decode("utf-8")

    if use_fast_encode and _flood_fill_stop_event.is_set():
        return

    send_to_electron(
        prop="image-processed",
        message=message,
        wait_response=not use_fast_encode,
    )


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
                "upload_image": 上传图片,
                "process_image": 处理图片流程,
                "flood_fill": 洪水填充,
                "clear_flood_fill": 清除洪水填充,
                "save_image": 保存图片,
            }
            
            handler = handlers.get(data.get("type"))
            if handler:
                handler(data)

    if not _client.connected:
        _client.connect(url)

    return _client


def send_to_electron(prop, message, method="controller/example/receiveProcessedImage",
                     url="http://127.0.0.1:7070", wait_response=True):
    """向 Electron 发送数据"""
    try:
        client = init_client(url)
        data = {"cmd": method, "args": {"prop": prop, "message": message}}

        if not wait_response:
            client.emit("socket-channel", data)
            return None

        response_data = None
        response_received = False

        def callback(*args):
            nonlocal response_data, response_received
            response_data = args[0] if args else None
            response_received = True

        client.emit("socket-channel", data, callback=callback)

        # 等待响应（最多10秒）
        start_time = time.time()
        while not response_received and (time.time() - start_time) < 10:
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
    init_client()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序退出")
        if _client and _client.connected:
            _client.disconnect()
