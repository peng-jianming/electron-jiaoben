"""
全局设置
"""
import os

# 项目根目录
项目根目录 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 资源目录
资源目录 = os.path.join(项目根目录, "resource")

# 缓存目录
缓存目录 = os.path.join(资源目录, "cache")

# 未知界面截图目录
未知截图目录 = os.path.join(资源目录, "unknown")

# 字库文件路径
字库文件路径 = os.path.join(资源目录, "font_library.txt")

# YOLO 模型路径
模型文件路径 = os.path.join(资源目录, "best.pt")

# 提示音乐路径
音乐文件路径 = os.path.join(资源目录, "music.mp3")

# ADB 路径
ADB路径 = r"C:\platform-tools\adb.exe"

# Socket.IO 服务器地址
服务器地址 = "http://127.0.0.1:7072"

# 未知界面超时时间（秒）
未知界面超时时间 = 60

# 确保目录存在
os.makedirs(缓存目录, exist_ok=True)
os.makedirs(未知截图目录, exist_ok=True)
