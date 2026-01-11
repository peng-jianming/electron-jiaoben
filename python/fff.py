import cv2
import numpy as np
from PIL import Image


def color_filter_template_match(large_image_path, small_image_path, color_tolerance, similarity=0.8, region=(0, 0, 0, 0)):
    """
    根据颜色参数过滤图像，只匹配颜色范围内的像素，其他像素不参与匹配
    
    参数:
        large_image_path: 大图路径
        small_image_path: 小图路径
        color_tolerance: 颜色偏色参数，格式如 "C9C0B2-203040"
                        C9C0B2为基准色（RGB的16进制表示）
                        203040表示RGB的色偏分别是20 30 40（16进制表示）
        similarity: 相似度阈值，0-1之间，默认0.8
        region: 检测区域 (x, y, width, height)，如果全为0则检测整个大图
    
    返回:
        如果找到: {"x": x, "y": y, "w": w, "h": h, "similarity": similarity}
        如果没找到: None
    
    注意:
        使用遮罩匹配时，相似度可能比过滤匹配低，因为：
        1. 遮罩匹配只计算遮罩区域内的像素，相似度基于这些像素计算
        2. 如果遮罩区域较小，相似度会相应降低
        3. 这是正常现象，遮罩匹配更严格，只考虑颜色范围内的像素
    """
    try:
        # 1. 读取图像
        large_img = cv2.imread(large_image_path)
        small_img = cv2.imread(small_image_path)
        
        if large_img is None:
            print(f"无法加载大图: {large_image_path}")
            return None
        if small_img is None:
            print(f"无法加载小图: {small_image_path}")
            return None
        
        # 获取大图尺寸
        large_h, large_w = large_img.shape[:2]
        
        # 解析检测区域
        x, y, width, height = region
        
        # 判断是否指定了检测区域
        if x == 0 and y == 0 and width == 0 and height == 0:
            # 检测整个大图
            search_area = large_img
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
            search_area = large_img[crop_y:crop_y+crop_height, crop_x:crop_x+crop_width]
            offset_x, offset_y = crop_x, crop_y
        
        # 2. 解析颜色偏色参数
        # 格式: "C9C0B2-203040"
        parts = color_tolerance.split('-')
        if len(parts) != 2:
            print(f"颜色偏色参数格式错误: {color_tolerance}")
            return None
        
        base_color_hex = parts[0].strip()  # 基准色，如 "C9C0B2"
        tolerance_hex = parts[1].strip()   # 色偏，如 "203040"
        
        if len(base_color_hex) != 6 or len(tolerance_hex) != 6:
            print(f"颜色偏色参数格式错误: {color_tolerance}")
            return None
        
        # 解析基准色 RGB (16进制转10进制)
        base_color = np.array([
            int(base_color_hex[0:2], 16),  # R
            int(base_color_hex[2:4], 16),  # G
            int(base_color_hex[4:6], 16)   # B
        ], dtype=np.int16)
        
        # 解析色偏 RGB (16进制转10进制)
        tolerance = np.array([
            int(tolerance_hex[0:2], 16),  # R偏色
            int(tolerance_hex[2:4], 16),  # G偏色
            int(tolerance_hex[4:6], 16)   # B偏色
        ], dtype=np.int16)
        
        # 3. 计算颜色范围
        # OpenCV使用BGR格式，需要转换
        base_color_bgr = np.array([base_color[2], base_color[1], base_color[0]], dtype=np.int16)
        tolerance_bgr = np.array([tolerance[2], tolerance[1], tolerance[0]], dtype=np.int16)
        
        # 计算上下限
        lower_bound = np.clip(base_color_bgr - tolerance_bgr, 0, 255).astype(np.uint8)
        upper_bound = np.clip(base_color_bgr + tolerance_bgr, 0, 255).astype(np.uint8)
        
        # 4. 创建遮罩
        search_mask = cv2.inRange(search_area, lower_bound, upper_bound)
        small_mask = cv2.inRange(small_img, lower_bound, upper_bound)
        
        # 检查小图遮罩是否有有效像素
        if np.sum(small_mask) == 0:
            print("小图中没有符合颜色条件的像素")
            return None
        
        # 5. 获取小图尺寸
        small_h, small_w = small_img.shape[:2]
        search_h, search_w = search_area.shape[:2]
        
        # 检查小图是否大于检测区域
        if small_h > search_h or small_w > search_w:
            print("小图尺寸大于检测区域")
            return None
        
        result = cv2.matchTemplate(search_area, small_img, cv2.TM_CCOEFF_NORMED, mask=small_mask)
        
        # 找到最匹配的位置
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # 7. 检查是否达到相似度阈值
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
        
    except Exception as e:
        print(f"颜色过滤模板匹配出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


# 使用示例
if __name__ == "__main__":
    # 示例调用
    result = color_filter_template_match(
        large_image_path="9a8de478.png",
        small_image_path="hhh.bmp",
        color_tolerance="C9C0B2-25211F",  # 基准色C9C0B2，色偏20 30 40
        similarity=0.1
    )
    
    if result:
        print(f"找到匹配: x={result['x']}, y={result['y']}, 相似度={result['similarity']:.2f}")
    else:
        print("未找到匹配")

