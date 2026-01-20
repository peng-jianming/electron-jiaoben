<template>
  <div style="display: flex; flex-direction: column;height: 590px;">
    <div>
      <ImageUploadList 
        :images="uploadedImages"
        :screenshot-loading="screenshotLoading"
        @upload-click="handleUploadClick"
        @remove-image="handleRemoveImage"
        @clear-all-images="handleClearAllImages"
        @screenshot-click="$emit('screenshot-click')"
        @images-updated="handleImagesUpdated"
      />
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
    <div class="result-section">
      <el-image :src="transparentImageUrl" :preview-src-list="[transparentImageUrl]" fit="contain" preview-teleported
      style="height: 100%; width: 100%;">
        <template #placeholder>
          <div style="display: flex;justify-content: center;align-items: center;height: 100%;width: 100%;">透明图处理结果将显示在此处
          </div>
        </template>
      </el-image>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from "vue";
import { ElMessage } from "element-plus";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import ImageUploadList from "../lists/ImageUploadList.vue";
import ImageDisplayArea from "../common/ImageDisplayArea.vue";

const props = defineProps({
  uploadedImages: {
    type: Array,
    default: () => [],
  },
  screenshotLoading: {
    type: Boolean,
    default: false,
  },
  selectedDeviations: {
    type: Array,
    default: () => [],
  },
  selectionRect: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["screenshot-click", "images-updated", "remove-image", "clear-all-images"]);

const transparentImageUrl = ref(null);

// 处理图片更新
const handleImagesUpdated = (newImages) => {
  emit("images-updated", newImages);
};

// 监听图片列表变化，自动调用制作透明图
let isMakingTransparent = false; // 防止重复调用

watch(
  () => props.uploadedImages?.length || 0,
  async (newLength, oldLength) => {
    // 只有当图片数量增加时才自动调用（避免删除图片时也调用）
    const oldLen = oldLength ?? 0;
    if (newLength > 0 && newLength > oldLen) {
      if (!isMakingTransparent) {
        isMakingTransparent = true;
        // 等待一下，确保图片已添加到列表中
        await nextTick();
        // 再等待一下，确保图片已加载
        await new Promise(resolve => setTimeout(resolve, 100));
        try {
          await makeTransparentImage(true); // 静默模式，不显示提示
        } catch (error) {
          console.error('自动制作透明图失败:', error);
        } finally {
          isMakingTransparent = false;
        }
      }
    }
  },
  { immediate: false }
);

// 删除图片
const handleRemoveImage = (index) => {
  emit("remove-image", index);
};

// 清空所有图片
const handleClearAllImages = () => {
  emit("clear-all-images");
};

// 处理上传按钮点击（这个事件实际上由 ImageUploadList 内部处理）
const handleUploadClick = () => {
  // 这个事件由 ImageUploadList 内部处理，这里不需要做任何事
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
const makeTransparentImage = async (silent = false) => {
  if (!props.uploadedImages || props.uploadedImages.length === 0) {
    if (!silent) {
      ElMessage.warning('请先上传图片');
    }
    return;
  }

  try {
    // 解析颜色容差参数
    const colorToleranceParamsList = [];
    if (props.selectedDeviations && props.selectedDeviations.length > 0) {
      for (const ct of props.selectedDeviations) {
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
    for (let i = 0; i < props.uploadedImages.length; i++) {
      const imageItem = props.uploadedImages[i];
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
      // 只有在非静默模式下才显示成功提示
      if (!silent) {
        ElMessage.success(`透明图制作完成,共处理 ${props.uploadedImages.length} 张图片`);
      }
    }
  } catch (error) {
    console.error('制作透明图时出错:', error);
    if (!silent) {
      ElMessage.error('制作透明图失败');
    }
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

// 暴露透明图 URL 供外部访问
defineExpose({
  getTransparentImageUrl: () => transparentImageUrl.value,
  makeTransparentImage, // 暴露制作透明图方法，供外部调用
});
</script>

<style scoped>
.clear-all-btn {
  width: 100%;
  margin-top: 5px;
}
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

