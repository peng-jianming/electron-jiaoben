<template>
  <div class="pathfinding-panel">
    <!-- 截图工具卡片 -->
    <ScreenshotCard
      :capture-window-open="captureWindowOpen"
      :is-capturing="isCapturing"
      @toggle-capture-window="toggleCaptureWindow"
      @toggle-capturing="toggleCapturing"
    />

    <!-- 路径规划卡片 -->
    <PathPlanningCard
      :map-loaded="mapLoaded"
      :map-window-open="mapWindowOpen"
      :map-file-name="mapFileName"
      :map-size="mapSize"
      :start-point="startPoint"
      :end-point="endPoint"
      :planning="planning"
      :has-path="hasPath"
      :path-length="pathLength"
      :has-valid-points="hasValidPoints"
      @load-map="loadMap"
      @set-start-point="setStartPoint"
      @set-end-point="setEndPoint"
      @update-start-point="startPoint = $event"
      @update-end-point="endPoint = $event"
      @plan-route="planRoute"
      @clear-path="clearPath"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import { ipc } from '@/utils/ipcRenderer';
import { ipcApiRoute } from '@/api/index';
import { io } from 'socket.io-client';
import ScreenshotCard from './cards/ScreenshotCard.vue';
import PathPlanningCard from './cards/PathPlanningCard.vue';

// ========== 截图功能状态 ==========
const captureWindowOpen = ref(false);
const isCapturing = ref(false);

// ========== 路径规划状态 ==========
const mapLoaded = ref(false);
const mapWindowOpen = ref(false);
const mapFileName = ref('');
const mapSize = ref({ width: 0, height: 0 });
const startPoint = ref({ x: 0, y: 0 });
const endPoint = ref({ x: 0, y: 0 });
const planning = ref(false);
const hasPath = ref(false);
const pathLength = ref(0);
const selectingPoint = ref(null); // 'start' | 'end' | null

let socket = null;

// 计算是否有有效的起点和终点
const hasValidPoints = computed(() => {
  return startPoint.value.x >= 0 && startPoint.value.y >= 0 &&
         endPoint.value.x >= 0 && endPoint.value.y >= 0 &&
         (startPoint.value.x !== endPoint.value.x || startPoint.value.y !== endPoint.value.y);
});

// ========== 截图功能 ==========
async function toggleCaptureWindow() {
  try {
    if (captureWindowOpen.value) {
      const result = await ipc.invoke(ipcApiRoute.closeCaptureWindow, {});
      if (result.success) {
        captureWindowOpen.value = false;
        isCapturing.value = false;
        ElMessage.success('截图窗口已关闭');
      }
    } else {
      const result = await ipc.invoke(ipcApiRoute.openCaptureWindow, {});
      if (result.success) {
        captureWindowOpen.value = true;
        ElMessage.success('截图窗口已打开，请移动并调整窗口大小');
      }
    }
  } catch (error) {
    console.error('截图窗口操作错误:', error);
    ElMessage.error('操作失败: ' + error.message);
  }
}

async function toggleCapturing() {
  try {
    if (isCapturing.value) {
      const result = await ipc.invoke(ipcApiRoute.stopCapturing, {});
      if (result.success) {
        isCapturing.value = false;
        ElMessage.info('已停止截图');
      }
    } else {
      const result = await ipc.invoke(ipcApiRoute.startCapturing, {});
      if (result.success) {
        isCapturing.value = true;
        ElMessage.success('开始连续截图，每秒捕获一次');
      } else {
        ElMessage.warning(result.message);
      }
    }
  } catch (error) {
    console.error('截图状态切换错误:', error);
    ElMessage.error('操作失败: ' + error.message);
  }
}

