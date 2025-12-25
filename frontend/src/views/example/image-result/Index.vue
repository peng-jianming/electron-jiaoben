<template>
  <div class="image-result-container">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <div>正在加载图像...</div>
    </div>
    
    <!-- 错误状态 -->
    <div v-if="error" class="error">
      <div class="error-icon">⚠️</div>
      <div class="error-message">处理失败: {{ error }}</div>
    </div>
    
    <!-- 图像显示 - 只显示图片 -->
    <img 
      v-if="!loading && !error && processedImage" 
      :src="processedImage" 
      alt="处理结果" 
      class="result-image" 
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { io } from 'socket.io-client';

const loading = ref(true);
const error = ref(null);
const processedImage = ref(null);
const threshold = ref(null);

let socket = null;

onMounted(() => {
  // 连接到 Socket.IO 服务器
  socket = io('ws://localhost:7070');
  
  socket.on('connect', () => {
    console.log('结果窗口 Socket 连接成功');
  });
  
  // 监听图像处理结果
  socket.on('image-processed', (data) => {
    console.log('收到处理结果:', data);
    handleImageData(data);
  });
});

onUnmounted(() => {
  if (socket) {
    socket.disconnect();
  }
});

function handleImageData(data) {
  loading.value = false;
  
  if (data && data.success) {
    // 优先显示处理后的图像
    if (data.processedImage) {
      processedImage.value = `data:image/png;base64,${data.processedImage}`;
      threshold.value = data.threshold || 127;
      error.value = null;
    } 
    // // 如果没有处理后的图像，但有原图，也显示原图
    // else if (data.originalImage) {
    //   processedImage.value = `data:image/png;base64,${data.originalImage}`;
    //   error.value = null;
    // } 
    // 如果都没有，显示错误
    else {
      error.value = '未收到图像数据';
      processedImage.value = null;
      threshold.value = null;
    }
  } else {
    error.value = data?.error || '未知错误';
    processedImage.value = null;
    threshold.value = null;
  }
}
</script>

<style scoped>
.image-result-container {
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #1e1e1e;
  overflow: auto;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  color: #999;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #404040;
  border-top-color: #42d392;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  color: #f56c6c;
  text-align: center;
  padding: 20px;
}

.error-icon {
  font-size: 48px;
}

.error-message {
  font-size: 16px;
}

.result-image {
  display: block;
  width: auto;
  height: auto;
  max-width: none;
  max-height: none;
  /* 保持原始尺寸和比例，不压缩，不缩放 */
  object-fit: contain;
}
</style>

