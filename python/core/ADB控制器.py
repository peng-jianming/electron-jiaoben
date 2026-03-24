"""
ADB 控制器 - 封装 ADB 命令实现截图和点击功能
"""
import subprocess
import time
import random
from 设置 import ADB路径


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

    def 截图到内存_快速原始(self):
        """
        使用非 PNG 模式截图（raw RGBA），通常比 -p 更快。

        返回:
            原始字节数据（包含 12 字节头 + 像素数据），失败返回 None
        """
        try:
            命令 = [ADB路径]
            if self.设备ID:
                命令.extend(["-s", self.设备ID])
            命令.extend(["exec-out", "screencap"])

            结果 = subprocess.run(
                命令,
                shell=False,
                capture_output=True,
                timeout=10
            )
            if 结果.returncode == 0:
                return 结果.stdout
            return None
        except Exception as e:
            print(f"快速截图失败: {e}")
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

    # ====================== 拟人化滑动相关 ======================

    def _生成贝塞尔曲线(self, qx, qy, zx, zy):
        """
        生成从 (qx, qy) 到 (zx, zy) 的三次贝塞尔曲线轨迹点
        参考 JS 版本的 获取贝塞尔曲线 实现
        """
        def 三次贝塞尔曲线计算(cp, t):
            # X 轴
            cx = 3.0 * (cp[1]["x"] - cp[0]["x"])
            bx = 3.0 * (cp[2]["x"] - cp[1]["x"]) - cx
            ax = cp[3]["x"] - cp[0]["x"] - cx - bx

            # Y 轴
            cy = 3.0 * (cp[1]["y"] - cp[0]["y"])
            by = 3.0 * (cp[2]["y"] - cp[1]["y"]) - cy
            ay = cp[3]["y"] - cp[0]["y"] - cy - by

            t_squared = t * t
            t_cubed = t_squared * t

            return {
                "x": (ax * t_cubed) + (bx * t_squared) + (cx * t) + cp[0]["x"],
                "y": (ay * t_cubed) + (by * t_squared) + (cy * t) + cp[0]["y"],
            }

        # 4 个控制点：起点、两个随机控制点、终点
        control_points = [
            {"x": qx, "y": qy},
            {
                "x": qx + (random.random() * 240 - 120),
                "y": qy + random.random() * 100,
            },
            {
                "x": zx + (random.random() * 240 - 120),
                "y": zy + (random.random() * 200 - 100),
            },
            {"x": zx, "y": zy},
        ]

        points = []
        # 步长 0.15，轨迹点数量与 JS 版本一致
        t = 0.0
        while t <= 1.0 + 1e-6:
            point = 三次贝塞尔曲线计算(control_points, t)
            points.append((int(point["x"]), int(point["y"])))
            t += 0.15

        return points

    def _生成人类延时模式(self, 点数, 总时间毫秒=None):
        """
        生成拟人化的滑动时间间隔序列（秒）
        模仿“开始稍慢 - 中间较快 - 结束再慢”的手指滑动节奏
        """
        if 点数 <= 0:
            return []

        if 总时间毫秒 is None:
            总时间毫秒 = 300 + random.random() * 200  # 300-500ms

        基础间隔 = 总时间毫秒 / 点数
        模式 = []

        for i in range(点数):
            进度 = i / 点数

            if 进度 < 0.2:
                # 开始阶段：稍慢
                延时倍数 = 0.8 + random.random() * 0.2
            elif 进度 > 0.8:
                # 结束阶段：变慢
                延时倍数 = 1.0 + random.random() * 0.3
            else:
                # 中间阶段：更快
                延时倍数 = 0.4 + random.random() * 0.3

            # 随机波动
            延时倍数 += (random.random() - 0.5) * 0.2
            延时倍数 = max(0.25, 延时倍数)

            间隔秒 = (基础间隔 * 延时倍数) / 1000.0
            模式.append(间隔秒)

        return 模式

    def 拟人滑动(self, x1, y1, x2, y2):
        """
        拟人化滑动：使用 motionevent + 贝塞尔曲线 + 随机延时
        参考 JS 中的 ADB滑动 / 随机ADB滑动 实现，更接近真实手指操作
        """
        # 生成轨迹点
        points = self._生成贝塞尔曲线(x1, y1, x2, y2)
        if len(points) < 2:
            print("拟人滑动失败：轨迹点数量不足")
            return False

        # 为每个移动点生成延时（不包含起点）
        延时模式 = self._生成人类延时模式(len(points) - 1)

        try:
            # 按下起点
            start_x, start_y = points[0]
            成功, 输出 = self._执行命令(
                f"{self._命令前缀} shell input motionevent DOWN {start_x} {start_y}"
            )
            if not 成功:
                print(f"拟人滑动按下失败: {输出}")
                return False

            # 初始轻微延时
            time.sleep(0.01 + random.random() * 0.01)

            # 中间移动点
            for i in range(1, len(points) - 1):
                px, py = points[i]
                成功, 输出 = self._执行命令(
                    f"{self._命令前缀} shell input motionevent MOVE {px} {py}"
                )
                if not 成功:
                    print(f"拟人滑动移动失败: {输出}")
                    # 不中断整个滑动，继续尝试后续点
                # 使用对应的延时时间（第 i-1 个）
                延时 = 延时模式[i - 1] if i - 1 < len(延时模式) else 0.01
                time.sleep(max(0.005, 延时))

            # 移动到终点
            end_x, end_y = points[-1]
            成功, 输出 = self._执行命令(
                f"{self._命令前缀} shell input motionevent MOVE {end_x} {end_y}"
            )
            if not 成功:
                print(f"拟人滑动终点移动失败: {输出}")

            # 抬起前的微小停顿
            time.sleep(0.02 + random.random() * 0.02)

            成功, 输出 = self._执行命令(
                f"{self._命令前缀} shell input motionevent UP {end_x} {end_y}"
            )
            if not 成功:
                print(f"拟人滑动抬起失败: {输出}")
                return False

            return True
        except Exception as e:
            print(f"拟人滑动过程中出错: {e}")
            return False


    def _随机区间位置(self, start, end):
        """返回 [start, end] 间的随机整数"""
        if start > end:
            start, end = end, start
        return random.randint(int(start), int(end))

    def _随机坐标(self, x, y, 宽, 高):
        """在给定矩形区域内返回一个随机坐标"""
        return (
            self._随机区间位置(x, x + 宽),
            self._随机区间位置(y, y + 高),
        )

    def 拟人滑动_区域(self, 起始区域, 结束区域):
        """
        使用起始 / 结束“区域”进行拟人滑动。

        逻辑：
        - 起点：在起始区域内完全随机
        - 终点：在“主方向”上随机（由两个区域的大致位置决定），
                在“非主方向”上仅在起点附近做小幅偏移，避免出现左右大位移变成横向滑动。

        参数格式：
            起始区域、结束区域: "x,y,w,h" 字符串
        """
        try:
            sx, sy, sw, sh = [float(v) for v in 起始区域.split(",")]
            ex, ey, ew, eh = [float(v) for v in 结束区域.split(",")]
        except Exception as e:
            print(f"拟人滑动_区域 参数解析失败: {e}")
            return False

        # 先随机起点
        start_x, start_y = self._随机坐标(sx, sy, sw, sh)

        # 根据两个区域中心的相对位置，自动判断主方向（竖直 / 水平）
        start_cx, start_cy = sx + sw / 2.0, sy + sh / 2.0
        end_cx, end_cy = ex + ew / 2.0, ey + eh / 2.0
        dx = end_cx - start_cx
        dy = end_cy - start_cy

        # True 表示“上下滑”为主方向；False 表示“左右滑”为主方向
        竖直为主 = abs(dy) >= abs(dx)

        # 非主方向的最大偏移量：越小越“直”，越大越“歪”
        max_deviation = 30

        if 竖直为主:
            # === 上下滑动 ===
            # 主方向：Y —— 终点 Y 在结束区域内完全随机
            end_y = self._随机区间位置(ey, ey + eh)

            # 非主方向：X —— 终点 X 在起点附近做小范围浮动，再 clamp 到结束区域内
            raw_end_x = start_x + self._随机区间位置(-max_deviation, max_deviation)
            end_x = max(ex, min(ex + ew, raw_end_x))
        else:
            # === 左右滑动 ===
            # 主方向：X —— 终点 X 在结束区域内完全随机
            end_x = self._随机区间位置(ex, ex + ew)

            # 非主方向：Y —— 终点 Y 在起点附近做小范围浮动，再 clamp 到结束区域内
            raw_end_y = start_y + self._随机区间位置(-max_deviation, max_deviation)
            end_y = max(ey, min(ey + eh, raw_end_y))

        # print(f"拟人滑动_区域: start=({start_x},{start_y}) end=({end_x},{end_y}) 竖直为主={竖直为主}")
        return self.拟人滑动(start_x, start_y, end_x, end_y)