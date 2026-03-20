"""
全局设置
"""
import os

# 项目根目录（与 main.py 同目录）
项目根目录 = os.path.dirname(os.path.abspath(__file__))

# 资源目录
资源目录 = os.path.join(项目根目录, "资源")

# 缓存图片目录
缓存图片目录 = os.path.join(资源目录, "缓存图片")

# 洪水填充专用缓存图片目录（与图像处理缓存隔离）
洪水填充缓存图片目录 = os.path.join(资源目录, "洪水填充缓存图片")

# 寻路处理专用缓存图片目录（与图像处理缓存隔离）
寻路缓存图片目录 = os.path.join(资源目录, "寻路缓存图片")

# 路线规划专用缓存图片目录（与寻路测试缓存隔离）
路线规划缓存图片目录 = os.path.join(资源目录, "路线规划缓存图片")

# 寻路测试专用缓存图片目录（与路线规划缓存隔离）
寻路测试缓存图片目录 = os.path.join(资源目录, "寻路测试缓存图片")

# 图像处理参数配置路径
图像处理参数配置路径 = os.path.join(资源目录, "图像处理参数配置.json")




# ADB 路径（优先使用项目内置 ADB）
# 默认内置目录：<项目根目录>/adb/adb.exe
内置ADB路径 = os.path.join(项目根目录, "adb", "adb.exe")
默认系统ADB路径 = r"C:\platform-tools\adb.exe"

# 允许通过环境变量 ADB_PATH 覆盖
环境ADB路径 = os.environ.get("ADB_PATH")

if 环境ADB路径 and os.path.exists(环境ADB路径):
    ADB路径 = 环境ADB路径
elif os.path.exists(内置ADB路径):
    ADB路径 = 内置ADB路径
elif os.path.exists(默认系统ADB路径):
    ADB路径 = 默认系统ADB路径
else:
    # 最后退回到系统 PATH 中的 adb 命令名
    ADB路径 = "adb"

# Socket.IO 服务器地址
服务器地址 = "http://127.0.0.1:7075"

