import cv2
import numpy as np
from PIL import Image
def normalize_ccorr(result):
    """
    将TM_CCORR结果归一化到[0,1]
    """
    # 方法1：简单线性归一化
    result_norm = (result - result.min()) / (result.max() - result.min())
    
    # 方法2：使用图像和模板的能量归一化（更准确）
    # template_energy = np.sum(template**2)
    # result_norm = result / template_energy
    
    return result_norm

def normalize_ccoeff(result):
    """
    将TM_CCOEFF结果归一化到[0,1]
    TM_CCOEFF的原始范围是[-1,1]
    """
    # TM_CCOEFF结果范围是[-1,1]，其中1表示完全匹配
    # 将其映射到[0,1]
    similarity_ccoeff = (result + 1) / 2.0
    
    return similarity_ccoeff

def opencv颜色偏色找图(large_image_path, small_image_path, color_tolerance, similarity=0.8, region=(0, 0, 0, 0)):
    """
    使用颜色偏色二值化后进行模板匹配找图

    :param large_image_path: 大图路径
    :param small_image_path: 小图路径
    :param color_tolerance: 颜色偏色字符串，格式如 "D7CCC6-0E0E09"
                           其中D7CCC6为基准色(RGB)，0E0E09为RGB各通道的允许偏差
    :param similarity: 相似度阈值，0-1之间，默认0.8
    :param region: 检测区域 (x, y, width, height)，如果全为0则检测整个大图
    :return: 找到的位置 {"x": x, "y": y, "w": w, "h": h, "similarity": similarity} 或 None
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

    # 解析颜色偏色字符串
    base_color_hex, tolerance_hex = color_tolerance.split('-')
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

    # 方案2：自定义“白点匹配率”相似度
    # 只考虑小图中的白色像素，计算它们在大图中对应位置也是白色的比例
    template_mask = (small_binary == 255).astype(np.uint8)

    # 将大图二值结果也转换为 0/1 掩码
    search_mask = (search_binary == 255).astype(np.uint8)
    
    # 使用 TM_CCORR 对两个 0/1 掩码做匹配
    # 对于 0/1 掩码，TM_CCORR 的结果等于滑动窗口内 search_mask * template_mask 的和，
    result = cv2.matchTemplate(search_mask, template_mask, cv2.TM_CCORR)

    # 找到重合白点最多的位置
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    # 自定义相似度：重合白点数 / 模板白点总数，范围[0,1]
    overlap_white = max_val
    white_points = int(np.sum(template_mask))
    custom_similarity = overlap_white / white_points

    # print(f"自定义白点匹配率 - 重合白点: {overlap_white}, 相似度: {custom_similarity:.4f}, 位置: {max_loc}")

    if custom_similarity >= similarity:
        return {
            "x": max_loc[0] + offset_x,
            "y": max_loc[1] + offset_y,
            "w": small_w,
            "h": small_h,
            "similarity": float(custom_similarity)
        }
    return None






if __name__ == "__main__":
    large_image_path = "ttt.png"
    small_image_path = "aaa.png"
    color_tolerance = "C9C0B2-25211F"
    similarity = 0.8
    region = (0, 0, 0, 0)
    
    print("测试原始方案...")
    result = opencv颜色偏色找图(large_image_path, small_image_path, color_tolerance, similarity, region)
    print(f"结果: {result}")