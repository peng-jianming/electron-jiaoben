<template>
  <div>
    <el-table :data="list" border size="small" empty-text="没有发现设备~">
      <el-table-column type="selection" width="55"> </el-table-column>
      <el-table-column type="index" label="序号"> </el-table-column>
      <el-table-column label="设备ID" prop="设备ID" width="180"> </el-table-column>
      <el-table-column label="当前任务" prop="当前任务"> </el-table-column>
      <el-table-column label="下一任务" prop="下一任务"> </el-table-column>
      <el-table-column label="金币" prop="金币"> </el-table-column>
      <el-table-column label="等级" prop="等级"> </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button type="text" size="small" @click="handleStartTask(scope.row)"
            >开始</el-button
          >
          <el-button
            v-if="!scope.row.已暂停"
            type="text"
            size="small"
            @click="handlePauseTask(scope.row)"
            >暂停</el-button
          >
          <el-button
            v-else
            type="text"
            size="small"
            @click="handleResumeTask(scope.row)"
            >恢复</el-button
          >
          <el-button type="text" size="small" @click="handleEndTask(scope.row)"
            >结束</el-button
          >
        </template>
      </el-table-column>
    </el-table>

    <el-button @click="handleGetDeviceList">设备检测</el-button>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { ipcApiRoute } from "@/api";
import { ipc } from "@/utils/ipcRenderer";
import { io } from "socket.io-client";
const list = ref([]);

let matchSocket = null;

// 更新设备状态
function updateDeviceStatus(statusData) {
  const deviceId = statusData.设备ID;
  if (!deviceId) return;

  const index = list.value.findIndex((item) => item.设备ID === deviceId);
  if (index !== -1) {
    // 合并更新状态数据
    list.value[index] = {
      ...list.value[index],
      ...statusData,
    };
  }
}

// 初始化 Socket 连接
function initMatchSocket() {
  return new Promise((resolve, reject) => {
    if (matchSocket) {
      resolve();
      return;
    }

    matchSocket = io("ws://localhost:7072");

    matchSocket.on("connect", () => {
      console.log("匹配 Socket 连接成功");
      resolve();
    });

    // 接收设备列表
    matchSocket.on("device-list", (data) => {
      console.log("收到设备id列表:", data);
      list.value = data.map((item) => {
        return {
          设备ID: item,
          当前任务: "",
          下一任务: "",
          金币: "",
          等级: "",
          已暂停: false,
        };
      });
      resolve();
    });

    // 接收设备状态更新
    matchSocket.on("device-status-update", (data) => {
      console.log("收到设备状态更新:", data);
      updateDeviceStatus(data);
    });
  });
}

const handleGetDeviceList = () => {
  ipc.invoke(ipcApiRoute.发送到后端, {
    类型: "获取设备列表",
  });
};

const handleStartTask = (row) => {
  ipc.invoke(ipcApiRoute.发送到后端, {
    类型: "开始任务",
    设备ID: row.设备ID,
    任务队列: ["师门任务", "宝图任务", "抓鬼任务"],
  });
};

const handleEndTask = (row) => {
  ipc.invoke(ipcApiRoute.发送到后端, {
    类型: "结束任务",
    设备ID: row.设备ID,
  });
};

const handlePauseTask = (row) => {
  ipc.invoke(ipcApiRoute.发送到后端, {
    类型: "暂停任务",
    设备ID: row.设备ID,
  });
};

const handleResumeTask = (row) => {
  ipc.invoke(ipcApiRoute.发送到后端, {
    类型: "恢复任务",
    设备ID: row.设备ID,
  });
};

onMounted(async () => {
  await initMatchSocket();
  handleGetDeviceList();
});
</script>

<style scoped></style>
