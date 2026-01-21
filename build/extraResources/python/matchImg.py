import cv2
import numpy as np
from PIL import Image

def opencv找图(large_image_path, small_image_path, region=(0, 0, 0, 0)):
    """
    在大图中查找小图
    :param large_image_path: 大图路径
    :param small_image_path: 小图路径
    :param region: 检测区域 (x, y, width, height)，如果全为0则检测整个大图
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
    
    # 返回相对于整个大图的坐标（加上偏移量）
    return {"x": max_loc[0] + offset_x, "y": max_loc[1] + offset_y, 'w': w, 'h': h, 'similarity': max_val}
    

def opencv颜色偏色找图(large_image_path, small_image_path, color_tolerance, region=(0, 0, 0, 0)):
    """
    使用颜色偏色二值化后进行模板匹配找图

    :param large_image_path: 大图路径
    :param small_image_path: 小图路径
    :param color_tolerance: 颜色偏色字符串或字符串数组，格式如 "D7CCC6-0E0E09" 或 ["D7CCC6-0E0E09", "FFFFFF-101010"]
                        其中D7CCC6为基准色(RGB)，0E0E09为RGB各通道的允许偏差
                        支持多个颜色容差，会合并所有匹配的颜色区域
    :param region: 检测区域 (x, y, width, height)，如果全为0则检测整个大图
    """
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

    # 使用 TM_CCORR 对两个 0/1 掩码做匹配
    # 对于 0/1 掩码，TM_CCORR 的结果等于滑动窗口内 search_mask * template_mask 的和，
    result = cv2.matchTemplate(search_mask, template_mask, cv2.TM_CCORR)

    
    # 找到重合白点最多的位置
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    white_points = int(np.sum(template_mask))
    参数相似度 = 0.80
    # 相似度过关了,就不关注重合白点个数了, 后续关注区域内白点个数相似度, 找到最合适的点
    if((max_val / white_points) < 参数相似度):
        return None

    # 找到所有超过相似度阈值的位置
    locations = np.where(result >= (white_points * 参数相似度) )

    matches = []
    for y, x in zip(locations[0], locations[1]):
        matches.append({
            'x': x,
            'y': y,
            'w': small_w,
            'h': small_h,
            'score': result[y, x], # 可以得到这个区域重合的白点个数
            'count_similarity': 1- (abs(white_points - np.sum(search_mask[y:y+small_h, x:x+small_w]))/(small_w * small_h)) # 可以得到这个区域白点个数相似度
        })
    # 找到白点个数相似度最高的点
    max_item = max(matches, key=lambda x: x['count_similarity'])

    overlap_white = max_item['score']
    
    custom_similarity = overlap_white / white_points

    print(f"自定义白点匹配率 - 重合白点: {overlap_white}, 小图白点: {white_points}, 个数相似度: {max_item['count_similarity']:.4f}, 重合相似度: {custom_similarity:.4f}, 位置: {max_loc}, 最终相似度: {custom_similarity * 0.8 + max_item['count_similarity'] * 0.2:.4f}")

    # 最终确定的点的相似度,位置计算
    return {
        "x": max_loc[0] + offset_x,
        "y": max_loc[1] + offset_y,
        "w": small_w,
        "h": small_h,
        "similarity": custom_similarity * 0.8 + max_item['count_similarity'] * 0.2
    }

def 找图(large_image_path, small_image_path, region=(0, 0, 0, 0), color_tolerance=None):
    """
    找图函数，根据是否传入颜色偏色参数自动选择找图方式
    
    参数:
        large_image_path: 大图路径
        small_image_path: 小图路径
        region: 检测区域 (x, y, width, height)，如果全为0则检测整个大图
        color_tolerance: 颜色偏色参数，格式如 "D7CCC6-0E0E09" 或 ["D7CCC6-0E0E09", "FFFFFF-101010"]
                        如果传入此参数，则使用颜色偏色找图；如果不传入或为None，则使用普通找图
    
    返回:
        找到的位置 {"x": x, "y": y, "w": w, "h": h, "similarity": similarity} 或 None
    """
    if color_tolerance is not None:
        # 如果传入了颜色偏色参数，使用颜色偏色找图
        return opencv颜色偏色找图(large_image_path, small_image_path, color_tolerance, region)
    else:
        # 如果没有传入颜色偏色参数，使用普通找图
        return opencv找图(large_image_path, small_image_path, region)
    


if __name__ == "__main__":
    large_image_path = "888.png"
    small_image_path = "主界面.png"
    color_tolerance = ['72B23F-1A1D1D', 'A33631-312B2D']
    # color_tolerance = ["C9BDB8-262325"]
    region = (0, 0, 0, 0)
    
    result = opencv颜色偏色找图(large_image_path, small_image_path, color_tolerance, region)
    print(f"结果: {result}")