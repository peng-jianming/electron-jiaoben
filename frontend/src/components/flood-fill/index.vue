<template>
  <div class="flood-fill-wrapper">
    <div class="panel-body">
      <div class="layout">
        <!-- 左侧：原图/可编辑图 与交互 -->
        <div class="left-pane">
          <div class="toolbar">
            <el-button type="primary" size="small" @click="triggerUpload">
              上传图片
            </el-button>
            <el-button
              size="small"
              @click="useFromProcessing"
              :disabled="!canUseProcessingImage"
            >
              使用图像处理结果
            </el-button>

            <el-button size="small" :disabled="!hasImage" @click="resetEditedToOriginal">
              重置处理图
            </el-button>

            <el-button size="small" :disabled="!hasImage || !naturalReady" @click="fitToContainer">
              适应性缩放
            </el-button>
            <el-button size="small" :disabled="!hasImage || !naturalReady" @click="resetViewToOriginal">
              原始缩放
            </el-button>
          </div>

          <!-- 隐藏的文件选择器 -->
          <input
            ref="fileInputRef"
            type="file"
            accept="image/*"
            style="display: none"
            @change="onFileChange"
          />

          <div class="image-area" v-if="hasImage">
            <div class="preview-card preview-card-full">
              <div
                class="edit-container"
                ref="editContainerRef"
                @wheel="onWheel"
                @mousedown="onMouseDown"
                @mousemove="onMouseMove"
                @mouseup="onMouseUp"
                @mouseleave="onMouseLeave"
                @mouseenter="onMouseEnter"
                @click="onCanvasClick"
              >
                <div class="canvas-stage" ref="canvasStageRef" :style="stageStyle">
                  <canvas ref="editCanvasRef" class="edit-canvas"></canvas>
                  <div
                    v-if="hasSeedPoint && naturalReady"
                    class="seed-point-indicator"
                    :style="seedPointStyleInStage"
                  ></div>
                </div>
                <div v-show="magnifier.visible" class="magnifier" :style="magnifierStyle">
                  <canvas ref="magnifierCanvasRef" class="magnifier-canvas"></canvas>
                  <div class="magnifier-info">
                    ({{ magnifier.pixel.x }}, {{ magnifier.pixel.y }})
                  </div>
                </div>
                <div v-if="!naturalReady" class="image-placeholder">正在加载图片...</div>
              </div>
            </div>
          </div>

          <div v-else class="empty-tip">
            请先上传图片，或从图像处理模块中选择结果图片。
          </div>
        </div>

        <!-- 右侧：结果预览（与说明） -->
        <div class="right-pane">
          <div class="result-card">
            <div class="preview-title">结果图片</div>
            <div class="result-container">
              <img v-if="resultImageSrc" :src="resultImageSrc" class="result-image" />
              <div v-else class="result-placeholder">暂无结果，点击「开始填充」生成</div>
            </div>
          </div>

          <el-button
            type="success"
            size="small"
            :disabled="!hasImage || !hasSeedPoint || floodFillStore.isFilling"
            :loading="floodFillStore.isFilling"
            @click="handleStartFloodFill"
          >
            开始填充
          </el-button>

          <el-button
            style="margin-left: 0;"
            size="small"
            :disabled="!hasImage || !hasSeedPoint"
            @click="handlePlayAnimation"
          >
            播放动画
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from "vue";
import { ElMessage } from "element-plus";
import { storeToRefs } from "pinia";
import { useImageProcessingStore } from "@/stores/imageProcessing";
import { useFloodFillStore } from "@/stores/floodFill";

const imageProcessingStore = useImageProcessingStore();
const floodFillStore = useFloodFillStore();

const { currentImageId } = storeToRefs(imageProcessingStore);

const fileInputRef = ref(null);
const editContainerRef = ref(null);
const canvasStageRef = ref(null);
const editCanvasRef = ref(null);
const magnifierCanvasRef = ref(null);

const originalImageSrc = computed(() => floodFillStore.inputDisplayImageSrc);
const resultImageSrc = computed(() => floodFillStore.resultDisplayImageSrc);
const hasSeedPoint = computed(() => floodFillStore.hasSeedPoint);
const hasImage = computed(() => floodFillStore.hasImage);

const canUseProcessingImage = computed(() => !!currentImageId.value);

