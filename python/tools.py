import json
import random
import websockets
import os
import time
import asyncio
import cv2
from ultralytics import YOLO
import math
import numpy as np
from PIL import Image
import socketio



class DeviceController:
    """设备控制器类，封装所有设备操作功能"""
    
    def __init__(self, device_id):
        """
        初始化设备控制器
        
        参数:
            device_id: 设备ID
        """
        self.device_id = device_id
        self.font_library_cache = {}  # 初始化字库缓存，支持同名多个条目（使用列表存储）
        self.加载字库文件(os.path.join(os.path.dirname(__file__), "resource", "font_library.txt"))
        self._model_path = ""
        self._model = None
        self._socketio_client = None
        # 初始化 Socket.IO 客户端（可选，延迟连接）
        self.init_client()
        
    def 写入日志(self, info):
        """写入日志"""
        self.send_to_electron('logs', info)
    
    async def _send_to_gc(self, payload):
        """发送消息到GC服务器"""
        try:
            async with websockets.connect("ws://127.0.0.1:33332") as qc_ws:
                await qc_ws.send(json.dumps(payload))
                response = await qc_ws.recv()
                return json.loads(response)
        except Exception as e:
            print(f"GC Error: {e}")
            return None
    
    def 截图(self):
        """截图"""
        # 获取保存路径
        save_dir = os.path.join(os.path.dirname(__file__), "resource", "cache")
        os.makedirs(save_dir, exist_ok=True)
        save_path = save_dir  # 存储截图的目录
        
        payload = {
            "action": "screen",
            "comm": {"deviceIds": self.device_id, "savePath": save_path, "onlyDeviceName": 1},
        }
        response = asyncio.run(self._send_to_gc(payload))
        # 检查返回值是否成功
        if response and response.get("StatusCode") == 200 and response.get("result") == "OK" and response.get("data"):
            safe_device_id = self.device_id.replace(".", "_").replace(":", "_")
            file_path = os.path.join(save_path, f"{safe_device_id}.png")
            return file_path
        return None
    
    def 调用ADB(self, command):
        """调用ADB命令"""
        payload = {"action": "adb", "comm": {"deviceIds": self.device_id, "command": command}}
        asyncio.run(self._send_to_gc(payload))
    
    def ADB点击(self, x, y):
        """ADB点击"""
        if x and y:
            self.调用ADB(f"input motionevent DOWN {x} {y}")
            self.随机延时(0, 0.3)
            self.调用ADB(f"input motionevent UP {x} {y}")
    
    def 随机ADB点击(self, x, y, w, h):
        """随机ADB点击"""
        if x and y and w and h:
            random_x = random.randint(x, x + w)
            random_y = random.randint(y, y + h)
            self.ADB点击(random_x, random_y)
    
    def 随机延时(self, startMs, endMs):
        """随机延时"""
        if startMs > endMs:
            startMs, endMs = endMs, startMs
        time.sleep(random.uniform(startMs, endMs))
    
    def 加载字库文件(self,font_library_path):
        """
        读取字库文件并缓存到全局变量中
        
        此函数应在程序启动时调用，将字库数据加载到内存中，避免每次找图时重复读取文件
        
        :param font_library_path: 字库文件路径（txt文件，格式：点阵&长,宽,点阵总数量&偏色&命名）
        :return: 成功加载的字库数量，失败返回0
        """
        
        # 读取字库文件
        try:
            with open(font_library_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"读取字库文件失败: {e}")
            return 0
        print(lines)
        loaded_count = 0
        
        # 解析每一行字库数据
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 解析字库行：点阵&长,宽,点阵总数量&偏色&命名
            parts = line.split('&')
            if len(parts) != 4:
                continue
            
            matrix_hex, size_info, deviation_str, name = [p.strip() for p in parts]
            
            # 解析尺寸信息：长,宽,点阵总数量
            size_parts = size_info.split(',')
            if len(size_parts) != 3:
                continue
            
            try:
                width = int(size_parts[0])
                height = int(size_parts[1])
                total_count = int(size_parts[2])
            except ValueError:
                continue
            
            # 将16进制点阵转换为二值化图像
            # 点阵格式：每4位二进制转换为1个16进制字符
            binary_data = []
            for hex_char in matrix_hex:
                # 将16进制字符转换为4位二进制
                bits = format(int(hex_char, 16), '04b')
                binary_data.extend([int(bit) for bit in bits])
            
            # 只取前 width * height 位
            total_pixels = width * height
            binary_data = binary_data[:total_pixels]
            
            # 将二进制数据转换为numpy数组（重塑为图像形状）
            # 白色(1)对应255，黑色(0)对应0
            binary_array = np.array(binary_data, dtype=np.uint8).reshape((height, width))
            binary_array = np.where(binary_array == 1, 255, 0).astype(np.uint8)
            
            # 转换为 template_mask (0/1掩码)
            template_mask = (binary_array == 255).astype(np.uint8)
            
            # 存储到全局缓存（支持同名多个条目，使用列表存储）
            if name not in self.font_library_cache:
                self.font_library_cache[name] = []
            
            self.font_library_cache[name].append({
                'template_mask': template_mask,
                'width': width,
                'height': height,
                'total_count': total_count,
                'deviation': deviation_str,
                'matrix_hex': matrix_hex
            })
            
            loaded_count += 1
        
        print(f"成功加载 {loaded_count} 个字库到缓存")
        return loaded_count

    def opencv字库找图(self, large_image_path, font_name, similarity=0.9, region=(0, 0, 0, 0)):
        """
        根据字库名字进行颜色偏色找图（从全局缓存中读取字库数据）
        
        注意：使用此函数前，需要先调用 加载字库文件() 函数将字库加载到全局缓存中
        支持同名多个字库条目，会遍历所有同名条目，只要有一个符合相似度就返回
        
        :param large_image_path: 大图路径
        :param font_name: 字库名字（需要在全局缓存中存在）
        :param similarity: 相似度阈值，0-1之间，默认0.9
        :param region: 检测区域 (x, y, width, height)，如果全为0则检测整个大图
        :return: 找到的位置 {"x": x, "y": y, "w": w, "h": h, "similarity": similarity} 或 None
        """
        # 从全局缓存中获取字库数据（支持同名多个条目）
        if font_name not in self.font_library_cache:
            print(f"未找到字库: {font_name}，请先调用 加载字库文件() 函数加载字库")
            return None
        
        font_data_list = self.font_library_cache[font_name]
        if not font_data_list:
            print(f"字库 {font_name} 的条目列表为空")
            return None
        
        # 读取大图（只需要读取一次）
        large_img = Image.open(large_image_path).convert('RGB')
        large_array = np.array(large_img)
        
        if large_array is None:
            return None
        
        # 获取大图尺寸
        large_h, large_w = large_array.shape[:2]
        
        # 解析检测区域
        x, y, width, height = region
        
        # 判断是否指定了检测区域
        if x == 0 and y == 0 and width == 0 and height == 0:
            search_area = large_array
            offset_x, offset_y = 0, 0
        else:
            # 确保区域在图像范围内
            if x < 0: x = 0
            if y < 0: y = 0
            if width <= 0: width = large_w - x
            if height <= 0: height = large_h - y
            
            crop_x = max(0, x)
            crop_y = max(0, y)
            crop_width = min(width, large_w - crop_x)
            crop_height = min(height, large_h - crop_y)
            
            if crop_width <= 0 or crop_height <= 0:
                return None
            
            search_area = large_array[crop_y:crop_y + crop_height, crop_x:crop_x + crop_width]
            offset_x, offset_y = crop_x, crop_y
        
        # 遍历所有同名字库条目
        for idx, font_data in enumerate(font_data_list):
            template_mask = font_data['template_mask']
            white_points = font_data['total_count']
            small_w = font_data['width']
            small_h = font_data['height']
            
            # 检查小图是否大于检测区域
            if small_h > search_area.shape[0] or small_w > search_area.shape[1]:
                continue
            
            # 解析偏色信息（多个偏色用|连接）
            deviation_str = font_data['deviation']
            color_tolerances = deviation_str.split('|')
            
            # 初始化二值化结果
            search_binary_combined = np.zeros((search_area.shape[0], search_area.shape[1]), dtype=np.uint8)
            
            # 对每个颜色容差进行二值化处理并合并
            for color_tol in color_tolerances:
                color_tol = color_tol.strip()
                if not color_tol:
                    continue
                print(color_tol) 
                # 解析颜色偏色字符串
                try:
                    base_color_hex, tolerance_hex = color_tol.split('-')
                    base_color = np.array([
                        int(base_color_hex[0:2], 16),
                        int(base_color_hex[2:4], 16),
                        int(base_color_hex[4:6], 16)
                    ], dtype=np.int16)
                    tolerance = np.array([
                        int(tolerance_hex[0:2], 16),
                        int(tolerance_hex[2:4], 16),
                        int(tolerance_hex[4:6], 16)
                    ], dtype=np.int16)
                except Exception as e:
                    print(f"解析偏色字符串失败: {color_tol}, 错误: {e}")
                    continue
              
                # 二值化处理
                search_int16 = search_area.astype(np.int16)
                search_diff = np.abs(search_int16 - base_color)
                search_mask = np.all(search_diff <= tolerance, axis=2)
                search_binary = np.where(search_mask, 255, 0).astype(np.uint8)
                
                # 合并多个颜色容差的二值化结果（使用 OR 操作）
                search_binary_combined = np.bitwise_or(search_binary_combined, search_binary)

            # 将大图二值结果也转换为 0/1 掩码
            search_mask = (search_binary_combined == 255).astype(np.uint8)

            # 使用 TM_CCORR 对两个 0/1 掩码做匹配
            result = cv2.matchTemplate(search_mask, template_mask, cv2.TM_CCORR)
            
            # 找到重合白点最多的位置
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            # 自定义相似度：重合白点数 / 模板白点总数，范围[0,1]
            overlap_white = max_val
            custom_similarity = overlap_white / white_points if white_points > 0 else 0
            
            print(f"字库找图 - 字库名: {font_name}, 条目索引: {idx}/{len(font_data_list)-1}, 重合白点: {overlap_white}, 相似度: {custom_similarity:.4f}, 位置: {max_loc}")
            
            # 如果符合相似度要求，立即返回
            if custom_similarity >= similarity:
                return {
                    "x": max_loc[0] + offset_x,
                    "y": max_loc[1] + offset_y,
                    "w": small_w,
                    "h": small_h,
                    "similarity": float(custom_similarity)
                }
        
        # 所有条目都遍历完，没有找到符合相似度的，返回 None
        # print(f"字库找图 - 字库名: {font_name}, 遍历了 {len(font_data_list)} 个条目，均未达到相似度要求 {similarity}")
        return None

    def yolo(self, image_path, model_path, conf_threshold=0.6):
        """
        使用YOLOv8模型检测图片中的目标
        
        参数:
            image_path: 图片路径
            conf_threshold: 置信度阈值，默认0.6
        
        返回:
            检测结果列表，每个元素是一个字典，包含:
            - class_name: 分类名
            - confidence: 相似度/置信度
            - x: 边界框中心x坐标
            - y: 边界框中心y坐标
            - w: 边界框宽度
            - h: 边界框高度
        """
        model = self._获取模型(model_path)
        
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
    
    def _获取模型(self, model_path):
        """获取YOLO模型实例（懒加载）"""
        if model_path != self._model_path:
            self._model_path = model_path
            self._model = YOLO(model_path)
        
        return self._model
    
    def init_client(self, url="http://127.0.0.1:7072"):
        """初始化 Socket.IO 客户端"""
        if not hasattr(self, '_socketio_client') or self._socketio_client is None:
            self._socketio_client = socketio.Client()
        
        if not self._socketio_client.connected:
            try:
                self._socketio_client.connect(url)
            except Exception as e:
                print(f"Socket.IO 连接失败: {e}")
        
        return self._socketio_client
    
    def send_to_electron(self, prop, message, method="controller/example/changeProp",
                            url="http://127.0.0.1:7072", wait_response=True):
            """向 Electron 发送数据"""
            try:
                client = self.init_client(url)
                data = {"cmd": method, "args": {"deviceId": self.device_id, "prop": prop, "message": message}}
                
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


