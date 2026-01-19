import socketio
import time
import cv2
import numpy as np
import base64
import os
import traceback
import threading
from collections import deque
import tempfile
from matchImg import 找图

# Socket.IO 客户端实例
_client = None

# 存储当前加载的图像（numpy 数组格式）
_current_image = None  # 原图
_current_processed_image = None  # 当前处理后的图像（用于步骤链）
_step_images = {}  # 每个步骤完成后的图像，key为步骤索引

# 洪水填充控制标志
_flood_fill_running = False
_flood_fill_stop_event = threading.Event()

# 步骤处理控制
_steps_processing = False
_steps_stop_event = threading.Event()


def 上传图片(data):
    """处理图像上传请求"""
    global _current_image, _current_processed_image, _step_images

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
        _current_processed_image = None
        _step_images = {}  # 清空步骤图像缓存
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

    # 确保图像是BGR格式
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

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


def 对图像应用二值化(img, threshold_value):
    """对图像应用二值化处理"""
    if img is None:
        return None
    
    # 如果是彩色图像，先转换为灰度
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    _, binary = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
    return binary


def 逐步洪水填充算法(img, seed_point, fill_color=(255, 255, 255), batch_size=100, 
                      step_index=None, send_progress=True):
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
        return _flood_fill_stop_event.is_set() or _steps_stop_event.is_set()

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

            if send_progress and filled_count % batch_size == 0:
                time.sleep(0.05)
                if should_stop():
                    return None
                send_image_result(processed_image=result, use_fast_encode=True, 
                                step_index=step_index)

    if should_stop():
        return None

    return result


def 处理步骤列表(data):
    """处理步骤列表 - 按顺序执行每个步骤"""
    global _current_processed_image, _steps_processing, _step_images

    try:
        if _current_image is None:
            send_image_result(error="未加载图像，请先上传图像")
            return

        steps = data.get("steps", [])
        _step_images = {}  # 清空步骤图像缓存
        
        # 如果没有步骤，直接返回原图
        if not steps:
            _current_processed_image = _current_image.copy()
            print("没有处理步骤，返回原图")
            send_image_result(processed_image=_current_image)
            return

        # 停止之前的处理
        _steps_stop_event.set()
        _flood_fill_stop_event.set()
        time.sleep(0.1)
        _steps_stop_event.clear()
        _flood_fill_stop_event.clear()
        _steps_processing = True

        # 从原图开始处理
        current_img = _current_image.copy()
        print(f"开始处理 {len(steps)} 个步骤")

        for index, step in enumerate(steps):
            if _steps_stop_event.is_set():
                print("步骤处理已被中断")
                _steps_processing = False
                return

            step_type = step.get("type")
            params = step.get("params", {})
            print(f"处理步骤 {index + 1}/{len(steps)}: {step_type}")

            try:
                if step_type == "color_filter":
                    # 颜色过滤
                    keep_colors = params.get("keepColors", [])
                    filter_colors = params.get("filterColors", [])
                    result = 对图像应用颜色过滤(current_img, keep_colors, filter_colors)
                    if result is None:
                        send_image_result(error=f"步骤 {index + 1} 颜色过滤失败", 
                                        step_index=index)
                        _steps_processing = False
                        return
                    current_img = result
                    print(f"颜色过滤完成，保留: {keep_colors}, 过滤: {filter_colors}")

                elif step_type == "binary":
                    # 二值化
                    threshold_value = params.get("threshold", 127)
                    result = 对图像应用二值化(current_img, threshold_value)
                    if result is None:
                        send_image_result(error=f"步骤 {index + 1} 二值化失败", 
                                        step_index=index)
                        _steps_processing = False
                        return
                    current_img = result
                    print(f"二值化处理完成，阈值: {threshold_value}")

                elif step_type == "flood_fill":
                    # 洪水填充（无动画，直接完成）
                    x = params.get("x", 0)
                    y = params.get("y", 0)
                    
                    # 保存洪水填充前的图像，用于后续动画展示
                    _step_images[index] = current_img.copy()
                    
                    # 确保图像是BGR格式用于洪水填充
                    if len(current_img.shape) == 2:
                        current_img = cv2.cvtColor(current_img, cv2.COLOR_GRAY2BGR)
                    
                    result = 逐步洪水填充算法(
                        current_img, (x, y), 
                        fill_color=(255, 255, 255), 
                        batch_size=100,
                        step_index=index,
                        send_progress=False  # 不发送进度，直接完成
                    )
                    if result is None:
                        if not _steps_stop_event.is_set():
                            send_image_result(error=f"步骤 {index + 1} 洪水填充失败", 
                                            step_index=index)
                        _steps_processing = False
                        return
                    current_img = result
                    print(f"洪水填充完成，起点: ({x}, {y})")

                else:
                    print(f"未知的步骤类型: {step_type}")
                    continue

                # 发送当前步骤完成的结果
                _current_processed_image = current_img
                send_image_result(processed_image=current_img, step_index=index)

            except Exception as e:
                traceback.print_exc()
                send_image_result(error=f"步骤 {index + 1} 处理失败: {str(e)}", 
                                step_index=index)
                _steps_processing = False
                return

        _steps_processing = False
        print("所有步骤处理完成")

    except Exception as e:
        _steps_processing = False
        traceback.print_exc()
        send_image_result(error=str(e))


