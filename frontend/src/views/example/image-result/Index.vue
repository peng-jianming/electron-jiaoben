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
    
    <!-- 图像显示 - 只显示图片，支持点击 -->
    <img 
      v-if="!loading && !error && processedImage" 
      :src="processedImage" 
      alt="处理结果" 
      class="result-image"
      @click="handleImageClick"
      ref="imageRef"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { io } from 'socket.io-client';
import { ipc } from '@/utils/ipcRenderer';
import { ipcApiRoute } from '@/api';

const loading = ref(true);
const error = ref(null);
const processedImage = ref(null);
const threshold = ref(null);
const imageRef = ref(null);

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
  
  // 监听来自主窗口的洪水填充状态
  socket.on('flood-fill-enabled', (data) => {
    console.log('洪水填充已启用');
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
    // 优先显示处理后的图像（支持 PNG 和 JPEG）
    if (data.processedImage) {
      // 自动检测图像格式（JPEG 以 /9j/ 开头，PNG 以 iVBOR 开头）
      const isJpeg = data.processedImage.startsWith('/9j/');
      const mimeType = isJpeg ? 'image/jpeg' : 'image/png';
      processedImage.value = `data:${mimeType};base64,${data.processedImage}`;
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

// 处理图片点击事件
function handleImageClick(event) {
  if (!imageRef.value) return;
  
  const img = imageRef.value;
  const rect = img.getBoundingClientRect();
  
  // 计算点击位置相对于图片的坐标
  const x = Math.round(event.clientX - rect.left);
  const y = Math.round(event.clientY - rect.top);
  
  // 计算实际图片尺寸（考虑缩放）
  const imgNaturalWidth = img.naturalWidth;
  const imgNaturalHeight = img.naturalHeight;
  const imgDisplayWidth = rect.width;
  const imgDisplayHeight = rect.height;
  
  // 计算缩放比例
  const scaleX = imgNaturalWidth / imgDisplayWidth;
  const scaleY = imgNaturalHeight / imgDisplayHeight;
  
  // 转换为图片实际坐标
  const actualX = Math.round(x * scaleX);
  const actualY = Math.round(y * scaleY);
  
  console.log(`点击位置: 显示坐标(${x}, ${y}), 实际坐标(${actualX}, ${actualY})`);
  
  // 通过 IPC invoke 发送点击事件到主进程，然后转发到主窗口
  if (ipc) {
    ipc.invoke(ipcApiRoute.handleImageClick, { x: actualX, y: actualY }).catch((error) => {
      console.error("发送图片点击事件失败:", error);
    });
  } else if (window.ipcRenderer) {
    window.ipcRenderer.invoke('controller/example/handleImageClick', { x: actualX, y: actualY }).catch((error) => {
      console.error("发送图片点击事件失败:", error);
    });
  } else if (window.electron && window.electron.ipcRenderer) {
    window.electron.ipcRenderer.invoke('controller/example/handleImageClick', { x: actualX, y: actualY }).catch((error) => {
      console.error("发送图片点击事件失败:", error);
    });
  }
}
</script>

<style scoped>
.image-result-container {
  width: 100%;
  height: 100vh;
  background: #1e1e1e;
  overflow: auto;
  /* 使用 padding 让小图片看起来居中，大图片可以完整滚动 */
  padding: 20px;
  box-sizing: border-box;
}

.loading {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
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
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
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
  /* 保持原始尺寸，不缩放 */
  width: auto;
  height: auto;
  max-width: none;
  max-height: none;
}
</style>

