from PIL import Image
import numpy as np

def hex_to_rgb(hex_color):
    """将16进制颜色字符串转换为RGB元组"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    else:
        raise ValueError(f"无效的16进制颜色: {hex_color}")
    return (r, g, b)

def parse_tolerance(tolerance_str):
    """
    解析容差字符串，格式: '基准色-色偏'
    例如: 'C9C0B2-25211F'
    返回: (基准色RGB, 色偏RGB)
    """
    if tolerance_str is None:
        return None
    
    try:
        if '-' in tolerance_str:
            base_color_str, tolerance_color_str = tolerance_str.split('-')
            base_rgb = hex_to_rgb(base_color_str)
            tolerance_rgb = hex_to_rgb(tolerance_color_str)
            return (base_rgb, tolerance_rgb)
        else:
            # 如果没有'-'，假设整个字符串是基准色，色偏为0
            base_rgb = hex_to_rgb(tolerance_str)
            return (base_rgb, (0, 0, 0))
    except Exception as e:
        raise ValueError(f"容差格式错误: {tolerance_str}，正确格式: '基准色-色偏' 例如: 'C9C0B2-25211F'")

def compare_with_tolerance(img1_array, img2_array, base_rgb, tolerance_rgb):
    """
    比较两个图片数组，使用基准色和色偏范围
    如果像素颜色在基准色的色偏范围内，视为相同
    """
    # 创建结果数组
    result_array = img1_array.copy()
    
    # 获取图片尺寸
    height, width = img1_array.shape[:2]
    
    # 循环每个像素进行比较
    for y in range(height):
        for x in range(width):
            # 获取两个图片的像素颜色
            pixel1 = img1_array[y, x, :3]  # 只取RGB，忽略Alpha
            pixel2 = img2_array[y, x, :3]
            
            # 检查像素1是否在基准色的色偏范围内
            pixel1_in_range = True
            pixel2_in_range = True
            
            for channel in range(3):
                base_val = base_rgb[channel]
                tolerance_val = tolerance_rgb[channel]
                
                # 检查像素1
                if pixel1[channel] < base_val - tolerance_val or pixel1[channel] > base_val + tolerance_val:
                    pixel1_in_range = False
                
                # 检查像素2
                if pixel2[channel] < base_val - tolerance_val or pixel2[channel] > base_val + tolerance_val:
                    pixel2_in_range = False
            
            # 如果两个像素都在基准色的色偏范围内，则设置为透明
            if pixel1_in_range and pixel2_in_range:
                result_array[y, x, 3] = 0  # 设置alpha通道为0（完全透明）
    
    return result_array

def compare_images_with_hex_tolerance(img1_path, img2_path, output_path="result.png", 
                                     tolerance_str=None, mode="both_in_range"):
    """
    比较两张图片，使用基准色+色偏范围的容差模式
    
    参数:
    img1_path: str - 第一张图片路径（透明图）
    img2_path: str - 第二张图片路径
    output_path: str - 输出图片路径
    tolerance_str: str - 容差字符串，格式: '基准色-色偏' 例如: 'C9C0B2-25211F'
    mode: str - 比较模式，可选:
        'both_in_range': 两个像素都在基准色范围内才透明（默认）
        'either_in_range': 任一像素在基准色范围内就透明
        'img1_in_range': 仅图片1像素在基准色范围内时透明
        'img2_in_range': 仅图片2像素在基准色范围内时透明
    
    返回:
    PIL.Image - 处理后的图片对象
    """
    try:
        # 打开图片
        img1 = Image.open(img1_path).convert("RGBA")
        img2 = Image.open(img2_path).convert("RGBA")
        
        # 确保两张图片尺寸相同
        if img1.size != img2.size:
            print(f"调整图片尺寸: 图片1={img1.size}, 图片2={img2.size}")
            img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)
        
        # 将图片转换为numpy数组
        img1_array = np.array(img1)
        img2_array = np.array(img2)
        
        # 解析容差参数
        if tolerance_str:
            base_rgb, tolerance_rgb = parse_tolerance(tolerance_str)
            print(f"基准色: RGB{base_rgb}")
            print(f"色偏范围: R±{tolerance_rgb[0]}, G±{tolerance_rgb[1]}, B±{tolerance_rgb[2]}")
            
            # 根据选择的模式进行处理
            result_array = img1_array.copy()
            height, width = img1_array.shape[:2]
            
            for y in range(height):
                for x in range(width):
                    pixel1 = img1_array[y, x, :3]
                    pixel2 = img2_array[y, x, :3]
                    
                    # 检查像素是否在基准色范围内
                    pixel1_in_range = True
                    pixel2_in_range = True
                    
                    for channel in range(3):
                        base_val = base_rgb[channel]
                        tolerance_val = tolerance_rgb[channel]
                        
                        if pixel1[channel] < base_val - tolerance_val or pixel1[channel] > base_val + tolerance_val:
                            pixel1_in_range = False
                        
                        if pixel2[channel] < base_val - tolerance_val or pixel2[channel] > base_val + tolerance_val:
                            pixel2_in_range = False
                    
                    # 根据模式决定是否设置透明
                    should_transparent = False
                    if mode == "both_in_range" and pixel1_in_range and pixel2_in_range:
                        should_transparent = True
                    elif mode == "either_in_range" and (pixel1_in_range or pixel2_in_range):
                        should_transparent = True
                    elif mode == "img1_in_range" and pixel1_in_range:
                        should_transparent = True
                    elif mode == "img2_in_range" and pixel2_in_range:
                        should_transparent = True
                    
                    if should_transparent:
                        result_array[y, x, 3] = 0
            
        else:
            # 没有容差参数，严格比较
            print("使用严格比较模式（无容差）")
            mask = np.all(img1_array[:, :, :3] == img2_array[:, :, :3], axis=2)
            result_array = img1_array.copy()
            result_array[mask, 3] = 0
        
        # 创建结果图片
        result_img = Image.fromarray(result_array, mode="RGBA")
        
        # 保存结果
        result_img.save(output_path, format="PNG")
        print(f"处理完成！结果已保存到: {output_path}")
        
        return result_img
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return None


# 更高级的版本，支持多个基准色范围
def compare_with_multiple_tolerance_ranges(img1_path, img2_path, output_path="result.png", 
                                          tolerance_ranges=None, match_all_ranges=True):
    """
    比较两张图片，支持多个基准色范围
    
    参数:
    img1_path: str - 第一张图片路径
    img2_path: str - 第二张图片路径
    output_path: str - 输出图片路径
    tolerance_ranges: list - 容差范围列表，每个元素格式: '基准色-色偏'
                        例如: ['C9C0B2-25211F', 'FFFFFF-101010']
    match_all_ranges: bool - True: 需要在所有范围内才透明
                          False: 在任一范围内就透明
    
    返回:
    PIL.Image - 处理后的图片对象
    """
    try:
        # 打开图片
        img1 = Image.open(img1_path).convert("RGBA")
        img2 = Image.open(img2_path).convert("RGBA")
        
        # 调整尺寸
        if img1.size != img2.size:
            img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)
        
        # 转换为数组
        img1_array = np.array(img1)
        img2_array = np.array(img2)
        result_array = img1_array.copy()
        
        height, width = img1_array.shape[:2]
        
        if not tolerance_ranges:
            # 没有范围，严格比较
            mask = np.all(img1_array[:, :, :3] == img2_array[:, :, :3], axis=2)
            result_array[mask, 3] = 0
        else:
            # 解析所有范围
            parsed_ranges = []
            for range_str in tolerance_ranges:
                base_rgb, tolerance_rgb = parse_tolerance(range_str)
                parsed_ranges.append((base_rgb, tolerance_rgb))
                print(f"范围: 基准色RGB{base_rgb}, 色偏±RGB{tolerance_rgb}")
            
            # 处理每个像素
            for y in range(height):
                for x in range(width):
                    pixel1 = img1_array[y, x, :3]
                    pixel2 = img2_array[y, x, :3]
                    
                    # 检查像素在所有范围内的情况
                    in_all_ranges = True
                    in_any_range = False
                    
                    for base_rgb, tolerance_rgb in parsed_ranges:
                        pixel1_in_range = True
                        pixel2_in_range = True
                        
                        for channel in range(3):
                            base_val = base_rgb[channel]
                            tolerance_val = tolerance_rgb[channel]
                            
                            if pixel1[channel] < base_val - tolerance_val or pixel1[channel] > base_val + tolerance_val:
                                pixel1_in_range = False
                            
                            if pixel2[channel] < base_val - tolerance_val or pixel2[channel] > base_val + tolerance_val:
                                pixel2_in_range = False
                        
                        # 两个像素都在当前范围内
                        current_range_ok = pixel1_in_range and pixel2_in_range
                        
                        if not current_range_ok:
                            in_all_ranges = False
                        
                        if current_range_ok:
                            in_any_range = True
                    
                    # 根据匹配模式决定
                    if (match_all_ranges and in_all_ranges) or (not match_all_ranges and in_any_range):
                        result_array[y, x, 3] = 0
        
        # 创建结果图片
        result_img = Image.fromarray(result_array, mode="RGBA")
        result_img.save(output_path, format="PNG")
        print(f"处理完成！结果已保存到: {output_path}")
        
        return result_img
        
    except Exception as e:
        print(f"错误: {e}")
        return None


# 可视化函数，显示哪些像素被设置为透明
def visualize_transparency(img1_path, img2_path, tolerance_str, output_path="visualization.png"):
    """
    可视化显示哪些像素会被设置为透明
    
    参数:
    img1_path: str - 图片1路径
    img2_path: str - 图片2路径
    tolerance_str: str - 容差字符串
    output_path: str - 输出路径
    """
    try:
        # 打开图片
        img1 = Image.open(img1_path).convert("RGBA")
        img2 = Image.open(img2_path).convert("RGBA")
        
        if img1.size != img2.size:
            img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)
        
        img1_array = np.array(img1)
        img2_array = np.array(img2)
        
        # 解析容差
        if tolerance_str:
            base_rgb, tolerance_rgb = parse_tolerance(tolerance_str)
        else:
            base_rgb, tolerance_rgb = (0, 0, 0), (0, 0, 0)
        
        # 创建可视化数组
        visual_array = np.zeros((img1_array.shape[0], img1_array.shape[1], 4), dtype=np.uint8)
        visual_array[:, :, 3] = 255  # 设置完全不透明
        
        height, width = img1_array.shape[:2]
        
        for y in range(height):
            for x in range(width):
                pixel1 = img1_array[y, x, :3]
                pixel2 = img2_array[y, x, :3]
                
                # 检查是否在范围内
                pixel1_in_range = True
                pixel2_in_range = True
                
                for channel in range(3):
                    base_val = base_rgb[channel]
                    tolerance_val = tolerance_rgb[channel]
                    
                    if pixel1[channel] < base_val - tolerance_val or pixel1[channel] > base_val + tolerance_val:
                        pixel1_in_range = False
                    
                    if pixel2[channel] < base_val - tolerance_val or pixel2[channel] > base_val + tolerance_val:
                        pixel2_in_range = False
                
                # 根据情况设置颜色
                if pixel1_in_range and pixel2_in_range:
                    # 两个都在范围内 - 绿色（将被透明）
                    visual_array[y, x] = [0, 255, 0, 255]
                elif pixel1_in_range or pixel2_in_range:
                    # 只有一个在范围内 - 黄色
                    visual_array[y, x] = [255, 255, 0, 255]
                else:
                    # 都不在范围内 - 红色（将保留）
                    visual_array[y, x] = [255, 0, 0, 255]
        
        # 创建可视化图片
        visual_img = Image.fromarray(visual_array, mode="RGBA")
        visual_img.save(output_path, format="PNG")
        print(f"可视化图已保存到: {output_path}")
        
        return visual_img
        
    except Exception as e:
        print(f"错误: {e}")
        return None


# 使用示例
if __name__ == "__main__":
    # 示例1: 使用单个基准色范围
    print("示例1: 使用基准色范围 C9C0B2-25211F")
    result1 = compare_images_with_hex_tolerance(
        img1_path="toumingtu.png",
        img2_path="1111.png",
        output_path="output_single_range.png",
        tolerance_str="C9C0B2-25211F",  # 基准色#C9C0B2，R±32, G±48, B±64
        mode="img2_in_range"
    )
    
    # # 示例2: 使用多个基准色范围
    # print("\n示例2: 使用多个基准色范围")
    # result2 = compare_with_multiple_tolerance_ranges(
    #     img1_path="image1.png",
    #     img2_path="image2.png",
    #     output_path="output_multi_ranges.png",
    #     tolerance_ranges=[
    #         "C9C0B2-25211F",  # 第一个范围
    #         "FFFFFF-101010",  # 第二个范围（接近白色）
    #         "000000-080808"   # 第三个范围（接近黑色）
    #     ],
    #     match_all_ranges=False  # 在任一范围内就透明
    # )
    
    # # 示例3: 创建可视化图
    # print("\n示例3: 创建透明度可视化图")
    # visual = visualize_transparency(
    #     img1_path="image1.png",
    #     img2_path="image2.png",
    #     tolerance_str="C9C0B2-25211F",
    #     output_path="transparency_visualization.png"
    # )
    
    # # 示例4: 不同模式比较
    # print("\n示例4: 使用不同模式比较")
    # modes = ["both_in_range", "either_in_range", "img1_in_range", "img2_in_range"]
    
    # for i, mode in enumerate(modes):
        # result = compare_images_with_hex_tolerance(
        #     img1_path="image1.png",
        #     img2_path="image2.png",
        #     output_path=f"output_mode_{mode}.png",
        #     tolerance_str="C9C0B2-25211F",
        #     mode=mode
        # )
        # print(f"  模式 '{mode}' 处理完成")