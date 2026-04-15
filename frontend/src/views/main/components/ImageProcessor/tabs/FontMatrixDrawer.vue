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
          <div class="color-table-wrap">
            <el-table
              :data="selectedColors"
              height="150"
              size="small"
              empty-text="请在图片上点击选取颜色"
              :header-cell-style="{
                background: '#f8fafc',
                color: '#64748b',
                fontSize: '11px',
                fontWeight: 600,
                borderBottom: '1px solid #e2e8f0',
              }"
              :cell-style="{ fontSize: '12px', padding: '4px 0' }"
              :row-style="{ transition: 'background 0.15s' }"
            >
              <el-table-column label="HEX" width="84">
                <template #default="scope">
                  <div
                    class="hex-cell"
                    :style="{
                      backgroundColor:
                        '#' + String(scope.row.hex || '').replace(/^#/, ''),
                      color: isLightColor(scope.row.hex) ? '#1e293b' : '#f8fafc',
                    }"
                  >
                    {{ scope.row.hex }}
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="偏色" min-width="120">
                <template #default="scope">
                  <div class="slider-cell">
                    <el-slider
                      :model-value="getRowDeviation(scope.$index)"
                      :min="0"
                      :max="100"
                      :show-tooltip="true"
                      @update:model-value="(v) => setRowDeviation(scope.$index, v)"
                    />
                    <span class="slider-value">{{ getRowDeviation(scope.$index) }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="" width="40" fixed="right">
                <template #default="scope">
                  <el-button
                    type="danger"
                    link
                    size="small"
                    @click="handleRemoveColor(scope.$index)"
                    class="delete-btn"
                  >
                    <el-icon><Close /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <div class="table-footer">
              <span class="table-count">{{ selectedColors.length }} 个颜色</span>
              <el-button
                type="danger"
                size="small"
                text
                @click="handleClearAllColors"
                :disabled="!selectedColors.length"
                >清空</el-button
              >
            </div>
          </div>

          <div class="result-section">
            <el-image
              v-if="processedImageUrl"
              :src="processedImageUrl"
              :preview-src-list="[processedImageUrl]"
              fit="contain"
              preview-teleported
              style="height: 100%; width: 100%"
            />
            <div v-else class="result-placeholder">
              <el-icon :size="20" style="opacity: 0.3; margin-bottom: 4px">
                <Picture />
              </el-icon>
              偏色二值化预览
            </div>
          </div>

          <div class="font-config-section">
            <div v-if="requireName" class="font-row">
              <span class="font-label">命名</span>
              <div class="font-field">
                <el-input
                  v-model="localName"
                  placeholder="请输入字库名称"
                  size="small"
                  clearable
                />
              </div>
            </div>
            <div class="font-row">
              <span class="font-label">是否裁剪</span>
              <div class="font-field">
                <el-checkbox v-model="enableAutoCrop" size="small" />
              </div>
            </div>
            <div class="font-row">
              <span class="font-label">偏移点击区域</span>
              <div class="font-field">
                <el-input
                  v-model="fontClickOffsetAreaInput"
                  placeholder="偏移点击区域 x,y,w,h（可选）"
                  size="small"
                  clearable
                >
                  <template #append>
                    <el-button
                      :type="isFontClickOffsetAreaSelectionActive ? 'warning' : 'primary'"
                      :disabled="!hasSelectionRect"
                      size="small"
                      @click="toggleFontClickOffsetAreaSelection"
                    >
                      {{ isFontClickOffsetAreaSelectionActive ? "取消" : "圈选" }}
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
            :disabled="!processedImageUrl"
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
import { Close, Picture } from "@element-plus/icons-vue";

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
    default: "添加字库配置",
  },
  subtitle: {
    type: String,
    default: "基于当前图片与圈选区域生成字库点阵配置",
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
    default: "configFontClickOffsetArea",
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

const selectedColors = ref([]);
const rowDeviations = ref([]);
const processedImageUrl = ref(null);
const enableAutoCrop = ref(true);
const fontClickOffsetAreaInput = ref("");
const fontClickOffsetAreaSelectionEnabled = ref(false);
const localName = ref("");

watch(
  () => props.initialName,
  (val) => {
    localName.value = String(val || "");
  },
  { immediate: true }
);

watch(
  () => props.modelValue,
  (opened) => {
    if (opened) {
      localName.value = String(props.initialName || "");
    } else {
      fontClickOffsetAreaSelectionEnabled.value = false;
      emit("stop-code-generator-selection");
    }
  }
);

const hasSelectionRect = computed(() => {
  return props.selectionRect && props.selectionRect.w && props.selectionRect.h;
});

const isFontClickOffsetAreaSelectionActive = computed(() => {
  return fontClickOffsetAreaSelectionEnabled.value;
});

const handleClose = () => {
  fontClickOffsetAreaSelectionEnabled.value = false;
  emit("stop-code-generator-selection");
  emit("update:modelValue", false);
};

const parseClickOffsetAreaInput = () => {
  let clickOffsetArea = "0,0,0,0";
  if (fontClickOffsetAreaInput.value && fontClickOffsetAreaInput.value.trim()) {
    const raw = fontClickOffsetAreaInput.value.trim();
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

const toggleFontClickOffsetAreaSelection = () => {
  if (!hasSelectionRect.value) {
    ElMessage.warning("请先在左侧进行圈选，才能使用偏移点击区域功能");
    return;
  }
  if (fontClickOffsetAreaSelectionEnabled.value) {
    fontClickOffsetAreaSelectionEnabled.value = false;
    emit("stop-code-generator-selection");
    ElMessage.info("已取消圈选模式");
    return;
  }
  fontClickOffsetAreaSelectionEnabled.value = true;
  emit("start-code-generator-selection", props.selectionType);
  ElMessage.info("请在图片上圈选偏移点击区域");
};

const getRowDeviation = (index) => rowDeviations.value[index] ?? 0;

const setRowDeviation = (index, value) => {
  const arr = [...rowDeviations.value];
  arr[index] = Math.max(0, Math.min(100, value));
  rowDeviations.value = arr;
  runBinarizationFromTable();
};

const isLightColor = (hex) => {
  hex = String(hex || "").replace("#", "");
  if (hex.length === 3) {
    hex = hex
      .split("")
      .map((c) => c + c)
      .join("");
  }
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > 186;
};

const hexToRgb = (hex) => {
  const normalized = String(hex || "").replace("#", "");
  const fullHex =
    normalized.length === 3
      ? normalized
          .split("")
          .map((c) => c + c)
          .join("")
      : normalized;
  return {
    r: parseInt(fullHex.substring(0, 2), 16),
    g: parseInt(fullHex.substring(2, 4), 16),
    b: parseInt(fullHex.substring(4, 6), 16),
  };
};

const numToHex = (num) => {
  const hex = Math.max(0, Math.min(255, Math.floor(num)))
    .toString(16)
    .toUpperCase();
  return hex.length === 1 ? "0" + hex : hex;
};

const parseDeviation = (deviationStr) => {
  const [baseHex, deviationHex] = String(deviationStr || "").split("-");
  if (!baseHex || !deviationHex || baseHex.length !== 6 || deviationHex.length !== 6) {
    return null;
  }
  return {
    base: {
      r: parseInt(baseHex.substring(0, 2), 16),
      g: parseInt(baseHex.substring(2, 4), 16),
      b: parseInt(baseHex.substring(4, 6), 16),
    },
    deviation: {
      r: parseInt(deviationHex.substring(0, 2), 16),
      g: parseInt(deviationHex.substring(2, 4), 16),
      b: parseInt(deviationHex.substring(4, 6), 16),
    },
  };
};

const isColorInDeviationRange = (r, g, b, deviationData) => {
  const { base, deviation } = deviationData;
  return (
    r >= Math.max(0, base.r - deviation.r) &&
    r <= Math.min(255, base.r + deviation.r) &&
    g >= Math.max(0, base.g - deviation.g) &&
    g <= Math.min(255, base.g + deviation.g) &&
    b >= Math.max(0, base.b - deviation.b) &&
    b <= Math.min(255, base.b + deviation.b)
  );
};

const buildDeviationListFromTable = () => {
  const list = [];
  for (let i = 0; i < selectedColors.value.length; i++) {
    const d = rowDeviations.value[i] ?? 0;
    const baseRgb = hexToRgb(selectedColors.value[i].hex);
    const baseHex = numToHex(baseRgb.r) + numToHex(baseRgb.g) + numToHex(baseRgb.b);
    const deviationHex = numToHex(d) + numToHex(d) + numToHex(d);
    list.push(`${baseHex}-${deviationHex}`);
  }
  return list;
};

const runBinarizationFromTable = () => {
  if (!props.currentImage?.url) return;
  const deviationList = buildDeviationListFromTable();
  if (!deviationList.length) return;
  const deviationDataList = deviationList.map(parseDeviation).filter(Boolean);
  if (!deviationDataList.length) return;

  const img = new Image();
  img.crossOrigin = "anonymous";
  img.onload = () => {
    try {
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
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
      canvas.width = width;
      canvas.height = height;
      ctx.drawImage(img, startX, startY, width, height, 0, 0, width, height);
      const imageData = ctx.getImageData(0, 0, width, height);
      const pixelData = imageData.data;
      for (let i = 0; i < pixelData.length; i += 4) {
        const r = pixelData[i];
        const g = pixelData[i + 1];
        const b = pixelData[i + 2];
        let inRange = false;
        for (const dd of deviationDataList) {
          if (isColorInDeviationRange(r, g, b, dd)) {
            inRange = true;
            break;
          }
        }
        pixelData[i] = pixelData[i + 1] = pixelData[i + 2] = inRange ? 255 : 0;
        pixelData[i + 3] = 255;
      }
      ctx.putImageData(imageData, 0, 0);
      processedImageUrl.value = canvas.toDataURL("image/png");
    } catch (error) {
      console.error("二值化出错:", error);
    }
  };
  img.src = props.currentImage.url;
};

const handleRemoveColor = (index) => {
  selectedColors.value.splice(index, 1);
  rowDeviations.value.splice(index, 1);
  if (selectedColors.value.length > 0 && props.currentImage?.url) {
    runBinarizationFromTable();
  } else {
    processedImageUrl.value = null;
  }
};

const handleClearAllColors = () => {
  selectedColors.value = [];
  rowDeviations.value = [];
  processedImageUrl.value = null;
  ElMessage.success("已清空全部颜色");
};

const buildFontResult = async () => {
  const img = new Image();
  img.crossOrigin = "anonymous";

  return await new Promise((resolve, reject) => {
    img.onload = async () => {
      try {
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        const imageData = ctx.getImageData(0, 0, img.width, img.height);
        const pixelData = imageData.data;

        let minX = img.width;
        let minY = img.height;
        let maxX = 0;
        let maxY = 0;
        let whitePixelCount = 0;

        for (let y = 0; y < img.height; y++) {
          for (let x = 0; x < img.width; x++) {
            const idx = (y * img.width + x) * 4;
            if (
              pixelData[idx] > 200 &&
              pixelData[idx + 1] > 200 &&
              pixelData[idx + 2] > 200
            ) {
              whitePixelCount++;
              minX = Math.min(minX, x);
              minY = Math.min(minY, y);
              maxX = Math.max(maxX, x);
              maxY = Math.max(maxY, y);
            }
          }
        }

        if (whitePixelCount === 0) {
          reject(new Error("二值化图片中没有白色像素"));
          return;
        }

        let cropMinX;
        let cropMinY;
        let cropMaxX;
        let cropMaxY;
        if (enableAutoCrop.value) {
          cropMinX = minX;
          cropMinY = minY;
          cropMaxX = maxX;
          cropMaxY = maxY;
        } else {
          cropMinX = 0;
          cropMinY = 0;
          cropMaxX = img.width - 1;
          cropMaxY = img.height - 1;
        }

        const width = cropMaxX - cropMinX + 1;
        const height = cropMaxY - cropMinY + 1;
        const binaryData = [];

        for (let y = cropMinY; y <= cropMaxY; y++) {
          for (let x = cropMinX; x <= cropMaxX; x++) {
            const idx = (y * img.width + x) * 4;
            const isWhite =
              pixelData[idx] > 200 && pixelData[idx + 1] > 200 && pixelData[idx + 2] > 200;
            binaryData.push(isWhite ? "1" : "0");
          }
        }

        let matrixHex = "";
        for (let i = 0; i < binaryData.length; i += 4) {
          const bits = binaryData.slice(i, i + 4).join("");
          matrixHex += parseInt(bits.padEnd(4, "0"), 2).toString(16).toUpperCase();
        }

        const clickOffsetArea = parseClickOffsetAreaInput();
        const deviation = buildDeviationListFromTable().join("|");
        const name = String(localName.value || "").trim();

        resolve({
          id: Date.now(),
          matrix: matrixHex,
          width,
          height,
          totalCount: whitePixelCount,
          sizeInfo: `${width}×${height} (${whitePixelCount})`,
          deviation,
          clickOffsetArea,
          binaryData,
          name,
          editing: false,
        });
      } catch (error) {
        reject(error);
      }
    };
    img.onerror = () => reject(new Error("加载图片失败"));
    img.src = processedImageUrl.value;
  });
};

const handleConfirm = async () => {
  if (!processedImageUrl.value) {
    ElMessage.warning("请先生成点阵");
    return;
  }
  if (!buildDeviationListFromTable().length) {
    ElMessage.warning("请先添加颜色");
    return;
  }
  if (props.requireName && !String(localName.value || "").trim()) {
    ElMessage.warning("请输入命名");
    return;
  }
  try {
    const fontResult = await buildFontResult();
    if (typeof props.onConfirm === "function") {
      const result = await props.onConfirm(fontResult);
      if (result === false) return;
    }
    handleClose();
  } catch (error) {
    ElMessage.error("添加配置失败: " + (error.message || "未知错误"));
  }
};

const addColor = (colorInfo) => {
  if (!colorInfo || !colorInfo.hex) return;
  const hex = String(colorInfo.hex).replace(/^#/, "").toUpperCase();
  if (selectedColors.value.some((item) => item.hex === hex)) {
    ElMessage.warning("已存在相同颜色");
    return;
  }
  selectedColors.value.push({ hex });
  rowDeviations.value.push(0);
  if (props.currentImage?.url) runBinarizationFromTable();
};

const setFontClickOffsetAreaFromSelection = (rect) => {
  if (!rect || !rect.w || !rect.h) return;
  if (!props.selectionRect || !props.selectionRect.w || !props.selectionRect.h) {
    ElMessage.warning("请先在左侧进行圈选，然后再圈选偏移点击区域");
    return;
  }
  const offsetX = rect.x - props.selectionRect.x;
  const offsetY = rect.y - props.selectionRect.y;
  fontClickOffsetAreaInput.value = `${offsetX},${offsetY},${rect.w},${rect.h}`;
  fontClickOffsetAreaSelectionEnabled.value = false;
  emit("stop-code-generator-selection");
  ElMessage.success("已获取偏移点击区域范围（已计算偏移值）");
};

const resetForOpen = (options = {}) => {
  const keepColors = options.keepColors !== false;
  const resetName = options.resetName !== false;
  enableAutoCrop.value = true;
  fontClickOffsetAreaInput.value = "";
  fontClickOffsetAreaSelectionEnabled.value = false;
  if (!keepColors) {
    selectedColors.value = [];
    rowDeviations.value = [];
    processedImageUrl.value = null;
  }
  if (resetName) {
    localName.value = String(props.initialName || "");
  }
};

const isDrawerOpen = () => props.modelValue;

defineExpose({
  addColor,
  isDrawerOpen,
  resetForOpen,
  setFontClickOffsetAreaFromSelection,
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
.color-table-wrap {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}
.hex-cell {
  width: 58px;
  height: 22px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
}
.slider-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.slider-value {
  width: 24px;
  font-size: 12px;
  color: #475569;
}
.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  border-top: 1px solid #e2e8f0;
}
.table-count {
  color: #64748b;
  font-size: 12px;
}
.result-section {
  height: 180px;
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
