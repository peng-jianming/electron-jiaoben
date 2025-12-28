<template>
  <div class="pathfinding-panel">
    <!-- 截图工具卡片 -->
    <section class="card pathfinding-card">
      <div class="card-header">
        <div class="card-icon pathfinding-icon">
          <el-icon><Position /></el-icon>
        </div>
        <h2>寻路测试</h2>
      </div>
      
      <div class="card-body">
        <div class="screenshot-controls">
          <h3 class="section-title">
            <el-icon><Camera /></el-icon>
            屏幕截图工具
          </h3>
          <p class="section-desc">创建一个透明选区窗口，然后开始连续截图以捕获该区域的内容</p>
          
          <div class="button-group">
            <el-button 
              :type="captureWindowOpen ? 'danger' : 'primary'" 
              :icon="captureWindowOpen ? Close : Crop"
              @click="toggleCaptureWindow"
              class="control-btn"
            >
              {{ captureWindowOpen ? '关闭截图窗口' : '打开截图窗口' }}
            </el-button>
            
            <el-button 
              :type="isCapturing ? 'warning' : 'success'" 
              :icon="isCapturing ? VideoPause : VideoPlay"
              :disabled="!captureWindowOpen"
              @click="toggleCapturing"
              class="control-btn"
            >
              {{ isCapturing ? '停止截图' : '开始截图' }}
            </el-button>
          </div>
          
          <div class="status-info" v-if="captureWindowOpen">
            <div class="status-item">
              <span class="status-label">截图窗口:</span>
              <el-tag type="success" size="small">已打开</el-tag>
            </div>
            <div class="status-item">
              <span class="status-label">截图状态:</span>
              <el-tag :type="isCapturing ? 'warning' : 'info'" size="small">
                {{ isCapturing ? '正在截图...' : '未开始' }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 路径规划卡片 -->
    <section class="card pathfinding-card">
      <div class="card-header">
        <div class="card-icon route-icon">
          <el-icon><Guide /></el-icon>
        </div>
        <h2>路径规划</h2>
      </div>
      
      <div class="card-body">
        <div class="pathfinding-controls">
          <h3 class="section-title">
            <el-icon><MapLocation /></el-icon>
            地图与路线规划
          </h3>
          <p class="section-desc">载入二值化地图，设置起点和终点，然后进行路径规划</p>
          
          <!-- 载入地图 -->
          <div class="control-row">
            <el-button 
              type="primary" 
              :icon="Upload"
              @click="loadMap"
              class="control-btn"
            >
              载入地图
            </el-button>
            <span class="file-name" v-if="mapLoaded">{{ mapFileName }}</span>
          </div>

          <!-- 起点终点设置 -->
          <div class="points-row" v-if="mapLoaded">
            <div class="point-input">
              <span class="point-label start-label">起点:</span>
              <el-input-number 
                v-model="startPoint.x" 
                :min="0" 
                size="small" 
                placeholder="X"
                controls-position="right"
              />
              <el-input-number 
                v-model="startPoint.y" 
                :min="0" 
                size="small" 
                placeholder="Y"
                controls-position="right"
              />
              <el-button 
                type="success" 
                size="small"
                :icon="Aim"
                @click="setStartPoint"
                :disabled="!mapWindowOpen"
              >
                点击选取
              </el-button>
            </div>
            <div class="point-input">
              <span class="point-label end-label">终点:</span>
              <el-input-number 
                v-model="endPoint.x" 
                :min="0" 
                size="small" 
                placeholder="X"
                controls-position="right"
              />
              <el-input-number 
                v-model="endPoint.y" 
                :min="0" 
                size="small" 
                placeholder="Y"
                controls-position="right"
              />
              <el-button 
                type="danger" 
                size="small"
                :icon="Aim"
                @click="setEndPoint"
                :disabled="!mapWindowOpen"
              >
                点击选取
              </el-button>
            </div>
          </div>

          <!-- 路径规划按钮 -->
          <div class="button-group" v-if="mapLoaded">
            <el-button 
              type="warning" 
              :icon="Promotion"
              @click="planRoute"
              :disabled="!hasValidPoints"
              :loading="planning"
              class="control-btn"
            >
              {{ planning ? '规划中...' : '进行路线规划' }}
            </el-button>
            <el-button 
              v-if="hasPath"
              type="info" 
              :icon="Delete"
              @click="clearPath"
              class="control-btn"
            >
              清除路径
            </el-button>
          </div>

          <!-- 状态信息 -->
          <div class="status-info" v-if="mapLoaded">
            <div class="status-item">
              <span class="status-label">地图尺寸:</span>
              <el-tag type="info" size="small">{{ mapSize.width }} × {{ mapSize.height }}</el-tag>
            </div>
            <div class="status-item" v-if="hasPath">
              <span class="status-label">路径长度:</span>
              <el-tag type="success" size="small">{{ pathLength }} 步</el-tag>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { Position, Camera, Crop, Close, VideoPlay, VideoPause, Upload, MapLocation, Guide, Aim, Promotion, Delete } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { ipc } from '@/utils/ipcRenderer';
import { ipcApiRoute } from '@/api/index';
import { io } from 'socket.io-client';

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

.card {
  background: var(--bg-card);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s ease;
}

.card:hover {
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: var(--shadow-lg);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(51, 65, 85, 0.3);
  border-bottom: 1px solid var(--border-color);
}

.card-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  flex: 1;
}

.card-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.card-body {
  padding: 24px;
}

.pathfinding-card {
  background: linear-gradient(135deg, var(--bg-card) 0%, rgba(236, 72, 153, 0.05) 100%);
}

.pathfinding-icon {
  background: linear-gradient(135deg, #ec4899, #f472b6);
  color: white;
}

.route-icon {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  color: white;
}

/* 截图控制区域 */
.screenshot-controls,
.pathfinding-controls {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.section-title .el-icon {
  color: #ec4899;
}

.pathfinding-controls .section-title .el-icon {
  color: #f59e0b;
}

.section-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.6;
}

.button-group {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.control-btn {
  padding: 12px 24px !important;
  font-size: 15px !important;
  font-weight: 500;
  border-radius: 10px !important;
  transition: all 0.3s ease;
}

.control-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.control-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.file-name {
  font-size: 14px;
  color: var(--text-secondary);
  background: rgba(51, 65, 85, 0.4);
  padding: 6px 12px;
  border-radius: 6px;
}

.points-row {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.point-input {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.point-label {
  font-size: 14px;
  font-weight: 600;
  min-width: 50px;
}

.start-label {
  color: #10b981;
}

.end-label {
  color: #ef4444;
}

.point-input :deep(.el-input-number) {
  width: 100px;
}

.point-input :deep(.el-input-number .el-input__inner) {
  background: rgba(51, 65, 85, 0.4);
  border-color: var(--border-color);
  color: var(--text-primary);
}

.status-info {
  display: flex;
  gap: 24px;
  padding: 16px 20px;
  background: rgba(51, 65, 85, 0.4);
  border-radius: 10px;
  border: 1px solid var(--border-color);
  flex-wrap: wrap;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-label {
  font-size: 14px;
  color: var(--text-secondary);
}
</style>

