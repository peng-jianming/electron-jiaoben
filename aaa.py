import ctypes
from ctypes import wintypes as 窗口类型
import time

import cv2 as 视觉库
import numpy as 数组库
import win32gui as 窗口图形

用户库 = ctypes.WinDLL("user32", use_last_error=True)
图形库 = ctypes.WinDLL("gdi32", use_last_error=True)

位块复制 = 0x00CC0020
位图红绿蓝 = 0
彩色位图 = 0
输入类型鼠标 = 0
鼠标事件移动 = 0x0001
仅客户端 = 0x00000001
完整渲染内容 = 0x00000002


class 位图信息头(ctypes.Structure):
    _fields_ = [
        ("位图大小", 窗口类型.DWORD),
        ("位图宽度", 窗口类型.LONG),
        ("位图高度", 窗口类型.LONG),
        ("颜色平面数", 窗口类型.WORD),
        ("位深", 窗口类型.WORD),
        ("压缩方式", 窗口类型.DWORD),
        ("图像字节大小", 窗口类型.DWORD),
        ("每米水平像素", 窗口类型.LONG),
        ("每米垂直像素", 窗口类型.LONG),
        ("使用颜色数", 窗口类型.DWORD),
        ("重要颜色数", 窗口类型.DWORD),
    ]


class 位图信息(ctypes.Structure):
    _fields_ = [
        ("位图头", 位图信息头),
        ("位图颜色", 窗口类型.DWORD * 3),
    ]


class 鼠标输入(ctypes.Structure):
    _fields_ = [
        ("位移x", 窗口类型.LONG),
        ("位移y", 窗口类型.LONG),
        ("鼠标数据", 窗口类型.DWORD),
        ("标志位", 窗口类型.DWORD),
        ("时间戳", 窗口类型.DWORD),
        ("附加信息", ctypes.c_size_t),
    ]


class _输入联合(ctypes.Union):
    _fields_ = [("鼠标输入结构", 鼠标输入)]


class 输入(ctypes.Structure):
    _anonymous_ = ("联合体",)
    _fields_ = [("输入类型", 窗口类型.DWORD), ("联合体", _输入联合)]


class 点坐标(ctypes.Structure):
    _fields_ = [("横坐标", 窗口类型.LONG), ("纵坐标", 窗口类型.LONG)]


发送输入 = 用户库.SendInput
发送输入.argtypes = (窗口类型.UINT, ctypes.POINTER(输入), ctypes.c_int)
发送输入.restype = 窗口类型.UINT
获取光标位置 = 用户库.GetCursorPos
获取光标位置.argtypes = (ctypes.POINTER(点坐标),)
获取光标位置.restype = 窗口类型.BOOL
打印窗口 = 用户库.PrintWindow
打印窗口.argtypes = (窗口类型.HWND, 窗口类型.HDC, 窗口类型.UINT)
打印窗口.restype = 窗口类型.BOOL


