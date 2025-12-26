<template>
  <div class="image-processor">
    <!-- 顶部标题栏 -->
    <header class="app-header">
      <div class="header-content">
        <div class="logo-section">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
              <circle cx="12" cy="13" r="4"/>
            </svg>
          </div>
          <h1>OpenCV 图像处理工具</h1>
        </div>
        <div class="header-actions">
          <el-button 
            type="success" 
            :icon="Download" 
            :disabled="!imageLoaded || processing"
            @click="handleSaveImage"
            class="save-btn"
          >
            保存图片
          </el-button>
        </div>
      </div>
    </header>

    <main class="main-content">
      <!-- 图像上传卡片 -->
      <section class="card upload-card">
        <div class="card-header">
          <div class="card-icon upload-icon">
            <el-icon><Upload /></el-icon>
          </div>
          <h2>图像加载</h2>
        </div>
        <div class="card-body">
          <el-upload
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleImageSelect"
            accept="image/*"
            drag
            class="upload-dragger"
          >
            <div class="upload-content">
              <el-icon class="upload-big-icon"><Upload /></el-icon>
              <div class="upload-text">
                <p class="primary-text">拖拽图像文件到此处</p>
                <p class="secondary-text">或点击选择文件</p>
              </div>
            </div>
          </el-upload>
          <div v-if="imageFileName" class="file-info">
            <el-icon><Document /></el-icon>
            <span>{{ imageFileName }}</span>
          </div>
        </div>
      </section>

      <!-- 处理选项区域 -->
      <div v-if="imageLoaded" class="processing-options">
        <!-- 颜色过滤卡片 -->
        <section class="card filter-card">
          <div class="card-header">
            <div class="card-icon filter-icon">
              <el-icon><Brush /></el-icon>
            </div>
            <h2>颜色过滤</h2>
            <el-switch 
              v-model="enableColorFilter" 
              @change="handleColorFilterToggle"
              class="header-switch"
            />
          </div>
          
          <div class="card-body">
            <!-- 保留颜色 -->
            <div class="filter-group">
              <div class="group-header">
                <span class="group-label">保留颜色</span>
                <el-button 
                  type="primary" 
                  size="small" 
                  :icon="Plus"
                  circle
                  @click="addKeepColor"
                />
              </div>
              <div class="color-inputs">
                <div 
                  v-for="(item, index) in keepColors"
                  :key="'keep-' + index"
                  class="color-input-row"
                >
                  <div 
                    class="color-preview" 
                    :style="{ backgroundColor: getColorPreview(keepColors[index]) }"
                  ></div>
                  <el-input
                    v-model="keepColors[index]"
                    placeholder="格式: RRGGBB-容差"
                    @input="processImage"
                  />
                  <el-button 
                    type="danger" 
                    size="small"
                    :icon="Delete" 
                    circle
                    @click="removeKeepColor(index)"
                  />
                </div>
              </div>
            </div>

            <!-- 过滤颜色 -->
            <div class="filter-group">
              <div class="group-header">
                <span class="group-label">过滤颜色</span>
                <el-button 
                  type="primary" 
                  size="small" 
                  :icon="Plus"
                  circle
                  @click="addFilterColor"
                />
              </div>
              <div class="color-inputs">
                <div 
                  v-for="(item, index) in filterColors"
                  :key="'filter-' + index"
                  class="color-input-row"
                >
                  <div 
                    class="color-preview" 
                    :style="{ backgroundColor: getColorPreview(filterColors[index]) }"
                  ></div>
                  <el-input
                    v-model="filterColors[index]"
                    placeholder="格式: RRGGBB-容差"
                    @input="processImage"
                  />
                  <el-button 
                    type="danger" 
                    size="small"
                    :icon="Delete" 
                    circle
                    @click="removeFilterColor(index)"
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 二值化卡片 -->
        <section class="card binary-card">
          <div class="card-header">
            <div class="card-icon binary-icon">
              <el-icon><MagicStick /></el-icon>
            </div>
            <h2>二值化处理</h2>
            <el-switch 
              v-model="enableBinary" 
              @change="handleBinaryToggle"
              class="header-switch"
            />
          </div>
          
          <div class="card-body">
            <div class="threshold-control">
              <div class="threshold-label">
                <span>阈值</span>
                <span class="threshold-value">{{ threshold }}</span>
              </div>
              <el-slider
                v-model="threshold"
                :min="0"
                :max="255"
                :step="1"
                @change="processImage"
                :marks="{ 0: '0', 127: '127', 255: '255' }"
              />
            </div>
          </div>
        </section>

        <!-- 洪水填充卡片 -->
        <section class="card flood-card">
          <div class="card-header">
            <div class="card-icon flood-icon">
              <el-icon><Aim /></el-icon>
            </div>
            <h2>洪水填充</h2>
            <el-switch 
              v-model="enableFloodFill" 
              @change="handleFloodFillToggle"
              :disabled="!floodFillStartPoint"
              class="header-switch"
            />
          </div>
          
          <div class="card-body">
            <div class="flood-info">
              <el-alert
                v-if="!floodFillStartPoint"
                type="info"
                :closable="false"
                show-icon
              >
                请在图片上点击选择填充起始位置
              </el-alert>
              <div v-else class="point-display">
                <el-tag type="success" effect="dark" size="large">
                  <el-icon><Location /></el-icon>
                  起始位置: ({{ floodFillStartPoint.x }}, {{ floodFillStartPoint.y }})
                </el-tag>
              </div>
            </div>
            
            <div class="batch-control">
              <span class="batch-label">每批填充像素数:</span>
              <el-input-number
                v-model="floodFillBatchSize"
                :min="1"
                :max="10000"
                :step="50"
                size="default"
              />
            </div>
          </div>
        </section>
      </div>

      <!-- 处理状态指示器 -->
      <transition name="fade">
        <div v-if="processing" class="processing-indicator">
          <div class="spinner"></div>
          <span>处理中...</span>
        </div>
      </transition>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import { io } from "socket.io-client";
