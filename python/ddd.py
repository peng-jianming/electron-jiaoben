import subprocess
import os


def get_connected_devices_simple():
    adb_path = r"C:\platform-tools\adb.exe"

    # 检查ADB是否存在
    if not os.path.exists(adb_path):
        print(f"错误: ADB不存在于 {adb_path}")
        print(r"请检查ADB是否安装在 C:\platform-tools 目录下")
        return []

    try:
        # 运行adb devices命令
        # Windows下建议使用shell=True
        result = subprocess.run(
            [adb_path, 'devices'],
            capture_output=True,
            text=True,
            timeout=10,
            shell=True
        )

        # 解析输出
        devices = []
        for line in result.stdout.split('\n'):
            if line.strip() and not line.startswith('List'):
                parts = line.split()
                if len(parts) >= 2 and parts[1] == 'device':
                    devices.append(parts[0])

        return devices

    except Exception as e:
        print(f"执行错误: {e}")
        return []


# 直接测试
if __name__ == "__main__":
    devices = get_connected_devices_simple()

    if devices:
        print(f"\n找到 {len(devices)} 个设备:")
        for device in devices:
            print(f"  - {device}")