<template>
  <div class="right-panel">
    <!-- 放大镜 -->
    <div class="card">
      <div class="card-body magnifier-container">
        <div v-if="magnifierVisible && currentImage" class="magnifier">
          <canvas ref="magnifierCanvasRef" class="magnifier-canvas"></canvas>
        </div>
        <div v-else class="magnifier-placeholder">
          <el-icon>
            <ZoomIn />
          </el-icon>
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
        <div style="display: flex; flex-direction: column;height: 590px;">
          <div style="display: flex">
            <div>
              <el-table :data="currentSelectedColors" height="205" border size="small" empty-text="等待选取颜色">
                <el-table-column type="index" label="#"> </el-table-column>
                <el-table-column label="坐标" width="80">
                  <template #default="scope">
                    {{ scope.row.x }}, {{ scope.row.y }}
                  </template>
                </el-table-column>
                <el-table-column prop="hex" label="hex" width="80">
                  <template #default="scope">
                    <div :style="{
                      'background-color': scope.row.hex,
                      color: isLightColor(scope.row.hex) ? '#000000' : '#ffffff',
                    }">
                      {{ scope.row.hex }}
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="70">
                  <template #default="scope">
                    <el-button type="text" size="small" @click="$emit('remove-color', scope.$index)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
             <div style="padding: 0 5px;">
              <el-button type="primary" size="small" class="clear-all-btn" @click="calculateDeviation">
                计算偏色
              </el-button>
              <el-button type="danger" size="small" @click="$emit('clear-all-colors')" class="clear-all-btn">
                清空全部
              </el-button>
             </div>
            </div>
            <div style="
              color: #909399;
              border: 1px solid #dcdfe6;
              margin-left: 5px;
              width: 170px;
            ">
              <div style="font-size: 14px; padding: 5px; border-bottom: 1px solid #dcdfe6">
                偏色列表
              </div>
              <div>
                <el-scrollbar height="162px" style="padding: 5px">
                  <el-checkbox-group v-model="checkboxGroup2" size="small"
                    style="display: flex; flex-direction: column; gap: 5px">
                    <el-checkbox v-for="(item, index) in deviationColors" :key="index" :label="item"
                      border></el-checkbox>
                  </el-checkbox-group>
                </el-scrollbar>
              </div>
              <div style="padding: 0 5px;">
                <el-button type="primary" size="small" class="clear-all-btn" @click="clearDeviationColors">
                  清空偏色
                </el-button>
                <el-button type="primary" size="small" class="clear-all-btn" @click="handleRerender">
                  重新渲染
                </el-button>

              </div>
            </div>
          </div>
          <!-- 显示渲染后的图片区域 -->
          <div style="
            margin-top: 5px;
            flex: 1;
            border: 1px solid #dcdfe6;
            border-radius: 4px;
            overflow: hidden;
            background: #f5f5f5;
            display: flex;
            align-items: center;
            justify-content: center;
          ">
            <img v-if="processedImageUrl" :src="processedImageUrl" alt="处理后的图片"
              style="max-width: 100%; max-height: 100%; object-fit: contain" />
            <div v-else style="color: #909399; font-size: 12px">
              偏色二值化后的图片将显示在此处
            </div>
          </div>

        </div>
      </el-tab-pane>
      <el-tab-pane label="图片">
        <div style="display: flex; flex-direction: column;height: 590px;">
          <div>
            <!-- 隐藏的文件选择框 -->
            <input ref="imageFileInputRef" type="file" accept="image/*" multiple style="display: none"
              @change="handleImageFileSelect" />
            <el-table :data="uploadedImages" height="205" border style="width: 100%" size="small" empty-text="等待上传图片">
              <el-table-column type="index" label="#" width="50"> </el-table-column>
              <el-table-column label="缩略图">
                <template #default="scope">
                  <div class="thumbnail-container">
                    <el-image :src="scope.row.url" :preview-src-list="getPreviewSrcList()" :initial-index="scope.$index"
                      fit="contain" preview-teleported class="thumbnail-image" />
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="70">
                <template #default="scope">
                  <el-button type="text" size="small" @click="removeImage(scope.$index)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <div style="display: flex; justify-content: space-between; margin-top: 5px">
              <el-button type="primary" size="small" style="width: 48%" @click="handleUploadClick">
                上传
              </el-button>
              <el-button type="primary" size="small" style="width: 48%" :loading="screenshotLoading"
                @click="handleScreenshotClick">
                截图
              </el-button>
            </div>
            <el-button type="danger" size="small" class="clear-all-btn" @click="clearAllImages">
              清空全部
            </el-button>
            <div style="display: flex; justify-content: space-between; margin-top: 5px">
              <el-button type="primary" size="small" style="width: 48%" @click="makeTransparentImage">
                制作透明图
              </el-button>
              <el-button type="danger" size="small" style="width: 48%" @click="clearTransparentImage">
                删除透明图
              </el-button>

            </div>
            <el-button type="primary" size="small" class="clear-all-btn" @click="handleSaveTransparentImage">
              保存透明图
            </el-button>
          </div>
          <!-- 透明图处理结果显示区域 -->
          <div 
            class="transparent-image-result"
            ref="transparentImageContainerRef"
            :style="{ cursor: transparentIsDragging ? 'grabbing' : 'default' }"
            @mousedown="handleTransparentImageMouseDown"
            @mousemove="handleTransparentImageMouseMove"
            @mouseup="handleTransparentImageMouseUp"
            @mouseleave="handleTransparentImageMouseLeave"
            @wheel="handleTransparentImageWheel"
          >
            <div v-if="transparentImageUrl" class="transparent-image-wrapper" :style="transparentImageWrapperStyle">
              <img 
                :src="transparentImageUrl" 
                alt="透明图处理结果" 
                class="transparent-result-image"
                ref="transparentImageRef"
                :style="transparentImageStyle"
                @load="handleTransparentImageLoad"
                draggable="false"
              />
            </div>
            <div v-else class="transparent-result-placeholder">
              透明图处理结果将显示在此处
            </div>
          </div>

        </div>

      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from "vue";
