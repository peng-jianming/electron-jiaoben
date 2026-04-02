import ctypes
import time
import os
from ctypes import wintypes

# 定义常量
服务控制管理器全部访问 = 0xF003F
服务全部访问 = 0xF01FF

服务内核驱动 = 0x00000001
服务按需启动 = 0x00000003
服务错误普通 = 0x00000001

服务控制停止 = 0x00000001
服务控制查询 = 0x00000004

服务已停止 = 0x00000001
服务启动待定 = 0x00000002
服务停止待定 = 0x00000003
服务运行中 = 0x00000004

错误服务不存在 = 0x00000424

# 定义服务状态结构体
class 服务状态(ctypes.Structure):
    _fields_ = [
        ("服务类型", wintypes.DWORD),
        ("当前状态", wintypes.DWORD),
        ("接受控制", wintypes.DWORD),
        ("Win32退出码", wintypes.DWORD),
        ("服务特定退出码", wintypes.DWORD),
        ("检查点", wintypes.DWORD),
        ("等待提示", wintypes.DWORD)
    ]

# 定义Windows API函数
服务控制库 = ctypes.WinDLL('advapi32')
内核库 = ctypes.WinDLL('kernel32')

打开服务控制管理器 = 服务控制库.OpenSCManagerW
打开服务控制管理器.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
打开服务控制管理器.restype = wintypes.SC_HANDLE

创建服务 = 服务控制库.CreateServiceW
创建服务.argtypes = [
    wintypes.SC_HANDLE,        # hSCManager
    wintypes.LPCWSTR,          # lpServiceName
    wintypes.LPCWSTR,          # lpDisplayName
    wintypes.DWORD,            # 期望访问权限
    wintypes.DWORD,            # 服务类型
    wintypes.DWORD,            # 启动类型
    wintypes.DWORD,            # 错误控制
    wintypes.LPCWSTR,          # lpBinaryPathName
    wintypes.LPCWSTR,          # lpLoadOrderGroup
    wintypes.LPDWORD,          # TagId 指针
    wintypes.LPCWSTR,          # lpDependencies
    wintypes.LPCWSTR,          # lpServiceStartName
    wintypes.LPCWSTR           # lpPassword
]
创建服务.restype = wintypes.SC_HANDLE

打开服务 = 服务控制库.OpenServiceW
打开服务.argtypes = [wintypes.SC_HANDLE, wintypes.LPCWSTR, wintypes.DWORD]
打开服务.restype = wintypes.SC_HANDLE

启动服务 = 服务控制库.StartServiceW
启动服务.argtypes = [wintypes.SC_HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.LPCWSTR)]
启动服务.restype = wintypes.BOOL

控制服务 = 服务控制库.ControlService
控制服务.argtypes = [wintypes.SC_HANDLE, wintypes.DWORD, ctypes.POINTER(服务状态)]
控制服务.restype = wintypes.BOOL

删除服务 = 服务控制库.DeleteService
删除服务.argtypes = [wintypes.SC_HANDLE]
删除服务.restype = wintypes.BOOL

关闭服务句柄 = 服务控制库.CloseServiceHandle
关闭服务句柄.argtypes = [wintypes.SC_HANDLE]
关闭服务句柄.restype = wintypes.BOOL

获取最后错误码 = 内核库.GetLastError
获取最后错误码.argtypes = []
获取最后错误码.restype = wintypes.DWORD