import { Upload, Delete, Plus, Document, Brush, MagicStick, Aim, Location, Download } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const imageFileName = ref(null);
const threshold = ref(127);
const processing = ref(false);
const imageLoaded = ref(false);
const enableBinary = ref(false);
const enableColorFilter = ref(false);
const enableFloodFill = ref(false);
const floodFillBatchSize = ref(100);
const floodFillStartPoint = ref(null);
const keepColors = ref([]);
const filterColors = ref([]);

let socket = null;

// 获取颜色预览
function getColorPreview(colorStr) {
  if (!colorStr) return 'transparent';
  const parts = colorStr.split('-');
  const hex = parts[0];
  if (hex && hex.length === 6) {
    return `#${hex}`;
  }
  return 'transparent';
}

// 处理图像选择
function handleImageSelect(file) {
  const fileObj = file.raw || file;
  if (!fileObj) return;

  imageFileName.value = fileObj.name;
  processing.value = true;
  enableBinary.value = false;
  enableColorFilter.value = false;
  enableFloodFill.value = false;
  floodFillStartPoint.value = null;
  imageLoaded.value = true;

  const imagePath = fileObj.path || fileObj.name;
  
  if (!imagePath) {
    console.error("无法获取文件路径");
    processing.value = false;
    return;
  }

  ipc.invoke(ipcApiRoute.sendToPython, {
    type: 'upload_image',
    path: imagePath
  }).catch((error) => {
    console.error("发送图像路径失败:", error);
    processing.value = false;
  });
}

