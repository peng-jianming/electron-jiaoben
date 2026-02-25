<template>
  <div class="screenshot-preview-container">
    <!-- 顶部信息栏 -->
    <header class="preview-header">
      <div class="header-content">
        <div class="title-section">
          <div class="title-icon">📸</div>
          <h1>实时截图预览</h1>
        </div>
        <div class="status-section">
          <div class="status-badge" :class="{ active: isReceiving }">
            <span class="status-dot"></span>
            {{ isReceiving ? '接收中' : '等待中' }}
          </div>
          <div class="timestamp" v-if="lastTimestamp">
            {{ formatTime(lastTimestamp) }}
          </div>
        </div>
      </div>
    </header>

    <!-- 截图显示区域 -->
    <main class="preview-main">
      <!-- 等待状态 -->
      <div v-if="!currentImage" class="waiting-state">
        <div class="waiting-icon">🖼️</div>
        <h2>等待截图...</h2>
        <p>请在主窗口中点击"开始截图"按钮</p>
      </div>

      <!-- 截图图片 -->
      <div v-else class="image-wrapper">
        <img 
          :src="currentImage" 
          alt="截图预览" 
          class="screenshot-image"
        />
        <div class="image-info">
          <span>尺寸: {{ imageBounds.width }} × {{ imageBounds.height }}</span>
          <span>位置: ({{ imageBounds.x }}, {{ imageBounds.y }})</span>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { io } from 'socket.io-client';

// 状态
const currentImage = ref(null);
const lastTimestamp = ref(null);
const isReceiving = ref(false);
const imageBounds = ref({ x: 0, y: 0, width: 0, height: 0 });

let socket = null;
let receiveTimeout = null;

// 格式化时间
function formatTime(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

// 处理截图数据
function handleScreenshotData(data) {
  if (data && data.image) {
    currentImage.value = data.image;
    lastTimestamp.value = data.timestamp;
    imageBounds.value = data.bounds || { x: 0, y: 0, width: 0, height: 0 };
    
    // 设置接收状态
    isReceiving.value = true;
    
    // 清除之前的超时
    if (receiveTimeout) {
      clearTimeout(receiveTimeout);
    }
    
    // 3秒没收到新数据则设为等待状态
    receiveTimeout = setTimeout(() => {
      isReceiving.value = false;
    }, 3000);
  }
}

onMounted(() => {
  // 连接到 Socket.IO 服务器
  socket = io('ws://localhost:7070');
  
  socket.on('connect', () => {
    console.log('截图预览窗口 Socket 连接成功');
  });
  
  // 监听截图更新事件
  socket.on('screenshot-update', (data) => {
    handleScreenshotData(data);
  });
  
  socket.on('disconnect', () => {
    console.log('Socket 断开连接');
    isReceiving.value = false;
  });
});

onUnmounted(() => {
  if (receiveTimeout) {
    clearTimeout(receiveTimeout);
  }
  if (socket) {
    socket.disconnect();
  }
});
</script>

<style scoped>
.screenshot-preview-container {
  width: 100%;
  height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* 顶部信息栏 */
.preview-header {
  background: rgba(30, 41, 59, 0.9);
  border-bottom: 1px solid rgba(51, 65, 85, 0.8);
  backdrop-filter: blur(10px);
}

.header-content {
  padding: 12px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  font-size: 24px;
}

.title-section h1 {
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
  margin: 0;
}

.status-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: rgba(51, 65, 85, 0.6);
  border-radius: 20px;
  font-size: 13px;
  color: #94a3b8;
  transition: all 0.3s ease;
}

.status-badge.active {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #64748b;
  transition: all 0.3s ease;
}

.status-badge.active .status-dot {
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.2); }
}

.timestamp {
  font-size: 13px;
  color: #64748b;
  font-family: 'Consolas', monospace;
}

/* 主显示区域 */
.preview-main {
  flex: 1;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

/* 等待状态 */
.waiting-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  text-align: center;
}

.waiting-icon {
  font-size: 64px;
  opacity: 0.6;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.waiting-state h2 {
  font-size: 20px;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0;
}

.waiting-state p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

/* 图片包装器 */
.image-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.screenshot-image {
  max-width: 100%;
  max-height: calc(100vh - 140px);
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  border: 2px solid rgba(99, 102, 241, 0.3);
  transition: all 0.3s ease;
}

.screenshot-image:hover {
  border-color: rgba(99, 102, 241, 0.6);
  box-shadow: 0 12px 40px rgba(99, 102, 241, 0.2);
}

.image-info {
  display: flex;
  gap: 20px;
  font-size: 12px;
  color: #64748b;
  font-family: 'Consolas', monospace;
}
</style>

