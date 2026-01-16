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
            <div style="font-size: 14px; padding: 5px; border-bottom: 1px solid #dcdfe6">
              偏色列表
            </div>
            <div>
              <el-scrollbar height="162px" style="padding: 5px">
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
              @click="handleRerender"
            >
              重新渲染
            </el-button>
          </div>
        </div>
        <!-- 显示渲染后的图片区域 -->
        <div
          style="
            margin-top: 5px;
            height: 250px;
            border: 1px solid #dcdfe6;
            border-radius: 4px;
            overflow: hidden;
            background: #f5f5f5;
            display: flex;
            align-items: center;
            justify-content: center;
          "
        >
          <img
            v-if="processedImageUrl"
            :src="processedImageUrl"
            alt="处理后的图片"
            style="max-width: 100%; max-height: 100%; object-fit: contain"
          />
          <div v-else style="color: #909399; font-size: 12px">
            偏色二值化后的图片将显示在此处
          </div>
        </div>
      </el-tab-pane>
      <el-tab-pane label="图片">
        <div>
          <!-- 隐藏的文件选择框 -->
          <input
            ref="imageFileInputRef"
            type="file"
            accept="image/*"
            multiple
            style="display: none"
            @change="handleImageFileSelect"
          />
          <el-table
            :data="uploadedImages"
            height="205"
            border
            style="width: 100%"
            size="small"
            empty-text="等待上传图片"
          >
            <el-table-column type="index" label="#" width="50"> </el-table-column>
            <el-table-column label="缩略图">
              <template #default="scope">
                <div class="thumbnail-container">
                  <el-image
                    :src="scope.row.url"
                    :preview-src-list="getPreviewSrcList()"
                    :initial-index="scope.$index"
                    fit="contain"
                    preview-teleported
                    class="thumbnail-image"
                  />
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="70">
              <template #default="scope">
                <el-button
                  type="text"
                  size="small"
                  @click="removeImage(scope.$index)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="display: flex; justify-content: space-between; margin-top: 10px">
            <el-button
              type="primary"
              size="small"
              style="width: 48%"
              @click="handleUploadClick"
            >
              上传
            </el-button>
            <el-button type="primary" size="small" style="width: 48%">
              截图
            </el-button>
          </div>
          <el-button
            type="danger"
            size="small"
            class="clear-all-btn"
            @click="clearAllImages"
          >
            清空全部
          </el-button>
        </div>
        <div></div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, nextTick } from "vue";
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
  selectionRect: {
    type: Object,
    default: null,
  },
  imageRef: {
    type: Object,
    default: null,
  },
});

defineEmits(["remove-color", "clear-all-colors"]);

const magnifierCanvasRef = ref(null);
const deviationColors = ref([]);
const checkboxGroup2 = ref([]);
const processedImageUrl = ref(null);
const imageFileInputRef = ref(null);
const uploadedImages = ref([]);

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
  const hex = Math.max(0, Math.min(255, Math.floor(num)))
    .toString(16)
    .toUpperCase();
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

  // 9. 自动执行一次二值化渲染
  // 使用 nextTick 确保 checkboxGroup2 已更新
  nextTick(() => {
    handleRerender();
  });
};

// 清空偏色列表
const clearDeviationColors = () => {
  deviationColors.value = [];
  checkboxGroup2.value = [];
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
  if (!props.currentImage || !props.currentImage.url) {
    ElMessage.warning("请先载入图片");
    return;
  }

  // 获取选中的偏色列表
  const selectedDeviations = checkboxGroup2.value;
  if (selectedDeviations.length === 0) {
    ElMessage.warning("请先选择偏色项");
    return;
  }

  // 解析所有选中的偏色
  const deviationDataList = selectedDeviations
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

// 处理上传按钮点击
const handleUploadClick = () => {
  imageFileInputRef.value?.click();
};

// 处理图片文件选择
const handleImageFileSelect = (event) => {
  const files = Array.from(event.target.files || []);
  if (files.length === 0) return;

  // 过滤出图片文件
  const imageFiles = files.filter((file) => file.type.startsWith("image/"));

  if (imageFiles.length === 0) {
    ElMessage.error("请选择图片文件");
    return;
  }

  // 处理每个图片文件
  imageFiles.forEach((file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const url = e.target.result;

      // 创建缩略图
      const img = new Image();
      img.onload = () => {
        // 创建缩略图 canvas
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        const maxSize = 100; // 缩略图最大尺寸

        // 计算缩略图尺寸
        let thumbWidth = img.width;
        let thumbHeight = img.height;
        if (thumbWidth > thumbHeight) {
          if (thumbWidth > maxSize) {
            thumbHeight = (thumbHeight * maxSize) / thumbWidth;
            thumbWidth = maxSize;
          }
        } else {
          if (thumbHeight > maxSize) {
            thumbWidth = (thumbWidth * maxSize) / thumbHeight;
            thumbHeight = maxSize;
          }
        }

        canvas.width = thumbWidth;
        canvas.height = thumbHeight;
        ctx.drawImage(img, 0, 0, thumbWidth, thumbHeight);

        const thumbnail = canvas.toDataURL("image/png");

        // 添加到列表
        uploadedImages.value.push({
          id: Date.now() + Math.random(), // 生成唯一ID
          url: url,
          thumbnail: thumbnail,
          file: file, // 保存原始文件对象
        });

        ElMessage.success("图片上传成功");
      };
      img.onerror = () => {
        ElMessage.error("图片加载失败");
      };
      img.src = url;
    };
    reader.onerror = () => {
      ElMessage.error("读取文件失败");
    };
    reader.readAsDataURL(file);
  });

  // 清空文件选择，以便可以重复选择同一文件
  event.target.value = "";
};

// 删除图片
const removeImage = (index) => {
  uploadedImages.value.splice(index, 1);
  ElMessage.success("图片已删除");
};

// 清空所有图片
const clearAllImages = () => {
  if (uploadedImages.value.length === 0) {
    ElMessage.warning("列表已为空");
    return;
  }
  uploadedImages.value = [];
  ElMessage.success("已清空所有图片");
};

// 获取预览图片列表
const getPreviewSrcList = () => {
  return uploadedImages.value.map((img) => img.url);
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
  margin-top: 10px;
}

.thumbnail-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 60px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  overflow: hidden;
  background: #f5f5f5;
  transition: all 0.2s ease;
}

.thumbnail-container:hover {
  border-color: var(--primary-color);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
  transform: scale(1.05);
}

.thumbnail-image {
  width: 100%;
  height: 100%;
}
</style>
