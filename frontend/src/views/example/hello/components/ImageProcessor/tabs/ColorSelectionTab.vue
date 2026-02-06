<template>
  <div class="color-selection-container">
    <!-- 颜色表格 -->
    <div class="color-table-wrap">
      <el-table
        :data="tableRows"
        height="195"
        size="small"
        empty-text="点击图片选取颜色"
        :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontSize: '11px', fontWeight: 600, borderBottom: '1px solid #e2e8f0' }"
        :cell-style="{ fontSize: '12px', padding: '4px 0' }"
        :row-style="{ transition: 'background 0.15s' }"
      >
        <el-table-column label="HEX" width="84">
          <template #default="scope">
            <div class="hex-cell" :style="{
              backgroundColor: '#' + String(scope.row.hex || '').replace(/^#/, ''),
              color: isLightColor(scope.row.hex) ? '#1e293b' : '#f8fafc',
            }">
              {{ scope.row.hex }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="偏色" min-width="130">
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
        <el-table-column label="" width="44" fixed="right">
          <template #default="scope">
            <el-button type="danger" link size="small" @click="$emit('remove-color', scope.$index)" class="delete-btn">
              <el-icon><Close /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-footer">
        <span class="table-count">{{ tableRows.length }} 个颜色</span>
        <el-button type="danger" size="small" text @click="handleClearAllColors" :disabled="!tableRows.length">清空</el-button>
      </div>
    </div>

    <!-- 结果预览区域 -->
    <div class="result-section">
      <el-image :src="processedImageUrl" :preview-src-list="[processedImageUrl]" fit="contain" preview-teleported
        style="height: 100%; width: 100%;">
        <template #placeholder>
          <div class="result-placeholder">
            <el-icon :size="20" style="opacity: 0.3; margin-bottom: 4px;"><Picture /></el-icon>
            偏色二值化预览
          </div>
        </template>
      </el-image>
    </div>

    <!-- 字库操作区 -->
    <div class="font-library-section">
      <div class="font-row">
        <el-input
          v-model="fontClickOffsetAreaInput"
          placeholder="偏移点击区域 x,y,w,h（可选）"
          size="small"
          clearable
        >
          <template #append>
            <el-button
              :type="fontClickOffsetAreaSelectionEnabled ? 'warning' : 'primary'"
              :disabled="!hasSelectionRect"
              size="small"
              @click="toggleFontClickOffsetAreaSelection"
            >
              {{ fontClickOffsetAreaSelectionEnabled ? '取消' : '圈选' }}
            </el-button>
          </template>
        </el-input>
      </div>
      <div class="font-row">
        <el-input
          v-model="fontNameInput"
          placeholder="字库名称"
          size="small"
          clearable
        />
        <el-button
          type="success"
          size="small"
          @click="handleAddFontLibrary"
          :disabled="!fontNameInput || !processedImageUrl || !tableRows.length || !hasFontLibraryFile"
          class="add-font-btn"
        >
          加入字库
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { ElMessage } from "element-plus";
import { Close, Picture } from "@element-plus/icons-vue";

const props = defineProps({
  currentSelectedColors: {
    type: Array,
    default: () => [],
  },
  currentImage: {
    type: Object,
    default: null,
  },
  selectionRect: {
    type: Object,
    default: null,
  },
  hasFontLibraryFile: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits([
  "remove-color",
  "clear-all-colors",
  "add-colors",
  "add-font-library",
  "start-code-generator-selection",
  "stop-code-generator-selection",
]);

// 每行偏色值 0–100，与 currentSelectedColors 按索引对应
const rowDeviations = ref([]);

const processedImageUrl = ref(null);
const lastRenderedImageUrl = ref(null);
const fontClickOffsetAreaInput = ref("");
const fontNameInput = ref("");

// 表格数据 = 当前选中颜色
const tableRows = computed(() => props.currentSelectedColors || []);

// 同步行数与偏色数组长度
watch(
  () => props.currentSelectedColors?.length ?? 0,
  (len, oldLen) => {
    const arr = [...rowDeviations.value];
    while (arr.length < len) arr.push(0);
    if (arr.length > len) arr.splice(len);
    rowDeviations.value = arr;
    if (len > 0 && props.currentImage?.url) runBinarizationFromTable();
  },
  { immediate: true }
);

const getRowDeviation = (index) => rowDeviations.value[index] ?? 0;
const setRowDeviation = (index, value) => {
  const arr = [...rowDeviations.value];
  arr[index] = Math.max(0, Math.min(100, value));
  rowDeviations.value = arr;
  runBinarizationFromTable();
};

const isLightColor = (hex) => {
  hex = String(hex).replace("#", "");
  if (hex.length === 3) hex = hex.split("").map((c) => c + c).join("");
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return luminance > 186;
};

const handleClearAllColors = () => {
  rowDeviations.value = [];
  processedImageUrl.value = null;
  lastRenderedImageUrl.value = null;
  emit("clear-all-colors");
  ElMessage.success("已清空全部");
};

// 偏移点击区域圈选状态
const fontClickOffsetAreaSelectionEnabled = ref(false);

// 是否存在左侧圈选范围（用于偏移点击区域的基准）
const hasSelectionRect = computed(() => {
  return props.selectionRect && props.selectionRect.w && props.selectionRect.h;
});

// 切换偏移点击区域圈选模式（交互风格与 CodeGeneratorTab 保持一致）
const toggleFontClickOffsetAreaSelection = () => {
  if (!hasSelectionRect.value) {
    ElMessage.warning("请先在左侧进行圈选，才能使用偏移点击区域功能");
    return;
  }

  if (fontClickOffsetAreaSelectionEnabled.value) {
    fontClickOffsetAreaSelectionEnabled.value = false;
    emit("stop-code-generator-selection");
    ElMessage.info("已取消圈选模式");
  } else {
    fontClickOffsetAreaSelectionEnabled.value = true;
    // 使用专门的类型标识，方便上层区分来源
    emit("start-code-generator-selection", "fontClickOffsetArea");
    ElMessage.info("请在图片上圈选偏移点击区域");
  }
};

// HEX 转 RGB
const hexToRgb = (hex) => {;
  hex = hex.replace("#", "");
  if (hex.length === 3) {
    hex = hex
      .split("")
      .map((char) => char + char)
      .join("");
  }
  return {
    r: parseInt(hex.substring(0, 2), 16),
    g: parseInt(hex.substring(2, 4), 16),
    b: parseInt(hex.substring(4, 6), 16),
  };
};

// 数字转 HEX（两位，大写）
const numToHex = (num) => {
  const hex = Math.max(0, Math.min(255, Math.floor(num)))
    .toString(16)
    .toUpperCase();
  return hex.length === 1 ? "0" + hex : hex;
};

// 从表格行构建偏色字符串列表（每行 hex + 偏色 0–100 → baseHex-deviationHex）
const buildDeviationListFromTable = () => {
  const colors = props.currentSelectedColors || [];
  const list = [];
  for (let i = 0; i < colors.length; i++) {
    const d = rowDeviations.value[i] ?? 0;
    const baseRgb = hexToRgb(colors[i].hex);
    const baseHex = numToHex(baseRgb.r) + numToHex(baseRgb.g) + numToHex(baseRgb.b);
    const deviationHex = numToHex(d) + numToHex(d) + numToHex(d);
    list.push(`${baseHex}-${deviationHex}`);
  }
  return list;
};

// 根据表格中的 hex+偏色 做二值化并更新 processedImageUrl
const runBinarizationFromTable = () => {
  if (!props.currentImage?.url) return;
  const deviationList = buildDeviationListFromTable();
  if (deviationList.length === 0) return;

  const deviationDataList = deviationList
    .map((dev) => parseDeviation(dev))
    .filter((data) => data !== null);
  if (deviationDataList.length === 0) return;

  const img = new Image();
  img.crossOrigin = "anonymous";
  img.onload = () => {
    try {
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      let startX = 0, startY = 0, width = img.width, height = img.height;
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
      const data = imageData.data;

      for (let i = 0; i < data.length; i += 4) {
        const r = data[i], g = data[i + 1], b = data[i + 2];
        let inRange = false;
        for (const deviationData of deviationDataList) {
          if (isColorInDeviationRange(r, g, b, deviationData)) {
            inRange = true;
            break;
          }
        }
        if (inRange) {
          data[i] = data[i + 1] = data[i + 2] = 255;
          data[i + 3] = 255;
        } else {
          data[i] = data[i + 1] = data[i + 2] = 0;
          data[i + 3] = 255;
        }
      }
      ctx.putImageData(imageData, 0, 0);
      processedImageUrl.value = canvas.toDataURL("image/png");
      lastRenderedImageUrl.value = processedImageUrl.value;
    } catch (e) {
      console.error("二值化出错:", e);
    }
  };
  img.onerror = () => console.error("加载图片失败");
  img.src = props.currentImage.url;
};

// 解析偏色字符串（如 "D7CCC6-0E0E09"）
const parseDeviation = (deviationStr) => {
  const [baseHex, deviationHex] = deviationStr.split("-");
  if (!baseHex || !deviationHex || baseHex.length !== 6 || deviationHex.length !== 6) {
    return null;
  }

  const baseR = parseInt(baseHex.substring(0, 2), 16);
  const baseG = parseInt(baseHex.substring(2, 4), 16);
  const baseB = parseInt(baseHex.substring(4, 6), 16);

  const deviationR = parseInt(deviationHex.substring(0, 2), 16);
  const deviationG = parseInt(deviationHex.substring(2, 4), 16);
  const deviationB = parseInt(deviationHex.substring(4, 6), 16);

  return {
    base: { r: baseR, g: baseG, b: baseB },
    deviation: { r: deviationR, g: deviationG, b: deviationB },
  };
};

// 检查颜色是否在偏色范围内
const isColorInDeviationRange = (r, g, b, deviationData) => {
  const { base, deviation } = deviationData;

  // 计算每个通道的范围
  const minR = Math.max(0, base.r - deviation.r);
  const maxR = Math.min(255, base.r + deviation.r);
  const minG = Math.max(0, base.g - deviation.g);
  const maxG = Math.min(255, base.g + deviation.g);
  const minB = Math.max(0, base.b - deviation.b);
  const maxB = Math.min(255, base.b + deviation.b);

  // 检查颜色是否在所有通道的范围内
  return r >= minR && r <= maxR && g >= minG && g <= maxG && b >= minB && b <= maxB;
};

// 供外部调用的重新渲染（与表格二值化一致）
const handleRerender = () => runBinarizationFromTable();

// 通过圈选结果设置偏移点击区域（由父组件调用）
const setFontClickOffsetAreaFromSelection = (rect) => {
  if (!rect || !rect.w || !rect.h) {
    return;
  }

  // 偏移点击区域需要基于左侧圈选范围计算偏移值
  if (!props.selectionRect || !props.selectionRect.w || !props.selectionRect.h) {
    ElMessage.warning("请先在左侧进行圈选，然后再圈选偏移点击区域");
    // 不取消圈选模式，让用户可以继续操作
    return;
  }

  // 计算偏移值：偏移点击区域的坐标 - 左侧圈选范围的坐标
  const offsetX = rect.x - props.selectionRect.x;
  const offsetY = rect.y - props.selectionRect.y;
  const areaStr = `${offsetX},${offsetY},${rect.w},${rect.h}`;
  fontClickOffsetAreaInput.value = areaStr;
  ElMessage.success("已获取偏移点击区域范围（已计算偏移值）");

  // 自动取消圈选模式
  fontClickOffsetAreaSelectionEnabled.value = false;
  emit("stop-code-generator-selection");
};

// 处理加入字库
const handleAddFontLibrary = async () => {
  if (!processedImageUrl.value) {
    ElMessage.warning("请先生成二值化图片");
    return;
  }

  const selectedDeviationsList = buildDeviationListFromTable();
  if (!selectedDeviationsList.length) {
    ElMessage.warning("请先选取颜色并设置偏色");
    return;
  }

  if (!fontNameInput.value || !fontNameInput.value.trim()) {
    ElMessage.warning("请输入字库名字");
    return;
  }

  // 处理偏移点击区域，格式为 x,y,w,h，若未填写则默认 0,0,0,0
  let clickOffsetArea = "0,0,0,0";
  if (fontClickOffsetAreaInput.value && fontClickOffsetAreaInput.value.trim()) {
    const raw = fontClickOffsetAreaInput.value.trim();
    const parts = raw.split(",").map((s) => s.trim());
    if (parts.length !== 4 || parts.some((p) => p === "" || isNaN(parseInt(p, 10)))) {
      ElMessage.warning("偏移点击区域格式不正确，应为：x,y,w,h");
      return;
    }
    const [x, y, w, h] = parts.map((p) => parseInt(p, 10));
    if (w < 0 || h < 0) {
      ElMessage.warning("偏移点击区域宽高必须为非负整数");
      return;
    }
    clickOffsetArea = `${x},${y},${w},${h}`;
  }

  try {
    // 加载图片并处理
    const img = new Image();
    img.crossOrigin = "anonymous";
    
    await new Promise((resolve, reject) => {
      img.onload = async () => {
        try {
          // 创建 canvas 用于处理
          const canvas = document.createElement("canvas");
          const ctx = canvas.getContext("2d");
          canvas.width = img.width;
          canvas.height = img.height;
          ctx.drawImage(img, 0, 0);

          // 获取像素数据
          const imageData = ctx.getImageData(0, 0, img.width, img.height);
          const data = imageData.data;

          // 找到最小边界框（只包含白色像素的区域）
          let minX = img.width, minY = img.height, maxX = 0, maxY = 0;
          let whitePixelCount = 0;

          for (let y = 0; y < img.height; y++) {
            for (let x = 0; x < img.width; x++) {
              const idx = (y * img.width + x) * 4;
              const r = data[idx];
              const g = data[idx + 1];
              const b = data[idx + 2];
              
              // 判断是否为白色（RGB都接近255）
              if (r > 200 && g > 200 && b > 200) {
                whitePixelCount++;
                minX = Math.min(minX, x);
                minY = Math.min(minY, y);
                maxX = Math.max(maxX, x);
                maxY = Math.max(maxY, y);
              }
            }
          }

          // 如果没有白色像素，提示错误
          if (whitePixelCount === 0) {
            ElMessage.warning("二值化图片中没有白色像素");
            reject(new Error("没有白色像素"));
            return;
          }

          // 计算最小宽高
          const width = maxX - minX + 1;
          const height = maxY - minY + 1;

          // 提取最小区域的像素数据
          const binaryData = [];
          for (let y = minY; y <= maxY; y++) {
            for (let x = minX; x <= maxX; x++) {
              const idx = (y * img.width + x) * 4;
              const r = data[idx];
              const g = data[idx + 1];
              const b = data[idx + 2];
              
              // 白色记为1，黑色记为0
              const isWhite = r > 200 && g > 200 && b > 200;
              binaryData.push(isWhite ? '1' : '0');
            }
          }

          // 转换为16进制点阵字符串
          let matrixHex = '';
          for (let i = 0; i < binaryData.length; i += 4) {
            const bits = binaryData.slice(i, i + 4).join('');
            // 如果不足4位，后面补0
            const paddedBits = bits.padEnd(4, '0');
            const hexChar = parseInt(paddedBits, 2).toString(16).toUpperCase();
            matrixHex += hexChar;
          }

          // 偏色信息，多个之间以|连接
          const deviationStr = selectedDeviationsList.join('|');

          // 创建字库项
          const fontItem = {
            id: Date.now(),
            matrix: matrixHex,
            width: width,
            height: height,
            totalCount: whitePixelCount,
            sizeInfo: `${width}×${height} (${whitePixelCount})`,
            deviation: deviationStr,
            name: fontNameInput.value.trim(),
            clickOffsetArea,
            editing: false,
            binaryData: binaryData // 保存二进制数据用于显示
          };

          // 通过事件传递给父组件，由 FontLibraryTab 处理
          // 传递一个 Promise，让父组件可以返回结果
          const addPromise = new Promise((resolveAdd) => {
            emit("add-font-library", fontItem, resolveAdd);
          });

          // 等待父组件的处理结果
          const success = await addPromise;
          
          // 只有在成功时才清空输入框
          if (success) {
            fontClickOffsetAreaInput.value = "";
            fontNameInput.value = "";
          } else {
            // 如果失败，不显示任何消息（错误消息已在 FontLibraryTab 中显示）
            // 不清空输入框，让用户可以修改后重试
          }

          resolve();
        } catch (error) {
          console.error("处理字库时出错:", error);
          reject(error);
        }
      };

      img.onerror = () => {
        ElMessage.error("加载图片失败");
        reject(new Error("加载图片失败"));
      };

      img.src = processedImageUrl.value;
    });
  } catch (error) {
    console.error("加入字库失败:", error);
    ElMessage.error("加入字库失败: " + (error.message || "未知错误"));
  }
};

// 暴露选中的偏色列表（由表格 hex+偏色 构建）和处理后的图片URL，供父组件使用
defineExpose({
  getSelectedDeviations: () => buildDeviationListFromTable(),
  getProcessedImageUrl: () => processedImageUrl.value,
  setFontClickOffsetAreaFromSelection,
});
</script>

<style scoped>
.color-selection-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 0;
}

.color-table-wrap {
  flex-shrink: 0;
}

/* 去除表格外边框 */
.color-table-wrap :deep(.el-table) {
  --el-table-border-color: #e8ecf1;
}

.color-table-wrap :deep(.el-table td.el-table__cell),
.color-table-wrap :deep(.el-table th.el-table__cell) {
  border-right: none;
}

.color-table-wrap :deep(.el-table--border::after),
.color-table-wrap :deep(.el-table--border::before) {
  display: none;
}

.color-table-wrap :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.table-footer {
  padding: 3px 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
  background: #fafbfc;
}

.table-count {
  font-size: 10px;
  color: #94a3b8;
  font-weight: 500;
}

.hex-cell {
  padding: 2px 6px;
  border-radius: 4px;
  font-family: "JetBrains Mono", "Cascadia Code", "Courier New", monospace;
  font-size: 11px;
  font-weight: 600;
  text-align: center;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.slider-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 12px;
}

.slider-cell :deep(.el-slider) {
  flex: 1;
}

.slider-value {
  font-family: "JetBrains Mono", "Cascadia Code", "Courier New", monospace;
  font-size: 10px;
  color: #94a3b8;
  min-width: 20px;
  text-align: right;
}

.delete-btn {
  padding: 2px !important;
}

.result-section {
  margin-top: 4px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 8px;
  background: #0f172a;
  background-image:
    linear-gradient(45deg, #1e293b 25%, transparent 25%),
    linear-gradient(-45deg, #1e293b 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #1e293b 75%),
    linear-gradient(-45deg, transparent 75%, #1e293b 75%);
  background-size: 12px 12px;
  background-position: 0 0, 0 6px, 6px -6px, -6px 0px;
}

.result-placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  width: 100%;
  color: #475569;
  font-size: 11px;
  letter-spacing: 0.3px;
}

.font-library-section {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 2px 4px;
  border-top: 1px solid #e2e8f0;
}

.font-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.add-font-btn {
  flex-shrink: 0;
}
</style>