import { ZoomIn, Collection, Delete } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import { io } from "socket.io-client";

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
  currentDeviceId: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["remove-color", "clear-all-colors", "right-panel-screenshot-start", "right-panel-screenshot-end"]);

const magnifierCanvasRef = ref(null);
const deviationColors = ref([]);
const checkboxGroup2 = ref([]);
const processedImageUrl = ref(null);
const imageFileInputRef = ref(null);
const uploadedImages = ref([]);
const transparentImageUrl = ref(null);
const screenshotLoading = ref(false);
const isRightPanelScreenshotPending = ref(false); // 标记是否是右侧面板发起的截图
let deviceSocket = null;

// 透明图拖动和缩放相关
const transparentImageContainerRef = ref(null);
const transparentImageRef = ref(null);
const transparentImageScale = ref(1); // 缩放比例
const transparentImageTranslateX = ref(0); // X轴偏移
const transparentImageTranslateY = ref(0); // Y轴偏移
const transparentInitialScale = ref(1); // 初始缩放比例（用于重置）
const transparentInitialTranslateX = ref(0); // 初始X偏移
const transparentInitialTranslateY = ref(0); // 初始Y偏移
const transparentIsDragging = ref(false);
const transparentDragStartX = ref(0);
const transparentDragStartY = ref(0);
const transparentDragStartTranslateX = ref(0);
const transparentDragStartTranslateY = ref(0);

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

// 解析颜色容差字符串 (格式: 'C9C0B2-203040')
const parseColorTolerance = (colorToleranceStr) => {
  if (!colorToleranceStr || !colorToleranceStr.includes('-')) {
    return null;
  }

  try {
    const parts = colorToleranceStr.split('-');
    if (parts.length !== 2) {
      return null;
    }

    const baseColor = parts[0].trim().toUpperCase();
    const toleranceColor = parts[1].trim().toUpperCase();

    // 解析基准色 (6位16进制)
    if (baseColor.length !== 6 || toleranceColor.length !== 6) {
      return null;
    }

    const baseR = parseInt(baseColor.substring(0, 2), 16);
    const baseG = parseInt(baseColor.substring(2, 4), 16);
    const baseB = parseInt(baseColor.substring(4, 6), 16);

    const toleranceR = parseInt(toleranceColor.substring(0, 2), 16);
    const toleranceG = parseInt(toleranceColor.substring(2, 4), 16);
    const toleranceB = parseInt(toleranceColor.substring(4, 6), 16);

    return { baseR, baseG, baseB, toleranceR, toleranceG, toleranceB };
  } catch (error) {
    console.error('解析颜色容差参数失败:', colorToleranceStr, error);
    return null;
  }
};

