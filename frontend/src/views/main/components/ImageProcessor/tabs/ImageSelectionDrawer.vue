<template>
  <transition name="config-drawer-slide">
    <div v-if="modelValue" class="config-drawer-wrapper">
      <div class="config-drawer-mask" @click="handleClose"></div>
      <div class="config-drawer">
        <div class="config-drawer-header">
          <div class="config-drawer-title-wrap">
            <div class="config-drawer-title-main">
              <span class="config-drawer-title">{{ title }}</span>
            </div>
            <div class="config-drawer-subtitle">{{ subtitle }}</div>
          </div>
          <el-button
            class="cfg-toolbar-btn cfg-toolbar-btn--outline"
            size="small"
            @click="handleClose"
          >
            关闭
          </el-button>
        </div>

        <div class="config-drawer-body">
          <div class="result-section">
            <el-image
              v-if="selectionPreviewUrl"
              :src="selectionPreviewUrl"
              :preview-src-list="[selectionPreviewUrl]"
              fit="contain"
              preview-teleported
              style="height: 100%; width: 100%"
            />
            <div v-else class="result-placeholder">
              <el-icon :size="20" style="opacity: 0.3; margin-bottom: 4px">
                <Picture />
              </el-icon>
              当前圈选图片预览
            </div>
          </div>

          <div class="font-config-section">
            <div v-if="requireName" class="font-row">
              <span class="font-label">命名</span>
              <div class="font-field">
                <el-input
                  v-model="localName"
                  placeholder="请输入图片命名"
                  size="small"
                  clearable
                />
              </div>
            </div>

            <div class="font-row">
              <span class="font-label">偏移点击区域</span>
              <div class="font-field">
                <el-input
                  v-model="clickOffsetAreaInput"
                  placeholder="偏移点击区域 x,y,w,h（可选）"
                  size="small"
                  clearable
                >
                  <template #append>
                    <el-button
                      :type="selectionEnabled ? 'warning' : 'primary'"
                      :disabled="!hasSelectionRect"
                      size="small"
                      @click="toggleSelection"
                    >
                      {{ selectionEnabled ? "取消" : "圈选" }}
                    </el-button>
                  </template>
                </el-input>
              </div>
            </div>
          </div>
        </div>

        <div class="config-drawer-footer">
          <el-button
            type="primary"
            size="small"
            @click="handleConfirm"
            :disabled="!selectionPreviewUrl"
          >
            确认添加
          </el-button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { Picture } from "@element-plus/icons-vue";

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  currentImage: {
    type: Object,
    default: null,
  },
  selectionRect: {
    type: Object,
    default: null,
  },
  title: {
    type: String,
    default: "添加图片配置",
  },
  subtitle: {
    type: String,
    default: "基于当前圈选图片添加图片配置并设置偏移点击区域",
  },
  requireName: {
    type: Boolean,
    default: false,
  },
  initialName: {
    type: String,
    default: "",
  },
  selectionType: {
    type: String,
    default: "configImageClickOffsetArea",
  },
  onConfirm: {
    type: Function,
    default: null,
  },
});

const emit = defineEmits([
  "update:modelValue",
  "start-code-generator-selection",
  "stop-code-generator-selection",
]);

const selectionPreviewUrl = ref("");
const clickOffsetAreaInput = ref("");
const selectionEnabled = ref(false);
const localName = ref("");

const hasSelectionRect = computed(() => {
  return props.selectionRect && props.selectionRect.w && props.selectionRect.h;
});

watch(
  () => props.initialName,
  (val) => {
    localName.value = String(val || "");
  },
  { immediate: true }
);

watch(
  () => props.modelValue,
  async (opened) => {
    if (opened) {
      localName.value = String(props.initialName || "");
      try {
        await rebuildSelectionPreview();
      } catch (error) {
        console.error("生成圈选预览失败:", error);
        ElMessage.error("生成圈选预览失败: " + (error.message || "未知错误"));
      }
    } else {
      selectionEnabled.value = false;
      emit("stop-code-generator-selection");
    }
  },
  { immediate: true }
);

async function rebuildSelectionPreview() {
  selectionPreviewUrl.value = "";
  if (!props.currentImage?.url) return;
  const img = new Image();
  img.crossOrigin = "anonymous";
  selectionPreviewUrl.value = await new Promise((resolve, reject) => {
    img.onload = () => {
      try {
        let startX = 0;
        let startY = 0;
        let width = img.width;
        let height = img.height;
        if (props.selectionRect?.w > 0 && props.selectionRect?.h > 0) {
          startX = Math.max(0, Math.min(props.selectionRect.x, img.width - 1));
          startY = Math.max(0, Math.min(props.selectionRect.y, img.height - 1));
          width = Math.min(props.selectionRect.w, img.width - startX);
          height = Math.min(props.selectionRect.h, img.height - startY);
        }
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        canvas.width = width;
        canvas.height = height;
        ctx.drawImage(img, startX, startY, width, height, 0, 0, width, height);
        resolve(canvas.toDataURL("image/png"));
      } catch (error) {
        reject(error);
      }
    };
    img.onerror = () => reject(new Error("加载图片失败"));
    img.src = props.currentImage.url;
  });
}

