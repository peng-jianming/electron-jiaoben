<template>
  <div class="path-finding-wrapper">
    <div class="panel-body">
      <div class="layout">
        <div class="left-pane">
          <div class="left-pane-row">
            <div class="result-card">
              <div class="preview-title">
                <div>规划图</div>
                <div class="toolbar">
                  <el-button type="primary" size="small" @click="triggerUpload"
                    >上传图片</el-button
                  >
                  <el-button
                    size="small"
                    :disabled="!canUseFloodFillResult"
                    @click="useFloodFillResult"
                  >
                    洪水填充结果
                  </el-button>
                </div>

                <input
                  ref="fileInputRef"
                  type="file"
                  accept="image/*"
                  style="display: none"
                  @change="onFileChange"
                />
              </div>
              <div class="result-container">
                <div v-if="hasImage" class="image-area">
                  <div
                    class="edit-container"
                    :class="{ 'is-selecting-point': !!selectionMode }"
                    @click="onCanvasClick"
                    @mousedown="onCanvasMouseDown"
                  >
                    <canvas
                      ref="canvasRef"
                      class="edit-canvas"
                      :style="canvasTransformStyle"
                    ></canvas>
                    <div
                      v-if="hasStart && naturalReady"
                      class="pt start"
                      :style="startStyle"
                    ></div>
                    <div
                      v-if="hasEnd && naturalReady"
                      class="pt end"
                      :style="endStyle"
                    ></div>
                    <div v-if="!naturalReady" class="image-placeholder">
                      正在加载图片...
                    </div>
                  </div>
                  <div class="tips">
                    <div v-if="pathFindingStore.lastErrorMessage" class="err">
                      {{ pathFindingStore.lastErrorMessage }}
                    </div>
                  </div>
                </div>
                <div v-else class="result-placeholder">
                  请先上传图片，或使用洪水填充后的图片。
                </div>
              </div>
            </div>
            <div class="result-card">
              <div class="preview-title">
                <div>原始地图</div>
                <div class="toolbar">
                  <el-button
                    size="small"
                    :loading="originalMapUploading"
                    :disabled="originalMapUploading"
                    @click="triggerOriginalMapUpload"
                  >
                    上传原始地图
                  </el-button>
                  <el-button
                    size="small"
                    :loading="originalMapUploading"
                    :disabled="!canUseImageProcessingResult || originalMapUploading"
                    @click="useImageProcessingResult"
                  >
                    图片处理结果
                  </el-button>
                  <input
                    ref="originalMapFileInputRef"
                    type="file"
                    accept="image/*"
                    style="display: none"
                    @change="onOriginalMapFileChange"
                  />
                </div>
              </div>
              <div class="result-container">
                <img
                  v-if="originalMapDisplayImage"
                  :src="originalMapDisplayImage"
                  class="result-image"
                />
                <div v-else class="result-placeholder">暂无原始地图</div>
              </div>
            </div>
          </div>

          <div class="left-pane-row">
            <div class="result-card">
              <div class="preview-title">
                <div>骨干网</div>
                <el-button
                  size="small"
                  :disabled="!hasImage || pathFindingStore.isGettingSkeleton"
                  :loading="pathFindingStore.isGettingSkeleton"
                  @click="handleGetSkeleton"
                >
                  获取骨干网
                </el-button>
              </div>
              <div class="result-container">
                <img v-if="skeletonImage" :src="skeletonImage" class="result-image" />
                <div v-else class="result-placeholder">暂无骨干网结果</div>
              </div>
            </div>

            <div class="result-card">
              <div class="preview-title">
                <div>路线图</div>
                <el-button
                  type="success"
                  size="small"
                  :disabled="
                    !hasImage || !hasStart || !hasEnd || pathFindingStore.isFinding
                  "
                  :loading="pathFindingStore.isFinding"
                  @click="handleStartFinding"
                >
                  规划路线
                </el-button>
              </div>
              <div class="result-container">
                <img v-if="resultImage" :src="resultImage" class="result-image" />
                <div v-else class="result-placeholder">暂无路线结果</div>
              </div>
              <div style="display: flex; align-items: center; gap: 10px">
                <el-input size="small" :model-value="startInputText" :readonly="true">
                  <template #append>
                    <el-button
                      size="small"
                      :disabled="!canSelectPoints"
                      @click="selectStart"
                    >
                      起点
                    </el-button>
                  </template>
                </el-input>
                <el-input size="small" :model-value="endInputText" :readonly="true">
                  <template #append>
                    <el-button
                      size="small"
                      :disabled="!canSelectPoints"
                      @click="selectEnd"
                    >
                      终点
                    </el-button>
                  </template>
                </el-input>
              </div>
            </div>
          </div>
        </div>

        <div class="right-pane">
          <div style="display: flex; gap: 10px; width: 100%">
            <div class="result-card" style="flex: 1">
              <div class="preview-title">
                <div>小地图实时显示</div>
                <el-button size="small" type="primary" @click="startMiniMapCapture"
                  >截屏获取</el-button
                >
              </div>
              <div class="result-container">
                <img v-if="miniMapImage" :src="miniMapImage" class="result-image" />
                <div v-else class="result-placeholder">暂无小地图结果</div>
              </div>
              <div>
                <span
                  style="
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    margin-right: 10px;
                  "
                >
                  中心坐标:
                  <el-input
                    size="small"
                    :model-value="miniMapCenterText"
                    readonly
                    style="width: 160px"
                  />
                </span>
                <span style="display: inline-flex; align-items: center; gap: 6px">
                  正方形半径:
                  <el-input
                    size="small"
                    :model-value="miniMapRadiusText"
                    readonly
                    style="width: 120px"
                  />
                </span>
              </div>
            </div>
            <div class="result-card" style="flex: 1">
              <div class="preview-title">
                <div>匹配地图实时显示</div>
              </div>
              <div class="result-container">
                <img v-if="matchMapImage" :src="matchMapImage" class="result-image" />
                <div v-else class="result-placeholder">暂无匹配地图结果</div>
              </div>
            </div>
          </div>
          <div class="result-card">
            <div class="preview-title">
              <div>寻路实况</div>
              <el-button size="small">开始寻路</el-button>
            </div>
            <div class="result-container">
              <img v-if="aaa" :src="aaa" class="result-image" />
              <div v-else class="result-placeholder">暂无寻路结果</div>
            </div>
            <div style="display: flex; align-items: center; gap: 10px">
              <el-input size="small" :readonly="true">
                <template #append>
                  <el-button size="small"> 角色中心坐标点 </el-button>
                </template>
              </el-input>
              <el-input size="small" placeholder="请输入半径范围" :readonly="true">
                <template #prepend> 半径范围 </template>
              </el-input>
              <el-input size="small" :readonly="true">
                <template #append>
                  <el-button size="small"> 终点 </el-button>
                </template>
              </el-input>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from "vue";