// 检查颜色是否在容差范围内
const isColorInToleranceRange = (r, g, b, baseR, baseG, baseB, toleranceR, toleranceG, toleranceB) => {
  const rDiff = Math.abs(r - baseR);
  const gDiff = Math.abs(g - baseG);
  const bDiff = Math.abs(b - baseB);

  return rDiff <= toleranceR && gDiff <= toleranceG && bDiff <= toleranceB;
};

// 制作透明图
const makeTransparentImage = async () => {
  if (!uploadedImages.value || uploadedImages.value.length === 0) {
    ElMessage.warning('请先上传图片');
    return;
  }

  try {
    // 解析颜色容差参数
    const colorToleranceParamsList = [];
    if (checkboxGroup2.value && checkboxGroup2.value.length > 0) {
      for (const ct of checkboxGroup2.value) {
        const params = parseColorTolerance(ct);
        if (params) {
          colorToleranceParamsList.push(params);
        }
      }
    }

    // 使用颜色容差模式还是对比模式
    const useColorTolerance = colorToleranceParamsList.length > 0;

    // 获取裁剪配置
    let cropConfig = null;
    let expectedWidth = 0;
    let expectedHeight = 0;
    if (props.selectionRect && props.selectionRect.w > 0 && props.selectionRect.h > 0) {
      cropConfig = {
        enabled: true,
        x: props.selectionRect.x,
        y: props.selectionRect.y,
        w: props.selectionRect.w,
        h: props.selectionRect.h,
      };
      expectedWidth = cropConfig.w;
      expectedHeight = cropConfig.h;
    }

    let baseImageData = null;
    let baseWidth = 0;
    let baseHeight = 0;

    // 如果有结果图片,检查尺寸是否匹配当前裁剪配置
    if (transparentImageUrl.value) {
      const baseImg = new Image();
      baseImg.crossOrigin = 'anonymous';
      await new Promise((resolve, reject) => {
        baseImg.onload = () => {
          // 如果启用了裁剪,检查结果图片的尺寸是否匹配
          if (cropConfig && cropConfig.enabled) {
            if (baseImg.width === expectedWidth && baseImg.height === expectedHeight) {
              // 尺寸匹配,使用结果图片作为 base_image
              const canvas = document.createElement('canvas');
              const ctx = canvas.getContext('2d');
              canvas.width = baseImg.width;
              canvas.height = baseImg.height;
              ctx.drawImage(baseImg, 0, 0);
              baseImageData = ctx.getImageData(0, 0, baseImg.width, baseImg.height);
              baseWidth = baseImg.width;
              baseHeight = baseImg.height;
            } else {
              // 尺寸不匹配,忽略结果图片,重新开始处理
              console.log(`结果图片尺寸(${baseImg.width}x${baseImg.height})与当前裁剪配置(${expectedWidth}x${expectedHeight})不匹配,将重新开始处理`);
            }
          } else {
            // 没有裁剪配置,直接使用结果图片
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = baseImg.width;
            canvas.height = baseImg.height;
            ctx.drawImage(baseImg, 0, 0);
            baseImageData = ctx.getImageData(0, 0, baseImg.width, baseImg.height);
            baseWidth = baseImg.width;
            baseHeight = baseImg.height;
          }
          resolve();
        };
        baseImg.onerror = () => {
          // 加载失败,忽略结果图片
          resolve();
        };
        baseImg.src = transparentImageUrl.value;
      });
    }

    // 处理每张图片
    for (let i = 0; i < uploadedImages.value.length; i++) {
      const imageItem = uploadedImages.value[i];
      const img = new Image();
      img.crossOrigin = 'anonymous';

      await new Promise((resolve, reject) => {
        img.onload = () => {
          try {
            // 创建 canvas 用于处理
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            // 确定处理区域
            let startX = 0;
            let startY = 0;
            let width = img.width;
            let height = img.height;

            // 如果启用了裁剪,先对图片进行裁剪
            if (cropConfig && cropConfig.enabled) {
              startX = Math.max(0, Math.min(cropConfig.x, img.width - 1));
              startY = Math.max(0, Math.min(cropConfig.y, img.height - 1));
              width = Math.min(cropConfig.w, img.width - startX);
              height = Math.min(cropConfig.h, img.height - startY);
            }

            // 设置 canvas 尺寸
            canvas.width = width;
            canvas.height = height;

            // 绘制原始图片区域到 canvas
            ctx.drawImage(img, startX, startY, width, height, 0, 0, width, height);

            // 获取当前图片的像素数据
            const currentImageData = ctx.getImageData(0, 0, width, height);
            const currentData = currentImageData.data;

            // 如果是第一张图片且没有 base_image,使用当前图片作为基准
            if (baseImageData === null) {
              baseImageData = currentImageData;
              baseWidth = width;
              baseHeight = height;
            } else {
              // 确保尺寸一致
              if (baseWidth !== width || baseHeight !== height) {
                ElMessage.warning(`图片 ${i + 1} 尺寸不一致,跳过`);
                resolve();
                return;
              }

              // 获取基准图片的像素数据
              const baseData = baseImageData.data;

              // 遍历所有像素进行对比
              for (let y = 0; y < height; y++) {
                for (let x = 0; x < width; x++) {
                  const idx = (y * width + x) * 4;

                  // 获取基准图片像素 (r, g, b, a)
                  const baseR = baseData[idx];
                  const baseG = baseData[idx + 1];
                  const baseB = baseData[idx + 2];
                  const baseA = baseData[idx + 3];

                  // 如果基准图片这个点已经是透明的,就不用处理了
                  if (baseA === 0) {
                    continue;
                  }

                  // 获取当前图片像素
                  const currentR = currentData[idx];
                  const currentG = currentData[idx + 1];
                  const currentB = currentData[idx + 2];
                  const currentA = currentData[idx + 3];

                  let shouldSetTransparent = false;

                  if (useColorTolerance) {
                    // 使用颜色容差模式
                    // 检查当前图片的像素是否在任何一个颜色容差范围内
                    let inRange = false;
                    for (const params of colorToleranceParamsList) {
                      if (
                        isColorInToleranceRange(
                          currentR,
                          currentG,
                          currentB,
                          params.baseR,
                          params.baseG,
                          params.baseB,
                          params.toleranceR,
                          params.toleranceG,
                          params.toleranceB
                        )
                      ) {
                        inRange = true;
                        break;
                      }
                    }

                    // 如果不在任何一个范围内,设置为透明
                    if (!inRange) {
                      shouldSetTransparent = true;
                    }
                  } else {
                    // 使用对比模式
                    const rDiff = Math.abs(baseR - currentR);
                    const gDiff = Math.abs(baseG - currentG);
                    const bDiff = Math.abs(baseB - currentB);
                    const aDiff = Math.abs(baseA - currentA);

                    if (rDiff > 0 || gDiff > 0 || bDiff > 0 || aDiff > 0) {
                      shouldSetTransparent = true;
                    }
                  }

                  // 设置为透明
                  if (shouldSetTransparent) {
                    baseData[idx] = 0; // R
                    baseData[idx + 1] = 0; // G
                    baseData[idx + 2] = 0; // B
                    baseData[idx + 3] = 0; // A
                  }
                }
              }
            }

            resolve();
          } catch (error) {
            console.error(`处理图片 ${i + 1} 时出错:`, error);
            reject(error);
          }
        };
        img.onerror = () => {
          ElMessage.error(`加载图片 ${i + 1} 失败`);
          resolve(); // 继续处理下一张
        };
        img.src = imageItem.url;
      });
    }

    // 如果有更新,保存结果
    if (baseImageData) {
      const resultCanvas = document.createElement('canvas');
      const resultCtx = resultCanvas.getContext('2d');
      resultCanvas.width = baseWidth;
      resultCanvas.height = baseHeight;
      resultCtx.putImageData(baseImageData, 0, 0);

      // 转换为图片 URL
      transparentImageUrl.value = resultCanvas.toDataURL('image/png');
      ElMessage.success(`透明图制作完成,共处理 ${uploadedImages.value.length} 张图片`);
    }
  } catch (error) {
    console.error('制作透明图时出错:', error);
    ElMessage.error('制作透明图失败');
  }
};