const naturalReady = ref(false);
const viewScale = ref(1);
const viewTranslate = ref({ x: 0, y: 0 });
const isPanning = ref(false);
const panStart = ref({ x: 0, y: 0, tx: 0, ty: 0 });
const undoStack = ref([]);
const maxUndo = 50;
const spacePressed = ref(false);

const magnifier = ref({
  visible: false,
  left: 0,
  top: 0,
  pixel: { x: 0, y: 0 },
});

const magnifierStyle = computed(() => {
  return {
    left: `${magnifier.value.left}px`,
    top: `${magnifier.value.top}px`,
  };
});

const MAG_PIXELS = 11;
// 放大镜每个像素格的显示尺寸（越大越“清晰”）
const MAG_SCALE = 12;
const MAG_CANVAS_SIZE = MAG_PIXELS * MAG_SCALE;
const MAG_BOX_PADDING = 10;
const MAG_BOX_W = MAG_CANVAS_SIZE + MAG_BOX_PADDING * 2;
const MAG_BOX_H = MAG_CANVAS_SIZE + MAG_BOX_PADDING * 2 + 20;
let magRaf = 0;
let magPending = false;
let lastMagClient = { x: 0, y: 0 };

const stageStyle = computed(() => {
  return {
    transform: `translate(${viewTranslate.value.x}px, ${viewTranslate.value.y}px) scale(${viewScale.value})`,
    transformOrigin: "0 0",
  };
});

const seedPointStyleInStage = computed(() => {
  // 让缩放/平移触发重新计算（虽然圆点会跟着 transform 走，但这里用于确保依赖完整）
  const _scale = viewScale.value;
  const _tx = viewTranslate.value.x;
  const _ty = viewTranslate.value.y;

  const canvas = editCanvasRef.value;
  if (!canvas || !hasSeedPoint.value) return {};

  const w = canvas.width || 0;
  const h = canvas.height || 0;
  if (!w || !h) return {};

  const cssW = canvas.clientWidth || 0;
  const cssH = canvas.clientHeight || 0;
  if (!cssW || !cssH) return {};

  const left = (floodFillStore.seedPoint.x / w) * cssW;
  const top = (floodFillStore.seedPoint.y / h) * cssH;

  return {
    left: `${left}px`,
    top: `${top}px`,
  };
});

const triggerUpload = () => {
  fileInputRef.value && fileInputRef.value.click();
};

const onFileChange = (event) => {
  const file = event.target.files && event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    const preview = e.target.result;
    floodFillStore.handleFloodImageUpload({
      path: file.path || "",
      preview,
    });
  };
  reader.readAsDataURL(file);

  // 重置 input，方便连续选择相同文件
  event.target.value = "";
};

const useFromProcessing = () => {
  if (!currentImageId.value) {
    ElMessage.warning("当前没有图像处理结果可用");
    return;
  }
  floodFillStore.useImageFromProcessing();
};

const setupCanvasFromOriginal = async () => {
  const src = originalImageSrc.value;
  const canvas = editCanvasRef.value;
  if (!src || !canvas) return;

  naturalReady.value = false;

  const img = new Image();
  img.crossOrigin = "anonymous";
  img.src = src;
  await new Promise((resolve, reject) => {
    img.onload = () => resolve();
    img.onerror = () => reject(new Error("图片加载失败"));
  });

  floodFillStore.setImageNaturalSize(img.naturalWidth, img.naturalHeight);
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;

  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(img, 0, 0);

  viewScale.value = 1;
  viewTranslate.value = { x: 0, y: 0 };
  undoStack.value = [];
  naturalReady.value = true;
};

const resetEditedToOriginal = async () => {
  if (!hasImage.value) return;
  try {
    await setupCanvasFromOriginal();
    ElMessage.success("已重置处理图");
  } catch (e) {
    ElMessage.error("重置失败");
  }
};

const getCanvasPointFromClient = (clientX, clientY) => {
  const canvas = editCanvasRef.value;
  if (!canvas) return null;
  const rect = canvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return null;

  const x = Math.floor(((clientX - rect.left) / rect.width) * canvas.width);
  const y = Math.floor(((clientY - rect.top) / rect.height) * canvas.height);
  if (x < 0 || y < 0 || x >= canvas.width || y >= canvas.height) return null;
  return { x, y, rect };
};