// ========== 路径规划功能 ==========
async function loadMap() {
  try {
    const result = await ipc.invoke(ipcApiRoute.loadPathfindingMap, {});
    if (result.success) {
      mapLoaded.value = true;
      mapWindowOpen.value = true;
      mapFileName.value = result.fileName;
      mapSize.value = { width: result.width, height: result.height };
      hasPath.value = false;
      pathLength.value = 0;
      ElMessage.success('地图加载成功');
    } else if (!result.canceled) {
      ElMessage.error(result.message || '加载地图失败');
    }
  } catch (error) {
    console.error('加载地图错误:', error);
    ElMessage.error('加载地图失败: ' + error.message);
  }
}

async function setStartPoint() {
  selectingPoint.value = 'start';
  ElMessage.info('请在地图窗口中点击选择起点');
  // 通过 IPC 通知地图窗口进入选点模式
  try {
    await ipc.invoke(ipcApiRoute.setSelectPointMode, { type: 'start' });
  } catch (error) {
    console.error('设置选点模式错误:', error);
  }
}

async function setEndPoint() {
  selectingPoint.value = 'end';
  ElMessage.info('请在地图窗口中点击选择终点');
  // 通过 IPC 通知地图窗口进入选点模式
  try {
    await ipc.invoke(ipcApiRoute.setSelectPointMode, { type: 'end' });
  } catch (error) {
    console.error('设置选点模式错误:', error);
  }
}

async function planRoute() {
  if (!hasValidPoints.value) {
    ElMessage.warning('请先设置有效的起点和终点');
    return;
  }
  
  planning.value = true;
  try {
    // 将 Vue 响应式对象转换为普通对象，避免 IPC 克隆错误
    const result = await ipc.invoke(ipcApiRoute.planPath, {
      start: { x: startPoint.value.x, y: startPoint.value.y },
      end: { x: endPoint.value.x, y: endPoint.value.y }
    });
    
    if (result.success) {
      hasPath.value = true;
      pathLength.value = result.pathLength;
      ElMessage.success(`路径规划成功，共 ${result.pathLength} 步`);
    } else {
      ElMessage.error(result.message || '路径规划失败，可能无法到达终点');
    }
  } catch (error) {
    console.error('路径规划错误:', error);
    ElMessage.error('路径规划失败: ' + error.message);
  } finally {
    planning.value = false;
  }
}

async function clearPath() {
  try {
    await ipc.invoke(ipcApiRoute.clearPath, {});
    hasPath.value = false;
    pathLength.value = 0;
    ElMessage.info('路径已清除');
  } catch (error) {
    console.error('清除路径错误:', error);
  }
}

// 处理地图点击事件
function handleMapClick(data) {
  if (selectingPoint.value === 'start') {
    startPoint.value = { x: data.x, y: data.y };
    ElMessage.success(`起点已设置: (${data.x}, ${data.y})`);
  } else if (selectingPoint.value === 'end') {
    endPoint.value = { x: data.x, y: data.y };
    ElMessage.success(`终点已设置: (${data.x}, ${data.y})`);
  }
  selectingPoint.value = null;
}

// 组件挂载
onMounted(async () => {
  try {
    const status = await ipc.invoke(ipcApiRoute.getCaptureStatus, {});
    captureWindowOpen.value = status.hasCaptureWindow;
    isCapturing.value = status.isCapturing;
  } catch (error) {
    console.error('获取状态错误:', error);
  }

  // 连接 Socket.IO
  socket = io('ws://localhost:7070');
  
  socket.on('connect', () => {
    console.log('PathfindingTab Socket 连接成功');
  });
  
  // 监听地图点击事件
  socket.on('map-point-clicked', (data) => {
    handleMapClick(data);
  });

  // 监听地图窗口关闭事件
  socket.on('map-window-closed', () => {
    mapWindowOpen.value = false;
  });
});

// 组件卸载
onUnmounted(async () => {
  if (isCapturing.value) {
    try {
      await ipc.invoke(ipcApiRoute.stopCapturing, {});
    } catch (error) {
      console.error('停止截图错误:', error);
    }
  }
  if (socket) {
    socket.disconnect();
  }
});
</script>

<style scoped>
.pathfinding-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style>

