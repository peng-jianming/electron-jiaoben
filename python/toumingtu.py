# 透明图制作, 对比源图片和结果图片, 如果结果图片的像素点和源图片的像素点不同,则设置为透明,已经设为透明的像素点,则不处理,保持透明
# IMAGE_DIR 需要处理的源图片文件夹
# resultPath 处理后的图片, 如果文件不存在,则创建文件,如果存在,就作为上次的结果继续处理
# CROP_CONFIG 源图片裁剪配置,
# color_tolerance 颜色容差参数, 可以是单个字符串或字符串数组
#   格式: 'C9C0B2-203040', 其中C9C0B2为基准色(16进制RGB), 203040表示RGB的色偏分别是20 30 40(16进制)
#   支持多个颜色容差: ['C9C0B2-203040', 'FFFFFF-101010']
#   只要像素在任何一个颜色容差范围内就保留,其他的都设置为透明

import os
import time
import glob
from PIL import Image

# 配置路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 源图片文件夹路径（存放所有需要处理的截图）
IMAGE_DIR = os.path.join(BASE_DIR, './cache')
RESULT_PATH = os.path.join(BASE_DIR, './cache/toumingtu.png')

# 支持的图片扩展名
IMAGE_EXTENSIONS = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif']

# 源图片裁剪配置
CROP_CONFIG = {
    'enabled': False,  # 是否启用裁剪,让配置生效
    'x': 118,  # 裁剪的x坐标
    'y': 1028,  # 裁剪的y坐标
    'w': 94,  # 裁剪的宽度
    'h': 31  # 裁剪的高度
}

