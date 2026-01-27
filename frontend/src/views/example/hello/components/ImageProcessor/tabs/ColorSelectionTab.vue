<template>
  <div style="display: flex; flex-direction: column;height: 590px;">
    <div style="display: flex">
      <ColorList 
        :colors="currentSelectedColors"
        :current-image="currentImage"
        :selection-rect="selectionRect"
        @remove-color="$emit('remove-color', $event)"
        @calculate-deviation="handleCalculateDeviation"
        @clear-all-colors="$emit('clear-all-colors')"
        @add-colors="handleAddColors"
        @preview-toggle="handlePreviewToggle"
        @deviation-change="handleDeviationChange"
        @add-to-deviation-list="handleAddToDeviationList"
      />
      <DeviationList 
        :deviation-colors="deviationColors"
        v-model="selectedDeviations"
        :is-preview-enabled="isPreviewEnabled"
        @clear-deviations="handleClearDeviationColors"
        @rerender="handleRerender"
      />
    </div>
    <!-- 显示渲染后的图片区域 -->
    <div class="result-section">
      <el-image :src="processedImageUrl" :preview-src-list="[processedImageUrl]" fit="contain" preview-teleported
      style="height: 100%; width: 100%;">
        <template #placeholder>
          <div style="display: flex;justify-content: center;align-items: center;height: 100%;width: 100%;">偏色二值化后的图片将显示在此处
          </div>
        </template>
      </el-image>
    </div>

    <!-- 字库制作区域：偏移点击区域（单独一行，可圈选） -->
    <div style="margin-top: 10px; display: flex; align-items: center; gap: 10px; padding: 0 5px; flex-shrink: 0;">
      <el-input
        v-model="fontClickOffsetAreaInput"
        placeholder="请输入偏移点击区域，格式：x,y,w,h（可不填，默认 0,0,0,0）"
        size="small"
        style="flex: 1;"
        clearable
      >
        <template #append>
          <el-button
            :type="fontClickOffsetAreaSelectionEnabled ? 'warning' : 'primary'"
            :disabled="!hasSelectionRect"
            size="small"
            @click="toggleFontClickOffsetAreaSelection"
          >
            {{ fontClickOffsetAreaSelectionEnabled ? '取消圈选范围' : '启动圈选范围' }}
          </el-button>
        </template>
      </el-input>
    </div>

    <!-- 字库制作区域：字库名称 + 加入按钮 -->
    <div style="margin-top: 5px; display: flex; align-items: center; gap: 10px; padding: 0 5px; flex-shrink: 0;">
      <el-input
        v-model="fontNameInput"
        placeholder="请输入字库名字"
        size="small"
        style="flex: 1;"
        clearable
      />
      <el-button
        type="success"
        size="small"
        @click="handleAddFontLibrary"
        :disabled="!fontNameInput || !processedImageUrl || !selectedDeviations || selectedDeviations.length === 0 || !hasFontLibraryFile"
      >
        加入字库
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed } from "vue";
import { ElMessage } from "element-plus";
import ColorList from "../lists/ColorList.vue";
import DeviationList from "../lists/DeviationList.vue";
import ImageDisplayArea from "../common/ImageDisplayArea.vue";

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

const deviationColors = ref([]);
const selectedDeviations = ref([]);
const processedImageUrl = ref(null);
const lastRenderedImageUrl = ref(null); // 保存最后一次通过"重新渲染"生成的图片
const isPreviewEnabled = ref(false);
const previewDeviationValue = ref(0);
const fontClickOffsetAreaInput = ref("");
const fontNameInput = ref("");

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

// RGB 转 HSV
const rgbToHsv = (rgb) => {
  const r = rgb.r / 255;
  const g = rgb.g / 255;
  const b = rgb.b / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const delta = max - min;

  let h = 0;
  if (delta !== 0) {
    if (max === r) {
      h = ((g - b) / delta) % 6;
    } else if (max === g) {
      h = (b - r) / delta + 2;
    } else {
      h = (r - g) / delta + 4;
    }
  }
  h = Math.round(h * 60);
  if (h < 0) h += 360;

  const s = max === 0 ? 0 : delta / max;
  const v = max;

  return { h, s, v };
};

