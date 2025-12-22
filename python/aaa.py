
import json
import random
import websockets
import os
import time
import asyncio

import cv2
import numpy as np
from PIL import Image

import math


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
    # large_image = cv2.imread(large_image_path)
    # small_image = cv2.imread(small_image_path)


        # 2. 加载大图（带Alpha通道）
    large_image = cv2.imread(large_image_path, cv2.IMREAD_UNCHANGED)

    # 确保有Alpha通道
    if large_image.shape[2] == 3:
        large_image = cv2.cvtColor(large_image, cv2.COLOR_BGR2BGRA)

    # 3. 加载小图（带Alpha通道）
    small_image = cv2.imread(small_image_path, cv2.IMREAD_UNCHANGED)

    # 确保有Alpha通道
    if small_image.shape[2] == 3:
        small_image = cv2.cvtColor(small_image, cv2.COLOR_BGR2BGRA)



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

    s_b, s_g, s_r, s_a = cv2.split(small_image)

    # 创建掩码：Alpha > 0 的部分为 255，否则为 0
    _, mask = cv2.threshold(s_a, 0, 255, cv2.THRESH_BINARY)

    # 使用模板匹配
    result = cv2.matchTemplate(search_area, small_image, cv2.TM_CCOEFF_NORMED, mask=mask)

    # 找到最匹配的位置
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # 检查是否达到相似度阈值
    if max_val >= similarity:
        # 返回相对于整个大图的坐标（加上偏移量）
        return {"x": max_loc[0] + offset_x, "y": max_loc[1] + offset_y, 'w': w, 'h': h, 'similarity': max_val}

    return None

def opencv找透明图(large_img_path, small_img_path, tolerance=0, similarity=0.9, region=(0, 0, 0, 0)):
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
            crop_img = large_img[region_y:region_y + region_h, region_x:region_x + region_w]

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
            (cv2.TM_CCORR_NORMED, 1.0),  # 相关归一化
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

            # 确保不超出大图边界（包括起始坐标为负数的情况）
            if start_x < 0 or start_y < 0 or end_x > large_w or end_y > large_h:
                return None

            # 提取匹配区域
            match_area = large_img[start_y:end_y, start_x:end_x]

            # 检查匹配区域是否为空
            if match_area.size == 0:
                return None

            # 确保匹配区域有4个通道（BGRA）
            if len(match_area.shape) < 3 or match_area.shape[2] != 4:
                # 如果只有3个通道，添加Alpha通道
                if len(match_area.shape) == 3 and match_area.shape[2] == 3:
                    match_area = cv2.cvtColor(match_area, cv2.COLOR_BGR2BGRA)
                else:
                    return None

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
            "w": small_w,
            "h": small_h,
            "region_used": (region_x, region_y, region_w, region_h)
        }

    except Exception as e:
        print(f"找图出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def opencv找透明图2(large_img_path, small_img_path,  similarity=0.9, region=(0, 0, 0, 0)):
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
            crop_img = large_img[region_y:region_y + region_h, region_x:region_x + region_w]

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
            (cv2.TM_CCORR_NORMED, 1.0),  # 相关归一化
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
            print(weighted_val, best_val)
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

        # 11. 返回结果
        return {
            "x": start_x,
            "y": start_y,
            "similarity": float(final_similarity),
            "w": small_w,
            "h": small_h,
            "region_used": (region_x, region_y, region_w, region_h)
        }

    except Exception as e:
        print(f"找图出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def aaaaaaaaaaa(large_image_path, small_image_path, similarity_threshold=0.9):
    try:
        # 1. 读取图片
        large_img = cv2.imread(large_image_path, cv2.IMREAD_COLOR)
        small_img = cv2.imread(small_image_path, cv2.IMREAD_UNCHANGED)

        if large_img is None:
            raise ValueError(f"无法读取大图: {large_image_path}")
        if small_img is None:
            raise ValueError(f"无法读取小图: {small_image_path}")

        # 2. 转换颜色空间（BGR转RGB如果需要的话）
        large_img_rgb = cv2.cvtColor(large_img, cv2.COLOR_BGR2RGB)

        # 3. 处理小图的透明通道（如果存在）
        if small_img.shape[2] == 4:  # 有alpha通道
            # 分离透明通道作为mask
            small_rgb = small_img[:, :, :3]
            alpha_channel = small_img[:, :, 3]

            # 将透明区域设置为纯黑色，以便模板匹配忽略这些区域
            mask = alpha_channel > 0  # 非透明区域

            # 获取非透明区域的边界框，减少匹配范围
            non_zero_indices = np.where(mask)
            if len(non_zero_indices[0]) == 0:
                return {'found': False, 'error': '小图完全透明'}

            y_min, y_max = non_zero_indices[0].min(), non_zero_indices[0].max()
            x_min, x_max = non_zero_indices[1].min(), non_zero_indices[1].max()

            # 裁剪小图到非透明区域
            small_cropped = small_rgb[y_min:y_max + 1, x_min:x_max + 1]
            mask_cropped = mask[y_min:y_max + 1, x_min:x_max + 1]
        else:
            small_cropped = cv2.cvtColor(small_img, cv2.COLOR_BGR2RGB)
            mask_cropped = None

        # 4. 检查尺寸
        h_small, w_small = small_cropped.shape[:2]
        h_large, w_large = large_img_rgb.shape[:2]

        if h_small > h_large or w_small > w_large:
            return {'found': False, 'error': '小图比大图大'}

        # 5. 使用模板匹配（考虑透明区域）
        if mask_cropped is not None:
            # 对于有透明通道的图片，使用掩码匹配
            # 将掩码转换为0-255的uint8
            mask_uint8 = (mask_cropped * 255).astype(np.uint8)

            # 使用TM_CCOEFF_NORMED方法，支持掩码
            result = cv2.matchTemplate(large_img_rgb, small_cropped,
                                       cv2.TM_CCOEFF_NORMED, mask=mask_uint8)
        else:
            # 对于没有透明通道的图片，直接匹配
            result = cv2.matchTemplate(large_img_rgb, small_cropped,
                                       cv2.TM_CCOEFF_NORMED)

        # 6. 找到最佳匹配位置
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # 7. 判断是否找到
        if max_val >= similarity_threshold:
            # 计算实际位置（考虑裁剪偏移）
            x = max_loc[0]
            y = max_loc[1]

            if mask_cropped is not None:
                x += x_min
                y += y_min

            return {
                'found': True,
                'position': (x, y),
                'confidence': float(max_val),
                'bounding_box': (x, y, w_small, h_small),
                'match_score': max_val
            }
        else:
            return {
                'found': False,
                'best_match_score': float(max_val),
                'best_position': (max_loc[0], max_loc[1]) if max_val > 0 else None
            }

    except Exception as e:
        return {'found': False, 'error': str(e)}

if __name__ == "__main__":

    aa =  opencv找透明图('3.png', 'aaaa.png', 30, 0)
    bb = opencv找透明图2('3.png', 'aaaa.png', 0)
    cc = opencv找图('3.png', 'aaaa.png', 0)
    dd = aaaaaaaaaaa('3.png', 'aaaa.png', 0)
    print(aa)
    print(bb)
    print(cc)
    print(dd)