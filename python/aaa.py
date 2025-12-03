import argparse
import json
import sys
import time

import multiprocessing as mp
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .worker import worker_main


app = FastAPI()


class WorkerManager:
    def __init__(self):
        self.clients = set()
        self.workers = {}

    def add_client(self, ws):
        self.clients.add(ws)

    def remove_client(self, ws):
        self.clients.discard(ws)

    def init_worker(self, hwnd, name):
        if hwnd in self.workers:
            return self.workers[hwnd]

        in_queue = mp.Queue()
        process = mp.Process(target=worker_main, args=(hwnd, name, in_queue))
        process.daemon = True
        process.start()

        worker_info = {
            "process": process,
            "in_queue": in_queue,
            "hwnd": hwnd,
            "name": name,
            "status": "空闲中",
            "last_update": time.time(),
            "action": None,
        }
        self.workers[hwnd] = worker_info
        return worker_info

    def send_to_worker(self, hwnd, message):
        worker_info = self.workers.get(hwnd)
        if not worker_info:
            raise RuntimeError(f"Worker {hwnd} not found")

        queue = worker_info["in_queue"]
        queue.put({**message, "hwnd": hwnd})

    def force_restart_worker(self, hwnd):
        worker_info = self.workers.get(hwnd)
        if not worker_info:
            print(f"Worker {hwnd} not found, cannot restart", file=sys.stderr)
            return

        name = worker_info["name"]
        process = worker_info["process"]

        try:
            if process.is_alive():
                process.terminate()
        except Exception as exc:
            print(f"强制终止进程 {hwnd} 失败: {exc}", file=sys.stderr)

        self.workers.pop(hwnd, None)
        time.sleep(0.1)
        self.init_worker(hwnd, name)
        print(f"工作进程 {hwnd} 已强制重启")

    def stop_task(self, hwnd, timeout=3.0):
        worker_info = self.workers.get(hwnd)
        if not worker_info:
            print(f"Worker {hwnd} not found", file=sys.stderr)
            return False

        process = worker_info["process"]

        try:
            self.send_to_worker(hwnd, {"type": "stop"})
        except Exception as exc:
            print(f"发送停止消息到 {hwnd} 失败: {exc}", file=sys.stderr)
            return False

        start_time = time.time()
        while time.time() - start_time < timeout:
            if not process.is_alive():
                print(f"任务 {hwnd} 正常停止")
                return True
            time.sleep(0.1)

        print(
            f"任务 {hwnd} 在 {int(timeout * 1000)}ms 内未停止，强制重启子进程",
            file=sys.stderr,
        )
        self.force_restart_worker(hwnd)
        return False

    async def handle_init(self):
        device_list = []
        message = {
            "type": "init",
            "data": {
                "list": device_list
            },
        }
        await self.broadcast(message)

    async def handle_client_message(self, message):
        print("收到来自客户端的信息(已解析):", message)

        device_list = message.get("deviceList") or message.get("device_list")
        if not device_list:
            await self.broadcast({"type": "echo", "data": message})
            return

        hwnds = [str(d.get("hwnd")) for d in device_list if d.get("hwnd") is not None]

        if message.get("type") == "stop":
            for hwnd in hwnds:
                self.stop_task(hwnd)
        else:
            for hwnd in hwnds:
                if hwnd not in self.workers:
                    self.init_worker(hwnd, name=str(hwnd))
                try:
                    self.send_to_worker(hwnd, message)
                except Exception as exc:
                    print(f"发送消息到 {hwnd} 失败: {exc}", file=sys.stderr)

    def get_data_format(self, info):
        last_update_ts = info.get("last_update")
        if last_update_ts:
            t = time.localtime(last_update_ts)
            last_update_str = time.strftime("%Y-%m-%d %H:%M:%S", t)
        else:
            last_update_str = ""

        return {
            "hwnd": info.get("hwnd"),
            "name": info.get("name"),
            "status": info.get("status"),
            "lastUpdate": last_update_str,
            "action": info.get("action"),
        }

    async def broadcast(self, payload):
        if not self.clients:
            return

        text = json.dumps(payload, ensure_ascii=False)
        for ws in list(self.clients):
            try:
                await ws.send_text(text)
            except Exception as exc:
                print("广播到某个 WebSocket 客户端失败:", exc, file=sys.stderr)
                try:
                    await ws.close()
                except Exception:
                    pass
                self.remove_client(ws)


worker_manager = WorkerManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket):
    await websocket.accept()
    worker_manager.add_client(websocket)
    print("新的 WebSocket 连接")

    await worker_manager.handle_init()

    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                data = json.loads(raw_message)
            except Exception as exc:
                print("处理 WebSocket 消息失败:", exc, file=sys.stderr)
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "message": "消息格式错误",
                        },
                        ensure_ascii=False,
                    )
                )
                continue

            await worker_manager.handle_client_message(data)

    except WebSocketDisconnect:
        print("WebSocket 连接关闭")
    except Exception as exc:
        print("WebSocket 错误:", exc, file=sys.stderr)
    finally:
        worker_manager.remove_client(websocket)


parser = argparse.ArgumentParser(description="Python Server")
parser.add_argument("--port", type=int, default=7074, help="The port number.")
args = parser.parse_args()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=args.port)






# 命令行,且传入设备id,启动脚本,启动通讯
# 启动时绑定然后进行任务开始, 任务结束这关闭脚本



# 主进程 获取所有设备, 任务处理,
# 主进程开启websocket服务器
# 设备开始任务, 则调用命令行 传入设备di 启动脚本, 连接主进程的websocket服务器
# 主进程接收到客户端的信息,将配置传过去,开始任务
