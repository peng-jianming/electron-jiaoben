# import json
import random

# import websockets
import os
import time

# import asyncio
import cv2
from ultralytics import YOLO
import math
import numpy as np
from PIL import Image
import socketio
from abdTools import ADBController
from resource.config import 界面集合
from io import BytesIO


class ScreenshotContext:
    """截图上下文管理器，同一轮次复用截图"""
    
    def __init__(self, controller):
        self._controller = controller
        self._当前截图 = None
    
    def 新轮次(self):
        """开始新一轮检测，清除缓存的截图"""
        self._当前截图 = None
    
    def get_截图(self):
        """懒加载截图，同轮次内复用"""
        if self._当前截图 is None:
            self._当前截图 = self._controller.截图到内存()
        return self._当前截图



class DeviceController:
    """设备控制器类，封装所有设备操作功能"""

    def __init__(self, device_id):
        """
        初始化设备控制器

        参数:
            device_id: 设备ID
        """
        self.device_id = device_id
        self.adb = ADBController(device_id)
        self._socketio_client = None
        # 初始化 Socket.IO 客户端（可选，延迟连接）
        self.init_client()
        # 点击位置监控，记录最后一次点击的位置和时间
        # self._last_click_position = None  # 记录最后点击的位置 (x, y, w, h)
        # self._last_click_time = None  # 记录最后点击的时间

    def 写入日志(self, info):
        """写入日志"""
        self.send_to_electron("logs", info)

    def 截图到内存(self):
        """
        截图并直接返回 PIL Image 对象（不保存到文件，性能更好）

        返回:
            PIL Image 对象，失败返回 None
        """
        try:
            # 使用 ADB 直接获取图像字节流
            image_bytes = self.adb.截图到内存()
            if image_bytes is None:
                return None

            image = Image.open(BytesIO(image_bytes))
            return image.convert("RGB")
        except Exception as e:
            print(f"内存截图失败: {e}")
            return None

    def 截图到本地(self):
        save_dir = os.path.join(os.path.dirname(__file__), "resource", "cache")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{self.device_id}.png")
        return self.adb.截图(save_path)
        
    def ADB点击(self, x, y):
        if x and y:
            self.adb.模拟点击(x, y, (0, 0.3))

    def 随机ADB点击(self, x, y, w, h):
        """
        随机ADB点击，带8秒内同位置防重复点击监控
        如果已经点击了其他位置，则不存在这个限制
        
        参数:
            x: 点击区域左上角x坐标
            y: 点击区域左上角y坐标
            w: 点击区域宽度
            h: 点击区域高度
        """
        if x and y and w and h:
            # # 使用区域坐标作为键来标识点击位置
            # click_key = (x, y)
            # current_time = time.time()
            
            # # 只有当当前点击位置和最后一次点击位置相同时，才检查8秒限制
            # if (self._last_click_position == click_key and 
            #     self._last_click_time is not None):
            #     time_since_last_click = current_time - self._last_click_time
                
            #     if time_since_last_click < 25:
            #         # 25秒内重复点击同一位置，跳过
            #         print(f"跳过重复点击: 位置({x}, {y}, {w}, {h}) 距离上次点击仅 {time_since_last_click:.2f} 秒")
            #         return
            
            # 执行点击
            random_x = random.randint(x, x + w)
            random_y = random.randint(y, y + h)
            self.adb.模拟点击(random_x, random_y, (0, 0.3))
            
            # 记录本次点击位置和时间（如果点击了其他位置，会更新这里，从而清除之前位置的限制）
            # self._last_click_position = click_key
            # self._last_click_time = current_time

    def init_client(self, url="http://127.0.0.1:7072"):
        """初始化 Socket.IO 客户端"""
        if not hasattr(self, "_socketio_client") or self._socketio_client is None:
            self._socketio_client = socketio.Client()

        if not self._socketio_client.connected:
            try:
                self._socketio_client.connect(url)
            except Exception as e:
                print(f"Socket.IO 连接失败: {e}")

        return self._socketio_client

    def send_to_electron(
        self,
        prop,
        message,
        method="controller/example/changeProp",
        url="http://127.0.0.1:7072",
        wait_response=True,
    ):
        """向 Electron 发送数据"""
        try:
            client = self.init_client(url)
            data = {
                "cmd": method,
                "args": {"deviceId": self.device_id, "prop": prop, "message": message},
            }

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
    def __init__(self, config, controller, 截图上下文=None):
        self.controller = controller
        self._截图上下文 = 截图上下文  # 共享截图上下文
        self.日志 = config.get("日志")
        self.方式 = config.get("方式")
        self.查找字符串 = config.get("查找字符串")
        self.分类名 = config.get("分类名")
        self.大图路径 = config.get("大图路径")
        self.相似度 = config.get("相似度", 0.8)
        self.查找区域 = config.get("查找区域", [0, 0, 0, 0])
        self.偏移点击区域 = config.get("偏移点击区域")
        self.点击区域 = config.get("点击区域") # 找到后才会点击
        self.固定点击区域 = config.get("固定点击区域") # 不需要找到,直接点击
        self.字库集合 = {}
        self.模型 = None
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0
    
    def 设置截图上下文(self, 截图上下文):
        """设置截图上下文"""
        self._截图上下文 = 截图上下文
        return self
    
    def _获取截图(self):
        """自动获取截图：优先使用已设置的大图路径，其次从上下文获取，最后直接截图"""
        if self.大图路径:
            return self.大图路径
        if self._截图上下文:
            return self._截图上下文.get_截图()
        return self.controller.截图到内存()

    def 查找(self):
        if not self.查找字符串:
            return self
        # 使用自动获取截图
        截图 = self._获取截图()
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0
        if 截图:
            if self.方式 == "yolo":
                result = self._yolo(截图, self.模型路径, self.相似度)
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
                result = self._opencv字库找图(
                    截图, self.查找字符串, self.相似度, self.查找区域
                )
                if result:
                    self.x = result["target_x"]
                    self.y = result["target_y"]
                    self.w = result["target_w"]
                    self.h = result["target_h"]
        return self

    def 点击(self, x=None, y=None, w=None, h=None):
        """点击字段"""
        # 找到目标, 但是需要点击的位置需要根据找到目标位置进行划定,那么就需要偏移点击区域,
        # 找到目标, 但是需要点击的目标是固定位置, 那么就需要点击区域,
        # 找到目标, 点击目标位置就是找到的位置,那就直接点击找到的位置
        if self.是否找到():
            if x and y and w and h:
                self.controller.随机ADB点击(x, y, w, h)
            elif x and y:
                self.controller.ADB点击(x, y)
            elif self.偏移点击区域:
                self.偏移点击(*self.偏移点击区域)
            elif self.点击区域:
                self.controller.随机ADB点击(self.点击区域[0], self.点击区域[1], self.点击区域[2], self.点击区域[3])
            else :
                self.controller.随机ADB点击(self.x, self.y, self.w, self.h)
        elif self.固定点击区域:
            self.controller.随机ADB点击(self.固定点击区域[0], self.固定点击区域[1], self.固定点击区域[2], self.固定点击区域[3])

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
        if self.是否找到() or self.固定点击区域:
            if startMs > endMs:
                startMs, endMs = endMs, startMs
            time.sleep(random.uniform(startMs, endMs))
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

    def 设置字库(self, 字库集合):
        if self.查找字符串 not in 字库集合:
            print(f"{self.查找字符串},不在字库里")
        self.字库集合 = 字库集合
        return self

    def 设置模型(self, 模型):
        self.模型 = 模型
        return self

    def 是否找到(self):
        """判断是否找到"""
        return bool(self.x and self.y)

    def 点击如果找到(self, 延时=(1, 3), 日志=None) -> bool:
        """
        简化API：查找目标，如果找到则点击并延时
        
        参数:
            延时: 点击后的随机延时范围，元组 (最小秒数, 最大秒数)
            日志: 可选的日志信息
        
        返回:
            bool: 是否找到并点击成功
        """
        self.查找()
        if self.是否找到():
            self.点击()
            if 日志:
                self.日志 = 日志
                print(日志)
            if 延时:
                time.sleep(random.uniform(*延时))
            return True
        return False
    
    def 必须点击(self, 延时=(1, 3), 日志=None) -> bool:
        """
        简化API：固定位置点击（不需要查找）或查找后点击
        
        参数:
            延时: 点击后的随机延时范围，元组 (最小秒数, 最大秒数)
            日志: 可选的日志信息
        
        返回:
            bool: 是否点击成功
        """
        
        if self.固定点击区域:
            self.controller.随机ADB点击(*self.固定点击区域)
            if 日志:
                self.日志 = 日志
                print(日志)
            if 延时:
                time.sleep(random.uniform(*延时))
            return True
        return self.点击如果找到(延时)

    def _opencv字库找图(
        self, large_image_path, font_name, similarity=0.9, region=(0, 0, 0, 0)
    ):
        """
        根据字库名字进行颜色偏色找图（从全局缓存中读取字库数据）

        注意：使用此函数前，需要先调用 加载字库文件() 函数将字库加载到全局缓存中
        支持同名多个字库条目，会遍历所有同名条目，只要有一个符合相似度就返回

        :param large_image_path: 大图路径（字符串）或 PIL Image 对象
        :param font_name: 字库名字（需要在全局缓存中存在）
        :param similarity: 相似度阈值，0-1之间，默认0.9
        :param region: 检测区域 (x, y, width, height)，如果全为0则检测整个大图
        :return: 找到的位置 {"x": x, "y": y, "w": w, "h": h, "similarity": similarity} 或 None
        """

        # 从全局缓存中获取字库数据（支持同名多个条目）
        if font_name not in self.字库集合:
            print(f"未找到字库: {font_name}，请先调用 加载字库文件() 函数加载字库")
            return None

        font_data_list = self.字库集合[font_name]
        if not font_data_list:
            print(f"字库 {font_name} 的条目列表为空")
            return None

        # 读取大图（支持文件路径或 PIL Image 对象）
        if isinstance(large_image_path, Image.Image):
            # 如果传入的是 PIL Image 对象，直接使用
            large_img = large_image_path.convert("RGB")
        else:
            # 如果是文件路径，从文件读取
            large_img = Image.open(large_image_path).convert("RGB")
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
            if x < 0:
                x = 0
            if y < 0:
                y = 0
            if width <= 0:
                width = large_w - x
            if height <= 0:
                height = large_h - y

            crop_x = max(0, x)
            crop_y = max(0, y)
            crop_width = min(width, large_w - crop_x)
            crop_height = min(height, large_h - crop_y)

            if crop_width <= 0 or crop_height <= 0:
                return None

            search_area = large_array[
                crop_y : crop_y + crop_height, crop_x : crop_x + crop_width
            ]
            offset_x, offset_y = crop_x, crop_y

        # 遍历所有同名字库条目
        for idx, font_data in enumerate(font_data_list):
            template_mask = font_data["template_mask"]
            white_points = font_data["total_count"]
            small_w = font_data["width"]
            small_h = font_data["height"]
            target_offset_x = font_data["target_offset_x"]
            target_offset_y = font_data["target_offset_y"]
            target_offset_w = font_data["target_offset_w"]
            target_offset_h = font_data["target_offset_h"]

            # 检查小图是否大于检测区域
            if small_h > search_area.shape[0] or small_w > search_area.shape[1]:
                continue

            # 解析偏色信息（多个偏色用|连接）
            color_tolerances_parsed = font_data["color_tolerances_parsed"]
            # color_tolerances = deviation_str.split("|")

            # 初始化二值化结果
            search_binary_combined = np.zeros(
                (search_area.shape[0], search_area.shape[1]), dtype=np.uint8
            )

            # 对每个颜色容差进行二值化处理并合并
            for color_tol in color_tolerances_parsed:
                base_color = color_tol["base_color"]
                tolerance = color_tol["tolerance"]

                # 二值化处理
                lower = (base_color - tolerance).clip(0, 255).astype(np.uint8)
                upper = (base_color + tolerance).clip(0, 255).astype(np.uint8)
                search_binary = cv2.inRange(search_area, lower, upper)

                # 合并多个颜色容差的二值化结果（使用 OR 操作）
                search_binary_combined = np.bitwise_or(
                    search_binary_combined, search_binary
                )

            # 将大图二值结果也转换为 0/1 掩码
            search_mask = (search_binary_combined == 255).astype(np.uint8)

            # 使用 TM_CCORR 对两个 0/1 掩码做匹配
            result = cv2.matchTemplate(search_mask, template_mask, cv2.TM_CCORR)

            h, w = result.shape
            # 使用积分图快速计算大图中每个区域的点数
            search_integral = cv2.integral(search_mask)

            H, W = search_mask.shape[:2]
            h, w = template_mask.shape[:2]

            # 使用向量化计算每个区域的点数
            # 计算积分图的四个角
            result_h, result_w = result.shape

            # 预计算积分图的四个角区域
            A = search_integral[0:result_h, 0:result_w]
            B = search_integral[0:result_h, w : w + result_w]
            C = search_integral[h : h + result_h, 0:result_w]
            D = search_integral[h : h + result_h, w : w + result_w]

            search_points_matrix = D - B - C + A
            # 遍历每个位置计算F1分数
            precision = result / (search_points_matrix + 1e-5)
            recall = result / (white_points + 1e-5)
            scores = 2 * precision * recall / (precision + recall + 1e-5)
            # 找到重合白点最多的位置
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(scores)

            print(
                f"字库找图 - 字库名: {font_name}, 条目索引: {idx}/{len(font_data_list)-1}, 相似度: {max_val:.4f}, 位置: {max_loc}"
            )

            # 如果符合相似度要求，立即返回
            if max_val >= similarity:
                return {
                    "origin_x": max_loc[0] + offset_x,
                    "origin_y": max_loc[1] + offset_y,
                    "origin_w": small_w,
                    "origin_h": small_h,
                    "target_x": max_loc[0] + offset_x + target_offset_x,
                    "target_y": max_loc[1] + offset_y + target_offset_y,
                    "target_w": target_offset_w,
                    "target_h": target_offset_h,
                    "similarity": float(max_val),
                }

        # 所有条目都遍历完，没有找到符合相似度的，返回 None
        # print(f"字库找图 - 字库名: {font_name}, 遍历了 {len(font_data_list)} 个条目，均未达到相似度要求 {similarity}")
        return None

    def _yolo(self, image_path, model_path, conf_threshold=0.6):
        """
        使用YOLOv8模型检测图片中的目标

        参数:
            image_path: 图片路径（字符串）或 PIL Image 对象或 numpy 数组
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

        if self.模型 is None:
            print("未加载模型，请先调用 加载模型文件() 函数加载模型")
            return None
        # 进行推理（YOLO 支持文件路径、PIL Image 和 numpy 数组）
        results = self.模型(image_path, conf=conf_threshold, verbose=False)
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
                class_name = self.模型.names[class_id]

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


class 界面配置:
    """界面配置类，在初始化时直接将配置转换为对象属性访问"""
    
    def __init__(self, 界面名称, config_dict, controller, 截图上下文, 字库集合, 模型):
        self._名称 = 界面名称
        self._config = config_dict
        
        # 动态创建按钮属性
        if '按钮' in config_dict:
            self.按钮 = type('按钮集合', (), {})()
            for 名称, 配置 in config_dict['按钮'].items():
                if isinstance(配置, list):
                    # 固定点击区域
                    field = Field({"固定点击区域": 配置}, controller, 截图上下文)
                else:
                    # 需要查找的按钮
                    field_config = {"查找字符串": f'{界面名称}_按钮_{名称}'}
                    field_config.update(配置)
                    field = Field(field_config, controller, 截图上下文).设置字库(字库集合).设置模型(模型)
                setattr(self.按钮, 名称, field)
        else:
            self.按钮 = type('按钮集合', (), {})()
        
        # 动态创建状态属性
        if '状态' in config_dict:
            self.状态 = type('状态集合', (), {})()
            for 名称, 配置 in config_dict['状态'].items():
                field_config = {"查找字符串": f'{界面名称}_状态_{名称}'}
                field_config.update(配置)
                field = Field(field_config, controller, 截图上下文).设置字库(字库集合).设置模型(模型)
                setattr(self.状态, 名称, field)
        else:
            self.状态 = type('状态集合', (), {})()
    
    def get(self, name, default=None):
        """兼容字典访问"""
        if name == "按钮":
            return self.按钮
        if name == "状态":
            return self.状态
        return self._config.get(name, default)


class TaskLineMachine:
    """任务状态机类"""

    def __init__(self, device_id):
        self.font_library_cache = {}
        self.加载字库文件(
            os.path.join(os.path.dirname(__file__), "resource", "font_library.txt")
        )
        self._model = None
        # self.加载模型文件(os.path.join(os.path.dirname(__file__), "resource", "model.pt"))

        self.controller = DeviceController(device_id)
        self._截图上下文 = ScreenshotContext(self.controller)  # 截图上下文管理器
        self.界面识别缓存 = {}
        self.界面集合 = self.加载界面配置(界面集合)
        self._states = {}
        self._current_interface = None
        self._previous_interface = None
        self._is_running = False
        self._context = {}  # 上下文信息
        self._unknown_start_time = None  # 未知界面开始时间
        self._unknown_timeout = 60  # 未知界面超时时间（秒）

    def state(self, 界面名称):
        """装饰器：直接注册界面处理函数"""

        def decorator(func):
            self._states[界面名称] = func

        return decorator

    def _copy_unknown_screenshot(self, image_data):
        """
        保存未知界面截图到unknown文件夹

        参数:
            image_data: 文件路径（字符串）或 PIL Image 对象
        """
        try:
            # 创建unknown文件夹
            unknown_dir = os.path.join(os.path.dirname(__file__), "resource", "unknown")
            os.makedirs(unknown_dir, exist_ok=True)

            # 生成带时间戳的文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"unknown_{timestamp}.png"
            dest_path = os.path.join(unknown_dir, filename)

            # 如果是 PIL Image 对象，直接保存
            if isinstance(image_data, Image.Image):
                image_data.save(dest_path)
            else:
                # 如果是文件路径，复制文件
                import shutil

                shutil.copy(image_data, dest_path)

            print(f"未知界面截图已保存: {dest_path}")
        except Exception as e:
            print(f"保存未知界面截图失败: {e}")

    def _play_alert_music(self):
        """播放提示音乐"""
        import threading

        try:
            music_path = os.path.join(
                os.path.dirname(__file__), "resource", "music.mp3"
            )
            if os.path.exists(music_path):
                # 在后台线程播放，避免阻塞主程序
                def play():
                    try:
                        from playsound import playsound

                        playsound(music_path)
                    except ImportError:
                        # 如果没有playsound，尝试使用系统命令
                        import platform

                        if platform.system() == "Windows":
                            os.system(f'start "" "{music_path}"')
                        elif platform.system() == "Darwin":  # macOS
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
            # 每轮开始时重置截图上下文
            self._截图上下文.新轮次()
            截图 = self._截图上下文.get_截图()
            是否找到 = False
            # 优先检测当前/上一个界面 (利用局部性原理)
            优先检测列表 = []
            if self._current_interface:
                优先检测列表.append(self._current_interface)
            if self._previous_interface and self._previous_interface != self._current_interface:
                优先检测列表.append(self._previous_interface)
            for 界面名称 in 优先检测列表 + [k for k in self._states.keys() if k not in 优先检测列表]:

                if self.界面识别缓存[界面名称].查找().是否找到():
                    是否找到 = True
                    print(f"目前位于: {界面名称}")
                    self.update_context(上一状态=self._current_interface)
                    self._current_interface = 界面名称
                    # 找到已知界面，重置未知界面计时器
                    self._unknown_start_time = None
                    # 直接使用已转换的界面配置对象
                    result = self._states[界面名称](self._context, self.界面集合[界面名称])
                    if isinstance(result, dict):
                        self._context.update(result)
                    elif result is False:
                        # 处理函数返回False，表示操作失败或需要重试
                        print(f"界面 {self._current_interface} 处理失败")
                    break
                

            if not 是否找到:
                # 如果长时间处于未知界面,先尽可能关闭当前界面, 如果还是一直处于未知界面,然后就报警
                print(f"目前位于: 未知界面")
                # 尝试关闭未注册界面
                for 界面名称, 界面配置对象 in self.界面集合.items():
                    if 界面名称 in self._states:
                        continue
                    # 检查是否有关闭按钮
                    if hasattr(界面配置对象.按钮, '关闭'):
                        if self.界面识别缓存[界面名称].查找().是否找到():
                            界面配置对象.按钮.关闭.点击()
                            print(f"目前位于未注册界面: {界面名称}")
                            break

                # 未知界面计时逻辑
                if self._unknown_start_time is None:
                    self._unknown_start_time = time.time()
                else:
                    elapsed = time.time() - self._unknown_start_time
                    if elapsed >= self._unknown_timeout:
                        print(f"未知界面已持续 {elapsed:.1f} 秒，保存截图")
                        # 保存截图（支持文件路径和 PIL Image 对象）
                        self._copy_unknown_screenshot(截图)
                        # 播放提示音乐
                        self._play_alert_music()
                        # 重置计时器，避免重复保存
                        self._unknown_start_time = time.time()

            time.sleep(0.2)

    def stop(self):
        """停止状态机"""
        self._is_running = False

    def update_context(self, **kwargs):
        """更新上下文"""
        self._context.update(kwargs)

    def Field(self, config):
        return (
            Field(config, self.controller)
            .设置字库(self.font_library_cache)
            .设置模型(self._model)
        )

    def 加载字库文件(self, font_library_path):
        """
        读取字库文件并缓存到全局变量中

        此函数应在程序启动时调用，将字库数据加载到内存中，避免每次找图时重复读取文件

        :param font_library_path: 字库文件路径（txt文件，格式：点阵&长,宽,点阵总数量&偏色&命名）
        :return: 成功加载的字库数量，失败返回0
        """

        # 读取字库文件
        try:
            with open(font_library_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"读取字库文件失败: {e}")
            return 0
        loaded_count = 0

        # 解析每一行字库数据
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 解析字库行：点阵&长,宽,点阵总数量&偏色&命名&偏移点击区域
            parts = line.split("&")
            if len(parts) != 5:
                continue

            matrix_hex, size_info, deviation_str, name, target_offset = [p.strip() for p in parts]

    
            # 预解析偏色信息
            color_tolerances_parsed = []
            for color_tol in deviation_str.split("|"):
                color_tol = color_tol.strip()
                if not color_tol:
                    continue
                base_color_hex, tolerance_hex = color_tol.split("-")
                color_tolerances_parsed.append({
                    "base_color": np.array([
                        int(base_color_hex[0:2], 16),
                        int(base_color_hex[2:4], 16),
                        int(base_color_hex[4:6], 16),
                    ], dtype=np.int16),
                    "tolerance": np.array([
                        int(tolerance_hex[0:2], 16),
                        int(tolerance_hex[2:4], 16),
                        int(tolerance_hex[4:6], 16),
                    ], dtype=np.int16),
                })


            # 解析尺寸信息：长,宽,点阵总数量
            size_parts = size_info.split(",")
            if len(size_parts) != 3:
                continue

            try:
                width = int(size_parts[0])
                height = int(size_parts[1])
                total_count = int(size_parts[2])
            except ValueError:
                continue

            # 目标偏移信息
            target_offset_parts = target_offset.split(",")
            if len(target_offset_parts) != 4:
                continue
                
            try:
                target_offset_x = int(target_offset_parts[0])
                target_offset_y = int(target_offset_parts[1])
                target_offset_w = int(target_offset_parts[2])
                target_offset_h = int(target_offset_parts[3])
            except ValueError:
                continue

            # 将16进制点阵转换为二值化图像
            # 点阵格式：每4位二进制转换为1个16进制字符
            binary_data = []
            for hex_char in matrix_hex:
                # 将16进制字符转换为4位二进制
                bits = format(int(hex_char, 16), "04b")
                binary_data.extend([int(bit) for bit in bits])

            # 只取前 width * height 位
            total_pixels = width * height
            binary_data = binary_data[:total_pixels]

            # 将二进制数据转换为numpy数组（重塑为图像形状）
            # 白色(1)对应255，黑色(0)对应0
            binary_array = np.array(binary_data, dtype=np.uint8).reshape(
                (height, width)
            )
            binary_array = np.where(binary_array == 1, 255, 0).astype(np.uint8)

            # 转换为 template_mask (0/1掩码)
            template_mask = (binary_array == 255).astype(np.uint8)

            # 存储到全局缓存（支持同名多个条目，使用列表存储）
            if name not in self.font_library_cache:
                self.font_library_cache[name] = []

            self.font_library_cache[name].append(
                {
                    "template_mask": template_mask,
                    "width": width,
                    "height": height,
                    "total_count": total_count,
                    "deviation": deviation_str,
                    "color_tolerances_parsed": color_tolerances_parsed,
                    "matrix_hex": matrix_hex,
                    "target_offset_x": target_offset_x,
                    "target_offset_y": target_offset_y,
                    "target_offset_w": target_offset_w,
                    "target_offset_h": target_offset_h,
                }
            )

            loaded_count += 1

        print(f"成功加载 {loaded_count} 个字库到缓存")
        return loaded_count

    def 加载模型文件(self, model_path):
        self._model = YOLO(model_path)
        return self._model

    def 加载界面配置(self, 界面集合):
        """加载界面配置，直接转换为对象属性访问"""
        config = {}
        for 界面名称, 原始配置 in 界面集合.items():
            # 创建界面识别用的 Field
            识别配置 = {"查找字符串": 界面名称}
            识别配置.update(原始配置)
            self.界面识别缓存[界面名称] = (
                Field(识别配置, self.controller, self._截图上下文)
                .设置字库(self.font_library_cache)
                .设置模型(self._model)
            )
            # 创建界面配置对象（直接转换为属性访问）
            config[界面名称] = 界面配置(
                界面名称, 
                原始配置, 
                self.controller, 
                self._截图上下文, 
                self.font_library_cache, 
                self._model
            )
        return config
 