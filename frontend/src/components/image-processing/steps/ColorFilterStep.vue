<template>
  <div class="color-filter-step">
    <div>
      <div v-for="item in data.list" :key="item.id">
        <div class="color-block" :style="{ backgroundColor: item.baseColor }"></div>
        <div class="color-text">{{ item.baseColor }}</div>
        <div class="color-text">{{ item.offset }}</div>
        <button class="danger-btn" @click="removeRow(item.id)">删除</button>
      </div>
    </div>
    <button class="primary-btn" @click="openDialog">颜色过滤处理</button>

    <div v-if="visible" class="dialog-mask" @click.self="closeDialog">
      <div class="dialog">
        <div class="dialog-header">
          <span>颜色过滤</span>
          <button class="close-btn" @click="closeDialog">×</button>
        </div>
        <div class="dialog-body">
          <div class="left-panel">
            <div class="panel-title">当前图片</div>
            <div
              class="image-container"
              @wheel.prevent="handleWheel"
            >
              <canvas
                ref="mainCanvasRef"
                class="main-canvas"
                @mousedown="handleMouseDown"
                @mouseup="handleMouseUp"
                @mouseleave="handleMouseUp"
                @mousemove="handleMouseMove"
                @click="handlePickColor"
              ></canvas>
            </div>
            <div class="panel-title panel-title-bottom">结果图片</div>
            <div class="result-container">
              <canvas ref="resultCanvasRef" class="result-canvas"></canvas>
            </div>
          </div>

          <div class="right-panel">
            <div class="panel-title">放大镜</div>
            <div class="magnifier-container">
              <canvas ref="magnifierCanvasRef" class="magnifier-canvas"></canvas>
              <div
                class="magnifier-color-preview"
                :style="{ backgroundColor: currentHoverColorHex || '#ffffff' }"
              ></div>
              <div class="magnifier-color-text">
                {{ currentHoverColorHex || '未选中' }}
              </div>
            </div>

            <div class="panel-title table-title">颜色表</div>
            <table class="color-table">
              <thead>
                <tr>
                  <th>基准色</th>
                  <th>偏色(0 ~ 100)</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!rows.length">
                  <td colspan="3" class="empty-tip">
                    请在左侧图片上点击选取基准色
                  </td>
                </tr>
                <tr v-for="row in rows" :key="row.id">
                  <td>
                    <div class="base-color-cell">
                      <span
                        class="color-block"
                        :style="{ backgroundColor: row.baseColorHex }"
                      ></span>
                      <span class="color-text">{{ row.baseColorHex }}</span>
                    </div>
                  </td>
                  <td>
                    <div class="slider-cell">
                      <input
                        type="range"
                        min="0"
                        max="100"
                        v-model.number="row.offset"
                      />
                      <span class="slider-value">{{ row.offset }}</span>
                    </div>
                  </td>
                  <td>
                    <button class="danger-btn" @click="removeRow(row.id)">
                      删除
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>

            <button class="primary-btn" @click="handleConfirm">确定</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch, inject } from "vue";

const props = defineProps({
  data: {
    type: Object,
    default: () => ({}),
  },
  // 当前原始图 URL（来自父组件）
  imageSrc: {
    type: String,
    default: "",
  },
  // 当前图片对应的后端 imageId
  imageId: {
    type: String,
    default: "",
  },
});

const sendToBackend = inject("sendToBackend", null);
const colorFilterPreview = inject("colorFilterPreview", null);

const visible = ref(false);
const mainCanvasRef = ref(null);
const resultCanvasRef = ref(null);
const magnifierCanvasRef = ref(null);

const scale = ref(1);
const offsetX = ref(0);
const offsetY = ref(0);
const isPanning = ref(false);
const isPanClickBlocked = ref(false);
const lastMouseX = ref(0);
const lastMouseY = ref(0);
const originalCanvas = ref(null);
const imageElement = ref(null);
const currentHoverColorHex = ref("");

const rows = ref([]);

const openDialog = () => {
  visible.value = true;
  setTimeout(() => {
    initCanvasImage();
  }, 100);
};

const closeDialog = () => {
  visible.value = false;
};

const handleWheel = (event) => {
  if (!event.ctrlKey) return;
  event.preventDefault();
  const delta = event.deltaY > 0 ? -0.1 : 0.1;
  let next = scale.value + delta;
  if (next < 0.2) next = 0.2;
  if (next > 5) next = 5;
  scale.value = next;
  drawMainCanvas();
};

const handleMouseDown = (event) => {
  if (!event.ctrlKey) return;
  const canvas = mainCanvasRef.value;
  if (!canvas) return;
  isPanning.value = true;
  isPanClickBlocked.value = true;
  const rect = canvas.getBoundingClientRect();
  lastMouseX.value = event.clientX - rect.left;
  lastMouseY.value = event.clientY - rect.top;
};

