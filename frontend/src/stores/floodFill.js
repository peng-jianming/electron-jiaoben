import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useImageProcessingStore } from '@/stores/imageProcessing';
import { getMatchSocket } from '@/utils/matchSocket';

export const useFloodFillStore = defineStore('floodFill', () => {
  const imageProcessingStore = useImageProcessingStore();

  // 洪水填充输入图：独立于图像处理模块
  // - source: 'flood' 表示洪水填充自己上传的缓存
  // - source: 'processing' 表示“使用图像处理结果”作为输入
  const inputImage = ref({ source: 'flood', id: '' });
  // 洪水填充输入图的本地预览（仅当 source='flood' 且刚上传时使用）
  const floodInputPreview = ref('');
  // 起始点
  const seedPoint = ref({ x: null, y: null });
  // 原始图片在后端中的原始尺寸
  const imageNaturalWidth = ref(0);
  const imageNaturalHeight = ref(0);

  // 结果预览
  const floodResultImage = ref('');
  const lastErrorMessage = ref('');
  const pendingUploadResolvers = ref({});

  // 状态
  const isFilling = ref(false);
  const isAnimating = ref(false);

  // 输入图展示：不包含结果图（由组件分开展示）
  const inputDisplayImageSrc = computed(() => {
    if (inputImage.value.source === 'flood') {
      return floodInputPreview.value || '';
    }
    return imageProcessingStore.displayImageSrc || '';
  });

  const resultDisplayImageSrc = computed(() => {
    return floodResultImage.value || '';
  });

  const hasSeedPoint = computed(() => {
    return (
      seedPoint.value &&
      seedPoint.value.x !== null &&
      seedPoint.value.y !== null
    );
  });

  const hasImage = computed(() => {
    const hasInputId = !!(inputImage.value && inputImage.value.id);
    if (inputImage.value.source === 'processing') {
      return !!(imageProcessingStore.currentImageId || inputDisplayImageSrc.value);
    }
    return !!(hasInputId || floodInputPreview.value || inputDisplayImageSrc.value);
  });

  const sendToBackend = (类型, extra = {}) => {
    // 复用图像处理 store 里的统一发送方法
    return imageProcessingStore.sendToBackend(类型, extra);
  };

  // 1. 从图像处理模块拿当前结果图像作为洪水填充输入
  const useImageFromProcessing = () => {
    if (!imageProcessingStore.currentImageId) return;
    inputImage.value = { source: 'processing', id: imageProcessingStore.currentImageId };
    floodResultImage.value = '';
    floodInputPreview.value = '';
    seedPoint.value = { x: null, y: null };
  };

  // 2. 洪水填充独立上传图片（不影响图像处理模块）
  const handleFloodImageUpload = (payload) => {
    const safePayload = payload || {};
    const path = safePayload.path || '';
    const preview = safePayload.preview || '';
    if (!path) return;

    // 先本地预览，提升体验
    floodInputPreview.value = preview || '';
    inputImage.value = { source: 'flood', id: '' };
    floodResultImage.value = '';
    seedPoint.value = { x: null, y: null };

    // 通知后端做洪水填充专用缓存
    sendToBackend('洪水填充上传缓存', {
      图片路径: path,
    });
  };

  // 后端缓存完成后回传 flood-image-uploaded
  const handleFloodImageUploaded = (payload) => {
    const data = payload || {};
    if (data && typeof data.imageId === 'string') {
      inputImage.value = { source: 'flood', id: data.imageId };
    }
    if (data && typeof data.preview === 'string') {
      floodInputPreview.value = data.preview;
    }

    const requestId = data && data.requestId;
    if (requestId && pendingUploadResolvers.value && pendingUploadResolvers.value[requestId]) {
      try {
        pendingUploadResolvers.value[requestId]({ imageId: data.imageId, preview: data.preview });
      } finally {
        delete pendingUploadResolvers.value[requestId];
      }
    }
  };

  const uploadEditedImageDataUrl = async (dataUrl) => {
    if (!dataUrl) return null;

    const requestId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const p = new Promise((resolve) => {
      pendingUploadResolvers.value[requestId] = resolve;
    });

    sendToBackend('洪水填充上传base64缓存', {
      dataUrl,
      requestId,
    });

    const res = await p;
    if (res && res.imageId) {
      inputImage.value = { source: 'flood', id: res.imageId };
    }
    return (res && res.imageId) || null;
  };

  // 由前端图片组件在 onLoad 时设置原始尺寸
  const setImageNaturalSize = (width, height) => {
    imageNaturalWidth.value = width || 0;
    imageNaturalHeight.value = height || 0;
  };

  // 将前端点击的相对坐标（相对于显示区域）换算为原图坐标
  const setSeedPointByClientPoint = ({
    offsetX,
    offsetY,
    clientWidth,
    clientHeight,
  }) => {
    if (!imageNaturalWidth.value || !imageNaturalHeight.value) return;
    if (!clientWidth || !clientHeight) return;

    const scaleX = imageNaturalWidth.value / clientWidth;
    const scaleY = imageNaturalHeight.value / clientHeight;

    const x = Math.round(offsetX * scaleX);
    const y = Math.round(offsetY * scaleY);

    seedPoint.value = { x, y };
  };

  // 3. 触发洪水填充
  const startFloodFill = () => {
    const imageId = inputImage.value && inputImage.value.id;
    if (!imageId) return;
    if (!hasSeedPoint.value) return;

    isFilling.value = true;
    floodResultImage.value = '';
    lastErrorMessage.value = '';

    sendToBackend('洪水填充', {
      imageId,
      imageSource: (inputImage.value && inputImage.value.source) || 'flood',
      x: seedPoint.value.x,
      y: seedPoint.value.y,
    });
  };

  // 4. 播放洪水填充动画（由后端在新窗口中展示）
  const playFloodFillAnimation = (stepIndex = 0) => {
    const imageId = inputImage.value && inputImage.value.id;
    if (!imageId) return;
    if (!hasSeedPoint.value) return;
    isAnimating.value = true;

    sendToBackend('洪水填充动画', {
      imageId,
      imageSource: (inputImage.value && inputImage.value.source) || 'flood',
      x: seedPoint.value.x,
      y: seedPoint.value.y,
      stepIndex,
    });
  };

  // 供外部在 socket 回调中设置最终结果
  const handleFloodFillResult = (payload) => {
    const data = payload || {};
    const img = data.image || '';
    if (typeof img === 'string') {
      floodResultImage.value = img;
    }
    lastErrorMessage.value = '';
    isFilling.value = false;
  };

  const handleFloodFillError = (payload) => {
    const data = payload || {};
    const message = data.message || '洪水填充失败';
    lastErrorMessage.value = String(message);
    isFilling.value = false;
  };

  const markAnimationStopped = () => {
    isAnimating.value = false;
  };


  const socket = getMatchSocket();
  // 洪水填充上传图片回传（与图像处理的 image-uploaded 隔离）
  socket.on('flood-image-uploaded', (data) => {
    handleFloodImageUploaded(data || {});
  });

  // 洪水填充结果预览
  socket.on('flood-fill-result', (data) => {
    handleFloodFillResult(data || {});
  });

  // 洪水填充失败（用于解除 loading）
  socket.on('flood-fill-error', (data) => {
    handleFloodFillError(data || {});
  });

  return {
    // state
    inputImage,
    floodInputPreview,
    seedPoint,
    imageNaturalWidth,
    imageNaturalHeight,
    floodResultImage,
    lastErrorMessage,
    isFilling,
    isAnimating,
    inputDisplayImageSrc,
    resultDisplayImageSrc,
    hasSeedPoint,
    hasImage,
    // actions
    useImageFromProcessing,
    handleFloodImageUpload,
    handleFloodImageUploaded,
    uploadEditedImageDataUrl,
    setImageNaturalSize,
    setSeedPointByClientPoint,
    startFloodFill,
    playFloodFillAnimation,
    handleFloodFillResult,
    handleFloodFillError,
    markAnimationStopped,
  };
});

