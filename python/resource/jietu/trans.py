"""
将当前文件夹中的所有 PNG 图片转换为 BMP 格式
"""
import os
from PIL import Image


def convert_png_to_bmp():
    """将当前文件夹中的所有 PNG 图片转换为 BMP 格式"""
    # 获取当前脚本所在文件夹
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 获取所有 PNG 文件
    png_files = [f for f in os.listdir(current_dir) 
                 if f.lower().endswith('.png')]
    
    if not png_files:
        print(f"在文件夹 {current_dir} 中未找到 PNG 文件")
        return
    
    print(f"找到 {len(png_files)} 个 PNG 文件，开始转换...")
    
    success_count = 0
    error_count = 0
    
    for png_file in png_files:
        try:
            # 构建完整路径
            png_path = os.path.join(current_dir, png_file)
            
            # 生成 BMP 文件名（替换扩展名）
            bmp_file = os.path.splitext(png_file)[0] + '.bmp'
            bmp_path = os.path.join(current_dir, bmp_file)
            
            # 打开 PNG 图片并转换为 BMP
            with Image.open(png_path) as img:
                # 如果图片有透明通道，转换为 RGB 模式（BMP 不支持透明）
                if img.mode in ('RGBA', 'LA', 'P'):
                    # 创建白色背景
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 保存为 BMP
                img.save(bmp_path, 'BMP')
                print(f"✓ 转换成功: {png_file} -> {bmp_file}")
                success_count += 1
                
        except Exception as e:
            print(f"✗ 转换失败: {png_file} - {str(e)}")
            error_count += 1
    
    print(f"\n转换完成！成功: {success_count} 个，失败: {error_count} 个")


if __name__ == "__main__":
    convert_png_to_bmp()