// 保存图片
async function handleSaveImage() {
  try {
    // 生成默认文件名
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const defaultName = `processed_${timestamp}.png`;
    
    // 打开保存对话框
    const result = await ipc.invoke(ipcApiRoute.openSaveDialog, {
      defaultName: defaultName
    });
    
    if (!result.success || result.canceled) {
      return;
    }
    
    processing.value = true;
    
    // 发送保存请求到 Python
    await ipc.invoke(ipcApiRoute.sendToPython, {
      type: 'save_image',
      savePath: result.filePath
    });
    
  } catch (error) {
    console.error("保存图片失败:", error);
    ElMessage.error(`保存失败: ${error.message || '未知错误'}`);
    processing.value = false;
  }
}

// 添加保留颜色
function addKeepColor() {
  keepColors.value.push('');
}

// 移除保留颜色
function removeKeepColor(index) {
  keepColors.value.splice(index, 1);
  processImage();
}

// 添加过滤颜色
function addFilterColor() {
  filterColors.value.push('');
}

// 移除过滤颜色
function removeFilterColor(index) {
  filterColors.value.splice(index, 1);
  processImage();
}

// 处理颜色过滤开关切换
function handleColorFilterToggle() {
  processImage();
}

// 处理二值化开关切换
function handleBinaryToggle() {
  processImage();
}

// 处理洪水填充开关切换
function handleFloodFillToggle() {
  if (enableFloodFill.value) {
    if (floodFillStartPoint.value) {
      startFloodFill();
    }
  } else {
    clearFloodFill();
  }
}

// 清除洪水填充效果
function clearFloodFill() {
  processing.value = true;
  
  const requestData = {
    type: 'clear_flood_fill',
  };
  
  if (enableColorFilter.value) {
    const validKeepColors = keepColors.value.filter(c => c && c.trim());
    const validFilterColors = filterColors.value.filter(c => c && c.trim());
    
    if (validKeepColors.length > 0 || validFilterColors.length > 0) {
      requestData.enableColorFilter = true;
      requestData.keepColors = validKeepColors;
      requestData.filterColors = validFilterColors;
    } else {
      requestData.enableColorFilter = false;
    }
  } else {
    requestData.enableColorFilter = false;
  }
  
  if (enableBinary.value) {
    requestData.enableBinary = true;
    requestData.threshold = threshold.value;
  } else {
    requestData.enableBinary = false;
  }
  
  ipc.invoke(ipcApiRoute.sendToPython, requestData).catch((error) => {
    console.error("清除洪水填充失败:", error);
    processing.value = false;
  });
}

// 处理图片点击事件
function handleImageClick(x, y) {
  if (!imageLoaded.value) return;
  
  floodFillStartPoint.value = { x, y };
  console.log(`已选择洪水填充起始位置: (${x}, ${y})`);
  
  if (enableFloodFill.value) {
    startFloodFill();
  }
}

// 开始洪水填充
function startFloodFill() {
  if (!floodFillStartPoint.value) {
    ElMessage.warning('请先选择填充起始位置');
    enableFloodFill.value = false;
    return;
  }
  
  const processPromise = new Promise((resolve) => {
    processImage();
    
    const checkProcessing = setInterval(() => {
      if (!processing.value) {
        clearInterval(checkProcessing);
        resolve();
      }
    }, 100);
  });
  
  processPromise.then(() => {
    processing.value = true;
    
    const requestData = {
      type: 'flood_fill',
      x: floodFillStartPoint.value.x,
      y: floodFillStartPoint.value.y,
      batchSize: floodFillBatchSize.value,
    };
    
    ipc.invoke(ipcApiRoute.sendToPython, requestData).catch((error) => {
      console.error("洪水填充失败:", error);
      processing.value = false;
      ElMessage.error(`洪水填充失败: ${error.message || '未知错误'}`);
    });
  });
}

