<template>
  <div class="card">
    <div class="card-body magnifier-container">
      <div v-if="magnifierVisible && currentImage" class="magnifier">
        <canvas ref="magnifierCanvasRef" class="magnifier-canvas"></canvas>
      </div>
      <div v-else class="magnifier-placeholder">
        <el-icon>
          <ZoomIn />
        </el-icon>
        <p>将鼠标移动到图片上查看</p>
      </div>
      <!-- 当前颜色值 -->
      <div class="current-color">
        <div style="display: flex; gap: 12px">
          <div>x: {{ currentPosition ? currentPosition.x : "0" }}</div>
          <div>y: {{ currentPosition ? currentPosition.y : "0" }}</div>
        </div>
        <div>HEX: {{ currentColor ? currentColor.hex : "#000000" }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { ZoomIn } from "@element-plus/icons-vue";

const props = defineProps({
  magnifierVisible: {
    type: Boolean,
    default: false,
  },
  currentImage: {
    type: Object,
    default: null,
  },
  currentPosition: {
    type: Object,
    default: () => ({ x: 0, y: 0 }),
  },
  currentColor: {
    type: Object,
    default: null,
  },
});

const magnifierCanvasRef = ref(null);

// 暴露放大镜 canvas 给父组件
defineExpose({
  getMagnifierCanvas: () => magnifierCanvasRef.value,
});
</script>

<style scoped>
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

.card-body {
  padding: 10px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-width: 0;
}

.magnifier-container {
  display: flex;
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
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 120px;
  text-align: left;
}
</style>

