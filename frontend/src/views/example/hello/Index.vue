<template>
  <div id="hero">
    <div>
      <el-button type="primary" @click="handleGetDeviceList">重置所有</el-button>
      <el-button type="primary" @click="handleStart(list)">全部开始</el-button>
      <el-button type="primary" @click="handleStop(list)">全部结束</el-button>
      <el-table :data="list" border>
        <el-table-column prop="deviceId" label="句柄" width="180"> </el-table-column>
        <el-table-column prop="name" label="窗口名" width="180"> </el-table-column>
        <el-table-column prop="isRunning" label="是否运行" width="180"> </el-table-column>
        <el-table-column prop="currentTask" label="当前任务" width="180">
        </el-table-column>
        <el-table-column prop="logs" label="日志" width="180"> </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button type="primary" @click="handleStart([scope.row])" size="small"
              >开始</el-button
            >
            <el-button type="primary" @click="handleStop([scope.row])" size="small"
              >结束</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, toRaw } from "vue";
import Abc from "./Abc.vue";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import { io } from "socket.io-client";
const client = {
  socket: null,
};
const list = ref([]);
const handleGetDeviceList = async () => {
  await handleStop(list.value);

  const result = await ipc.invoke(ipcApiRoute.获取设备列表);
  list.value = result;

  list.value.forEach((item, index) => {
    // 移除之前的监听器，防止重复监听
    client.socket.off(`${item.deviceId}`);

    // 添加新的监听器
    client.socket.on(`${item.deviceId}`, (response) => {
      const index = list.value.findIndex((_item) => _item.deviceId == item.deviceId);
      list.value[index] = response;
    });
  });
};

const handleStart = async (deviceList) => {
  await ipc.invoke(ipcApiRoute.开始任务, {
    deviceList: JSON.stringify(deviceList),
    taskList: ["shimen", "main"],
  });
};
const handleStop = async (deviceList) => {
  await ipc.invoke(ipcApiRoute.结束任务, {
    deviceList: JSON.stringify(deviceList),
  });
};

onMounted(() => {
  client.socket = io("ws://localhost:7070");
  client.socket.on("connect", () => {
    console.log("connect!!!!!!!!");
  });

  handleGetDeviceList();
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
.dev-name {
  font-weight: bold;
}
.dev-id {
  color: #666;
}

.dev-actions {
  margin-left: 10px;
}

.btn.small {
  padding: 4px 10px;
  font-size: 12px;
  margin-right: 5px;
}

.btn.small.warning {
  background-color: #e6a23c;
}
.btn.small.success {
  background-color: #67c23a;
}
.btn.small.danger {
  background-color: #f56c6c;
}

.dev-status {
  font-size: 12px;
  margin-right: 10px;
}
.dev-status span {
  margin-left: 5px;
  font-weight: bold;
}
.dev-status .running {
  color: #67c23a;
}
.dev-status .paused {
  color: #e6a23c;
}
.dev-status .stopped {
  color: #f56c6c;
}
.dev-status .completed {
  color: #409eff;
}

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