// 统一的图像处理函数
function processImage() {
  if (!imageLoaded.value) return;
  
  processing.value = true;
  
  const requestData = {
    type: 'process_image',
  };
  
  if (enableColorFilter.value) {
    const validKeepColors = keepColors.value.filter(c => c && c.trim());
    const validFilterColors = filterColors.value.filter(c => c && c.trim());
    
    if (validKeepColors.length > 0 || validFilterColors.length > 0) {
      requestData.enableColorFilter = true;
      requestData.keepColors = validKeepColors;
      requestData.filterColors = validFilterColors;
    } else {
      requestData.enableColorFilter = false;
    }
  } else {
    requestData.enableColorFilter = false;
  }
  
  if (enableBinary.value) {
    requestData.enableBinary = true;
    requestData.threshold = threshold.value;
  } else {
    requestData.enableBinary = false;
  }
  
  if (enableFloodFill.value) {
    requestData.enableFloodFill = true;
    requestData.floodFillBatchSize = floodFillBatchSize.value;
  } else {
    requestData.enableFloodFill = false;
  }
  
  ipc.invoke(ipcApiRoute.sendToPython, requestData).catch((error) => {
    console.error("图像处理失败:", error);
    processing.value = false;
    ElMessage.error(`图像处理失败: ${error.message || '未知错误'}`);
  });
}

// 接收 Python 处理结果
const handleProcessedImage = (data) => {
  processing.value = false;
  
  if (data && !data.success) {
    console.error("图像处理失败:", data.error);
    ElMessage.error(`处理失败: ${data.error || '未知错误'}`);
  }
};

// 处理保存结果
const handleSaveResult = (data) => {
  processing.value = false;
  
  if (data && data.success) {
    ElMessage.success(`图片已保存: ${data.path}`);
  } else if (data && data.error) {
    ElMessage.error(`保存失败: ${data.error}`);
  }
};

onMounted(() => {
  socket = io("ws://localhost:7070");
  socket.on("connect", () => {
    console.log("Socket 连接成功");
  });

  socket.on("image-processed", (response) => {
    console.log("收到处理结果:", response);
    handleProcessedImage(response);
  });
  
  socket.on("image-saved", (response) => {
    console.log("收到保存结果:", response);
    handleSaveResult(response);
  });
  
  if (ipc) {
    ipc.on('image-click', (event, data) => {
      console.log("收到图片点击事件:", data);
      handleImageClick(data.x, data.y);
    });
  } else if (window.ipcRenderer) {
    window.ipcRenderer.on('image-click', (event, data) => {
      console.log("收到图片点击事件:", data);
      handleImageClick(data.x, data.y);
    });
  } else if (window.electron && window.electron.ipcRenderer) {
    window.electron.ipcRenderer.on('image-click', (event, data) => {
      console.log("收到图片点击事件:", data);
      handleImageClick(data.x, data.y);
    });
  }
});

onUnmounted(() => {
  if (socket) {
    socket.disconnect();
  }
  
  if (ipc) {
    ipc.removeAllListeners('image-click');
  } else if (window.ipcRenderer) {
    window.ipcRenderer.removeAllListeners('image-click');
  } else if (window.electron && window.electron.ipcRenderer) {
    window.electron.ipcRenderer.removeAllListeners('image-click');
  }
});
</script>

