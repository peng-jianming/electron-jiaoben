from 驱动加载器 import 驱动加载器
import random
import os
import ctypes
import time
from ctypes import wintypes

内核库 = ctypes.WinDLL("kernel32", use_last_error=True)
用户库 = ctypes.WinDLL("user32", use_last_error=True)

创建文件A = 内核库.CreateFileA
创建文件A.argtypes = [
    wintypes.LPCSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
]
创建文件A.restype = wintypes.HANDLE

通用读 = 0x80000000
通用写 = 0x40000000

打开_已存在 = 3
无效句柄值 = wintypes.HANDLE(-1).value

设备IO控制 = 内核库.DeviceIoControl
设备IO控制.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPVOID,
]
设备IO控制.restype = wintypes.BOOL






# 与 C 宏一致的设备类型
设备类型_键鼠 = 0x8000  # 键鼠设备类型

# 与 C 宏一致的功能码基值
键鼠控制码基值 = 0x800    # 功能码基值

# 方法和访问权限（与 C 宏一致）
方法_缓冲 = 0x0
访问_任意 = 0x0

# 定义 CTL_CODE 宏
def 生成控制码(设备类型, 功能码, 方法, 访问权限):
    return (设备类型 << 16) | (访问权限 << 14) | (功能码 << 2) | 方法

# 定义 CTL_CODE_KEYMOUSE 宏
def 生成键鼠控制码(索引):
    return 生成控制码(设备类型_键鼠, 键鼠控制码基值 + 索引, 方法_缓冲, 访问_任意)

# 与 C 宏一致的 IOCTL 定义
IOCTL_键盘 = 生成键鼠控制码(0)  # 键盘 IOCTL
IOCTL_鼠标 = 生成键鼠控制码(1)  # 鼠标 IOCTL


# 鼠标按钮标志
鼠标_左键按下 = 0x0001
鼠标_左键抬起 = 0x0002
鼠标_右键按下 = 0x0004
鼠标_右键抬起 = 0x0008
鼠标_中键按下 = 0x0010
鼠标_中键抬起 = 0x0020

# 鼠标移动标志
鼠标_相对移动 = 0x00
鼠标_绝对移动 = 0x01


获取系统指标 = 用户库.GetSystemMetrics
获取系统指标.argtypes = [wintypes.INT]
获取系统指标.restype = wintypes.INT

系统指标_屏幕宽 = 0
系统指标_屏幕高 = 1

扩展键码集 = {0x68, 0x69, 0x6A, 0x6B, 0x6C, 0x6D, 0x6E, 0x6F, 0x26, 0x28, 0x25, 0x27}

