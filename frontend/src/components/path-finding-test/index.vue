<template>
  <div class="path-finding-test-wrapper">
    <div class="panel-body">
      <div class="layout">
        <div class="right-pane">
          <div style="display: flex; gap: 10px; width: 100%">
            <div class="result-card" style="flex: 1">
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
            <div class="result-card" style="flex: 1">
              <div class="preview-title">
                <div>小地图实时显示</div>
                <el-button size="small" type="primary" @click="startMiniMapCapture">
                  截屏获取
                </el-button>
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
              <div>寻路实况（预留）</div>
            </div>
            <div class="result-container">
              <div class="result-placeholder">这里预留给后续寻路实况联调</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { ElMessage } from "element-plus";
import { getMatchSocket } from "@/utils/matchSocket";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import { useImageProcessingStore } from "@/stores/imageProcessing";

const imageProcessingStore = useImageProcessingStore();

const originalMapFileInputRef = ref(null);
const originalMapImage = ref("");
const originalMapUploadRequestId = ref("");
const originalMapUploading = ref(false);
const originalMapUploadTimeout = ref(null);

const miniMapImage = ref("");
const matchMapImage = ref("");
const miniMapCenter = ref({ x: 0, y: 0 });
const miniMapRadius = ref(0);

const canUseImageProcessingResult = computed(
  () => !!imageProcessingStore.displayImageSrc
);
const originalMapDisplayImage = computed(() => originalMapImage.value || "");
const miniMapCenterText = computed(
  () => `(${miniMapCenter.value.x}, ${miniMapCenter.value.y})`
);
const miniMapRadiusText = computed(() => String(miniMapRadius.value || 0));

let socket = null;

onMounted(() => {
  socket = getMatchSocket() || window.matchSocket;
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
  if (socket && typeof socket.off === "function") {
    socket.off("mini-map-frame");
    socket.off("mini-map-meta");
    socket.off("match-map-frame");
    socket.off("path-image-uploaded");
  }
  if (originalMapUploadTimeout.value) {
    clearTimeout(originalMapUploadTimeout.value);
    originalMapUploadTimeout.value = null;
  }
});

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

const startMiniMapCapture = async () => {
  await ipc.invoke(ipcApiRoute.打开小地图截屏框, { size: 240 });
};
</script>

<style scoped lang="less">
.path-finding-test-wrapper {
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

.right-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.preview-title {
  font-size: 12px;
  font-weight: 600;
  color: #0f172a;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
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