// 清除透明图结果
const clearTransparentImage = () => {
  if (!transparentImageUrl.value) {
    ElMessage.warning('当前没有透明图结果');
    return;
  }
  transparentImageUrl.value = null;
  ElMessage.success('已清除透明图结果');
};

// 保存透明图
const handleSaveTransparentImage = async () => {
  if (!transparentImageUrl.value) {
    ElMessage.warning('没有可保存的透明图');
    return;
  }

  try {
    // 打开保存对话框
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const defaultName = `transparent_${timestamp}.png`;

    const result = await ipc.invoke(ipcApiRoute.openSaveDialog, {
      defaultName: defaultName
    });

    if (!result || !result.success || result.canceled) {
      return; // 用户取消或对话框失败
    }

    // 从 base64 URL 中提取 base64 字符串（去掉 data:image/png;base64, 前缀）
    let base64Data = transparentImageUrl.value;
    if (base64Data.includes(',')) {
      base64Data = base64Data.split(',')[1];
    }

    // 通过 IPC 调用主进程保存文件
    const saveResult = await ipc.invoke(ipcApiRoute.saveBase64Image, {
      filePath: result.filePath,
      imageData: base64Data
    });

    if (saveResult && saveResult.success) {
      ElMessage.success('透明图保存成功');
    } else {
      throw new Error(saveResult?.error || '保存失败');
    }
  } catch (error) {
    console.error('保存透明图失败:', error);
    ElMessage.error(`保存透明图失败: ${error.message || '未知错误'}`);
  }
};

