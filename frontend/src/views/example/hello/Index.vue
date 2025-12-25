<template>
  <div class="image-processor">
    <el-card class="main-card">
      <template #header>
        <h3>OpenCV 图像处理</h3>
      </template>

      <!-- 图像加载区域 -->
      <div class="upload-section">
        <el-upload
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleImageSelect"
          accept="image/*"
        >
          <el-button type="primary">
            <el-icon><Upload /></el-icon>
            选择图像文件
          </el-button>
        </el-upload>
        <div v-if="imageFileName" class="file-info">
          当前图像: {{ imageFileName }}
        </div>
      </div>

      <!-- 颜色过滤模块 -->
      <div v-if="imageLoaded" class="filter-section">
        <el-checkbox v-model="enableColorFilter" @change="handleColorFilterToggle">
          启用颜色过滤
        </el-checkbox>
        
        <div v-if="enableColorFilter">
          <!-- 保留颜色 -->
          <div class="filter-group">
            <div class="filter-label">保留颜色：</div>
            <div class="filter-inputs">
              <el-input
                v-for="(item, index) in keepColors"
                :key="'keep-' + index"
                v-model="keepColors[index]"
                placeholder="格式: 191919-203040"
                class="filter-input"
                @input="processImage"
              >
                <template #append>
                  <el-button @click="removeKeepColor(index)" type="danger" :icon="Delete" />
                </template>
              </el-input>
            </div>
            <el-button @click="addKeepColor" type="primary" size="small" style="margin-top: 10px;">
              添加保留颜色
            </el-button>
          </div>

          <!-- 过滤颜色 -->
          <div class="filter-group">
            <div class="filter-label">过滤颜色：</div>
            <div class="filter-inputs">
              <el-input
                v-for="(item, index) in filterColors"
                :key="'filter-' + index"
                v-model="filterColors[index]"
                placeholder="格式: 191919-203040"
                class="filter-input"
                @input="processImage"
              >
                <template #append>
                  <el-button @click="removeFilterColor(index)" type="danger" :icon="Delete" />
                </template>
              </el-input>
            </div>
            <el-button @click="addFilterColor" type="primary" size="small" style="margin-top: 10px;">
              添加过滤颜色
            </el-button>
          </div>
        </div>
      </div>

      <!-- 二值化控制区域 -->
      <div v-if="imageLoaded" class="binary-section">
        <el-checkbox v-model="enableBinary" @change="handleBinaryToggle">
          启用二值化处理
        </el-checkbox>
        
        <div v-if="enableBinary" class="threshold-control">
          <el-slider
            v-model="threshold"
            :min="0"
            :max="255"
            :step="1"
            show-input
            @change="processImage"
          />
          <div class="threshold-info">
            当前阈值: <strong>{{ threshold }}</strong>
          </div>
        </div>
      </div>

      <!-- 处理状态 -->
      <el-alert
        v-if="processing"
        type="info"
        :closable="false"
        show-icon
      >
        处理中...
      </el-alert>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import { io } from "socket.io-client";
import { Upload, Delete } from '@element-plus/icons-vue';

const imageFileName = ref(null);
const threshold = ref(127);
const processing = ref(false);
const imageLoaded = ref(false);
const enableBinary = ref(false);
const enableColorFilter = ref(false);
const keepColors = ref([]);
const filterColors = ref([]);

let socket = null;

// 处理图像选择
function handleImageSelect(file) {
  const fileObj = file.raw || file;
  if (!fileObj) return;

  imageFileName.value = fileObj.name;
  processing.value = true;
  enableBinary.value = false; // 默认不启用二值化
  enableColorFilter.value = false; // 默认不启用颜色过滤
  imageLoaded.value = true; // 标记图像已加载

  // 获取文件路径（Electron 环境）
  const imagePath = fileObj.path || fileObj.name;
  
  if (!imagePath) {
    console.error("无法获取文件路径");
    processing.value = false;
    return;
  }

  // 通过 IPC 发送文件路径到 Python（只传递路径，不传递图像数据）
  ipc.invoke(ipcApiRoute.sendToPython, {
    type: 'upload_image',
    path: imagePath
  }).catch((error) => {
    console.error("发送图像路径失败:", error);
    processing.value = false;
  });
}

