def 写入日志(info):
    print(f'{info}')



import json
import random
import websockets
import os
import time
import asyncio

import cv2

from ultralytics import YOLO
import math

def opencv找图(large_image_path, small_image_path, similarity=0.9, region=(0, 0, 0, 0)):
    """
    在大图中查找小图
    :param large_image_path: 大图路径
    :param small_image_path: 小图路径
    :param similarity: 相似度阈值，0-1之间
    :param region: 检测区域 (x, y, width, height)，如果全为0则检测整个大图
    :return: 找到的位置 {"x": x, "y": y} 或 None
    """
    # 读取图像
    # large_image = cv2.imread(large_image_path)
    # small_image = cv2.imread(small_image_path)


        # 2. 加载大图（带Alpha通道）
    large_image = cv2.imread(large_image_path, cv2.IMREAD_UNCHANGED)

    # 确保有Alpha通道
    if large_image.shape[2] == 3:
        large_image = cv2.cvtColor(large_image, cv2.COLOR_BGR2BGRA)

    # 3. 加载小图（带Alpha通道）
    small_image = cv2.imread(small_image_path, cv2.IMREAD_UNCHANGED)

    # 确保有Alpha通道
    if small_image.shape[2] == 3:
        small_image = cv2.cvtColor(small_image, cv2.COLOR_BGR2BGRA)



    if large_image is None or small_image is None:
        return None

    # 获取大图尺寸
    large_h, large_w = large_image.shape[:2]
    
    # 解析检测区域
    x, y, width, height = region
    
    # 判断是否指定了检测区域
    if x == 0 and y == 0 and width == 0 and height == 0:
        # 检测整个大图
        search_area = large_image
        offset_x, offset_y = 0, 0
    else:
        # 确保区域在图像范围内
        if x < 0: x = 0
        if y < 0: y = 0
        if width <= 0: width = large_w - x
        if height <= 0: height = large_h - y
        
        # 计算实际裁剪区域
        crop_x = max(0, x)
        crop_y = max(0, y)
        crop_width = min(width, large_w - crop_x)
        crop_height = min(height, large_h - crop_y)
        
        # 确保裁剪区域有效
        if crop_width <= 0 or crop_height <= 0:
            return None
            
        # 裁剪检测区域
        search_area = large_image[crop_y:crop_y+crop_height, crop_x:crop_x+crop_width]
        offset_x, offset_y = crop_x, crop_y

    # 获取小图尺寸
    h, w = small_image.shape[:2]
    
    # 检查小图是否大于检测区域
    if h > search_area.shape[0] or w > search_area.shape[1]:
        return None

    s_b, s_g, s_r, s_a = cv2.split(small_image)

    # 创建掩码：Alpha > 0 的部分为 255，否则为 0
    _, mask = cv2.threshold(s_a, 0, 255, cv2.THRESH_BINARY)

    # 使用模板匹配
    result = cv2.matchTemplate(search_area, small_image, cv2.TM_CCOEFF_NORMED, mask=mask)

    # 找到最匹配的位置
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # 检查是否达到相似度阈值
    if max_val >= similarity:
        # 返回相对于整个大图的坐标（加上偏移量）
        return {"x": max_loc[0] + offset_x, "y": max_loc[1] + offset_y, 'w': w, 'h': h, 'similarity': max_val}

    return None


async def send_to_gc(payload):
    try:
        # print(f"Sending to GC: {payload}")
        async with websockets.connect("ws://127.0.0.1:33332") as qc_ws:
            await qc_ws.send(json.dumps(payload))
            response = await qc_ws.recv()
            # print(f"GC Response: {response}")
            return json.loads(response)
    except Exception as e:
        print(f"GC Error: {e}")
        return None


def 截图():
    # 获取保存路径
    save_dir = os.path.join(os.path.dirname(__file__), "resource", "cache")
    os.makedirs(save_dir, exist_ok=True)
    save_path = save_dir  # 存储截图的目录

    payload = {
        "action": "screen",
        "comm": {"deviceIds": deviceIds, "savePath": save_path, "onlyDeviceName": 1},
    }
    response = asyncio.run(send_to_gc(payload))
    # 检查返回值是否成功
    if response and response.get("StatusCode") == 200 and response.get("result") == "OK" and response.get("data"):
        safe_device_id = deviceIds.replace(".", "_").replace(":", "_")
        file_path = os.path.join(save_path, f"{safe_device_id}.png")
        return file_path
    return None


def 调用ADB(command):
    payload = {"action": "adb", "comm": {"deviceIds": deviceIds, "command": command}}
    asyncio.run(send_to_gc(payload))


def 随机延时(startMs, endMs):
    if startMs > endMs:
        startMs, endMs = endMs, startMs
    time.sleep(random.uniform(startMs, endMs))