// 初始化设备 Socket 连接
function initDeviceSocket() {
  if (deviceSocket) {
    return; // 已经连接过了
  }

  deviceSocket = io("ws://localhost:7070");

  deviceSocket.on("connect", () => {
    console.log("设备 Socket 连接成功 (RightPanel)");
  });

  deviceSocket.on("device-screenshot", (data) => {
    console.log("收到设备截图 (RightPanel):", data);
    // 只处理自己发起的截图请求
    if (isRightPanelScreenshotPending.value) {
      handleDeviceScreenshot(data);
    }
  });
}

// 处理设备截图结果
function handleDeviceScreenshot(data) {
  screenshotLoading.value = false;
  isRightPanelScreenshotPending.value = false; // 清除标志
  emit("right-panel-screenshot-end"); // 通知父组件截图结束

  if (!data || !data.success || !data.image) {
    ElMessage.error(data?.error || "获取截图失败");
    return;
  }

  const url = `data:image/png;base64,${data.image}`;
  const img = new Image();
  img.onload = () => {
    // 创建缩略图
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

    // 添加到图片列表
    uploadedImages.value.push({
      id: Date.now() + Math.random(), // 生成唯一ID
      url: url,
      thumbnail: thumbnail,
      file: null, // 截图没有文件对象
    });

    ElMessage.success("截图已添加到图片列表");
  };
  img.onerror = () => {
    ElMessage.error("图片加载失败");
  };
  img.src = url;
}

// 处理截图按钮点击
async function handleScreenshotClick() {
  // 检查是否有当前设备
  if (!props.currentDeviceId) {
    ElMessage.warning("请先连接设备");
    return;
  }

  screenshotLoading.value = true;
  isRightPanelScreenshotPending.value = true; // 设置标志，表示这是右侧面板发起的截图
  // 先同步设置父组件的标志，确保在 socket 事件到达前已设置
  emit("right-panel-screenshot-start"); // 通知父组件开始截图
  // 使用 nextTick 确保 emit 事件已处理
  await nextTick();
  try {
    await ipc.invoke(ipcApiRoute.sendToPython, {
      type: "capture_screenshot",
      source: "right-panel", // 添加来源标识
    });
    // 截图结果会通过 socket 事件返回，在 handleDeviceScreenshot 中处理
    // 设置超时，防止标志一直存在
    setTimeout(() => {
      if (isRightPanelScreenshotPending.value) {
        isRightPanelScreenshotPending.value = false;
        screenshotLoading.value = false;
        emit("right-panel-screenshot-end"); // 通知父组件截图结束
      }
    }, 10000); // 10秒超时
  } catch (error) {
    console.error("截图失败:", error);
    ElMessage.error(`截图失败: ${error.message || "未知错误"}`);
    screenshotLoading.value = false;
    isRightPanelScreenshotPending.value = false; // 清除标志
    emit("right-panel-screenshot-end"); // 通知父组件截图结束
  }
}

