<template>
  <div class="image-stitching-wrapper">
    <div class="panel-body">
      <div class="layout">
        <div class="left-pane">
          <div class="result-card">
            <div class="preview-title">
              <div>待拼接图片</div>
              <div class="toolbar">
                <el-button
                  type="primary"
                  size="small"
                  @click="triggerUpload"
                  :disabled="stitchStore.isStitching || captureMode"
                >
                  上传多张图片
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  :disabled="!images.length || stitchStore.isStitching || captureMode"
                  @click="clearImages"
                >
                  清空
                </el-button>
                <el-button
                  size="small"
                  type="success"
                  :disabled="stitchStore.isStitching || captureMode"
                  @click="startCaptureAndStitch"
                >
                  不断截屏并拼接
                </el-button>
                <el-button
                  size="small"
                  type="warning"
                  :disabled="!captureMode"
                  @click="stopCaptureAndStitch"
                >
                  停止截屏
                </el-button>
              </div>
            </div>

            <input
              ref="fileInputRef"
              type="file"
              accept="image/*"
              multiple
              style="display: none"
              @change="onFileChange"
            />

            <div class="image-list">
              <div v-if="images.length" class="image-items">
                <div v-for="img in images" :key="img.id" class="image-item">
                  <div class="image-item-meta">
                    <div class="image-item-name">{{ img.name }}</div>
                    <div class="image-item-size">{{ formatBytes(img.size) }}</div>
                  </div>
                  <el-button
                    size="small"
                    type="danger"
                    text
                    :disabled="stitchStore.isStitching || captureMode"
                    @click="removeImage(img.id)"
                  >
                    删除
                  </el-button>
                </div>
              </div>
              <div v-else class="empty-tip">暂无图片，请先上传至少两张</div>
            </div>

            <div class="options-card">
              <div class="tip-row">预处理步骤使用「图像处理」页当前保存的流水线参数。</div>
            </div>

            <div class="actions">
              <el-button
                type="success"
                size="small"
                :disabled="!canStart"
                :loading="stitchStore.isStitching"
                @click="startStitching"
              >
                开始拼接
              </el-button>
            </div>

            <div class="tips">
              <div v-if="captureMode" class="progress-msg">
                {{
                  capturedFrameCount === 0
                    ? "已打开截屏框：请在弹框点击“开始”后再截屏"
                    : `截屏中：已获取 ${capturedFrameCount} 帧（增量拼接）`
                }}
              </div>
              <div v-if="stitchStore.progressMessage" class="progress-msg">
                {{ stitchStore.progressMessage }}
              </div>
              <div v-if="stitchStore.lastErrorMessage" class="err">
                {{ stitchStore.lastErrorMessage }}
              </div>
            </div>

            <el-progress v-if="stitchStore.isStitching" :percentage="stitchStore.progress" />
          </div>
        </div>

        <div class="right-pane">
          <div class="result-card">
            <div class="preview-title">
              <div>拼接结果</div>
            </div>
            <div class="result-container">
              <img
                v-if="stitchStore.resultImageSrc"
                :src="stitchStore.resultImageSrc"
                class="result-image"
              />
              <div v-else class="result-placeholder">
                {{
                  captureMode
                    ? capturedFrameCount < 1
                      ? "截屏模式：等待第一帧截屏…"
                      : "等待拼接结果…"
                    : images.length < 2
                      ? "上传至少两张图片"
                      : "点击「开始拼接」生成结果"
                }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from "vue";
import { useImageStitchingStore } from "@/stores/imageStitching";
import { createMiniMapFrameCapturer } from "@/utils/miniMapCapture";

const stitchStore = useImageStitchingStore();

const fileInputRef = ref(null);
const images = ref([]); // {id, filePath, name, size}

const captureMode = ref(false);
const capturedFrameCount = ref(0); // 纯计数（只用于展示，不保存所有帧，避免内存增长）
let miniMapCapturer = null;
let stitchSessionId = "";
let pendingLatestFrame = null; // 始终只保留“最新一帧”，避免越积越多
let initRequested = false;
let baseReady = false;
let shouldEndSession = false;
let lastIncrementalOp = null; // 'init' | 'step' | null

const canStart = computed(() => !captureMode.value && images.value.length >= 2 && stitchStore.canStart);

const triggerUpload = () => {
  fileInputRef.value && fileInputRef.value.click();
};

const formatBytes = (bytes) => {
  const b = Number(bytes || 0);
  if (!Number.isFinite(b) || b <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let idx = 0;
  let v = b;
  while (v >= 1024 && idx < units.length - 1) {
    v /= 1024;
    idx += 1;
  }
  return `${v.toFixed(idx === 0 ? 0 : 1)} ${units[idx]}`;
};

const addFiles = (fileList) => {
  if (!fileList) return;
  const list = Array.from(fileList);
  if (!list.length) return;

  const existing = new Set(images.value.map((i) => i.filePath));
  const next = [];

  for (const file of list) {
    const filePath = file?.path || "";
    if (!filePath) continue; // electron 才会有 path，浏览器环境下不会走到这里
    if (existing.has(filePath)) continue;

    next.push({
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      filePath,
      name: file?.name || filePath,
      size: file?.size || 0,
    });
    existing.add(filePath);
  }

  if (next.length) images.value = images.value.concat(next);
};

const onFileChange = (event) => {
  const files = event.target.files;
  if (files && files.length) addFiles(files);
  // 清空 input，方便再次选择同一批文件能触发 change
  event.target.value = "";
};

const removeImage = (id) => {
  if (!id) return;
  images.value = images.value.filter((i) => i.id !== id);
};

const clearImages = () => {
  images.value = [];
  stitchStore.reset();
};

const startStitching = () => {
  if (!canStart.value) return;

  const paths = images.value.map((i) => i.filePath).filter(Boolean);
  stitchStore.startStitching(paths);
};

const startCaptureAndStitch = async () => {
  if (captureMode.value) return;

  captureMode.value = true;
  capturedFrameCount.value = 0;
  stitchSessionId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  pendingLatestFrame = null;
  initRequested = false;
  baseReady = false;
  shouldEndSession = false;
  lastIncrementalOp = null;
  stitchStore.reset();

  miniMapCapturer = createMiniMapFrameCapturer({
    size: 240,
    onFrame: (payload) => {
      // Electron 会先发“原始帧”(带 meta)，Python 再发“处理后帧”(只包含 image)。
      // 截图拼接模式只收处理后帧，避免 pipeline 被重复应用。
      if (payload?.center || payload?.radius || payload?.bounds || payload?.display) return;

      const image = payload?.image;
      if (typeof image !== "string" || !image) return;

      capturedFrameCount.value += 1;

      if (!initRequested) {
        initRequested = true;
        lastIncrementalOp = "init";
        stitchStore.startIncrementalStitchInitByDataUrl(image, stitchSessionId, {
          skipPipeline: true,
        });
        return;
      }

      // 串行拼接：如果当前后端在处理，就只缓存“最新帧”；等本次完成再继续处理最新帧。
      pendingLatestFrame = image;

      if (baseReady && !stitchStore.isStitching) {
        const next = pendingLatestFrame;
        pendingLatestFrame = null;
        lastIncrementalOp = "step";
        stitchStore.startIncrementalStitchStepByDataUrl(next, stitchSessionId, {
          skipPipeline: true,
        });
      }
    },
  });

  try {
    await miniMapCapturer.start();
  } catch (e) {
    captureMode.value = false;
    miniMapCapturer = null;
    stitchStore.lastErrorMessage = typeof e?.message === "string" ? e.message : "截屏启动失败";
  }
};

const stopCaptureAndStitch = async () => {
  captureMode.value = false;
  shouldEndSession = true;
  pendingLatestFrame = null;
  if (miniMapCapturer) {
    try {
      await miniMapCapturer.stop();
    } catch (e) {
      // ignore
    }
  }
  miniMapCapturer = null;

  if (!stitchStore.isStitching && stitchSessionId) {
    stitchStore.endIncrementalStitchSession(stitchSessionId);
    stitchSessionId = "";
    shouldEndSession = false;
  }
};

watch(
  () => stitchStore.isStitching,
  (now, prev) => {
    // 当前拼接完成后，继续处理“最新一帧”
    if (!prev || now) return;

    if (lastIncrementalOp === "init") {
      baseReady = true;
    }

    if (shouldEndSession) {
      if (stitchSessionId) {
        stitchStore.endIncrementalStitchSession(stitchSessionId);
      }
      stitchSessionId = "";
      shouldEndSession = false;
      pendingLatestFrame = null;
      lastIncrementalOp = null;
      initRequested = false;
      baseReady = false;
      return;
    }

    if (captureMode.value && baseReady && pendingLatestFrame && !stitchStore.isStitching) {
      const next = pendingLatestFrame;
      pendingLatestFrame = null;
      lastIncrementalOp = "step";
      stitchStore.startIncrementalStitchStepByDataUrl(next, stitchSessionId, {
        skipPipeline: true,
      });
    }
  }
);

onBeforeUnmount(() => {
  // 防止页面切走后仍在截屏
  if (miniMapCapturer) miniMapCapturer.stop();
  if (stitchSessionId && !stitchStore.isStitching) {
    stitchStore.endIncrementalStitchSession(stitchSessionId);
    stitchSessionId = "";
  }
});
</script>

<style scoped lang="less">
.image-stitching-wrapper {
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

.right-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
}

.toolbar {
  display: flex;
  align-items: center;
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

.preview-title {
  font-size: 12px;
  font-weight: 600;
  color: #0f172a;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.image-list {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px;
  min-height: 200px;
  overflow: auto;
}

.image-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.image-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  background: #ffffff;
}

.image-item-meta {
  min-width: 0;
  flex: 1;
}

.image-item-name {
  font-size: 12px;
  font-weight: 500;
  color: #0f172a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.image-item-size {
  margin-top: 4px;
  font-size: 11px;
  color: #64748b;
}

.empty-tip {
  color: #94a3b8;
  font-size: 13px;
  line-height: 1.6;
  text-align: center;
  padding: 20px 0;
}

.options-card {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.option-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tip-row {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
}

.option-label {
  font-size: 12px;
  font-weight: 600;
  color: #334155;
  white-space: nowrap;
}

.spacer {
  flex: 1;
}

.actions {
  display: flex;
  justify-content: flex-start;
  margin-top: 2px;
}

.tips {
  min-height: 20px;
  font-size: 12px;
  color: #475569;
}

.progress-msg {
  color: #475569;
  word-break: break-word;
}

.err {
  margin-top: 6px;
  color: #ef4444;
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
  object-fit: contain;
  user-select: none;
}

.result-placeholder {
  color: #94a3b8;
  font-size: 13px;
  text-align: center;
  padding: 16px;
}
</style>
