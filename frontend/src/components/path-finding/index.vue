<template>
  <div class="path-finding-wrapper">
    <div class="panel-body">
      <div class="layout">
        <div class="left-pane">
          <div class="toolbar">
            <el-button type="primary" size="small" @click="triggerUpload">上传图片</el-button>
            <el-button size="small" :disabled="!canUseFloodFillResult" @click="useFloodFillResult">
              使用洪水填充结果
            </el-button>
            <el-button size="small" :disabled="!hasImage || pathFindingStore.isGettingSkeleton" :loading="pathFindingStore.isGettingSkeleton" @click="handleGetSkeleton">
              获取骨干网
            </el-button>
            <el-button
              type="success"
              size="small"
              :disabled="!hasImage || !hasStart || !hasEnd || pathFindingStore.isFinding"
              :loading="pathFindingStore.isFinding"
              @click="handleStartFinding"
            >
              开始寻路
            </el-button>
          </div>

          <input ref="fileInputRef" type="file" accept="image/*" style="display:none" @change="onFileChange" />

          <div v-if="hasImage" class="image-area">
            <div class="preview-title">上传/输入图片（点击选点：先起点后终点）</div>
            <div class="edit-container" @click="onCanvasClick">
              <canvas ref="canvasRef" class="edit-canvas"></canvas>
              <div v-if="hasStart && naturalReady" class="pt start" :style="startStyle"></div>
              <div v-if="hasEnd && naturalReady" class="pt end" :style="endStyle"></div>
              <div v-if="!naturalReady" class="image-placeholder">正在加载图片...</div>
            </div>
            <div class="tips">
              <div>起点：({{ startPoint.x ?? "-" }}, {{ startPoint.y ?? "-" }})</div>
              <div>终点：({{ endPoint.x ?? "-" }}, {{ endPoint.y ?? "-" }})</div>
              <div v-if="pathFindingStore.lastErrorMessage" class="err">{{ pathFindingStore.lastErrorMessage }}</div>
            </div>
          </div>
          <div v-else class="empty-tip">请先上传图片，或使用洪水填充后的图片。</div>
        </div>

        <div class="right-pane">
          <div class="result-card">
            <div class="preview-title">骨干网</div>
            <div class="result-container">
              <img v-if="skeletonImage" :src="skeletonImage" class="result-image" />
              <div v-else class="result-placeholder">暂无骨干网结果</div>
            </div>
          </div>

          <div class="result-card">
            <div class="preview-title">路线图</div>
            <div class="result-container">
              <img v-if="resultImage" :src="resultImage" class="result-image" />
              <div v-else class="result-placeholder">暂无路线结果</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from "vue";
import { ElMessage } from "element-plus";
import { storeToRefs } from "pinia";
import { useFloodFillStore } from "@/stores/floodFill";
import { usePathFindingStore } from "@/stores/pathFinding";

const floodFillStore = useFloodFillStore();
const pathFindingStore = usePathFindingStore();

const { startPoint, endPoint } = storeToRefs(pathFindingStore);

const fileInputRef = ref(null);
const canvasRef = ref(null);
const naturalReady = ref(false);

const inputSrc = computed(() => pathFindingStore.inputDisplayImageSrc);
const skeletonImage = computed(() => pathFindingStore.skeletonImage);
const resultImage = computed(() => pathFindingStore.resultImage);

const hasImage = computed(() => pathFindingStore.hasImage);
const hasStart = computed(() => pathFindingStore.hasStart);
const hasEnd = computed(() => pathFindingStore.hasEnd);
const canUseFloodFillResult = computed(() => !!floodFillStore.resultDisplayImageSrc);

const triggerUpload = () => fileInputRef.value && fileInputRef.value.click();

const onFileChange = (event) => {
  const file = event.target.files && event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    const preview = e.target.result;
    pathFindingStore.handlePathImageUpload({
      path: file.path || "",
      preview,
    });
  };
  reader.readAsDataURL(file);
  event.target.value = "";
};

const useFloodFillResult = async () => {
  if (!canUseFloodFillResult.value) {
    ElMessage.warning("当前没有洪水填充结果可用");
    return;
  }
  await pathFindingStore.useFloodFillResultAsInput();
};