def 保存图片(data):
    """保存当前处理后的图片"""
    try:
        save_path = data.get("savePath")
        if not save_path:
            send_save_result(error="未提供保存路径")
            return

        # 确定要保存的图片：优先级 处理后的图像 > 原图
        image_to_save = None
        if _current_processed_image is not None:
            image_to_save = _current_processed_image
            print("保存处理后的图片")
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


def 洪水填充动画(data):
    """在新窗口中显示洪水填充动画"""
    global _flood_fill_running
    
    try:
        step_index = data.get("stepIndex", 0)
        params = data.get("params", {})
        x = params.get("x", 0)
        y = params.get("y", 0)
        
        # 获取该步骤开始前的图像
        if step_index in _step_images:
            base_img = _step_images[step_index].copy()
        elif step_index == 0 and _current_image is not None:
            base_img = _current_image.copy()
        else:
            print(f"未找到步骤 {step_index} 的基础图像")
            return
        
        # 确保图像是BGR格式
        if len(base_img.shape) == 2:
            base_img = cv2.cvtColor(base_img, cv2.COLOR_GRAY2BGR)
        
        print(f"开始洪水填充动画，步骤: {step_index}, 起点: ({x}, {y})")
        
        # 停止之前的洪水填充
        _flood_fill_stop_event.set()
        time.sleep(0.1)
        _flood_fill_stop_event.clear()
        _flood_fill_running = True
        
        # 在新线程中运行动画
        def run_animation():
            global _flood_fill_running
            try:
                h, w = base_img.shape[:2]
                
                if not (0 <= x < w and 0 <= y < h):
                    print("起始点超出图像范围")
                    _flood_fill_running = False
                    return
                
                result = base_img.copy()
                seed_color = base_img[y, x].copy()
                fill_color = np.array([255, 255, 255], dtype=np.uint8)
                
                if np.array_equal(seed_color, fill_color):
                    print("起始点颜色与填充颜色相同")
                    _flood_fill_running = False
                    return
                
                queue = deque([(x, y)])
                visited = np.zeros((h, w), dtype=bool)
                visited[y, x] = True
                filled_count = 0
                batch_size = 100
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                
                # 创建窗口
                window_name = f"洪水填充动画 - 步骤 {step_index + 1}"
                cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                
                # 设置窗口置顶
                cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
                
                # 计算窗口大小（限制最大尺寸）
                max_size = 800
                scale = min(max_size / w, max_size / h, 1.0)
                win_w, win_h = int(w * scale), int(h * scale)
                cv2.resizeWindow(window_name, win_w, win_h)
                
                def is_window_closed():
                    """检测窗口是否被用户关闭"""
                    try:
                        return cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1
                    except:
                        return True
                
                while queue:
                    if _flood_fill_stop_event.is_set() or is_window_closed():
                        print("洪水填充动画已中断")
                        _flood_fill_stop_event.set()
                        break
                    
                    px, py = queue.popleft()
                    
                    if np.array_equal(result[py, px], seed_color):
                        result[py, px] = fill_color
                        filled_count += 1
                        
                        for dx, dy in directions:
                            nx, ny = px + dx, py + dy
                            if 0 <= nx < w and 0 <= ny < h and not visited[ny, nx]:
                                if np.array_equal(result[ny, nx], seed_color):
                                    visited[ny, nx] = True
                                    queue.append((nx, ny))
                        
                        if filled_count % batch_size == 0:
                            cv2.imshow(window_name, result)
                            key = cv2.waitKey(1)
                            if key == 27 or key == ord('q') or is_window_closed():  # ESC、Q 或关闭窗口
                                _flood_fill_stop_event.set()
                                break
                
                # 显示最终结果
                if not _flood_fill_stop_event.is_set() and not is_window_closed():
                    cv2.imshow(window_name, result)
                    print(f"洪水填充动画完成，共填充 {filled_count} 个像素")
                    print("按任意键关闭窗口...")
                    while True:
                        key = cv2.waitKey(100)
                        if key != -1 or is_window_closed():
                            break
                
                # 安全关闭窗口
                try:
                    cv2.destroyWindow(window_name)
                except:
                    pass  # 窗口可能已被用户关闭
                _flood_fill_running = False
                
            except Exception as e:
                traceback.print_exc()
                # 安全关闭窗口
                try:
                    cv2.destroyWindow(window_name)
                except:
                    pass
                _flood_fill_running = False
        
        # 启动动画线程
        animation_thread = threading.Thread(target=run_animation, daemon=True)
        animation_thread.start()
        
    except Exception as e:
        traceback.print_exc()
        _flood_fill_running = False


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