const clamp = (v, min, max) => Math.min(max, Math.max(min, v));

const setViewCenteredWithScale = (scale) => {
  const next = Number.isFinite(scale) ? scale : 1;
  const clamped = Math.min(8, Math.max(0.05, next));
  viewScale.value = clamped;

  const stage = canvasStageRef.value;
  if (!stage) {
    viewTranslate.value = { x: 0, y: 0 };
    return;
  }

  const baseW = stage.offsetWidth || 0; // 未应用 transform 的布局尺寸
  const baseH = stage.offsetHeight || 0;
  if (!baseW || !baseH) {
    viewTranslate.value = { x: 0, y: 0 };
    return;
  }

  // 关键点：.edit-container 已经用 flex 把“未缩放的 stage 布局盒子”居中。
  // transform 不参与布局，所以我们只需要补偿缩放带来的尺寸差：
  // 让缩放后的盒子仍以中心为基准缩放（视觉上居中）。
  viewTranslate.value = {
    x: (baseW * (1 - clamped)) / 2,
    y: (baseH * (1 - clamped)) / 2,
  };
};

const fitToContainer = async () => {
  if (!naturalReady.value) return;
  await nextTick();

  const container = editContainerRef.value;
  const stage = canvasStageRef.value;
  if (!container || !stage) return;

  const cr = container.getBoundingClientRect();
  const baseW = stage.offsetWidth || 0; // 不含 transform 的布局尺寸
  const baseH = stage.offsetHeight || 0;
  if (!cr.width || !cr.height || !baseW || !baseH) return;

  // “最大边占满”：等价于 contain，取 min 比例，使最长边刚好贴边，另一边留空
  const scale = Math.min(cr.width / baseW, cr.height / baseH);
  setViewCenteredWithScale(scale);
};

const resetViewToOriginal = async () => {
  if (!naturalReady.value) return;
  await nextTick();
  setViewCenteredWithScale(1);
};

const drawMagnifierAt = (pixelX, pixelY) => {
  const srcCanvas = editCanvasRef.value;
  const magCanvas = magnifierCanvasRef.value;
  if (!srcCanvas || !magCanvas) return;

  magCanvas.width = MAG_CANVAS_SIZE;
  magCanvas.height = MAG_CANVAS_SIZE;

  const ctx = magCanvas.getContext("2d");
  if (!ctx) return;

  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, MAG_CANVAS_SIZE, MAG_CANVAS_SIZE);

  const half = Math.floor(MAG_PIXELS / 2);
  const sx = clamp(pixelX - half, 0, Math.max(0, srcCanvas.width - MAG_PIXELS));
  const sy = clamp(pixelY - half, 0, Math.max(0, srcCanvas.height - MAG_PIXELS));

  ctx.drawImage(
    srcCanvas,
    sx,
    sy,
    MAG_PIXELS,
    MAG_PIXELS,
    0,
    0,
    MAG_CANVAS_SIZE,
    MAG_CANVAS_SIZE
  );

  // 网格线（每个像素格边界）
  ctx.save();
  ctx.strokeStyle = "rgba(226, 232, 240, 0.25)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let i = 1; i < MAG_PIXELS; i++) {
    const p = i * MAG_SCALE + 0.5;
    ctx.moveTo(p, 0);
    ctx.lineTo(p, MAG_CANVAS_SIZE);
    ctx.moveTo(0, p);
    ctx.lineTo(MAG_CANVAS_SIZE, p);
  }
  ctx.stroke();
  ctx.restore();

  // 中心像素十字
  const center = half * MAG_SCALE + Math.floor(MAG_SCALE / 2);
  ctx.strokeStyle = "rgba(34, 197, 94, 0.95)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(center + 0.5, 0);
  ctx.lineTo(center + 0.5, MAG_CANVAS_SIZE);
  ctx.moveTo(0, center + 0.5);
  ctx.lineTo(MAG_CANVAS_SIZE, center + 0.5);
  ctx.stroke();

  // 边框
  ctx.strokeStyle = "rgba(255, 255, 255, 0.85)";
  ctx.strokeRect(0.5, 0.5, MAG_CANVAS_SIZE - 1, MAG_CANVAS_SIZE - 1);
};

