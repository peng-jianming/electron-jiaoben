# 轮廓检测透明图制作
# 使用轮廓检测算法处理图片，对比轮廓不同的设置为透明，相同的保留
# IMAGE_DIR 需要处理的源图片文件夹
# resultPath 处理后的图片, 如果文件不存在则创建,如果存在就作为上次的结果继续处理
# CROP_CONFIG 源图片裁剪配置

import os
import time
import glob
import cv2
import numpy as np
from PIL import Image
from index import 截图

# 配置路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 源图片文件夹路径（存放所有需要处理的截图）
IMAGE_DIR = os.path.join(BASE_DIR, './cache')
RESULT_PATH = os.path.join(BASE_DIR, './cache/bianyun.png')

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

# 轮廓检测参数
CONTOUR_CONFIG = {
    'blur_kernel': 5,        # 高斯模糊核大小（必须是奇数）
    'threshold': 127,        # 二值化阈值
    'thickness': 1,          # 轮廓线条粗细 (1=细线, -1=填充)
    'mode': cv2.RETR_TREE,   # 轮廓检索模式
    'method': cv2.CHAIN_APPROX_SIMPLE  # 轮廓近似方法
}

base_image = None
base_contours = None  # 基准图片的轮廓检测结果（二值图）
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


def detect_contours(image):
    """
    对图片进行轮廓检测
    参数:
        image: PIL Image对象 (RGBA模式)
    返回:
        轮廓检测结果 (numpy array, 二值图，255=轮廓，0=非轮廓)
    """
    # 将PIL Image转换为numpy array
    img_array = np.array(image)
    
    # 转换为BGR格式（OpenCV使用BGR）
    if img_array.shape[2] == 4:
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
    else:
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # 转换为灰度图
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # 高斯模糊去噪
    blurred = cv2.GaussianBlur(gray, (CONTOUR_CONFIG['blur_kernel'], CONTOUR_CONFIG['blur_kernel']), 0)
    
    # 二值化
    _, binary = cv2.threshold(blurred, CONTOUR_CONFIG['threshold'], 255, cv2.THRESH_BINARY)
    
    # 查找轮廓
    contours, _ = cv2.findContours(binary, CONTOUR_CONFIG['mode'], CONTOUR_CONFIG['method'])
    
    # 创建空白图像，绘制轮廓
    contour_image = np.zeros_like(gray)
    cv2.drawContours(contour_image, contours, -1, 255, CONTOUR_CONFIG['thickness'])
    
    return contour_image


def apply_contour_mask(image, contours):
    """
    对图片应用轮廓遮罩：二值化处理
    - 轮廓部分设为白色（255, 255, 255, 255）
    - 非轮廓部分设为透明（0, 0, 0, 0）
    参数:
        image: PIL Image对象 (RGBA模式)，会被直接修改
        contours: 轮廓检测结果 (numpy array, 二值图，255=轮廓，0=非轮廓)
    """
    width, height = image.size
    pixels = image.load()
    
    contour_count = 0
    transparent_count = 0
    
    for x in range(width):
        for y in range(height):
            # contours 是 (height, width) 格式
            contour_val = contours[y, x]
            
            if contour_val > 0:
                # 是轮廓，设为白色
                pixels[x, y] = (255, 255, 255, 255)
                contour_count += 1
            else:
                # 非轮廓，设为透明
                pixels[x, y] = (0, 0, 0, 0)
                transparent_count += 1
    
    print(f'轮廓处理完成：{contour_count} 个轮廓像素（白色），{transparent_count} 个非轮廓像素（透明）')


def process_single_image(image_path):
    """处理单张图片"""
    global base_image, base_contours, file_mtimes

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
            box = (
                CROP_CONFIG['x'],
                CROP_CONFIG['y'],
                CROP_CONFIG['x'] + CROP_CONFIG['w'],
                CROP_CONFIG['y'] + CROP_CONFIG['h']
            )
            current_image = current_image.crop(box)

        file_mtimes[image_path] = current_mtime

        # 对当前图片进行轮廓检测
        current_contours = detect_contours(current_image)

        if base_image is None:
            if os.path.exists(RESULT_PATH):
                print('发现 bianyun.png，将其作为基准图片')
                try:
                    base_image = Image.open(RESULT_PATH).convert("RGBA")
                    base_contours = detect_contours(base_image)
                except IOError:
                    # 如果读取失败，可能文件损坏，重新开始
                    base_image = current_image.copy()
                    base_contours = current_contours.copy()
                    # 对第一张图片进行轮廓处理
                    apply_contour_mask(base_image, base_contours)
                    print('读取基准图片失败，已使用当前图片重新初始化（已应用轮廓处理）')
                    base_image.save(RESULT_PATH)
                    return True
            else:
                # 第一张图片，作为基准，同时进行轮廓处理
                base_image = current_image.copy()
                base_contours = current_contours.copy()
                # 对第一张图片进行轮廓处理：非轮廓部分设为透明
                apply_contour_mask(base_image, base_contours)
                print(f'已使用 {os.path.basename(image_path)} 初始化基准图片（已应用轮廓处理）')
                base_image.save(RESULT_PATH)
                return True

        # 确保尺寸一致
        if base_image.size != current_image.size:
            print(f'图片 {os.path.basename(image_path)} 尺寸不一致，跳过')
            return False

        width, height = base_image.size
        # 获取像素数据以便读写
        base_pixels = base_image.load()

        diff_count = 0
        keep_count = 0

        # 遍历所有像素，比较轮廓检测结果
        for x in range(width):
            for y in range(height):
                # 获取基准图片像素的alpha值
                r1, g1, b1, a1 = base_pixels[x, y]

                # 如果基准图片这个点已经是透明的，就不用比了
                if a1 == 0:
                    continue

                # 获取轮廓检测结果（0表示非轮廓，255表示轮廓）
                base_contour_val = base_contours[y, x]
                current_contour_val = current_contours[y, x]

                # 比较轮廓是否相同
                # 基准是轮廓(255)，当前也是轮廓(255) -> 相同，保留
                # 基准是轮廓(255)，当前不是轮廓(0) -> 不同，设为透明
                if base_contour_val == current_contour_val:
                    # 相同，保留（不做任何操作）
                    keep_count += 1
                else:
                    # 不同，设置为透明
                    base_pixels[x, y] = (0, 0, 0, 0)
                    # 同时更新 base_contours，标记该位置已被移除
                    base_contours[y, x] = 0
                    diff_count += 1

        if diff_count > 0:
            print(f'[{os.path.basename(image_path)}] 保留 {keep_count} 个相同像素，移除 {diff_count} 个不同像素')
            return True
        
        return False

    except Exception as err:
        print(f'处理 {os.path.basename(image_path)} 出错: {err}')
        import traceback
        traceback.print_exc()
        return False


def process_all_images():
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
            if process_single_image(image_path):
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
    print(f'轮廓检测参数: 模糊核={CONTOUR_CONFIG["blur_kernel"]}, 阈值={CONTOUR_CONFIG["threshold"]}, 线条粗细={CONTOUR_CONFIG["thickness"]}')

    try:
        while True:
            # 截图()
            process_all_images()
            time.sleep(1)
    except KeyboardInterrupt:
        print('程序已停止')