const setupCanvas = async () => {
  const src = inputSrc.value;
  const canvas = canvasRef.value;
  if (!src || !canvas) return;

  naturalReady.value = false;
  const img = new Image();
  img.crossOrigin = "anonymous";
  img.src = src;
  await new Promise((resolve, reject) => {
    img.onload = () => resolve();
    img.onerror = () => reject(new Error("图片加载失败"));
  });

  pathFindingStore.setImageNaturalSize(img.naturalWidth, img.naturalHeight);
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(img, 0, 0);
  naturalReady.value = true;
};

const getCanvasPointFromClient = (clientX, clientY) => {
  const canvas = canvasRef.value;
  if (!canvas) return null;
  const rect = canvas.getBoundingClientRect();
  if (!rect.width || !rect.height) return null;

  const x = Math.floor(((clientX - rect.left) / rect.width) * canvas.width);
  const y = Math.floor(((clientY - rect.top) / rect.height) * canvas.height);
  if (x < 0 || y < 0 || x >= canvas.width || y >= canvas.height) return null;
  return { x, y, rect };
};

const onCanvasClick = (event) => {
  if (!naturalReady.value) return;
  const p = getCanvasPointFromClient(event.clientX, event.clientY);
  if (!p) return;

  const type = !hasStart.value ? "start" : !hasEnd.value ? "end" : "start";
  if (type === "start") {
    // 如果已经有终点，再点一次从头开始
    if (hasEnd.value) {
      endPoint.value = { x: null, y: null };
    }
  }

  pathFindingStore.setPointByImagePoint({
    type,
    x: p.x,
    y: p.y,
  });
};

const getMarkerStyle = (pt) => {
  const canvas = canvasRef.value;
  if (!canvas) return {};

  // 关键点：canvas 在容器内是居中显示的，且会按容器缩放。
  // 需要用 DOMRect 来拿到 canvas 相对容器的真实偏移与尺寸。
  const canvasRect = canvas.getBoundingClientRect();
  const parent = canvas.parentElement;
  if (!parent) return {};
  const parentRect = parent.getBoundingClientRect();

  const cw = canvas.width || 0;
  const ch = canvas.height || 0;
  if (!cw || !ch) return {};

  const x = Number(pt?.x);
  const y = Number(pt?.y);
  if (!Number.isFinite(x) || !Number.isFinite(y)) return {};

  const left = (canvasRect.left - parentRect.left) + (x / cw) * canvasRect.width;
  const top = (canvasRect.top - parentRect.top) + (y / ch) * canvasRect.height;
  return { left: `${left}px`, top: `${top}px` };
};

const startStyle = computed(() => {
  if (!hasStart.value) return {};
  return getMarkerStyle(startPoint.value);
});

const endStyle = computed(() => {
  if (!hasEnd.value) return {};
  return getMarkerStyle(endPoint.value);
});

const handleGetSkeleton = () => {
  if (!hasImage.value) {
    ElMessage.warning("请先选择或上传图片");
    return;
  }
  pathFindingStore.getSkeleton();
};

const handleStartFinding = () => {
  if (!hasImage.value) {
    ElMessage.warning("请先选择或上传图片");
    return;
  }
  if (!hasStart.value || !hasEnd.value) {
    ElMessage.warning("请先在图片上选择起点和终点");
    return;
  }
  pathFindingStore.startFinding();
};

watch(
  () => inputSrc.value,
  async (v) => {
    if (!v) return;
    try {
      await nextTick();
      await setupCanvas();
    } catch (e) {
      // ignore
    }
  },
  { immediate: true }
);
</script>

<style scoped lang="less">
.path-finding-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
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
  min-width: 0;
}

.right-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
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
  gap: 10px;
  min-height: 0;
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
  min-height: 220px;
  user-select: none;
  cursor: crosshair;
}

.edit-canvas {
  display: block;
  max-width: 100%;
  max-height: 100%;
}

.image-placeholder {
  color: #94a3b8;
  font-size: 13px;
}

.pt {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  position: absolute;
  transform: translate(-50%, -50%);
  pointer-events: none;
  box-shadow: 0 0 6px rgba(255, 255, 255, 0.25);
}
.pt.start {
  border: 2px solid #3b82f6;
  background: rgba(59, 130, 246, 0.35);
}
.pt.end {
  border: 2px solid #f59e0b;
  background: rgba(245, 158, 11, 0.35);
}

.tips {
  font-size: 12px;
  color: #475569;
  line-height: 1.6;
}
.err {
  margin-top: 4px;
  color: #ef4444;
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

.result-card {
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
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
