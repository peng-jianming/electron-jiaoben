<template>
  <div class="right-panel">
    <!-- 放大镜 -->
    <div class="card">
      <div class="card-body magnifier-container">
        <div v-if="magnifierVisible && currentImage" class="magnifier">
          <canvas ref="magnifierCanvasRef" class="magnifier-canvas"></canvas>
        </div>
        <div v-else class="magnifier-placeholder">
          <el-icon><ZoomIn /></el-icon>
          <p>将鼠标移动到图片上查看</p>
        </div>
        <!-- 当前颜色值 -->
        <div class="current-color">
          <div style="display: flex; gap: 12px">
            <div>x: {{ currentPosition ? currentPosition.x : "0" }}</div>
            <div>y: {{ currentPosition ? currentPosition.y : "0" }}</div>
          </div>
          <div>HEX: {{ currentColor ? currentColor.hex : "#000000" }}</div>
        </div>
      </div>
    </div>

    <!-- 选中颜色列表 -->
    <el-tabs type="border-card" size="mini">
      <el-tab-pane label="颜色">
        <div style="display: flex">
          <div>
            <el-table
              :data="currentSelectedColors"
              height="205"
              border
              style="width: 250px"
              size="small"
              empty-text="等待选取颜色"
            >
              <el-table-column type="index"> </el-table-column>
              <el-table-column label="坐标" width="60">
                <template #default="scope">
                  {{ scope.row.x }}, {{ scope.row.y }}
                </template>
              </el-table-column>
              <el-table-column prop="hex" label="hex" width="80">
                <template #default="scope">
                  <div
                    :style="{
                      'background-color': scope.row.hex,
                      color: isLightColor(scope.row.hex) ? '#000000' : '#ffffff',
                    }"
                  >
                    {{ scope.row.hex }}
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="70">
                <template #default="scope">
                  <el-button
                    type="text"
                    size="small"
                    @click="$emit('remove-color', scope.$index)"
                    >删除</el-button
                  >
                </template>
              </el-table-column>
            </el-table>
            <el-button
              type="primary"
              size="small"
              class="clear-all-btn"
              @click="calculateDeviation"
            >
              计算偏色
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="$emit('clear-all-colors')"
              class="clear-all-btn"
            >
              清空全部
            </el-button>
          </div>
          <div
            style="
              color: #909399;
              border: 1px solid #dcdfe6;
              margin-left: 5px;
              width: 130px;
            "
          >
            <div style="font-size: 14px;  padding: 5px; border-bottom: 1px solid #dcdfe6;">
              偏色列表
            </div>
            <div>
              <el-scrollbar height="162px" style="padding: 5px;">
                <el-checkbox-group
                  v-model="checkboxGroup2"
                  size="small"
                  style="display: flex; flex-direction: column; gap: 5px"
                >
                  <el-checkbox
                    v-for="(item, index) in deviationColors"
                    :key="index"
                    :label="item"
                    border
                  ></el-checkbox>
                </el-checkbox-group>
              </el-scrollbar>
            </div>
            <el-button
              type="primary"
              size="small"
              class="clear-all-btn"
              @click="clearDeviationColors"
            >
              清空偏色
            </el-button>
            <el-button
              type="primary"
              size="small"
              class="clear-all-btn"
            >
              重新渲染
            </el-button>
          </div>
        </div>

        <div style="height: 250px; display: flex">
          <div>1</div>
        </div>
      </el-tab-pane>
      <el-tab-pane label="图片">等待实现</el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { ZoomIn, Collection, Delete } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

const props = defineProps({
  magnifierVisible: {
    type: Boolean,
    default: false,
  },
  currentImage: {
    type: Object,
    default: null,
  },
  currentPosition: {
    type: Object,
    default: () => ({ x: 0, y: 0 }),
  },
  currentColor: {
    type: Object,
    default: null,
  },
  currentSelectedColors: {
    type: Array,
    default: () => [],
  },
});

defineEmits(["remove-color", "clear-all-colors"]);

const magnifierCanvasRef = ref(null);
const deviationColors = ref([]);
const checkboxGroup2 = ref([]);

// 判断颜色是否偏白（根据亮度计算）
const isLightColor = (hex) => {
  // 移除 # 号
  hex = hex.replace("#", "");

  // 如果是3位hex，转换为6位
  if (hex.length === 3) {
    hex = hex
      .split("")
      .map((char) => char + char)
      .join("");
  }

  // 转换为 RGB
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  // 计算相对亮度（W3C 标准公式）
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;

  // 如果亮度大于 186（约 73%），则认为偏白，使用黑色字体
  return luminance > 186;
};