class 窗口工具类:
    def __init__(self, 窗口句柄: int):
        if not 窗口图形.IsWindow(窗口句柄):
            raise ValueError(f"无效窗口句柄: {窗口句柄}")
        self.窗口句柄 = 窗口句柄

    def _规范化区域(self, 左上x, 左上y, 右下x, 右下y):
        左边, 上边, 右边, 下边 = 窗口图形.GetClientRect(self.窗口句柄)
        客户区宽, 客户区高 = 右边 - 左边, 下边 - 上边
        if 客户区宽 <= 0 or 客户区高 <= 0:
            raise RuntimeError("窗口客户区尺寸无效，无法截图")

        if 左上x is None or 左上y is None or 右下x is None or 右下y is None:
            左上x, 左上y, 右下x, 右下y = 0, 0, 客户区宽, 客户区高

        左上x = max(0, 左上x)
        左上y = max(0, 左上y)
        右下x = min(客户区宽, 右下x)
        右下y = min(客户区高, 右下y)

        宽度 = 右下x - 左上x
        高度 = 右下y - 左上y
        if 宽度 <= 0 or 高度 <= 0:
            raise ValueError("截图区域无效，请检查 左上x/左上y/右下x/右下y")

        return 左上x, 左上y, 宽度, 高度

    @staticmethod
    def _获取鼠标路径(当前x, 当前y, 目标x, 目标y, 最小阈值=10):
        轨迹 = []
        距离系数表 = {
            550: 1,
            300: 2.1,
            200: 2.2,
            150: 2.3,
            100: 2.4,
            50: 2.55,
            25: 2.58,
            0: 2.6,
        }
        速度步进系数 = 2
        while True:
            距离 = ((目标x - 当前x) ** 2 + (目标y - 当前y) ** 2) ** 0.5
            if 距离 <= 最小阈值:
                break
            for 阈值, 系数 in 距离系数表.items():
                if 距离 > 阈值:
                    移动距离 = 距离 / (系数 + 速度步进系数)
                    break
            else:
                移动距离 = 1

            方向x = (目标x - 当前x) / 距离
            方向y = (目标y - 当前y) / 距离
            步进x = round(方向x * 移动距离)
            步进y = round(方向y * 移动距离)
            当前x += 步进x
            当前y += 步进y
            轨迹.append([步进x, 步进y])

        轨迹.append((目标x - 当前x, 目标y - 当前y))
        return 轨迹

    @staticmethod
    def _鼠标相对移动(位移x: int, 位移y: int):
        输入事件 = 输入(
            输入类型=输入类型鼠标,
            鼠标输入结构=鼠标输入(位移x=位移x, 位移y=位移y, 标志位=鼠标事件移动),
        )
        已发送 = 发送输入(1, ctypes.byref(输入事件), ctypes.sizeof(输入))
        if 已发送 != 1:
            raise ctypes.WinError(ctypes.get_last_error())

    def 鼠标相对平滑移动(self, 位移x: int, 位移y: int, 最小阈值: int = 10, 间隔秒: float = 0.002):
        """
        参考鼠标路径算法 + 鼠标相对移动接口的平滑相对移动。
        位移x/位移y 为总相对位移（屏幕坐标系）。
        """
        总位移x = int(位移x)
        总位移y = int(位移y)
        阈值 = max(1, int(最小阈值))
        延时 = max(0.0, float(间隔秒))

        路径 = self._获取鼠标路径(0, 0, 总位移x, 总位移y, 阈值)
        for 步进x, 步进y in 路径:
            self._鼠标相对移动(int(步进x), int(步进y))
            if 延时 > 0:
                time.sleep(延时)
        return 路径

    def 鼠标移动到屏幕坐标(self, 目标x: int, 目标y: int, 最小阈值: int = 10, 间隔秒: float = 0.002):
        """
        从当前鼠标位置平滑移动到屏幕绝对坐标 (x, y)。
        """
        光标点 = 点坐标()
        是否成功 = 获取光标位置(ctypes.byref(光标点))
        if not 是否成功:
            raise ctypes.WinError(ctypes.get_last_error())

        目标x = int(目标x)
        目标y = int(目标y)
        位移x = 目标x - int(光标点.横坐标)
        位移y = 目标y - int(光标点.纵坐标)
        return self.鼠标相对平滑移动(位移x, 位移y, 最小阈值=最小阈值, 间隔秒=间隔秒)

    @staticmethod
    def _位图转蓝绿红(设备上下文句柄, 位图句柄, 宽度, 高度) -> 数组库.ndarray:
        行填充 = (4 - (宽度 * 3) % 4) % 4
        行字节数 = 宽度 * 3 + 行填充
        图像字节数 = 高度 * 行字节数

        位图信息实例 = 位图信息()
        位图信息实例.位图头.位图大小 = ctypes.sizeof(位图信息头)
        位图信息实例.位图头.位图宽度 = 宽度
        位图信息实例.位图头.位图高度 = -高度
        位图信息实例.位图头.颜色平面数 = 1
        位图信息实例.位图头.位深 = 24
        位图信息实例.位图头.压缩方式 = 位图红绿蓝
        位图信息实例.位图头.图像字节大小 = 图像字节数

        缓冲区 = ctypes.create_string_buffer(图像字节数)
        扫描行数 = 图形库.GetDIBits(
            设备上下文句柄, 位图句柄, 0, 高度, 缓冲区, ctypes.byref(位图信息实例), 彩色位图
        )
        if 扫描行数 == 0:
            raise ctypes.WinError(ctypes.get_last_error())

        像素数组 = 数组库.frombuffer(缓冲区, dtype=数组库.uint8).reshape((高度, 行字节数))
        图像蓝绿红 = 像素数组[:, : 宽度 * 3].reshape((高度, 宽度, 3))
        return 图像蓝绿红.copy()

    def 移动窗口(self, 目标x: int, 目标y: int, 需要重绘: bool = True):
        """
        移动窗口到指定屏幕坐标，保持窗口当前尺寸不变。
        """
        左边, 上边, 右边, 下边 = 窗口图形.GetWindowRect(self.窗口句柄)
        宽度 = 右边 - 左边
        高度 = 下边 - 上边
        if 宽度 <= 0 or 高度 <= 0:
            raise RuntimeError("窗口尺寸无效，无法移动")

        try:
            窗口图形.MoveWindow(self.窗口句柄, int(目标x), int(目标y), 宽度, 高度, 需要重绘)
        except 窗口图形.error as 错误:
            raise RuntimeError(f"移动窗口失败: {错误}") from 错误
        return 窗口图形.GetWindowRect(self.窗口句柄)

    def 调整客户区大小(self, 目标客户区宽: int, 目标客户区高: int, 需要重绘: bool = True):
        """
        调整窗口客户区（工作区）尺寸，不改变当前窗口左上角位置。
        """
        目标客户区宽 = int(目标客户区宽)
        目标客户区高 = int(目标客户区高)
        if 目标客户区宽 <= 0 or 目标客户区高 <= 0:
            raise ValueError("客户区尺寸必须大于 0")

        窗口左, 窗口上, 窗口右, 窗口下 = 窗口图形.GetWindowRect(self.窗口句柄)
        当前客户左, 当前客户上, 当前客户右, 当前客户下 = 窗口图形.GetClientRect(
            self.窗口句柄
        )
        当前客户区宽 = 当前客户右 - 当前客户左
        当前客户区高 = 当前客户下 - 当前客户上
        if 当前客户区宽 <= 0 or 当前客户区高 <= 0:
            raise RuntimeError("当前客户区尺寸无效，无法调整")

        边框宽 = (窗口右 - 窗口左) - 当前客户区宽
        边框高 = (窗口下 - 窗口上) - 当前客户区高
        目标窗口宽 = 目标客户区宽 + 边框宽
        目标窗口高 = 目标客户区高 + 边框高
        if 目标窗口宽 <= 0 or 目标窗口高 <= 0:
            raise RuntimeError("计算后的窗口尺寸无效，请检查参数")

        try:
            窗口图形.MoveWindow(
                self.窗口句柄, 窗口左, 窗口上, 目标窗口宽, 目标窗口高, 需要重绘
            )
        except 窗口图形.error as 错误:
            raise RuntimeError(f"调整客户区尺寸失败: {错误}") from 错误
        return 窗口图形.GetClientRect(self.窗口句柄)

    def 后台截图(self, 左上x=None, 左上y=None, 右下x=None, 右下y=None) -> 数组库.ndarray:
        左上x, 左上y, 宽度, 高度 = self._规范化区域(左上x, 左上y, 右下x, 右下y)

        窗口设备上下文 = 用户库.GetDC(self.窗口句柄)
        if not 窗口设备上下文:
            raise ctypes.WinError(ctypes.get_last_error())

        内存设备上下文 = 图形库.CreateCompatibleDC(窗口设备上下文)
        if not 内存设备上下文:
            用户库.ReleaseDC(self.窗口句柄, 窗口设备上下文)
            raise ctypes.WinError(ctypes.get_last_error())

        位图句柄 = 图形库.CreateCompatibleBitmap(窗口设备上下文, 宽度, 高度)
        if not 位图句柄:
            图形库.DeleteDC(内存设备上下文)
            用户库.ReleaseDC(self.窗口句柄, 窗口设备上下文)
            raise ctypes.WinError(ctypes.get_last_error())

        旧对象句柄 = 图形库.SelectObject(内存设备上下文, 位图句柄)
        if not 旧对象句柄:
            图形库.DeleteObject(位图句柄)
            图形库.DeleteDC(内存设备上下文)
            用户库.ReleaseDC(self.窗口句柄, 窗口设备上下文)
            raise ctypes.WinError(ctypes.get_last_error())

        try:
            是否成功 = 图形库.BitBlt(内存设备上下文, 0, 0, 宽度, 高度, 窗口设备上下文, 左上x, 左上y, 位块复制)
            if not 是否成功:
                raise ctypes.WinError(ctypes.get_last_error())
            return self._位图转蓝绿红(内存设备上下文, 位图句柄, 宽度, 高度)
        finally:
            图形库.SelectObject(内存设备上下文, 旧对象句柄)
            图形库.DeleteObject(位图句柄)
            图形库.DeleteDC(内存设备上下文)
            用户库.ReleaseDC(self.窗口句柄, 窗口设备上下文)

    def 前台截图(self, 左上x=None, 左上y=None, 右下x=None, 右下y=None) -> 数组库.ndarray:
        左上x, 左上y, 宽度, 高度 = self._规范化区域(左上x, 左上y, 右下x, 右下y)
        屏幕x, 屏幕y = 窗口图形.ClientToScreen(self.窗口句柄, (0, 0))
        源x = 屏幕x + 左上x
        源y = 屏幕y + 左上y

        屏幕宽 = 用户库.GetSystemMetrics(0)
        屏幕高 = 用户库.GetSystemMetrics(1)
        if 源x >= 屏幕宽:
            raise ValueError(f"起始坐标超过屏幕横轴 {源x} >= {屏幕宽}")
        if 源y >= 屏幕高:
            raise ValueError(f"起始坐标超过屏幕纵轴 {源y} >= {屏幕高}")

        屏幕设备上下文 = 用户库.GetDC(0)
        if not 屏幕设备上下文:
            raise ctypes.WinError(ctypes.get_last_error())

        内存设备上下文 = 图形库.CreateCompatibleDC(屏幕设备上下文)
        if not 内存设备上下文:
            用户库.ReleaseDC(0, 屏幕设备上下文)
            raise ctypes.WinError(ctypes.get_last_error())

        位图句柄 = 图形库.CreateCompatibleBitmap(屏幕设备上下文, 宽度, 高度)
        if not 位图句柄:
            图形库.DeleteDC(内存设备上下文)
            用户库.ReleaseDC(0, 屏幕设备上下文)
            raise ctypes.WinError(ctypes.get_last_error())

        旧对象句柄 = 图形库.SelectObject(内存设备上下文, 位图句柄)
        if not 旧对象句柄:
            图形库.DeleteObject(位图句柄)
            图形库.DeleteDC(内存设备上下文)
            用户库.ReleaseDC(0, 屏幕设备上下文)
            raise ctypes.WinError(ctypes.get_last_error())

        try:
            是否成功 = 图形库.BitBlt(内存设备上下文, 0, 0, 宽度, 高度, 屏幕设备上下文, 源x, 源y, 位块复制)
            if not 是否成功:
                raise ctypes.WinError(ctypes.get_last_error())
            return self._位图转蓝绿红(内存设备上下文, 位图句柄, 宽度, 高度)
        finally:
            图形库.SelectObject(内存设备上下文, 旧对象句柄)
            图形库.DeleteObject(位图句柄)
            图形库.DeleteDC(内存设备上下文)
            用户库.ReleaseDC(0, 屏幕设备上下文)

    def 打印窗口截图(self, 左上x=None, 左上y=None, 右下x=None, 右下y=None, 完整渲染: bool = True) -> 数组库.ndarray:
        """
        使用打印窗口接口进行后台截图（尽量获取遮挡/最小化窗口内容）。
        坐标参数使用客户区坐标系，行为与后台截图保持一致。
        """
        裁剪x, 裁剪y, 裁剪宽, 裁剪高 = self._规范化区域(左上x, 左上y, 右下x, 右下y)
        _, _, 客户区宽, 客户区高 = self._规范化区域(0, 0, None, None)

        窗口设备上下文 = 用户库.GetDC(self.窗口句柄)
        if not 窗口设备上下文:
            raise ctypes.WinError(ctypes.get_last_error())

        内存设备上下文 = 图形库.CreateCompatibleDC(窗口设备上下文)
        if not 内存设备上下文:
            用户库.ReleaseDC(self.窗口句柄, 窗口设备上下文)
            raise ctypes.WinError(ctypes.get_last_error())

        位图句柄 = 图形库.CreateCompatibleBitmap(窗口设备上下文, 客户区宽, 客户区高)
        if not 位图句柄:
            图形库.DeleteDC(内存设备上下文)
            用户库.ReleaseDC(self.窗口句柄, 窗口设备上下文)
            raise ctypes.WinError(ctypes.get_last_error())

        旧对象句柄 = 图形库.SelectObject(内存设备上下文, 位图句柄)
        if not 旧对象句柄:
            图形库.DeleteObject(位图句柄)
            图形库.DeleteDC(内存设备上下文)
            用户库.ReleaseDC(self.窗口句柄, 窗口设备上下文)
            raise ctypes.WinError(ctypes.get_last_error())

        try:
            标志位 = 仅客户端 | (完整渲染内容 if 完整渲染 else 0)
            是否成功 = 打印窗口(self.窗口句柄, 内存设备上下文, 标志位)
            if not 是否成功:
                raise RuntimeError("打印窗口接口截图失败，目标窗口可能不支持该方式")

            完整图像 = self._位图转蓝绿红(内存设备上下文, 位图句柄, 客户区宽, 客户区高)
            return 完整图像[裁剪y : 裁剪y + 裁剪高, 裁剪x : 裁剪x + 裁剪宽].copy()
        finally:
            图形库.SelectObject(内存设备上下文, 旧对象句柄)
            图形库.DeleteObject(位图句柄)
            图形库.DeleteDC(内存设备上下文)
            用户库.ReleaseDC(self.窗口句柄, 窗口设备上下文)


if __name__ == "__main__":
    # 示例：把下面这个句柄替换为你自己的窗口句柄（十进制整数）
    目标窗口句柄 = 3739680

    if 目标窗口句柄 == 0:
        raise SystemExit("请先把 目标窗口句柄 改成目标窗口句柄")

    窗口工具 = 窗口工具类(目标窗口句柄)
    # 前台截图（可见内容）
    # 图像帧 = 窗口工具.前台截图()
    # 后台截图（窗口设备上下文）
    # 窗口工具.鼠标移动到屏幕坐标(100, 100)
    # 图像帧 = 窗口工具.调整客户区大小(700,700)
    图像帧 = 窗口工具.后台截图()
    # 图像帧 = 窗口工具.打印窗口截图()

    
    视觉库.imshow("窗口截图", 图像帧)
    视觉库.waitKey(0)
    视觉库.destroyAllWindows()
