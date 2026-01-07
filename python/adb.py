"""
ADB 工具类 - 直接使用 ADB 命令实现截图和点击功能
"""
import subprocess
import os
import time
import random


class ADBController:
    """ADB 控制器类，封装截图和点击功能"""
    
    def __init__(self, device_id=None):
        """
        初始化 ADB 控制器
        
        参数:
            device_id: 设备ID，如果有多个设备连接时需要指定
                      可以通过 adb devices 命令查看设备ID
        """
        self.device_id = device_id
        self._adb_prefix = self._build_adb_prefix()
    
    def _build_adb_prefix(self):
        """构建 ADB 命令前缀"""
        adb_path = r"C:\platform-tools\adb.exe"
        if self.device_id:
            return f'"{adb_path}" -s {self.device_id}'
        return f'"{adb_path}"'
    
    def _run_command(self, command, shell=True):
        """
        执行命令并返回结果
        
        参数:
            command: 要执行的命令
            shell: 是否使用 shell 执行
            
        返回:
            (success, output) - 成功标志和输出内容
        """
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "命令执行超时"
        except Exception as e:
            return False, str(e)
    @staticmethod
    def get_devices(self):
        """
        获取所有已连接的设备列表
        
        返回:
            设备ID列表
        """
        adb_path = r"C:\platform-tools\adb.exe"
        success, output = self._run_command(f'"{adb_path}" devices')
        if not success:
            return []
        
        devices = []
        lines = output.strip().split('\n')
        for line in lines[1:]:  # 跳过第一行 "List of devices attached"
            if '\t' in line:
                device_id = line.split('\t')[0]
                devices.append(device_id)
        return devices
    
    def 截图到内存(self):
        """
        截图并直接返回图像数据（不保存到文件）
        
        返回:
            PNG 图像的字节数据，失败返回 None
        """
        try:
            result = subprocess.run(
                f"{self._adb_prefix} exec-out screencap -p",
                shell=True,
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout
            return None
        except Exception as e:
            print(f"截图失败: {e}")
            return None
    


# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 创建 ADB 控制器
    # 如果只有一个设备，不需要指定 device_id
    adb = ADBController()
    
    # 如果有多个设备，需要指定设备ID
    # adb = ADBController(device_id="127.0.0.1:5555")
    
    # 查看已连接的设备
    print("已连接设备:", ADBController.get_devices())
    
    # 检查设备连接
    if adb.check_connection():
        print("设备已连接")
        
        # 获取屏幕分辨率
        resolution = adb.获取屏幕分辨率()
        print(f"屏幕分辨率: {resolution}")
        
        # 截图
        screenshot_path = adb.截图到内存()
        if screenshot_path:
            print(f"截图已保存到: {screenshot_path}")
        
        # 点击屏幕中心
        if resolution:
            center_x = resolution[0] // 2
            center_y = resolution[1] // 2
            print(f"点击屏幕中心: ({center_x}, {center_y})")
            adb.点击(center_x, center_y)
        
        # 随机延时
        adb.随机延时(0.5, 1.0)
        
        # 在区域内随机点击
        adb.随机点击(100, 200, 50, 50)
        
        # 滑动
        # adb.滑动(500, 1000, 500, 500, 300)
        
        # 返回
        # adb.返回()
    else:
        print("设备未连接，请检查 ADB 连接")