# 透明图处理工具2
# 功能: 将 toumingtu.py 得到的结果图片 a 作为参数,传入另外一张图片 b
# 如果图片 b 的某个像素在颜色容差范围内,那么将图片 a 的那个像素设置为透明

import os
from PIL import Image

# 配置路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def parse_color_tolerance(color_tolerance_str):
    """
    解析颜色容差参数
    格式: 'C9C0B2-203040'
    返回: (base_r, base_g, base_b, tolerance_r, tolerance_g, tolerance_b)
    """
    if not color_tolerance_str or '-' not in color_tolerance_str:
        return None
    
    try:
        parts = color_tolerance_str.split('-')
        if len(parts) != 2:
            return None
        
        base_color = parts[0].strip().upper()
        tolerance_color = parts[1].strip().upper()
        
        # 解析基准色 (6位16进制)
        if len(base_color) != 6:
            return None
        base_r = int(base_color[0:2], 16)
        base_g = int(base_color[2:4], 16)
        base_b = int(base_color[4:6], 16)
        
        # 解析容差 (6位16进制)
        if len(tolerance_color) != 6:
            return None
        tolerance_r = int(tolerance_color[0:2], 16)
        tolerance_g = int(tolerance_color[2:4], 16)
        tolerance_b = int(tolerance_color[4:6], 16)
        
        return (base_r, base_g, base_b, tolerance_r, tolerance_g, tolerance_b)
    except (ValueError, IndexError) as e:
        print(f'解析颜色容差参数失败: {color_tolerance_str}, 错误: {e}')
        return None


def is_color_in_range(r, g, b, base_r, base_g, base_b, tolerance_r, tolerance_g, tolerance_b):
    """
    检查颜色是否在容差范围内
    返回: True表示在范围内, False表示不在范围内
    """
    r_diff = abs(r - base_r)
    g_diff = abs(g - base_g)
    b_diff = abs(b - base_b)
    
    return r_diff <= tolerance_r and g_diff <= tolerance_g and b_diff <= tolerance_b


def process_image_with_mask(image_a_path, image_b_path, color_tolerance, output_path=None):
    """
    处理图片: 如果图片 b 的某个像素在颜色容差范围内,那么将图片 a 的那个像素设置为透明
    
    参数:
        image_a_path: toumingtu.py 得到的结果图片 a 的路径
        image_b_path: 用于判断的图片 b 的路径
        color_tolerance: 颜色容差参数, 格式: 'C9C0B2-203040'
        output_path: 输出图片路径, 如果为 None, 则覆盖 image_a_path
    
    返回:
        True 表示处理成功, False 表示处理失败
    """
    try:
        # 解析颜色容差参数
        color_tolerance_params = parse_color_tolerance(color_tolerance)
        if color_tolerance_params is None:
            print(f'颜色容差参数格式错误: {color_tolerance}')
            return False
        
        base_r, base_g, base_b, tolerance_r, tolerance_g, tolerance_b = color_tolerance_params
        
        # 读取图片 a
        if not os.path.exists(image_a_path):
            print(f'图片 a 不存在: {image_a_path}')
            return False
        
        image_a = Image.open(image_a_path).convert("RGBA")
        
        # 读取图片 b
        if not os.path.exists(image_b_path):
            print(f'图片 b 不存在: {image_b_path}')
            return False
        
        image_b = Image.open(image_b_path).convert("RGBA")
        
        # 确保尺寸一致
        if image_a.size != image_b.size:
            print(f'图片尺寸不一致: 图片 a {image_a.size}, 图片 b {image_b.size}')
            # 如果尺寸不一致, 将图片 b 调整为图片 a 的尺寸
            image_b = image_b.resize(image_a.size, Image.Resampling.LANCZOS)
            print(f'已将图片 b 调整为图片 a 的尺寸: {image_a.size}')
        
        width, height = image_a.size
        # 获取像素数据以便读写
        pixels_a = image_a.load()
        pixels_b = image_b.load()
        
        transparent_count = 0
        
        # 遍历所有像素
        for x in range(width):
            for y in range(height):
                # 获取图片 a 的像素 (r, g, b, a)
                r_a, g_a, b_a, a_a = pixels_a[x, y]
                
                # 如果图片 a 这个点已经是透明的, 跳过
                if a_a == 0:
                    continue
                
                # 获取图片 b 的像素
                r_b, g_b, b_b, a_b = pixels_b[x, y]
                
                # 检查图片 b 的像素是否在颜色容差范围内
                if is_color_in_range(r_b, g_b, b_b, base_r, base_g, base_b, tolerance_r, tolerance_g, tolerance_b):
                    # 在范围内, 将图片 a 对应位置的像素设置为透明
                    pixels_a[x, y] = (0, 0, 0, 0)
                    transparent_count += 1
        
        # 确定输出路径
        if output_path is None:
            output_path = image_a_path
        
        # 保存结果
        image_a.save(output_path)
        print(f'处理完成: 将 {transparent_count} 个像素设置为透明')
        print(f'结果已保存到: {output_path}')
        
        return True
        
    except Exception as err:
        print(f'处理出错: {err}')
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 示例用法
    # 图片 a 的路径 (toumingtu.py 的结果图片)
    image_a_path = os.path.join(BASE_DIR, 'toumingtu.png')
    
    # 图片 b 的路径 (用于判断的图片)
    image_b_path = os.path.join(BASE_DIR, '9a8de478.png')
    
    # 颜色容差参数
    color_tolerance_val = 'C9C0B2-25211F'
    
    # 输出路径 (如果为 None, 则覆盖 image_a_path)
    output_path = os.path.join(BASE_DIR, 'toumingtu2_result.png')
    
    # 执行处理
    process_image_with_mask(image_a_path, image_b_path, color_tolerance_val, output_path)






# 72B23F-1A1D1D|A33631-312B2D