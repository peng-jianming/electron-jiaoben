<template>
  <div class="config-tab-container">
    <vue-json-pretty deep="1" :data="data">
      <template #renderNodeValue="{ node, defaultValue }">
        <span v-if="node.key === '点阵'">点阵信息过长不展示</span>
        <span v-else>{{ defaultValue }}</span>
      </template>
      <template #renderNodeActions="{ node, defaultActions }">
        <el-button
          v-if="node.type == 'objectStart' && node.level <= 2"
          type="primary"
          size="small"
          @click="handleAddConfig(node)"
          >添加</el-button
        >
      </template>
    </vue-json-pretty>
    <transition name="config-drawer-slide">
      <div v-if="drawer" class="config-drawer">
        <div class="config-drawer-header">
          <span class="config-drawer-title">添加配置</span>
          <el-button link type="primary" size="small" @click="drawer = false">
            关闭
          </el-button>
        </div>
        <div class="config-drawer-body">
          <!-- 颜色表格 -->
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
            >
              <el-table-column label="HEX" width="84">
                <template #default="scope">
                  <div
                    class="hex-cell"
                    :style="{
                      backgroundColor:
                        '#' +
                        String(scope.row.hex || '').replace(/^#/, ''),
                      color: isLightColor(scope.row.hex)
                        ? '#1e293b'
                        : '#f8fafc',
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
                      @update:model-value="
                        (v) => setRowDeviation(scope.$index, v)
                      "
                    />
                    <span class="slider-value">{{
                      getRowDeviation(scope.$index)
                    }}</span>
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
              <span class="table-count"
                >{{ selectedColors.length }} 个颜色</span
              >
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

          <!-- 二值化预览 -->
          <div class="result-section">
            <el-image
              v-if="processedImageUrl"
              :src="processedImageUrl"
              :preview-src-list="[processedImageUrl]"
              fit="contain"
              preview-teleported
              style="height: 100%; width: 100%"
            />
            <div v-else class="result-placeholder">偏色二值化预览</div>
          </div>

          <!-- 偏移点击区域、字库名称和裁剪选项 -->
          <div class="font-config-section">
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
                placeholder="字库名称（作为添加的 key）"
                size="small"
                clearable
              />
            </div>
            <div class="font-row">
              <el-checkbox
                v-model="enableAutoCrop"
                size="small"
                label="是否裁剪"
                border
              />
            </div>
          </div>
        </div>
        <div class="config-drawer-footer">
          <el-button
            type="primary"
            size="small"
            @click="handleConfirmAddConfig"
            :disabled="!fontNameInput || !processedImageUrl"
          >
            确认添加
          </el-button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import VueJsonPretty from "vue-json-pretty";
import "vue-json-pretty/lib/styles.css";
import { ref, computed } from "vue";
import { ElMessage } from "element-plus";
import { Close } from "@element-plus/icons-vue";

const props = defineProps({
  currentImage: {
    type: Object,
    default: null,
  },
  selectionRect: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits([
  "start-code-generator-selection",
  "stop-code-generator-selection",
]);

const drawer = ref(false);
const currentNode = ref(null);

// ========== 独立的颜色管理 ==========
const selectedColors = ref([]); // 自己维护的颜色列表 [{ hex: 'D61E24' }, ...]
const rowDeviations = ref([]); // 每行偏色值 0–100

const processedImageUrl = ref(null);
const enableAutoCrop = ref(true);
const fontClickOffsetAreaInput = ref("");
const fontNameInput = ref("");

// ========== 偏移点击区域圈选 ==========
const fontClickOffsetAreaSelectionEnabled = ref(false);

// 是否存在左侧圈选范围（用于偏移点击区域的基准）
const hasSelectionRect = computed(() => {
  return props.selectionRect && props.selectionRect.w && props.selectionRect.h;
});

// 切换偏移点击区域圈选模式
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
    emit("start-code-generator-selection", "configFontClickOffsetArea");
    ElMessage.info("请在图片上圈选偏移点击区域");
  }
};

// 通过圈选结果设置偏移点击区域（由父组件调用）
const setFontClickOffsetAreaFromSelection = (rect) => {
  if (!rect || !rect.w || !rect.h) {
    return;
  }

  // 偏移点击区域需要基于左侧圈选范围计算偏移值
  if (!props.selectionRect || !props.selectionRect.w || !props.selectionRect.h) {
    ElMessage.warning("请先在左侧进行圈选，然后再圈选偏移点击区域");
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

// 供外部（图片点击）调用的添加颜色方法
const addColor = (colorInfo) => {
  if (!colorInfo || !colorInfo.hex) return;
  const hex = colorInfo.hex.replace(/^#/, "").toUpperCase();
  // 检查是否已存在相同颜色
  if (selectedColors.value.some((c) => c.hex === hex)) {
    ElMessage.warning("已存在相同颜色");
    return;
  }
  selectedColors.value.push({ hex });
  rowDeviations.value.push(0);
  // 重新计算二值化
  if (props.currentImage?.url) runBinarizationFromTable();
};

// 删除颜色
const handleRemoveColor = (index) => {
  selectedColors.value.splice(index, 1);
  rowDeviations.value.splice(index, 1);
  if (selectedColors.value.length > 0 && props.currentImage?.url) {
    runBinarizationFromTable();
  } else {
    processedImageUrl.value = null;
  }
};

// 清空所有颜色
const handleClearAllColors = () => {
  selectedColors.value = [];
  rowDeviations.value = [];
  processedImageUrl.value = null;
  ElMessage.success("已清空全部颜色");
};

// ========== 节点操作 ==========
const handleAddConfig = (node) => {
  if (node.level == 0) {
    currentNode.value = data.value;
  }
  if (node.level == 2) {
    const match = node.path.match(/root\["([^"]+)"\]/);
    const firstKey = match ? match[1] : null;
    currentNode.value = data.value[firstKey][node.key];
  }
  // 重置 drawer 状态（保留已有的颜色列表，方便连续操作）
  fontNameInput.value = "";
  enableAutoCrop.value = true;
  processedImageUrl.value = null;
  // 如果已有颜色且有图片，立即生成二值化
  if (selectedColors.value.length > 0 && props.currentImage?.url) {
    runBinarizationFromTable();
  }
  drawer.value = true;
};

// ========== 偏色管理 ==========
const getRowDeviation = (index) => rowDeviations.value[index] ?? 0;
const setRowDeviation = (index, value) => {
  const arr = [...rowDeviations.value];
  arr[index] = Math.max(0, Math.min(100, value));
  rowDeviations.value = arr;
  runBinarizationFromTable();
};

// ========== 工具函数 ==========
const isLightColor = (hex) => {
  hex = String(hex).replace("#", "");
  if (hex.length === 3)
    hex = hex
      .split("")
      .map((c) => c + c)
      .join("");
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > 186;
};

const hexToRgb = (hex) => {
  hex = hex.replace("#", "");
  if (hex.length === 3)
    hex = hex
      .split("")
      .map((c) => c + c)
      .join("");
  return {
    r: parseInt(hex.substring(0, 2), 16),
    g: parseInt(hex.substring(2, 4), 16),
    b: parseInt(hex.substring(4, 6), 16),
  };
};

const numToHex = (num) => {
  const hex = Math.max(0, Math.min(255, Math.floor(num)))
    .toString(16)
    .toUpperCase();
  return hex.length === 1 ? "0" + hex : hex;
};

// ========== 偏色计算 ==========
const buildDeviationListFromTable = () => {
  const list = [];
  for (let i = 0; i < selectedColors.value.length; i++) {
    const d = rowDeviations.value[i] ?? 0;
    const baseRgb = hexToRgb(selectedColors.value[i].hex);
    const baseHex =
      numToHex(baseRgb.r) + numToHex(baseRgb.g) + numToHex(baseRgb.b);
    const deviationHex = numToHex(d) + numToHex(d) + numToHex(d);
    list.push(`${baseHex}-${deviationHex}`);
  }
  return list;
};

const parseDeviation = (deviationStr) => {
  const [baseHex, deviationHex] = deviationStr.split("-");
  if (
    !baseHex ||
    !deviationHex ||
    baseHex.length !== 6 ||
    deviationHex.length !== 6
  )
    return null;
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

// ========== 二值化处理 ==========
const runBinarizationFromTable = () => {
  if (!props.currentImage?.url) return;
  const deviationList = buildDeviationListFromTable();
  if (deviationList.length === 0) return;
  const deviationDataList = deviationList.map(parseDeviation).filter(Boolean);
  if (deviationDataList.length === 0) return;

  const img = new Image();
  img.crossOrigin = "anonymous";
  img.onload = () => {
    try {
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");
      let startX = 0,
        startY = 0,
        width = img.width,
        height = img.height;
      if (props.selectionRect?.w > 0 && props.selectionRect?.h > 0) {
        startX = Math.max(
          0,
          Math.min(props.selectionRect.x, img.width - 1)
        );
        startY = Math.max(
          0,
          Math.min(props.selectionRect.y, img.height - 1)
        );
        width = Math.min(props.selectionRect.w, img.width - startX);
        height = Math.min(props.selectionRect.h, img.height - startY);
      }
      canvas.width = width;
      canvas.height = height;
      ctx.drawImage(
        img,
        startX,
        startY,
        width,
        height,
        0,
        0,
        width,
        height
      );
      const imageData = ctx.getImageData(0, 0, width, height);
      const pixelData = imageData.data;

      for (let i = 0; i < pixelData.length; i += 4) {
        const r = pixelData[i],
          g = pixelData[i + 1],
          b = pixelData[i + 2];
        let inRange = false;
        for (const dd of deviationDataList) {
          if (isColorInDeviationRange(r, g, b, dd)) {
            inRange = true;
            break;
          }
        }
        pixelData[i] = pixelData[i + 1] = pixelData[i + 2] = inRange
          ? 255
          : 0;
        pixelData[i + 3] = 255;
      }
      ctx.putImageData(imageData, 0, 0);
      processedImageUrl.value = canvas.toDataURL("image/png");
    } catch (e) {
      console.error("二值化出错:", e);
    }
  };
  img.src = props.currentImage.url;
};

// ========== 确认添加配置 ==========
const handleConfirmAddConfig = async () => {
  if (!fontNameInput.value?.trim()) {
    ElMessage.warning("请输入字库名称");
    return;
  }
  if (!processedImageUrl.value) {
    ElMessage.warning("请先生成二值化图片");
    return;
  }
  if (!currentNode.value) {
    ElMessage.warning("请选择要添加到的节点");
    return;
  }

  const deviationList = buildDeviationListFromTable();
  if (!deviationList.length) {
    ElMessage.warning("请先添加颜色");
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

  const fontName = fontNameInput.value.trim();

  try {
    const img = new Image();
    img.crossOrigin = "anonymous";

    await new Promise((resolve, reject) => {
      img.onload = () => {
        try {
          const canvas = document.createElement("canvas");
          const ctx = canvas.getContext("2d");
          canvas.width = img.width;
          canvas.height = img.height;
          ctx.drawImage(img, 0, 0);

          const imageData = ctx.getImageData(0, 0, img.width, img.height);
          const pixelData = imageData.data;

          // 找到白色像素的最小边界框
          let minX = img.width,
            minY = img.height,
            maxX = 0,
            maxY = 0;
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
            ElMessage.warning("二值化图片中没有白色像素");
            reject(new Error("没有白色像素"));
            return;
          }

          // 根据是否裁剪决定范围
          let cropMinX, cropMinY, cropMaxX, cropMaxY;
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

          // 提取二值数据
          const binaryData = [];
          for (let y = cropMinY; y <= cropMaxY; y++) {
            for (let x = cropMinX; x <= cropMaxX; x++) {
              const idx = (y * img.width + x) * 4;
              const isWhite =
                pixelData[idx] > 200 &&
                pixelData[idx + 1] > 200 &&
                pixelData[idx + 2] > 200;
              binaryData.push(isWhite ? "1" : "0");
            }
          }

          // 转为十六进制点阵字符串
          let matrixHex = "";
          for (let i = 0; i < binaryData.length; i += 4) {
            const bits = binaryData.slice(i, i + 4).join("");
            const paddedBits = bits.padEnd(4, "0");
            matrixHex += parseInt(paddedBits, 2)
              .toString(16)
              .toUpperCase();
          }

          // 偏色列表以 "|" 组合
          const deviationStr = deviationList.join("|");
          // 点阵 = hex&width,height,count
          const matrixStr = `${matrixHex}&${width},${height},${whitePixelCount}`;

          // 以字库名字作为 key 添加进 currentNode，并写入偏移点击区域属性
          currentNode.value[fontName] = {
            偏移点击区域: clickOffsetArea,
            偏色: deviationStr,
            点阵: matrixStr,
          };

          ElMessage.success(`配置 "${fontName}" 添加成功`);
          fontNameInput.value = "";
          fontClickOffsetAreaInput.value = "";
          drawer.value = false;
          resolve();
        } catch (error) {
          console.error("处理点阵时出错:", error);
          reject(error);
        }
      };
      img.onerror = () => reject(new Error("加载图片失败"));
      img.src = processedImageUrl.value;
    });
  } catch (error) {
    console.error("添加配置失败:", error);
    ElMessage.error("添加配置失败: " + (error.message || "未知错误"));
  }
};

// 暴露给父组件的方法
defineExpose({
  addColor,
  setFontClickOffsetAreaFromSelection,
});

const data = ref({
  主界面: {
    点阵:
      "000040000000000018000000008000000000000400000001000000000000000000000000000000000002000000020000000000000400000007800000000000000000000FC00003E00000000000000FE00003FFC000000000000FE00000C04000000000000FE00003E0C0000000000009C00007FFC00007C00000000000001FC000002000000000000000000000000000100000001E00000000000010000000FE000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000020000000000000000000001FFC00000000003FF000003FFC000000000007F000007FFC00000000000078000007FE00000000001C7C000007EF00000000003C7E000007C780000000007C7F00020FC3C000000000FE3D80041F81E000000003FF1CC0081F80F000000013FF0E60003F007800000047FF8720007F003C000000FFFFC3C880FE0007C00003FFFFE1E601FC0000F80037FFFFE0FF3FFC00007F3FFFFFFFF03FFFFFFFF07FFFFFFFFFF8007FFFFFFFFFFFFFFFFFF0000000003FFFFFFFF01FC0000000003FFFFFFFFFFFC00000000007FFFFFFFFFF8000000000001FFFFE000100000000000000C0000000000000000000000000000000000000000000000000000000000018000000000000000000007F0000000000F0000000007F0000000001F0000000007F0000000C01C0000000003F00000008000000000000180000000000000000&88,49,858",
    偏移点击区域: "0,0,0,0",
    查找区域: "2,2,100,100",
    固定点击区域: "2,2,100,100",
    偏色: "D61E24-373737",
    相似度: 0.9,
    状态: {},
    按钮: {
      活动: [574, 24, 73, 73],
      对话框第一个选项按钮: { 相似度: 0.7 },
    },
  },
});
</script>

<style scoped>
.config-tab-container {
  position: relative;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.config-drawer {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  min-width: 220px;
  background-color: #fff;
  display: flex;
  flex-direction: column;
  z-index: 1;
}

.config-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  flex-shrink: 0;
}

.config-drawer-title {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.config-drawer-body {
  flex: 1;
  padding: 0 14px;
  overflow: auto;
  font-size: 13px;
  color: #475569;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-drawer-footer {
  flex-shrink: 0;
  padding: 8px 14px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
}

/* 颜色表格 */
.color-table-wrap {
  flex-shrink: 0;
}

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
  padding: 0 8px;
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

/* 二值化预览区域 */
.result-section {
  flex: 1;
  min-height: 80px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 6px;
  background: #0f172a;
  background-image: linear-gradient(45deg, #1e293b 25%, transparent 25%),
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
  padding: 20px 0;
}

/* 字库配置区 */
.font-config-section {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 4px 0;
}

.font-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 过渡动画 */
.config-drawer-slide-enter-from,
.config-drawer-slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.config-drawer-slide-enter-active,
.config-drawer-slide-leave-active {
  transition: all 0.25s ease;
}
</style>