// 计算基准色和偏色（从颜色列表中）
const calculateBaseOffset = (rgbColors) => {
  if (!rgbColors || rgbColors.length === 0) {
    return null;
  }

  // 确定每个通道的最小值和最大值
  let minR = 255, maxR = 0;
  let minG = 255, maxG = 0;
  let minB = 255, maxB = 0;

  rgbColors.forEach((rgb) => {
    minR = Math.min(minR, rgb.r);
    maxR = Math.max(maxR, rgb.r);
    minG = Math.min(minG, rgb.g);
    maxG = Math.max(maxG, rgb.g);
    minB = Math.min(minB, rgb.b);
    maxB = Math.max(maxB, rgb.b);
  });

  // 计算基准色（取最小值和最大值的平均值，向下取整）
  const baseR = Math.floor((minR + maxR) / 2);
  const baseG = Math.floor((minG + maxG) / 2);
  const baseB = Math.floor((minB + maxB) / 2);

  // 计算偏色（最大值减基准色）
  const deviationR = maxR - baseR;
  const deviationG = maxG - baseG;
  const deviationB = maxB - baseB;

  // 格式化为 HEX 字符串
  const baseHex = numToHex(baseR) + numToHex(baseG) + numToHex(baseB);
  const deviationHex = numToHex(deviationR) + numToHex(deviationG) + numToHex(deviationB);

  // 组合结果
  return `${baseHex}-${deviationHex}`;
};

// 智能颜色分段算法
const colorSegmentation = (colorList) => {
  const segments = {};
  
  for (const color of colorList) {
    const rgb = hexToRgb(color);
    const { h, s, v } = rgbToHsv(rgb);

    // 1. 按亮度分组
    let brightnessGroup;
    if (v < 0.33) {
      brightnessGroup = "dark";
    } else if (v < 0.67) {
      brightnessGroup = "medium";
    } else {
      brightnessGroup = "light";
    }

    // 2. 按色相分组
    let hueGroup;
    if (s < 0.2) {
      // 接近无色
      hueGroup = "grayscale";
    } else if (h < 30 || h >= 330) {
      hueGroup = "red";
    } else if (h < 90) {
      hueGroup = "yellow_orange";
    } else if (h < 150) {
      hueGroup = "green";
    } else if (h < 210) {
      hueGroup = "cyan";
    } else if (h < 270) {
      hueGroup = "blue";
    } else {
      hueGroup = "purple";
    }

    // 3. 组合键
    const segmentKey = `${brightnessGroup}_${hueGroup}`;

    if (!segments[segmentKey]) {
      segments[segmentKey] = [];
    }
    segments[segmentKey].push(rgb);
  }
 
  // 4. 为每个分段计算基准色+偏色
  const results = [];
  for (const [segmentKey, colors] of Object.entries(segments)) {
    if (colors.length >= 2) {
      // 计算基准色和偏色
      const result = calculateBaseOffset(colors);
      if (result) {
        results.push({ segmentKey, deviation: result });
      }
    } else if (colors.length === 1) {
      // 只有一个颜色，只有基准色，无偏色（这种情况暂时跳过，因为需要偏色）
      // 可以设置为偏色为 000000，或者跳过
      const rgb = colors[0];
      const baseHex = numToHex(rgb.r) + numToHex(rgb.g) + numToHex(rgb.b);
      const result = `${baseHex}-000000`;
      results.push({ segmentKey, deviation: result });
    }
  }

  return results;
};