const parseClickOffsetAreaInput = () => {
  let clickOffsetArea = "0,0,0,0";
  if (clickOffsetAreaInput.value && clickOffsetAreaInput.value.trim()) {
    const raw = clickOffsetAreaInput.value.trim();
    const parts = raw.split(",").map((s) => s.trim());
    if (
      parts.length !== 4 ||
      parts.some((p) => p === "" || Number.isNaN(parseInt(p, 10)))
    ) {
      throw new Error("偏移点击区域格式不正确，应为：x,y,w,h");
    }
    const [x, y, w, h] = parts.map((p) => parseInt(p, 10));
    if (w < 0 || h < 0) {
      throw new Error("偏移点击区域宽高必须为非负整数");
    }
    clickOffsetArea = `${x},${y},${w},${h}`;
  }
  return clickOffsetArea;
};

const toggleSelection = () => {
  if (!hasSelectionRect.value) {
    ElMessage.warning("请先在左侧进行圈选，才能使用偏移点击区域功能");
    return;
  }
  if (selectionEnabled.value) {
    selectionEnabled.value = false;
    emit("stop-code-generator-selection");
    ElMessage.info("已取消圈选模式");
    return;
  }
  selectionEnabled.value = true;
  emit("start-code-generator-selection", props.selectionType);
  ElMessage.info("请在图片上圈选偏移点击区域");
};

const setClickOffsetAreaFromSelection = (rect) => {
  if (!rect || !rect.w || !rect.h) return;
  if (!props.selectionRect || !props.selectionRect.w || !props.selectionRect.h) {
    ElMessage.warning("请先在左侧进行圈选，然后再圈选偏移点击区域");
    return;
  }
  const offsetX = rect.x - props.selectionRect.x;
  const offsetY = rect.y - props.selectionRect.y;
  clickOffsetAreaInput.value = `${offsetX},${offsetY},${rect.w},${rect.h}`;
  selectionEnabled.value = false;
  emit("stop-code-generator-selection");
  ElMessage.success("已获取偏移点击区域范围（已计算偏移值）");
};

const handleClose = () => {
  selectionEnabled.value = false;
  emit("stop-code-generator-selection");
  emit("update:modelValue", false);
};

const handleConfirm = async () => {
  if (!selectionPreviewUrl.value) {
    ElMessage.warning("当前没有可添加图片");
    return;
  }
  if (props.requireName && !String(localName.value || "").trim()) {
    ElMessage.warning("请输入命名");
    return;
  }
  let clickOffsetArea = "0,0,0,0";
  try {
    clickOffsetArea = parseClickOffsetAreaInput();
  } catch (error) {
    ElMessage.warning(error.message || "偏移点击区域格式不正确");
    return;
  }
  try {
    const payload = {
      name: String(localName.value || "").trim(),
      clickOffsetArea,
      selectionRect: props.selectionRect || null,
      currentImageUrl: props.currentImage?.url || "",
      previewDataUrl: selectionPreviewUrl.value,
    };
    if (typeof props.onConfirm === "function") {
      const ok = await props.onConfirm(payload);
      if (ok === false) return;
    }
    handleClose();
  } catch (error) {
    ElMessage.error("添加图片失败: " + (error.message || "未知错误"));
  }
};

const resetForOpen = (options = {}) => {
  const resetName = options.resetName !== false;
  if (resetName) {
    localName.value = String(props.initialName || "");
  }
  clickOffsetAreaInput.value = "";
  selectionEnabled.value = false;
};

const isDrawerOpen = () => props.modelValue;

defineExpose({
  resetForOpen,
  isDrawerOpen,
  setClickOffsetAreaFromSelection,
});
</script>

<style scoped>
.config-drawer-wrapper {
  position: absolute;
  inset: 0;
  z-index: 30;
}
.config-drawer-mask {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
}
.config-drawer {
  position: absolute;
  top: 0;
  right: 0;
  width: 460px;
  height: 100%;
  background: #fff;
  box-shadow: -10px 0 30px rgba(15, 23, 42, 0.18);
  display: flex;
  flex-direction: column;
}
.config-drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px 12px;
  border-bottom: 1px solid #e2e8f0;
}
.config-drawer-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.config-drawer-title-main {
  display: flex;
  align-items: center;
  gap: 8px;
}
.config-drawer-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}
.config-drawer-subtitle {
  font-size: 12px;
  color: #64748b;
}
.config-drawer-body {
  flex: 1;
  padding: 14px 16px 10px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: auto;
}
.result-section {
  height: 220px;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  overflow: hidden;
}
.result-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 12px;
}
.font-config-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.font-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.font-label {
  width: 86px;
  flex-shrink: 0;
  color: #334155;
  font-size: 12px;
}
.font-field {
  flex: 1;
}
.config-drawer-footer {
  border-top: 1px solid #e2e8f0;
  padding: 12px 16px;
  display: flex;
  justify-content: flex-end;
}
.config-drawer-slide-enter-active,
.config-drawer-slide-leave-active {
  transition: all 0.2s ease;
}
.config-drawer-slide-enter-from,
.config-drawer-slide-leave-to {
  opacity: 0;
}
.config-drawer-slide-enter-from .config-drawer,
.config-drawer-slide-leave-to .config-drawer {
  transform: translateX(100%);
}
</style>