// 添加保留颜色
function addKeepColor() {
  keepColors.value.push('');
}

// 移除保留颜色
function removeKeepColor(index) {
  keepColors.value.splice(index, 1);
  processImage(); // 移除后自动处理
}

// 添加过滤颜色
function addFilterColor() {
  filterColors.value.push('');
}

// 移除过滤颜色
function removeFilterColor(index) {
  filterColors.value.splice(index, 1);
  processImage(); // 移除后自动处理
}

// 处理颜色过滤开关切换
function handleColorFilterToggle() {
  processImage();
}

// 处理二值化开关切换
function handleBinaryToggle() {
  processImage();
}

// 统一的图像处理函数
function processImage() {
  if (!imageLoaded.value) return;
  
  processing.value = true;
  
  // 构建统一的处理请求数据
  const requestData = {
    type: 'process_image',
  };
  
  // 如果启用了颜色过滤，添加颜色过滤参数
  if (enableColorFilter.value) {
    const validKeepColors = keepColors.value.filter(c => c && c.trim());
    const validFilterColors = filterColors.value.filter(c => c && c.trim());
    
    // 只有当有有效颜色时才添加参数
    if (validKeepColors.length > 0 || validFilterColors.length > 0) {
      requestData.enableColorFilter = true;
      requestData.keepColors = validKeepColors;
      requestData.filterColors = validFilterColors;
    } else {
      // 如果勾选了但没有有效颜色，不启用过滤
      requestData.enableColorFilter = false;
    }
  } else {
    requestData.enableColorFilter = false;
  }
  
  // 如果启用了二值化，添加二值化参数
  if (enableBinary.value) {
    requestData.enableBinary = true;
    requestData.threshold = threshold.value;
  } else {
    requestData.enableBinary = false;
  }
  
  // 发送统一的处理请求
  ipc.invoke(ipcApiRoute.sendToPython, requestData).catch((error) => {
    console.error("图像处理失败:", error);
    processing.value = false;
    alert(`图像处理失败: ${error.message || '未知错误'}`);
  });
}

// 接收 Python 处理结果（主窗口不再显示图像，只更新状态）
const handleProcessedImage = (data) => {
  processing.value = false;
  
  if (data && !data.success) {
    console.error("图像处理失败:", data.error);
    alert(`处理失败: ${data.error || '未知错误'}`);
  }
};

onMounted(() => {
  // 初始化 Socket 连接
  socket = io("ws://localhost:7070");
  socket.on("connect", () => {
    console.log("Socket 连接成功");
  });

  // 监听 Python 返回的处理结果
  socket.on("image-processed", (response) => {
    console.log("收到处理结果:", response);
    handleProcessedImage(response);
  });
});

onUnmounted(() => {
  if (socket) {
    socket.disconnect();
  }
});
</script>

<style scoped>
.image-processor {
  padding: 20px;
  height: 100vh;
  overflow-y: auto;
}

.main-card {
  max-width: 1200px;
  margin: 0 auto;
}

.main-card :deep(.el-card__header) {
  background-color: #f5f7fa;
  padding: 15px 20px;
}

.main-card h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
}

.upload-section {
  margin-bottom: 20px;
}

.file-info {
  margin-top: 10px;
  color: #606266;
  font-size: 14px;
}

.filter-section {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.filter-section h4 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
}

.filter-group {
  margin-bottom: 20px;
}

.filter-label {
  margin-bottom: 10px;
  font-weight: 500;
  color: #606266;
}

.filter-inputs {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.filter-input {
  width: 100%;
}

.filter-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.binary-section {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.threshold-control {
  margin-top: 15px;
}

.threshold-info {
  margin-top: 10px;
  font-size: 14px;
  color: #606266;
}

.threshold-info strong {
  color: #409eff;
}

</style>
