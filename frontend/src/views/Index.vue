<template>
  <div class="app-container">
    <TitleBar title="设备管理系统" />

    <div class="main-wrapper">
      <!-- 左侧导航栏 -->
      <aside class="sidebar">
        <div class="nav-menu">
          <div
            class="nav-item"
            :class="{ active: currentTab === 'device' }"
            @click="currentTab = 'device'"
            title="设备管理"
          >
            <el-icon :size="22"><Monitor /></el-icon>
            <span class="nav-label">设备</span>
          </div>
          <div
            class="nav-item"
            :class="{ active: currentTab === 'task' }"
            @click="currentTab = 'task'"
            title="任务配置"
          >
            <el-icon :size="22"><List /></el-icon>
            <span class="nav-label">任务</span>
          </div>
          <div
            class="nav-item"
            :class="{ active: currentTab === 'account' }"
            @click="currentTab = 'account'"
            title="账号管理"
          >
            <el-icon :size="22"><User /></el-icon>
            <span class="nav-label">账号</span>
          </div>
        </div>
        
        <!-- 底部状态指示 -->
        <div class="sidebar-footer">
          <div class="status-indicator">
            <span class="status-dot" :class="{ online: isConnected }"></span>
            <span class="status-text">{{ isConnected ? '已连接' : '未连接' }}</span>
          </div>
        </div>
      </aside>

      <!-- 主内容区域 -->
      <main class="main-content">
        <!-- 内容面板 -->
        <div class="content-panel">
          <div class="panel-header">
            <h3 class="panel-title">
              <el-icon v-if="currentTab === 'device'"><Monitor /></el-icon>
              <el-icon v-else-if="currentTab === 'task'"><List /></el-icon>
              <el-icon v-else><User /></el-icon>
              {{ panelTitle }}
            </h3>
            <div class="panel-actions">
              <el-button 
                v-if="currentTab === 'device'"
                type="primary" 
                plain 
                size="small"
                @click="handleGetDeviceList"
              >
                <el-icon><Refresh /></el-icon>
                刷新设备
              </el-button>
            </div>
          </div>
          
          <div class="panel-body">
            <!-- 使用 v-show 保持组件状态 -->
            <Device
              v-show="currentTab === 'device'"
              :list="deviceList"
              :taskSelectValue="taskSelectValue"
              @startTask="handleStartTask"
              @pauseTask="handlePauseTask"
              @resumeTask="handleResumeTask"
              @endTask="handleEndTask"
              @getDeviceList="handleGetDeviceList"
            />
            <Task
              v-show="currentTab === 'task'"
              :task-list="taskList"
              v-model="taskSelectValue"
              @reload="handleGetTaskList"
              class="task-select-full"
            />
            <Account
              v-show="currentTab === 'account'"
              :list="accountList"
              @deleteAccount="handleDeleteAccount"
            />
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import Account from "@/components/Account.vue";
import Device from "@/components/Device.vue";
import Task from "@/components/Task.vue";
import TitleBar from "@/components/TitleBar.vue";
import { Monitor, User, List, Refresh } from "@element-plus/icons-vue";