<style scoped>
/* 基础变量 */
.image-processor {
  --primary-color: #6366f1;
  --primary-light: #818cf8;
  --primary-dark: #4f46e5;
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --danger-color: #ef4444;
  --bg-dark: #0f172a;
  --bg-card: #1e293b;
  --bg-card-hover: #334155;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --border-color: #334155;
  --shadow-lg: 0 10px 40px rgba(0, 0, 0, 0.3);
  
  min-height: 100vh;
  background: linear-gradient(135deg, var(--bg-dark) 0%, #1a1a2e 50%, #16213e 100%);
  color: var(--text-primary);
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* 顶部标题栏 */
.app-header {
  background: rgba(30, 41, 59, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.logo-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

.logo-section h1 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  background: linear-gradient(90deg, var(--text-primary), var(--primary-light));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.save-btn {
  padding: 10px 20px !important;
  font-weight: 500;
  border-radius: 8px !important;
  transition: all 0.3s ease;
}

.save-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

/* 主内容区 */
.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

/* 卡片样式 */
.card {
  background: var(--bg-card);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  margin-bottom: 20px;
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

.upload-icon {
  background: linear-gradient(135deg, #3b82f6, #60a5fa);
  color: white;
}

.filter-icon {
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
  color: white;
}

.binary-icon {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  color: white;
}

.flood-icon {
  background: linear-gradient(135deg, #10b981, #34d399);
  color: white;
}

.header-switch {
  --el-switch-on-color: var(--primary-color);
}

.card-body {
  padding: 20px;
}

/* 上传区域 */
.upload-card {
  background: linear-gradient(135deg, var(--bg-card) 0%, rgba(59, 130, 246, 0.05) 100%);
}

.upload-dragger {
  width: 100%;
}

.upload-dragger :deep(.el-upload-dragger) {
  background: transparent;
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  transition: all 0.3s ease;
  padding: 40px 20px;
}

.upload-dragger :deep(.el-upload-dragger:hover) {
  border-color: var(--primary-color);
  background: rgba(99, 102, 241, 0.05);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.upload-big-icon {
  font-size: 48px;
  color: var(--primary-light);
}

.upload-text {
  text-align: center;
}

.primary-text {
  font-size: 16px;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.secondary-text {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 12px 16px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 8px;
  color: var(--primary-light);
  font-size: 14px;
}

/* 处理选项区域 */
.processing-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
}

/* 颜色过滤 */
.filter-group {
  margin-bottom: 20px;
}

.filter-group:last-child {
  margin-bottom: 0;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.group-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.color-inputs {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.color-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.color-preview {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 2px solid var(--border-color);
  flex-shrink: 0;
}

.color-input-row :deep(.el-input) {
  flex: 1;
}

/* 二值化控制 */
.threshold-control {
  padding: 0 4px;
}

.threshold-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.threshold-label span {
  font-size: 14px;
  color: var(--text-secondary);
}

.threshold-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--primary-light) !important;
}

.threshold-control :deep(.el-slider__runway) {
  background: var(--border-color);
}

.threshold-control :deep(.el-slider__bar) {
  background: linear-gradient(90deg, var(--primary-color), var(--primary-light));
}

.threshold-control :deep(.el-slider__button) {
  border-color: var(--primary-color);
}

/* 洪水填充 */
.flood-info {
  margin-bottom: 16px;
}

.point-display {
  display: flex;
  align-items: center;
}

.point-display :deep(.el-tag) {
  padding: 8px 16px;
  font-size: 14px;
}

.batch-control {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(51, 65, 85, 0.3);
  border-radius: 8px;
}

.batch-label {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 处理状态指示器 */
.processing-indicator {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  background: var(--bg-card);
  border: 1px solid var(--primary-color);
  border-radius: 12px;
  box-shadow: var(--shadow-lg);
  z-index: 1000;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 过渡动画 */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Element Plus 样式覆盖 */
:deep(.el-input__wrapper) {
  background: rgba(51, 65, 85, 0.5);
  border: 1px solid var(--border-color);
  box-shadow: none !important;
}

:deep(.el-input__wrapper:hover) {
  border-color: var(--primary-color);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: var(--primary-color);
}

:deep(.el-input__inner) {
  color: var(--text-primary);
}

:deep(.el-input-number) {
  --el-input-bg-color: rgba(51, 65, 85, 0.5);
  --el-input-border-color: var(--border-color);
  --el-input-hover-border-color: var(--primary-color);
  --el-input-focus-border-color: var(--primary-color);
}

:deep(.el-alert) {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

:deep(.el-alert .el-alert__description) {
  color: var(--text-secondary);
}
</style>
