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
    
    def opencv找图(self, large_image_path, small_image_path, similarity=0.9, region=(0, 0, 0, 0)):
        """
        在大图中查找小图
        :param large_image_path: 大图路径
        :param small_image_path: 小图路径
        :param similarity: 相似度阈值，0-1之间
        :param region: 检测区域 (x, y, width, height)，如果全为0则检测整个大图
        :return: 找到的位置 {"x": x, "y": y} 或 None
        """
        # 读取图像
        large_image = cv2.imread(large_image_path)
        small_image = cv2.imread(small_image_path)
        
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
        
        # 使用模板匹配
        result = cv2.matchTemplate(search_area, small_image, cv2.TM_CCOEFF_NORMED)
        
        # 找到最匹配的位置
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # 检查是否达到相似度阈值
        if max_val >= similarity:
            # 返回相对于整个大图的坐标（加上偏移量）
            return {"x": max_loc[0] + offset_x, "y": max_loc[1] + offset_y, 'w': w, 'h': h, 'similarity': max_val}
        
        return None
    
    def opencv找透明图(self, large_img_path, small_img_path, tolerance=0, similarity=0.9, region=(0, 0, 0, 0)):
        """
        在大图的指定区域中查找小图（仅支持图片路径）
        
        参数:
            large_img_path: 大图路径
            small_img_path: 小图路径
            tolerance: 像素颜色容差 (0-255)
            similarity: 相似度阈值 (0.0-1.0)
            region: 检测区域 (x, y, width, height)，如果全为0或超出范围则检测整个大图
        
        返回:
            如果找到: {"x": x, "y": y, "similarity": similarity, "width": width, "height": height}
            如果没找到: None
        """
        try:
            # 1. 检查文件是否存在
            if not os.path.exists(large_img_path):
                print(f"大图不存在: {large_img_path}")
                return None
            if not os.path.exists(small_img_path):
                print(f"小图不存在: {small_img_path}")
                return None
            
            # 2. 加载大图（带Alpha通道）
            large_img = cv2.imread(large_img_path, cv2.IMREAD_UNCHANGED)
            if large_img is None:
                print(f"无法加载大图: {large_img_path}")
                return None
                
            # 确保有Alpha通道
            if large_img.shape[2] == 3:
                large_img = cv2.cvtColor(large_img, cv2.COLOR_BGR2BGRA)
            
            # 3. 加载小图（带Alpha通道）
            small_img = cv2.imread(small_img_path, cv2.IMREAD_UNCHANGED)
            if small_img is None:
                print(f"无法加载小图: {small_img_path}")
                return None
                
            # 确保有Alpha通道
            if small_img.shape[2] == 3:
                small_img = cv2.cvtColor(small_img, cv2.COLOR_BGR2BGRA)
            
            # 4. 获取图像尺寸
            large_h, large_w = large_img.shape[:2]
            small_h, small_w = small_img.shape[:2]
            
            # 5. 处理检测区域
            region_x, region_y, region_w, region_h = region
            
            # 检查是否应该检测整个图像
            use_full_image = False
            if region_w <= 0 or region_h <= 0:
                use_full_image = True
            elif (region_x < 0 or region_y < 0 or 
                  region_x + region_w > large_w or region_y + region_h > large_h):
                print(f"检测区域超出图像范围，改为全图检测")
                use_full_image = True
            
            if use_full_image:
                region_x, region_y = 0, 0
                region_w, region_h = large_w, large_h
                crop_img = large_img
            else:
                # 裁剪出指定区域
                crop_img = large_img[region_y:region_y+region_h, region_x:region_x+region_w]
            
            # 6. 检查小图是否大于区域
            if small_w > region_w or small_h > region_h:
                print(f"小图尺寸({small_w}x{small_h})大于检测区域({region_w}x{region_h})")
                return None
            
            # 7. 提取小图的Alpha通道作为掩码
            # 分离通道
            s_b, s_g, s_r, s_a = cv2.split(small_img)
            
            # 创建掩码：Alpha > 0 的部分为 255，否则为 0
            _, mask = cv2.threshold(s_a, 0, 255, cv2.THRESH_BINARY)
            
            # 8. 模板匹配
            # 使用不同的匹配方法提高准确性
            methods = [
                (cv2.TM_CCOEFF_NORMED, 1.0),  # 相关系数归一化
                (cv2.TM_CCORR_NORMED, 1.0),   # 相关归一化
            ]
            
            best_match = None
            best_val = 0
            crop_h, crop_w = crop_img.shape[:2]
            
            # 转换为BGR用于匹配（保留掩码）
            crop_bgr = cv2.cvtColor(crop_img, cv2.COLOR_BGRA2BGR)
            small_bgr = cv2.cvtColor(small_img, cv2.COLOR_BGRA2BGR)
        
            # 计算匹配结果
            for method, weight in methods:
                result = cv2.matchTemplate(crop_bgr, small_bgr, method, mask=mask)
                
                # 找到最大值和最小值的位置
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
      
                # 根据匹配方法选择最佳位置
                if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                    current_val = 1 - min_val  # 对于平方差方法，值越小越好
                    current_loc = min_loc
                else:
                    current_val = max_val
                    current_loc = max_loc
                
                # 应用权重
                weighted_val = current_val * weight
                
                if weighted_val > best_val:
                    best_val = weighted_val
                    best_match = current_loc 
            # 9. 如果匹配度不足，直接返回

            if best_val < similarity:
                return None
            
            # 将区域内的坐标转换为大图坐标
            start_x = region_x + best_match[0]
            start_y = region_y + best_match[1]

            # 10. 根据容差进行二次像素级验证
            final_similarity = best_val
            if tolerance > 0:
                # 准备像素数据
                total_pixels = 0
                matched_pixels = 0
                
                # 提取小图的RGBA数据
                s_b, s_g, s_r, s_a = cv2.split(small_img)
                
                # 获取匹配区域在大图中的位置
                end_x = start_x + small_w
                end_y = start_y + small_h
                
                # 确保不超出大图边界（包括起始坐标为负数的情况）
                if start_x < 0 or start_y < 0 or end_x > large_w or end_y > large_h:
                    return None
                
                # 提取匹配区域
                match_area = large_img[start_y:end_y, start_x:end_x]
                
                # 检查匹配区域是否为空
                if match_area.size == 0:
                    return None
                
                # 确保匹配区域有4个通道（BGRA）
                if len(match_area.shape) < 3 or match_area.shape[2] != 4:
                    # 如果只有3个通道，添加Alpha通道
                    if len(match_area.shape) == 3 and match_area.shape[2] == 3:
                        match_area = cv2.cvtColor(match_area, cv2.COLOR_BGR2BGRA)
                    else:
                        return None
                
                # 分离匹配区域的通道
                m_b, m_g, m_r, m_a = cv2.split(match_area)
                
                # 遍历像素
                for y in range(small_h):
                    for x in range(small_w):
                        # 跳过小图中的透明像素
                        if s_a[y, x] == 0:
                            continue
                        
                        total_pixels += 1
                        
                        # 获取小图像素值
                        sr, sg, sb, sa = s_r[y, x], s_g[y, x], s_b[y, x], s_a[y, x]
                        
                        # 获取大图对应位置像素值
                        mr, mg, mb, ma = m_r[y, x], m_g[y, x], m_b[y, x], m_a[y, x]
                        
                        # 计算颜色差异
                        r_diff = abs(int(sr) - int(mr))
                        g_diff = abs(int(sg) - int(mg))
                        b_diff = abs(int(sb) - int(mb))
                        a_diff = abs(int(sa) - int(ma))
                        
                        # 检查是否在容差范围内
                        if (r_diff <= tolerance and g_diff <= tolerance and 
                            b_diff <= tolerance and a_diff <= tolerance):
                            matched_pixels += 1
                
                # 计算像素级匹配率
                pixel_match_rate = matched_pixels / total_pixels if total_pixels > 0 else 0
                # 如果像素级匹配度不足，返回None
                if pixel_match_rate < similarity:
                    return None
                
                final_similarity = pixel_match_rate
            
            # 11. 返回结果
            return {
                "x": start_x,
                "y": start_y,
                "similarity": float(final_similarity),
                "w": small_w,
                "h": small_h,
                "region_used": (region_x, region_y, region_w, region_h)
            }
            
        except Exception as e:
            print(f"找图出错: {str(e)}")
            import traceback
            traceback.print_exc()
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
    
    def init_client(self, url="http://127.0.0.1:7070"):
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
                         url="http://127.0.0.1:7070", wait_response=True):
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
        self.查找区域 = config.get("查找区域", {"x": 0, "y": 0, "w": 0, "h": 0})
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0
        self.是否判断状态 = False
    
    def 查找(self):
        """查找字段"""
        url = self.大图路径 if self.大图路径 else self.controller.截图()
        if url:
            if self.方式 == "opencv找图":
                result = self.controller.opencv找图(url, self.图片路径, self.相似度, 
                                                    (self.查找区域["x"], self.查找区域["y"],
                                                     self.查找区域["w"], self.查找区域["h"]))
                if result:
                    self.x = result["x"]
                    self.y = result["y"]
                    self.w = result["w"]
                    self.h = result["h"]
            elif self.方式 == "opencv找透明图":
                result = self.controller.opencv找透明图(url, self.图片路径, 50, self.相似度,
                                                        (self.查找区域["x"], self.查找区域["y"],
                                                         self.查找区域["w"], self.查找区域["h"]))
                if result:
                    self.x = result["x"]
                    self.y = result["y"]
                    self.w = result["w"]
                    self.h = result["h"]
            elif self.方式 == "opencv找透明图2":
                result = self.controller.opencv找透明图2(url, self.图片路径, self.相似度,
                                                        (self.查找区域["x"], self.查找区域["y"],
                                                         self.查找区域["w"], self.查找区域["h"]))
                if result:
                    self.x = result["x"]
                    self.y = result["y"]
                    self.w = result["w"]
                    self.h = result["h"]
            elif self.方式 == "yolo":
                result = self.controller.yolo(url, self.模型路径, self.相似度)
                if len(result):
                    for r in result:
                        if r["class_name"] == self.分类名:
                            print(r)
                            self.x = self.查找区域["x"] + math.ceil(r["x"])
                            self.y = self.查找区域["y"] + math.ceil(r["y"])
                            self.w = math.floor(r["w"])
                            self.h = math.floor(r["h"])
                            break
        if self.是否判断状态:
            self.controller.写入日志(f"{self.标识}: {'是' if self.是否找到() else '否'}")
        return self
    
    def 点击(self, x=None, y=None, w=None, h=None):
        """点击字段"""
        if self.是否找到():
            if x and y and w and h:
                self.controller.随机ADB点击(x, y, w, h)
            elif x and y:
                self.controller.ADB点击(x, y)
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
            
            if self.标识:
                self.controller.写入日志(f"{self.标识}")
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
    
    def 设置标识(self, 标识, 是否判断状态=False):
        """设置标识"""
        self.标识 = 标识
        self.是否判断状态 = 是否判断状态
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

    