const handleMouseUp = () => {
  isPanning.value = false;
  // 延迟一帧再允许点击，避免拖拽结束立刻触发选色
  requestAnimationFrame(() => {
    isPanClickBlocked.value = false;
  });
};

const getImageCoordinateFromEvent = (event) => {
  const canvas = mainCanvasRef.value;
  if (!canvas || !imageElement.value) return null;

  const rect = canvas.getBoundingClientRect();
  const canvasX = event.clientX - rect.left;
  const canvasY = event.clientY - rect.top;

  const img = imageElement.value;
  const canvasWidth = canvas.width;
  const canvasHeight = canvas.height;
  const imgAspect = img.width / img.height;
  const canvasAspect = canvasWidth / canvasHeight;

  let baseDrawWidth;
  let baseDrawHeight;
  if (imgAspect > canvasAspect) {
    baseDrawWidth = canvasWidth;
    baseDrawHeight = canvasWidth / imgAspect;
  } else {
    baseDrawHeight = canvasHeight;
    baseDrawWidth = canvasHeight * imgAspect;
  }

  const drawWidth = baseDrawWidth * scale.value;
  const drawHeight = baseDrawHeight * scale.value;

  const startX = (canvasWidth - baseDrawWidth) / 2 + offsetX.value;
  const startY = (canvasHeight - baseDrawHeight) / 2 + offsetY.value;

  const relX = (canvasX - startX) / drawWidth;
  const relY = (canvasY - startY) / drawHeight;

  const imgX = Math.floor(relX * img.width);
  const imgY = Math.floor(relY * img.height);

  if (imgX < 0 || imgY < 0 || imgX >= img.width || imgY >= img.height) {
    return null;
  }

  return { x: imgX, y: imgY };
};

const handleMouseMove = (event) => {
  const canvas = mainCanvasRef.value;
  if (!canvas || !imageElement.value) return;

  const rect = canvas.getBoundingClientRect();
  const canvasX = event.clientX - rect.left;
  const canvasY = event.clientY - rect.top;

  if (isPanning.value && event.ctrlKey) {
    const dx = canvasX - lastMouseX.value;
    const dy = canvasY - lastMouseY.value;
    offsetX.value += dx;
    offsetY.value += dy;
    lastMouseX.value = canvasX;
    lastMouseY.value = canvasY;
    drawMainCanvas();
    return;
  }

  const imgPos = getImageCoordinateFromEvent(event);
  if (!imgPos) return;
  drawMagnifier(imgPos.x, imgPos.y);
};

const handlePickColor = (event) => {
  // 正在或刚刚拖拽时，不进行颜色选取
  if (event.ctrlKey || isPanClickBlocked.value) return;

  const imgPos = getImageCoordinateFromEvent(event);
  if (!imgPos || !originalCanvas.value) return;

  const ctx = originalCanvas.value.getContext("2d");
  const pixel = ctx.getImageData(imgPos.x, imgPos.y, 1, 1).data;
  const hex = rgbToHex(pixel[0], pixel[1], pixel[2]);

  rows.value.push({
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    baseColorHex: hex,
    offset: 0,
  });
};

const removeRow = (id) => {
  rows.value = rows.value.filter((item) => item.id !== id);
};

const numToHex = (num) => {
  const hex = Math.max(0, Math.min(255, Math.floor(num)))
    .toString(16)
    .toUpperCase();
  return hex.length === 1 ? "0" + hex : hex;
};

const debounce = (fn, delay = 300) => {
  let timer = null;
  return (...args) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      fn(...args);
    }, delay);
  };
};

const sendRowsToBackend = (val) => {
  // 表格数据发生变化时打印
  // 只打印必要字段，避免过多无用信息
  sendToBackend("颜色过滤", {
    imageId: props.imageId,
    rows: val.map((item) => ({
      baseColor: item.baseColorHex,
      offset: numToHex(item.offset) + numToHex(item.offset) + numToHex(item.offset)
    })),
  });
};

const debouncedSendRowsToBackend = debounce(sendRowsToBackend, 300);

watch(
  rows,
  (val) => {
    debouncedSendRowsToBackend(val);
  },
  { deep: true }
);