const updateMagnifierFromEvent = (event) => {
  if (!naturalReady.value) return;
  if (event.ctrlKey || spacePressed.value) return;

  const p = getCanvasPointFromClient(event.clientX, event.clientY);
  if (!p) {
    magnifier.value.visible = false;
    return;
  }

  magnifier.value.visible = true;
  magnifier.value.pixel = { x: p.x, y: p.y };

  const container = editContainerRef.value;
  if (container) {
    const cr = container.getBoundingClientRect();
    const rawLeft = event.clientX - cr.left + 16;
    const rawTop = event.clientY - cr.top + 16;
    const maxLeft = Math.max(0, cr.width - MAG_BOX_W - 4);
    const maxTop = Math.max(0, cr.height - MAG_BOX_H - 4);
    magnifier.value.left = clamp(rawLeft, 4, maxLeft);
    magnifier.value.top = clamp(rawTop, 4, maxTop);
  }

  lastMagClient = { x: event.clientX, y: event.clientY };
  if (magPending) return;
  magPending = true;
  if (magRaf) cancelAnimationFrame(magRaf);
  magRaf = requestAnimationFrame(() => {
    magPending = false;
    drawMagnifierAt(magnifier.value.pixel.x, magnifier.value.pixel.y);
  });
};

const pushUndo = () => {
  const canvas = editCanvasRef.value;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const snapshot = ctx.getImageData(0, 0, canvas.width, canvas.height);
  undoStack.value.push(snapshot);
  if (undoStack.value.length > maxUndo) undoStack.value.shift();
};

const undoPaint = () => {
  const canvas = editCanvasRef.value;
  if (!canvas) return;
  const last = undoStack.value.pop();
  if (!last) return;
  const ctx = canvas.getContext("2d");
  ctx.putImageData(last, 0, 0);
};

const paintWhitePixel = (x, y) => {
  const canvas = editCanvasRef.value;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  pushUndo();
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(x, y, 1, 1);
};

const onCanvasClick = (event) => {
  if (!naturalReady.value) return;
  if (event.altKey) {
    const p = getCanvasPointFromClient(event.clientX, event.clientY);
    if (!p) return;
    paintWhitePixel(p.x, p.y);
    // alt 点击涂色后立即刷新放大镜（否则需要移动鼠标才会触发 mousemove 重绘）
    updateMagnifierFromEvent(event);
    return;
  }

  // Ctrl / 空格用于缩放&拖动时，不应触发选点
  if (event.ctrlKey || spacePressed.value) return;

  const p = getCanvasPointFromClient(event.clientX, event.clientY);
  if (!p) return;

  floodFillStore.setSeedPointByClientPoint({
    offsetX: p.x,
    offsetY: p.y,
    clientWidth: editCanvasRef.value.width,
    clientHeight: editCanvasRef.value.height,
  });
};

const onWheel = (event) => {
  if (!event.ctrlKey) return;
  event.preventDefault();

  const delta = event.deltaY;
  const factor = delta > 0 ? 0.9 : 1.1;
  const next = Math.min(8, Math.max(0.2, viewScale.value * factor));
  viewScale.value = next;
};

const onMouseDown = (event) => {
  if (!(event.ctrlKey || spacePressed.value)) return;
  isPanning.value = true;
  panStart.value = {
    x: event.clientX,
    y: event.clientY,
    tx: viewTranslate.value.x,
    ty: viewTranslate.value.y,
  };
};

const onMouseMove = (event) => {
  if (isPanning.value) {
    const dx = event.clientX - panStart.value.x;
    const dy = event.clientY - panStart.value.y;
    viewTranslate.value = { x: panStart.value.tx + dx, y: panStart.value.ty + dy };
    magnifier.value.visible = false;
    return;
  }
  updateMagnifierFromEvent(event);
};

const onMouseUp = () => {
  isPanning.value = false;
};

const onMouseLeave = () => {
  isPanning.value = false;
  magnifier.value.visible = false;
};

const onMouseEnter = (event) => {
  updateMagnifierFromEvent(event);
};