虚拟键码集 = {
    'backspace': 0x08,
    'tab': 0x09,
    'clear': 0x0C,
    'enter': 0x0D,
    'shift': 0x10,
    'ctrl': 0x11,
    'alt': 0x12,
    'pause': 0x13,
    'caps_lock': 0x14,
    'esc': 0x1B,
    'spacebar': 0x20,
    'space': 0x20,
    'page_up': 0x21,
    'page_down': 0x22,
    'end': 0x23,
    'home': 0x24,
    'left': 0x25,
    'up': 0x26,
    'right': 0x27,
    'down': 0x28,
    'select': 0x29,
    'print': 0x2A,
    'execute': 0x2B,
    'print_screen': 0x2C,
    'ins': 0x2D,
    'del': 0x2E,
    'help': 0x2F,
    '0': 0x30,
    '1': 0x31,
    '2': 0x32,
    '3': 0x33,
    '4': 0x34,
    '5': 0x35,
    '6': 0x36,
    '7': 0x37,
    '8': 0x38,
    '9': 0x39,
    'a': 0x41,
    'b': 0x42,
    'c': 0x43,
    'd': 0x44,
    'e': 0x45,
    'f': 0x46,
    'g': 0x47,
    'h': 0x48,
    'i': 0x49,
    'j': 0x4A,
    'k': 0x4B,
    'l': 0x4C,
    'm': 0x4D,
    'n': 0x4E,
    'o': 0x4F,
    'p': 0x50,
    'q': 0x51,
    'r': 0x52,
    's': 0x53,
    't': 0x54,
    'u': 0x55,
    'v': 0x56,
    'w': 0x57,
    'x': 0x58,
    'y': 0x59,
    'z': 0x5A,
    'numpad_0': 0x60,
    'numpad_1': 0x61,
    'numpad_2': 0x62,
    'numpad_3': 0x63,
    'numpad_4': 0x64,
    'numpad_5': 0x65,
    'numpad_6': 0x66,
    'numpad_7': 0x67,
    'numpad_8': 0x68,
    'numpad_9': 0x69,
    'multiply_key': 0x6A,
    'add_key': 0x6B,
    'separator_key': 0x6C,
    'subtract_key': 0x6D,
    'decimal_key': 0x6E,
    'divide_key': 0x6F,
    'f1': 0x70,
    'f2': 0x71,
    'f3': 0x72,
    'f4': 0x73,
    'f5': 0x74,
    'f6': 0x75,
    'f7': 0x76,
    'f8': 0x77,
    'f9': 0x78,
    'f10': 0x79,
    'f11': 0x7A,
    'f12': 0x7B,
    'f13': 0x7C,
    'f14': 0x7D,
    'f15': 0x7E,
    'f16': 0x7F,
    'f17': 0x80,
    'f18': 0x81,
    'f19': 0x82,
    'f20': 0x83,
    'f21': 0x84,
    'f22': 0x85,
    'f23': 0x86,
    'f24': 0x87,
    'num_lock': 0x90,
    'scroll_lock': 0x91,
    'left_shift': 0xA0,
    'right_shift ': 0xA1,
    'left_control': 0xA2,
    'right_control': 0xA3,
    'left_menu': 0xA4,
    'right_menu': 0xA5,
    'browser_back': 0xA6,
    'browser_forward': 0xA7,
    'browser_refresh': 0xA8,
    'browser_stop': 0xA9,
    'browser_search': 0xAA,
    'browser_favorites': 0xAB,
    'browser_start_and_home': 0xAC,
    'volume_mute': 0xAD,
    'volume_Down': 0xAE,
    'volume_up': 0xAF,
    'next_track': 0xB0,
    'previous_track': 0xB1,
    'stop_media': 0xB2,
    'play/pause_media': 0xB3,
    'start_mail': 0xB4,
    'select_media': 0xB5,
    'start_application_1': 0xB6,
    'start_application_2': 0xB7,
    'attn_key': 0xF6,
    'crsel_key': 0xF7,
    'exsel_key': 0xF8,
    'play_key': 0xFA,
    'zoom_key': 0xFB,
    'clear_key': 0xFE,
    '+': 0xBB,
    ',': 0xBC,
    '-': 0xBD,
    '.': 0xBE,
    '/': 0xBF,
    '`': 0xC0,
    ';': 0xBA,
    '[': 0xDB,
    '\\': 0xDC,
    ']': 0xDD,
    "'": 0xDE,
    '`': 0xC0
}

# 定义鼠标输入数据结构
class _按钮结构(ctypes.Structure):
    _fields_ = [
        ("按钮标志", wintypes.USHORT),
        ("按钮数据", wintypes.USHORT),
    ]

class _按钮联合(ctypes.Union):
    _fields_ = [
        ("按钮值", wintypes.ULONG),
        ("按钮结构", _按钮结构),
    ]

class 鼠标输入数据(ctypes.Structure):
    _fields_ = [
        ("设备单元ID", wintypes.USHORT),
        ("标志", wintypes.USHORT),
        ("按钮联合", _按钮联合),
        ("原始按钮", wintypes.ULONG),
        ("最后X", wintypes.LONG),
        ("最后Y", wintypes.LONG),
        ("附加信息", wintypes.ULONG),
    ]



