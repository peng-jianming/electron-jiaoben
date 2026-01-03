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
    
    # 检查小图尺寸是否合法
    if small_binary.shape[0] > big_binary.shape[0] or small_binary.shape[1] > big_binary.shape[1]:
        return False, None, 0.0
    
    # 使用OpenCV模板匹配 (TM_CCOEFF_NORMED 返回 -1 到 1 的归一化相关系数)
    result = cv2.matchTemplate(big_binary, small_binary, cv2.TM_CCOEFF_NORMED)
    
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
    
    # 使用OpenCV模板匹配
    result = cv2.matchTemplate(big_binary, small_binary, cv2.TM_CCOEFF_NORMED)
    
    # 找出所有超过阈值的位置
    locations = np.where(result >= similarity)
    
    # 构建结果列表 (x, y, similarity)
    matches = []
    for pt in zip(*locations[::-1]):  # 转换为 (x, y) 格式
        matches.append((pt[0], pt[1], result[pt[1], pt[0]]))
    
    # 按相似度降序排序
    matches.sort(key=lambda x: x[2], reverse=True)
    
    return matches


if __name__ == "__main__":
    # 测试示例
    import os
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 测试用例
    test_image = os.path.join(script_dir, "111111111.bmp")
    output_image = os.path.join(script_dir, "output_binary_test.png")
    
    if os.path.exists(test_image):
        result = color_filter_binarize(test_image, "D7CCC6-0E0E09", output_image)
        aaa = color_match_template('9a8de478.png', '333.png', "D7CCC6-0E0E09", 0.8)
        print(aaa,"==========")
        print(f"二值化完成，输出图片: {output_image}")
        print(f"图片尺寸: {result.shape}")
        print(f"白色像素数: {np.sum(result == 255)}")
        print(f"黑色像素数: {np.sum(result == 0)}")
    else:
        print(f"测试图片不存在: {test_image}")

