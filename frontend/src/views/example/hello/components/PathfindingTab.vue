<template>
  <div class="pathfinding-panel">
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
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { Position, Camera, Crop, Close, VideoPlay, VideoPause } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { ipc } from '@/utils/ipcRenderer';
import { ipcApiRoute } from '@/api/index';

// 状态
const captureWindowOpen = ref(false);
const isCapturing = ref(false);

// 切换截图窗口
async function toggleCaptureWindow() {
  try {
    if (captureWindowOpen.value) {
      // 关闭窗口
      const result = await ipc.invoke(ipcApiRoute.closeCaptureWindow, {});
      if (result.success) {
        captureWindowOpen.value = false;
        isCapturing.value = false;
        ElMessage.success('截图窗口已关闭');
      }
    } else {
      // 打开窗口
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

// 切换截图状态
async function toggleCapturing() {
  try {
    if (isCapturing.value) {
      // 停止截图
      const result = await ipc.invoke(ipcApiRoute.stopCapturing, {});
      if (result.success) {
        isCapturing.value = false;
        ElMessage.info('已停止截图');
      }
    } else {
      // 开始截图
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

// 组件挂载时获取状态
onMounted(async () => {
  try {
    const status = await ipc.invoke(ipcApiRoute.getCaptureStatus, {});
    captureWindowOpen.value = status.hasCaptureWindow;
    isCapturing.value = status.isCapturing;
  } catch (error) {
    console.error('获取状态错误:', error);
  }
});

// 组件卸载时停止截图
onUnmounted(async () => {
  if (isCapturing.value) {
    try {
      await ipc.invoke(ipcApiRoute.stopCapturing, {});
    } catch (error) {
      console.error('停止截图错误:', error);
    }
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

/* 截图控制区域 */
.screenshot-controls {
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

.status-info {
  display: flex;
  gap: 24px;
  padding: 16px 20px;
  background: rgba(51, 65, 85, 0.4);
  border-radius: 10px;
  border: 1px solid var(--border-color);
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

