"""
ADB 控制器 - 封装 ADB 命令实现截图和点击功能
"""
import subprocess
import time
import random
from 配置.设置 import ADB路径


class ADB控制器类:
    """ADB 控制器，封装截图和点击功能"""

    def __init__(self, 设备ID=None):
        """
        初始化 ADB 控制器

        参数:
            设备ID: 设备ID，如果有多个设备连接时需要指定
        """
        self.设备ID = 设备ID
        self._命令前缀 = self._构建命令前缀()

    def _构建命令前缀(self):
        """构建 ADB 命令前缀"""
        if self.设备ID:
            return f'"{ADB路径}" -s {self.设备ID}'
        return f'"{ADB路径}"'

    def _执行命令(self, 命令, shell=True):
        """
        执行命令并返回结果

        返回:
            (成功, 输出) - 成功标志和输出内容
        """
        try:
            结果 = subprocess.run(
                命令,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=30
            )
            if 结果.returncode == 0:
                return True, 结果.stdout.strip()
            else:
                return False, 结果.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "命令执行超时"
        except Exception as e:
            return False, str(e)

    def 检查连接(self):
        """检查设备连接状态"""
        成功, 输出 = self._执行命令(f"{self._命令前缀} get-state")
        return 成功 and "device" in 输出

    def 获取设备列表(self):
        """获取所有已连接的设备列表"""
        成功, 输出 = self._执行命令(f'"{ADB路径}" devices')
        if not 成功:
            return []

        设备列表 = []
        行列表 = 输出.strip().split('\n')
        for 行 in 行列表[1:]:
            if '\t' in 行:
                设备ID = 行.split('\t')[0]
                设备列表.append(设备ID)
        return 设备列表

    def 截图(self, 保存路径):
        """
        截取手机屏幕截图

        返回:
            截图保存的完整路径，失败返回 None
        """
        手机路径 = "/sdcard/screen_temp.png"

        # 在手机上截图
        成功, 输出 = self._执行命令(
            f"{self._命令前缀} shell screencap -p {手机路径}"
        )
        if not 成功:
            print(f"截图失败: {输出}")
            return None

        # 将截图从手机拉取到电脑
        成功, 输出 = self._执行命令(
            f'{self._命令前缀} pull {手机路径} "{保存路径}"'
        )
        if not 成功:
            print(f"拉取截图失败: {输出}")
            return None

        # 删除手机上的临时截图
        self._执行命令(f"{self._命令前缀} shell rm {手机路径}")

        return 保存路径

    def 截图到内存(self):
        """
        截图并直接返回图像数据（不保存到文件）

        返回:
            PNG 图像的字节数据，失败返回 None
        """
        try:
            结果 = subprocess.run(
                f"{self._命令前缀} exec-out screencap -p",
                shell=True,
                capture_output=True,
                timeout=10
            )
            if 结果.returncode == 0:
                return 结果.stdout
            return None
        except Exception as e:
            print(f"截图失败: {e}")
            return None

    def 点击(self, x, y):
        """点击屏幕指定坐标"""
        成功, 输出 = self._执行命令(
            f"{self._命令前缀} shell input tap {x} {y}"
        )
        if not 成功:
            print(f"点击失败: {输出}")
        return 成功

    def 模拟点击(self, x, y, 按压时长=(0, 0.3)):
        """
        模拟真实点击（使用 motionevent，更像人为操作）

        参数:
            x: X 坐标
            y: Y 坐标
            按压时长: 按下持续时间（秒），可以是单个值或(最小, 最大)元组
        """
        if not x or not y:
            return False

        # 按下
        成功1, 输出1 = self._执行命令(
            f"{self._命令前缀} shell input motionevent DOWN {x} {y}"
        )
        if not 成功1:
            print(f"模拟点击按下失败: {输出1}")
            return False

        # 随机延时
        if isinstance(按压时长, (tuple, list)) and len(按压时长) == 2:
            self.随机延时(按压时长[0], 按压时长[1])
        else:
            time.sleep(按压时长 if isinstance(按压时长, (int, float)) else 0.1)

        # 抬起
        成功2, 输出2 = self._执行命令(
            f"{self._命令前缀} shell input motionevent UP {x} {y}"
        )
        if not 成功2:
            print(f"模拟点击抬起失败: {输出2}")
            return False

        return True

    def 长按(self, x, y, 时长毫秒=1000):
        """长按屏幕指定坐标"""
        成功, 输出 = self._执行命令(
            f"{self._命令前缀} shell input swipe {x} {y} {x} {y} {时长毫秒}"
        )
        if not 成功:
            print(f"长按失败: {输出}")
        return 成功

    def 滑动(self, x1, y1, x2, y2, 时长毫秒=500):
        """滑动操作"""
        成功, 输出 = self._执行命令(
            f"{self._命令前缀} shell input swipe {x1} {y1} {x2} {y2} {时长毫秒}"
        )
        if not 成功:
            print(f"滑动失败: {输出}")
        return 成功

    def 随机点击(self, x, y, 宽, 高):
        """在指定区域内随机点击"""
        随机x = random.randint(x, x + 宽)
        随机y = random.randint(y, y + 高)
        return self.点击(随机x, 随机y)

    def 输入文本(self, 文本):
        """输入文本（仅支持英文和数字）"""
        转义文本 = 文本.replace(' ', '%s').replace('&', '\\&').replace('<', '\\<').replace('>', '\\>').replace('|', '\\|')
        成功, 输出 = self._执行命令(
            f'{self._命令前缀} shell input text "{转义文本}"'
        )
        if not 成功:
            print(f"输入文本失败: {输出}")
        return 成功

    def 按键(self, 键码):
        """
        模拟按键

        常用键码:
            - 3: HOME
            - 4: BACK
            - 24: 音量+
            - 25: 音量-
            - 26: 电源键
            - 82: 菜单键
            - 187: 多任务
        """
        成功, 输出 = self._执行命令(
            f"{self._命令前缀} shell input keyevent {键码}"
        )
        if not 成功:
            print(f"按键失败: {输出}")
        return 成功

    def 返回(self):
        """模拟返回键"""
        return self.按键(4)

    def 主页(self):
        """模拟 HOME 键"""
        return self.按键(3)

    def 获取屏幕分辨率(self):
        """获取屏幕分辨率，返回 (宽, 高) 元组"""
        成功, 输出 = self._执行命令(
            f"{self._命令前缀} shell wm size"
        )
        if 成功:
            try:
                尺寸字符串 = 输出.split(':')[-1].strip()
                宽, 高 = map(int, 尺寸字符串.split('x'))
                return (宽, 高)
            except:
                pass
        return None

    def 延时(self, 秒数):
        """延时指定秒数"""
        time.sleep(秒数)

    def 随机延时(self, 最小秒数, 最大秒数):
        """随机延时"""
        if 最小秒数 > 最大秒数:
            最小秒数, 最大秒数 = 最大秒数, 最小秒数
        time.sleep(random.uniform(最小秒数, 最大秒数))

    def 执行Shell命令(self, 命令):
        """执行自定义 ADB shell 命令"""
        return self._执行命令(f"{self._命令前缀} shell {命令}")
