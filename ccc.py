import numpy as np
import cv2
import os

# 读取两张图片（示例）
script_dir = os.path.dirname(os.path.abspath(__file__))
img1_path = os.path.join(script_dir, '120x120.jpg')
# img2_path = os.path.join(os.path.dirname(__file__), '测试资源/800x800.png')

img1 = cv2.imread(img1_path)
# cv2.imshow('img1', img1)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
# 保存到 .npz 文件，指定名称
np.savez('my_templates.npz', 
         logo=img1)          # 键名为 'icon'

# 如果希望压缩以节省空间（无损压缩）
# np.savez_compressed('my_templates.npz', logo=img1, icon=img2)

print("文件已保存！")