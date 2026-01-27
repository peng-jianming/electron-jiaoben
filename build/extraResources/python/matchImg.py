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

    # 最终确定的点的相似度,位置计算
    return {
        "x": max_loc[0] + offset_x,
        "y": max_loc[1] + offset_y,
        "w": small_w,
        "h": small_h,
        "similarity": final_similarity
    }



def opencv颜色偏色找图2(large_image_path, small_image_path, color_tolerance, region=None, method='f1'):
    """
    使用颜色偏色二值化后进行模板匹配找图，使用F1分数评估相似度

    :param large_image_path: 大图路径
    :param small_image_path: 小图路径
    :param color_tolerance: 颜色偏色字符串或字符串数组，格式如 "D7CCC6-0E0E09" 或 ["D7CCC6-0E0E09", "FFFFFF-101010"]
                        其中D7CCC6为基准色(RGB)，0E0E09为RGB各通道的允许偏差
                        支持多个颜色容差，会合并所有匹配的颜色区域
    :param similarity: F1分数阈值，0-1之间，默认0.8
    :param region: 检测区域 [x, y, w, h]，如果全为0则检测整个大图
    :param method: 相似度计算方法，支持 'f1'(默认), 'precision', 'recall', 'jaccard', 'dice'
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

    # 将二值结果转换为 0/1 掩码
    template_mask = (small_binary_combined == 255).astype(np.uint8)
    search_mask = (search_binary_combined == 255).astype(np.uint8)
    
    # 计算模板点数（小图白点总数）
    template_points = int(np.sum(template_mask))
    
    # 如果模板点数为0，直接返回None
    if template_points == 0:
        return None
    
    # 使用TM_CCORR获取每个位置的重合点数
    result = cv2.matchTemplate(search_mask, template_mask, cv2.TM_CCORR)

    h, w = result.shape
    # 使用积分图快速计算大图中每个区域的点数
    search_integral = cv2.integral(search_mask)
    
    # 计算每个位置的F1分数
    f1_scores = np.zeros((h, w), dtype=np.float32)
    
    # 遍历每个位置计算F1分数
    for y in range(h):
        for x in range(w):
            # 当前区域的重合点数
            overlap = float(result[y, x])
            
            # 使用积分图计算当前区域的点数
            # 积分图索引需要+1（因为积分图比原图多一行一列）
            sum1 = search_integral[y, x]
            sum2 = search_integral[y, x + small_w]
            sum3 = search_integral[y + small_h, x]
            sum4 = search_integral[y + small_h, x + small_w]
            search_points = float(sum4 - sum2 - sum3 + sum1)
            
            # 计算相似度分数
            if method == 'precision':
                score = overlap / (search_points + 1e-5)
            elif method == 'recall':
                score = overlap / (template_points + 1e-5)
            elif method == 'jaccard':
                union = template_points + search_points - overlap
                score = overlap / (union + 1e-5)
            elif method == 'dice':
                score = 2 * overlap / (template_points + search_points + 1e-5)
            else:  # 'f1' 默认
                precision = overlap / (search_points + 1e-5)
                recall = overlap / (template_points + 1e-5)
                if precision + recall == 0:
                    score = 0
                else:
                    score = 2 * precision * recall / (precision + recall + 1e-5)
            
            f1_scores[y, x] = score
    
    # 找到F1分数最高的位置
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(f1_scores)
    
    # 输出调试信息
    if max_val:
        x, y = max_loc
        # 获取该位置的详细信息
        overlap = float(result[y, x])
        
        # 计算当前区域的点数
        sum1 = search_integral[y, x]
        sum2 = search_integral[y, x + small_w]
        sum3 = search_integral[y + small_h, x]
        sum4 = search_integral[y + small_h, x + small_w]
        search_points = float(sum4 - sum2 - sum3 + sum1)
        
        # 计算精度和召回率
        precision = overlap / (search_points + 1e-5)
        recall = overlap / (template_points + 1e-5)
        
        print(
            f"F1匹配结果 - 方法: {method}, "
            f"F1分数: {max_val:.4f}, "
            f"位置: {max_loc}, "
            f"重合白点: {overlap:.0f}, "
            f"小图白点: {template_points}, "
            f"区域白点: {search_points:.0f}, "
            f"精度: {precision:.4f}, "
            f"召回率: {recall:.4f}"
        )
        
        return {
            "x": max_loc[0] + offset_x,
            "y": max_loc[1] + offset_y,
            "w": small_w,
            "h": small_h,
            "similarity": float(max_val)
        }
    
    print(f"未找到匹配项: {max_val:.4f}")
    return None



def opencv字库找图(large_image_path, font_library_info_array, region=(0, 0, 0, 0), similarity=0.8):
    """
    根据字库信息数组进行颜色偏色找图，遍历数组直到找到符合相似度条件的就返回
    
    :param large_image_path: 大图路径
    :param font_library_info_array: 字库信息数组，每个元素是字库行字符串，格式：点阵&长,宽,点阵总数量&偏色&命名
    :param region: 检测区域 (x, y, width, height)，如果全为0则检测整个大图
    :param similarity: 相似度阈值，0-1之间，默认0.8
    :return: 找到的位置 {"x": x, "y": y, "w": w, "h": h, "similarity": similarity} 或 None
    """
    # 如果传入的是单个字符串，转换为数组
    if isinstance(font_library_info_array, str):
        font_library_info_array = [font_library_info_array]
    
    # 遍历字库信息数组，直到找到符合相似度条件的
    for line in font_library_info_array:
        result = opencv字库找图单个(large_image_path, line, region)
        if result:
            result_similarity = result.get("similarity", 0)
            # 确保相似度是数字类型
            if isinstance(result_similarity, (int, float)):
                if result_similarity >= similarity:
                    print(f"字库找图成功 - 相似度: {result_similarity:.4f}, 阈值: {similarity}, 位置: ({result.get('x')}, {result.get('y')})")
                    return result
                else:
                    print(f"字库找图相似度不足 - 相似度: {result_similarity:.4f}, 阈值: {similarity}")
            else:
                print(f"字库找图相似度类型错误 - 类型: {type(result_similarity)}, 值: {result_similarity}")
    
    # 没有找到符合相似度条件的
    print(f"字库找图未找到符合相似度条件的匹配 - 阈值: {similarity}")
    return None


def opencv字库找图单个(large_image_path, line, region=(0, 0, 0, 0)):
    """
    根据字库行字符串进行颜色偏色找图（单个字库信息）
    
    :param large_image_path: 大图路径
    :param line: 字库行字符串，格式：点阵&长,宽,点阵总数量&偏色&命名
    :param region: 检测区域 (x, y, width, height)，如果全为0则检测整个大图
    :return: 找到的位置 {"x": x, "y": y, "w": w, "h": h, "similarity": similarity} 或 None
    """
    # 解析字库行
    line = line.strip()
    if not line:
        print("字库行为空")
        return None
    
    # 解析字库行：
    # 新格式：点阵&长,宽,点阵总数量&偏色&命名&偏移点击区域
    parts = line.split('&')
    if len(parts) != 5:
        print(f"字库行格式错误，应为5部分，实际为{len(parts)}部分: {line}")
        return None
    
    matrix_hex, size_info, deviation_str, name, click_offset_area = [p.strip() for p in parts]
    
    # 解析尺寸信息：长,宽,点阵总数量
    size_parts = size_info.split(',')
    if len(size_parts) != 3:
        print(f"尺寸信息格式错误: {size_info}")
        return None
    
    try:
        width = int(size_parts[0])
        height = int(size_parts[1])
        total_count = int(size_parts[2])
    except ValueError as e:
        print(f"解析尺寸信息失败: {e}")
        return None

    # 目标偏移信息
    target_offset_parts = click_offset_area.split(",")
    if len(target_offset_parts) != 4:
        print(f"目标偏移信息格式错误: {click_offset_area}")
        return None
        
    try:
        target_offset_x = int(target_offset_parts[0])
        target_offset_y = int(target_offset_parts[1])
        target_offset_w = int(target_offset_parts[2])
        target_offset_h = int(target_offset_parts[3])
    except ValueError:
        print(f"解析目标偏移信息失败: {click_offset_area}")
        return None
    
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
    small_w = width
    small_h = height
    
    # 读取大图
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
    
    # 检查小图是否大于检测区域
    if small_h > search_area.shape[0] or small_w > search_area.shape[1]:
        return None
    
    # 解析偏色信息（多个偏色用|连接）
    color_tolerances = deviation_str.split('|')
    
    # 初始化二值化结果
    search_binary_combined = np.zeros((search_area.shape[0], search_area.shape[1]), dtype=np.uint8)
    
    # 对每个颜色容差进行二值化处理并合并
    for color_tol in color_tolerances:
        color_tol = color_tol.strip()
        if not color_tol:
            continue
            
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


    h, w = result.shape
    # 使用积分图快速计算大图中每个区域的点数
    search_integral = cv2.integral(search_mask)


    # 计算模板点数（小图白点总数）
    template_points = int(np.sum(template_mask))

    # 计算每个位置的F1分数
    f1_scores = np.zeros((h, w), dtype=np.float32)
    
    # 遍历每个位置计算F1分数
    for y in range(h):
        for x in range(w):
            # 当前区域的重合点数
            overlap = float(result[y, x])
            
            # 使用积分图计算当前区域的点数
            # 积分图索引需要+1（因为积分图比原图多一行一列）
            sum1 = search_integral[y, x]
            sum2 = search_integral[y, x + small_w]
            sum3 = search_integral[y + small_h, x]
            sum4 = search_integral[y + small_h, x + small_w]
            search_points = float(sum4 - sum2 - sum3 + sum1)
            
            precision = overlap / (search_points + 1e-5)
            recall = overlap / (template_points + 1e-5)
            if precision + recall == 0:
                score = 0
            else:
                score = 2 * precision * recall / (precision + recall + 1e-5)
            
            f1_scores[y, x] = score

    # 找到重合白点最多的位置
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(f1_scores)
    
    print(f"字库行找图 - 字库名: {name}, 相似度: {max_val:.4f}, 位置: {max_loc}")
    
    return {
        "origin_x": max_loc[0] + offset_x,
        "origin_y": max_loc[1] + offset_y,
        "origin_w": small_w,
        "origin_h": small_h,
        "x": max_loc[0] + offset_x + target_offset_x,
        "y": max_loc[1] + offset_y + target_offset_y,
        "w": target_offset_w if target_offset_w != 0 else small_w,
        "h": target_offset_h if target_offset_h != 0 else small_h,
        "similarity": float(max_val)
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
        return opencv颜色偏色找图2(large_image_path, small_image_path, color_tolerance, region)
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