def send_image_result(processed_image=None, error=None, use_fast_encode=False, step_index=None):
    """发送图像处理结果到 Electron"""
    if use_fast_encode and (_flood_fill_stop_event.is_set() or _steps_stop_event.is_set()):
        return

    message = {"success": error is None}

    if step_index is not None:
        message["stepIndex"] = step_index

    if error:
        message["error"] = error
    elif processed_image is not None:
        if use_fast_encode:
            _, buffer = cv2.imencode(".jpg", processed_image, [cv2.IMWRITE_JPEG_QUALITY, 70])
        else:
            _, buffer = cv2.imencode(".png", processed_image, [cv2.IMWRITE_PNG_COMPRESSION, 0])

        if use_fast_encode and (_flood_fill_stop_event.is_set() or _steps_stop_event.is_set()):
            return

        message["processedImage"] = base64.b64encode(buffer).decode("utf-8")

    if use_fast_encode and (_flood_fill_stop_event.is_set() or _steps_stop_event.is_set()):
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
            # print(f"收到来自 Electron 的消息: {data}")
            if not isinstance(data, dict):
                return

            handlers = {
                "upload_image": 上传图片,
                "process_steps": 处理步骤列表,
                "save_image": 保存图片,
                "flood_fill_animation": 洪水填充动画,
                "get_devices": 获取设备列表,
                "set_device": 设置当前设备,
                "capture_screenshot": 截图当前设备,
                "image_match": 图片匹配,
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


# ==================== 设备管理 ====================

# 当前已连接的设备 ID（由前端选择）
_current_device_id = None


def 发送设备列表(devices=None, error=None):
    """向 Electron 发送设备列表"""
    message = {
        "success": error is None,
        "devices": devices or [],
        "currentDeviceId": _current_device_id,
    }
    if error:
        message["error"] = error

    # prop 使用 device-list，Electron 再通过 socket 转发给前端
    send_to_electron(
        prop="device-list",
        message=message,
        wait_response=False,
    )


def 发送设备选择结果(error=None):
    """向 Electron 发送当前设备选择结果"""
    message = {
        "success": error is None,
        "currentDeviceId": _current_device_id,
    }
    if error:
        message["error"] = error

    send_to_electron(
        prop="device-selected",
        message=message,
        wait_response=False,
    )


def 获取设备列表(data):
    """获取当前已连接的 ADB 设备列表"""
    try:
        adb_path = r"C:\platform-tools\adb.exe"
        # 直接调用 adb devices
        result = subprocess.run(
            f'"{adb_path}" devices',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or "获取设备列表失败"
            print(error_msg)
            发送设备列表(devices=[], error=error_msg)
            return

        devices = []
        lines = result.stdout.strip().splitlines()
        # 第一行为 "List of devices attached"
        for line in lines[1:]:
            if "\t" in line:
                device_id, status = line.split("\t", 1)
                device_id = device_id.strip()
                if device_id:
                    devices.append(device_id)

        print(f"已检测到设备: {devices}")
        发送设备列表(devices=devices)
    except Exception as e:
        traceback.print_exc()
        发送设备列表(devices=[], error=str(e))


def 设置当前设备(data):
    """设置当前使用的设备 ID"""
    global _current_device_id
    try:
        device_id = data.get("deviceId") or data.get("device_id")
        if device_id:
            _current_device_id = str(device_id)
            print(f"当前连接设备已设置为: {_current_device_id}")
        else:
            # 允许清空
            _current_device_id = None
            print("当前连接设备已清空")

        发送设备选择结果()
    except Exception as e:
        traceback.print_exc()
        发送设备选择结果(error=str(e))


def 发送设备截图(image_bytes=None, error=None, source=None):
    """向 Electron 发送设备截图（PNG base64）"""
    message = {
        "success": error is None and image_bytes is not None,
        "currentDeviceId": _current_device_id,
    }
    if error or image_bytes is None:
        message["error"] = error or "截图失败"
    else:
        message["image"] = base64.b64encode(image_bytes).decode("utf-8")
    
    # 添加来源标识，用于前端区分处理
    if source:
        message["source"] = source

    send_to_electron(
        prop="device-screenshot",
        message=message,
        wait_response=False,
    )


def 截图当前设备(data):
    """对当前连接的设备执行截图"""
    try:
        # 获取来源标识（left-panel 或 right-panel）
        source = data.get("source", "left-panel")
        
        if not _current_device_id:
            print("尚未选择当前设备，无法截图")
            发送设备截图(image_bytes=None, error="未选择设备", source=source)
            return

        controller = ADBController(device_id=_current_device_id)
        img_bytes = controller.截图到内存()
        if not img_bytes:
            发送设备截图(image_bytes=None, error="截图失败", source=source)
            return

        发送设备截图(image_bytes=img_bytes, source=source)
    except Exception as e:
        traceback.print_exc()
        发送设备截图(image_bytes=None, error=str(e), source=data.get("source", "left-panel"))


def 发送图片匹配结果(result=None, result_image_bytes=None, error=None):
    """向 Electron 发送图片匹配结果"""
    message = {
        "success": error is None and result is not None,
    }
    if error:
        message["error"] = error
    elif result:
        message["result"] = result
        if result_image_bytes:
            message["resultImage"] = base64.b64encode(result_image_bytes).decode("utf-8")
    
    send_to_electron(
        prop="image-match-result",
        message=message,
        wait_response=False,
    )


def 图片匹配(data):
    """图片匹配处理函数"""
    try:
        small_image_base64 = data.get("smallImage")
        large_image_base64 = data.get("largeImage")  # 可能为 None，需要自动截图
        region = data.get("region")  # {x, y, w, h} 或 None
        color_tolerance = data.get("colorTolerance")  # 字符串数组或 None
        
        # 检查小图（必须提供）
        if not small_image_base64:
            发送图片匹配结果(error="缺少小图数据")
            return
        
        # 处理大图：如果没有提供，则自动截图
        large_image_path = None
        if not large_image_base64:
            # 需要自动截图
            if not _current_device_id:
                发送图片匹配结果(error="未选择设备，无法自动截图")
                return
            
            print(f"未提供大图，自动截图设备: {_current_device_id}")
            controller = ADBController(device_id=_current_device_id)
            large_image_bytes = controller.截图到内存()
            if not large_image_bytes:
                发送图片匹配结果(error="自动截图失败")
                return
            
            # 将截图保存为临时文件
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as large_file:
                large_file.write(large_image_bytes)
                large_image_path = large_file.name
            print(f"截图已保存到临时文件: {large_image_path}")
        else:
            # 将 base64 转换为临时文件
            large_image_bytes = base64.b64decode(large_image_base64)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as large_file:
                large_file.write(large_image_bytes)
                large_image_path = large_file.name
        
        # 将小图 base64 转换为临时文件
        small_image_bytes = base64.b64decode(small_image_base64)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as small_file:
            small_file.write(small_image_bytes)
            small_image_path = small_file.name
        
        try:
            # 解析区域参数
            region_tuple = (0, 0, 0, 0)  # 默认全图
            if region:
                region_tuple = (region.get("x", 0), region.get("y", 0), 
                              region.get("w", 0), region.get("h", 0))
            
            # 调用找图函数
            result = 找图(
                large_image_path=large_image_path,
                small_image_path=small_image_path,
                region=region_tuple,
                color_tolerance=color_tolerance
            )
            
            if result is None:
                发送图片匹配结果(error="未找到匹配位置")
                return
            
            # 读取大图用于绘制结果
            large_image = cv2.imread(large_image_path)
            if large_image is None:
                发送图片匹配结果(error="无法读取大图")
                return
            
            # 在结果图片上绘制匹配位置
            result_image = large_image.copy()
            
            # 绘制矩形框
            x = result["x"]
            y = result["y"]
            w = result["w"]
            h = result["h"]
            cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # 绘制相似度文本
            similarity_text = f"Similarity: {result['similarity']:.4f}"
            text_x = x
            text_y = max(y - 10, 20)
            
            # 绘制文本背景
            (text_width, text_height), baseline = cv2.getTextSize(
                similarity_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
            )
            cv2.rectangle(
                result_image,
                (text_x - 5, text_y - text_height - 5),
                (text_x + text_width + 5, text_y + baseline + 5),
                (0, 255, 0),
                -1
            )
            
            # 绘制文本
            cv2.putText(
                result_image,
                similarity_text,
                (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),
                2
            )
            
            # 将结果图片编码为 PNG
            _, result_buffer = cv2.imencode(".png", result_image)
            result_image_bytes = result_buffer.tobytes()
            
            # 发送结果
            发送图片匹配结果(result=result, result_image_bytes=result_image_bytes)
            
        finally:
            # 清理临时文件
            try:
                os.unlink(small_image_path)
            except:
                pass
            try:
                os.unlink(large_image_path)
            except:
                pass
            
    except Exception as e:
        traceback.print_exc()
        发送图片匹配结果(error=str(e))


#================================================================
import subprocess
class ADBController:
    """ADB 控制器类，封装截图和点击功能"""
    
    def __init__(self, device_id=None):
        """
        初始化 ADB 控制器
        
        参数:
            device_id: 设备ID，如果有多个设备连接时需要指定
                      可以通过 adb devices 命令查看设备ID
        """
        self.device_id = device_id
        self._adb_prefix = self._build_adb_prefix()
    
    def _build_adb_prefix(self):
        """构建 ADB 命令前缀"""
        adb_path = r"C:\platform-tools\adb.exe"
        if self.device_id:
            return f'"{adb_path}" -s {self.device_id}'
        return f'"{adb_path}"'
    
    def _run_command(self, command, shell=True):
        """
        执行命令并返回结果
        
        参数:
            command: 要执行的命令
            shell: 是否使用 shell 执行
            
        返回:
            (success, output) - 成功标志和输出内容
        """
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "命令执行超时"
        except Exception as e:
            return False, str(e)
    
    def get_devices(self):
        """
        获取所有已连接的设备列表
        
        返回:
            设备ID列表
        """
        adb_path = r"C:\platform-tools\adb.exe"
        success, output = self._run_command(f'"{adb_path}" devices')
        if not success:
            return []
        
        devices = []
        lines = output.strip().split('\n')
        for line in lines[1:]:  # 跳过第一行 "List of devices attached"
            if '\t' in line:
                device_id = line.split('\t')[0]
                devices.append(device_id)
        return devices
    
    def 截图到内存(self):
        """
        截图并直接返回图像数据（不保存到文件）
        
        返回:
            PNG 图像的字节数据，失败返回 None
        """
        try:
            result = subprocess.run(
                f"{self._adb_prefix} exec-out screencap -p",
                shell=True,
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout
            return None
        except Exception as e:
            print(f"截图失败: {e}")
            return None
    








if __name__ == "__main__":
    controller = ADBController()
    devices = controller.get_devices()
    print(devices)

    init_client()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("程序退出")
        if _client and _client.connected:
            _client.disconnect()
