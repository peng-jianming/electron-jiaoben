<template>
  <div class="map-container">
    <!-- 顶部信息栏 -->
    <header class="map-header">
      <div class="header-content">
        <div class="title-section">
          <div class="title-icon">🗺️</div>
          <h1>路径规划地图</h1>
        </div>
        <div class="status-section">
          <div class="status-badge" :class="{ selecting: selectingPoint }">
            <span class="status-dot"></span>
            {{ selectingPoint ? `选择${selectingPoint === 'start' ? '起点' : '终点'}中...` : '就绪' }}
          </div>
        </div>
      </div>
    </header>

    <!-- 地图显示区域 -->
    <main class="map-main">
      <div class="canvas-wrapper" ref="canvasWrapper">
        <canvas 
          ref="mapCanvas" 
          @click="handleCanvasClick"
          @mousemove="handleMouseMove"
          :style="{ cursor: selectingPoint ? 'crosshair' : 'default' }"
        ></canvas>
        <!-- 鼠标位置提示 -->
        <div class="mouse-position" v-if="mousePos.x >= 0">
          坐标: ({{ mousePos.x }}, {{ mousePos.y }})
        </div>
      </div>
    </main>

    <!-- 底部图例 -->
    <footer class="map-footer">
      <div class="legend">
        <div class="legend-item">
          <span class="legend-color walkable"></span>
          <span>可通行</span>
        </div>
        <div class="legend-item">
          <span class="legend-color obstacle"></span>
          <span>障碍物</span>
        </div>
        <div class="legend-item">
          <span class="legend-color start"></span>
          <span>起点</span>
        </div>
        <div class="legend-item">
          <span class="legend-color end"></span>
          <span>终点</span>
        </div>
        <div class="legend-item">
          <span class="legend-color path"></span>
          <span>规划路径</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { io } from 'socket.io-client';

// 获取 ipcRenderer（地图窗口开启了 nodeIntegration）
const { ipcRenderer } = window.require ? window.require('electron') : { ipcRenderer: null };

const mapCanvas = ref(null);
const canvasWrapper = ref(null);
const selectingPoint = ref(null);
const mousePos = ref({ x: -1, y: -1 });

// 地图数据
let mapImageData = null;
let mapWidth = 0;
let mapHeight = 0;
let startPoint = null;
let endPoint = null;
let pathPoints = [];
let socket = null;

