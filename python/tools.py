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
        self._model_path = ""
        self._model = None
        self._socketio_client = None
        # 初始化 Socket.IO 客户端（可选，延迟连接）
        self.init_client()
        # self.send_to_electron("abc", '123')
        
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
    
    def opencv找图(self, large_image_path, small_image_path, similarity=0.9, region=None):
        """
        在大图中查找小图
        :param large_image_path: 大图路径
        :param small_image_path: 小图路径
        :param similarity: 相似度阈值，0-1之间
        :param region: 检测区域 [x, y, w, h]，如果全为0则检测整个大图
        :return: 找到的位置 {"x": x, "y": y} 或 None
        """
        # 默认使用全图区域 [0, 0, 0, 0]
        if region is None:
            region = [0, 0, 0, 0]
        
        # 读取图像
        large_image = cv2.imread(large_image_path)
        small_image = cv2.imread(small_image_path)
        
        if large_image is None or small_image is None:
            return None
        
        # 获取大图尺寸
        large_h, large_w = large_image.shape[:2]
        
        # 解析检测区域 [x, y, w, h]
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
        
        # 使用模板匹配
        result = cv2.matchTemplate(search_area, small_image, cv2.TM_CCOEFF_NORMED)
        
        # 找到最匹配的位置
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # 检查是否达到相似度阈值
        if max_val >= similarity:
            # 返回相对于整个大图的坐标（加上偏移量）
            return {"x": max_loc[0] + offset_x, "y": max_loc[1] + offset_y, 'w': w, 'h': h, 'similarity': max_val}
        
        return None
    
    def opencv颜色偏色找图(self,large_image_path, small_image_path, color_tolerance, similarity=0.8, region=None):
        """
        使用颜色偏色二值化后进行模板匹配找图

        :param large_image_path: 大图路径
        :param small_image_path: 小图路径
        :param color_tolerance: 颜色偏色字符串或字符串数组，格式如 "D7CCC6-0E0E09" 或 ["D7CCC6-0E0E09", "FFFFFF-101010"]
                            其中D7CCC6为基准色(RGB)，0E0E09为RGB各通道的允许偏差
                            支持多个颜色容差，会合并所有匹配的颜色区域
        :param similarity: 相似度阈值，0-1之间，默认0.8
        :param region: 检测区域 [x, y, w, h]，如果全为0则检测整个大图
        :return: 找到的位置 {"x": x, "y": y, "w": w, "h": h, "similarity": similarity} 或 None
        """
        # 默认使用全图区域 [0, 0, 0, 0]
        if region is None:
            region = [0, 0, 0, 0]
        # 读取图像
        large_img = Image.open(large_image_path).convert('RGB')
        small_img = Image.open(small_image_path).convert('RGB')

        large_array = np.array(large_img)
        small_array = np.array(small_img)

        if large_array is None or small_array is None:
            return None

        # 获取大图尺寸
        large_h, large_w = large_array.shape[:2]
        small_h, small_w = small_array.shape[:2]

        # 解析检测区域 [x, y, w, h]
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

        # 检查小图是否大于检测区域
        if small_h > search_area.shape[0] or small_w > search_area.shape[1]:
            return None

        # 将 color_tolerance 转换为数组（支持单个字符串或数组）
        if isinstance(color_tolerance, str):
            color_tolerances = [color_tolerance]
        elif isinstance(color_tolerance, (list, tuple)):
            color_tolerances = list(color_tolerance)
        else:
            return None

        # 初始化二值化结果
        search_binary_combined = np.zeros((search_area.shape[0], search_area.shape[1]), dtype=np.uint8)
        small_binary_combined = np.zeros((small_h, small_w), dtype=np.uint8)

        # 对每个颜色容差进行二值化处理并合并
        for color_tol in color_tolerances:
            # 解析颜色偏色字符串
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

            # 二值化处理
            search_int16 = search_area.astype(np.int16)
            search_diff = np.abs(search_int16 - base_color)
            search_mask = np.all(search_diff <= tolerance, axis=2)
            search_binary = np.where(search_mask, 255, 0).astype(np.uint8)

            small_int16 = small_array.astype(np.int16)
            small_diff = np.abs(small_int16 - base_color)
            small_mask = np.all(small_diff <= tolerance, axis=2)
            small_binary = np.where(small_mask, 255, 0).astype(np.uint8)

            # 合并多个颜色容差的二值化结果（使用 OR 操作）
            search_binary_combined = np.bitwise_or(search_binary_combined, search_binary)
            small_binary_combined = np.bitwise_or(small_binary_combined, small_binary)

        # 自定义"白点匹配率"相似度
        # 只考虑小图中的白色像素，计算它们在大图中对应位置也是白色的比例
        template_mask = (small_binary_combined == 255).astype(np.uint8)

        # 将大图二值结果也转换为 0/1 掩码
        search_mask = (search_binary_combined == 255).astype(np.uint8)
        # cv2.imshow('small_binary_combined Threshold', small_binary_combined)
        # cv2.imshow('search_binary_combined Threshold', search_binary_combined)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        # 使用 TM_CCORR 对两个 0/1 掩码做匹配
        # 对于 0/1 掩码，TM_CCORR 的结果等于滑动窗口内 search_mask * template_mask 的和，
        result = cv2.matchTemplate(search_mask, template_mask, cv2.TM_CCORR)

        # 找到重合白点最多的位置
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        white_points = int(np.sum(template_mask))

        # 相似度过关了,就不关注重合白点个数了, 后续关注区域内白点个数相似度, 找到最合适的点

        if((max_val / white_points) < similarity):
            return None

        # 找到所有超过相似度阈值的位置
        locations = np.where(result >= (white_points * similarity) )

        matches = []
        for y, x in zip(locations[0], locations[1]):
            sum_val = np.sum(search_mask[y:y+small_h, x:x+small_w])
            diff = int(white_points) - int(sum_val)

            matches.append({
                'x': x,
                'y': y,
                'w': small_w,
                'h': small_h,
                'score': result[y, x], # 可以得到这个区域重合的白点个数
                'count_similarity': 1 - (abs(diff)/(small_w * small_h)) # 可以得到这个区域白点个数相似度
            })
        # 找到白点个数相似度最高的点
        max_item = max(matches, key=lambda x: x['count_similarity'])
        
        overlap_white = max_item['score']
        
        custom_similarity = overlap_white / white_points

        # 先计算最终相似度，再保留 4 位小数
        final_similarity = custom_similarity * 0.8 + max_item['count_similarity'] * 0.2
        final_similarity = float(f"{final_similarity:.4f}")

        print(
            f"自定义白点匹配率 - 重合白点: {overlap_white}, 小图白点: {white_points}, "
            f"个数相似度: {max_item['count_similarity']:.4f}, 重合相似度: {custom_similarity:.4f}, "
            f"位置: {max_loc}, 最终相似度: {final_similarity:.4f}"
        )

        
        if final_similarity >= similarity:
            return {
                "x": max_loc[0] + offset_x,
                "y": max_loc[1] + offset_y,
                "w": small_w,
                "h": small_h,
                "similarity": final_similarity
            }
        return None
    
    def 找图(self, large_image_path, small_image_path, similarity=0.9, region=None, color_tolerance=None):
        """
        找图函数，根据是否传入颜色偏色参数自动选择找图方式
        
        参数:
            large_image_path: 大图路径
            small_image_path: 小图路径
            similarity: 相似度阈值，0-1之间，默认0.9
            region: 检测区域 [x, y, w, h]，如果全为0则检测整个大图
            color_tolerance: 颜色偏色参数，格式如 "D7CCC6-0E0E09" 或 ["D7CCC6-0E0E09", "FFFFFF-101010"]
                          如果传入此参数，则使用颜色偏色找图；如果不传入或为None，则使用普通找图
        
        返回:
            找到的位置 {"x": x, "y": y, "w": w, "h": h, "similarity": similarity} 或 None
        """
        # 默认使用全图区域 [0, 0, 0, 0]
        if region is None:
            region = [0, 0, 0, 0]

        if color_tolerance is not None:
            # 如果传入了颜色偏色参数，使用颜色偏色找图
            return self.opencv颜色偏色找图(large_image_path, small_image_path, color_tolerance, similarity, region)
        else:
            # 如果没有传入颜色偏色参数，使用普通找图
            return self.opencv找图(large_image_path, small_image_path, similarity, region)
    
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
        self.标识 = config.get("标识")
        self.方式 = config.get("方式")
        self.图片路径 = config.get("图片路径")
        self.大图路径 = config.get("大图路径")
        self.相似度 = config.get("相似度", 0.8)
        self.分类名 = config.get("分类名")
        self.模型路径 = config.get("模型路径")
        self.颜色偏色 = config.get("颜色偏色")  # 格式如 "D7CCC6-0E0E09"
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
            if self.方式 == "找图":
                result = self.controller.找图(
                    url,
                    self.图片路径,
                    self.相似度,
                    self.查找区域,
                    self.颜色偏色
                )
                if result:
                    self.x = result["x"]
                    self.y = result["y"]
                    self.w = result["w"]
                    self.h = result["h"]
            elif self.方式 == "yolo":
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
                self.controller.随机ADB点击(*self.偏移点击区域)
            elif self.x and self.y:
                self.controller.随机ADB点击(self.x, self.y, self.w, self.h)
            
            if self.标识:
                self.controller.写入日志(f"{self.标识}")
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
    
    def 设置标识(self, 标识):
        """设置标识"""
        self.标识 = 标识
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
            self._states[Field['标识']] = {
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
                            print(f"目前位于: {config['标识']}")
                            self.update_context(上一状态=self._current_interface)
                            self._current_interface = config['标识']
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

    