# 定义安装驱动服务的函数
def 安装驱动服务(驱动服务名, 驱动完整路径):
    """
    安装驱动服务
    参数:
        驱动服务名: 驱动服务名称
        驱动完整路径: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    import winreg
    if not 驱动服务名 or not 驱动完整路径:
        return False

    try:
        # 构造注册表路径
        注册表路径 = r"SYSTEM\CurrentControlSet\Services\{}".format(驱动服务名)
        # 打开注册表键，若不存在则创建
        注册表键 = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, 注册表路径)
        # 设置DisplayName
        winreg.SetValueEx(注册表键, "DisplayName", 0, winreg.REG_SZ, 驱动服务名)
        # 设置ErrorControl
        winreg.SetValueEx(注册表键, "ErrorControl", 0, winreg.REG_DWORD, 1)
        # 设置ImagePath
        winreg.SetValueEx(注册表键, "ImagePath", 0, winreg.REG_EXPAND_SZ, r"\??\{}".format(驱动完整路径))
        # 设置Start
        winreg.SetValueEx(注册表键, "Start", 0, winreg.REG_DWORD, 3)
        # 设置Type
        winreg.SetValueEx(注册表键, "Type", 0, winreg.REG_DWORD, 1)
        # 设置Security\Security (空值)
        安全键 = winreg.CreateKey(注册表键, "Security")
        winreg.SetValueEx(安全键, "Security", 0, winreg.REG_BINARY, b'')
        winreg.CloseKey(安全键)
        winreg.CloseKey(注册表键)
        return True
    except Exception:
        # 可以在这里打印错误信息
        print("安装驱动服务错误")
        return False

# 定义创建驱动服务的函数
def 创建驱动服务(驱动服务名, 驱动完整路径):
    """
    创建驱动服务
    参数:
        驱动服务名: 驱动服务名称
        驱动完整路径: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    schManager = 打开服务控制管理器(None, None, 服务控制管理器全部访问)
    if not schManager:
        return False

    schService = 打开服务(schManager, 驱动服务名, 服务全部访问)
    if schService:
        # 服务已存在，尝试停止服务
        svcStatus = 服务状态()
        # 先尝试查询当前状态；查询失败不能当“停止完成”
        for _ in range(5):
            if 控制服务(schService, 服务控制查询, ctypes.byref(svcStatus)):
                break
            time.sleep(1)
        else:
            关闭服务句柄(schService)
            关闭服务句柄(schManager)
            return False

        if svcStatus.当前状态 != 服务已停止:
            # 服务正在运行，尝试停止
            if not 控制服务(schService, 服务控制停止, ctypes.byref(svcStatus)):
                关闭服务句柄(schService)
                关闭服务句柄(schManager)
                return False
            # 等待服务停止（避免查询失败直接“成功返回”）
            for _ in range(10):
                if not 控制服务(schService, 服务控制查询, ctypes.byref(svcStatus)):
                    time.sleep(1)
                    continue
                if svcStatus.当前状态 == 服务已停止:
                    break
                time.sleep(4)
            if svcStatus.当前状态 != 服务已停止:
                关闭服务句柄(schService)
                关闭服务句柄(schManager)
                return False
        关闭服务句柄(schService)
        关闭服务句柄(schManager)
        return True
    else:
        # 服务不存在，创建服务
        schService = 创建服务(
            schManager,
            驱动服务名,
            驱动服务名,
            服务全部访问,
            服务内核驱动,
            服务按需启动,
            服务错误普通,
            驱动完整路径,
            None,
            None,
            None,
            None,
            None
        )
        if not schService:
            关闭服务句柄(schManager)
            return False
        关闭服务句柄(schService)
        关闭服务句柄(schManager)
        return True

