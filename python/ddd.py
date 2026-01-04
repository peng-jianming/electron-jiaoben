"""
轮廓匹配示例模块
支持传入大图和小图，进行轮廓提取和模板匹配
"""
import cv2
import numpy as np
from typing import Union, Tuple, Optional, List


def contour_match(
    big_image: Union[str, np.ndarray],
    small_image: Union[str, np.ndarray],
    similarity: float = 0.8,
    canny_threshold1: int = 50,
    canny_threshold2: int = 150
) -> Tuple[bool, Optional[Tuple[int, int]], float]:
    """
    使用轮廓提取进行模板匹配，判断小图是否在大图中
    
    Args:
        big_image: 大图路径或numpy数组
        small_image: 小图路径或numpy数组
        similarity: 相似度阈值 (0-1)，默认0.8
        canny_threshold1: Canny边缘检测的低阈值，默认50
        canny_threshold2: Canny边缘检测的高阈值，默认150
    
    Returns:
        (is_found, position, max_similarity) 元组
        - is_found: 是否找到匹配
        - position: 匹配位置 (x, y) 为小图左上角在大图中的坐标，未找到时为None
        - max_similarity: 最大相似度值
    
    Example:
        # found, pos, sim = contour_match("big.png", "small.png", 0.8)
        # if found:
        ...     print(f"找到匹配，位置: {pos}, 相似度: {sim:.2f}")
    """
    # 加载大图
    if isinstance(big_image, str):
        big_img = cv2.imread(big_image)
        if big_img is None:
            raise ValueError(f"无法加载大图: {big_image}")
    else:
        big_img = big_image.copy()
    
    # 加载小图
    if isinstance(small_image, str):
        small_img = cv2.imread(small_image)
        if small_img is None:
            raise ValueError(f"无法加载小图: {small_image}")
    else:
        small_img = small_image.copy()
    
    # 转换为灰度图
    if len(big_img.shape) == 3:
        big_gray = cv2.cvtColor(big_img, cv2.COLOR_BGR2GRAY)
    else:
        big_gray = big_img
    
    if len(small_img.shape) == 3:
        small_gray = cv2.cvtColor(small_img, cv2.COLOR_BGR2GRAY)
    else:
        small_gray = small_img
    
    # 使用Canny边缘检测提取轮廓
    big_edges = cv2.Canny(big_gray, canny_threshold1, canny_threshold2)
    small_edges = cv2.Canny(small_gray, canny_threshold1, canny_threshold2)

    # 定义结构元素
    kernel = np.ones((5, 5), np.uint8)

    # 闭运算
    big_edges = cv2.dilate(big_edges, kernel, iterations=1)
    small_edges = cv2.dilate(small_edges, kernel, iterations=1)
    
    cv2.imshow('big_edges', big_edges)
    cv2.imshow('small_edges', small_edges)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # 检查小图尺寸是否合法
    if small_edges.shape[0] > big_edges.shape[0] or small_edges.shape[1] > big_edges.shape[1]:
        return False, None, 0.0
    
    # 使用轮廓图进行模板匹配
    result = cv2.matchTemplate(big_edges, small_edges, cv2.TM_CCOEFF_NORMED)
    
    # 获取最大匹配值和位置
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    # 判断是否达到相似度阈值
    is_found = max_val >= similarity
    position = max_loc if is_found else None
    
    return is_found, position, max_val