// 暴露放大镜 canvas 给父组件，用于绘制
// 同时暴露截图状态，让父组件可以检查
defineExpose({
  getMagnifierCanvas: () => magnifierCanvasRef.value,
  get isRightPanelScreenshotPending() {
    return isRightPanelScreenshotPending.value;
  },
});

// 透明图包装器样式（用于定位）
const transparentImageWrapperStyle = computed(() => {
  return {
    transform: `translate(${transparentImageTranslateX.value}px, ${transparentImageTranslateY.value}px)`,
    position: "absolute",
    top: 0,
    left: 0,
    cursor: transparentIsDragging.value ? "grabbing" : "default",
  };
});

// 透明图样式（用于缩放）
const transparentImageStyle = computed(() => {
  return {
    transform: `scale(${transparentImageScale.value})`,
    transformOrigin: "top left",
    display: "block",
  };
});

// 透明图加载完成
function handleTransparentImageLoad() {
  if (transparentImageRef.value && transparentImageContainerRef.value) {
    nextTick(() => {
      calculateTransparentInitialTransform();
    });
  }
}

// 计算透明图初始变换（居中显示）
function calculateTransparentInitialTransform() {
  if (!transparentImageRef.value || !transparentImageContainerRef.value) return;

  const containerRect = transparentImageContainerRef.value.getBoundingClientRect();
  const imgWidth = transparentImageRef.value.naturalWidth;
  const imgHeight = transparentImageRef.value.naturalHeight;

  // 计算适合容器的缩放比例（保持宽高比，最大边占满）
  const scaleX = containerRect.width / imgWidth;
  const scaleY = containerRect.height / imgHeight;
  const scale = Math.min(scaleX, scaleY, 1); // 不超过原始大小

  transparentImageScale.value = scale;
  transparentInitialScale.value = scale;

  // 居中显示
  const scaledWidth = imgWidth * scale;
  const scaledHeight = imgHeight * scale;
  transparentImageTranslateX.value = (containerRect.width - scaledWidth) / 2;
  transparentImageTranslateY.value = (containerRect.height - scaledHeight) / 2;
  transparentInitialTranslateX.value = transparentImageTranslateX.value;
  transparentInitialTranslateY.value = transparentImageTranslateY.value;
}

// 透明图鼠标按下
function handleTransparentImageMouseDown(event) {
  if (!transparentImageUrl.value || !transparentImageRef.value) return;
  
  // 仅响应左键
  if (event.button !== 0) return;

  // 检查是否按住了Ctrl键，如果是则允许拖动
  if (event.ctrlKey || event.metaKey) {
    transparentIsDragging.value = true;
    transparentDragStartX.value = event.clientX;
    transparentDragStartY.value = event.clientY;
    transparentDragStartTranslateX.value = transparentImageTranslateX.value;
    transparentDragStartTranslateY.value = transparentImageTranslateY.value;
    event.preventDefault();
    return;
  }
  
  // 如果没有按住Ctrl，也允许拖动（方便操作）
  transparentIsDragging.value = true;
  transparentDragStartX.value = event.clientX;
  transparentDragStartY.value = event.clientY;
  transparentDragStartTranslateX.value = transparentImageTranslateX.value;
  transparentDragStartTranslateY.value = transparentImageTranslateY.value;
}

// 透明图鼠标移动
function handleTransparentImageMouseMove(event) {
  if (!transparentImageUrl.value || !transparentImageRef.value) return;

  // 如果正在拖动图片
  if (transparentIsDragging.value) {
    const deltaX = event.clientX - transparentDragStartX.value;
    const deltaY = event.clientY - transparentDragStartY.value;
    transparentImageTranslateX.value = transparentDragStartTranslateX.value + deltaX;
    transparentImageTranslateY.value = transparentDragStartTranslateY.value + deltaY;
  }
}

