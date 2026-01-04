import cv2
import numpy as np
from typing import Union, Optional, Tuple
from tools import DeviceController


def find_image_with_ignore_corner_color(
    large_image: Union[str, np.ndarray],
    small_image: Union[str, np.ndarray],
    similarity: float = 0.9,
    region: Tuple[int, int, int, int] = (0, 0, 0, 0)
) -> Optional[dict]:
    """
    在大图中查找小图，如果小图四个角的颜色相同，则匹配时忽略该颜色
    
    参数:
        large_image: 大图路径或numpy数组 (BGR格式)
        small_image: 小图路径或numpy数组 (BGR格式)
        similarity: 相似度阈值，0-1之间，默认0.9
        region: 检测区域 (x, y, width, height)，如果全为0则检测整个大图
    
    返回:
        如果找到: {"x": x, "y": y, "w": w, "h": h, "similarity": similarity}
        如果没找到: None
    """
    # 读取大图
    if isinstance(large_image, str):
        large_img = cv2.imread(large_image)
        if large_img is None:
            return None
    else:
        large_img = large_image.copy()
    
    # 读取小图
    if isinstance(small_image, str):
        small_img = cv2.imread(small_image)
        if small_img is None:
            return None
    else:
        small_img = small_image.copy()
    
    # 获取图像尺寸
    large_h, large_w = large_img.shape[:2]
    small_h, small_w = small_img.shape[:2]
    
    # 处理检测区域
    x, y, width, height = region
    
    # 判断是否指定了检测区域
    if x == 0 and y == 0 and width == 0 and height == 0:
        # 检测整个大图
        search_area = large_img
        offset_x, offset_y = 0, 0
        region_w, region_h = large_w, large_h
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
        
        # 计算实际裁剪区域
        crop_x = max(0, x)
        crop_y = max(0, y)
        crop_width = min(width, large_w - crop_x)
        crop_height = min(height, large_h - crop_y)
        
        # 确保裁剪区域有效
        if crop_width <= 0 or crop_height <= 0:
            return None
        
        # 裁剪检测区域
        search_area = large_img[crop_y:crop_y+crop_height, crop_x:crop_x+crop_width]
        offset_x, offset_y = crop_x, crop_y
        region_w, region_h = crop_width, crop_height
    
    # 检查小图是否大于检测区域
    if small_h > region_h or small_w > region_w:
        return None
    
    # 检查小图四个角的颜色是否相同
    # 四个角的坐标：(左上, 右上, 左下, 右下)
    corners = [
        small_img[0, 0],           # 左上角
        small_img[0, small_w-1],   # 右上角
        small_img[small_h-1, 0],    # 左下角
        small_img[small_h-1, small_w-1]  # 右下角
    ]
    
    # 判断四个角的颜色是否相同（允许小的容差）
    corner_color = None
    tolerance = 5  # 颜色容差，允许RGB各通道有5的差异
    
    # 比较四个角的颜色
    corners_match = True
    base_corner = corners[0]
    
    for corner in corners[1:]:
        # 计算颜色差异
        diff = np.abs(corner.astype(np.int16) - base_corner.astype(np.int16))
        if np.any(diff > tolerance):
            corners_match = False
            break
    
    # 如果四个角颜色相同，创建掩码忽略该颜色
    mask = None
    if corners_match:
        corner_color = base_corner
        # 创建掩码：小图中与角颜色相同的像素设为0（忽略），其他像素设为255（参与匹配）
        # 计算每个像素与角颜色的差异
        small_int16 = small_img.astype(np.int16)
        corner_int16 = corner_color.astype(np.int16)
        diff = np.abs(small_int16 - corner_int16)
        # 如果RGB三个通道的差异都在容差范围内，则认为该像素是角颜色
        color_mask = np.all(diff <= tolerance, axis=2)
        # 创建掩码：角颜色区域为0（忽略），其他区域为255（参与匹配）
        mask = np.where(color_mask, 0, 255).astype(np.uint8)
    
    # 使用模板匹配
    if mask is not None:
        # 使用带掩码的模板匹配
        result = cv2.matchTemplate(search_area, small_img, cv2.TM_CCOEFF_NORMED, mask=mask)
    else:
        # 不使用掩码的普通模板匹配
        result = cv2.matchTemplate(search_area, small_img, cv2.TM_CCOEFF_NORMED)
    
    # 找到最匹配的位置
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    print(max_val, "===")
    # 检查是否达到相似度阈值
    if max_val >= similarity:
        # 返回相对于整个大图的坐标（加上偏移量）
        return {
            "x": max_loc[0] + offset_x,
            "y": max_loc[1] + offset_y,
            "w": small_w,
            "h": small_h,
            "similarity": float(max_val)
        }
    
    return None


if __name__ == "__main__":
    aaa = DeviceController('9a8de478')
    url = aaa.截图()
    large_image = cv2.imread(url)
    small_image = cv2.imread("111.png")
    result = find_image_with_ignore_corner_color(large_image, small_image, 0.9)
    print(result)