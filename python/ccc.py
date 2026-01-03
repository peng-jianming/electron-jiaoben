import cv2
import numpy as np


def feature_match(large_image_path, small_image_path, min_match_count=10, ratio_threshold=0.75):
    """
    使用ORB特征匹配在大图中查找小图
    
    参数:
        large_image_path: 大图路径
        small_image_path: 小图路径  
        min_match_count: 最小匹配点数，默认10
        ratio_threshold: 匹配比率阈值，默认0.75（越小越严格）
    
    返回:
        找到时返回: {
            "found": True,
            "x": 左上角x坐标,
            "y": 左上角y坐标,
            "w": 宽度,
            "h": 高度,
            "center_x": 中心点x,
            "center_y": 中心点y,
            "match_count": 匹配点数量,
            "corners": 四个角点坐标
        }
        未找到时返回: {"found": False, "match_count": 匹配点数量}
    """
    # 读取图像
    large_img = cv2.imread(large_image_path, cv2.IMREAD_GRAYSCALE)
    small_img = cv2.imread(small_image_path, cv2.IMREAD_GRAYSCALE)
    
    if large_img is None:
        print(f"无法读取大图: {large_image_path}")
        return {"found": False, "match_count": 0}
    
    if small_img is None:
        print(f"无法读取小图: {small_image_path}")
        return {"found": False, "match_count": 0}
    
    # 创建ORB特征检测器
    orb = cv2.ORB_create(nfeatures=1000)
    
    # 检测特征点和计算描述符
    kp1, des1 = orb.detectAndCompute(small_img, None)
    kp2, des2 = orb.detectAndCompute(large_img, None)
    print(des1, des2)
    if des1 is None or des2 is None:
        print("无法检测到足够的特征点")
        return {"found": False, "match_count": 0}
    
    # 创建BF匹配器
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    
    # KNN匹配
    try:
        matches = bf.knnMatch(des1, des2, k=2)
    except Exception as e:
        print(f"匹配失败: {e}")
        return {"found": False, "match_count": 0}
    
    # 应用比率测试筛选好的匹配
    good_matches = []
    for match_pair in matches:
        if len(match_pair) == 2:
            m, n = match_pair
            if m.distance < ratio_threshold * n.distance:
                good_matches.append(m)
    
    match_count = len(good_matches)
    print(f"找到 {match_count} 个有效匹配点")
    
    # 判断是否找到足够的匹配点
    if match_count >= min_match_count:
        # 提取匹配点坐标
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        
        # 计算单应性矩阵
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        
        if M is not None:
            # 获取小图的四个角点
            h, w = small_img.shape
            pts = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
            
            # 变换到大图坐标
            dst = cv2.perspectiveTransform(pts, M)
            corners = dst.reshape(-1, 2).tolist()
            
            # 计算边界框
            x_coords = [p[0] for p in corners]
            y_coords = [p[1] for p in corners]
            
            min_x = int(min(x_coords))
            min_y = int(min(y_coords))
            max_x = int(max(x_coords))
            max_y = int(max(y_coords))
            
            width = max_x - min_x
            height = max_y - min_y
            center_x = min_x + width // 2
            center_y = min_y + height // 2
            
            return {
                "found": True,
                "x": min_x,
                "y": min_y,
                "w": width,
                "h": height,
                "center_x": center_x,
                "center_y": center_y,
                "match_count": match_count,
                "corners": corners
            }
    
    return {"found": False, "match_count": match_count}


def draw_match_result(large_image_path, small_image_path, output_path="match_result.png"):
    """
    绘制特征匹配结果并保存
    
    参数:
        large_image_path: 大图路径
        small_image_path: 小图路径
        output_path: 输出图片路径
    """
    result = feature_match(large_image_path, small_image_path)
    
    if result["found"]:
        # 读取大图（彩色）
        img = cv2.imread(large_image_path)
        
        # 绘制边界框
        corners = np.int32(result["corners"])
        cv2.polylines(img, [corners], True, (0, 255, 0), 3)
        
        # 绘制中心点
        cv2.circle(img, (result["center_x"], result["center_y"]), 5, (0, 0, 255), -1)
        
        # 保存结果
        cv2.imwrite(output_path, img)
        print(f"匹配结果已保存到: {output_path}")
    else:
        print("未找到匹配")


# 使用示例
if __name__ == "__main__":
    # 示例用法
    large_img = "9a8de478.png"  # 大图路径
    small_img = "333.png"     # 小图路径
    
    # 基本使用
    result = feature_match(large_img, small_img)
    
    if result["found"]:
        print(f"找到目标!")
        print(f"位置: ({result['x']}, {result['y']})")
        print(f"尺寸: {result['w']} x {result['h']}")
        print(f"中心点: ({result['center_x']}, {result['center_y']})")
    else:
        print("未找到目标")
    
    # 绘制并保存结果
    # draw_match_result(large_img, small_img, "output.png")