base_image = None
is_processing = False
# 记录每个文件的最后修改时间
file_mtimes = {}


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
    返回: True表示在范围内(保留), False表示不在范围内(设置为透明)
    """
    r_diff = abs(r - base_r)
    g_diff = abs(g - base_g)
    b_diff = abs(b - base_b)
    
    return r_diff <= tolerance_r and g_diff <= tolerance_g and b_diff <= tolerance_b


def get_image_files():
    """获取文件夹内所有图片文件"""
    image_files = []
    for ext in IMAGE_EXTENSIONS:
        pattern = os.path.join(IMAGE_DIR, ext)
        image_files.extend(glob.glob(pattern))
    
    # 排除结果文件本身
    result_path_normalized = os.path.normpath(RESULT_PATH)
    image_files = [f for f in image_files if os.path.normpath(f) != result_path_normalized]
    
    return image_files


def process_single_image(image_path, color_tolerance=None):
    """
    处理单张图片
    color_tolerance: 颜色容差参数, 可以是:
        - None: 使用旧的对比逻辑
        - 字符串: 'C9C0B2-203040' (单个颜色容差)
        - 列表: ['C9C0B2-203040', 'FFFFFF-101010'] (多个颜色容差,只要像素在任何一个范围内就保留)
    """
    global base_image, file_mtimes
    
    # 解析颜色容差参数
    color_tolerance_params_list = None
    if color_tolerance:
        # 如果是字符串，转换为列表
        if isinstance(color_tolerance, str):
            color_tolerance_list = [color_tolerance]
        elif isinstance(color_tolerance, list):
            color_tolerance_list = color_tolerance
        else:
            print(f'颜色容差参数类型错误: {type(color_tolerance)}, 将使用对比模式')
            color_tolerance_params_list = None
            color_tolerance_list = []
        
        if color_tolerance_list:
            color_tolerance_params_list = []
            for ct in color_tolerance_list:
                params = parse_color_tolerance(ct)
                if params is None:
                    print(f'颜色容差参数格式错误: {ct}, 跳过该参数')
                else:
                    color_tolerance_params_list.append(params)
            
            if not color_tolerance_params_list:
                print('所有颜色容差参数格式错误, 将使用对比模式')
                color_tolerance_params_list = None

    try:
        # 检查文件修改时间，避免重复处理同一张图片
        stats = os.stat(image_path)
        current_mtime = stats.st_mtime

        if image_path in file_mtimes and current_mtime == file_mtimes[image_path]:
            # 文件未更新，跳过
            return False

        # 读取当前图片
        try:
            current_image = Image.open(image_path).convert("RGBA")
        except IOError:
            # 可能文件正在写入中，读取失败
            return False

        # 如果启用了裁剪，先对图片进行裁剪
        if CROP_CONFIG['enabled']:
            # box = (left, upper, right, lower)
            box = (
                CROP_CONFIG['x'],
                CROP_CONFIG['y'],
                CROP_CONFIG['x'] + CROP_CONFIG['w'],
                CROP_CONFIG['y'] + CROP_CONFIG['h']
            )
            current_image = current_image.crop(box)

        file_mtimes[image_path] = current_mtime

        if base_image is None:
            if os.path.exists(RESULT_PATH):
                print('发现 toumingtu.png，将其作为基准图片')
                try:
                    base_image = Image.open(RESULT_PATH).convert("RGBA")
                except IOError:
                    # 如果读取失败，可能文件损坏，重新开始
                    base_image = current_image
                    print('读取基准图片失败，已使用当前图片重新初始化')
                    base_image.save(RESULT_PATH)
                    return True
            else:
                # 第一张图片，作为基准
                base_image = current_image
                print(f'已使用 {os.path.basename(image_path)} 初始化基准图片')
                base_image.save(RESULT_PATH)
                return True

        # 确保尺寸一致
        if base_image.size != current_image.size:
            print(f'图片 {os.path.basename(image_path)} 尺寸不一致，跳过')
            return False

        width, height = base_image.size
        # 获取像素数据以便读写
        base_pixels = base_image.load()
        current_pixels = current_image.load()

        diff_count = 0

        # 如果使用颜色容差模式
        if color_tolerance_params_list:
            # 遍历所有像素进行颜色容差检查
            for x in range(width):
                for y in range(height):
                    # 获取基准图片像素 (r, g, b, a)
                    r1, g1, b1, a1 = base_pixels[x, y]

                    # 如果基准图片这个点已经是透明的，就不用处理了
                    if a1 == 0:
                        continue

                    # 获取当前图片像素
                    r2, g2, b2, a2 = current_pixels[x, y]

                    # 检查当前图片的像素是否在任何一个颜色容差范围内
                    in_range = False
                    for base_r, base_g, base_b, tolerance_r, tolerance_g, tolerance_b in color_tolerance_params_list:
                        if is_color_in_range(r2, g2, b2, base_r, base_g, base_b, tolerance_r, tolerance_g, tolerance_b):
                            in_range = True
                            break
                    
                    # 如果不在任何一个范围内，设置为透明
                    if not in_range:
                        base_pixels[x, y] = (0, 0, 0, 0)
                        diff_count += 1
        else:
            # 使用旧的对比模式（兼容旧代码）
            # 遍历所有像素进行对比
            for x in range(width):
                for y in range(height):
                    # 获取基准图片像素 (r, g, b, a)
                    r1, g1, b1, a1 = base_pixels[x, y]

                    # 如果基准图片这个点已经是透明的，就不用比了
                    if a1 == 0:
                        continue

                    # 获取当前图片像素
                    r2, g2, b2, a2 = current_pixels[x, y]

                    # 对比两个像素是否相同（使用简单的差值判断）
                    r_diff = abs(r1 - r2)
                    g_diff = abs(g1 - g2)
                    b_diff = abs(b1 - b2)
                    a_diff = abs(a1 - a2)

                    if r_diff > 0 or g_diff > 0 or b_diff > 0 or a_diff > 0:
                        # 不一样，设置为透明
                        base_pixels[x, y] = (0, 0, 0, 0)
                        diff_count += 1

        if diff_count > 0:
            print(f'[{os.path.basename(image_path)}] 发现 {diff_count} 个不同像素')
            return True
        
        return False

    except Exception as err:
        print(f'处理 {os.path.basename(image_path)} 出错: {err}')
        return False


def process_all_images(color_tolerance=None):
    """
    处理文件夹内所有图片
    color_tolerance: 颜色容差参数, 可以是:
        - None: 使用旧的对比逻辑
        - 字符串: 'C9C0B2-203040' (单个颜色容差)
        - 列表: ['C9C0B2-203040', 'FFFFFF-101010'] (多个颜色容差,只要像素在任何一个范围内就保留)
    """
    global base_image, is_processing

    if is_processing:
        return
    is_processing = True

    try:
        # 检查文件夹是否存在
        if not os.path.exists(IMAGE_DIR):
            print(f'等待图片文件夹 {IMAGE_DIR}...')
            return

        # 获取所有图片文件
        image_files = get_image_files()
        
        if not image_files:
            print('文件夹内没有图片文件')
            return

        updated = False
        for image_path in image_files:
            if process_single_image(image_path, color_tolerance):
                updated = True

        # 如果有更新，保存结果
        if updated and base_image is not None:
            base_image.save(RESULT_PATH)
            print(f'已更新结果图片，共处理 {len(image_files)} 张图片')

    except Exception as err:
        print(f'处理出错: {err}')
    finally:
        is_processing = False


if __name__ == "__main__":
    # 每秒执行一次
    print(f'开始监控文件夹 {IMAGE_DIR} 的图片变化...')
    # 设置颜色容差参数, 支持单个或多个颜色容差
    # 格式: '基准色-色偏', 例如: 'C9C0B2-203040'
    # C9C0B2为基准色(16进制RGB), 203040表示RGB的色偏分别是20 30 40(16进制)
    # 只有在这个颜色范围内的像素保留,其他的都设置为透明
    # 可以设置为单个字符串或字符串数组,如果像素在任何一个颜色容差范围内就保留
    color_tolerance_val = ['CC8367-214340']  # 修改为你需要的颜色容差参数,支持多个: ['C9C0B2-25211F', 'FFFFFF-101010']

    try:
        while True:
            # controller = DeviceController('9a8de478')
            # controller.截图()
            process_all_images(color_tolerance_val)
            time.sleep(1)
    except KeyboardInterrupt:
        print('程序已停止')




#  让物体保持不变,其他保持变化, 可以清除变动的部分(清除物体不稳定因素和无关因素)
#  让物体消失,其他保持不变,  使用去除不变,  可以将除了目标外的部分清除(清除物体无关因素)