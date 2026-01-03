from PIL import Image
import os


def hex_to_rgb(hex_color):
    """
    将16进制颜色转换为RGB元组

    参数:
        hex_color: 16进制颜色，如 "#FF0000" 或 "FF0000"

    返回:
        RGB元组，如 (255, 0, 0)
    """
    # 移除 # 前缀（如果有）
    hex_color = hex_color.lstrip('#')

    # 解析RGB值
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return (r, g, b)


def filter_by_color(image_path, target_color, tolerance, output_path=None):
    """
    根据颜色和容差处理图片，保留在容差范围内的像素，其余设置为透明

    参数:
        image_path: 图片路径
        target_color: 目标颜色，支持16进制格式如 "#FF0000" 或 "FF0000"，也支持RGB元组如 (255, 0, 0)
        tolerance: 容差值 (0-255)，每个通道允许的最大差异
        output_path: 输出路径，如果不指定则在原文件名后加 _filtered

    返回:
        处理后的图片路径
    """
    # 打开图片并转换为 RGBA 模式
    img = Image.open(image_path)
    img = img.convert("RGBA")

    # 获取像素数据
    pixels = img.load()
    width, height = img.size

    # 解析目标颜色（支持16进制和RGB元组）
    if isinstance(target_color, str):
        target_r, target_g, target_b = hex_to_rgb(target_color)
    else:
        target_r, target_g, target_b = target_color

    # 遍历每个像素
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]

            # 计算与目标颜色的差异
            r_diff = abs(r - target_r)
            g_diff = abs(g - target_g)
            b_diff = abs(b - target_b)

            # 判断是否在容差范围内
            if r_diff <= tolerance and g_diff <= tolerance and b_diff <= tolerance:
                # 在容差范围内，保留像素（保持原透明度）
                pass
            else:
                # 不在容差范围内，设置为透明
                pixels[x, y] = (r, g, b, 0)

    # 生成输出路径
    if output_path is None:
        name, ext = os.path.splitext(image_path)
        output_path = f"{name}_filtered.png"

    # 保存图片（必须使用PNG格式以保留透明通道）
    img.save(output_path, "PNG")
    print(f"处理完成，已保存到: {output_path}")

    return output_path


def filter_by_color_range(image_path, color_min, color_max, output_path=None):
    """
    根据颜色范围处理图片，保留在范围内的像素，其余设置为透明

    参数:
        image_path: 图片路径
        color_min: 颜色范围最小值，支持16进制格式如 "#C80000" 或 RGB元组如 (200, 0, 0)
        color_max: 颜色范围最大值，支持16进制格式如 "#FF3232" 或 RGB元组如 (255, 50, 50)
        output_path: 输出路径，如果不指定则在原文件名后加 _filtered

    返回:
        处理后的图片路径
    """
    # 打开图片并转换为 RGBA 模式
    img = Image.open(image_path)
    img = img.convert("RGBA")

    # 获取像素数据
    pixels = img.load()
    width, height = img.size

    # 解析颜色范围（支持16进制和RGB元组）
    if isinstance(color_min, str):
        min_r, min_g, min_b = hex_to_rgb(color_min)
    else:
        min_r, min_g, min_b = color_min

    if isinstance(color_max, str):
        max_r, max_g, max_b = hex_to_rgb(color_max)
    else:
        max_r, max_g, max_b = color_max

    # 遍历每个像素
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]

            # 判断是否在颜色范围内
            if (min_r <= r <= max_r and
                min_g <= g <= max_g and
                min_b <= b <= max_b):
                # 在范围内，保留像素
                pass
            else:
                # 不在范围内，设置为透明
                pixels[x, y] = (r, g, b, 0)

    # 生成输出路径
    if output_path is None:
        name, ext = os.path.splitext(image_path)
        output_path = f"{name}_filtered.png"

    # 保存图片
    img.save(output_path, "PNG")
    print(f"处理完成，已保存到: {output_path}")

    return output_path


if __name__ == "__main__":
    # 示例用法

    # 方法1: 使用16进制颜色和容差
    # 例如：保留红色 #FF0000 附近的颜色，容差为50
    # filter_by_color("input.png", "#FF0000", 50)

    # 方法2: 使用颜色范围（16进制）
    # 例如：保留红色系颜色
    # filter_by_color_range("input.png", "#C80000", "#FF3232")

    # 也支持 RGB 元组格式
    # filter_by_color("input.png", (255, 0, 0), 50)

    # 测试代码 - 取消下面的注释来测试
    # image_path = "your_image.png"
    # target_color = "#FF0000"  # 红色
    # tolerance = 50
    # filter_by_color(image_path, target_color, tolerance)
    filter_by_color("111111111.bmp", "#e4d8c8", 12)
