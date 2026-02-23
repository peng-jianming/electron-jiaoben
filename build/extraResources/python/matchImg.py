import cv2
import json
import numpy as np
from PIL import Image

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

        下限 = (base_color - tolerance).clip(0, 255).astype(np.uint8)
        上限 = (base_color + tolerance).clip(0, 255).astype(np.uint8)
        搜索二值化 = cv2.inRange(search_area, 下限, 上限)
        搜索二值化结果 = np.bitwise_or(search_binary_combined, 搜索二值化)

    # 将大图二值结果也转换为 0/1 掩码
    search_mask = (搜索二值化结果 == 255).astype(np.uint8)
    
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

    # 找到重合白点最多的位置（单结果时用 minMaxLoc）
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(f1_scores)

    def _make_result(px, py, sim):
        return {
            "origin_x": px + offset_x,
            "origin_y": py + offset_y,
            "origin_w": small_w,
            "origin_h": small_h,
            "x": px + offset_x + target_offset_x,
            "y": py + offset_y + target_offset_y,
            "w": target_offset_w if target_offset_w != 0 else small_w,
            "h": target_offset_h if target_offset_h != 0 else small_h,
            "similarity": float(sim),
            "name": name
        }

    print(f"字库行找图 - 字库名: {name}, 相似度: {max_val:.4f}, 位置: {max_loc}")

    return _make_result(max_loc[0], max_loc[1], max_val)


def _解析字库项(item):
    """
    从字库 JSON 项（dict）解析出匹配所需字段。
    :param item: 字库项 dict，键：点阵, 长宽有效数量, 偏色, 名字, 偏移点击区域
    :return: (matrix_hex, width, height, deviation_str, name, target_offset_x, target_offset_y, target_offset_w, target_offset_h) 或 None
    """
    if not isinstance(item, dict):
        return None
    点阵 = (item.get("点阵") or "").strip()
    长宽有效数量 = (item.get("长宽有效数量") or "").strip()
    if not 点阵 or not 长宽有效数量:
        return None
    size_parts = 长宽有效数量.split(',')
    if len(size_parts) != 3:
        return None
    try:
        width = int(size_parts[0])
        height = int(size_parts[1])
    except ValueError:
        return None
    偏色 = (item.get("偏色") or "").strip()
    名字 = (item.get("名字") or "")
    if not isinstance(名字, str):
        名字 = str(名字)
    偏移点击区域 = (item.get("偏移点击区域") or "").strip()
    offset_parts = 偏移点击区域.split(",")
    if len(offset_parts) != 4:
        return None
    try:
        target_offset_x = int(offset_parts[0])
        target_offset_y = int(offset_parts[1])
        target_offset_w = int(offset_parts[2])
        target_offset_h = int(offset_parts[3])
    except ValueError:
        return None
    return (点阵, width, height, 偏色, 名字, target_offset_x, target_offset_y, target_offset_w, target_offset_h)


