<template>
  <div class="app-container">
    <TitleBar title="设备管理系统" />

    <div class="main-wrapper">
      <!-- 左侧导航栏 -->
      <aside class="sidebar">
        <div class="nav-menu">
          <div
            class="nav-item"
            :class="{ active: currentTab === 'account' }"
            @click="currentTab = 'account'"
            title="账号管理"
          >
            <el-icon :size="22"><User /></el-icon>
            <span class="nav-label">账号</span>
          </div>
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
        </div>
        
        <!-- 底部状态指示 -->
        <div class="sidebar-footer">
          <div class="status-indicator">
            <span class="status-dot" :class="{ online: isBackendReady, waiting: isConnected && !isBackendReady }"></span>
            <span class="status-text">{{ isBackendReady ? '已连接' : isConnected ? '等待后端' : '未连接' }}</span>
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
              <el-button 
                v-if="currentTab === 'account'"
                type="primary" 
                plain 
                size="small"
                @click="handleGetAccountList"
              >
                <el-icon><Refresh /></el-icon>
                刷新账号
              </el-button>
            </div>
          </div>
          
          <div class="panel-body">
            <Account
              v-show="currentTab === 'account'"
              :list="accountList"
              :taskSelectValue="taskSelectValue"
              @startTask="handleStartAccountTask"
              @pauseTask="handlePauseAccountTask"
              @resumeTask="handleResumeAccountTask"
              @endTask="handleEndAccountTask"
              @batchStart="handleBatchStart"
              @batchPause="handleBatchPause"
              @batchResume="handleBatchResume"
              @batchEnd="handleBatchEnd"
              @openLog="handleOpenLog"
            />
            <Device
              v-show="currentTab === 'device'"
              :list="deviceList"
            />
            <Task
              v-show="currentTab === 'task'"
              :task-list="taskList"
              v-model="taskSelectValue"
              @reload="handleGetTaskList"
              class="task-select-full"
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
import { ElMessage } from "element-plus";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import { io } from "socket.io-client";

const currentTab = ref("account");
const isConnected = ref(false);
const isBackendReady = ref(false);
const deviceList = ref([]);
const taskList = ref([]);
const accountList = ref([]);

const taskSelectValue = ref({
  selectedTasks: [],
  taskConfig: {},
});

// 加载任务配置
async function loadTaskConfig() {
  if (!ipc) return;
  try {
    const res = await ipc.invoke(ipcApiRoute.获取任务配置);
    if (!res || typeof res !== "object") return;
    taskSelectValue.value = {
      selectedTasks: Array.isArray(res.selectedTasks) ? res.selectedTasks : [],
      taskConfig: res.taskConfig != null ? res.taskConfig : [],
    };
  } catch (e) {}
}

async function saveTaskConfig() {
  if (!ipc) return;
  try {
    await ipc.invoke(ipcApiRoute.保存任务配置, {
      taskSelectValue: {
        selectedTasks: JSON.parse(JSON.stringify([...taskSelectValue.value.selectedTasks])),
        taskConfig: JSON.parse(JSON.stringify(taskSelectValue.value.taskConfig)),
      },
    });
  } catch (e) {}
}

const panelTitle = computed(() => {
  const titles = {
    device: '设备管理',
    task: '任务配置',
    account: '账号管理'
  };
  return titles[currentTab.value] || '';
});

let matchSocket = null;

// 更新账号状态（合并 socket 推送的字段到对应账号行）
function updateAccountStatus(statusData) {
  const 账号key = statusData.账号;
  if (!账号key) return;

  const index = accountList.value.findIndex((item) => item.账号 === 账号key);
  if (index === -1) return;

  // if (statusData.日志) {
  //   if (!Array.isArray(accountList.value[index].日志)) {
  //     accountList.value[index].日志 = [];
  //   }
  //   accountList.value[index].日志.push(`[${new Date().toLocaleTimeString()}] ${statusData.日志}`);
  //   if (accountList.value[index].日志.length > 50) {
  //     accountList.value[index].日志.splice(0, accountList.value[index].日志.length - 50);
  //   }
  //   return;
  // }

  accountList.value[index] = {
    ...accountList.value[index],
    ...statusData,
  };
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
    });

    matchSocket.on("disconnect", () => {
      console.log("匹配 Socket 断开连接");
      isConnected.value = false;
      isBackendReady.value = false;
    });

    matchSocket.on("backend-ready", () => {
      console.log("后端已准备就绪");
      isBackendReady.value = true;
      handleGetDeviceList();
      handleGetTaskList();
      handleGetAccountList();
    });

    matchSocket.on("device-list", (data) => {
      console.log("收到设备列表:", data);
      deviceList.value = Array.isArray(data) ? data : [];
    });

    matchSocket.on("task-list", (data) => {
      console.log("收到任务列表:", data);
      taskList.value = data;
      resolve();
    });

    matchSocket.on("account-list", (data) => {
      console.log("收到账号列表:", data);
      if (Array.isArray(data)) {
        accountList.value = data.map((item) => ({
          ...item,
          设备ID: "",
          状态: "空闲",
          当前任务: "",
          日志: "",
        }));
      }
    });

    matchSocket.on("account-status-update", (data) => {
      console.log("收到账号状态更新:", data);
      updateAccountStatus(data);
    });
  });
}

// ─── 发送指令到后端 ──────────────────────────

function sendToBackend(类型, extra = {}) {
  if (!isBackendReady.value) {
    ElMessage.warning("后端还未连接，请稍候...");
    return;
  }
  ipc.invoke(ipcApiRoute.发送到后端, { 类型, ...extra });
}

const handleGetDeviceList = () => sendToBackend("获取设备列表");
const handleGetTaskList = () => sendToBackend("获取任务列表");
const handleGetAccountList = () => sendToBackend("获取账号列表");

// ─── 账号操作 ────────────────────────────────

const handleStartAccountTask = (row) => {
  const { selectedTasks, taskConfig } = taskSelectValue.value;
  sendToBackend("账号开始任务", {
    账号: row.账号,
    任务队列: JSON.parse(JSON.stringify([...selectedTasks])),
    任务配置: JSON.parse(JSON.stringify(taskConfig)),
  });
};

const handleEndAccountTask = (row) => {
  sendToBackend("账号结束任务", { 账号: row.账号 });
};

const handlePauseAccountTask = (row) => {
  sendToBackend("账号暂停任务", { 账号: row.账号 });
};

const handleResumeAccountTask = (row) => {
  sendToBackend("账号恢复任务", { 账号: row.账号 });
};

const handleOpenLog = (row) => {
  sendToBackend("打开日志", { 账号: row.账号 });
};

// ─── 批量操作 ────────────────────────────────

const handleBatchStart = () => {
  const { selectedTasks, taskConfig } = taskSelectValue.value;
  sendToBackend("全部开始", {
    任务队列: JSON.parse(JSON.stringify([...selectedTasks])),
    任务配置: JSON.parse(JSON.stringify(taskConfig)),
  });
};

const handleBatchPause = () => sendToBackend("全部暂停");
const handleBatchResume = () => sendToBackend("全部恢复");
const handleBatchEnd = () => sendToBackend("全部结束");

// 监听任务选择变更，自动持久化
watch(taskSelectValue, () => saveTaskConfig(), { deep: true });

onMounted(async () => {
  await initMatchSocket();
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
  
  &.waiting {
    background-color: @warning-color;
    box-shadow: 0 0 8px rgba(245, 158, 11, 0.5);
    animation: pulse 1s infinite;
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