import { ElMessage } from "element-plus";
import { storeToRefs } from "pinia";
import { useFloodFillStore } from "@/stores/floodFill";
import { usePathFindingStore } from "@/stores/pathFinding";
import { useImageProcessingStore } from "@/stores/imageProcessing";
import { getMatchSocket } from "@/utils/matchSocket";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";

const floodFillStore = useFloodFillStore();
const pathFindingStore = usePathFindingStore();
const imageProcessingStore = useImageProcessingStore();

const { startPoint, endPoint } = storeToRefs(pathFindingStore);

const fileInputRef = ref(null);
const originalMapFileInputRef = ref(null);
const canvasRef = ref(null);
const naturalReady = ref(false);
const selectionMode = ref(null); // 'start' | 'end' | null
const originalMapImage = ref("");
const originalMapUploadRequestId = ref("");
const originalMapUploading = ref(false);
const originalMapUploadTimeout = ref(null);

const inputSrc = computed(() => pathFindingStore.inputDisplayImageSrc);
const skeletonImage = computed(() => pathFindingStore.skeletonImage);
const resultImage = computed(() => pathFindingStore.resultImage);

const miniMapImage = ref("");
const matchMapImage = ref("");
const miniMapCenter = ref({ x: 0, y: 0 });
const miniMapRadius = ref(0);

const miniMapCenterText = computed(
  () => `(${miniMapCenter.value.x}, ${miniMapCenter.value.y})`
);
const miniMapRadiusText = computed(() => String(miniMapRadius.value || 0));

// 规划图平移相关状态（按住 Ctrl 或空格拖动）
const panOffset = ref({ x: 0, y: 0 });
const isPanning = ref(false);
const lastPanPoint = ref(null);
const isPanKeyPressed = ref(false);

const canvasTransformStyle = computed(() => {
  const x = panOffset.value.x || 0;
  const y = panOffset.value.y || 0;
  if (!x && !y) return {};
  return {
    transform: `translate(${x}px, ${y}px)`,
  };
});

