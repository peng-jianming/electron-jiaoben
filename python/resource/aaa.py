import cv2
import time
import os
from datetime import datetime
from index import 截图
# 图片路径
image_path = os.path.join(os.path.dirname(__file__), "cache", "9a8de478.png")
output_dir = os.path.dirname(__file__)

# 创建输出目录
grayscale_dir = os.path.join(output_dir, "grayscale")
binary_dir = os.path.join(output_dir, "binary")
os.makedirs(grayscale_dir, exist_ok=True)
os.makedirs(binary_dir, exist_ok=True)



print(f"开始处理图片，每秒生成灰度和二值化图片...")
print(f"灰度图保存到: {grayscale_dir}")
print(f"二值图保存到: {binary_dir}")
print("按 Ctrl+C 停止")

counter = 0
try:
    while True:
# 读取原图

        截图()
        original_image = cv2.imread(image_path)
        if original_image is None:
            print(f"无法读取图片: {image_path}")
            exit(1)

        # 二值化处理 - 让前景更清晰
        # 1. 高斯模糊去噪
        blurred = cv2.GaussianBlur(original_image, (5, 5), 0)
        # 灰度化
        grayscale_image = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
        grayscale_filename = os.path.join(grayscale_dir, f"gray.png")
        cv2.imwrite(grayscale_filename, grayscale_image)
        



        # 二值化 (使用 OTSU 自动阈值)
        _, binary_image = cv2.threshold(grayscale_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binary_filename = os.path.join(binary_dir, f"binary.png")
        cv2.imwrite(binary_filename, binary_image)
        
        # 等待1秒
        time.sleep(1)
        
except KeyboardInterrupt:
    print(f"\n已停止，共处理 {counter} 次")

