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
        if self.device_id:
            return f"adb -s {self.device_id}"
        return "adb"
    
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
    
    def check_connection(self):
        """
        检查设备连接状态
        
        返回:
            True 如果设备已连接，False 否则
        """
        success, output = self._run_command(f"{self._adb_prefix} get-state")
        return success and "device" in output
    
    def get_devices(self):
        """
        获取所有已连接的设备列表
        
        返回:
            设备ID列表
        """
        success, output = self._run_command("adb devices")
        if not success:
            return []
        
        devices = []
        lines = output.strip().split('\n')
        for line in lines[1:]:  # 跳过第一行 "List of devices attached"
            if '\t' in line:
                device_id = line.split('\t')[0]
                devices.append(device_id)
        return devices
    
    def 截图(self, save_path=None):
        """
        截取手机屏幕截图
        
        参数:
            save_path: 保存路径，如果不指定则保存到默认位置
            
        返回:
            截图保存的完整路径，失败返回 None
        """
        # 默认保存路径
        if save_path is None:
            save_dir = os.path.join(os.path.dirname(__file__), "resource", "cache")
            os.makedirs(save_dir, exist_ok=True)
            timestamp = int(time.time() * 1000)
            save_path = os.path.join(save_dir, f"screenshot_{timestamp}.png")
        
        # 方法1: 直接截图到电脑 (推荐，更快)
        # 先在手机上截图，然后拉取到电脑
        phone_path = "/sdcard/screen_temp.png"
        
        # 在手机上截图
        success, output = self._run_command(
            f"{self._adb_prefix} shell screencap -p {phone_path}"
        )
        if not success:
            print(f"截图失败: {output}")
            return None
        
        # 将截图从手机拉取到电脑
        success, output = self._run_command(
            f"{self._adb_prefix} pull {phone_path} \"{save_path}\""
        )
        if not success:
            print(f"拉取截图失败: {output}")
            return None
        
        # 删除手机上的临时截图（可选）
        self._run_command(f"{self._adb_prefix} shell rm {phone_path}")
        
        return save_path
    
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
    
    def 点击(self, x, y):
        """
        点击屏幕指定坐标
        
        参数:
            x: X 坐标
            y: Y 坐标
        """
        success, output = self._run_command(
            f"{self._adb_prefix} shell input tap {x} {y}"
        )
        if not success:
            print(f"点击失败: {output}")
        return success
    
    def 长按(self, x, y, duration_ms=1000):
        """
        长按屏幕指定坐标
        
        参数:
            x: X 坐标
            y: Y 坐标
            duration_ms: 长按时长（毫秒），默认1000ms
        """
        success, output = self._run_command(
            f"{self._adb_prefix} shell input swipe {x} {y} {x} {y} {duration_ms}"
        )
        if not success:
            print(f"长按失败: {output}")
        return success
    
    def 滑动(self, x1, y1, x2, y2, duration_ms=500):
        """
        滑动操作
        
        参数:
            x1, y1: 起始坐标
            x2, y2: 结束坐标
            duration_ms: 滑动时长（毫秒），默认500ms
        """
        success, output = self._run_command(
            f"{self._adb_prefix} shell input swipe {x1} {y1} {x2} {y2} {duration_ms}"
        )
        if not success:
            print(f"滑动失败: {output}")
        return success
    
    def 随机点击(self, x, y, w, h):
        """
        在指定区域内随机点击
        
        参数:
            x: 区域左上角 X 坐标
            y: 区域左上角 Y 坐标
            w: 区域宽度
            h: 区域高度
        """
        random_x = random.randint(x, x + w)
        random_y = random.randint(y, y + h)
        return self.点击(random_x, random_y)
    
    def 输入文本(self, text):
        """
        输入文本（仅支持英文和数字）
        
        参数:
            text: 要输入的文本
        """
        # 需要转义特殊字符
        escaped_text = text.replace(' ', '%s').replace('&', '\\&').replace('<', '\\<').replace('>', '\\>').replace('|', '\\|')
        success, output = self._run_command(
            f'{self._adb_prefix} shell input text "{escaped_text}"'
        )
        if not success:
            print(f"输入文本失败: {output}")
        return success
    
    def 按键(self, keycode):
        """
        模拟按键
        
        参数:
            keycode: 按键代码，常用的有:
                - 3: HOME
                - 4: BACK
                - 24: 音量+
                - 25: 音量-
                - 26: 电源键
                - 82: 菜单键
                - 187: 多任务
        """
        success, output = self._run_command(
            f"{self._adb_prefix} shell input keyevent {keycode}"
        )
        if not success:
            print(f"按键失败: {output}")
        return success
    
    def 返回(self):
        """模拟返回键"""
        return self.按键(4)
    
    def 主页(self):
        """模拟 HOME 键"""
        return self.按键(3)
    
    def 获取屏幕分辨率(self):
        """
        获取屏幕分辨率
        
        返回:
            (width, height) 元组，失败返回 None
        """
        success, output = self._run_command(
            f"{self._adb_prefix} shell wm size"
        )
        if success:
            # 输出格式: Physical size: 1080x1920
            try:
                size_str = output.split(':')[-1].strip()
                width, height = map(int, size_str.split('x'))
                return (width, height)
            except:
                pass
        return None
    
    def 延时(self, seconds):
        """延时指定秒数"""
        time.sleep(seconds)
    
    def 随机延时(self, min_seconds, max_seconds):
        """随机延时"""
        if min_seconds > max_seconds:
            min_seconds, max_seconds = max_seconds, min_seconds
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def 执行命令(self, command):
        """
        执行自定义 ADB shell 命令
        
        参数:
            command: shell 命令（不需要加 adb shell 前缀）
            
        返回:
            (success, output)
        """
        return self._run_command(f"{self._adb_prefix} shell {command}")


# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 创建 ADB 控制器
    # 如果只有一个设备，不需要指定 device_id
    adb = ADBController()
    
    # 如果有多个设备，需要指定设备ID
    # adb = ADBController(device_id="127.0.0.1:5555")
    
    # 查看已连接的设备
    print("已连接设备:", adb.get_devices())
    
    # 检查设备连接
    if adb.check_connection():
        print("设备已连接")
        
        # 获取屏幕分辨率
        resolution = adb.获取屏幕分辨率()
        print(f"屏幕分辨率: {resolution}")
        
        # 截图
        screenshot_path = adb.截图()
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