class Field:
    """字段查找类"""
    
    def __init__(self, config, controller):
        """
        初始化字段
        
        参数:
            config: 配置字典
            controller: DeviceController实例
        """
        self.controller = controller
        self.日志 = config.get("日志")
        self.方式 = config.get("方式")
        self.查找字符串 = config.get("查找字符串")
        self.大图路径 = config.get("大图路径")
        self.相似度 = config.get("相似度", 0.8)
        self.分类名 = config.get("分类名")
        self.模型路径 = config.get("模型路径")
        self.查找区域 = config.get("查找区域", [0, 0, 0, 0])
        self.偏移点击区域 = config.get("偏移点击区域")
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0
    
    def 查找(self):
        """查找字段"""
        url = self.大图路径 if self.大图路径 else self.controller.截图()
        if url:
            if self.方式 == "yolo":
                result = self.controller.yolo(url, self.模型路径, self.相似度)
                if len(result):
                    rx, ry, _, _ = self.查找区域
                    for r in result:
                        if r["class_name"] == self.分类名:
                            self.x = rx + math.ceil(r["x"])
                            self.y = ry + math.ceil(r["y"])
                            self.w = math.floor(r["w"])
                            self.h = math.floor(r["h"])
                            break
            else:
                result = self.controller.opencv字库找图(
                    url,
                    self.查找字符串,
                    self.相似度,
                    self.查找区域
                )
                if result:
                    self.x = result["x"]
                    self.y = result["y"]
                    self.w = result["w"]
                    self.h = result["h"]
        return self
    
    def 点击(self, x=None, y=None, w=None, h=None):
        """点击字段"""
        if self.是否找到():
            if x and y and w and h:
                self.controller.随机ADB点击(x, y, w, h)
            elif x and y:
                self.controller.ADB点击(x, y)
            # 没有传入x,y,w,h时,则先看偏移点击区域是否存在,如果存在则点击偏移点击区域
            elif self.偏移点击区域:
                self.偏移点击(*self.偏移点击区域)
            elif self.x and self.y:
                self.controller.随机ADB点击(self.x, self.y, self.w, self.h)
            
        return self
    def 偏移点击(self, x=None, y=None, w=None, h=None):
        """偏移点击"""
        if self.是否找到():
            if not w and not h:
                self.controller.ADB点击(self.x + x, self.y + y)
            if w and h:
                self.controller.随机ADB点击(self.x + x, self.y + y, w, h)
        return self
    
    def 随机延时(self, startMs, endMs):
        """随机延时"""
        if self.是否找到():
            self.controller.随机延时(startMs, endMs)
        return self
    
    def 设置查找区域(self, 查找区域):
        """设置查找区域"""
        self.查找区域 = 查找区域
        return self
    
    def 设置大图路径(self, 大图路径):
        """设置大图路径"""
        self.大图路径 = 大图路径
        return self
    
    def 设置日志(self, 日志):
        """设置日志"""
        self.日志 = 日志
        return self
    
    def 是否找到(self):
        """判断是否找到"""
        return bool(self.x and self.y)