const hasImage = computed(() => pathFindingStore.hasImage);
const hasStart = computed(() => pathFindingStore.hasStart);
const hasEnd = computed(() => pathFindingStore.hasEnd);
const canSelectPoints = computed(() => hasImage.value && naturalReady.value);
const isSelectingPoint = computed(
  () => selectionMode.value === "start" || selectionMode.value === "end"
);
const startInputText = computed(() => {
  if (!hasStart.value) return "";
  return `(${startPoint.value.x}, ${startPoint.value.y})`;
});
const endInputText = computed(() => {
  if (!hasEnd.value) return "";
  return `(${endPoint.value.x}, ${endPoint.value.y})`;
});
const canUseFloodFillResult = computed(() => !!floodFillStore.resultDisplayImageSrc);
const canUseImageProcessingResult = computed(
  () => !!imageProcessingStore.displayImageSrc
);
const originalMapDisplayImage = computed(() => originalMapImage.value || "");

// 处理 Ctrl / 空格键状态
const updatePanKey = (event, pressed) => {
  const key = event.key;
  if (key === "Control" || event.ctrlKey) {
    isPanKeyPressed.value = pressed;
    if (!pressed) {
      stopPanning();
    }
    return;
  }
  if (key === " " || key === "Spacebar" || event.code === "Space") {
    isPanKeyPressed.value = pressed;
    if (!pressed) {
      stopPanning();
    }
  }
};

const handleKeyDown = (event) => {
  updatePanKey(event, true);
};

const handleKeyUp = (event) => {
  updatePanKey(event, false);
};

onMounted(() => {
  window.addEventListener("keydown", handleKeyDown);
  window.addEventListener("keyup", handleKeyUp);

  const socket = getMatchSocket() || window.matchSocket;
  if (!socket) return;

  socket.on("mini-map-frame", (data) => {
    const payload = data || {};
    if (typeof payload.image === "string") {
      miniMapImage.value = payload.image || "";
    }
    if (
      payload.center &&
      Number.isFinite(payload.center.x) &&
      Number.isFinite(payload.center.y)
    ) {
      miniMapCenter.value = {
        x: Math.round(payload.center.x),
        y: Math.round(payload.center.y),
      };
    }
    if (Number.isFinite(payload.radius)) {
      miniMapRadius.value = Math.max(0, Math.round(payload.radius));
    }
  });

  socket.on("mini-map-meta", (data) => {
    const payload = data || {};
    if (!payload.bounds) {
      return;
    }
    if (
      payload.center &&
      Number.isFinite(payload.center.x) &&
      Number.isFinite(payload.center.y)
    ) {
      miniMapCenter.value = {
        x: Math.round(payload.center.x),
        y: Math.round(payload.center.y),
      };
    }
    if (Number.isFinite(payload.radius)) {
      miniMapRadius.value = Math.max(0, Math.round(payload.radius));
    }
  });

  socket.on("match-map-frame", (data) => {
    const payload = data || {};
    if (typeof payload.image === "string") {
      matchMapImage.value = payload.image || "";
    }
  });

  socket.on("path-image-uploaded", (data) => {
    const payload = data || {};
    if (!originalMapUploadRequestId.value) return;
    if (payload.requestId !== originalMapUploadRequestId.value) return;
    if (typeof payload.preview === "string") {
      originalMapImage.value = payload.preview || "";
    }
    clearOriginalMapUploading();
  });
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleKeyDown);
  window.removeEventListener("keyup", handleKeyUp);
  stopPanning();
});

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

const triggerOriginalMapUpload = () =>
  originalMapFileInputRef.value && originalMapFileInputRef.value.click();

const clearOriginalMapUploading = () => {
  originalMapUploadRequestId.value = "";
  originalMapUploading.value = false;
  if (originalMapUploadTimeout.value) {
    clearTimeout(originalMapUploadTimeout.value);
    originalMapUploadTimeout.value = null;
  }
};

