<template>
  <div class="magnifier-card">
    <div class="magnifier-body">
      <!-- 放大镜 -->
      <div class="magnifier-area">
        <div v-if="magnifierVisible && currentImage" class="magnifier">
          <canvas ref="magnifierCanvasRef" class="magnifier-canvas"></canvas>
        </div>
        <div v-else class="magnifier-placeholder">
          <el-icon><ZoomIn /></el-icon>
          <p>移到图片上查看</p>
        </div>
      </div>
      <!-- 颜色信息 -->
      <div class="color-info-area">
        <!-- 颜色预览色块 + HEX -->
        <div class="color-swatch-row">
          <div
            class="color-swatch"
            :style="{ background: currentColor ? currentColor.hex : '#1e293b' }"
          ></div>
          <div class="color-text-group">
            <div class="color-hex-display">
              {{ currentColor ? currentColor.hex : "#000000" }}
            </div>
            <div class="color-rgb-display">
              {{ currentColor ? currentColor.rgb : "—" }}
            </div>
          </div>
        </div>
        <!-- 坐标 -->
        <div class="info-row">
          <span class="info-icon">📍</span>
          <span class="info-mono">{{ currentPosition ? currentPosition.x : 0 }}, {{ currentPosition ? currentPosition.y : 0 }}</span>
        </div>
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
.magnifier-card {
  flex-shrink: 0;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.magnifier-body {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  padding: 10px;
  gap: 8px;
  height: auto;
}

/* 放大镜区域 */
.magnifier-area {
  flex-shrink: 0;
  align-self: center;
}

.magnifier {
  width: 160px;
  height: 160px;
  border: 2px solid #6366f1;
  border-radius: 10px;
  overflow: hidden;
  background: #0f172a;
  box-shadow:
    0 0 0 1px rgba(99, 102, 241, 0.1),
    0 4px 16px rgba(99, 102, 241, 0.15);
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
  width: 160px;
  height: 160px;
  color: #94a3b8;
  background: #f1f5f9;
  border: 2px dashed #cbd5e1;
  border-radius: 10px;
}

.magnifier-placeholder .el-icon {
  font-size: 24px;
  margin-bottom: 4px;
  opacity: 0.35;
}

.magnifier-placeholder p {
  margin: 0;
  font-size: 10px;
}

/* 颜色信息区 */
.color-info-area {
  width: 100%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
}

.color-swatch-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.color-swatch {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  border: 2px solid #e2e8f0;
  box-shadow:
    inset 0 0 0 1px rgba(0, 0, 0, 0.05),
    0 2px 8px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
  transition: background 0.15s ease;
}

.color-text-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.color-hex-display {
  font-family: "JetBrains Mono", "Cascadia Code", "Courier New", monospace;
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: 0.5px;
  line-height: 1.2;
  white-space: nowrap;
}

.color-rgb-display {
  font-family: "JetBrains Mono", "Cascadia Code", "Courier New", monospace;
  font-size: 10px;
  color: #64748b;
  font-weight: 500;
  letter-spacing: 0.2px;
  white-space: nowrap;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
  padding: 4px 8px;
  background: rgba(99, 102, 241, 0.04);
  border-radius: 6px;
  border: 1px solid rgba(99, 102, 241, 0.08);
}

.info-icon {
  font-size: 12px;
  flex-shrink: 0;
}

.info-mono {
  font-family: "JetBrains Mono", "Cascadia Code", "Courier New", monospace;
  font-size: 12px;
  color: #475569;
  font-weight: 600;
  white-space: nowrap;
}
</style>

