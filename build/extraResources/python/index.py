import argparse
import time
import os

parser = argparse.ArgumentParser(description="Python Server")
parser.add_argument("--id", type=str, default='', help="The id number.")
args = parser.parse_args()



def 写入日志(info):
    print(f'{info}')
    # # 使用主运行模块所在目录，而不是当前文件所在目录
    # import sys
    # main_module = sys.modules['__main__']
    # main_dir = os.path.dirname(os.path.abspath(main_module.__file__))
    # log_dir = os.path.join(main_dir, 'logs')
    # os.makedirs(log_dir, exist_ok=True)
    # log_path = os.path.join(log_dir, f'{deviceIds}.log')
    #
    # # 读取已有日志内容
    # logs = []
    # if os.path.exists(log_path):
    #     with open(log_path, 'r', encoding='utf-8') as f:
    #         logs = f.readlines()
    #
    # # 保证最多一百行
    # logs = [line.rstrip('\n') for line in logs]
    # logs.append(info)
    # if len(logs) > 100:
    #     logs = logs[-100:]
    # with open(log_path, 'w', encoding='utf-8') as f:
    #     for line in logs:
    #         f.write(f'{line}\n')






import json
import random
import websockets
import os
import time
import asyncio

import cv2
import numpy as np
from PIL import Image

from ultralytics import YOLO
import math

# deviceIds = "9a8de478"
deviceIds = args.id


def 裁剪图片(url, x, y, w, h):
    try:
        # 检查文件是否存在
        if not os.path.exists(url):
            print(f"错误：文件 {url} 不存在")
            return False

        # 使用PIL打开图片
        img = Image.open(url)

        # 获取图片原始尺寸
        width, height = img.size

        # 检查裁剪参数是否有效
        if x < 0 or y < 0 or w <= 0 or h <= 0:
            print(f"错误：裁剪参数无效 (x={x}, y={y}, w={w}, h={h})")
            return False

        # 检查裁剪区域是否超出图片边界
        if x + w > width:
            w = width - x
            print(f"警告：裁剪宽度超出图片边界，已调整为 {w}")

        if y + h > height:
            h = height - y
            print(f"警告：裁剪高度超出图片边界，已调整为 {h}")

        # 执行裁剪
        crop_box = (x, y, x + w, y + h)
        cropped_img = img.crop(crop_box)

        # 保存图片（覆盖原文件）
        # 获取原图片格式
        img_format = img.format if img.format else "PNG"

        # 保存并覆盖原文件
        cropped_img.save(url, format=img_format)

        print(f"成功裁剪图片：{url}")
        print(f"原始尺寸：{width}x{height}，裁剪后尺寸：{w}x{h}")

        return True

    except Exception as e:
        print(f"裁剪图片时出错：{str(e)}")
        return False



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


def opencv找透明图(large_img_path, small_img_path, tolerance=0, similarity=0.9, region=(0, 0, 0, 0)):
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
            # print(f"模板匹配度不足: {best_val:.4f} < {similarity}")
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
            
            # 确保不超出大图边界
            if end_x > large_w or end_y > large_h:
                return None
            
            # 提取匹配区域
            match_area = large_img[start_y:end_y, start_x:end_x]
            
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
    写入日志(f"点击坐标: {x}, {y}")
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
        self.分类名 = config.get("分类名")
        self.相似度 = config.get("相似度", 0.8)
        self.模型路径 = config.get("模型路径")
        self.关闭区域 = config.get("关闭区域")
        self.查找区域 = config.get("查找区域", {"x": 0, "y": 0, "w": 0, "h": 0})
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0

    def 查找(self):
        url =  self.大图路径 if self.大图路径 else 截图()
        if url:
            if self.方式 == "opencv找图":
                result = opencv找图(url, self.图片路径, self.相似度,(self.查找区域["x"], self.查找区域["y"],self.查找区域["w"],self.查找区域["h"]))
                if result:
                    写入日志(f"找到{self.标识}: '{result}'")
                    self.x = result["x"]
                    self.y = result["y"]
                    self.w = result["w"]
                    self.h = result["h"]

            if self.方式 == "opencv找透明图":
                result = opencv找透明图(url, self.图片路径, 30, self.相似度, (self.查找区域["x"], self.查找区域["y"],self.查找区域["w"],self.查找区域["h"]))
                if result:
                    写入日志(f"找到{self.标识}: '{result}'")
                    self.x = result["x"]
                    self.y = result["y"]
                    self.w = result["w"]
                    self.h = result["h"]

            if self.方式 == "yolo":
                result = yolo(url, self.模型路径, self.相似度)
                if len(result):
                    for r in result:
                        if r["class_name"] == self.分类名:
                            写入日志(f"找到{self.标识}: '{result}'")
                            self.x = self.查找区域["x"] + math.ceil(r["x"])
                            self.y = self.查找区域["y"] + math.ceil(r["y"])
                            self.w = math.floor(r["w"])
                            self.h = math.floor(r["h"])
                            break
        
        return self

    def 点击(self, x=None, y=None, w=None, h=None):
        if self.是否找到():
            if x and y and w and h:
                随机ADB点击(x, y, w, h)
            elif x and y:
                ADB点击(x, y)
            elif self.x and self.y:
                随机ADB点击(self.x, self.y, self.w, self.h)
        return self

    def 偏移点击(self, x=None, y=None, w=None, h=None):
        if self.是否找到():
            if not w and not h:
                ADB点击(self.x + x, self.y + y)
            if w and h:
                随机ADB点击(self.x + x, self.y + y, w, h)
        return self

    def 关闭(self):
        if self.是否找到() and self.关闭区域:
            self.点击(self.关闭区域["x"],self.关闭区域["y"],self.关闭区域["w"],self.关闭区域["h"])

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
                    for state in self._states.values():
                        handler = state['handler']
                        config = state['Field']
                        if Field(config).设置大图路径(url).查找().是否找到():
                            self.update_context(上一状态=self._current_interface)
                            self._current_interface = config['标识']
                            result = handler(self._context)
                            if isinstance(result, dict):
                                self._context.update(result)
                            elif result is False:
                                # 处理函数返回False，表示操作失败或需要重试
                                print(f"界面 {self._current_interface} 处理失败")
                            break
                    
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
import time


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



















if __name__ == "__main__":
    start = time.time()
    # 循环在运行 5 秒后自动退出
    while time.time() - start < 5:
        time.sleep(1)
        写入日志(args.id, f'{time.strftime("%Y-%m-%d %H:%M:%S")} main')






















