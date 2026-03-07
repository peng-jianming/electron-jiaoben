import os
import json
import time
import random
import threading
import numpy as np
from PIL import Image

from .设备控制器 import 设备控制器类
from .截图管理器 import 截图管理器类
from .动作管理器 import 动作管理器类
from .界面管理器 import 界面管理器类
from 设置 import (
    字库文件路径, 模型文件路径, 音乐文件路径,
    未知截图目录, 界面配置文件路径
)



def 发现所有任务模块():
    import pkgutil
    import importlib
    """
    扫描同级的 `任务` 包下所有模块，以文件名作为任务名，收集文件下的 `创建任务` 函数。
    兼容两种包结构：
        - 顶层: core / 任务
        - 上层包: python.core / python.任务
    """
    模块名片段 = __name__.split(".")
    if len(模块名片段) >= 2:
        # 去掉最后两个片段（如 core.任务管理器），在同一父包下寻找兄弟包 任务
        父包片段 = 模块名片段[:-2]
    else:
        父包片段 = []

    if 父包片段:
        任务包名 = ".".join(父包片段 + ["任务"])
    else:
        任务包名 = "任务"

    try:
        任务包模块 = importlib.import_module(任务包名)
    except Exception as e:
        print(f"[任务发现] 导入任务包 {任务包名} 失败: {e}")
        return {}

    结果 = {}
    忽略模块名 = {'__init__', '任务管理器'}

    for 查找器, 模块全名, 是否包 in pkgutil.iter_modules(任务包模块.__path__, 任务包名 + '.'):
        # 文件名（不含 .py）即任务名
        任务名 = 模块全名.split('.')[-1]
        if 任务名 in 忽略模块名:
            continue
        try:
            模块 = importlib.import_module(模块全名)
        except Exception as e:
            print(f"[任务发现] 导入模块 {模块全名} 失败: {e}")
            continue

        创建任务 = getattr(模块, '创建任务', None)
        if 创建任务 is None:
            print(f"[任务发现] 跳过 {任务名}: 缺少 创建任务")
            continue
        if not callable(创建任务):
            print(f"[任务发现] 跳过 {任务名}: 创建任务 不可调用")
            continue

        结果[任务名] = 创建任务
        print(f"[任务发现] 已注册任务: {任务名}")

    return 结果


class 任务管理器类:
    def __init__(self, 参数集合):
        self.设备ID = 参数集合.get("设备ID")
        self.任务列表 = 参数集合.get("任务队列")
        self.更新数据 = 参数集合.get("更新数据")
        self.参数集合 = 参数集合
        
        self._任务类型映射 = 发现所有任务模块()

        # 设备控制器实例
        self.控制器 = 设备控制器类(self.设备ID)

        # 截图
        self._截图上下文 = 截图管理器类(self.控制器)

        # 资源配置
        self.字库缓存 = self.加载字库文件(字库文件路径)
        self._模型 = None

        # 界面配置
        self.界面识别缓存 = {}
        self.界面集合 = self._加载界面配置(界面配置文件路径)

        self.开始()

    # def 更新数据(self, 字段, 数据):
    #     更新数据 = self.参数集合.get("更新数据")
    #     更新数据(self.设备ID, 字段, 数据)

    def 开始(self):
        # 打印运行中
        
        for 任务名称 in self.任务列表:
            # 保存进度
            self.更新数据("当前任务", f"{任务名称}")
            self.更新数据("日志", f"{任务名称} 开始")
            任务状态机实例 = self._任务类型映射[任务名称]()
            任务状态机实例.开始(self.控制器, self.界面集合, self._截图上下文, self.界面识别缓存, self.更新数据)
            # 保存进度
            self.更新数据("当前任务", "")
            self.更新数据("日志", f"{任务名称} 完成")

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
                .设置模型(self._模型)
            )
            # 创建界面配置对象
            配置[界面名称] = 界面管理器类(
                界面名称,
                原始配置,
                self.控制器,
                self._截图上下文,
                self.字库缓存,
                self._模型,
                self.更新数据
            )
        return 配置


class 任务界面状态机类:
    def __init__(self):
        self.注册界面集合 = {}
        self.任务未完成 = True
        self.上下文 = {}

    def 注册界面(self, 界面名称):
        """装饰器：注册界面处理函数"""
        def 装饰器(函数):
            self.注册界面集合[界面名称] = 函数
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
        self.更新数据("日志", f"[误触模拟] 误触 - 类型: {误触类型}")
        
        if 误触类型 == '点击':
            self.控制器.随机点击("0,0,1280,720", (0, 0.2))
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

    def 开始(self, 控制器, 界面集合, _截图上下文, 界面识别缓存, 更新数据):
        self.控制器 = 控制器
        self.界面识别缓存 = 界面识别缓存
        self._截图上下文 = _截图上下文
        self.界面集合 = 界面集合
        self.更新数据 = 更新数据

        self.当前界面名 = None
        self.上一界面名 = None
        self._未知开始时间 = None
        self._未知超时时间 = 60

        while self.任务未完成:

            # 在当前不处于未知界面时，尝试执行随机误触, 避免干扰未知界面的操作
            if self._未知开始时间 is None:
                self._尝试执行误触()
            
            # 每轮开始时重置截图上下文
            self._截图上下文.新轮次()
            截图 = self._截图上下文.获取截图()
            已找到 = False

            # 优先检测当前/上一个界面
            优先列表 = []
            if self.当前界面名:
                优先列表.append(self.当前界面名)
            if self.上一界面名 and self.上一界面名 != self.当前界面名:
                优先列表.append(self.上一界面名)

            for 界面名称 in 优先列表 + [k for k in self.注册界面集合.keys() if k not in 优先列表]:
                if self.界面识别缓存[界面名称].查找().是否找到():
                    已找到 = True
                    self.更新上下文(上一状态=self.当前界面名)
                    self.当前界面名 = 界面名称
                    if self._未知开始时间 is not None:
                        self.更新数据("故障", False)
                    self._未知开始时间 = None
                    self.注册界面集合[界面名称](self.上下文, self.界面集合[界面名称])

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
                    if self._未知开始时间 is None:
                        self._未知开始时间 = time.time()
                    经过时间 = time.time() - self._未知开始时间
                    if 经过时间 >= self._未知超时时间:
                        self.更新数据("故障", True)
                        self.保存未知图片(截图)
                        self.播放音乐()
                        self._未知开始时间 = None
                    else:
                        self.更新数据("日志", f"目前位于未知界面, {60 - 经过时间:.0f} 秒后报警")

            time.sleep(0.2)

    def 结束(self):
        """结束状态机"""
        self.任务未完成 = False

    def 更新上下文(self, **kwargs):
        """更新上下文"""
        self.上下文.update(kwargs)

