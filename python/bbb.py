import numpy as np
from PIL import Image
import cv2
from typing import Union, Tuple, Optional


def _parse_color_tolerance(color_tolerance: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    解析颜色偏色字符串
    
    Args:
        color_tolerance: 颜色偏色字符串，格式如 "D7CCC6-0E0E09"
    
    Returns:
        (base_color, tolerance) 元组
    """
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
    
    return base_color, tolerance


def _binarize_array(img_array: np.ndarray, base_color: np.ndarray, tolerance: np.ndarray) -> np.ndarray:
    """
    对图片数组进行颜色偏色二值化处理
    
    Args:
        img_array: RGB图片数组 (H, W, 3)
        base_color: 基准色
        tolerance: 偏色范围
    
    Returns:
        二值化后的numpy数组
    """
    img_int16 = img_array.astype(np.int16)
    diff = np.abs(img_int16 - base_color)
    mask = np.all(diff <= tolerance, axis=2)
    return np.where(mask, 255, 0).astype(np.uint8)


def color_filter_binarize(image_path: str, color_tolerance: str, output_path: str = None) -> np.ndarray:
    """
    根据基准色和偏色范围对图片进行二值化处理
    
    Args:
        image_path: 输入图片路径
        color_tolerance: 颜色偏色字符串，格式如 "D7CCC6-0E0E09"
                        其中D7CCC6为基准色(RGB)，0E0E09为RGB各通道的允许偏差
        output_path: 输出图片路径（可选），如果提供则保存结果
    
    Returns:
        二值化后的numpy数组 (0或255)
    
    Example:
    """
    # 解析颜色偏色字符串
    base_color, tolerance = _parse_color_tolerance(color_tolerance)
    
    # 读取图片并转换为RGB
    img = Image.open(image_path).convert('RGB')
    img_array = np.array(img)
    
    # 二值化处理
    binary = _binarize_array(img_array, base_color, tolerance)
    
    # 如果指定了输出路径，保存结果
    if output_path:
        result_img = Image.fromarray(binary, mode='L')
        result_img.save(output_path)
    
    return binary


def color_match_template(
    big_image: Union[str, np.ndarray],
    small_image: Union[str, np.ndarray],
    color_tolerance: str,
    similarity: float = 0.8
) -> Tuple[bool, Optional[Tuple[int, int]], float]:
    """
    使用颜色偏色二值化后进行模板匹配，判断小图是否在大图中
    匹配时忽略黑色像素（只匹配白色像素区域）
    
    Args:
        big_image: 大图路径或numpy数组(RGB)
        small_image: 小图路径或numpy数组(RGB)
        color_tolerance: 颜色偏色字符串，格式如 "D7CCC6-0E0E09"
        similarity: 相似度阈值 (0-1)，默认0.8
    
    Returns:
        (is_found, position, max_similarity) 元组
        - is_found: 是否找到匹配
        - position: 匹配位置 (x, y)，未找到时为None
        - max_similarity: 最大相似度值
    
    Example:
        # found, pos, sim = color_match_template("big.png", "small.png", "D7CCC6-0E0E09", 0.9)
        # if found:
        #     print(f"找到匹配，位置: {pos}, 相似度: {sim:.2f}")
    """
    # 解析颜色偏色
    base_color, tolerance = _parse_color_tolerance(color_tolerance)
    
    # 加载大图
    if isinstance(big_image, str):
        big_img = Image.open(big_image).convert('RGB')
        big_array = np.array(big_img)
    else:
        big_array = big_image
    
    # 加载小图
    if isinstance(small_image, str):
        small_img = Image.open(small_image).convert('RGB')
        small_array = np.array(small_img)
    else:
        small_array = small_image
    
    # 对大图和小图进行二值化处理
    big_binary = _binarize_array(big_array, base_color, tolerance)
    small_binary = _binarize_array(small_array, base_color, tolerance)
    # cv2.imshow('big_binary', big_binary)
    # cv2.imshow('small_binary', small_binary)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # 检查小图尺寸是否合法
    if small_binary.shape[0] > big_binary.shape[0] or small_binary.shape[1] > big_binary.shape[1]:
        return False, None, 0.0
    
    # 创建掩码：白色像素(255)参与匹配，黑色像素(0)被忽略
    mask = small_binary.copy()
    
    # 使用带掩码的模板匹配 (TM_CCORR_NORMED 支持掩码，返回 0 到 1 的归一化相关系数)
    result = cv2.matchTemplate(big_binary, small_binary, cv2.TM_CCORR_NORMED, mask=mask)
    
    # 获取最大匹配值和位置
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    # 判断是否达到相似度阈值
    is_found = max_val >= similarity
    position = max_loc if is_found else None
    
    return is_found, position, max_val


def color_match_template_all(
    big_image: Union[str, np.ndarray],
    small_image: Union[str, np.ndarray],
    color_tolerance: str,
    similarity: float = 0.8
) -> list:
    """
    使用颜色偏色二值化后进行模板匹配，查找所有匹配位置
    匹配时忽略黑色像素（只匹配白色像素区域）
    
    Args:
        big_image: 大图路径或numpy数组(RGB)
        small_image: 小图路径或numpy数组(RGB)
        color_tolerance: 颜色偏色字符串，格式如 "D7CCC6-0E0E09"
        similarity: 相似度阈值 (0-1)，默认0.8
    
    Returns:
        匹配结果列表，每个元素为 (x, y, similarity) 元组
    
    Example:
        # matches = color_match_template_all("big.png", "small.png", "D7CCC6-0E0E09", 0.9)
        # for x, y, sim in matches:
        ...     print(f"位置: ({x}, {y}), 相似度: {sim:.2f}")
    """
    # 解析颜色偏色
    base_color, tolerance = _parse_color_tolerance(color_tolerance)
    
    # 加载大图
    if isinstance(big_image, str):
        big_img = Image.open(big_image).convert('RGB')
        big_array = np.array(big_img)
    else:
        big_array = big_image
    
    # 加载小图
    if isinstance(small_image, str):
        small_img = Image.open(small_image).convert('RGB')
        small_array = np.array(small_img)
    else:
        small_array = small_image
    
    # 对大图和小图进行二值化处理
    big_binary = _binarize_array(big_array, base_color, tolerance)
    small_binary = _binarize_array(small_array, base_color, tolerance)
    
    # 检查小图尺寸是否合法
    if small_binary.shape[0] > big_binary.shape[0] or small_binary.shape[1] > big_binary.shape[1]:
        return []
    
    # 创建掩码：白色像素(255)参与匹配，黑色像素(0)被忽略
    # mask = small_binary.copy()
    
    # 使用带掩码的模板匹配 (TM_CCORR_NORMED 支持掩码)
    result = cv2.matchTemplate(big_binary, small_binary, cv2.TM_CCORR_NORMED)

    # 找出所有超过阈值的位置
    locations = np.where(result >= similarity)
    
    # 构建结果列表 (x, y, similarity)
    matches = []
    for pt in zip(*locations[::-1]):  # 转换为 (x, y) 格式
        matches.append((pt[0], pt[1], result[pt[1], pt[0]]))
    
    # 按相似度降序排序
    matches.sort(key=lambda x: x[2], reverse=True)
    
    return matches




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


if __name__ == "__main__":
    # 测试示例
    import os
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 测试用例
    test_image = os.path.join(script_dir, "111111111.bmp")
    output_image = os.path.join(script_dir, "output_binary_test.png")
    
    if os.path.exists(test_image):
        result = color_filter_binarize(test_image, "D2C4B8-1C1923", output_image)
        # aaa = color_match_template('9a8de478.png', '444.png', "D7CCC6-0E0E09", 0.8)
        aaa = opencv找图('9a8de478.png', 'ccc.png', 0.8)
        print(aaa,"==========")
        print(f"二值化完成，输出图片: {output_image}")
        print(f"图片尺寸: {result.shape}")
        print(f"白色像素数: {np.sum(result == 255)}")
        print(f"黑色像素数: {np.sum(result == 0)}")
    else:
        print(f"测试图片不存在: {test_image}")

