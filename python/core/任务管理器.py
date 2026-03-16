import os
import sys
import json
import time
import random
import threading
import importlib
import numpy as np
from PIL import Image

from .设备控制器 import 设备控制器类
from .截图管理器 import 截图管理器类
from .动作管理器 import 动作管理器类
from .界面管理器 import 界面管理器类
from 设置 import (
    字库文件路径, 图片库文件路径, 模型文件路径, 音乐文件路径,
    未知截图目录, 界面配置文件路径, 任务目录
)

from dataclasses import dataclass

@dataclass
class 状态机环境:
    控制器: object
    界面集合: dict
    截图上下文: object
    界面识别缓存: dict
    更新数据: callable
    参数配置: dict

class 任务管理器类:
    # 任务管理器, 负责任务的运行工作, 包括任务的加载、运行、保存进度等。
    # 结束,暂停,恢复,由线程控制器强制控制线程运行状态.
    def __init__(self, 参数集合):
        self.设备ID = 参数集合.get("设备ID")
        self.任务配置列表 = 参数集合.get("任务配置列表")
        self.更新数据 = 参数集合.get("更新数据")
        self.参数集合 = 参数集合

        self._任务类型映射 = self.获取所有任务列表()

        # 设备控制器实例
        self.控制器 = 设备控制器类(self.设备ID)

        # 截图
        self._截图上下文 = 截图管理器类(self.控制器)

        # 资源配置
        self.字库缓存 = self.加载字库文件(字库文件路径)
        self.图片库缓存 = self.加载图片库文件(图片库文件路径)
        self._模型 = None

        # 界面配置
        self.界面识别缓存 = {}
        self.界面集合 = self._加载界面配置(界面配置文件路径)

        self.运行()

    @staticmethod
    def 获取所有任务列表():
        """
        扫描 任务目录 下所有 .py 模块，以文件名作为任务名，收集模块下的 `创建任务` 函数。
        """
        结果 = {}
        忽略模块名 = {'__init__', '任务管理器'}
        父目录 = os.path.dirname(任务目录)
        包名 = os.path.basename(任务目录)

        if 父目录 and 父目录 not in sys.path:
            sys.path.insert(0, 父目录)

        if not os.path.isdir(任务目录):
            print(f"[任务发现] 任务目录不存在: {任务目录}")
            return {}

        for 文件名 in os.listdir(任务目录):
            if not 文件名.endswith(".py"):
                continue
            任务名 = 文件名[:-3]
            if 任务名 in 忽略模块名:
                continue
            模块全名 = f"{包名}.{任务名}"
            try:
                模块 = importlib.import_module(模块全名)
            except Exception as e:
                print(f"[任务发现] 导入模块 {模块全名} 失败: {e}")
                continue

            创建任务 = getattr(模块, "创建任务", None)
            if 创建任务 is None:
                print(f"[任务发现] 跳过 {任务名}: 缺少 创建任务")
                continue
            if not callable(创建任务):
                print(f"[任务发现] 跳过 {任务名}: 创建任务 不可调用")
                continue

            结果[任务名] = 创建任务
            print(f"[任务发现] 已注册任务: {任务名}")

        return 结果

    def 运行(self):
        self.更新数据("任务配置列表", self.任务配置列表)
        self.更新数据("故障", False)
        for 任务配置 in self.任务配置列表:
            if 任务配置.get("是否完成"):
                continue
            self.更新数据("当前任务", 任务配置.get("名称"))
            self.更新数据("日志", f"{任务配置.get('名称')} 开始")
            环境 = 状态机环境(
                控制器=self.控制器,
                界面集合=self.界面集合,
                截图上下文=self._截图上下文,
                界面识别缓存=self.界面识别缓存,
                更新数据=self.更新数据,
                参数配置=任务配置.get("参数配置", {}),
            )
            self._任务类型映射[任务配置.get("名称")](环境)
            任务配置["是否完成"] = True
            self.更新数据("任务配置列表", self.任务配置列表)
            self.更新数据("日志", f"{任务配置.get('名称')} 完成")

        self.更新数据("日志", "所有任务完成")

    def 加载字库文件(self, 字库文件路径):
        """加载字库文件（JSON 格式）"""
        try:
            with open(字库文件路径, "r", encoding="utf-8") as f:
                条目列表 = json.load(f)
        except Exception:
            self.更新数据("日志", "读取字库文件失败")
            return {}

        if not isinstance(条目列表, list):
            self.更新数据("日志", "字库文件格式错误：应为 JSON 数组")
            return {}

        # 重置字库缓存
        self.字库缓存 = {}
        加载数量 = 0

        for 条目 in 条目列表:
            if not isinstance(条目, dict):
                continue

            名称 = 条目.get("名字")
            点阵十六进制 = 条目.get("点阵")
            尺寸信息 = 条目.get("长宽有效数量")
            偏色字符串 = 条目.get("偏色")
            目标偏移 = 条目.get("偏移点击区域")

            if not all([名称, 点阵十六进制, 尺寸信息, 偏色字符串 is not None, 目标偏移 is not None]):
                continue

            偏色字符串 = 偏色字符串.strip() if isinstance(偏色字符串, str) else ""

            # 预解析偏色信息
            颜色容差列表 = []
            for 颜色容差 in 偏色字符串.split("|"):
                颜色容差 = 颜色容差.strip()
                if not 颜色容差:
                    continue
                部分 = 颜色容差.split("-")
                if len(部分) != 2:
                    continue
                基础颜色十六进制, 容差十六进制 = 部分
                if len(基础颜色十六进制) != 6 or len(容差十六进制) != 6:
                    continue
                try:
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
                except ValueError:
                    continue

            尺寸部分 = 尺寸信息.strip().split(",")
            if len(尺寸部分) != 3:
                continue

            try:
                宽度 = int(尺寸部分[0].strip())
                高度 = int(尺寸部分[1].strip())
                总数量 = int(尺寸部分[2].strip())
            except ValueError:
                continue

            目标偏移部分 = 目标偏移.strip().split(",")
            if len(目标偏移部分) != 4:
                continue

            try:
                目标偏移x = int(目标偏移部分[0].strip())
                目标偏移y = int(目标偏移部分[1].strip())
                目标偏移宽 = int(目标偏移部分[2].strip())
                目标偏移高 = int(目标偏移部分[3].strip())
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
        self.更新数据("日志", f"成功加载 {加载数量} 个字库到缓存")
        return self.字库缓存

    def 加载图片库文件(self, 图片库文件路径):
        """加载图片库文件（.npz 格式），键为图片名，值为模板图像数组，供模板匹配找图使用。"""
        self.图片库缓存 = {}
        if not 图片库文件路径 or not os.path.isfile(图片库文件路径):
            self.更新数据("日志", "图片库文件不存在，跳过加载")
            return self.图片库缓存
        try:
            data = np.load(图片库文件路径, allow_pickle=False)
            for 名称 in data.files:
                self.图片库缓存[名称] = np.asarray(data[名称])
            data.close()
            self.更新数据("日志", f"成功加载 {len(self.图片库缓存)} 张图片到图片库缓存")
        except Exception as e:
            self.更新数据("日志", f"加载图片库文件失败: {e}")

        return self.图片库缓存

    def 加载模型文件(self, 模型路径):
        """加载 YOLO 模型"""
        from ultralytics import YOLO
        self._模型 = YOLO(模型路径)
        return self._模型

    def _加载界面配置(self, 界面配置文件路径):
        """加载界面配置"""
        with open(界面配置文件路径, "r", encoding="utf-8") as f:
            界面集合 = json.load(f)
        if not isinstance(界面集合, dict):
            self.更新数据("日志", "界面配置文件格式错误：应为 JSON 对象")
            return {}

        配置 = {}
        for 界面名称, 原始配置 in 界面集合.items():
            # 创建界面识别用的动作管理器
            识别配置 = {"查找字符串": 界面名称}
            识别配置.update(原始配置)
            self.界面识别缓存[界面名称] = (
                动作管理器类(识别配置, self.控制器, self._截图上下文, self.更新数据)
                .设置字库(self.字库缓存)
                .设置图片库(self.图片库缓存)
                .设置模型(self._模型)
            )
            # 创建界面配置对象
            配置[界面名称] = 界面管理器类(
                界面名称,
                原始配置,
                self.控制器,
                self._截图上下文,
                self.字库缓存,
                self.图片库缓存,
                self._模型,
                self.更新数据
            )
        return 配置


