<template>
  <div class="app-container">
    <TitleBar title="设备管理系统" />

    <!-- 主要内容区域 -->
    <div class="main-content">
      <el-tabs type="border-card" class="custom-tabs">
        <el-tab-pane label="设备列表">
          <Device
            :list="deviceList"
            :taskList="taskList"
            @startTask="handleStartTask"
            @pauseTask="handlePauseTask"
            @resumeTask="handleResumeTask"
            @endTask="handleEndTask"
            @getDeviceList="handleGetDeviceList"
          />
        </el-tab-pane>
        <el-tab-pane label="账号列表">
          <Account :list="accountList" @deleteAccount="handleDeleteAccount" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import Account from "./account/index.vue";
import Device from "./device/index.vue";
import TitleBar from "@/components/TitleBar.vue";

import { ref, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import { io } from "socket.io-client";

const deviceList = ref([]);
const taskList = ref([]);

let matchSocket = null;

// 更新设备状态
function updateDeviceStatus(statusData) {
  const deviceId = statusData.设备ID;
  if (!deviceId) return;

  // 如果当前任务是更新信息, 则更新账号对应信息
  if (statusData.当前任务 === "更新信息") {
    updateAccountInfo(statusData);
  }

  const index = deviceList.value.findIndex((item) => item.设备ID === deviceId);
  if (index !== -1) {
    // 合并更新状态数据
    deviceList.value[index] = {
      ...deviceList.value[index],
      ...statusData,
    };
  }
}

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
      deviceList.value = data.map((item) => {
        return {
          设备ID: item,
          当前账号: null,
          当前任务: "",
          下一任务: "",
          金币: "",
          等级: "",
          已暂停: false,
        };
      });
      resolve();
    });

    // 接收任务列表
    matchSocket.on("task-list", (data) => {
      console.log("收到任务列表:", data);
      taskList.value = data;
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

const handleStartTask = (row, payload) => {
  const 任务队列 = payload?.任务队列?.length ? payload.任务队列 : [];
  const 任务配置 =
    payload?.任务配置 && typeof payload.任务配置 === "object"
      ? payload.任务配置
      : {};
  ipc.invoke(ipcApiRoute.发送到后端, {
    类型: "开始任务",
    设备ID: row.设备ID,
    任务队列,
    任务配置,
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

const accountList = ref([]);

async function loadAccountList() {
  if (!ipc) return;
  try {
    const res = await ipc.invoke(ipcApiRoute.获取账号列表);
    accountList.value = Array.isArray(res) ? res : [];
  } catch (e) {
    accountList.value = [];
    ElMessage.error("加载账号列表失败");
  }
}

async function handleDeleteAccount(index) {
  try {
    await ElMessageBox.confirm("确定删除该账号？", "提示", {
      type: "warning",
      confirmButtonText: "确定",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }
  accountList.value.splice(index, 1);
  try {
    await ipc.invoke(ipcApiRoute.保存账号列表, {
      accountList: [...accountList.value],
    });
  } catch (error) {
    ElMessage.error("删除账号失败");
    return;
  }
  ElMessage.success("已删除");
  loadAccountList();
}

// 更新账号信息（设备状态里 当前任务 为「更新信息」时，用状态数据更新对应账号）
async function updateAccountInfo(statusData) {
  const 名字 = statusData.名字;
  if (名字 == null) return;

  const index = accountList.value.findIndex((item) => item.名字 === 名字);
  if (index === -1) return;

  const account = accountList.value[index];

  accountList.value[index] = {
    ...account,
    ...statusData,
    更新时间: new Date().toISOString(),
  };

  try {
    await ipc.invoke(ipcApiRoute.保存账号列表, {
      accountList: [...accountList.value],
    });
  } catch (error) {
    ElMessage.error("更新账号信息失败");
    return;
  }
}

const handleGetTaskList = () => {
  ipc.invoke(ipcApiRoute.发送到后端, {
    类型: "获取任务列表",
  });
};

onMounted(async () => {
  await initMatchSocket();
  handleGetDeviceList();
  handleGetTaskList();
  loadAccountList();
});
</script>

<style lang="less">
html,
body,
#app {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB",
    "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
}

.app-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100vh;
  background-color: #f5f7fa;
}

.main-content {
  flex: 1;
  padding: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.custom-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);

  :deep(.el-tabs__content) {
    flex: 1;
    overflow: auto;
    padding: 15px;
    height: 100%;
  }
  
  :deep(.el-tabs__header) {
    background-color: #fff;
    border-bottom: 1px solid #e4e7ed;
  }
}
</style>
