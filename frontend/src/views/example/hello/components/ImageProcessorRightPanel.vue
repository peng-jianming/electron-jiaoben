<template>
  <div class="right-panel">
    <!-- 放大镜 -->
    <div class="card">
      <div class="card-body magnifier-container">
        <div 
          v-if="magnifierVisible && currentImage"
          class="magnifier"
        >
          <canvas ref="magnifierCanvasRef" class="magnifier-canvas"></canvas>
        </div>
        <div v-else class="magnifier-placeholder">
          <el-icon><ZoomIn /></el-icon>
          <p>将鼠标移动到图片上查看</p>
        </div>
        <!-- 当前颜色值 -->
        <div class="current-color">
          <div class="color-values">
            <div class="color-value-item">
              <span class="color-label">坐标:</span>
              <span class="color-value">
                ({{ currentPosition ? currentPosition.x : '0' }}, 
                {{ currentPosition ? currentPosition.y : '0' }})
              </span>
            </div>
            <div class="color-value-item">
              <span class="color-label">RGB:</span>
              <span class="color-value">{{ currentColor ? currentColor.rgb : '--' }}</span>
            </div>
            <div class="color-value-item">
              <span class="color-label">HEX:</span>
              <span class="color-value">{{ currentColor ? currentColor.hex : '--' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 选中颜色列表 -->
    <div class="card" style="flex: 1; overflow:auto">
      <div class="card-body selected-colors-container">
        <div v-if="currentSelectedColors.length === 0" class="empty-colors">
          <el-icon><Collection /></el-icon>
          <p>点击图片记录颜色</p>
        </div>
        <div v-else class="selected-colors-list">
          <div
            v-for="(color, index) in currentSelectedColors"
            :key="index"
            class="selected-color-item"
          >
            <div class="color-preview-small" :style="{ backgroundColor: color.hex }"></div>
            <div class="color-info-small">
              <div class="color-coord-small">坐标: {{ color.x }}, {{ color.y }}</div>
              <div class="color-rgb-small">{{ color.rgb }}</div>
              <div class="color-hex-small">{{ color.hex }}</div>
            </div>
            <el-button
              type="danger"
              size="small"
              :icon="Delete"
              circle
              @click="$emit('remove-color', index)"
              class="remove-color-btn"
            />
          </div>
        </div>
        <el-button
          v-if="currentSelectedColors.length > 0"
          type="danger"
          size="small"
          :icon="Delete"
          @click="$emit('clear-all-colors')"
          class="clear-all-btn"
        >
          清空全部
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ZoomIn, Collection, Delete } from '@element-plus/icons-vue';

defineProps({
  magnifierVisible: {
    type: Boolean,
    default: false
  },
  currentImage: {
    type: Object,
    default: null
  },
  currentPosition: {
    type: Object,
    default: () => ({ x: 0, y: 0 })
  },
  currentColor: {
    type: Object,
    default: null
  },
  currentSelectedColors: {
    type: Array,
    default: () => []
  }
});

defineEmits(['remove-color', 'clear-all-colors']);

const magnifierCanvasRef = ref(null);

// 暴露放大镜 canvas 给父组件，用于绘制
defineExpose({
  getMagnifierCanvas: () => magnifierCanvasRef.value
});
</script>

<style scoped>
.right-panel {
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
  display: flex;
  flex-direction: column;
}

.card:hover {
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: var(--shadow-lg);
}

.card-body {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-width: 0;
}

.magnifier-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  min-height: 200px;
}

.magnifier {
  width: 220px;
  height: 220px;
  border: 2px solid var(--primary-color);
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a2e;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.magnifier-canvas {
  width: 100%;
  height: 100%;
  image-rendering: pixelated;
}

.magnifier-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 220px;
  height: 220px;
  color: var(--text-secondary);
  border: 2px dashed var(--border-color);
  border-radius: 8px;
}

.magnifier-placeholder .el-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.magnifier-placeholder p {
  margin: 0;
  font-size: 12px;
}

.current-color {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(51, 65, 85, 0.3);
  border-radius: 8px;
}

.color-values {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.color-value-item {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.color-label {
  color: var(--text-secondary);
}

.color-value {
  color: var(--text-primary);
  font-weight: 500;
  font-family: 'Courier New', monospace;
}

.selected-colors-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.empty-colors {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--text-secondary);
}

.empty-colors .el-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-colors p {
  margin: 0;
  font-size: 14px;
}

.selected-colors-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.selected-color-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(51, 65, 85, 0.3);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.selected-color-item:hover {
  background: rgba(51, 65, 85, 0.5);
}

.color-preview-small {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  flex-shrink: 0;
}

.color-info-small {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.color-rgb-small,
.color-hex-small {
  font-size: 12px;
  color: var(--text-primary);
  font-family: 'Courier New', monospace;
}

.color-hex-small {
  color: var(--text-secondary);
}

.color-coord-small {
  font-size: 11px;
  color: var(--primary-light);
  font-weight: 500;
  margin-bottom: 2px;
}

.remove-color-btn {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.selected-color-item:hover .remove-color-btn {
  opacity: 1;
}

.clear-all-btn {
  width: 100%;
  margin-top: 8px;
}
</style>


