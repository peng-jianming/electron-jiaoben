import { ref, watch, computed } from "vue";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import { io } from "socket.io-client";
import { ElMessage } from 'element-plus';

export const STEP_TYPES = {
  color_filter: { label: '颜色过滤', gradient: 'linear-gradient(135deg, #8b5cf6, #a78bfa)' },
  binary: { label: '二值化', gradient: 'linear-gradient(135deg, #f59e0b, #fbbf24)' },
  flood_fill: { label: '洪水填充', gradient: 'linear-gradient(135deg, #10b981, #34d399)' },
};

function getDefaultParams(type) {
  switch (type) {
    case 'color_filter': return { keepColors: [], filterColors: [] };
    case 'binary': return { threshold: 127 };
    case 'flood_fill': return { x: 0, y: 0 };
    default: return {};
  }
}

export function useColoring() {
  const imageFileName = ref(null);
  const processing = ref(false);
  const imageLoaded = ref(false);
  const processedImage = ref(null);
  const originalImageUrl = ref(null);

  const pipeline = ref([]);
  const dragIndex = ref(null);
  const activeFloodFillStepId = ref(null);

  let socket = null;
  let stepIdCounter = 0;
  let hasShownCompleteMessage = false;
  let processDebounceTimer = null;

  function generateStepId() {
    return `step_${Date.now()}_${++stepIdCounter}`;
  }

  function getColorPreview(colorStr) {
    if (!colorStr) return 'transparent';
    const hex = colorStr.split('-')[0];
    return (hex && hex.length === 6) ? `#${hex}` : 'transparent';
  }

  // ==================== Pipeline 管理 ====================

  function addStep(type) {
    if (!STEP_TYPES[type]) return;
    pipeline.value.push({
      id: generateStepId(),
      type,
      expanded: true,
      completed: false,
      params: getDefaultParams(type),
    });
    ElMessage.success(`已添加${STEP_TYPES[type].label}步骤`);
  }

  function updateStepParams(stepId, newParams) {
    const step = pipeline.value.find(s => s.id === stepId);
    if (step) {
      step.params = { ...step.params, ...newParams };
    }
  }

  function toggleStepExpand(stepId) {
    const step = pipeline.value.find(s => s.id === stepId);
    if (step) step.expanded = !step.expanded;
  }

  function removeStep(index) {
    pipeline.value.splice(index, 1);
  }

  function clearAllSteps() {
    pipeline.value = [];
    ElMessage.info('已清空所有步骤');
  }

  // ==================== 拖拽 ====================

  function handleDragStart(index, event) {
    dragIndex.value = index;
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', index);
  }

  function handleDragOver(index, event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }

  function handleDrop(index, event) {
    event.preventDefault();
    const fromIndex = dragIndex.value;
    if (fromIndex !== null && fromIndex !== index) {
      const item = pipeline.value.splice(fromIndex, 1)[0];
      pipeline.value.splice(index, 0, item);
    }
  }

  function handleDragEnd() {
    dragIndex.value = null;
  }

  // ==================== 图像操作 ====================

  function handleImageSelect(file) {
    const fileObj = file.raw || file;
    if (!fileObj) return;

    imageFileName.value = fileObj.name;
    processing.value = true;
    imageLoaded.value = true;
    pipeline.value.forEach(step => step.completed = false);

    if (fileObj instanceof Blob) {
      const reader = new FileReader();
      reader.onload = (e) => {
        originalImageUrl.value = e.target.result;
      };
      reader.readAsDataURL(fileObj);
    }

    const imagePath = fileObj.path || fileObj.name;
    if (!imagePath) {
      console.error("无法获取文件路径");
      processing.value = false;
      return;
    }

    ipc.invoke(ipcApiRoute.sendToPython, {
      type: 'upload_image',
      path: imagePath,
    }).catch((error) => {
      console.error("发送图像路径失败:", error);
      processing.value = false;
    });
  }

  async function handleSaveImage() {
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const result = await ipc.invoke(ipcApiRoute.openSaveDialog, {
        defaultName: `processed_${timestamp}.png`,
      });
      if (!result.success || result.canceled) return;

      processing.value = true;
      await ipc.invoke(ipcApiRoute.sendToPython, {
        type: 'save_image',
        savePath: result.filePath,
      });
    } catch (error) {
      console.error("保存图片失败:", error);
      ElMessage.error(`保存失败: ${error.message || '未知错误'}`);
      processing.value = false;
    }
  }

  // ==================== 洪水填充坐标选取 ====================

  function startPointSelection(stepId) {
    activeFloodFillStepId.value = stepId;
    ElMessage.info('请在图片上点击选择填充起始位置');
  }

  function handleImageClick(x, y) {
    if (!imageLoaded.value) return;
    if (activeFloodFillStepId.value) {
      const step = pipeline.value.find(s => s.id === activeFloodFillStepId.value);
      if (step && step.type === 'flood_fill') {
        step.params = { ...step.params, x, y };
        ElMessage.success(`已选择填充起始位置: (${x}, ${y})`);
      }
      activeFloodFillStepId.value = null;
    }
  }

  function showFloodFillAnimation(stepIndex, step) {
    if (!step || step.type !== 'flood_fill') return;
    const params = JSON.parse(JSON.stringify(step.params));
    ipc.invoke(ipcApiRoute.sendToPython, {
      type: 'flood_fill_animation',
      stepIndex,
      params,
    }).catch((error) => {
      console.error("显示动画失败:", error);
      ElMessage.error(`显示动画失败: ${error.message || '未知错误'}`);
    });
  }

  // ==================== 执行处理 ====================

  function startProcessing() {
    if (!imageLoaded.value) return;

    pipeline.value.forEach(step => step.completed = false);
    processing.value = true;
    hasShownCompleteMessage = false;

    const steps = JSON.parse(JSON.stringify(
      pipeline.value.map(step => ({ type: step.type, params: step.params }))
    ));

    ipc.invoke(ipcApiRoute.sendToPython, {
      type: 'process_steps',
      steps,
    }).catch((error) => {
      console.error("处理失败:", error);
      ElMessage.error(`处理失败: ${error.message || '未知错误'}`);
      processing.value = false;
    });
  }

  // ==================== Auto Processing ====================

  const pipelineSignature = computed(() => {
    return JSON.stringify(pipeline.value.map(s => ({ type: s.type, params: s.params })));
  });

  watch(pipelineSignature, () => {
    if (!imageLoaded.value) return;
    if (processDebounceTimer) clearTimeout(processDebounceTimer);
    processDebounceTimer = setTimeout(() => {
      startProcessing();
    }, 500);
  });

  // ==================== Socket / IPC ====================

  const handleProcessedImage = (data) => {
    if (data && data.success && data.processedImage) {
      const isJpeg = data.processedImage.startsWith('/9j/');
      const mimeType = isJpeg ? 'image/jpeg' : 'image/png';
      processedImage.value = `data:${mimeType};base64,${data.processedImage}`;
    }

    if (data && data.stepIndex !== undefined) {
      if (data.stepIndex < pipeline.value.length) {
        pipeline.value[data.stepIndex].completed = true;
      }
      const isLastStep = data.stepIndex >= pipeline.value.length - 1;
      const isComplete = data.isComplete === true;

      if ((isLastStep || isComplete) && data.success) {
        processing.value = false;
      } else if (!data.success) {
        processing.value = false;
      }
    } else {
      processing.value = false;
      if (pipeline.value.length > 0) {
        startProcessing();
      }
    }

    if (data && !data.success && data.error) {
      console.error("图像处理失败:", data.error);
      ElMessage.error(`处理失败: ${data.error}`);
    }
  };

  const handleSaveResult = (data) => {
    processing.value = false;
    if (data && data.success) {
      ElMessage.success(`图片已保存: ${data.path}`);
    } else if (data && data.error) {
      ElMessage.error(`保存失败: ${data.error}`);
    }
  };

  function initSocket() {
    socket = io("ws://localhost:7070");
    socket.on("connect", () => console.log("Socket 连接成功"));
    socket.on("image-processed", handleProcessedImage);
    socket.on("image-saved", handleSaveResult);
  }

  function initIpcListeners() {
    // no-op: image clicks are now handled directly in the same window
  }

  function cleanup() {
    if (socket) socket.disconnect();
    if (processDebounceTimer) clearTimeout(processDebounceTimer);
  }

  return {
    imageFileName,
    originalImageUrl,
    processing,
    imageLoaded,
    processedImage,
    pipeline,
    dragIndex,
    activeFloodFillStepId,

    getColorPreview,
    addStep,
    updateStepParams,
    toggleStepExpand,
    removeStep,
    clearAllSteps,
    handleImageSelect,
    handleImageClick,
    handleSaveImage,
    startPointSelection,
    showFloodFillAnimation,
    handleDragStart,
    handleDragOver,
    handleDrop,
    handleDragEnd,
    startProcessing,

    initSocket,
    initIpcListeners,
    cleanup,
  };
}
