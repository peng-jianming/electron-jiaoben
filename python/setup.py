import PyInstaller.__main__
import os
import sys

# 修复 PyQt5 插件路径问题：设置环境变量阻止查找插件
os.environ['QT_PLUGIN_PATH'] = ''
# 阻止 PyInstaller 查找 PyQt5 插件
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''

# PyInstaller 打包参数配置
pyinstaller_args = [
    "common/index.py",  # 入口脚本
    "--name=pyapp",  # 可执行文件名称
    "--distpath=./dist",  # 输出目录
    "--workpath=./build",  # 临时文件目录
    "--specpath=.",  # spec 文件输出目录
    "--clean",  # 清理临时文件
    "--noconfirm",  # 覆盖输出目录而不询问
    # 排除模块
    "--exclude-module=PyQt5",
    "--exclude-module=PyQt5.QtQml",
    "--exclude-module=PyQt5.QtQuick",
    "--exclude-module=PyQt5.QtWebEngine",
    "--exclude-module=PyQt5.QtWebEngineWidgets",
    "--exclude-module=PyQt5.QtWebEngineCore",
    # 优化级别 (0=无优化, 1=移除断言, 2=移除断言和文档字符串)
    "--optimize=2",
    # 不显示控制台窗口（如果需要 GUI 应用，取消注释下面这行）
    # "--noconsole",
    # 单文件模式（如果需要打包成单个 exe 文件，取消注释下面这行）
    # "--onefile",
]

if __name__ == "__main__":
    # 执行 PyInstaller 打包
    PyInstaller.__main__.run(pyinstaller_args)
