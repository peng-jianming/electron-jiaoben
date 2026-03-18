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
  const currentImageId = ref('');

  // ADB 设备相关
  const adbDevices = ref([]);
  const currentDeviceId = ref('');

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
      defaultParams: {
        list: [],
      },
    },
    {
      type: '膨胀',
      defaultParams: {
        kernelSize: 3,
        iterations: 1,
        kernelShape: 'rect',
      },
    },
    {
      type: '腐蚀',
      defaultParams: {
        kernelSize: 3,
        iterations: 1,
        kernelShape: 'rect',
      },
    },
  ]);

  // 统一的展示用图片：直接使用当前结果（上传预览或处理结果）
  const displayImageSrc = computed(() => {
    return imageProcessingResult.value || '';
  });

  let matchSocket = null;
  let floodFillStorePromise = null;

  const getFloodFillStore = () => {
    if (!floodFillStorePromise) {
      floodFillStorePromise = import('@/stores/floodFill').then((mod) => {
        const useFloodFillStore = mod && mod.useFloodFillStore;
        if (typeof useFloodFillStore !== 'function') {
          throw new Error('useFloodFillStore 未导出或不是函数');
        }
        return useFloodFillStore();
      });
    }
    return floodFillStorePromise;
  };

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
          currentImageId.value = data.imageId;
          // 上传图片返回时，直接作为当前展示图片
          imageProcessingResult.value = data.preview || '';
        }
      });

      // 洪水填充上传图片回传（与图像处理的 image-uploaded 隔离）
      matchSocket.on('flood-image-uploaded', (data) => {
        getFloodFillStore()
          .then((store) => store.handleFloodImageUploaded(data || {}))
          .catch((e) => console.warn('处理洪水填充上传结果失败:', e));
      });

      // 后端启动后推送的流水线参数，用于页面初始化时回显
      matchSocket.on('image-processing-pipeline-params', (data) => {
        const steps = (data && data.steps) || [];
        if (!Array.isArray(steps)) return;

        pipelineSteps.value = steps.map((step) => {
          const safeStep = step || {};
          return {
            id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
            type: safeStep.type,
            params: { ...(safeStep.params || {}) },
          };
        });
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

      // 洪水填充结果预览
      matchSocket.on('flood-fill-result', (data) => {
        getFloodFillStore()
          .then((store) => store.handleFloodFillResult(data || {}))
          .catch((e) => console.warn('处理洪水填充结果失败:', e));
      });

      // 洪水填充失败（用于解除 loading）
      matchSocket.on('flood-fill-error', (data) => {
        getFloodFillStore()
          .then((store) => store.handleFloodFillError(data || {}))
          .catch((e) => console.warn('处理洪水填充错误失败:', e));
      });

      // ADB 设备列表
      matchSocket.on('adb-devices', (data) => {
        const devices = (data && (data.devices || data.list)) || [];
        if (Array.isArray(devices)) {
          adbDevices.value = devices;
        } else {
          adbDevices.value = [];
        }
      });

      // ADB 设备连接结果
      matchSocket.on('adb-device-connected', (data) => {
        const success = !!(data && data.success);
        if (success) {
          currentDeviceId.value = data.deviceId || '';
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

    // 前端本地预览一份，提升体验（临时结果）
    imageProcessingResult.value = preview || '';
    currentImageId.value = '';

    // 通知后端做缓存
    sendToBackend('图像上传缓存', {
      图片路径: path,
    });

    // 重置颜色过滤预览与流水线步骤
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
    const currentId = currentImageId.value;
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
    currentImageId,
    adbDevices,
    currentDeviceId,
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

    // ADB 相关 actions
    requestAdbDevices() {
      sendToBackend('获取ADB设备列表');
    },
    connectAdbDevice(deviceId) {
      if (!deviceId) return;
      sendToBackend('连接ADB设备', { 设备ID: deviceId });
    },
    takeAdbScreenshot() {
      if (!currentDeviceId.value) return;
      sendToBackend('ADB截图', { 设备ID: currentDeviceId.value });
    },
  };
});