const initCanvasImage = () => {

  const canvas = mainCanvasRef.value;
  if (!canvas) return;

  // 若无真实图片，使用简单的渐变占位图，保证功能可用
  const width = 320;
  const height = 240;
  canvas.width = width;
  canvas.height = height;

  const img = new Image();
  img.crossOrigin = "anonymous";

  img.onload = () => {
    imageElement.value = img;
    const off = document.createElement("canvas");
    off.width = img.width;
    off.height = img.height;
    const offCtx = off.getContext("2d");
    offCtx.drawImage(img, 0, 0);
    originalCanvas.value = off;
    drawMainCanvas();
  };

  // 如果外面传了 imageSrc 就用，否则画一张占位图片
  if (props.imageSrc) {
    img.src = props.imageSrc;
  } else {
    const tempCanvas = document.createElement("canvas");
    tempCanvas.width = width;
    tempCanvas.height = height;
    const tempCtx = tempCanvas.getContext("2d");
    const gradient = tempCtx.createLinearGradient(0, 0, width, height);
    gradient.addColorStop(0, "#ff0000");
    gradient.addColorStop(0.5, "#00ff00");
    gradient.addColorStop(1, "#0000ff");
    tempCtx.fillStyle = gradient;
    tempCtx.fillRect(0, 0, width, height);
    img.src = tempCanvas.toDataURL("image/png");
  }

  // 初始化结果画布为白底
  const resultCanvas = resultCanvasRef.value;
  if (resultCanvas) {
    const rctx = resultCanvas.getContext("2d");
    resultCanvas.width = width;
    resultCanvas.height = height;
    rctx.fillStyle = "#ffffff";
    rctx.fillRect(0, 0, width, height);
  }

  // 初始化放大镜
  const magnifierCanvas = magnifierCanvasRef.value;
  if (magnifierCanvas) {
    magnifierCanvas.width = 11;
    magnifierCanvas.height = 11;
  }
};

const drawMainCanvas = () => {
  const canvas = mainCanvasRef.value;
  if (!canvas || !imageElement.value) return;

  const rect = canvas.getBoundingClientRect();
  const ctx = canvas.getContext("2d");

  canvas.width = rect.width;
  canvas.height = rect.height;

  const img = imageElement.value;
  const imgAspect = img.width / img.height;
  const canvasAspect = canvas.width / canvas.height;

  let baseDrawWidth;
  let baseDrawHeight;
  if (imgAspect > canvasAspect) {
    baseDrawWidth = canvas.width;
    baseDrawHeight = canvas.width / imgAspect;
  } else {
    baseDrawHeight = canvas.height;
    baseDrawWidth = canvas.height * imgAspect;
  }

  const drawWidth = baseDrawWidth * scale.value;
  const drawHeight = baseDrawHeight * scale.value;

  const startX = (canvas.width - baseDrawWidth) / 2 + offsetX.value;
  const startY = (canvas.height - baseDrawHeight) / 2 + offsetY.value;

  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(img, startX, startY, drawWidth, drawHeight);
};

const drawMagnifier = (centerX, centerY) => {
  const magnifierCanvas = magnifierCanvasRef.value;
  if (!magnifierCanvas || !originalCanvas.value) return;

  const srcCtx = originalCanvas.value.getContext("2d");
  const mctx = magnifierCanvas.getContext("2d");

  const size = 11;
  const half = (size - 1) / 2;
  const cellSize = 8;

  const startX = Math.max(0, centerX - half);
  const startY = Math.max(0, centerY - half);
  const clampedWidth = Math.min(size, originalCanvas.value.width - startX);
  const clampedHeight = Math.min(size, originalCanvas.value.height - startY);

  const imageData = srcCtx.getImageData(startX, startY, clampedWidth, clampedHeight);

  magnifierCanvas.width = size * cellSize;
  magnifierCanvas.height = size * cellSize;

  mctx.clearRect(0, 0, magnifierCanvas.width, magnifierCanvas.height);

  const data = imageData.data;
  for (let j = 0; j < size; j++) {
    for (let i = 0; i < size; i++) {
      const sx = i;
      const sy = j;
      if (sx >= clampedWidth || sy >= clampedHeight) continue;
      const idx = (sy * clampedWidth + sx) * 4;
      const r = data[idx];
      const g = data[idx + 1];
      const b = data[idx + 2];
      mctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
      mctx.fillRect(i * cellSize, j * cellSize, cellSize, cellSize);
    }
  }

  // 绘制网格
  mctx.strokeStyle = "rgba(0,0,0,0.3)";
  mctx.lineWidth = 1;
  for (let i = 0; i <= size; i++) {
    const pos = i * cellSize + 0.5;
    mctx.beginPath();
    mctx.moveTo(pos, 0);
    mctx.lineTo(pos, size * cellSize);
    mctx.stroke();
    mctx.beginPath();
    mctx.moveTo(0, pos);
    mctx.lineTo(size * cellSize, pos);
    mctx.stroke();
  }

  // 高亮中心格子
  const centerIndex = half;
  mctx.strokeStyle = "#ffffff";
  mctx.lineWidth = 2;
  mctx.strokeRect(
    centerIndex * cellSize + 1,
    centerIndex * cellSize + 1,
    cellSize - 2,
    cellSize - 2
  );
  mctx.strokeStyle = "#000000";
  mctx.lineWidth = 1;
  mctx.strokeRect(
    centerIndex * cellSize + 0.5,
    centerIndex * cellSize + 0.5,
    cellSize - 1,
    cellSize - 1
  );

  // 中心点颜色，用于右侧预览（从原图取）
  const centerSrcX = centerX;
  const centerSrcY = centerY;
  if (
    centerSrcX >= 0 &&
    centerSrcY >= 0 &&
    centerSrcX < originalCanvas.value.width &&
    centerSrcY < originalCanvas.value.height
  ) {
    const centerData = srcCtx.getImageData(centerSrcX, centerSrcY, 1, 1).data;
    const r = centerData[0];
    const g = centerData[1];
    const b = centerData[2];
    currentHoverColorHex.value = rgbToHex(r, g, b);
  }
};

