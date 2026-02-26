import cv2
import os
import numpy as np

def load_binary_map(img_path, threshold=127, white_is_boundary=True):
    """
    读取图像并转换为二值矩阵。
    white_is_boundary=True 表示白色为边界，黑色为可通行区域。
    转换后：边界点=1，可通行点=0。
    """
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"无法读取图像: {img_path}")

    if white_is_boundary:
        # 白色 > threshold 变为1，黑色变为0
        _, binary = cv2.threshold(img, threshold, 1, cv2.THRESH_BINARY)
    else:
        # 如果白色是可通行区域，则反转
        _, binary = cv2.threshold(img, threshold, 1, cv2.THRESH_BINARY_INV)

    return binary.astype(np.uint8)

def find_offset_by_correlation(img1, img2, max_dx=None, max_dy=None):
    """
    使用归一化互相关找到 img2 相对于 img1 的最佳平移偏移 (dx, dy)。
    返回 (dx, dy, confidence)
    """
    h1, w1 = img1.shape
    h2, w2 = img2.shape

    if max_dx is None:
        max_dx = max(w1, w2) // 2
    if max_dy is None:
        max_dy = max(h1, h2) // 2

    # 创建画布，将 img1 放在中央
    canvas_h = h1 + 2 * max_dy
    canvas_w = w1 + 2 * max_dx
    canvas = np.zeros((canvas_h, canvas_w), dtype=np.float32)
    canvas[max_dy:max_dy + h1, max_dx:max_dx + w1] = img1.astype(np.float32)

    # 模板匹配（归一化互相关）
    result = cv2.matchTemplate(canvas, img2.astype(np.float32), cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    best_x, best_y = max_loc

    dx = best_x - max_dx
    dy = best_y - max_dy
    return dx, dy, max_val

def stitch_maps(img1, img2, dx, dy):
    """根据偏移拼接两张二值图，返回拼接后的0/1矩阵"""
    h1, w1 = img1.shape
    h2, w2 = img2.shape

    x_min = min(0, dx)
    y_min = min(0, dy)
    x_max = max(w1, w2 + dx)
    y_max = max(h1, h2 + dy)

    canvas_w = x_max - x_min
    canvas_h = y_max - y_min
    canvas = np.zeros((canvas_h, canvas_w), dtype=np.uint8)

    x1 = -x_min
    y1 = -y_min
    canvas[y1:y1+h1, x1:x1+w1] = img1

    x2 = -x_min + dx
    y2 = -y_min + dy
    canvas[y2:y2+h2, x2:x2+w2] = img2

    return canvas

def save_binary_as_image(binary_mat, output_path):
    """将0/1矩阵保存为黑白图像：1->白色，0->黑色"""
    vis = (binary_mat * 255).astype(np.uint8)
    cv2.imwrite(output_path, vis)
    print(f"已保存: {output_path}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    img1_path = os.path.join(script_dir, '3.png')
    img2_path = os.path.join(script_dir, '4.png')
    output_path = "big_map.png"
    overlay_path = "overlay_check.png"
    # 搜索范围（像素），如果图片很大，可以适当增大
    MAX_DX = 300   # 水平方向最大搜索偏移
    MAX_DY = 200   # 垂直方向最大搜索偏移
    # 是否假设白色为边界？如果图片中边界是白色，保持True
    WHITE_IS_BOUNDARY = True
    # ==============================

    # 1. 加载二值图
    print("加载图像...")
    b1 = load_binary_map(img1_path, white_is_boundary=WHITE_IS_BOUNDARY)
    b2 = load_binary_map(img2_path, white_is_boundary=WHITE_IS_BOUNDARY)
    print(f"图像1: {b1.shape}, 边界点数: {np.sum(b1)}")
    print(f"图像2: {b2.shape}, 边界点数: {np.sum(b2)}")

    # 2. 自动匹配
    print("\n正在进行自动匹配...")
    dx, dy, conf = find_offset_by_correlation(b1, b2, MAX_DX, MAX_DY)
    print(f"自动计算偏移: dx={dx}, dy={dy}, 置信度={conf:.4f}")

    # 4. 拼接并保存
    result = stitch_maps(b1, b2, dx, dy)
    print(f"拼接后尺寸: {result.shape}")
    save_binary_as_image(result, output_path)
    print("完成！")