class TaskLineMachine:
    """任务状态机类"""
    
    def __init__(self, device_id):
        """
        初始化任务状态机
        
        参数:
            controller: DeviceController实例
        """
        self.controller = DeviceController(device_id)
        self._states = {}
        self._current_interface = None
        self._previous_interface = None
        self._is_running = False
        self._context = {}  # 上下文信息
        self._unknown_start_time = None  # 未知界面开始时间
        self._unknown_timeout = 60  # 未知界面超时时间（秒）
    
    def state(self, Field):
        """装饰器：直接注册界面处理函数"""
        def decorator(func):
            self._states[Field['界面']] = {
                'handler': func,
                'Field': Field
            }
        return decorator
    
    def _copy_unknown_screenshot(self, url):
        """复制未知界面截图到unknown文件夹"""
        import shutil
        try:
            # 创建unknown文件夹
            unknown_dir = os.path.join(os.path.dirname(__file__), "resource", "unknown")
            os.makedirs(unknown_dir, exist_ok=True)
            
            # 生成带时间戳的文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"unknown_{timestamp}.png"
            dest_path = os.path.join(unknown_dir, filename)
            
            # 复制文件
            shutil.copy(url, dest_path)
            print(f"未知界面截图已保存: {dest_path}")
        except Exception as e:
            print(f"复制未知界面截图失败: {e}")
    
    def _play_alert_music(self):
        """播放提示音乐"""
        import threading
        try:
            music_path = os.path.join(os.path.dirname(__file__), "resource", "music.mp3")
            if os.path.exists(music_path):
                # 在后台线程播放，避免阻塞主程序
                def play():
                    try:
                        from playsound import playsound
                        playsound(music_path)
                    except ImportError:
                        # 如果没有playsound，尝试使用系统命令
                        import platform
                        if platform.system() == 'Windows':
                            os.system(f'start "" "{music_path}"')
                        elif platform.system() == 'Darwin':  # macOS
                            os.system(f'afplay "{music_path}" &')
                        else:  # Linux
                            os.system(f'mpg123 "{music_path}" &')
                    except Exception as e:
                        print(f"播放音乐失败: {e}")
                
                thread = threading.Thread(target=play, daemon=True)
                thread.start()
                print("正在播放提示音乐...")
            else:
                print(f"音乐文件不存在: {music_path}")
        except Exception as e:
            print(f"播放音乐出错: {e}")
    
    def start(self):
        """启动状态机"""
        self._is_running = True
        
        while self._is_running:
            try:
                url = self.controller.截图()
                if url:
                    是否找到 = False
                    for state in self._states.values():
                        handler = state['handler']
                        config = state['Field']
                        if Field(config, self.controller).设置大图路径(url).查找().是否找到():
                            是否找到 = True
                            print(f"目前位于: {config['界面']}")
                            self.update_context(上一状态=self._current_interface)
                            self._current_interface = config['界面']
                            # 找到已知界面，重置未知界面计时器
                            self._unknown_start_time = None
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
                        
                        # 未知界面计时逻辑
                        if self._unknown_start_time is None:
                            self._unknown_start_time = time.time()
                        else:
                            elapsed = time.time() - self._unknown_start_time
                            if elapsed >= self._unknown_timeout:
                                print(f"未知界面已持续 {elapsed:.1f} 秒，保存截图")
                                # 截图
                                self._copy_unknown_screenshot(url)
                                # 播放提示音乐
                                self._play_alert_music()
                                # 重置计时器，避免重复保存
                                self._unknown_start_time = time.time()
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

    def Field(self, config):
        return Field(config,self.controller)

    