def ADB点击(x, y):
    if x and y:
        调用ADB(f"input motionevent DOWN {x} {y}")
        随机延时(0, 0.3)
        调用ADB(f"input motionevent UP {x} {y}")


def 随机ADB点击(x, y, w, h):
    if x and y and w and h:
        random_x = random.randint(x, x + w)
        random_y = random.randint(y, y + h)
        ADB点击(random_x, random_y)


def yolo(image_path, model_path, conf_threshold=0.6):
    """
    使用YOLOv8模型检测图片中的目标

    参数:
        image_path: 图片路径
        conf_threshold: 置信度阈值，默认0.25

    返回:
        检测结果列表，每个元素是一个字典，包含:
        - class_name: 分类名
        - confidence: 相似度/置信度
        - x: 边界框中心x坐标
        - y: 边界框中心y坐标
        - w: 边界框宽度
        - h: 边界框高度
    """
    model = 获取模型(model_path)

    # 进行推理
    results = model(image_path, conf=conf_threshold, verbose=False)

    detections = []

    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue

        for i in range(len(boxes)):
            # 获取边界框坐标 (xywh格式: 中心点x, 中心点y, 宽度, 高度)
            xywh = boxes.xywh[i].tolist()
            x, y, w, h = xywh

            # 获取置信度
            confidence = float(boxes.conf[i])

            # 获取类别ID和类别名
            class_id = int(boxes.cls[i])
            class_name = model.names[class_id]

            detection = {
                "class_name": class_name,
                "confidence": confidence,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
            }
            detections.append(detection)

    return detections


_model_path = ""
_model = None


def 获取模型(model_path):
    """获取YOLO模型实例（懒加载）"""
    global _model
    global _model_path
    if model_path != _model_path:
        _model_path = model_path
        _model = YOLO(model_path)

    return _model



class Field:
    def __init__(self, config):
        self.标识 = config.get("标识")
        self.方式 = config.get("方式")
        self.图片路径 = config.get("图片路径")
        self.大图路径 = config.get("大图路径")
        self.相似度 = config.get("相似度", 0.8)
        self.分类名 = config.get("分类名")
        self.模型路径 = config.get("模型路径")
        self.查找区域 = config.get("查找区域", {"x": 0, "y": 0, "w": 0, "h": 0})
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0
        self.是否判断状态 = False

    def 查找(self):
        url =  self.大图路径 if self.大图路径 else 截图()
        if url:
            if self.方式 == "opencv找图":
                result = opencv找图(url, self.图片路径, self.相似度,(self.查找区域["x"], self.查找区域["y"],self.查找区域["w"],self.查找区域["h"]))
                if result:
                    self.x = result["x"]
                    self.y = result["y"]
                    self.w = result["w"]
                    self.h = result["h"]

            if self.方式 == "yolo":
                result = yolo(url, self.模型路径, self.相似度)
                if len(result):
                    for r in result:
                        if r["class_name"] == self.分类名:
                            self.x = self.查找区域["x"] + math.ceil(r["x"])
                            self.y = self.查找区域["y"] + math.ceil(r["y"])
                            self.w = math.floor(r["w"])
                            self.h = math.floor(r["h"])
                            break
        if self.是否判断状态:
            写入日志(f"{self.标识}: {'是' if self.是否找到() else '否'}")
        return self

    def 点击(self, x=None, y=None, w=None, h=None):
        if self.是否找到():
            if x and y and w and h:
                随机ADB点击(x, y, w, h)
            elif x and y:
                ADB点击(x, y)
            elif self.x and self.y:
                随机ADB点击(self.x, self.y, self.w, self.h)

            if self.标识:
                写入日志(f"{self.标识}")
        return self

    def 偏移点击(self, x=None, y=None, w=None, h=None):
        if self.是否找到():
            if not w and not h:
                ADB点击(self.x + x, self.y + y)
            if w and h:
                随机ADB点击(self.x + x, self.y + y, w, h)

            if self.标识:
                写入日志(f"{self.标识}")
        return self

    def 随机延时(self, startMs, endMs):
        if self.是否找到():
            随机延时(startMs, endMs)
        return self

    def 设置查找区域(self, 查找区域):
        self.查找区域 = 查找区域
        return self

    def 设置大图路径(self, 大图路径):
        self.大图路径 = 大图路径
        return self

    def 设置标识(self, 标识, 是否判断状态=False):
        self.标识 = 标识
        self.是否判断状态 = 是否判断状态
        return self

    def 是否找到(self):
        return bool(self.x and self.y)