# 定义键盘输入数据结构
class 键盘输入数据(ctypes.Structure):
    _fields_ = [
        ("设备单元ID", wintypes.USHORT),
        ("扫描码", wintypes.USHORT),
        ("标志", wintypes.USHORT),
        ("保留", wintypes.USHORT),
        ("附加信息", wintypes.ULONG),
    ]

映射虚拟键 = 用户库.MapVirtualKeyW
映射虚拟键.argtypes = [wintypes.UINT, wintypes.UINT]
映射虚拟键.restype = wintypes.UINT

映射方式_虚拟键到扫描码 = 0

# 键盘输入标志
键盘标志_按下 = 0x00  # 按下
键盘标志_弹起 = 0x01  # 弹起
键盘标志_E0 = 0x02
键盘标志_E1 = 0x04

键盘标志_键按下 = 键盘标志_按下
键盘标志_键弹起 = 键盘标志_弹起



def 获取鼠标移动轨迹(当前x, 当前y,目标x, 目标y, 最小距离阈值=10):
    
    轨迹列表 = [] 
    距离步长映射 = {
        550: 1,
        300: 2.1,
        200: 2.2,
        150: 2.3,
        100: 2.4,
        50: 2.55,
        25:2.58,
        0:2.6
    }
    步长增量 = 2
    while True:
        # 计算当前点到目标点的距离
        距离 = ((目标x - 当前x) ** 2 + (目标y - 当前y) ** 2) ** 0.5
        # 检查是否到达目标
        # 最小距离阈值 越小,移动越平滑,但越慢
        if 距离 <= 最小距离阈值:
            break
        for 距离阈值, 步长系数 in 距离步长映射.items():

            # 根据距离决定移动步长
            if 距离 > 距离阈值:  # 距离较远
                步长 = 距离 / (步长系数 + 步长增量)  # 大步移动
                break
        else:
            步长 = 1
        # 计算方向向量并进行移动
        方向x = (目标x - 当前x) / 距离
        方向y = (目标y - 当前y) / 距离

        # 更新当前位置
        步长x = round(方向x * 步长)
        步长y = round(方向y * 步长)

        当前x += 步长x
        当前y += 步长y

        # 添加当前位置到轨迹
        轨迹列表.append([步长x, 步长y])  # 取整以模拟实际鼠标位置

    # 添加最终目的地
    轨迹列表.append((目标x-当前x, 目标y-当前y))

    return 轨迹列表


