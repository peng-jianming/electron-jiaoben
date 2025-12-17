# 透明图制作, 对比源图片和结果图片, 如果结果图片的像素点和源图片的像素点不同,则设置为透明,已经设为透明的像素点,则不处理,保持透明
# IMAGE_DIR 需要处理的源图片文件夹
# resultPath 处理后的图片, 如果文件不存在,则创建文件,如果存在,就作为上次的结果继续处理
# CROP_CONFIG 源图片裁剪配置,
# tolerance 处理时的容差值

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


def process_single_image(image_path, tolerance=0):
    """处理单张图片"""
    global base_image, file_mtimes

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

                # 对比两个像素是否相同
                r_diff = abs(r1 - r2)
                g_diff = abs(g1 - g2)
                b_diff = abs(b1 - b2)
                a_diff = abs(a1 - a2)

                if r_diff > tolerance or g_diff > tolerance or b_diff > tolerance or a_diff > tolerance:
                    # 不一样，设置为透明
                    # Pillow中设置透明可以直接设 alpha=0, 也可以全0
                    base_pixels[x, y] = (0, 0, 0, 0)
                    diff_count += 1

        if diff_count > 0:
            print(f'[{os.path.basename(image_path)}] 发现 {diff_count} 个不同像素')
            return True
        
        return False

    except Exception as err:
        print(f'处理 {os.path.basename(image_path)} 出错: {err}')
        return False


def process_all_images(tolerance=0):
    """处理文件夹内所有图片"""
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
            if process_single_image(image_path, tolerance):
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
    tolerance_val = 25  # 设置容差值

    try:
        while True:
            process_all_images(tolerance_val)
            time.sleep(1)
    except KeyboardInterrupt:
        print('程序已停止')