// HEX 转 RGB
const hexToRgb = (hex) => {
  // 移除 # 号
  hex = hex.replace("#", "");

  // 如果是3位hex，转换为6位
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
  const hex = Math.max(0, Math.min(255, Math.floor(num))).toString(16).toUpperCase();
  return hex.length === 1 ? "0" + hex : hex;
};

// 计算偏色
const calculateDeviation = () => {
  if (!props.currentSelectedColors || props.currentSelectedColors.length === 0) {
    ElMessage.warning("请先选取颜色");
    return;
  }

  // 1. 将所有颜色转换为 RGB
  const rgbColors = props.currentSelectedColors.map((color) => {
    return hexToRgb(color.hex);
  });

  // 2. 确定每个通道的最小值和最大值
  let minR = 255,
    maxR = 0;
  let minG = 255,
    maxG = 0;
  let minB = 255,
    maxB = 0;

  rgbColors.forEach((rgb) => {
    minR = Math.min(minR, rgb.r);
    maxR = Math.max(maxR, rgb.r);
    minG = Math.min(minG, rgb.g);
    maxG = Math.max(maxG, rgb.g);
    minB = Math.min(minB, rgb.b);
    maxB = Math.max(maxB, rgb.b);
  });

  // 3. 计算基准色（取最小值和最大值的平均值，向下取整）
  const baseR = Math.floor((minR + maxR) / 2);
  const baseG = Math.floor((minG + maxG) / 2);
  const baseB = Math.floor((minB + maxB) / 2);

  // 4. 计算偏色（最大值减基准色）
  const deviationR = maxR - baseR;
  const deviationG = maxG - baseG;
  const deviationB = maxB - baseB;

  // 5. 格式化为 HEX 字符串
  const baseHex = numToHex(baseR) + numToHex(baseG) + numToHex(baseB);
  const deviationHex = numToHex(deviationR) + numToHex(deviationG) + numToHex(deviationB);

  // 6. 组合结果
  const result = `${baseHex}-${deviationHex}`;
  
  // 7. 检查偏色列表中是否已存在相同的偏色
  const existingIndex = deviationColors.value.findIndex((item) => item === result);
  if (existingIndex !== -1) {
    ElMessage.warning(`偏色 ${result} 已存在于列表中（第 ${existingIndex + 1} 项）`);
    return;
  }

  // 8. 添加到偏色列表并默认勾选
  deviationColors.value.push(result);
  checkboxGroup2.value.push(result);
  
  ElMessage.success("偏色计算完成");
};

// 清空偏色列表
const clearDeviationColors = () => {
  deviationColors.value = [];
  checkboxGroup2.value = [];
  ElMessage.success("已清空偏色列表");
};

// 暴露放大镜 canvas 给父组件，用于绘制
defineExpose({
  getMagnifierCanvas: () => magnifierCanvasRef.value,
});
</script>

<style scoped>
.el-button + .el-button {
  margin-left: 0;
}
.el-checkbox {
  margin-right: 0;
}
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 0 10px;
}

.card {
  background: var(--bg-card);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s ease;
}

.card:hover {
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: var(--shadow-lg);
}

.card-body {
  padding: 10px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-width: 0;
}

.magnifier-container {
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 200px;
}

.magnifier {
  width: 220px;
  height: 220px;
  border: 2px solid var(--primary-color);
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a2e;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.magnifier-canvas {
  width: 100%;
  height: 100%;
  image-rendering: pixelated;
}

.magnifier-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 220px;
  height: 220px;
  color: var(--text-secondary);
  border: 2px dashed var(--border-color);
  border-radius: 8px;
}

.magnifier-placeholder .el-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.magnifier-placeholder p {
  margin: 0;
  font-size: 12px;
}

.current-color {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 120px;
  text-align: left;
}

.color-values {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.color-value-item {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.color-label {
  color: var(--text-secondary);
}

.color-value {
  color: var(--text-primary);
  font-weight: 500;
  font-family: "Courier New", monospace;
}

.selected-colors-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.empty-colors {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--text-secondary);
}

.empty-colors .el-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-colors p {
  margin: 0;
  font-size: 14px;
}

.selected-colors-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.selected-color-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(51, 65, 85, 0.3);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.selected-color-item:hover {
  background: rgba(51, 65, 85, 0.5);
}

.color-preview-small {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  flex-shrink: 0;
}

.color-info-small {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.color-rgb-small,
.color-hex-small {
  font-size: 12px;
  color: var(--text-primary);
  font-family: "Courier New", monospace;
}

.color-hex-small {
  color: var(--text-secondary);
}

.color-coord-small {
  font-size: 11px;
  color: var(--primary-light);
  font-weight: 500;
  margin-bottom: 2px;
}

.remove-color-btn {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.selected-color-item:hover .remove-color-btn {
  opacity: 1;
}

.clear-all-btn {
  width: 100%;
}
</style>
