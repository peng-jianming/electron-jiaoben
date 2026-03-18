<template>
  <div class="flood-fill-wrapper">
    <div class="panel-header">
      <h3 class="panel-title">洪水填充</h3>
    </div>

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
              size="small"
              :disabled="!hasImage || !hasSeedPoint"
              @click="handlePlayAnimation"
            >
              播放动画
            </el-button>
            <el-button size="small" :disabled="!hasImage" @click="resetEditedToOriginal">
              重置处理图
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
              <div class="preview-title">当前图片</div>
              <div
                class="edit-container"
                ref="editContainerRef"
                @wheel="onWheel"
                @mousedown="onMouseDown"
                @mousemove="onMouseMove"
                @mouseup="onMouseUp"
                @mouseleave="onMouseUp"
                @click="onCanvasClick"
              >
                <div
                  class="canvas-stage"
                  ref="canvasStageRef"
                  :style="stageStyle"
                >
                  <canvas ref="editCanvasRef" class="edit-canvas"></canvas>
                  <div
                    v-if="hasSeedPoint && naturalReady"
                    class="seed-point-indicator"
                    :style="seedPointStyleInStage"
                  ></div>
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
              <img
                v-if="resultImageSrc"
                :src="resultImageSrc"
                class="result-image"
              />
              <div v-else class="result-placeholder">暂无结果，点击「开始填充」生成</div>
            </div>
          </div>

          <div class="info-card">
            <h4>当前状态</h4>
            <ul>
              <li>
                图片：<span>{{ hasImage ? "已就绪" : "未选择" }}</span>
              </li>
              <li>
                起始点：
                <span v-if="hasSeedPoint">
                  ({{ floodFillStore.seedPoint.x }}, {{ floodFillStore.seedPoint.y }})
                </span>
                <span v-else>未选择</span>
              </li>
              <li>
                填充状态：
                <span>
                  {{ floodFillStore.isFilling ? "填充中..." : "空闲" }}
                </span>
              </li>
            </ul>
          </div>

          <div class="info-card">
            <h4>说明</h4>
            <p>可以在图像处理中先做二值化、膨胀、腐蚀等操作，让需要填充的区域闭合后，再在此处执行洪水填充。</p>
          </div>
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
  if (!isPanning.value) return;
  const dx = event.clientX - panStart.value.x;
  const dy = event.clientY - panStart.value.y;
  viewTranslate.value = { x: panStart.value.tx + dx, y: panStart.value.ty + dy };
};

const onMouseUp = () => {
  isPanning.value = false;
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