// 透明图鼠标抬起
function handleTransparentImageMouseUp(event) {
  transparentIsDragging.value = false;
}

// 透明图鼠标离开
function handleTransparentImageMouseLeave(event) {
  transparentIsDragging.value = false;
}

// 透明图滚轮缩放（Ctrl + 滚轮）
function handleTransparentImageWheel(event) {
  if (!transparentImageUrl.value || !transparentImageRef.value || !transparentImageContainerRef.value) return;

  // 检查是否按住了Ctrl键
  if (!event.ctrlKey && !event.metaKey) {
    return; // 没有按住Ctrl，不处理缩放
  }

  event.preventDefault();

  // 获取容器和图片的位置信息
  const containerRect = transparentImageContainerRef.value.getBoundingClientRect();
  const mouseX = event.clientX - containerRect.left;
  const mouseY = event.clientY - containerRect.top;

  // 计算鼠标在图片上的相对位置（考虑当前缩放和偏移）
  const imgRect = transparentImageRef.value.getBoundingClientRect();
  const imgX = (mouseX - transparentImageTranslateX.value) / transparentImageScale.value;
  const imgY = (mouseY - transparentImageTranslateY.value) / transparentImageScale.value;

  // 计算缩放增量
  const zoomFactor = event.deltaY > 0 ? 0.9 : 1.1;
  const newScale = Math.max(0.1, Math.min(10, transparentImageScale.value * zoomFactor));

  // 计算新的偏移，使鼠标指向的图片位置保持不变
  const newTranslateX = mouseX - imgX * newScale;
  const newTranslateY = mouseY - imgY * newScale;

  transparentImageScale.value = newScale;
  transparentImageTranslateX.value = newTranslateX;
  transparentImageTranslateY.value = newTranslateY;
}

// 监听透明图 URL 变化，重置缩放和位置
watch(transparentImageUrl, (newUrl) => {
  if (newUrl) {
    // 重置缩放和位置
    transparentImageScale.value = 1;
    transparentImageTranslateX.value = 0;
    transparentImageTranslateY.value = 0;
    transparentInitialScale.value = 1;
    transparentInitialTranslateX.value = 0;
    transparentInitialTranslateY.value = 0;
    // 等待图片加载后重新计算
    nextTick(() => {
      if (transparentImageRef.value) {
        transparentImageRef.value.onload = () => {
          calculateTransparentInitialTransform();
        };
        // 如果图片已经加载完成，直接计算
        if (transparentImageRef.value.complete) {
          calculateTransparentInitialTransform();
        }
      }
    });
  }
});

// 组件挂载时初始化 socket
onMounted(() => {
  initDeviceSocket();
});

// 组件卸载时断开 socket
onUnmounted(() => {
  if (deviceSocket) {
    deviceSocket.disconnect();
    deviceSocket = null;
  }
});
</script>

<style scoped>
.el-button+.el-button {
  margin-left: 0;
}

.el-checkbox {
  margin-right: 0;
}

.right-panel {
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex-shrink: 0;
  padding: 0 5px;
  width: 460px;
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
  margin-top: 5px;
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

/* 透明图处理结果显示区域 */
.transparent-image-result {
  margin-top: 5px;
  flex: 1;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 深色棋盘格背景，用于显示透明区域 */
  background: #1a1a2e;
  background-image: linear-gradient(45deg, #2a2a3e 25%, transparent 25%),
    linear-gradient(-45deg, #2a2a3e 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, #2a2a3e 75%),
    linear-gradient(-45deg, transparent 75%, #2a2a3e 75%);
  background-size: 16px 16px;
  background-position: 0 0, 0 8px, 8px -8px, -8px 0px;
  position: relative;
  user-select: none;
}

.transparent-image-wrapper {
  display: inline-block;
  position: relative;
  user-select: none;
}

.transparent-result-image {
  width: auto;
  height: auto;
  max-width: none;
  max-height: none;
  object-fit: contain;
  display: block;
  user-select: none;
  pointer-events: none;
}

.transparent-result-placeholder {
  color: #909399;
  font-size: 12px;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
</style>