class 鼠标键盘控制器:
    驱动加载器 = None
    def __init__(self, 窗口句柄: int | None = None):
        # 未传句柄或传 0 都视为“按全屏操作”
        self.窗口句柄 = 窗口句柄 if 窗口句柄 else None
        self.按全屏操作 = self.窗口句柄 is None
        self.键鼠驱动句柄 = self.安装驱动()
        if self.键鼠驱动句柄 is None:
            raise Exception("安装驱动失败")

    def _发送控制命令(self, 控制码, 输入结构):
        输出字节数 = wintypes.DWORD()
        res = 设备IO控制(
            self.键鼠驱动句柄,
            控制码,
            ctypes.byref(输入结构),
            ctypes.sizeof(输入结构),
            None,
            0,
            ctypes.byref(输出字节数),
            None,
        )
        if not res:
            raise ctypes.WinError(ctypes.get_last_error())

    def 安装驱动(self):
        if 鼠标键盘控制器.驱动加载器 is None:
            鼠标键盘控制器.驱动加载器 = 驱动加载器(os.path.abspath(os.path.join(os.path.dirname(__file__), "../", "dxkm.sys")))

        # 安装/卸载/启动在内核驱动场景下经常存在时序延迟
        # 这里做少量重试，避免“刚卸载完就安装”的短暂过渡态失败。
        for _ in range(3):
            try:
                鼠标键盘控制器.驱动加载器.卸载()

                if not 鼠标键盘控制器.驱动加载器.安装():
                    print("鼠标键盘驱动安装失败")
                    time.sleep(2)
                    continue
                if not 鼠标键盘控制器.驱动加载器.启动():
                    print("鼠标键盘驱动启动失败")
                    time.sleep(2)
                    continue

                # 启动成功后，设备节点/符号链接可能还没完全准备好
                print("鼠标键盘驱动启动成功")
                for 打开尝试次数 in range(10):
                    句柄 = 创建文件A(
                        b"\\\\.\\kmclass",
                        通用读 | 通用写,
                        0,
                        None,
                        打开_已存在,
                        0,
                        None
                    )
                    if 句柄 != 无效句柄值:
                        return 句柄
                    time.sleep(1)
                return None
            except Exception:
                # 驱动安装/启动失败时，直接重试外层循环
                time.sleep(2)
                continue

        return None

    def 卸载驱动(self):
        if 鼠标键盘控制器.驱动加载器.停止():
            if 鼠标键盘控制器.驱动加载器.卸载():
                self.键鼠驱动句柄 = None
                print("鼠标键盘驱动卸载成功")
            else:
                print("鼠标键盘驱动卸载失败")
        else:
            print("鼠标键盘驱动停止失败")

    def 鼠标左键按下(self):
        输入 = 鼠标输入数据()
        输入.按钮联合.按钮结构.按钮标志 = 鼠标_左键按下
        self._发送控制命令(IOCTL_鼠标, 输入)

    def 鼠标左键抬起(self):
        输入 = 鼠标输入数据()
        输入.按钮联合.按钮结构.按钮标志 = 鼠标_左键抬起
        self._发送控制命令(IOCTL_鼠标, 输入)

    def 鼠标右键按下(self):
        输入 = 鼠标输入数据()
        输入.按钮联合.按钮结构.按钮标志 = 鼠标_右键按下
        self._发送控制命令(IOCTL_鼠标, 输入)

    def 鼠标右键抬起(self):
        输入 = 鼠标输入数据()
        输入.按钮联合.按钮结构.按钮标志 = 鼠标_右键抬起
        self._发送控制命令(IOCTL_鼠标, 输入)

    def 鼠标中键按下(self):
        输入 = 鼠标输入数据()
        输入.按钮联合.按钮结构.按钮标志 = 鼠标_中键按下
        self._发送控制命令(IOCTL_鼠标, 输入)

    def 鼠标中键抬起(self):
        输入 = 鼠标输入数据()
        输入.按钮联合.按钮结构.按钮标志 = 鼠标_中键抬起
        self._发送控制命令(IOCTL_鼠标, 输入)

    def 鼠标相对移动(self, x, y):
        输入 = 鼠标输入数据()
        输入.标志 = 鼠标_相对移动
        输入.最后X = x
        输入.最后Y = y
        self._发送控制命令(IOCTL_鼠标, 输入)

    def 鼠标绝对移动(self, x, y):
        输入 = 鼠标输入数据()
        输入.标志 = 鼠标_绝对移动
        屏幕宽 = 获取系统指标(系统指标_屏幕宽)
        屏幕高 = 获取系统指标(系统指标_屏幕高)
        输入.最后X = int(x * 0xFFFF / 屏幕宽)
        输入.最后Y = int(y * 0xFFFF / 屏幕高)
        self._发送控制命令(IOCTL_鼠标, 输入)

    def 按键按下(self, 键码):
        # 按下键码可以是虚拟键码或扫描码
        输入 = 键盘输入数据()
        虚拟键码 = 虚拟键码集.get(键码.lower(), 键码)
        输入.扫描码 = 映射虚拟键(虚拟键码, 映射方式_虚拟键到扫描码)
        if 键码 in 扩展键码集:
            输入.标志 = 键盘标志_键按下 | 0x0002  # 添加扩展标志,发送键值码
        else:
            输入.标志 = 键盘标志_键按下

        self._发送控制命令(IOCTL_键盘, 输入)

    def 按键抬起(self, 键码):
        # 抬起键码可以是虚拟键码或扫描码
        输入 = 键盘输入数据()
        虚拟键码 = 虚拟键码集.get(键码.lower(), 键码)
        if 键码 in 扩展键码集:
            输入.标志 = 键盘标志_键弹起 | 0x0002  # 添加扩展标志,发送键值码
        else:
            输入.标志 = 键盘标志_键弹起
        输入.扫描码 = 映射虚拟键(虚拟键码, 映射方式_虚拟键到扫描码)
        self._发送控制命令(IOCTL_键盘, 输入)


    def 鼠标左键点击(self):
        self.鼠标左键按下()
        time.sleep(random.uniform(0.1, 0.3))
        self.鼠标左键抬起()

    def 鼠标右键点击(self):
        self.鼠标右键按下()
        time.sleep(random.uniform(0.1, 0.3))
        self.鼠标右键抬起()

    def 鼠标中键点击(self):
        self.鼠标中键按下()
        time.sleep(random.uniform(0.1, 0.3))
        self.鼠标中键抬起()

    def 按键点击(self, 键码):
        # 按键点击可以是虚拟键码或扫描码
        self.按键按下(键码)
        time.sleep(random.uniform(0.1, 0.3))
        self.按键抬起(键码)

    def 获取当前鼠标位置(self):
        class 点结构(ctypes.Structure):
            _fields_ = [
                ("x", wintypes.LONG),
                ("y", wintypes.LONG)
            ]

        点 = 点结构()
        用户库.GetCursorPos(ctypes.byref(点))
        return 点.x, 点.y

    def 获取窗口对应屏幕坐标(self, x, y):
        # 此时的x,y代表的是窗口的坐标(self.窗口句柄),需要转为屏幕的坐标
        点 = ctypes.wintypes.POINT()
        点.x = x
        点.y = y
        for i in range(10):
            is_ok: bool = 用户库.ClientToScreen(self.窗口句柄, ctypes.byref(点))
            if not is_ok:
                raise Exception('call ClientToScreen failed')
            if 点.x !=0 and 点.y != 0:
                return 点.x, 点.y
            time.sleep(0.01)


    def 鼠标移动(self, x, y, 模拟真实移动=True, 最小距离阈值=10):
        当前x, 当前y = self.获取当前鼠标位置()
        # 按全屏操作时，(x,y) 即为屏幕坐标；否则将窗口坐标转为屏幕坐标
        if self.按全屏操作:
            目标x, 目标y = x, y
        else:
            目标x, 目标y = self.获取窗口对应屏幕坐标(x, y)

        if 模拟真实移动:
            轨迹列表 = 获取鼠标移动轨迹(当前x, 当前y, 目标x, 目标y, 最小距离阈值)
            for 步长x, 步长y in 轨迹列表:
                self.鼠标相对移动(步长x, 步长y)
                time.sleep(0.002)
        else:
            self.鼠标相对移动(目标x - 当前x, 目标y - 当前y)

    def 鼠标滑动(self, x1, y1, x2, y2, 模拟真实滑动=True, 最小距离阈值=10):
        pass


if __name__ == "__main__":
    鼠标键盘控制 = 鼠标键盘控制器(77600230)
    # 鼠标键盘控制.鼠标移动(100,100, 模拟真实移动=True, 最小距离阈值=10)
    # time.sleep(1)
    # 鼠标键盘控制.鼠标绝对移动(100,100)
    # 鼠标键盘控制.鼠标相对移动(-100,500)
    鼠标键盘控制.鼠标移动(100,100)
    # 鼠标键盘控制.按键点击(0x28)