// 处理预览开关
const handlePreviewToggle = (enabled) => {
  isPreviewEnabled.value = enabled;
  if (enabled) {
    // 开启预览时，保存当前的渲染图片（如果有）
    if (processedImageUrl.value) {
      lastRenderedImageUrl.value = processedImageUrl.value;
    }
    // 立即执行一次预览渲染
    processPreviewImage();
  } else {
    // 关闭预览时，恢复之前的渲染图片（如果有）
    if (lastRenderedImageUrl.value) {
      processedImageUrl.value = lastRenderedImageUrl.value;
    } else {
      processedImageUrl.value = null;
    }
  }
};

// 处理偏差值变化
const handleDeviationChange = (value) => {
  previewDeviationValue.value = value;
  if (isPreviewEnabled.value) {
    // 如果预览已开启，立即更新预览图片
    processPreviewImage();
  }
};

// 处理预览图片二值化
const processPreviewImage = () => {
  if (!props.currentImage || !props.currentImage.url) {
    return;
  }

  if (!props.currentSelectedColors || props.currentSelectedColors.length === 0) {
    return;
  }

  // 获取第一个颜色作为基准色
  const firstColor = props.currentSelectedColors[0];
  const baseRgb = hexToRgb(firstColor.hex);

  // 进度条值直接对应RGB偏差值
  const deviationR = previewDeviationValue.value;
  const deviationG = previewDeviationValue.value;
  const deviationB = previewDeviationValue.value;

  // 创建图片对象
  const img = new Image();
  img.crossOrigin = "anonymous";
  img.onload = () => {
    try {
      // 创建 canvas 用于处理
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");

      // 确定处理区域
      let startX = 0;
      let startY = 0;
      let width = img.width;
      let height = img.height;

      if (props.selectionRect && props.selectionRect.w > 0 && props.selectionRect.h > 0) {
        // 使用圈选范围
        startX = Math.max(0, Math.min(props.selectionRect.x, img.width - 1));
        startY = Math.max(0, Math.min(props.selectionRect.y, img.height - 1));
        width = Math.min(props.selectionRect.w, img.width - startX);
        height = Math.min(props.selectionRect.h, img.height - startY);
      }

      // 设置 canvas 尺寸
      canvas.width = width;
      canvas.height = height;

      // 绘制原始图片区域到 canvas
      ctx.drawImage(img, startX, startY, width, height, 0, 0, width, height);

      // 获取像素数据
      const imageData = ctx.getImageData(0, 0, width, height);
      const data = imageData.data;

      // 计算每个通道的范围
      const minR = Math.max(0, baseRgb.r - deviationR);
      const maxR = Math.min(255, baseRgb.r + deviationR);
      const minG = Math.max(0, baseRgb.g - deviationG);
      const maxG = Math.min(255, baseRgb.g + deviationG);
      const minB = Math.max(0, baseRgb.b - deviationB);
      const maxB = Math.min(255, baseRgb.b + deviationB);

      // 遍历每个像素进行二值化处理
      for (let i = 0; i < data.length; i += 4) {
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];

        // 检查是否在偏色范围内
        const inRange = r >= minR && r <= maxR && g >= minG && g <= maxG && b >= minB && b <= maxB;

        // 在范围内设置为白色，否则设置为黑色
        if (inRange) {
          data[i] = 255; // R
          data[i + 1] = 255; // G
          data[i + 2] = 255; // B
          data[i + 3] = 255; // A
        } else {
          data[i] = 0; // R
          data[i + 1] = 0; // G
          data[i + 2] = 0; // B
          data[i + 3] = 255; // A
        }
      }

      // 将处理后的数据写回 canvas
      ctx.putImageData(imageData, 0, 0);

      // 转换为图片 URL
      processedImageUrl.value = canvas.toDataURL("image/png");
    } catch (error) {
      console.error("处理预览图片时出错:", error);
    }
  };

  img.onerror = () => {
    console.error("加载图片失败");
  };

  img.src = props.currentImage.url;
};