def _字库找图单个2_在图上(large_array, 字库项, region=(0, 0, 0, 0)):
    """
    opencv字库找图单个2 的核心算法：在给定的图像数组上做单次找图。
    用于识字时在“当前图”（可能已被涂黑）上反复找同一模板直到找不到为止。
    :param large_array: 大图 numpy 数组 (H, W, 3) RGB
    :param 字库项: 字库 JSON 项（dict），键：点阵, 长宽有效数量, 偏色, 名字, 偏移点击区域
    :param region: 检测区域 (x, y, width, height)，全0表示整图
    :return: 一个匹配 {"origin_x", "origin_y", "origin_w", "origin_h", "x", "y", "w", "h", "similarity", "name"} 或 None
    """
    parsed = _解析字库项(字库项)
    if parsed is None:
        return None
    matrix_hex, width, height, deviation_str, name, target_offset_x, target_offset_y, target_offset_w, target_offset_h = parsed
    binary_data = []
    for hex_char in matrix_hex:
        bits = format(int(hex_char, 16), '04b')
        binary_data.extend([int(bit) for bit in bits])
    total_pixels = width * height
    binary_data = binary_data[:total_pixels]
    binary_array = np.array(binary_data, dtype=np.uint8).reshape((height, width))
    binary_array = np.where(binary_array == 1, 255, 0).astype(np.uint8)
    template_mask = (binary_array == 255).astype(np.uint8)
    small_w = width
    small_h = height
    large_h, large_w = large_array.shape[:2]
    x, y, width, height = region
    if x == 0 and y == 0 and width == 0 and height == 0:
        search_area = large_array
        offset_x, offset_y = 0, 0
    else:
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
    if small_h > search_area.shape[0] or small_w > search_area.shape[1]:
        return None
    color_tolerances = deviation_str.split('|')
    search_binary_combined = np.zeros((search_area.shape[0], search_area.shape[1]), dtype=np.uint8)
    搜索二值化结果 = np.zeros((search_area.shape[0], search_area.shape[1]), dtype=np.uint8)
    for color_tol in color_tolerances:
        color_tol = color_tol.strip()
        if not color_tol:
            continue
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
        except Exception:
            continue
        search_int16 = search_area.astype(np.int16)
        search_diff = np.abs(search_int16 - base_color)
        search_mask = np.all(search_diff <= tolerance, axis=2)
        search_binary = np.where(search_mask, 255, 0).astype(np.uint8)
        search_binary_combined = np.bitwise_or(search_binary_combined, search_binary)
        下限 = (base_color - tolerance).clip(0, 255).astype(np.uint8)
        上限 = (base_color + tolerance).clip(0, 255).astype(np.uint8)
        搜索二值化 = cv2.inRange(search_area, 下限, 上限)
        搜索二值化结果 = np.bitwise_or(search_binary_combined, 搜索二值化)
    search_mask = (搜索二值化结果 == 255).astype(np.uint8)
    result = cv2.matchTemplate(search_mask, template_mask, cv2.TM_CCORR)
    h, w = result.shape
    search_integral = cv2.integral(search_mask)
    template_points = int(np.sum(template_mask))
    f1_scores = np.zeros((h, w), dtype=np.float32)
    for yi in range(h):
        for xi in range(w):
            overlap = float(result[yi, xi])
            sum1 = search_integral[yi, xi]
            sum2 = search_integral[yi, xi + small_w]
            sum3 = search_integral[yi + small_h, xi]
            sum4 = search_integral[yi + small_h, xi + small_w]
            search_points = float(sum4 - sum2 - sum3 + sum1)
            precision = overlap / (search_points + 1e-5)
            recall = overlap / (template_points + 1e-5)
            if precision + recall == 0:
                score = 0
            else:
                score = 2 * precision * recall / (precision + recall + 1e-5)
            f1_scores[yi, xi] = score
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(f1_scores)
    def _make_result(px, py, sim):
        return {
            "origin_x": px + offset_x,
            "origin_y": py + offset_y,
            "origin_w": small_w,
            "origin_h": small_h,
            "x": px + offset_x + target_offset_x,
            "y": py + offset_y + target_offset_y,
            "w": target_offset_w if target_offset_w != 0 else small_w,
            "h": target_offset_h if target_offset_h != 0 else small_h,
            "similarity": float(sim),
            "name": name
        }
    print(f"字库行找图 - 字库名: {name}, 相似度: {max_val:.4f}, 位置: {max_loc}")
    return _make_result(max_loc[0], max_loc[1], max_val)


def _加载字库文件(字库路径):
    """
    从字库 JSON 文件路径加载字库，返回字库项数组（每项为 dict）。
    格式：JSON 数组，每项为 {"名字","点阵","长宽有效数量","偏色","偏移点击区域"}。
    """
    with open(字库路径, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, list):
        data = [data]
    return [item for item in data if isinstance(item, dict)]