const handleStartFloodFill = () => {
  if (!hasImage.value) {
    ElMessage.warning("请先选择或上传图片");
    return;
  }
  if (!hasSeedPoint.value) {
    ElMessage.warning("请先在图片上点击选取起始点");
    return;
  }

  const canvas = editCanvasRef.value;
  if (!canvas) {
    ElMessage.warning("处理图未就绪");
    return;
  }

  const dataUrl = canvas.toDataURL("image/png");
  floodFillStore
    .uploadEditedImageDataUrl(dataUrl)
    .then(() => {
      floodFillStore.startFloodFill();
    })
    .catch(() => {
      ElMessage.error("上传处理图失败");
    });
};

const handlePlayAnimation = () => {
  if (!hasImage.value || !hasSeedPoint.value) {
    ElMessage.warning("请先选择图片并选取起始点");
    return;
  }
  floodFillStore.playFloodFillAnimation(0);
};

const onKeyDown = (event) => {
  const key = (event && event.key) || "";
  const isZ = key.toLowerCase() === "z";
  if (event.ctrlKey && isZ) {
    event.preventDefault();
    undoPaint();
    return;
  }
  if (key === " " || key === "Spacebar" || event.code === "Space") {
    spacePressed.value = true;
    // 避免空格触发页面滚动，影响拖动体验
    event.preventDefault();
  }
};

const onKeyUp = (event) => {
  const key = (event && event.key) || "";
  if (key === " " || key === "Spacebar" || event.code === "Space") {
    spacePressed.value = false;
  }
};

watch(
  () => originalImageSrc.value,
  async (v) => {
    if (!v) return;
    try {
      await nextTick();
      await setupCanvasFromOriginal();
    } catch (e) {
      // ignore
    }
  }
);

onMounted(() => {
  window.addEventListener("keydown", onKeyDown);
  window.addEventListener("keyup", onKeyUp);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeyDown);
  window.removeEventListener("keyup", onKeyUp);
  if (magRaf) cancelAnimationFrame(magRaf);
});
</script>

<style scoped lang="less">
.flood-fill-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  padding: 10px 16px;
  border-bottom: 1px solid #e2e8f0;
}

.panel-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.panel-body {
  flex: 1;
  padding: 12px 16px;
  overflow: hidden;
}

.layout {
  display: flex;
  height: 100%;
  gap: 16px;
}

.left-pane {
  flex: 2;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.right-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.image-area {
  flex: 1;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.image {
  max-width: 100%;
  max-height: 100%;
  cursor: default;
  user-select: none;
}

.image-placeholder {
  color: #94a3b8;
  font-size: 13px;
}

.preview-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
}

.preview-card-full {
  flex: 1;
}

.preview-title {
  font-size: 12px;
  font-weight: 600;
  color: #0f172a;
}

.edit-container {
  flex: 1;
  background: #0f172a;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 180px;
  user-select: none;
}

.canvas-stage {
  position: relative;
  display: inline-block;
}

.edit-canvas {
  display: block;
  max-width: 100%;
  max-height: 100%;
}

.magnifier {
  position: absolute;
  width: 152px;
  height: 172px;
  background: rgba(15, 23, 42, 0.92);
  border: 1px solid rgba(226, 232, 240, 0.45);
  border-radius: 10px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.35);
  padding: 10px;
  pointer-events: none;
  z-index: 5;
  backdrop-filter: blur(8px);
}

.magnifier-canvas {
  width: 132px;
  height: 132px;
  display: block;
  border-radius: 8px;
}

.magnifier-info {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(226, 232, 240, 0.9);
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.seed-point-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid #22c55e;
  background: rgba(34, 197, 94, 0.4);
  position: absolute;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.7);
  pointer-events: none;
}

.tips {
  font-size: 12px;
  color: #64748b;
  line-height: 1.6;
}

.empty-tip {
  flex: 1;
  border-radius: 8px;
  border: 1px dashed #cbd5f5;
  background: #eff6ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1d4ed8;
  font-size: 13px;
}

.info-card {
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  padding: 10px 12px;
}

.info-card h4 {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.info-card ul {
  margin: 0;
  padding-left: 16px;
  font-size: 12px;
  color: #475569;
}

.result-card {
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-container {
  background: #0f172a;
  border-radius: 8px;
  overflow: hidden;
  min-height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-image {
  max-width: 100%;
  max-height: 100%;
  user-select: none;
}

.result-placeholder {
  color: #94a3b8;
  font-size: 13px;
}
</style>
