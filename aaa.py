import ctypes
from ctypes import wintypes
import time

import cv2
import numpy as np
import win32gui

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

SRCCOPY = 0x00CC0020
BI_RGB = 0
DIB_RGB_COLORS = 0
INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
PW_CLIENTONLY = 0x00000001
PW_RENDERFULLCONTENT = 0x00000002


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", wintypes.DWORD * 3),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


SendInput = user32.SendInput
SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
SendInput.restype = wintypes.UINT
GetCursorPos = user32.GetCursorPos
GetCursorPos.argtypes = (ctypes.POINTER(POINT),)
GetCursorPos.restype = wintypes.BOOL
PrintWindow = user32.PrintWindow
PrintWindow.argtypes = (wintypes.HWND, wintypes.HDC, wintypes.UINT)
PrintWindow.restype = wintypes.BOOL


class WindowTool:
    def __init__(self, hwnd: int):
        if not win32gui.IsWindow(hwnd):
            raise ValueError(f"无效窗口句柄: {hwnd}")
        self.hwnd = hwnd

    def _normalize_rect(self, x1, y1, x2, y2):
        left, top, right, bottom = win32gui.GetClientRect(self.hwnd)
        client_w, client_h = right - left, bottom - top
        if client_w <= 0 or client_h <= 0:
            raise RuntimeError("窗口客户区尺寸无效，无法截图")

        if x1 is None or y1 is None or x2 is None or y2 is None:
            x1, y1, x2, y2 = 0, 0, client_w, client_h

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(client_w, x2)
        y2 = min(client_h, y2)

        width = x2 - x1
        height = y2 - y1
        if width <= 0 or height <= 0:
            raise ValueError("截图区域无效，请检查 x1/y1/x2/y2")

        return x1, y1, width, height

    @staticmethod
    def _get_mouse_path(current_x, current_y, target_x, target_y, min_n=10):
        trajectory = []
        dct = {
            550: 1,
            300: 2.1,
            200: 2.2,
            150: 2.3,
            100: 2.4,
            50: 2.55,
            25: 2.58,
            0: 2.6,
        }
        step_v = 2
        while True:
            distance = ((target_x - current_x) ** 2 + (target_y - current_y) ** 2) ** 0.5
            if distance <= min_n:
                break
            for k, v in dct.items():
                if distance > k:
                    move_distance = distance / (v + step_v)
                    break
            else:
                move_distance = 1

            direction_x = (target_x - current_x) / distance
            direction_y = (target_y - current_y) / distance
            step_x = round(direction_x * move_distance)
            step_y = round(direction_y * move_distance)
            current_x += step_x
            current_y += step_y
            trajectory.append([step_x, step_y])

        trajectory.append((target_x - current_x, target_y - current_y))
        return trajectory

    @staticmethod
    def _mouse_move_relative(dx: int, dy: int):
        event = INPUT(type=INPUT_MOUSE, mi=MOUSEINPUT(dx=dx, dy=dy, dwFlags=MOUSEEVENTF_MOVE))
        sent = SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT))
        if sent != 1:
            raise ctypes.WinError(ctypes.get_last_error())

    def move_mouse_relative(self, dx: int, dy: int, min_n: int = 10, interval: float = 0.002):
        """
        参考 get_mouse_path + MouseMoveRELATIVE 的平滑相对移动。
        dx/dy 为总相对位移（屏幕坐标系）。
        """
        total_dx = int(dx)
        total_dy = int(dy)
        threshold = max(1, int(min_n))
        delay = max(0.0, float(interval))

        path = self._get_mouse_path(0, 0, total_dx, total_dy, threshold)
        for step_x, step_y in path:
            self._mouse_move_relative(int(step_x), int(step_y))
            if delay > 0:
                time.sleep(delay)
        return path

    def move_mouse_to_screen(self, x: int, y: int, min_n: int = 10, interval: float = 0.002):
        """
        从当前鼠标位置平滑移动到屏幕绝对坐标 (x, y)。
        """
        pt = POINT()
        ok = GetCursorPos(ctypes.byref(pt))
        if not ok:
            raise ctypes.WinError(ctypes.get_last_error())

        target_x = int(x)
        target_y = int(y)
        dx = target_x - int(pt.x)
        dy = target_y - int(pt.y)
        return self.move_mouse_relative(dx, dy, min_n=min_n, interval=interval)

    @staticmethod
    def _bitmap_to_bgr(h_dc, h_bitmap, width, height) -> np.ndarray:
        padding = (4 - (width * 3) % 4) % 4
        line_size = width * 3 + padding
        image_size = height * line_size

        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 24
        bmi.bmiHeader.biCompression = BI_RGB
        bmi.bmiHeader.biSizeImage = image_size

        buffer = ctypes.create_string_buffer(image_size)
        scan_lines = gdi32.GetDIBits(
            h_dc, h_bitmap, 0, height, buffer, ctypes.byref(bmi), DIB_RGB_COLORS
        )
        if scan_lines == 0:
            raise ctypes.WinError(ctypes.get_last_error())

        arr = np.frombuffer(buffer, dtype=np.uint8).reshape((height, line_size))
        img_bgr = arr[:, : width * 3].reshape((height, width, 3))
        return img_bgr.copy()

    def move_window(self, x: int, y: int, repaint: bool = True):
        """
        移动窗口到指定屏幕坐标，保持窗口当前尺寸不变。
        """
        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
        width = right - left
        height = bottom - top
        if width <= 0 or height <= 0:
            raise RuntimeError("窗口尺寸无效，无法移动")

        try:
            win32gui.MoveWindow(self.hwnd, int(x), int(y), width, height, repaint)
        except win32gui.error as e:
            raise RuntimeError(f"移动窗口失败: {e}") from e
        return win32gui.GetWindowRect(self.hwnd)

    def resize_client_area(self, client_width: int, client_height: int, repaint: bool = True):
        """
        调整窗口客户区（工作区）尺寸，不改变当前窗口左上角位置。
        """
        client_width = int(client_width)
        client_height = int(client_height)
        if client_width <= 0 or client_height <= 0:
            raise ValueError("客户区尺寸必须大于 0")

        win_left, win_top, win_right, win_bottom = win32gui.GetWindowRect(self.hwnd)
        cur_client_left, cur_client_top, cur_client_right, cur_client_bottom = win32gui.GetClientRect(
            self.hwnd
        )
        cur_client_width = cur_client_right - cur_client_left
        cur_client_height = cur_client_bottom - cur_client_top
        if cur_client_width <= 0 or cur_client_height <= 0:
            raise RuntimeError("当前客户区尺寸无效，无法调整")

        frame_w = (win_right - win_left) - cur_client_width
        frame_h = (win_bottom - win_top) - cur_client_height
        target_window_w = client_width + frame_w
        target_window_h = client_height + frame_h
        if target_window_w <= 0 or target_window_h <= 0:
            raise RuntimeError("计算后的窗口尺寸无效，请检查参数")

        try:
            win32gui.MoveWindow(
                self.hwnd, win_left, win_top, target_window_w, target_window_h, repaint
            )
        except win32gui.error as e:
            raise RuntimeError(f"调整客户区尺寸失败: {e}") from e
        return win32gui.GetClientRect(self.hwnd)

    def capture_background(self, x1=None, y1=None, x2=None, y2=None) -> np.ndarray:
        x1, y1, width, height = self._normalize_rect(x1, y1, x2, y2)

        h_wnd_dc = user32.GetDC(self.hwnd)
        if not h_wnd_dc:
            raise ctypes.WinError(ctypes.get_last_error())

        h_mem_dc = gdi32.CreateCompatibleDC(h_wnd_dc)
        if not h_mem_dc:
            user32.ReleaseDC(self.hwnd, h_wnd_dc)
            raise ctypes.WinError(ctypes.get_last_error())

        h_bitmap = gdi32.CreateCompatibleBitmap(h_wnd_dc, width, height)
        if not h_bitmap:
            gdi32.DeleteDC(h_mem_dc)
            user32.ReleaseDC(self.hwnd, h_wnd_dc)
            raise ctypes.WinError(ctypes.get_last_error())

        old_obj = gdi32.SelectObject(h_mem_dc, h_bitmap)
        if not old_obj:
            gdi32.DeleteObject(h_bitmap)
            gdi32.DeleteDC(h_mem_dc)
            user32.ReleaseDC(self.hwnd, h_wnd_dc)
            raise ctypes.WinError(ctypes.get_last_error())

        try:
            ok = gdi32.BitBlt(h_mem_dc, 0, 0, width, height, h_wnd_dc, x1, y1, SRCCOPY)
            if not ok:
                raise ctypes.WinError(ctypes.get_last_error())
            return self._bitmap_to_bgr(h_mem_dc, h_bitmap, width, height)
        finally:
            gdi32.SelectObject(h_mem_dc, old_obj)
            gdi32.DeleteObject(h_bitmap)
            gdi32.DeleteDC(h_mem_dc)
            user32.ReleaseDC(self.hwnd, h_wnd_dc)

    def capture_foreground(self, x1=None, y1=None, x2=None, y2=None) -> np.ndarray:
        x1, y1, width, height = self._normalize_rect(x1, y1, x2, y2)
        screen_x, screen_y = win32gui.ClientToScreen(self.hwnd, (0, 0))
        src_x = screen_x + x1
        src_y = screen_y + y1

        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
        if src_x >= screen_w:
            raise ValueError(f"起始坐标超过屏幕横轴 {src_x} >= {screen_w}")
        if src_y >= screen_h:
            raise ValueError(f"起始坐标超过屏幕纵轴 {src_y} >= {screen_h}")

        h_screen_dc = user32.GetDC(0)
        if not h_screen_dc:
            raise ctypes.WinError(ctypes.get_last_error())

        h_mem_dc = gdi32.CreateCompatibleDC(h_screen_dc)
        if not h_mem_dc:
            user32.ReleaseDC(0, h_screen_dc)
            raise ctypes.WinError(ctypes.get_last_error())

        h_bitmap = gdi32.CreateCompatibleBitmap(h_screen_dc, width, height)
        if not h_bitmap:
            gdi32.DeleteDC(h_mem_dc)
            user32.ReleaseDC(0, h_screen_dc)
            raise ctypes.WinError(ctypes.get_last_error())

        old_obj = gdi32.SelectObject(h_mem_dc, h_bitmap)
        if not old_obj:
            gdi32.DeleteObject(h_bitmap)
            gdi32.DeleteDC(h_mem_dc)
            user32.ReleaseDC(0, h_screen_dc)
            raise ctypes.WinError(ctypes.get_last_error())

        try:
            ok = gdi32.BitBlt(h_mem_dc, 0, 0, width, height, h_screen_dc, src_x, src_y, SRCCOPY)
            if not ok:
                raise ctypes.WinError(ctypes.get_last_error())
            return self._bitmap_to_bgr(h_mem_dc, h_bitmap, width, height)
        finally:
            gdi32.SelectObject(h_mem_dc, old_obj)
            gdi32.DeleteObject(h_bitmap)
            gdi32.DeleteDC(h_mem_dc)
            user32.ReleaseDC(0, h_screen_dc)

    def capture_printwindow(self, x1=None, y1=None, x2=None, y2=None, render_full: bool = True) -> np.ndarray:
        """
        使用 PrintWindow 进行后台截图（尽量获取遮挡/最小化窗口内容）。
        坐标参数使用客户区坐标系，行为与 capture_background 保持一致。
        """
        crop_x, crop_y, crop_w, crop_h = self._normalize_rect(x1, y1, x2, y2)
        _, _, client_w, client_h = self._normalize_rect(0, 0, None, None)

        h_wnd_dc = user32.GetDC(self.hwnd)
        if not h_wnd_dc:
            raise ctypes.WinError(ctypes.get_last_error())

        h_mem_dc = gdi32.CreateCompatibleDC(h_wnd_dc)
        if not h_mem_dc:
            user32.ReleaseDC(self.hwnd, h_wnd_dc)
            raise ctypes.WinError(ctypes.get_last_error())

        h_bitmap = gdi32.CreateCompatibleBitmap(h_wnd_dc, client_w, client_h)
        if not h_bitmap:
            gdi32.DeleteDC(h_mem_dc)
            user32.ReleaseDC(self.hwnd, h_wnd_dc)
            raise ctypes.WinError(ctypes.get_last_error())

        old_obj = gdi32.SelectObject(h_mem_dc, h_bitmap)
        if not old_obj:
            gdi32.DeleteObject(h_bitmap)
            gdi32.DeleteDC(h_mem_dc)
            user32.ReleaseDC(self.hwnd, h_wnd_dc)
            raise ctypes.WinError(ctypes.get_last_error())

        try:
            flags = PW_CLIENTONLY | (PW_RENDERFULLCONTENT if render_full else 0)
            ok = PrintWindow(self.hwnd, h_mem_dc, flags)
            if not ok:
                raise RuntimeError("PrintWindow 截图失败，目标窗口可能不支持该方式")

            full_img = self._bitmap_to_bgr(h_mem_dc, h_bitmap, client_w, client_h)
            return full_img[crop_y : crop_y + crop_h, crop_x : crop_x + crop_w].copy()
        finally:
            gdi32.SelectObject(h_mem_dc, old_obj)
            gdi32.DeleteObject(h_bitmap)
            gdi32.DeleteDC(h_mem_dc)
            user32.ReleaseDC(self.hwnd, h_wnd_dc)


if __name__ == "__main__":
    # 示例：把下面这个句柄替换为你自己的窗口句柄（十进制整数）
    target_hwnd = 3739680

    if target_hwnd == 0:
        raise SystemExit("请先把 target_hwnd 改成目标窗口句柄")

    cap = WindowTool(target_hwnd)
    # 前台截图（可见内容）
    # frame = cap.capture_foreground()
    # 后台截图（窗口 DC）
    # cap.move_mouse_to_screen(100, 100)
    # frame = cap.resize_client_area(700,700)
    frame = cap.capture_background()
    # frame = cap.capture_printwindow()

    
    cv2.imshow("window_capture", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