// 绘制地图
function drawMap() {
  if (!mapCanvas.value || !mapImageData) return;
  
  const canvas = mapCanvas.value;
  const ctx = canvas.getContext('2d');
  
  // 设置 canvas 尺寸
  canvas.width = mapWidth;
  canvas.height = mapHeight;
  
  // 创建图片并绘制
  const img = new Image();
  img.onload = () => {
    // 清除画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 绘制地图图片
    ctx.drawImage(img, 0, 0);
    
    // 绘制路径（红色线条）
    if (pathPoints.length > 1) {
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.beginPath();
      ctx.moveTo(pathPoints[0].x, pathPoints[0].y);
      for (let i = 1; i < pathPoints.length; i++) {
        ctx.lineTo(pathPoints[i].x, pathPoints[i].y);
      }
      ctx.stroke();
    }
    
    // 绘制起点（绿色圆点）
    if (startPoint) {
      ctx.fillStyle = '#10b981';
      ctx.beginPath();
      ctx.arc(startPoint.x, startPoint.y, 8, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();
      
      // 绘制 "S" 标记
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 10px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('S', startPoint.x, startPoint.y);
    }
    
    // 绘制终点（红色圆点）
    if (endPoint) {
      ctx.fillStyle = '#ef4444';
      ctx.beginPath();
      ctx.arc(endPoint.x, endPoint.y, 8, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();
      
      // 绘制 "E" 标记
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 10px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('E', endPoint.x, endPoint.y);
    }
  };
  img.src = mapImageData;
}

// 处理画布点击
async function handleCanvasClick(event) {
  if (!mapCanvas.value) return;
  
  const rect = mapCanvas.value.getBoundingClientRect();
  const scaleX = mapWidth / rect.width;
  const scaleY = mapHeight / rect.height;
  
  const x = Math.round((event.clientX - rect.left) * scaleX);
  const y = Math.round((event.clientY - rect.top) * scaleY);
  
  if (selectingPoint.value) {
    const pointType = selectingPoint.value;
    
    // 更新本地显示
    if (pointType === 'start') {
      startPoint = { x, y };
    } else if (pointType === 'end') {
      endPoint = { x, y };
    }
    
    selectingPoint.value = null;
    drawMap();
    
    // 通过 IPC 发送点击事件到后端，后端再广播到主窗口
    if (ipcRenderer) {
      try {
        await ipcRenderer.invoke('controller/example/handleMapPointClick', { x, y, type: pointType });
      } catch (error) {
        console.error('发送点击事件失败:', error);
      }
    }
  }
}

// 处理鼠标移动
function handleMouseMove(event) {
  if (!mapCanvas.value) return;
  
  const rect = mapCanvas.value.getBoundingClientRect();
  const scaleX = mapWidth / rect.width;
  const scaleY = mapHeight / rect.height;
  
  mousePos.value = {
    x: Math.round((event.clientX - rect.left) * scaleX),
    y: Math.round((event.clientY - rect.top) * scaleY)
  };
}

// 处理地图数据
function handleMapData(data) {
  if (data && data.image) {
    mapImageData = data.image;
    mapWidth = data.width;
    mapHeight = data.height;
    startPoint = data.startPoint || null;
    endPoint = data.endPoint || null;
    pathPoints = [];
    
    nextTick(() => {
      drawMap();
    });
  }
}

// 处理路径数据
function handlePathData(data) {
  if (data && data.path) {
    pathPoints = data.path;
    drawMap();
  }
}

// 清除路径
function handleClearPath() {
  pathPoints = [];
  drawMap();
}

// 更新起点终点
function handleUpdatePoints(data) {
  if (data.startPoint !== undefined) {
    startPoint = data.startPoint;
  }
  if (data.endPoint !== undefined) {
    endPoint = data.endPoint;
  }
  drawMap();
}

onMounted(() => {
  // 连接 Socket.IO
  socket = io('ws://localhost:7070');
  
  socket.on('connect', () => {
    console.log('地图窗口 Socket 连接成功');
  });
  
  // 监听地图数据
  socket.on('map-data', handleMapData);
  
  // 监听路径数据
  socket.on('path-data', handlePathData);
  
  // 监听清除路径
  socket.on('clear-path', handleClearPath);
  
  // 监听选点模式
  socket.on('select-point-mode', (data) => {
    selectingPoint.value = data.type;
  });
  
  // 监听起点终点更新
  socket.on('update-points', handleUpdatePoints);
});

onUnmounted(() => {
  if (socket) {
    socket.disconnect();
  }
});
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* 顶部信息栏 */
.map-header {
  background: rgba(30, 41, 59, 0.9);
  border-bottom: 1px solid rgba(51, 65, 85, 0.8);
  backdrop-filter: blur(10px);
  flex-shrink: 0;
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

.status-badge.selecting {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #64748b;
  transition: all 0.3s ease;
}

.status-badge.selecting .status-dot {
  background: #f59e0b;
  box-shadow: 0 0 8px #f59e0b;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.2); }
}

/* 地图区域 */
.map-main {
  flex: 1;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.canvas-wrapper {
  position: relative;
  display: inline-block;
  background: #1e293b;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  border: 2px solid rgba(99, 102, 241, 0.3);
}

canvas {
  display: block;
  max-width: 100%;
  max-height: calc(100vh - 180px);
  border-radius: 6px;
}

.mouse-position {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: #f1f5f9;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Consolas', monospace;
}

/* 底部图例 */
.map-footer {
  background: rgba(30, 41, 59, 0.9);
  border-top: 1px solid rgba(51, 65, 85, 0.8);
  padding: 12px 20px;
  flex-shrink: 0;
}

.legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #94a3b8;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.legend-color.walkable {
  background: #fff;
}

.legend-color.obstacle {
  background: #000;
}

.legend-color.start {
  background: #10b981;
  border-radius: 50%;
}

.legend-color.end {
  background: #ef4444;
  border-radius: 50%;
}

.legend-color.path {
  background: linear-gradient(90deg, #ef4444, #ef4444);
  height: 4px;
  border-radius: 2px;
  align-self: center;
}
</style>

