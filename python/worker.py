import multiprocessing as mp
import time
from typing import Any, Dict


def worker_main(hwnd: str, name: str, in_queue: "mp.Queue[Dict[str, Any]]") -> None:
    """
    每个设备对应一个子进程的入口函数。

    你可以在这里实现：
    - 截图
    - 图像匹配（和事先准备的小图对比）
    - 根据对比结果对设备进行点击/操作

    当前只是一个最小骨架示例：根据收到的消息类型，简单打印并模拟状态变化。
    真正的业务逻辑可以完全按你自己的需求来写。
    """
    print(f"[worker {hwnd}] start, name={name}")

    running = True

    while running:
        try:
            # 等待来自主进程的指令
            message = in_queue.get(timeout=0.5)
        except Exception:
            # 没有消息时可以在这里做一些“常驻轮询”工作，比如定时截图等
            # TODO: 在这里放你自己的循环逻辑（截图 / 图色 / 点击）
            continue

        msg_type = message.get("type")
        print(f"[worker {hwnd}] recv message:", message)

        if msg_type == "stop":
            # 收到停止指令时，做一些清理工作后优雅退出
            # TODO: 在这里做你需要的“安全停止”逻辑
            running = False

        else:
            # TODO: 这里根据你的协议，自行扩展各种指令
            # 比如 type == "task_start" / "click" / "custom_xxx" 等
            pass

    print(f"[worker {hwnd}] exit")


if __name__ == "__main__":
    # 仅用于本文件被直接运行时的简单测试
    q: "mp.Queue[Dict[str, Any]]" = mp.Queue()
    p = mp.Process(target=worker_main, args=("test_hwnd", "test_name", q))
    p.start()
    q.put({"type": "stop"})
    p.join()


