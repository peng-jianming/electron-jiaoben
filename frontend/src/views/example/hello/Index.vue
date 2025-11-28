<template>
  <div id="hero">
    <div class="content">
      <div class="card">
        <h3>WebSocket 通讯测试</h3>
        <div class="status">状态: {{ isConnected ? '已连接' : '未连接' }}</div>
        <div class="actions">
          <button class="btn" @click="getDeviceList" :disabled="!isConnected">获取设备列表</button>
          <button class="btn warning" @click="screenCapture" :disabled="!isConnected">执行群控截图</button>
        </div>
        
        <div class="device-list" v-if="deviceList.length > 0">
            <h4>设备列表 ({{ deviceList.length }})</h4>
            <div class="list-container">
                <div v-for="dev in deviceList" :key="dev.deviceId" class="device-item">
                    <div class="dev-info">
                        <span class="dev-name">{{ dev.name }}</span>
                        <span class="dev-id">{{ dev.deviceId }}</span>
                        <span class="dev-no">No.{{ dev.no }}</span>
                    </div>
                    <div class="dev-status" v-if="tasks[dev.deviceId]">
                        <span :class="tasks[dev.deviceId].status">{{ tasks[dev.deviceId].status }}</span>
                        <span class="progress" v-if="tasks[dev.deviceId].progress">{{ tasks[dev.deviceId].progress }}</span>
                    </div>
                    <div class="dev-actions">
                        <button class="btn small" v-if="!tasks[dev.deviceId] || tasks[dev.deviceId].status === 'stopped' || tasks[dev.deviceId].status === 'completed'" @click="controlTask(dev.deviceId, 'start')" :disabled="!isConnected">开始</button>
                        <button class="btn small warning" v-if="tasks[dev.deviceId] && tasks[dev.deviceId].status === 'running'" @click="controlTask(dev.deviceId, 'pause')">暂停</button>
                        <button class="btn small success" v-if="tasks[dev.deviceId] && tasks[dev.deviceId].status === 'paused'" @click="controlTask(dev.deviceId, 'resume')">恢复</button>
                        <button class="btn small danger" v-if="tasks[dev.deviceId] && (tasks[dev.deviceId].status === 'running' || tasks[dev.deviceId].status === 'paused')" @click="controlTask(dev.deviceId, 'stop')">停止</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="log-box">
          <div v-for="(log, index) in wsLog" :key="index" class="log-item">{{ log }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";

// WebSocket Logic
const wsLog = ref([]);
const isConnected = ref(false);
const deviceList = ref([]);
const tasks = ref({}); // 存储每个设备的任务状态 { deviceId: { status: 'running'|'paused'|'stopped', progress: '1/5' } }
let ws = null;

const initWebSocket = () => {
  const port = 7074;
  const url = `ws://127.0.0.1:${port}/ws`;
  
  ws = new WebSocket(url);
  
  ws.onopen = () => {
    console.log("WebSocket connected");
    isConnected.value = true;
    wsLog.value.push(`Connected to ${url}`);
  };
  
  ws.onmessage = (e) => {
    console.log('ws message:', e.data);
    try {
      const res = JSON.parse(e.data);
        
      if (res.type === 'device_list') {
        deviceList.value = JSON.parse(res.data);
        wsLog.value.push(`收到设备列表: ${res.data.length}台设备`);
      } else if (res.type === 'screen_result') {
        wsLog.value.push('收到截图结果: 执行成功');
      } else if (res.type === 'script_progress') {
        // 更新任务进度状态
        tasks.value[res.deviceId] = {
            status: res.status,
            progress: res.progress
        };
        if (res.step) {
             wsLog.value.push(`[${res.deviceId}] ${res.step} (${res.progress})`);
        }
      } else if (res.type === 'script_result') {
        const status = res.status;
        // 标记任务结束
        if (tasks.value[res.deviceId]) {
            tasks.value[res.deviceId].status = status === 'success' ? 'completed' : status;
        }
        wsLog.value.push(`设备[${res.deviceId}]脚本执行: ${res.message}`);
      } else if (res.type === 'error') {
        wsLog.value.push(`服务端错误: ${res.message}`);
      } else {
        wsLog.value.push(`收到服务端JSON: ${JSON.stringify(res)}`);
      }
      
    } catch (err) {
       wsLog.value.push(`收到服务端文本: ${e.data}`);
    }
  };
  
  ws.onerror = (e) => {
    console.error('ws error:', e);
    wsLog.value.push('WebSocket 连接错误');
    isConnected.value = false;
  };
  
  ws.onclose = () => {
    console.log('WebSocket closed');
    wsLog.value.push('WebSocket 连接断开');
    isConnected.value = false;
  };
};

const getDeviceList = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'getDevice' }));
        wsLog.value.push("发送: 获取设备列表");
    }
};