# 定义启动驱动服务的函数
def 启动驱动服务(驱动服务名, 驱动完整路径):
    """
    启动驱动服务
    参数:
        驱动服务名: 驱动服务名称
        驱动完整路径: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    if not 驱动服务名:
        print("驱动服务名称不能为空")
        return False

    if not 创建驱动服务(驱动服务名, 驱动完整路径):
        print("驱动创建失败")
        return False

    schManager = 打开服务控制管理器(None, None, 服务控制管理器全部访问)
    if not schManager:
        print("无法打开服务控制管理器。错误代码: %d", 获取最后错误码())
        return False

    schService = 打开服务(schManager, 驱动服务名, 服务全部访问)
    if not schService:
        关闭服务句柄(schManager)
        return False

    svcStatus = 服务状态()

    if 控制服务(schService, 服务控制查询, ctypes.byref(svcStatus)):
        print("服务当前状态: %d", svcStatus.当前状态)
        if svcStatus.当前状态 == 服务运行中:
            print("服务已在运行。")
            关闭服务句柄(schService)
            关闭服务句柄(schManager)
            return True
    else:
        最后错误码 = 获取最后错误码()
        if 最后错误码 != 1062:  # 服务未激活
            print("服务控制查询失败。错误代码: %d", 最后错误码)
            关闭服务句柄(schService)
            关闭服务句柄(schManager)
            return False

    # 尝试启动服务
    if not 启动服务(schService, 0, None):
        最后错误码 = 获取最后错误码()
        if 最后错误码 == 1056:  # 服务已在运行
            print("服务已经在运行。")
            return True
        elif 最后错误码 == 1072 or 最后错误码 == 183:  # 服务已存在
            print("服务已经存在且可能正在运行。")
            return True
        else:
            print("启动服务失败。错误代码: %d", 最后错误码)
            关闭服务句柄(schService)
            关闭服务句柄(schManager)
            return False
    # else:
    #     print("启动服务命令已发送。")

    # 等待服务启动
    for i in range(10):
        if not 控制服务(schService, 服务控制查询, ctypes.byref(svcStatus)):
            关闭服务句柄(schService)
            关闭服务句柄(schManager)
            return False
        else:
            if svcStatus.当前状态 == 服务运行中:
                break
        time.sleep(4)

    关闭服务句柄(schService)
    关闭服务句柄(schManager)

    if svcStatus.当前状态 == 服务运行中:
        return True
    else:
        return False

# 定义停止驱动服务的函数
def 停止驱动服务(驱动服务名, 驱动完整路径):
    """
    停止驱动服务
    参数:
        驱动服务名: 驱动服务名称
        驱动完整路径: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    schManager = 打开服务控制管理器(None, None, 服务控制管理器全部访问)
    if not schManager:
        return False

    schService = 打开服务(schManager, 驱动服务名, 服务全部访问)
    if not schService:
        关闭服务句柄(schManager)
        return False

    svcStatus = 服务状态()

    if 控制服务(schService, 服务控制查询, ctypes.byref(svcStatus)):
        if svcStatus.当前状态 != 服务已停止:
            if not 控制服务(schService, 服务控制停止, ctypes.byref(svcStatus)):
                关闭服务句柄(schService)
                关闭服务句柄(schManager)
                return False
            # 等待服务停止
            for i in range(10):
                if not 控制服务(schService, 服务控制查询, ctypes.byref(svcStatus)):
                    break
                else:
                    if svcStatus.当前状态 == 服务已停止:
                        break
                time.sleep(4)
            if svcStatus.当前状态 != 服务已停止:
                关闭服务句柄(schService)
                关闭服务句柄(schManager)
                return False
    else:
        # 服务未运行
        关闭服务句柄(schService)
        关闭服务句柄(schManager)
        return True

    关闭服务句柄(schService)
    关闭服务句柄(schManager)
    return True

