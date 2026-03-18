<template>
  <div class="flood-fill-wrapper">
    <div class="panel-header">
      <h3 class="panel-title">洪水填充</h3>
    </div>

    <div class="panel-body">
      <div class="layout">
        <!-- 左侧：图片与交互 -->
        <div class="left-pane">
          <div class="toolbar">
            <el-button type="primary" size="small" @click="triggerUpload">
              上传图片
            </el-button>
            <el-button
              size="small"
              @click="useFromProcessing"
              :disabled="!canUseProcessingImage"
            >
              使用图像处理结果
            </el-button>

            <el-button
              type="success"
              size="small"
              :disabled="!hasImage || !hasSeedPoint || floodFillStore.isFilling"
              :loading="floodFillStore.isFilling"
              @click="handleStartFloodFill"
            >
              开始填充
            </el-button>

            <el-button
              size="small"
              :disabled="!hasImage || !hasSeedPoint"
              @click="handlePlayAnimation"
            >
              播放动画
            </el-button>
          </div>

          <!-- 隐藏的文件选择器 -->
          <input
            ref="fileInputRef"
            type="file"
            accept="image/*"
            style="display: none"
            @change="onFileChange"
          />

          <div class="image-area" v-if="hasImage">
            <div class="image-container" ref="imageContainerRef">
              <img
                v-if="displayImageSrc"
                :src="displayImageSrc"
                class="image"
                ref="imageRef"
                @load="onImageLoad"
                @click="onImageClick"
              />
              <div v-else class="image-placeholder">正在加载图片...</div>

              <div v-if="hasSeedPoint" class="seed-point-indicator" :style="seedPointStyle"></div>
            </div>

            <div class="tips">
              <p>1. 在图片上点击选择起始点（需要填充的区域内）</p>
              <p>2. 点击「开始填充」查看结果</p>
              <p>3. 点击「播放动画」在新窗口中查看填充过程</p>
            </div>
          </div>

          <div v-else class="empty-tip">
            请先上传图片，或从图像处理模块中选择结果图片。
          </div>
        </div>

        <!-- 右侧：结果预览（与说明） -->
        <div class="right-pane">
          <div class="info-card">
            <h4>当前状态</h4>
            <ul>
              <li>
                图片：<span>{{ hasImage ? "已就绪" : "未选择" }}</span>
              </li>
              <li>
                起始点：
                <span v-if="hasSeedPoint">
                  ({{ floodFillStore.seedPoint.x }}, {{ floodFillStore.seedPoint.y }})
                </span>
                <span v-else>未选择</span>
              </li>
              <li>
                填充状态：
                <span>
                  {{ floodFillStore.isFilling ? "填充中..." : "空闲" }}
                </span>
              </li>
            </ul>
          </div>

          <div class="info-card">
            <h4>说明</h4>
            <p>可以在图像处理中先做二值化、膨胀、腐蚀等操作，让需要填充的区域闭合后，再在此处执行洪水填充。</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { ElMessage } from "element-plus";
import { storeToRefs } from "pinia";
import { useImageProcessingStore } from "@/stores/imageProcessing";
import { useFloodFillStore } from "@/stores/floodFill";

const imageProcessingStore = useImageProcessingStore();
const floodFillStore = useFloodFillStore();

const { currentImageId } = storeToRefs(imageProcessingStore);

const fileInputRef = ref(null);
const imageContainerRef = ref(null);
const imageRef = ref(null);

const displayImageSrc = computed(() => floodFillStore.displayImageSrc);
const hasSeedPoint = computed(() => floodFillStore.hasSeedPoint);
const hasImage = computed(() => floodFillStore.hasImage);

const canUseProcessingImage = computed(() => !!currentImageId.value);

const seedPointStyle = computed(() => {
  if (!imageContainerRef.value || !imageRef.value || !hasSeedPoint.value) return {};

  const containerRect = imageContainerRef.value.getBoundingClientRect();
  const imgRect = imageRef.value.getBoundingClientRect();

  if (!containerRect.width || !containerRect.height) return {};
  if (!imgRect.width || !imgRect.height) return {};

  if (!floodFillStore.imageNaturalWidth || !floodFillStore.imageNaturalHeight) {
    return {};
  }

  const scaleX = imgRect.width / floodFillStore.imageNaturalWidth;
  const scaleY = imgRect.height / floodFillStore.imageNaturalHeight;

  const imgOffsetLeft = imgRect.left - containerRect.left;
  const imgOffsetTop = imgRect.top - containerRect.top;

  const left = imgOffsetLeft + floodFillStore.seedPoint.x * scaleX;
  const top = imgOffsetTop + floodFillStore.seedPoint.y * scaleY;

  return {
    left: `${left}px`,
    top: `${top}px`,
  };
});

const triggerUpload = () => {
  fileInputRef.value && fileInputRef.value.click();
};

const onFileChange = (event) => {
  const file = event.target.files && event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    const preview = e.target.result;
    floodFillStore.handleFloodImageUpload({
      path: file.path || "",
      preview,
    });
  };
  reader.readAsDataURL(file);

  // 重置 input，方便连续选择相同文件
  event.target.value = "";
};

const useFromProcessing = () => {
  if (!currentImageId.value) {
    ElMessage.warning("当前没有图像处理结果可用");
    return;
  }
  floodFillStore.useImageFromProcessing();
};

const onImageLoad = (event) => {
  const img = event.target;
  const naturalWidth = img.naturalWidth;
  const naturalHeight = img.naturalHeight;
  floodFillStore.setImageNaturalSize(naturalWidth, naturalHeight);
};

const onImageClick = (event) => {
  const img = event.target;
  const rect = img.getBoundingClientRect();

  const offsetX = event.clientX - rect.left;
  const offsetY = event.clientY - rect.top;

  floodFillStore.setSeedPointByClientPoint({
    offsetX,
    offsetY,
    clientWidth: rect.width,
    clientHeight: rect.height,
  });
};

const handleStartFloodFill = () => {
  if (!hasImage.value) {
    ElMessage.warning("请先选择或上传图片");
    return;
  }
  if (!hasSeedPoint.value) {
    ElMessage.warning("请先在图片上点击选取起始点");
    return;
  }
  floodFillStore.startFloodFill();
};

const handlePlayAnimation = () => {
  if (!hasImage.value || !hasSeedPoint.value) {
    ElMessage.warning("请先选择图片并选取起始点");
    return;
  }
  floodFillStore.playFloodFillAnimation(0);
};
</script>

<style scoped lang="less">
.flood-fill-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  padding: 10px 16px;
  border-bottom: 1px solid #e2e8f0;
}

.panel-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
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
  flex: 2;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.right-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.image-area {
  flex: 1;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.image-container {
  flex: 1;
  background: #0f172a;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image {
  max-width: 100%;
  max-height: 100%;
  cursor: crosshair;
  user-select: none;
}

.image-placeholder {
  color: #94a3b8;
  font-size: 13px;
}

.seed-point-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid #22c55e;
  background: rgba(34, 197, 94, 0.4);
  position: absolute;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.7);
}

.tips {
  font-size: 12px;
  color: #64748b;
  line-height: 1.6;
}

.empty-tip {
  flex: 1;
  border-radius: 8px;
  border: 1px dashed #cbd5f5;
  background: #eff6ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1d4ed8;
  font-size: 13px;
}

.info-card {
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  padding: 10px 12px;
}

.info-card h4 {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.info-card ul {
  margin: 0;
  padding-left: 16px;
  font-size: 12px;
  color: #475569;
}
</style>