const screenCapture = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const payload = {
            type: 'screen',
            comm: {
                deviceIds: "all",
                savePath: "d:/quickmirror",
                onlyDeviceName: 1,
                customName: "test"
            }
        };
        ws.send(JSON.stringify(payload));
        wsLog.value.push("发送: 执行截图");
    }
};

const controlTask = (deviceId, action) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const payload = {
            type: 'control_task',
            action: action,
            deviceId: deviceId,
            config: {
                // 启动时的配置，其他操作可能忽略
                scriptName: "daily_task",
                steps: ["打开应用", "点击签到", "浏览内容", "关闭应用"] // 模拟步骤
            }
        };
        ws.send(JSON.stringify(payload));
        wsLog.value.push(`发送控制指令: ${action} -> ${deviceId}`);
    }
};

const sendWsMessage = () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    const msg = {
      a: 1,
      b: '222'
    };
    ws.send(JSON.stringify(msg));
    wsLog.value.push(`发送: ${JSON.stringify(msg)}`);
  } else {
    wsLog.value.push('发送失败: 未连接');
  }
};

onMounted(() => {
  initWebSocket();
});

onUnmounted(() => {
  if (ws) ws.close();
});
</script>

<style scoped>
section {
  padding: 42px 32px;
}

#hero {
  padding: 50px 32px;
  text-align: center;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.content {
  max-width: 800px;
  width: 100%;
}

.card {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid #ccc;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  text-align: left;
}

h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #42d392;
}

.btn {
  font-size: 16px;
  display: inline-block;
  background-color: #42d392;
  color: white;
  padding: 8px 18px;
  font-weight: 500;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-right: 10px;
}

.btn.warning {
    background-color: #e6a23c;
}
.btn.warning:hover {
    background-color: #cf9236;
}

.btn:hover {
  background-color: #33a06f;
}

.btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.status {
  margin-bottom: 10px;
  font-weight: bold;
}

.device-list {
    margin: 15px 0;
    padding: 10px;
    background: #f9f9f9;
    border: 1px solid #eee;
    border-radius: 4px;
}
.device-list h4 {
    margin: 0 0 10px 0;
}
.list-container {
    max-height: 150px;
    overflow-y: auto;
}
.device-item {
    display: flex;
    justify-content: space-between;
    padding: 5px;
    border-bottom: 1px solid #eee;
    font-size: 14px;
}
.dev-name { font-weight: bold; }
.dev-id { color: #666; }

.dev-actions {
    margin-left: 10px;
}

.btn.small {
    padding: 4px 10px;
    font-size: 12px;
    margin-right: 5px;
}

.btn.small.warning { background-color: #e6a23c; }
.btn.small.success { background-color: #67c23a; }
.btn.small.danger { background-color: #f56c6c; }

.dev-status {
    font-size: 12px;
    margin-right: 10px;
}
.dev-status span {
    margin-left: 5px;
    font-weight: bold;
}
.dev-status .running { color: #67c23a; }
.dev-status .paused { color: #e6a23c; }
.dev-status .stopped { color: #f56c6c; }
.dev-status .completed { color: #409eff; }

.log-box {
  margin-top: 15px;
  background: #f4f4f4;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 10px;
  height: 200px;
  overflow-y: auto;
  font-family: monospace;
  color: #333;
}

.log-item {
  margin-bottom: 4px;
  border-bottom: 1px solid #eee;
  padding-bottom: 2px;
}

/* Dark mode adaptation if needed, keeping original styles vaguely in mind */
.dark .card {
  background: #222;
  border-color: #444;
}
.dark .log-box {
  background: #111;
  color: #eee;
  border-color: #444;
}
.dark .device-list {
    background: #333;
    border-color: #555;
}
.dark .device-item {
    border-color: #444;
}
</style>
