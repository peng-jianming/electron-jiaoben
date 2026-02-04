"""
任务执行器 - 状态机核心逻辑
"""
import os
import time
import random
import threading
import numpy as np
from PIL import Image

from .设备控制器 import 设备控制器类
from .截图管理器 import 截图管理器类
from .动作管理器 import 动作管理器类
from .界面管理器 import 界面管理器类
from 配置.设置 import (
    字库文件路径, 模型文件路径, 音乐文件路径,
    未知截图目录, 未知界面超时时间
)
from 配置.界面配置 import 界面集合


class 任务执行器类:
    
    def __init__(self, 设备ID):
        """
        初始化任务执行器

        参数:
            设备ID: 设备ID
        """
        self.字库缓存 = {}
        self.加载字库文件(字库文件路径)
        self._模型 = None

        self.控制器 = 设备控制器类(设备ID)
        self._截图上下文 = 截图管理器类(self.控制器)
        self.界面识别缓存 = {}
        self.界面集合 = self._加载界面配置(界面集合)
        self._状态集合 = {}
        self._当前界面 = None
        self._上一界面 = None
        self._运行中 = False
        self._暂停中 = False
        self._暂停事件 = threading.Event()
        self._暂停事件.set()  # 初始为非暂停状态
        self._上下文 = {}
        self._未知开始时间 = None
        self._未知超时时间 = 未知界面超时时间

    def 注册界面(self, 界面名称):
        """装饰器：注册界面处理函数"""
        def 装饰器(函数):
            self._状态集合[界面名称] = 函数
        return 装饰器

    def _尝试执行误触(self):
        
        # 根据概率决定是否触发误触
        if random.random() > 0.03:
            return False
        
        # 随机选择误触类型
        误触类型 = random.choices(
            ['点击', '滑动', '等待'],
            weights=[0.5, 0.2, 0.3],  # 点击50%, 滑动20%, 等待30%
            k=1
        )[0]
        
        print(f"[误触模拟] 误触 - 类型: {误触类型}")
        
        if 误触类型 == '点击':
            self.控制器.随机误触()
        elif 误触类型 == '滑动':
            self.控制器.随机空白滑动()
        else:  # 等待
            self.控制器.随机等待(0.3, 1.5)
        
        return True

    def 保存未知图片(self, 图像数据):
        """保存未知界面截图"""
        try:
            os.makedirs(未知截图目录, exist_ok=True)
            时间戳 = time.strftime("%Y%m%d_%H%M%S")
            文件名 = f"unknown_{时间戳}.png"
            目标路径 = os.path.join(未知截图目录, 文件名)

            if isinstance(图像数据, Image.Image):
                图像数据.save(目标路径)
            else:
                import shutil
                shutil.copy(图像数据, 目标路径)

            print(f"未知界面截图已保存: {目标路径}")
        except Exception as e:
            print(f"保存未知界面截图失败: {e}")

    def 播放音乐(self):
        """播放提示音乐"""
        try:
            if os.path.exists(音乐文件路径):
                def 播放():
                    try:
                        from playsound import playsound
                        playsound(音乐文件路径)
                    except ImportError:
                        import platform
                        if platform.system() == "Windows":
                            os.system(f'start "" "{音乐文件路径}"')
                        elif platform.system() == "Darwin":
                            os.system(f'afplay "{音乐文件路径}" &')
                        else:
                            os.system(f'mpg123 "{音乐文件路径}" &')
                    except Exception as e:
                        print(f"播放音乐失败: {e}")

                线程 = threading.Thread(target=播放, daemon=True)
                线程.start()
                print("正在播放提示音乐...")
            else:
                print(f"音乐文件不存在: {音乐文件路径}")
        except Exception as e:
            print(f"播放音乐出错: {e}")

    def 开始(self):
        """启动状态机"""
        self._运行中 = True
        while self._运行中:
            # 检查暂停状态，如果暂停则等待
            self._暂停事件.wait()
            if not self._运行中:
                break
            
            # 在当前不处于未知界面时，尝试执行随机误触, 避免干扰未知界面的操作
            if self._未知开始时间 is None:
                self._尝试执行误触()
            
            # 每轮开始时重置截图上下文
            self._截图上下文.新轮次()
            截图 = self._截图上下文.获取截图()
            已找到 = False

            # 优先检测当前/上一个界面
            优先列表 = []
            if self._当前界面:
                优先列表.append(self._当前界面)
            if self._上一界面 and self._上一界面 != self._当前界面:
                优先列表.append(self._上一界面)

            for 界面名称 in 优先列表 + [k for k in self._状态集合.keys() if k not in 优先列表]:
                if self.界面识别缓存[界面名称].查找().是否找到():
                    已找到 = True
                    print(f"目前位于: {界面名称}")
                    self.更新上下文(上一状态=self._当前界面)
                    self._当前界面 = 界面名称
                    self._未知开始时间 = None

                    结果 = self._状态集合[界面名称](self._上下文, self.界面集合[界面名称])
                    if isinstance(结果, dict):
                        self._上下文.update(结果)
                    elif 结果 is False:
                        print(f"界面 {self._当前界面} 处理失败")
                    break

            if not 已找到:
                print("搜索未注册界面")
                # 尝试关闭未注册界面
                for 界面名称, 界面对象 in self.界面集合.items():
                    if 界面名称 in self._状态集合:
                        continue
                    if hasattr(界面对象.按钮, '关闭'):
                        if self.界面识别缓存[界面名称].查找().是否找到():
                            界面对象.按钮.关闭.点击()
                            print(f"目前位于未注册界面: {界面名称}")
                            break

                # 未知界面计时逻辑
                if self._未知开始时间 is None:
                    self._未知开始时间 = time.time()
                else:
                    经过时间 = time.time() - self._未知开始时间
                    if 经过时间 >= self._未知超时时间:
                        print(f"未知界面已持续 {经过时间:.1f} 秒，保存截图")
                        self.保存未知图片(截图)
                        self.播放音乐()
                        self._未知开始时间 = time.time()

            time.sleep(0.2)

    def 结束(self):
        """结束状态机"""
        self._运行中 = False
        self._暂停事件.set()  # 确保退出等待状态

    def 暂停(self):
        """暂停状态机"""
        if self._运行中 and not self._暂停中:
            self._暂停中 = True
            self._暂停事件.clear()
            print("任务已暂停")
            return True
        return False

    def 恢复(self):
        """恢复状态机"""
        if self._运行中 and self._暂停中:
            self._暂停中 = False
            self._暂停事件.set()
            print("任务已恢复")
            return True
        return False

    def 更新上下文(self, **kwargs):
        """更新上下文"""
        self._上下文.update(kwargs)

    def 更新设备状态(self, **kwargs):
        """
        更新设备状态到前端（金币、等级等信息）
        
        参数:
            **kwargs: 支持以下字段：
                - 金币: 当前金币数量
                - 等级: 当前等级
                - 其他自定义字段
        
        示例:
            self.更新设备状态(金币=123456, 等级=69)
        """
        self.控制器.更新设备状态(**kwargs)

    def 加载字库文件(self, 字库文件路径):
        """加载字库文件"""
        try:
            with open(字库文件路径, "r", encoding="utf-8") as f:
                行列表 = f.readlines()
        except Exception as e:
            print(f"读取字库文件失败: {e}")
            return 0

        加载数量 = 0

        for 行 in 行列表:
            行 = 行.strip()
            if not 行:
                continue

            部分列表 = 行.split("&")
            if len(部分列表) != 5:
                continue

            点阵十六进制, 尺寸信息, 偏色字符串, 名称, 目标偏移 = [p.strip() for p in 部分列表]

            # 预解析偏色信息
            颜色容差列表 = []
            for 颜色容差 in 偏色字符串.split("|"):
                颜色容差 = 颜色容差.strip()
                if not 颜色容差:
                    continue
                基础颜色十六进制, 容差十六进制 = 颜色容差.split("-")
                颜色容差列表.append({
                    "基础颜色": np.array([
                        int(基础颜色十六进制[0:2], 16),
                        int(基础颜色十六进制[2:4], 16),
                        int(基础颜色十六进制[4:6], 16),
                    ], dtype=np.int16),
                    "容差": np.array([
                        int(容差十六进制[0:2], 16),
                        int(容差十六进制[2:4], 16),
                        int(容差十六进制[4:6], 16),
                    ], dtype=np.int16),
                })

            尺寸部分 = 尺寸信息.split(",")
            if len(尺寸部分) != 3:
                continue

            try:
                宽度 = int(尺寸部分[0])
                高度 = int(尺寸部分[1])
                总数量 = int(尺寸部分[2])
            except ValueError:
                continue

            目标偏移部分 = 目标偏移.split(",")
            if len(目标偏移部分) != 4:
                continue

            try:
                目标偏移x = int(目标偏移部分[0])
                目标偏移y = int(目标偏移部分[1])
                目标偏移宽 = int(目标偏移部分[2])
                目标偏移高 = int(目标偏移部分[3])
            except ValueError:
                continue

            # 将16进制点阵转换为二值化图像
            二进制数据 = []
            for 十六进制字符 in 点阵十六进制:
                位 = format(int(十六进制字符, 16), "04b")
                二进制数据.extend([int(b) for b in 位])

            总像素 = 宽度 * 高度
            二进制数据 = 二进制数据[:总像素]

            二进制数组 = np.array(二进制数据, dtype=np.uint8).reshape((高度, 宽度))
            二进制数组 = np.where(二进制数组 == 1, 255, 0).astype(np.uint8)
            模板掩码 = (二进制数组 == 255).astype(np.uint8)

            if 名称 not in self.字库缓存:
                self.字库缓存[名称] = []

            self.字库缓存[名称].append({
                "模板掩码": 模板掩码,
                "宽度": 宽度,
                "高度": 高度,
                "总数量": 总数量,
                "偏色": 偏色字符串,
                "颜色容差列表": 颜色容差列表,
                "点阵十六进制": 点阵十六进制,
                "目标偏移x": 目标偏移x,
                "目标偏移y": 目标偏移y,
                "目标偏移宽": 目标偏移宽,
                "目标偏移高": 目标偏移高,
            })

            加载数量 += 1

        print(f"成功加载 {加载数量} 个字库到缓存")
        return 加载数量

    def 加载模型文件(self, 模型路径):
        """加载 YOLO 模型"""
        from ultralytics import YOLO
        self._模型 = YOLO(模型路径)
        return self._模型

    def _加载界面配置(self, 界面集合):
        """加载界面配置"""
        配置 = {}
        for 界面名称, 原始配置 in 界面集合.items():
            # 创建界面识别用的动作管理器
            识别配置 = {"查找字符串": 界面名称}
            识别配置.update(原始配置)
            self.界面识别缓存[界面名称] = (
                动作管理器类(识别配置, self.控制器, self._截图上下文)
                .设置字库(self.字库缓存)
                .设置模型(self._模型)
            )
            # 创建界面配置对象
            配置[界面名称] = 界面管理器类(
                界面名称,
                原始配置,
                self.控制器,
                self._截图上下文,
                self.字库缓存,
                self._模型
            )
        return 配置