const rgbToHex = (r, g, b) => {
  const toHex = (n) => {
    const h = n.toString(16);
    return h.length === 1 ? "0" + h : h;
  };
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
};

const drawResultImage = (src) => {
  const resultCanvas = resultCanvasRef.value;
  if (!resultCanvas || !src) return;

  const rctx = resultCanvas.getContext("2d");
  const img = new Image();
  img.crossOrigin = "anonymous";
  img.onload = () => {
    resultCanvas.width = img.width;
    resultCanvas.height = img.height;
    rctx.clearRect(0, 0, resultCanvas.width, resultCanvas.height);
    rctx.drawImage(img, 0, 0);
  };
  img.src = src;
};

onMounted(() => {
  // 懒加载，初次打开弹框时再绘制
});

// 监听后端返回的预览结果，并绘制到“结果图片”画布
if (colorFilterPreview) {
  watch(
    colorFilterPreview,
    (val) => {
      if (!visible.value) return;
      if (val && typeof val === "string") {
        drawResultImage(val);
      }
    },
    { immediate: false }
  );
}


const handleConfirm = () => {
  props.data.list = rows.value.map((item) => ({
    baseColor: item.baseColorHex,
    offset: numToHex(item.offset) + numToHex(item.offset) + numToHex(item.offset)
  }));
  closeDialog();
};
</script>

<style scoped>
.color-filter-step {
  display: flex;
  align-items: center;
}

.primary-btn {
  padding: 4px 10px;
  font-size: 12px;
  border-radius: 4px;
  border: 1px solid #3b82f6;
  background-color: #3b82f6;
  color: #ffffff;
  cursor: pointer;
}

.dialog-mask {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  width: 960px;
  max-width: 100%;
  max-height: 90vh;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.25);
  display: flex;
  flex-direction: column;
}

.dialog-header {
  padding: 10px 14px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.close-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
}

.dialog-body {
  padding: 12px;
  display: flex;
  gap: 12px;
}

.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.left-panel {
  flex: 3;
}

.right-panel {
  flex: 2;
}

.panel-title {
  font-size: 13px;
  font-weight: 500;
  color: #4b5563;
}

.panel-title-bottom {
  margin-top: 4px;
}

.image-container {
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 4px;
  background-color: #f9fafb;
  overflow: hidden;
  width: 100%;
  height: 260px;
}

.main-canvas {
  display: block;
  width: 100%;
  height: 100%;
  image-rendering: pixelated;
}

.result-container {
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 4px;
  background-color: #f9fafb;
  width: 100%;
  max-height: 260px;
  overflow: auto;
}

.result-canvas {
  display: block;
  max-width: 100%;
  height: auto;
}

.magnifier-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.magnifier-canvas {
  width: 88px;
  height: 88px;
  border: 1px solid #e5e7eb;
  image-rendering: pixelated;
}

.magnifier-color-preview {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  border: 1px solid #d1d5db;
}

.magnifier-color-text {
  font-size: 12px;
  color: #4b5563;
}

.table-title {
  margin-top: 4px;
}

.color-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.color-table th,
.color-table td {
  border: 1px solid #e5e7eb;
  padding: 4px 6px;
  text-align: left;
}

.color-table thead {
  background-color: #f3f4f6;
}

.empty-tip {
  text-align: center;
  color: #9ca3af;
  padding: 8px 0;
}

.base-color-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.color-block {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  border: 1px solid #d1d5db;
}

.color-text {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
    "Liberation Mono", "Courier New", monospace;
}

.slider-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.slider-cell input[type="range"] {
  flex: 1;
}

.slider-value {
  width: 28px;
  text-align: right;
}

.danger-btn {
  padding: 2px 8px;
  font-size: 12px;
  border-radius: 4px;
  border: 1px solid #ef4444;
  background-color: #ffffff;
  color: #ef4444;
  cursor: pointer;
}
</style>