import { ref, computed, onMounted, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import { io } from "socket.io-client";

const currentTab = ref("device");
const isConnected = ref(false);
const deviceList = ref([]);
const taskList = ref([]);

// 任务选择状态（提升到父组件以保持状态）
const taskSelectValue = ref({
  selectedTasks: [],
  taskConfig: {},
});

// 加载任务配置（已选任务列表 & 任务配置）
async function loadTaskConfig() {
  if (!ipc) return;
  try {
    const res = await ipc.invoke(ipcApiRoute.获取任务配置);
    if (!res || typeof res !== "object") return;

    const selectedTasks = Array.isArray(res.selectedTasks) ? res.selectedTasks : [];
    const taskConfig = res.taskConfig != null ? res.taskConfig : [];

    taskSelectValue.value = {
      selectedTasks,
      taskConfig,
    };
  } catch (e) {
    // 静默失败，不影响页面使用
  }
}

// 保存任务配置到本地（通过主进程写入 JSON 文件）
async function saveTaskConfig() {
  if (!ipc) return;
  try {
    await ipc.invoke(ipcApiRoute.保存任务配置, {
      taskSelectValue: {
        selectedTasks: JSON.parse(JSON.stringify([...taskSelectValue.value.selectedTasks])),
        taskConfig: JSON.parse(JSON.stringify(taskSelectValue.value.taskConfig)),
      },
    });
  } catch (e) {
    // 静默失败，避免频繁弹错
  }
}

// 面板标题
const panelTitle = computed(() => {
  const titles = {
    device: '设备管理',
    task: '任务配置',
    account: '账号管理'
  };
  return titles[currentTab.value] || '';
});

// 计算运行中和暂停的设备数量
const runningCount = computed(() => {
  return deviceList.value.filter((d) => !d.已暂停 && d.当前任务).length;
});
const pausedCount = computed(() => {
  return deviceList.value.filter((d) => d.已暂停).length;
});

let matchSocket = null;

// 更新设备状态
function updateDeviceStatus(statusData) {
  const deviceId = statusData.设备ID;
  if (!deviceId) return;



  const index = deviceList.value.findIndex((item) => item.设备ID === deviceId);
  if (index !== -1) {

    if (statusData.日志) {
      if (!Array.isArray(deviceList.value[index].日志)) {
        deviceList.value[index].日志 = [];
      }
      // 添加新日志
      deviceList.value[index].日志.push(`[${new Date().toLocaleString()}]： ${statusData.日志}`);
      // 如果超过50条，移除最早的
      if (deviceList.value[index].日志.length > 50) {
        deviceList.value[index].日志.splice(0, deviceList.value[index].日志.length - 50);
      }
      return
    }

    // 如果当前任务是更新信息, 则更新账号对应信息
  // if (statusData.当前任务 === "更新信息") {
  //   updateAccountInfo(statusData);
  // }

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
      isConnected.value = true;
      handleGetDeviceList();
      handleGetTaskList();
    });

    matchSocket.on("disconnect", () => {
      console.log("匹配 Socket 断开连接");
      isConnected.value = false;
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
      resolve();
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

// 监听任务选择与配置变更，自动持久化
watch(
  taskSelectValue,
  () => {
    saveTaskConfig();
  },
  { deep: true }
);

onMounted(async () => {
  await initMatchSocket();
  loadAccountList();
  loadTaskConfig();
});
</script>

<style lang="less">
// 变量定义
@sidebar-width: 72px;
@title-bar-height: 40px;
@stats-bar-height: 80px;
@panel-header-height: 50px;
@primary-color: #5b6af0;
@success-color: #22c55e;
@warning-color: #f59e0b;
@danger-color: #ef4444;
@bg-color: #f1f5f9;
@card-bg: #ffffff;
@text-primary: #1e293b;
@text-secondary: #475569;
@text-muted: #94a3b8;
@border-color: #e2e8f0;

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
  background-color: @bg-color;
}

.main-wrapper {
  display: flex;
  flex: 1;
  overflow: hidden;
  height: calc(100vh - @title-bar-height);
}

// 左侧导航栏
.sidebar {
  width: @sidebar-width;
  background: #ffffff;
  border-right: 1px solid @border-color;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  flex-shrink: 0;
}

.nav-menu {
  padding-top: 12px;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 14px 0;
  margin: 4px 8px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s ease;
  color: @text-muted;
  position: relative;
  
  &:hover {
    color: @primary-color;
    background: rgba(91, 106, 240, 0.06);
  }
  
  &.active {
    color: @primary-color;
    background: linear-gradient(135deg, rgba(91, 106, 240, 0.12) 0%, rgba(139, 92, 246, 0.08) 100%);
    
    .el-icon {
      transform: scale(1.05);
    }
  }
}

.nav-label {
  font-size: 11px;
  margin-top: 5px;
  font-weight: 500;
}

.sidebar-footer {
  padding: 12px 8px;
  border-top: 1px solid @border-color;
}

.status-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px;
  border-radius: 8px;
  background: #f8fafc;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: @danger-color;
  
  &.online {
    background-color: @success-color;
    box-shadow: 0 0 8px rgba(34, 197, 94, 0.5);
    animation: pulse 2s infinite;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.status-text {
  font-size: 10px;
  color: @text-muted;
  font-weight: 500;
}

// 主内容区域
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 15px;
  overflow: hidden;
  gap: 15px;
}

// 统计卡片栏
.stats-bar {
  display: flex;
  gap: 15px;
  height: @stats-bar-height;
  flex-shrink: 0;
}

.stat-card {
  flex: 1;
  background: @card-bg;
  border-radius: 8px;
  padding: 15px 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }
}

.stat-icon {
  width: 45px;
  height: 45px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  
  &.device-icon {
    background: linear-gradient(135deg, @primary-color 0%, #8b5cf6 100%);
    box-shadow: 0 4px 12px rgba(91, 106, 240, 0.3);
  }
  
  &.running-icon {
    background: linear-gradient(135deg, @success-color 0%, #4ade80 100%);
    box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
  }
  
  &.paused-icon {
    background: linear-gradient(135deg, @warning-color 0%, #fbbf24 100%);
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
  }
  
  &.account-icon {
    background: linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%);
    box-shadow: 0 4px 12px rgba(6, 182, 212, 0.3);
  }
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: @text-primary;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: @text-muted;
  margin-top: 2px;
}

// 内容面板
.content-panel {
  flex: 1;
  background: @card-bg;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03);
  border: 1px solid @border-color;
}

.panel-header {
  height: @panel-header-height;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid @border-color;
  flex-shrink: 0;
  background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%);
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: @text-primary;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  
  .el-icon {
    color: @primary-color;
    background: rgba(91, 106, 240, 0.1);
    padding: 6px;
    border-radius: 8px;
  }
}

.panel-actions {
  display: flex;
  gap: 10px;
}

.panel-body {
  flex: 1;
  padding: 15px;
  overflow: hidden;
}

// 任务配置页面全屏样式
.task-select-full {
  height: 100% !important;
  min-height: unset !important;
  max-height: unset !important;
  
  :deep(.task-columns) {
    height: 100%;
  }
  
  :deep(.column) {
    flex: 1;
    min-width: 200px;
  }
  
  :deep(.column-tasks) {
    flex: 0 0 30%;
  }
  
  :deep(.column-selected) {
    flex: 0 0 25%;
  }
  
  :deep(.column-config) {
    flex: 1;
  }
}

// 过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// Element Plus 组件样式覆盖
:deep(.el-button) {
  border-radius: 6px;
}

:deep(.el-table) {
  border-radius: 6px;
  
  th.el-table__cell {
    background-color: #fafafa;
    color: @text-secondary;
    font-weight: 500;
  }
}

:deep(.el-tag) {
  border-radius: 4px;
}
</style>
