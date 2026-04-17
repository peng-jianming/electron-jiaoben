import os
import sys
import ctypes
from ctypes import wintypes as 窗口类型
import numpy as 数组库
import win32gui as 窗口图形

用户库 = ctypes.WinDLL("user32", use_last_error=True)
图形库 = ctypes.WinDLL("gdi32", use_last_error=True)

位块复制 = 0x00CC0020
位图红绿蓝 = 0
彩色位图 = 0


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


def 位图转bgr(设备上下文句柄, 位图句柄, 宽度, 高度) -> 数组库.ndarray:
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

class 窗口工具类:
    def __init__(self, 窗口句柄: int | None = None):
        self.窗口句柄 = 窗口句柄
        self.按全屏操作 = 窗口句柄 is None
        if not self.按全屏操作 and not 窗口图形.IsWindow(窗口句柄):
            raise ValueError(f"无效窗口句柄: {窗口句柄}")

    def _规范化区域(self, 左上x, 左上y, 右下x, 右下y):
        if self.按全屏操作:
            区域宽 = 用户库.GetSystemMetrics(0)
            区域高 = 用户库.GetSystemMetrics(1)
        else:
            # 获取窗口客户区大小
            左边, 上边, 右边, 下边 = 窗口图形.GetClientRect(self.窗口句柄)
            区域宽, 区域高 = 右边 - 左边, 下边 - 上边
            if 区域宽 <= 0 or 区域高 <= 0:
                raise RuntimeError("窗口客户区尺寸无效，无法截图")

        if 左上x is None or 左上y is None or 右下x is None or 右下y is None:
            左上x, 左上y, 右下x, 右下y = 0, 0, 区域宽, 区域高

        左上x = max(0, 左上x)
        左上y = max(0, 左上y)
        右下x = min(区域宽, 右下x)
        右下y = min(区域高, 右下y)
        宽度 = 右下x - 左上x
        高度 = 右下y - 左上y
        if 宽度 <= 0 or 高度 <= 0:
            raise ValueError("截图区域无效，请检查 左上x/左上y/右下x/右下y")

        return 左上x, 左上y, 宽度, 高度

    def 后台截图(self, 左上x=None, 左上y=None, 右下x=None, 右下y=None) -> 数组库.ndarray:
        左上x, 左上y, 宽度, 高度 = self._规范化区域(左上x, 左上y, 右下x, 右下y)

        目标句柄 = 0 if self.按全屏操作 else self.窗口句柄
        窗口设备上下文 = 用户库.GetDC(目标句柄)
        if not 窗口设备上下文:
            raise ctypes.WinError(ctypes.get_last_error())

        内存设备上下文 = 图形库.CreateCompatibleDC(窗口设备上下文)
        if not 内存设备上下文:
            用户库.ReleaseDC(目标句柄, 窗口设备上下文)
            raise ctypes.WinError(ctypes.get_last_error())

        位图句柄 = 图形库.CreateCompatibleBitmap(窗口设备上下文, 宽度, 高度)
        if not 位图句柄:
            图形库.DeleteDC(内存设备上下文)
            用户库.ReleaseDC(目标句柄, 窗口设备上下文)
            raise ctypes.WinError(ctypes.get_last_error())

        旧对象句柄 = 图形库.SelectObject(内存设备上下文, 位图句柄)
        if not 旧对象句柄:
            图形库.DeleteObject(位图句柄)
            图形库.DeleteDC(内存设备上下文)
            用户库.ReleaseDC(目标句柄, 窗口设备上下文)
            raise ctypes.WinError(ctypes.get_last_error())

        try:
            是否成功 = 图形库.BitBlt(内存设备上下文, 0, 0, 宽度, 高度, 窗口设备上下文, 左上x, 左上y, 位块复制)
            if not 是否成功:
                raise ctypes.WinError(ctypes.get_last_error())
            return 位图转bgr(内存设备上下文, 位图句柄, 宽度, 高度)
        finally:
            图形库.SelectObject(内存设备上下文, 旧对象句柄)
            图形库.DeleteObject(位图句柄)
            图形库.DeleteDC(内存设备上下文)
            用户库.ReleaseDC(目标句柄, 窗口设备上下文)

    def 前台截图(self, 左上x=None, 左上y=None, 右下x=None, 右下y=None) -> 数组库.ndarray:
        左上x, 左上y, 宽度, 高度 = self._规范化区域(左上x, 左上y, 右下x, 右下y)
        if self.按全屏操作:
            源x, 源y = 左上x, 左上y
        else:
            # 获取窗口客户区左上角屏幕坐标
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
            return 位图转bgr(内存设备上下文, 位图句柄, 宽度, 高度)
        finally:
            图形库.SelectObject(内存设备上下文, 旧对象句柄)
            图形库.DeleteObject(位图句柄)
            图形库.DeleteDC(内存设备上下文)
            用户库.ReleaseDC(0, 屏幕设备上下文)

if __name__ == "__main__":
    # 示例：把下面这个句柄替换为你自己的窗口句柄（十进制整数）
    目标窗口句柄 = 77600230

    窗口工具 = 窗口工具类()
    图像帧 = 窗口工具.前台截图()
    # 后台截图（窗口设备上下文）
    # 窗口工具.鼠标移动到屏幕坐标(100, 100)
    # 图像帧 = 窗口工具.调整客户区大小(700,700)
    # 图像帧 = 窗口工具.后台截图()
    # 图像帧 = 窗口工具.打印窗口截图()

    import cv2 as 视觉库
    视觉库.imshow("窗口截图", 图像帧)
    视觉库.waitKey(0)
    视觉库.destroyAllWindows()
