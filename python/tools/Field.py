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

deviceIds = "9a8de478"


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


def opencv找图(large_image_path, small_image_path, tolerance=0, similarity=0.9):
    """
    在大图中查找小图
    :param large_image_path: 大图路径
    :param small_image_path: 小图路径
    :param tolerance: 容差，允许的颜色差异范围
    :param similarity: 相似度阈值，0-1之间
    :return: 找到的位置 (x, y) 或 None
    """
    try:
        # 1. 检查文件是否存在
        if not os.path.exists(large_image_path) or not os.path.exists(small_image_path):
            print("Image files not found.")
            return None

        # 2. 加载图片
        # 使用PIL加载，保持RGBA格式
        large_pil = Image.open(large_image_path).convert("RGBA")
        small_pil = Image.open(small_image_path).convert("RGBA")

        # 3. 转换为OpenCV格式 (RGBA)
        large_cv = cv2.cvtColor(np.array(large_pil), cv2.COLOR_RGBA2BGRA)
        small_cv = cv2.cvtColor(np.array(small_pil), cv2.COLOR_RGBA2BGRA)

        # 4. 提取小图的Alpha通道作为掩码
        # 分割通道
        b, g, r, alpha = cv2.split(small_cv)
        # 创建二值掩码：Alpha > 0 的部分为 255，否则为 0
        _, mask = cv2.threshold(alpha, 0, 255, cv2.THRESH_BINARY)

        # 5. 转换为BGR用于匹配
        large_bgr = cv2.cvtColor(large_cv, cv2.COLOR_BGRA2BGR)
        small_bgr = cv2.cvtColor(small_cv, cv2.COLOR_BGRA2BGR)

        # 6. 模板匹配
        # 使用TM_CCORR_NORMED配合掩码
        result = cv2.matchTemplate(large_bgr, small_bgr, cv2.TM_CCORR_NORMED, mask=mask)

        # 7. 获取最佳匹配位置
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # 释放内存（Python有自动垃圾回收，但显式删除大对象可以立即释放内存）
        del result

        # 8. 二次校验：根据容差逐像素比对
        start_x, start_y = max_loc

        # 获取图像数据
        large_data = np.array(large_pil)
        small_data = np.array(small_pil)

        total_pixels = 0
        matched_pixels = 0

        small_h, small_w = small_data.shape[:2]
        large_h, large_w = large_data.shape[:2]

        # 遍历小图的每一个像素
        for y in range(small_h):
            for x in range(small_w):
                # 获取小图当前像素的RGBA值
                s_r, s_g, s_b, s_a = small_data[y, x]

                # 如果小图该像素是透明的，忽略比对
                if s_a == 0:
                    continue

                total_pixels += 1

                # 计算大图中的对应位置
                lx = start_x + x
                ly = start_y + y

                # 检查边界
                if lx >= large_w or ly >= large_h:
                    continue

                # 获取大图对应位置像素
                l_r, l_g, l_b, l_a = large_data[ly, lx]

                # 计算差异
                r_diff = abs(int(s_r) - int(l_r))
                g_diff = abs(int(s_g) - int(l_g))
                b_diff = abs(int(s_b) - int(l_b))

                # 如果所有通道差异都在容差范围内，则认为该像素匹配
                if r_diff <= tolerance and g_diff <= tolerance and b_diff <= tolerance:
                    matched_pixels += 1

        # 计算匹配率
        match_rate = matched_pixels / total_pixels if total_pixels > 0 else 0

        # 释放内存
        del large_data, small_data, large_cv, small_cv, mask

        # 9. 判断是否达到相似度要求
        if match_rate >= similarity:
            return {"x": start_x, "y": start_y}
        else:
            # print(
            #     f"Found candidate at {start_x},{start_y} but similarity {match_rate:.4f} < {similarity}"
            # )
            return None

    except Exception as e:
        print(f"find_image error: {e}")
        return None


async def send_to_gc(payload):
    try:
        print(f"Sending to GC: {payload}")
        async with websockets.connect("ws://127.0.0.1:33332") as qc_ws:
            await qc_ws.send(json.dumps(payload))
            response = await qc_ws.recv()
            # print(f"GC Response: {response}")
            return json.loads(response)
    except Exception as e:
        # print(f"GC Error: {e}")
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
    asyncio.run(send_to_gc(payload))
    # 不论返回值，返回预期的图片路径
    safe_device_id = deviceIds.replace(".", "_").replace(":", "_")
    file_path = os.path.join(save_path, f"{safe_device_id}.png")
    return file_path


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


def 获取图片宽高(path):
    try:
        if not os.path.exists(path):
            print(f"错误：文件 {path} 不存在")
            return None

        img = Image.open(path)
        width, height = img.size
        return {"w": width, "h": height}
    except Exception as e:
        print(f"获取图片宽高时出错：{str(e)}")
        return None


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
    def __init__(self, config: dict):
        self.标识 = config.get("标识")
        self.方式 = config.get("方式")
        self.图片路径 = config.get("图片路径")
        self.分类名 = config.get("分类名")
        self.相似度 = config.get("相似度", 0.9)
        self.模型路径 = config.get("模型路径")
        self.查找区域 = config.get("查找区域", {"x": 0, "y": 0, "w": 0, "h": 0})
        self.x = 0
        self.y = 0
        self.w = 0
        self.h = 0

    def 查找(self):
        url = 截图()
        if (
            self.查找区域["x"]
            and self.查找区域["y"]
            and self.查找区域["w"]
            and self.查找区域["h"]
        ):
            裁剪图片(
                url,
                self.查找区域["x"],
                self.查找区域["y"],
                self.查找区域["w"],
                self.查找区域["h"],
            )

        if self.方式 == "opencv找图":
            result = opencv找图(url, self.图片路径, 30, self.相似度)
            result2 = 获取图片宽高(self.图片路径)
            if result and result2:
                self.x = self.查找区域["x"] + result["x"]
                self.y = self.查找区域["y"] + result["y"]
                self.w = result2["w"]
                self.h = result2["h"]

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
        return self

    def 点击(self, x=None, y=None, w=None, h=None):
        if x and y and w and h:
            随机ADB点击(x, y, w, h)
        elif x and y:
            ADB点击(x, y)
        elif self.x and self.y:
            ADB点击(self.x, self.y, self.w, self.h)
        return self

    def 偏移点击(self, x=None, y=None, w=None, h=None):
        if not w and not h:
            ADB点击(self.x + x, self.y + y)
        if w and h:
            随机ADB点击(self.x + x, self.y + y, w, h)
        return self

    def 随机延时(self, startMs, endMs):
        if self.x and self.y:
            随机延时(startMs, endMs)
        return self

    def 设置查找区域(self, 查找区域):
        self.查找区域 = 查找区域
        return self

    def 是否找到(self):
        return bool(self.x and self.y)


if __name__ == "__main__":
    # aaa = Field({"方式": "yolo", "分类名": "对话框", "相似度": 0.8}).查找()
    # print(aaa.x, aaa.y, aaa.w, aaa.h)
    print('123')