const uploadOriginalMapByPayload = async (payload = {}, useBase64 = false) => {
  const requestId = `original-map-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  originalMapUploadRequestId.value = requestId;
  originalMapUploading.value = true;
  if (originalMapUploadTimeout.value) {
    clearTimeout(originalMapUploadTimeout.value);
  }
  originalMapUploadTimeout.value = setTimeout(() => {
    if (originalMapUploadRequestId.value === requestId) {
      clearOriginalMapUploading();
      ElMessage.warning("原始地图上传超时，请重试");
    }
  }, 10000);
  const 类型 = useBase64 ? "寻路上传base64缓存" : "寻路上传缓存";
  try {
    await ipc.invoke(ipcApiRoute.发送到后端, {
      类型,
      ...payload,
      requestId,
    });
  } catch (e) {
    clearOriginalMapUploading();
    ElMessage.error("发送原始地图到后端失败");
  }
};

const onOriginalMapFileChange = (event) => {
  const file = event.target.files && event.target.files[0];
  if (!file) return;
  if (!file.path) {
    ElMessage.warning("未获取到文件路径，无法上传到后端");
    event.target.value = "";
    return;
  }
  uploadOriginalMapByPayload({ 图片路径: file.path }, false);
  event.target.value = "";
};

const useImageProcessingResult = () => {
  if (!canUseImageProcessingResult.value) {
    ElMessage.warning("当前没有图片处理结果可用");
    return;
  }
  uploadOriginalMapByPayload(
    { dataUrl: imageProcessingStore.displayImageSrc || "" },
    true
  );
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
  // 按住平移快捷键拖动时，不进行起终点选择
  if (isPanning.value || isPanKeyPressed.value || event.ctrlKey) return;
  if (!selectionMode.value) return;
  const p = getCanvasPointFromClient(event.clientX, event.clientY);
  if (!p) return;

  pathFindingStore.setPointByImagePoint({
    type: selectionMode.value,
    x: p.x,
    y: p.y,
  });
  selectionMode.value = null;
};

const onCanvasMouseDown = (event) => {
  if (!naturalReady.value) return;
  // 仅在按住 Ctrl 或空格时启用拖动
  const shouldPan = isPanKeyPressed.value || event.ctrlKey;
  if (!shouldPan || event.button !== 0) return;

  isPanning.value = true;
  lastPanPoint.value = { x: event.clientX, y: event.clientY };

  window.addEventListener("mousemove", onCanvasMouseMove);
  window.addEventListener("mouseup", onCanvasMouseUp);
  event.preventDefault();
};

const onCanvasMouseMove = (event) => {
  if (!isPanning.value || !lastPanPoint.value) return;
  const dx = event.clientX - lastPanPoint.value.x;
  const dy = event.clientY - lastPanPoint.value.y;
  panOffset.value = {
    x: (panOffset.value.x || 0) + dx,
    y: (panOffset.value.y || 0) + dy,
  };
  lastPanPoint.value = { x: event.clientX, y: event.clientY };
};

const stopPanning = () => {
  if (!isPanning.value) return;
  isPanning.value = false;
  lastPanPoint.value = null;
  window.removeEventListener("mousemove", onCanvasMouseMove);
  window.removeEventListener("mouseup", onCanvasMouseUp);
};

const onCanvasMouseUp = () => {
  stopPanning();
};

const selectStart = () => {
  if (!hasImage.value) return;
  if (!naturalReady.value) {
    ElMessage.info("图片正在加载中，请稍候再点");
    return;
  }
  selectionMode.value = "start";
};

const selectEnd = () => {
  if (!hasImage.value) return;
  if (!naturalReady.value) {
    ElMessage.info("图片正在加载中，请稍候再点");
    return;
  }
  selectionMode.value = "end";
};

const getMarkerStyle = (pt) => {
  // 依赖 panOffset，使平移时重新计算标记位置
  const _ox = panOffset.value.x;
  const _oy = panOffset.value.y;

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

  const left = canvasRect.left - parentRect.left + (x / cw) * canvasRect.width;
  const top = canvasRect.top - parentRect.top + (y / ch) * canvasRect.height;
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
    ElMessage.warning("请先选择起点和终点");
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
    selectionMode.value = null;
  },
  { immediate: true }
);

const startMiniMapCapture = async () => {
  await ipc.invoke(ipcApiRoute.打开小地图截屏框, { size: 240 });
};
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
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.left-pane-row {
  display: flex;
  gap: 10px;
  width: 100%;
  flex: 1;
  min-height: 0;
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
  display: flex;
  align-items: center;
  justify-content: space-between;
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
  cursor: default;
}

.edit-container.is-selecting-point {
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
  flex: 1;
}

.result-container {
  background: #0f172a;
  border-radius: 8px;
  overflow: hidden;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
}

.left-pane .result-container {
  min-height: 0;
}

.result-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  user-select: none;
}

.result-placeholder {
  color: #94a3b8;
  font-size: 13px;
}
</style>