class StateMachine:
    def __init__(self):
        self._states = {}
        self._current_state = None
        self._result = None
        self._is_running = False

    def state(self, name):
        """装饰器：直接注册状态处理函数"""
        def decorator(func):
            self._states[name] = func
            return func
        return decorator
        
    def on(self, state, handler):
        """注册状态处理函数"""
        self._states[state] = handler
        return self
        
    def start(self, initial_state):
        """启动状态机"""
        self._current_state = initial_state
        self._is_running = True
        
        while self._is_running and self._current_state is not None:
            # 如果当前状态已注册
            if self._current_state in self._states:
                # 执行状态处理函数
                handler = self._states[self._current_state]
                next_state = handler()
                
                # 如果返回了下一个状态
                if next_state is not None:
                    self._current_state = str(next_state)
                else:
                    self._result = self._current_state
                    self._is_running = False
            else:
                # 状态未注册，结束状态机
                self._result = self._current_state
                self._is_running = False
                
        return self._result
        
    def stop(self):
        """停止状态机"""
        self._is_running = False
        
    def get_current_state(self):
        """获取当前状态"""
        return self._current_state




class InterfaceStateMachine:
    def __init__(self):
        self._states = {}
        self._current_interface = None
        self._previous_interface = None
        self._is_running = False
        self._context = {}  # 上下文信息
        
        # 界面识别函数（需要用户实现）
        self._interface_recognizer = None
        
    def set_recognizer(self, recognizer):
        """设置界面识别函数"""
        self._interface_recognizer = recognizer
        return self
        
    def on(self, interface, handler):
        """注册界面处理函数"""
        self._states[interface] = handler
        return self
        
    def state(self, name):
        """装饰器：直接注册界面处理函数"""
        def decorator(func):
            self._states[name] = func
            return func
        return decorator
        
    def start(self):
        """启动状态机"""
        self._is_running = True
        
        while self._is_running:
            try:
                # 识别当前界面
                detected_interface = self._interface_recognizer()
                
                # 如果检测到界面变化
                if detected_interface != self._current_interface:
                    self._previous_interface = self._current_interface
                    self._current_interface = detected_interface
                    
                
                # 如果当前界面有注册处理函数
                if self._current_interface in self._states:
                    handler = self._states[self._current_interface]
                    
                    # 执行界面处理函数，传入当前上下文
                    result = handler(self._context)
                    
                    # 处理函数可以返回False表示需要保持当前界面状态
                    # 或者返回新的上下文数据
                    if isinstance(result, dict):
                        self._context.update(result)
                    elif result is False:
                        # 处理函数返回False，表示操作失败或需要重试
                        print(f"界面 {self._current_interface} 处理失败")
                
                # 短暂延迟，避免CPU占用过高
                # time.sleep(1)
                
            except Exception as e:
                print(f"状态机运行异常: {e}")
                self.stop()
            
    def stop(self):
        """停止状态机"""
        self._is_running = False
        
    def update_context(self, **kwargs):
        """更新上下文"""
        self._context.update(kwargs)
        




class TaskLineMachine:
    def __init__(self):
        self._states = {}
        self._current_interface = None
        self._previous_interface = None
        self._is_running = False
        self._context = {}  # 上下文信息
        
        
    def state(self, Field):
        """装饰器：直接注册界面处理函数"""
        def decorator(func):
            self._states[Field['标识']] = {
                'handler': func,
                'Field': Field
            }
        return decorator
        
    def start(self):
        """启动状态机"""
        self._is_running = True
        
        while self._is_running:
            try:
                url = 截图()
                if url:
                    是否找到 = False
                    for state in self._states.values():
                        handler = state['handler']
                        config = state['Field']
                        if Field(config).设置大图路径(url).查找().是否找到():
                            是否找到 = True
                            print(f"目前位于: {config['标识']}")
                            self.update_context(上一状态=self._current_interface)
                            self._current_interface = config['标识']
                            result = handler(self._context)
                            if isinstance(result, dict):
                                self._context.update(result)
                            elif result is False:
                                # 处理函数返回False，表示操作失败或需要重试
                                print(f"界面 {self._current_interface} 处理失败")
                            break

                    if not 是否找到:
                        # 可以在这里设置时长,如果长时间处于未知界面,那么就报警,或者调用关闭函数关闭所有界面等
                        print("目前处于: 未知界面")     
                    # 短暂延迟，避免CPU占用过高
                    # time.sleep(1)
                
            except Exception as e:
                print(f"状态机运行异常: {e}")
                self.stop()
            
    def stop(self):
        """停止状态机"""
        self._is_running = False
        
    def update_context(self, **kwargs):
        """更新上下文"""
        self._context.update(kwargs)






import socketio


# Socket.IO 客户端实例
_client = None

def send_to_electron(prop, message, method='controller/example/changeProp', url='http://127.0.0.1:7070'):
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

