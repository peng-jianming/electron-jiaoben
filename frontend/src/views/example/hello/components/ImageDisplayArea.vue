<template>
  <div 
    class="image-display-area"
    ref="containerRef"
    :style="{ cursor: isDragging ? 'grabbing' : 'default' }"
    @mousedown="handleMouseDown"
    @mousemove="handleMouseMove"
    @mouseup="handleMouseUp"
    @mouseleave="handleMouseLeave"
    @wheel="handleWheel"
  >
    <div v-if="imageUrl" class="image-wrapper" :style="wrapperStyle">
      <img 
        :src="imageUrl" 
        :alt="alt"
        class="display-image"
        ref="imageRef"
        :style="imageStyle"
        @load="handleImageLoad"
        draggable="false"
      />
    </div>
    <div v-else class="placeholder">
      {{ placeholderText }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from "vue";

const props = defineProps({
  imageUrl: {
    type: String,
    default: null,
  },
  alt: {
    type: String,
    default: "图片",
  },
  placeholderText: {
    type: String,
    default: "图片将显示在此处",
  },
});

const containerRef = ref(null);
const imageRef = ref(null);
const scale = ref(1);
const translateX = ref(0);
const translateY = ref(0);
const initialScale = ref(1);
const initialTranslateX = ref(0);
const initialTranslateY = ref(0);
const isDragging = ref(false);
const dragStartX = ref(0);
const dragStartY = ref(0);
const dragStartTranslateX = ref(0);
const dragStartTranslateY = ref(0);

// 包装器样式（用于定位）
const wrapperStyle = computed(() => {
  return {
    transform: `translate(${translateX.value}px, ${translateY.value}px)`,
    position: "absolute",
    top: 0,
    left: 0,
    cursor: isDragging.value ? "grabbing" : "default",
  };
});

// 图片样式（用于缩放）
const imageStyle = computed(() => {
  return {
    transform: `scale(${scale.value})`,
    transformOrigin: "top left",
    display: "block",
  };
});

// 图片加载完成
function handleImageLoad() {
  if (imageRef.value && containerRef.value) {
    nextTick(() => {
      calculateInitialTransform();
    });
  }
}

// 计算初始变换（居中显示）
function calculateInitialTransform() {
  if (!imageRef.value || !containerRef.value) return;

  const containerRect = containerRef.value.getBoundingClientRect();
  const imgWidth = imageRef.value.naturalWidth;
  const imgHeight = imageRef.value.naturalHeight;

  // 计算适合容器的缩放比例（保持宽高比，最大边占满）
  const scaleX = containerRect.width / imgWidth;
  const scaleY = containerRect.height / imgHeight;
  const newScale = Math.min(scaleX, scaleY, 1); // 不超过原始大小

  scale.value = newScale;
  initialScale.value = newScale;

  // 居中显示
  const scaledWidth = imgWidth * newScale;
  const scaledHeight = imgHeight * newScale;
  translateX.value = (containerRect.width - scaledWidth) / 2;
  translateY.value = (containerRect.height - scaledHeight) / 2;
  initialTranslateX.value = translateX.value;
  initialTranslateY.value = translateY.value;
}

// 鼠标按下
function handleMouseDown(event) {
  if (!props.imageUrl || !imageRef.value) return;
  
  // 仅响应左键
  if (event.button !== 0) return;

  // 检查是否按住了Ctrl键，如果是则允许拖动
  if (event.ctrlKey || event.metaKey) {
    isDragging.value = true;
    dragStartX.value = event.clientX;
    dragStartY.value = event.clientY;
    dragStartTranslateX.value = translateX.value;
    dragStartTranslateY.value = translateY.value;
    event.preventDefault();
    return;
  }
  
  // 如果没有按住Ctrl，也允许拖动（方便操作）
  isDragging.value = true;
  dragStartX.value = event.clientX;
  dragStartY.value = event.clientY;
  dragStartTranslateX.value = translateX.value;
  dragStartTranslateY.value = translateY.value;
}

// 鼠标移动
function handleMouseMove(event) {
  if (!props.imageUrl || !imageRef.value) return;

  // 如果正在拖动图片
  if (isDragging.value) {
    const deltaX = event.clientX - dragStartX.value;
    const deltaY = event.clientY - dragStartY.value;
    translateX.value = dragStartTranslateX.value + deltaX;
    translateY.value = dragStartTranslateY.value + deltaY;
  }
}

// 鼠标抬起
function handleMouseUp(event) {
  isDragging.value = false;
}

// 鼠标离开
function handleMouseLeave(event) {
  isDragging.value = false;
}

// 滚轮缩放（Ctrl + 滚轮）
function handleWheel(event) {
  if (!props.imageUrl || !imageRef.value || !containerRef.value) return;

  // 检查是否按住了Ctrl键
  if (!event.ctrlKey && !event.metaKey) {
    return; // 没有按住Ctrl，不处理缩放
  }

  event.preventDefault();

  // 获取容器和图片的位置信息
  const containerRect = containerRef.value.getBoundingClientRect();
  const mouseX = event.clientX - containerRect.left;
  const mouseY = event.clientY - containerRect.top;

  // 计算鼠标在图片上的相对位置（考虑当前缩放和偏移）
  const imgX = (mouseX - translateX.value) / scale.value;
  const imgY = (mouseY - translateY.value) / scale.value;

  // 计算缩放增量
  const zoomFactor = event.deltaY > 0 ? 0.9 : 1.1;
  const newScale = Math.max(0.1, Math.min(10, scale.value * zoomFactor));

  // 计算新的偏移，使鼠标指向的图片位置保持不变
  const newTranslateX = mouseX - imgX * newScale;
  const newTranslateY = mouseY - imgY * newScale;

  scale.value = newScale;
  translateX.value = newTranslateX;
  translateY.value = newTranslateY;
}

// 监听图片 URL 变化，重置缩放和位置
watch(() => props.imageUrl, (newUrl) => {
  if (newUrl) {
    // 重置缩放和位置
    scale.value = 1;
    translateX.value = 0;
    translateY.value = 0;
    initialScale.value = 1;
    initialTranslateX.value = 0;
    initialTranslateY.value = 0;
    // 等待图片加载后重新计算
    nextTick(() => {
      if (imageRef.value) {
        imageRef.value.onload = () => {
          calculateInitialTransform();
        };
        // 如果图片已经加载完成，直接计算
        if (imageRef.value.complete) {
          calculateInitialTransform();
        }
      }
    });
  }
});
</script>

<style scoped>
.image-display-area {
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

.image-wrapper {
  display: inline-block;
  position: relative;
  user-select: none;
}

.display-image {
  width: auto;
  height: auto;
  max-width: none;
  max-height: none;
  object-fit: contain;
  display: block;
  user-select: none;
  pointer-events: none;
}

.placeholder {
  color: #909399;
  font-size: 12px;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
</style>