class 任务界面状态机类:
    def __init__(self, 环境):
        self.控制器 = 环境.控制器
        self.界面识别缓存 = 环境.界面识别缓存
        self._截图上下文 = 环境.截图上下文
        self.界面集合 = 环境.界面集合
        self.更新数据 = 环境.更新数据
        self.参数配置 = 环境.参数配置
        self.注册界面集合 = {}
        self.任务未完成 = True
        self.上下文 = {}
        self._任务超时时间 = None

    def 注册界面(self, 界面名称):
        """装饰器：注册界面处理函数"""
        def 装饰器(函数):
            self.注册界面集合[界面名称] = 函数
        return 装饰器

    def 设置超时时间(self, 秒):
        """由具体任务脚本调用，设置任务级别超时时间（秒）"""
        try:
            self._任务超时时间 = float(秒)
        except Exception:
            # 解析失败则忽略，保持原值
            pass
        return self

    def _尝试执行误触(self, 区域 = None):
        if not 区域:
            return False
        # 根据概率决定是否触发误触
        if random.random() > 0.05:
            return False
        
        # 随机选择误触类型
        误触类型 = random.choices(
            ['点击', '滑动', '等待'],
            weights=[0.7, 0, 0.3],  # 点击50%, 滑动20%, 等待30%
            k=1
        )[0]
        self.更新数据("日志", f"[误触模拟] 误触 - 类型: {误触类型}")
        
        if 误触类型 == '点击':
            self.控制器.随机点击(区域)
        elif 误触类型 == '滑动':
            pass
        else:  # 等待
            time.sleep(random.uniform(0.3, 1.5))
        
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
            self.更新数据("日志", f"未知界面截图已保存: {目标路径}")
        except Exception:
            self.更新数据("日志", "保存未知界面截图失败")

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
                    except Exception:
                        self.更新数据("日志", "播放音乐失败")

                线程 = threading.Thread(target=播放, daemon=True)
                线程.start()
                self.更新数据("日志", "正在播放提示音乐...")
            else:
                self.更新数据("日志", f"音乐文件不存在: {音乐文件路径}")
        except Exception as e:
            self.更新数据("日志", "播放音乐出错")

    def 开始(self):
        当前界面名 = None
        上一界面名 = None
        未知开始时间 = None
        未知超时时间 = 60
        任务开始时间 = time.time()

        while self.任务未完成:

            # 每轮开始时重置截图上下文
            self._截图上下文.新轮次()
            截图 = self._截图上下文.获取截图()
            已找到 = False

            # 优先检测当前/上一个界面
            优先列表 = []
            if 当前界面名:
                优先列表.append(当前界面名)
            if 上一界面名 and 上一界面名 != 当前界面名:
                优先列表.append(上一界面名)

            for 界面名称 in 优先列表 + [k for k in self.注册界面集合.keys() if k not in 优先列表]:
                if self.界面识别缓存[界面名称].查找().是否找到():
                    已找到 = True
                    if self._尝试执行误触(self.界面识别缓存[界面名称].误触区域):
                        continue
                    self.更新上下文(上次识别界面名=当前界面名)
                    当前界面名 = 界面名称
                    if 未知开始时间 is not None:
                        self.更新数据("故障", False)
                    未知开始时间 = None
                    self.注册界面集合[界面名称](self.上下文, self.界面集合[界面名称])
                    break

            if not 已找到:
                是否处于未知界面 = True
                
                # 尝试关闭未注册界面
                for 界面名称, 界面对象 in self.界面集合.items():
                    if 界面名称 in self.注册界面集合:
                        continue
                    if hasattr(界面对象.按钮, '关闭'):
                        if self.界面识别缓存[界面名称].查找().是否找到():
                            是否处于未知界面 = False
                            界面对象.按钮.关闭.点击()
                            self.更新数据("日志", f"目前位于未注册界面: {界面名称}, 直接关闭当前界面")
                            break
                if 是否处于未知界面:
                    if 未知开始时间 is None:
                        未知开始时间 = time.time()
                    经过时间 = time.time() - 未知开始时间
                    if 经过时间 >= 未知超时时间:
                        self.更新数据("故障", True)
                        self.保存未知图片(截图)
                        self.播放音乐()
                        未知开始时间 = None
                    else:
                        self.更新数据("日志", f"目前位于未知界面, {60 - 经过时间:.0f} 秒后报警")

            # 检查任务级别超时
            if self._任务超时时间 is not None:
                任务已用时 = time.time() - 任务开始时间
                if 任务已用时 >= self._任务超时时间:
                    self.更新数据("日志", f"任务已超过设定超时时间 {self._任务超时时间:.0f} 秒, 播放提示音乐")
                    self.播放音乐()
                    self.更新数据("故障", True)
                    # 为避免每轮循环反复触发，只播一次后清空超时配置
                    self._任务超时时间 = None

            time.sleep(0.1)

    def 结束(self):
        """结束状态机"""
        self.任务未完成 = False

    def 更新上下文(self, **kwargs):
        """更新上下文"""
        self.上下文.update(kwargs)