def opencv字库识字(识别图片, 字库路径, 识别区域, 相似度, 文字间隔=None):
    """
    根据点阵字库在识别图片上做识字，按间隔参数将识别到的单字组合成词并返回。

    :param 识别图片: 要识别的图片路径（大图）
    :param 字库路径: 字库 JSON 文件路径，格式见 字库.json
    :param 识别区域: (x, y, width, height)，全0表示整图
    :param 相似度: 0~1，只有 >= 该相似度的匹配才计入
    :param 文字间隔: 不传或 None 表示无间隔，所有识别到的字直接组合成一段。
                      单数字表示水平=垂直=该值；或 (水平间隔像素, 垂直间隔像素)。
                      相邻两字：水平间隔 <= 水平阈值 且 垂直间隔 <= 垂直阈值 时合并为同一词，否则拆开
    :return: 字符串。无间隔时为全部组合；有间隔时为第一个识别到的组合。未识别到返回 ""
    """
    # 解析文字间隔：不传或 None 表示无间隔，全部直接组合
    if 文字间隔 is None:
        interval_h = interval_v = None
    elif isinstance(文字间隔, (list, tuple)):
        interval_h = max(0, int(文字间隔[0])) if len(文字间隔) >= 1 else 0
        interval_v = max(0, int(文字间隔[1])) if len(文字间隔) >= 2 else interval_h
    else:
        interval_h = interval_v = max(0, int(文字间隔))
    # 读取字库 JSON，得到字库项数组
    try:
        font_library_list = _加载字库文件(字库路径)
    except Exception as e:
        print(f"识字：读取字库失败 {字库路径}, {e}")
        return ""
    if not font_library_list:
        return ""
    # 加载大图一次，后续在同一张图上反复找并涂黑
    try:
        large_img = Image.open(识别图片).convert('RGB')
        large_array = np.array(large_img)
    except Exception as e:
        print(f"识字：加载识别图片失败 {识别图片}, {e}")
        return ""
    if large_array is None or large_array.size == 0:
        return ""
    # 遍历字库，每个点阵用 _字库找图单个2_在图上 单次找图 → 命中则涂黑 → 继续找直到找不到
    all_matches = []
    for 字库项 in font_library_list:
        while True:
            match = _字库找图单个2_在图上(large_array, 字库项, 识别区域)
            if match is None or match.get("similarity", 0) < 相似度:
                break
            all_matches.append(match)
            ox = match["origin_x"]
            oy = match["origin_y"]
            ow = match["origin_w"]
            oh = match["origin_h"]
            large_array[oy : oy + oh, ox : ox + ow, :] = 0  # 涂成 #000000，避免重复命中
            #在这里可视化large_array
            # cv2.imshow("large_array", large_array)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()
    if not all_matches:
        return ""

    # 按“左上优先”排序：先按 x 再按 y
    all_matches.sort(key=lambda m: (m["origin_x"], m["origin_y"]))
    # 无间隔：直接按顺序组合成一段字符串
    if interval_h is None and interval_v is None:
        return "".join(m.get("name", "") for m in all_matches)
    # 按间隔分组：水平间隔、垂直间隔分别与 interval_h、interval_v 比较，都满足才合并
    result_texts = []
    current_word = []
    prev_right = prev_bottom = None
    for m in all_matches:
        ox, oy = m["origin_x"], m["origin_y"]
        ow, oh = m["origin_w"], m["origin_h"]
        name = m.get("name", "")
        if prev_right is None and prev_bottom is None:
            current_word.append(name)
            prev_right = ox + ow
            prev_bottom = oy + oh
            continue
        # 当前字左边/上边 与 上一字右边/下边 的间隔（只取正间隔）
        gap_h = max(0, ox - prev_right)
        gap_v = max(0, oy - prev_bottom)
        if gap_h <= interval_h and gap_v <= interval_v:
            current_word.append(name)
            prev_right = ox + ow
            prev_bottom = oy + oh
        else:
            result_texts.append("".join(current_word))
            current_word = [name]
            prev_right = ox + ow
            prev_bottom = oy + oh
    if current_word:
        result_texts.append("".join(current_word))
    # 有间隔时只返回第一个识别到的组合
    return result_texts[0] if result_texts else ""