# 定义卸载驱动服务的函数
def 删除驱动服务(驱动服务名, 驱动完整路径):
    """
    卸载驱动服务
    参数:
        驱动服务名: 驱动服务名称
        驱动完整路径: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    schManager = 打开服务控制管理器(None, None, 服务控制管理器全部访问)
    if not schManager:
        return False

    schService = 打开服务(schManager, 驱动服务名, 服务全部访问)
    if not schService:
        关闭服务句柄(schManager)
        # 服务不存在，视为已卸载
        return True

    svcStatus = 服务状态()

    # 停止服务
    if 控制服务(schService, 服务控制查询, ctypes.byref(svcStatus)):
        if svcStatus.当前状态 != 服务已停止:
            if not 控制服务(schService, 服务控制停止, ctypes.byref(svcStatus)):
                关闭服务句柄(schService)
                关闭服务句柄(schManager)
                return False
            # 等待服务停止
            for i in range(10):
                if not 控制服务(schService, 服务控制查询, ctypes.byref(svcStatus)):
                    break
                else:
                    if svcStatus.当前状态 == 服务已停止:
                        break
                time.sleep(4)
            if svcStatus.当前状态 != 服务已停止:
                关闭服务句柄(schService)
                关闭服务句柄(schManager)
                return False

    # 删除服务（DeleteService 可能是异步生效，需要等待从 SCM 消失）
    if not 删除服务(schService):
        关闭服务句柄(schService)
        关闭服务句柄(schManager)
        return False

    关闭服务句柄(schService)
    关闭服务句柄(schManager)

    # 等待服务从 SCM 中消失，避免下一次安装时注册表/服务对象仍处于过渡态
    # Win32: ERROR_SERVICE_DOES_NOT_EXIST = 1060
    ERROR_SERVICE_DOES_NOT_EXIST = 1060
    for _ in range(20):
        schManager2 = 打开服务控制管理器(None, None, 服务控制管理器全部访问)
        if not schManager2:
            return False
        schService2 = 打开服务(schManager2, 驱动服务名, 服务全部访问)
        if schService2:
            关闭服务句柄(schService2)
            关闭服务句柄(schManager2)
            time.sleep(1)
            continue
        # OpenService 失败：检查是否是“服务不存在”
        last_err = 获取最后错误码()
        关闭服务句柄(schManager2)
        if last_err == ERROR_SERVICE_DOES_NOT_EXIST:
            return True
        # 其它错误继续等一下（有些场景错误码会短暂变化）
        time.sleep(1)

    # 超时仍未消失，认为卸载未完成
    return False

# 获取驱动名称的函数
def 获取驱动名称(驱动路径):
    """
    从驱动文件路径中获取驱动名称
    参数:
        驱动路径: 驱动文件的完整路径
    返回值:
        驱动名称（不含扩展名）
    """
    filename = os.path.basename(驱动路径)
    name, _ = os.path.splitext(filename)
    return name

# 定义安装函数
def 安装(驱动路径):
    """
    安装驱动服务
    参数:
        驱动路径: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    驱动服务名 = 获取驱动名称(驱动路径)
    return 安装驱动服务(驱动服务名, 驱动路径)

# 定义启动函数
def 启动(驱动路径):
    """
    启动驱动服务
    参数:
        驱动路径: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    驱动服务名 = 获取驱动名称(驱动路径)
    return 启动驱动服务(驱动服务名, 驱动路径)

# 定义停止函数
def 停止(驱动路径):
    """
    停止驱动服务
    参数:
        驱动路径: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    驱动服务名 = 获取驱动名称(驱动路径)
    return 停止驱动服务(驱动服务名, 驱动路径)

# 定义卸载函数
def 卸载(驱动路径):
    """
    卸载驱动服务
    参数:
        驱动路径: 驱动文件的完整路径
    返回值:
        成功返回True，失败返回False
    """
    驱动服务名 = 获取驱动名称(驱动路径)
    return 删除驱动服务(驱动服务名, 驱动路径)

class 驱动加载器:
    def __init__(self, 驱动路径):
        self.驱动路径 = 驱动路径

    def 安装(self):
        return 安装(self.驱动路径)

    def 启动(self):
        return 启动(self.驱动路径)

    def 停止(self):
        return 停止(self.驱动路径)

    def 卸载(self):
        return 卸载(self.驱动路径)

# 示例：安装驱动
if __name__ == '__main__':
    # r"D:\code\python\RuneLiteOne\dxGame\dx_lib\x64\dxkm.sys"
    while True:
        sys_path = input("请输入驱动路径,n退出:")
        if sys_path == "n":
            break
        if not os.path.exists(sys_path):
            print("文件不存在")
            continue
        driver_loader = 驱动加载器(sys_path)
        while True:
            flag = input("请输入操作:\n1:安装驱动\2:启动驱动\3:停止驱动\4:卸载驱动\5:重新输入驱动路径\n")
            if flag == "5":
                break
            if flag == "1":
                is_ok = driver_loader.安装()
                print("驱动安装",is_ok)
            if flag == "2":
                is_ok = driver_loader.启动()
                print("启动驱动",is_ok)
            if flag == "3":
                is_ok = driver_loader.停止()
                print("停止驱动",is_ok)
            if flag == "4":
                is_ok = driver_loader.卸载()
                print("卸载驱动",is_ok)