// 添加进偏色列表
const handleAddToDeviationList = () => {
  if (!props.currentSelectedColors || props.currentSelectedColors.length === 0) {
    ElMessage.warning("请先选取颜色");
    return;
  }

  // 获取第一个颜色作为基准色
  const firstColor = props.currentSelectedColors[0];
  const baseRgb = hexToRgb(firstColor.hex);

  // 进度条值直接对应RGB偏差值
  const deviationR = previewDeviationValue.value;
  const deviationG = previewDeviationValue.value;
  const deviationB = previewDeviationValue.value;

  // 格式化为 HEX 字符串
  const baseHex = numToHex(baseRgb.r) + numToHex(baseRgb.g) + numToHex(baseRgb.b);
  const deviationHex = numToHex(deviationR) + numToHex(deviationG) + numToHex(deviationB);

  // 组合结果
  const deviationStr = `${baseHex}-${deviationHex}`;

  // 检查偏色列表中是否已存在相同的偏色
  const existingIndex = deviationColors.value.findIndex((item) => item === deviationStr);
  if (existingIndex !== -1) {
    ElMessage.warning("该偏色已存在于列表中");
    return;
  }

  // 添加到偏色列表并默认勾选
  deviationColors.value.push(deviationStr);
  selectedDeviations.value.push(deviationStr);
  ElMessage.success("已添加进偏色列表");
};

// 计算偏色
const handleCalculateDeviation = () => {
  // 如果预览已开启，不执行计算偏色
  if (isPreviewEnabled.value) {
    ElMessage.warning("预览模式下无法计算偏色，请先关闭预览");
    return;
  }
  
  if (!props.currentSelectedColors || props.currentSelectedColors.length === 0) {
    ElMessage.warning("请先选取颜色");
    return;
  }

  // 1. 先进行颜色分段处理
  const colorHexList = props.currentSelectedColors.map((color) => color.hex);
  const segmentationResults = colorSegmentation(colorHexList);

  if (segmentationResults.length === 0) {
    ElMessage.warning("颜色分段后没有有效的结果");
    return;
  }

  // 2. 对每个分段的结果进行处理
  let addedCount = 0;
  for (const { segmentKey, deviation } of segmentationResults) {
    // 检查偏色列表中是否已存在相同的偏色
    const existingIndex = deviationColors.value.findIndex((item) => item === deviation);
    if (existingIndex !== -1) {
      console.log(`偏色 ${deviation} (分段: ${segmentKey}) 已存在于列表中（第 ${existingIndex + 1} 项）`);
      continue;
    }

    // 添加到偏色列表并默认勾选
    deviationColors.value.push(deviation);
    selectedDeviations.value.push(deviation);
    addedCount++;
  }

  if (addedCount === 0) {
    ElMessage.warning("所有偏色都已存在于列表中");
    return;
  }

  ElMessage.success(`偏色计算完成，共添加 ${addedCount} 个偏色（来自 ${segmentationResults.length} 个颜色分段）`);

  // 3. 自动执行一次二值化渲染
  nextTick(() => {
    handleRerender();
  });
};

// 处理添加统计的颜色
const handleAddColors = (colorStats) => {
  // 将统计的颜色添加到父组件的颜色列表中
  emit("add-colors", colorStats);
};

