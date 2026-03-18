import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { io } from 'socket.io-client';
import { ipc } from '@/utils/ipcRenderer';
import { ipcApiRoute } from '@/api';

export const useImageProcessingStore = defineStore('imageProcessing', () => {
  const isConnected = ref(false);
  const isBackendReady = ref(false);
  const imageProcessingResult = ref('');
  const colorFilterPreview = ref('');
  const imageUploadedInfo = ref({ imageId: '', preview: '' });

  // 流水线步骤（UI 和请求共用）
  const pipelineSteps = ref([]);

  // 步骤可选项模板
  const pipelineStepOptions = ref([
    {
      type: '二值化',
      defaultParams: {
        threshold: 127,
      },
    },
    {
      type: '颜色过滤',
      defaultParams: {},
    },
  ]);

  // 统一的展示用图片：优先显示处理结果，其次是上传预览
  const displayImageSrc = computed(() => {
    if (imageProcessingResult.value) {
      return imageProcessingResult.value;
    }
    if (imageUploadedInfo.value && imageUploadedInfo.value.preview) {
      return imageUploadedInfo.value.preview;
    }
    return '';
  });

  let matchSocket = null;

  const initMatchSocket = () => {
    return new Promise((resolve, reject) => {
      if (matchSocket) {
        resolve();
        return;
      }

      matchSocket = io('ws://localhost:7075');

      matchSocket.on('connect', () => {
        // 连接成功后，通知 electron 启动后端服务
        isConnected.value = true;
        ipc.invoke(ipcApiRoute.启动后端服务);
      });

      matchSocket.on('backend-ready', () => {
        isBackendReady.value = true;
      });

      matchSocket.on('image-uploaded', (data) => {
        if (data && typeof data.imageId === 'string') {
          imageUploadedInfo.value = {
            imageId: data.imageId,
            preview: data.preview || '',
          };
        }
      });

      matchSocket.on('image-processing-result', (data) => {
        if (data && typeof data.image === 'string') {
          imageProcessingResult.value = data.image;
        }
      });

      matchSocket.on('color-filter-preview', (data) => {
        if (data && typeof data.image === 'string') {
          colorFilterPreview.value = data.image;
        }
      });
    });
  };

  const sendToBackend = (类型, extra = {}) => {
    if (!isBackendReady.value) {
      // 在组件里通过 UI 提示，store 里只做简单保护
      console.warn('后端还未连接，请稍候...');
      return;
    }
    ipc.invoke(ipcApiRoute.发送到后端, { 类型, ...extra });
  };

  // 从前端上传组件接收到图片变更
  const handleImageChange = (payload) => {
    const safePayload = payload || {};
    const path = safePayload.path || '';
    const preview = safePayload.preview || '';

    if (!path) return;

    // 先在前端预览一份，提升体验
    imageUploadedInfo.value = {
      imageId: '',
      preview,
    };

    // 通知后端做缓存
    sendToBackend('图像上传缓存', {
      图片路径: path,
    });

    // 重置处理结果与颜色过滤预览
    imageProcessingResult.value = '';
    colorFilterPreview.value = '';
    pipelineSteps.value = [];
  };

  // 增加流水线步骤
  const addPipelineStep = (type) => {
    if (!type) return;
    const base = pipelineStepOptions.value.find((item) => item.type === type);
    if (!base) return;

    const step = {
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      type: base.type,
      params: JSON.parse(JSON.stringify(base.defaultParams || {})),
    };
    pipelineSteps.value.push(step);
  };

  // 根据下标删除流水线步骤
  const removePipelineStepByIndex = (index) => {
    if (index < 0 || index >= pipelineSteps.value.length) return;
    pipelineSteps.value.splice(index, 1);
  };

  // 触发流水线处理
  const handlePipelineProcess = () => {
    const currentId =
      imageUploadedInfo.value && imageUploadedInfo.value.imageId;
    if (!currentId) return;

    const paramsArr = pipelineSteps.value.map((step) => ({
      type: step.type,
      params: { ...step.params },
    }));

    sendToBackend('图像处理流水线', {
      imageId: currentId,
      步骤: JSON.parse(JSON.stringify(paramsArr)),
    });
  };

  return {
    // state
    isConnected,
    isBackendReady,
    imageProcessingResult,
    colorFilterPreview,
    imageUploadedInfo,
    displayImageSrc,
    pipelineSteps,
    pipelineStepOptions,
    // actions
    initMatchSocket,
    sendToBackend,
    handleImageChange,
    addPipelineStep,
    removePipelineStepByIndex,
    handlePipelineProcess,
  };
});

