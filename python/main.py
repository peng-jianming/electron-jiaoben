import argparse
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import sys
import json
import websockets
import asyncio
from typing import Dict

# 确保可以导入当前目录的模块
sys.path.append(".")

app = FastAPI()

# 解析命令行参数
parser = argparse.ArgumentParser(description='Python Server')
parser.add_argument('--port', type=int, default=7074, help='The port number.')
args = parser.parse_args()

# --- 任务管理器 ---
class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}
        self.task_events: Dict[str, asyncio.Event] = {}
        self.task_status: Dict[str, str] = {} # running, paused, stopped

    async def start_task(self, device_id, script_config, websocket):
        if device_id in self.tasks and not self.tasks[device_id].done():
            return False, "Task already running"
        
        # 创建暂停事件
        self.task_events[device_id] = asyncio.Event()
        self.task_events[device_id].set() # 初始为非暂停状态
        self.task_status[device_id] = "running"

        # 创建并启动任务
        task = asyncio.create_task(self._run_device_script(device_id, script_config, websocket))
        self.tasks[device_id] = task
        return True, "Task started"

    async def pause_task(self, device_id):
        if device_id in self.task_events:
            self.task_events[device_id].clear()
            self.task_status[device_id] = "paused"
            return True
        return False

    async def resume_task(self, device_id):
        if device_id in self.task_events:
            self.task_events[device_id].set()
            self.task_status[device_id] = "running"
            return True
        return False

    async def stop_task(self, device_id):
        if device_id in self.tasks:
            self.tasks[device_id].cancel()
            # 确保任务被清理
            try:
                await self.tasks[device_id]
            except asyncio.CancelledError:
                pass
            self._cleanup(device_id)
            return True
        return False

    def _cleanup(self, device_id):
        if device_id in self.tasks: del self.tasks[device_id]
        if device_id in self.task_events: del self.task_events[device_id]
        if device_id in self.task_status: del self.task_status[device_id]

    async def _run_device_script(self, device_id, script_config, websocket):
        try:
            # 模拟脚本步骤，这里假设脚本由多个步骤组成
            steps = script_config.get("steps", ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"])
            
            for i, step in enumerate(steps):
                # 检查暂停
                if device_id in self.task_events:
                     await self.task_events[device_id].wait()

                # 发送当前进度给前端
                await websocket.send_text(json.dumps({
                    "type": "script_progress",
                    "deviceId": device_id,
                    "status": "running",
                    "progress": f"{i+1}/{len(steps)}",
                    "step": step
                }))

                # 执行实际的群控指令
                payload = {
                    "action": "script",
                    "comm": {
                        "deviceId": device_id,
                        "step": step,
                        **script_config
                    }
                }
                await send_to_gc(payload)
                
                # 模拟耗时
                await asyncio.sleep(2)

            # 任务完成
            await websocket.send_text(json.dumps({
                "type": "script_result",
                "deviceId": device_id,
                "status": "success",
                "message": "Script completed"
            }))

        except asyncio.CancelledError:
            await websocket.send_text(json.dumps({
                "type": "script_result",
                "deviceId": device_id,
                "status": "stopped",
                "message": "Script stopped by user"
            }))
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "script_result",
                "deviceId": device_id,
                "status": "error",
                "message": str(e)
            }))
        finally:
            self._cleanup(device_id)

task_manager = TaskManager()

# 通用处理函数：连接群控发送指令
async def send_to_gc(payload):
    try:
        print(f"Sending to GC: {payload}")
        async with websockets.connect("ws://127.0.0.1:33332") as qc_ws:
            await qc_ws.send(json.dumps(payload))
            response = await qc_ws.recv()
            print(f"GC Response: {response}")
            return json.loads(response)
    except Exception as e:
        print(f"GC Error: {e}")
        return None

# WebSocket 路由
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connected")
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            
            try:
                json_data = json.loads(data)
                print(f"Parsed JSON: {json_data}")
                
                msg_type = json_data.get('type')

                if msg_type == 'getDevice':
                    response_data = await send_to_gc({ "action": "list" })
                    if response_data and response_data.get("StatusCode") == 200:
                        await websocket.send_text(json.dumps({
                            "type": "device_list",
                            "data": response_data.get("result", [])
                        }))
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Failed to get device list"
                        }))

                elif msg_type == 'control_task':
                    # 任务控制：start, pause, resume, stop
                    action = json_data.get('action') # start, pause, resume, stop
                    device_id = json_data.get('deviceId')
                    config = json_data.get('config', {})

                    if action == 'start':
                        success, msg = await task_manager.start_task(device_id, config, websocket)
                    elif action == 'pause':
                        success = await task_manager.pause_task(device_id)
                        msg = "Paused" if success else "Failed to pause"
                        if success:
                            await websocket.send_text(json.dumps({
                                "type": "script_progress",
                                "deviceId": device_id,
                                "status": "paused"
                            }))
                    elif action == 'resume':
                        success = await task_manager.resume_task(device_id)
                        msg = "Resumed" if success else "Failed to resume"
                    elif action == 'stop':
                        success = await task_manager.stop_task(device_id)
                        msg = "Stopped" if success else "Failed to stop"
                    
                    print(f"Task control {action} for {device_id}: {msg}")

                elif msg_type == 'screen':
                    # 使用前端传来的comm或者默认值
                    comm = json_data.get('comm', {
                        "deviceIds": "all",
                        "savePath": "d:/quickmirror",
                        "onlyDeviceName": 1,
                        "customName": "test"
                    })
                    response_data = await send_to_gc({ 
                        "action": "screen",
                        "comm": comm
                    })
                    
                    if response_data and response_data.get("StatusCode") == 200:
                         await websocket.send_text(json.dumps({
                            "type": "screen_result",
                            "data": response_data
                        }))
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Failed to capture screen"
                        }))

            except Exception as e:
                print(f"Error processing message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")


if __name__ == "__main__":
    print(f"Server running on port {args.port}")
    uvicorn.run(app, host="127.0.0.1", port=args.port)