// 清空偏色列表
const handleClearDeviationColors = () => {
  deviationColors.value = [];
  selectedDeviations.value = [];
  processedImageUrl.value = null;
  ElMessage.success("已清空偏色列表");
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

// 处理图片二值化
const handleRerender = () => {
  // 如果预览已开启，不执行重新渲染
  if (isPreviewEnabled.value) {
    ElMessage.warning("预览模式下无法重新渲染，请先关闭预览");
    return;
  }

  if (!props.currentImage || !props.currentImage.url) {
    ElMessage.warning("请先载入图片");
    return;
  }

  // 获取选中的偏色列表
  if (selectedDeviations.value.length === 0) {
    ElMessage.warning("请先选择偏色项");
    return;
  }

  // 解析所有选中的偏色
  const deviationDataList = selectedDeviations.value
    .map((dev) => parseDeviation(dev))
    .filter((data) => data !== null);

  if (deviationDataList.length === 0) {
    ElMessage.error("偏色数据格式错误");
    return;
  }

  // 创建图片对象
  const img = new Image();
  img.crossOrigin = "anonymous";
  img.onload = () => {
    try {
      // 创建 canvas 用于处理
      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");

      // 确定处理区域
      let startX = 0;
      let startY = 0;
      let width = img.width;
      let height = img.height;

      if (props.selectionRect && props.selectionRect.w > 0 && props.selectionRect.h > 0) {
        // 使用圈选范围
        startX = Math.max(0, Math.min(props.selectionRect.x, img.width - 1));
        startY = Math.max(0, Math.min(props.selectionRect.y, img.height - 1));
        width = Math.min(props.selectionRect.w, img.width - startX);
        height = Math.min(props.selectionRect.h, img.height - startY);
      }

      // 设置 canvas 尺寸
      canvas.width = width;
      canvas.height = height;

      // 绘制原始图片区域到 canvas
      ctx.drawImage(img, startX, startY, width, height, 0, 0, width, height);

      // 获取像素数据
      const imageData = ctx.getImageData(0, 0, width, height);
      const data = imageData.data;

      // 遍历每个像素进行二值化处理
      for (let i = 0; i < data.length; i += 4) {
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];

        // 检查是否在任何一个偏色范围内
        let inRange = false;
        for (const deviationData of deviationDataList) {
          if (isColorInDeviationRange(r, g, b, deviationData)) {
            inRange = true;
            break;
          }
        }

        // 在范围内设置为白色，否则设置为黑色
        if (inRange) {
          data[i] = 255; // R
          data[i + 1] = 255; // G
          data[i + 2] = 255; // B
          data[i + 3] = 255; // A
        } else {
          data[i] = 0; // R
          data[i + 1] = 0; // G
          data[i + 2] = 0; // B
          data[i + 3] = 255; // A
        }
      }

      // 将处理后的数据写回 canvas
      ctx.putImageData(imageData, 0, 0);

      // 转换为图片 URL
      processedImageUrl.value = canvas.toDataURL("image/png");
      // 保存最后一次渲染的图片
      lastRenderedImageUrl.value = processedImageUrl.value;
      ElMessage.success("图片处理完成");
    } catch (error) {
      console.error("处理图片时出错:", error);
      ElMessage.error("处理图片失败");
    }
  };

  img.onerror = () => {
    ElMessage.error("加载图片失败");
  };

  img.src = props.currentImage.url;
};

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

  if (!selectedDeviations.value || selectedDeviations.value.length === 0) {
    ElMessage.warning("请先选择偏色");
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
          const deviationStr = selectedDeviations.value.join('|');

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

// 暴露选中的偏色列表和处理后的图片URL，供父组件使用
defineExpose({
  getSelectedDeviations: () => selectedDeviations.value,
  getProcessedImageUrl: () => processedImageUrl.value,
  setFontClickOffsetAreaFromSelection,
});
</script>

<style scoped>
  .result-section {
    margin-top: 5px;
    flex: 1;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
    /* 深色棋盘格背景，用于显示透明区域 */
    background: #1a1a2e;
    background-image: linear-gradient(45deg, #2a2a3e 25%, transparent 25%),
      linear-gradient(-45deg, #2a2a3e 25%, transparent 25%),
      linear-gradient(45deg, transparent 75%, #2a2a3e 75%),
      linear-gradient(-45deg, transparent 75%, #2a2a3e 75%);
    background-size: 16px 16px;
    background-position: 0 0, 0 8px, 8px -8px, -8px 0px;
    color: #909399;
    font-size: 12px;
  }
  

  </style>