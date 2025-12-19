import cv2
import numpy as np
import os

def find_image_in_region(large_img_path, small_img_path, tolerance=0, similarity=0.9, region=(0, 0, 0, 0)):
    """
    在大图的指定区域中查找小图（仅支持图片路径）
    
    参数:
        large_img_path: 大图路径
        small_img_path: 小图路径
        tolerance: 像素颜色容差 (0-255)
        similarity: 相似度阈值 (0.0-1.0)
        region: 检测区域 (x, y, width, height)，如果全为0或超出范围则检测整个大图
    
    返回:
        如果找到: {"x": x, "y": y, "similarity": similarity, "width": width, "height": height}
        如果没找到: None
    """
    try:
        # 1. 检查文件是否存在
        if not os.path.exists(large_img_path):
            print(f"大图不存在: {large_img_path}")
            return None
        if not os.path.exists(small_img_path):
            print(f"小图不存在: {small_img_path}")
            return None
        
        # 2. 加载大图（带Alpha通道）
        large_img = cv2.imread(large_img_path, cv2.IMREAD_UNCHANGED)
        if large_img is None:
            print(f"无法加载大图: {large_img_path}")
            return None
            
        # 确保有Alpha通道
        if large_img.shape[2] == 3:
            large_img = cv2.cvtColor(large_img, cv2.COLOR_BGR2BGRA)
        
        # 3. 加载小图（带Alpha通道）
        small_img = cv2.imread(small_img_path, cv2.IMREAD_UNCHANGED)
        if small_img is None:
            print(f"无法加载小图: {small_img_path}")
            return None
            
        # 确保有Alpha通道
        if small_img.shape[2] == 3:
            small_img = cv2.cvtColor(small_img, cv2.COLOR_BGR2BGRA)
        
        # 4. 获取图像尺寸
        large_h, large_w = large_img.shape[:2]
        small_h, small_w = small_img.shape[:2]
        
        # 5. 处理检测区域
        region_x, region_y, region_w, region_h = region
        
        # 检查是否应该检测整个图像
        use_full_image = False
        if region_w <= 0 or region_h <= 0:
            use_full_image = True
        elif (region_x < 0 or region_y < 0 or 
              region_x + region_w > large_w or region_y + region_h > large_h):
            print(f"检测区域超出图像范围，改为全图检测")
            use_full_image = True
        
        if use_full_image:
            region_x, region_y = 0, 0
            region_w, region_h = large_w, large_h
            crop_img = large_img
        else:
            # 裁剪出指定区域
            crop_img = large_img[region_y:region_y+region_h, region_x:region_x+region_w]
        
        # 6. 检查小图是否大于区域
        if small_w > region_w or small_h > region_h:
            print(f"小图尺寸({small_w}x{small_h})大于检测区域({region_w}x{region_h})")
            return None
        
        # 7. 提取小图的Alpha通道作为掩码
        # 分离通道
        s_b, s_g, s_r, s_a = cv2.split(small_img)
        
        # 创建掩码：Alpha > 0 的部分为 255，否则为 0
        _, mask = cv2.threshold(s_a, 0, 255, cv2.THRESH_BINARY)
        
        # 8. 模板匹配
        # 使用不同的匹配方法提高准确性
        methods = [
            (cv2.TM_CCOEFF_NORMED, 1.0),  # 相关系数归一化
            (cv2.TM_CCORR_NORMED, 1.0),   # 相关归一化
        ]
        
        best_match = None
        best_val = 0
        crop_h, crop_w = crop_img.shape[:2]
        
        # 转换为BGR用于匹配（保留掩码）
        crop_bgr = cv2.cvtColor(crop_img, cv2.COLOR_BGRA2BGR)
        small_bgr = cv2.cvtColor(small_img, cv2.COLOR_BGRA2BGR)
        
        # 计算匹配结果
        for method, weight in methods:
            result = cv2.matchTemplate(crop_bgr, small_bgr, method, mask=mask)
            
            # 找到最大值和最小值的位置
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 根据匹配方法选择最佳位置
            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                current_val = 1 - min_val  # 对于平方差方法，值越小越好
                current_loc = min_loc
            else:
                current_val = max_val
                current_loc = max_loc
            
            # 应用权重
            weighted_val = current_val * weight
            
            if weighted_val > best_val:
                best_val = weighted_val
                best_match = current_loc
        
        # 9. 如果匹配度不足，直接返回
        if best_val < similarity:
            # print(f"模板匹配度不足: {best_val:.4f} < {similarity}")
            return None
        
        # 将区域内的坐标转换为大图坐标
        start_x = region_x + best_match[0]
        start_y = region_y + best_match[1]
        
        # 10. 根据容差进行二次像素级验证
        final_similarity = best_val
        
        if tolerance > 0:
            # 准备像素数据
            total_pixels = 0
            matched_pixels = 0
            
            # 提取小图的RGBA数据
            s_b, s_g, s_r, s_a = cv2.split(small_img)
            
            # 获取匹配区域在大图中的位置
            end_x = start_x + small_w
            end_y = start_y + small_h
            
            # 确保不超出大图边界
            if end_x > large_w or end_y > large_h:
                return None
            
            # 提取匹配区域
            match_area = large_img[start_y:end_y, start_x:end_x]
            
            # 分离匹配区域的通道
            m_b, m_g, m_r, m_a = cv2.split(match_area)
            
            # 遍历像素
            for y in range(small_h):
                for x in range(small_w):
                    # 跳过小图中的透明像素
                    if s_a[y, x] == 0:
                        continue
                    
                    total_pixels += 1
                    
                    # 获取小图像素值
                    sr, sg, sb, sa = s_r[y, x], s_g[y, x], s_b[y, x], s_a[y, x]
                    
                    # 获取大图对应位置像素值
                    mr, mg, mb, ma = m_r[y, x], m_g[y, x], m_b[y, x], m_a[y, x]
                    
                    # 计算颜色差异
                    r_diff = abs(int(sr) - int(mr))
                    g_diff = abs(int(sg) - int(mg))
                    b_diff = abs(int(sb) - int(mb))
                    a_diff = abs(int(sa) - int(ma))
                    
                    # 检查是否在容差范围内
                    if (r_diff <= tolerance and g_diff <= tolerance and 
                        b_diff <= tolerance and a_diff <= tolerance):
                        matched_pixels += 1
            
            # 计算像素级匹配率
            pixel_match_rate = matched_pixels / total_pixels if total_pixels > 0 else 0
            
            # 如果像素级匹配度不足，返回None
            if pixel_match_rate < similarity:
                return None
            
            final_similarity = pixel_match_rate
        
        # 11. 返回结果
        return {
            "x": start_x,
            "y": start_y,
            "similarity": float(final_similarity),
            "width": small_w,
            "height": small_h,
            "region_used": (region_x, region_y, region_w, region_h)
        }
        
    except Exception as e:
        print(f"找图出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


# 快速版本（不进行像素级验证）
def find_image_fast(large_img_path, small_img_path, similarity=0.9, region=(0, 0, 0, 0)):
    """
    快速找图（仅模板匹配，不进行像素级验证）
    """
    return find_image_in_region(
        large_img_path,
        small_img_path,
        tolerance=0,  # 不进行像素验证
        similarity=similarity,
        region=region
    )


# 多区域找图（同时检测多个区域）
def find_image_in_regions(large_img_path, small_img_path, regions, tolerance=0, similarity=0.9):
    """
    在多个区域中查找小图
    
    参数:
        regions: 区域列表，每个区域为 (x, y, width, height)
    
    返回:
        第一个找到的结果，或None
    """
    for region in regions:
        result = find_image_in_region(
            large_img_path,
            small_img_path,
            tolerance=tolerance,
            similarity=similarity,
            region=region
        )
        if result is not None:
            return result
    return None


# 使用示例
if __name__ == "__main__":
    # 示例1：全图检测
    result1 = find_image_in_region(
        "large.png",
        "small.png",
        tolerance=10,
        similarity=0.9
    )
    print(f"全图检测结果: {result1}")
    
    # 示例2：区域检测
    result2 = find_image_in_region(
        "large.png",
        "small.png",
        tolerance=10,
        similarity=0.9,
        region=(100, 100, 200, 200)  # 只检测(100,100)到(300,300)的区域
    )
    print(f"区域检测结果: {result2}")
    
    # 示例3：快速检测（无像素验证）
    result3 = find_image_fast(
        "large.png",
        "small.png",
        similarity=0.95,
        region=(50, 50, 150, 150)
    )
    print(f"快速检测结果: {result3}")
    
    # 示例4：多区域检测
    regions = [
        (0, 0, 100, 100),
        (200, 200, 100, 100),
        (400, 0, 100, 100)
    ]
    result4 = find_image_in_regions(
        "large.png",
        "small.png",
        regions=regions,
        similarity=0.9
    )
    print(f"多区域检测结果: {result4}")