def contour_match_all(
    big_image: Union[str, np.ndarray],
    small_image: Union[str, np.ndarray],
    similarity: float = 0.8,
    canny_threshold1: int = 50,
    canny_threshold2: int = 150,
    nms_threshold: int = 10
) -> List[Tuple[int, int, float]]:
    """
    使用轮廓提取进行模板匹配，查找所有匹配位置
    
    Args:
        big_image: 大图路径或numpy数组
        small_image: 小图路径或numpy数组
        similarity: 相似度阈值 (0-1)，默认0.8
        canny_threshold1: Canny边缘检测的低阈值，默认50
        canny_threshold2: Canny边缘检测的高阈值，默认150
        nms_threshold: 非极大值抑制的距离阈值，用于过滤重叠匹配
    
    Returns:
        匹配结果列表，每个元素为 (x, y, similarity) 元组，按相似度降序排列
    
    Example:
        # matches = contour_match_all("big.png", "small.png", 0.8)
        # for x, y, sim in matches:
        ...     print(f"位置: ({x}, {y}), 相似度: {sim:.2f}")
    """
    # 加载大图
    if isinstance(big_image, str):
        big_img = cv2.imread(big_image)
        if big_img is None:
            raise ValueError(f"无法加载大图: {big_image}")
    else:
        big_img = big_image.copy()
    
    # 加载小图
    if isinstance(small_image, str):
        small_img = cv2.imread(small_image)
        if small_img is None:
            raise ValueError(f"无法加载小图: {small_image}")
    else:
        small_img = small_image.copy()
    
    # 转换为灰度图
    if len(big_img.shape) == 3:
        big_gray = cv2.cvtColor(big_img, cv2.COLOR_BGR2GRAY)
    else:
        big_gray = big_img
    
    if len(small_img.shape) == 3:
        small_gray = cv2.cvtColor(small_img, cv2.COLOR_BGR2GRAY)
    else:
        small_gray = small_img
    
    # 使用Canny边缘检测提取轮廓
    big_edges = cv2.Canny(big_gray, canny_threshold1, canny_threshold2)
    small_edges = cv2.Canny(small_gray, canny_threshold1, canny_threshold2)
    
    # 检查小图尺寸是否合法
    if small_edges.shape[0] > big_edges.shape[0] or small_edges.shape[1] > big_edges.shape[1]:
        return []
    
    # 使用轮廓图进行模板匹配
    result = cv2.matchTemplate(big_edges, small_edges, cv2.TM_CCOEFF_NORMED)
    
    # 找出所有超过阈值的位置
    locations = np.where(result >= similarity)
    
    # 收集所有匹配点及其相似度
    matches = []
    for pt in zip(*locations[::-1]):  # 转换为 (x, y) 格式
        matches.append((pt[0], pt[1], result[pt[1], pt[0]]))
    
    # 按相似度降序排序
    matches.sort(key=lambda x: x[2], reverse=True)
    
    # 非极大值抑制，过滤重叠的匹配
    filtered_matches = []
    for match in matches:
        x, y, sim = match
        is_duplicate = False
        for fm in filtered_matches:
            if abs(x - fm[0]) < nms_threshold and abs(y - fm[1]) < nms_threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            filtered_matches.append(match)
    
    return filtered_matches


def visualize_match(
    big_image: Union[str, np.ndarray],
    small_image: Union[str, np.ndarray],
    similarity: float = 0.8
) -> np.ndarray:
    """
    可视化轮廓匹配结果，返回标注了匹配位置的图像
    
    Args:
        big_image: 大图路径或numpy数组
        small_image: 小图路径或numpy数组
        similarity: 相似度阈值 (0-1)，默认0.8
    
    Returns:
        标注了匹配位置的图像 (numpy数组)
    """
    # 加载大图
    if isinstance(big_image, str):
        big_img = cv2.imread(big_image)
        if big_img is None:
            raise ValueError(f"无法加载大图: {big_image}")
    else:
        big_img = big_image.copy()
    
    # 加载小图获取尺寸
    if isinstance(small_image, str):
        small_img = cv2.imread(small_image)
        if small_img is None:
            raise ValueError(f"无法加载小图: {small_image}")
    else:
        small_img = small_image
    
    h, w = small_img.shape[:2]
    
    # 获取所有匹配位置
    matches = contour_match_all(big_image, small_image, similarity)
    
    # 在大图上绘制匹配位置
    result_img = big_img.copy()
    for x, y, sim in matches:
        # 绘制矩形框
        cv2.rectangle(result_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # 显示相似度
        cv2.putText(result_img, f"{sim:.2f}", (x, y - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    return result_img


# 测试代码
if __name__ == "__main__":
    # 示例用法
    big_image_path = "9a8de478.png"
    small_image_path = "ccc.png"
    
    # 单个匹配
    found, position, sim = contour_match(big_image_path, small_image_path, 0.8)
    if found:
        print(f"找到匹配! 位置: {position}, 相似度: {sim:.2f}")
    else:
        print(f"未找到匹配, 最大相似度: {sim:.2f}")
    
    # 多个匹配
    # matches = contour_match_all(big_image_path, small_image_path, 0.8)
    # print(f"找到 {len(matches)} 个匹配:")
    # for x, y, s in matches:
    #     print(f"  位置: ({x}, {y}), 相似度: {s:.2f}")
    
    # 可视化结果
    # result = visualize_match(big_image_path, small_image_path, 0.8)
    # cv2.imshow("Match Result", result)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    #1. 透明图 + 遮罩  一般情况
    #2. 原图 + 边缘  颜色不单一