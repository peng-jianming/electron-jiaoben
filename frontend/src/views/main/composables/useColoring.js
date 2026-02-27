import { ref, watch } from "vue";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import { io } from "socket.io-client";
import { ElMessage } from 'element-plus';

export const STEP_TYPES = {
  color_filter: { label: '颜色过滤', gradient: 'linear-gradient(135deg, #8b5cf6, #a78bfa)' },
  binary: { label: '二值化', gradient: 'linear-gradient(135deg, #f59e0b, #fbbf24)' },
};

function getDefaultParams(type) {
  switch (type) {
    case 'color_filter': return { keepColors: [], filterColors: [] };
    case 'binary': return { threshold: 127 };
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

  // 独立洪水填充
  const floodFillSource = ref('processed'); // 'processed' | 'stitched'
  const floodFillX = ref(0);
  const floodFillY = ref(0);
  const floodFillResult = ref(null);
  const floodFillProcessing = ref(false);
  const isSelectingFloodFillPoint = ref(false);

  // 设备连接（参考 ImageProcessorTab）
  const deviceDialogVisible = ref(false);
  const deviceList = ref([]);
  const deviceLoading = ref(false);
  const selectedDeviceId = ref("");
  const currentDeviceId = ref("");
  const screenshotLoading = ref(false);
  const captureWindowLoading = ref(false);
  const deviceTab = ref('mobile');

  // 拼接状态
  const stitchedImage = ref(null);
  const stitchCount = ref(0);
  const isAutoStitching = ref(false);
  const stitchLoading = ref(false);
  const lastStitchConfidence = ref(0);
  const pendingStitch = ref(false);
  const stitchMaxDx = ref(300);
  const stitchMaxDy = ref(200);
  const stitchInterval = ref(500);
  const previewMode = ref('processed');
  const stitchBatchFiles = ref([]);
  const batchStitching = ref(false);

  let socket = null;
  let stepIdCounter = 0;
  let hasShownCompleteMessage = false;
  let processDebounceTimer = null;
  let autoStitchTimer = null;

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

  // ==================== 独立洪水填充 ====================

  function startFloodFillPointSelection() {
    const src = floodFillSource.value;
    if (src === 'processed' && !processedImage.value) {
      ElMessage.warning('没有管线处理结果，请先执行管线处理');
      return;
    }
    if (src === 'stitched' && !stitchedImage.value) {
      ElMessage.warning('没有拼接结果，请先进行拼接');
      return;
    }
    isSelectingFloodFillPoint.value = true;
    previewMode.value = src;
    ElMessage.info('请在右侧图片上点击选择填充起始位置');
  }

  function handleFloodFillImageClick(x, y) {
    if (!isSelectingFloodFillPoint.value) return;
    floodFillX.value = x;
    floodFillY.value = y;
    isSelectingFloodFillPoint.value = false;
    ElMessage.success(`已选择填充起始位置: (${x}, ${y})`);
  }

  function executeFloodFill() {
    const src = floodFillSource.value;
    if (src === 'processed' && !processedImage.value) {
      ElMessage.warning('没有管线处理结果');
      return;
    }
    if (src === 'stitched' && !stitchedImage.value) {
      ElMessage.warning('没有拼接结果');
      return;
    }

    floodFillProcessing.value = true;
    ipc.invoke(ipcApiRoute.sendToPython, {
      type: 'standalone_flood_fill',
      source: src,
      x: floodFillX.value,
      y: floodFillY.value,
    }).catch((error) => {
      console.error("洪水填充失败:", error);
      ElMessage.error(`填充失败: ${error.message || '未知错误'}`);
      floodFillProcessing.value = false;
    });
  }

  function showFloodFillAnimation() {
    const src = floodFillSource.value;
    if (src === 'processed' && !processedImage.value) {
      ElMessage.warning('没有管线处理结果');
      return;
    }
    if (src === 'stitched' && !stitchedImage.value) {
      ElMessage.warning('没有拼接结果');
      return;
    }

    ipc.invoke(ipcApiRoute.sendToPython, {
      type: 'standalone_flood_fill_animation',
      source: src,
      x: floodFillX.value,
      y: floodFillY.value,
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
  // 已改为纯手动模式：不再监听管线变化自动触发处理，
  // 仅在外部显式调用 startProcessing 时才会发送处理请求。

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
        // 处理完成后触发拼接
        if (pendingStitch.value || isAutoStitching.value) {
          pendingStitch.value = false;
          stitchCurrentImage();
        }
      } else if (!data.success) {
        processing.value = false;
        if (isAutoStitching.value) {
          stopAutoStitch();
        }
      }
    } else {
      processing.value = false;
      if (pipeline.value.length > 0) {
        startProcessing();
      } else if (pendingStitch.value || isAutoStitching.value) {
        pendingStitch.value = false;
        stitchCurrentImage();
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

  const handleStitchResult = (data) => {
    if (data && data.cleared) {
      stitchedImage.value = null;
      stitchCount.value = 0;
      lastStitchConfidence.value = 0;
      stitchLoading.value = false;
      return;
    }
    if (data && data.success && data.stitchedImage) {
      stitchedImage.value = `data:image/png;base64,${data.stitchedImage}`;
      stitchCount.value = data.count || 0;
      lastStitchConfidence.value = data.confidence || 0;
      if (previewMode.value === 'stitched' || isAutoStitching.value || batchStitching.value) {
        previewMode.value = 'stitched';
      }
    } else if (data && !data.success && data.error) {
      console.error("拼接失败:", data.error);
      ElMessage.error(`拼接失败: ${data.error}`);
    }
    // 批量拼接完成
    if (data && data.isComplete) {
      batchStitching.value = false;
      stitchLoading.value = false;
      if (data.success) {
        ElMessage.success(`批量拼接完成: 共${data.count}张`);
      }
      return;
    }
    // 自动拼接（连续截图模式）：完成后继续下一轮
    if (isAutoStitching.value && !batchStitching.value) {
      stitchLoading.value = false;
      autoStitchTimer = setTimeout(() => {
        if (isAutoStitching.value) {
          takeScreenshotForStitch();
        }
      }, stitchInterval.value);
    } else if (!batchStitching.value) {
      stitchLoading.value = false;
    }
  };

  // 仅处理来源为 coloring-tab 的截图
  function handleDeviceScreenshot(data) {
    if (data?.source !== "coloring-tab") return;
    screenshotLoading.value = false;
    if (!data?.success || !data?.image) {
      ElMessage.error(data?.error || "获取截图失败");
      if (isAutoStitching.value) stopAutoStitch();
      return;
    }
    const url = `data:image/png;base64,${data.image}`;
    imageFileName.value = `手机截图_${new Date().toLocaleTimeString().replace(/[/:]/g, "-")}.png`;
    originalImageUrl.value = url;
    imageLoaded.value = true;
    pipeline.value.forEach((step) => (step.completed = false));
    processing.value = true;
    ipc.invoke(ipcApiRoute.sendToPython, {
      type: "upload_image",
      base64: data.image,
    }).catch((err) => {
      console.error("上传截图失败:", err);
      processing.value = false;
    });
  }

  function handleDeviceList(data) {
    deviceLoading.value = false;
    if (!data?.success) {
      deviceList.value = [];
      if (data?.error) ElMessage.error(data.error);
      return;
    }
    deviceList.value = data.devices || [];
    if (data.currentDeviceId) {
      currentDeviceId.value = data.currentDeviceId;
      selectedDeviceId.value = data.currentDeviceId;
    } else if (deviceList.value.length > 0 && !selectedDeviceId.value) {
      selectedDeviceId.value = deviceList.value[0];
    }
  }

  function handleDeviceSelected(data) {
    if (!data?.success && data?.error) {
      ElMessage.error(data.error);
      return;
    }
    currentDeviceId.value = data?.currentDeviceId ?? "";
    if (currentDeviceId.value) {
      selectedDeviceId.value = currentDeviceId.value;
      ElMessage.success(`已连接设备: ${currentDeviceId.value}`);
    } else {
      ElMessage.info("已清除当前连接设备");
    }
  }

  const handleFloodFillResult = (data) => {
    floodFillProcessing.value = false;
    if (data?.success && data?.image) {
      floodFillResult.value = `data:image/png;base64,${data.image}`;
      previewMode.value = 'flood-fill';
      ElMessage.success('洪水填充完成');
    } else {
      ElMessage.error(data?.error || '洪水填充失败');
    }
  };

  function initSocket() {
    socket = io("ws://localhost:7070");
    socket.on("connect", () => console.log("Socket 连接成功"));
    socket.on("image-processed", handleProcessedImage);
    socket.on("image-saved", handleSaveResult);
    socket.on("device-list", handleDeviceList);
    socket.on("device-selected", handleDeviceSelected);
    socket.on("device-screenshot", handleDeviceScreenshot);
    socket.on("stitch-result", handleStitchResult);
    socket.on("flood-fill-result", handleFloodFillResult);
  }

  function openDeviceDialog() {
    deviceDialogVisible.value = true;
    refreshDevices();
  }

  async function refreshDevices() {
    deviceLoading.value = true;
    try {
      await ipc.invoke(ipcApiRoute.sendToPython, { type: "get_devices" });
    } catch (err) {
      console.error("刷新设备失败:", err);
      ElMessage.error(`刷新设备失败: ${err?.message || "未知错误"}`);
      deviceLoading.value = false;
    }
  }

  async function connectSelectedDevice() {
    if (!selectedDeviceId.value) return;
    try {
      await ipc.invoke(ipcApiRoute.sendToPython, {
        type: "set_device",
        deviceId: selectedDeviceId.value,
      });
    } catch (err) {
      console.error("连接设备失败:", err);
      ElMessage.error(`连接设备失败: ${err?.message || "未知错误"}`);
    }
  }

  async function captureScreenshot() {
    if (!currentDeviceId.value) {
      ElMessage.warning("请先连接设备");
      if (isAutoStitching.value) stopAutoStitch();
      return;
    }
    screenshotLoading.value = true;
    try {
      await ipc.invoke(ipcApiRoute.sendToPython, {
        type: "capture_screenshot",
        source: "coloring-tab",
      });
    } catch (err) {
      console.error("截图失败:", err);
      ElMessage.error(`截图失败: ${err?.message || "未知错误"}`);
      screenshotLoading.value = false;
      if (isAutoStitching.value) stopAutoStitch();
    }
  }

  async function openCaptureWindow() {
    try {
      const result = await ipc.invoke(ipcApiRoute.openCaptureWindow, {});
      if (result?.success) {
        ElMessage.success("截屏窗口已打开，可拖动调整区域后点击「截图」");
      } else {
        ElMessage.warning(result?.message || "打开截屏窗口失败");
      }
    } catch (err) {
      console.error("打开截屏窗口失败:", err);
      ElMessage.error(`打开截屏窗口失败: ${err?.message || "未知错误"}`);
    }
  }

  async function captureWindowScreenshot() {
    try {
      const status = await ipc.invoke(ipcApiRoute.getCaptureStatus, {});
      if (!status?.hasCaptureWindow) {
        ElMessage.warning("请先打开截屏窗口");
        if (isAutoStitching.value) stopAutoStitch();
        return;
      }
      captureWindowLoading.value = true;
      const result = await ipc.invoke(ipcApiRoute.captureScreenOnce, {});
      if (!result?.success || !result?.image) {
        captureWindowLoading.value = false;
        ElMessage.error(result?.message || "截图失败");
        if (isAutoStitching.value) stopAutoStitch();
        return;
      }
      captureWindowLoading.value = false;
      const url = result.image.startsWith("data:") ? result.image : `data:image/png;base64,${result.image}`;
      imageFileName.value = `截屏窗口_${new Date().toLocaleTimeString().replace(/[/:]/g, "-")}.png`;
      originalImageUrl.value = url;
      imageLoaded.value = true;
      pipeline.value.forEach((step) => (step.completed = false));
      processing.value = true;
      const base64 = result.image.replace(/^data:image\/\w+;base64,/, "");
      ipc.invoke(ipcApiRoute.sendToPython, {
        type: "upload_image",
        base64,
      }).catch((err) => {
        console.error("上传截图失败:", err);
        processing.value = false;
        if (isAutoStitching.value) stopAutoStitch();
      });
    } catch (err) {
      console.error("截屏窗口截图失败:", err);
      captureWindowLoading.value = false;
      ElMessage.error(`截图失败: ${err?.message || "未知错误"}`);
      if (isAutoStitching.value) stopAutoStitch();
    }
  }

  // ==================== 拼接功能 ====================

  function stitchCurrentImage() {
    stitchLoading.value = true;
    ipc.invoke(ipcApiRoute.sendToPython, {
      type: 'stitch_image',
      maxDx: stitchMaxDx.value,
      maxDy: stitchMaxDy.value,
    }).catch((error) => {
      console.error("拼接失败:", error);
      ElMessage.error(`拼接失败: ${error.message || '未知错误'}`);
      stitchLoading.value = false;
      if (isAutoStitching.value) stopAutoStitch();
    });
  }

  function takeScreenshotForStitch() {
    if (deviceTab.value === 'capture-window') {
      captureWindowScreenshot();
    } else {
      captureScreenshot();
    }
  }

  // ---- 批量拼接（拼接一次：上传多张图片） ----

  function addStitchFiles(file) {
    const raw = file.raw || file;
    if (!raw) return;
    const exists = stitchBatchFiles.value.some(
      (f) => f.name === raw.name && f.size === raw.size
    );
    if (!exists) {
      stitchBatchFiles.value.push(raw);
    }
  }

  function removeStitchFile(index) {
    stitchBatchFiles.value.splice(index, 1);
  }

  function clearStitchFiles() {
    stitchBatchFiles.value = [];
  }

  function doBatchStitch() {
    if (stitchBatchFiles.value.length === 0) {
      ElMessage.warning('请先选择要拼接的图片');
      return;
    }
    const imagePaths = stitchBatchFiles.value
      .map((f) => f.path)
      .filter(Boolean);
    if (imagePaths.length === 0) {
      ElMessage.warning('无法获取图片文件路径');
      return;
    }

    stitchLoading.value = true;
    batchStitching.value = true;
    previewMode.value = 'stitched';

    const steps = JSON.parse(
      JSON.stringify(pipeline.value.map((s) => ({ type: s.type, params: s.params })))
    );

    ipc.invoke(ipcApiRoute.sendToPython, {
      type: 'batch_stitch',
      imagePaths,
      steps,
      maxDx: stitchMaxDx.value,
      maxDy: stitchMaxDy.value,
    }).catch((error) => {
      console.error('批量拼接失败:', error);
      ElMessage.error(`拼接失败: ${error.message || '未知错误'}`);
      stitchLoading.value = false;
      batchStitching.value = false;
    });
  }

  function startAutoStitch() {
    if (!currentDeviceId.value && deviceTab.value !== 'capture-window') {
      ElMessage.warning("请先连接设备或打开截屏窗口");
      return;
    }
    if (pipeline.value.length === 0) {
      ElMessage.warning("请先添加处理步骤（至少需要二值化步骤）");
      return;
    }
    isAutoStitching.value = true;
    pendingStitch.value = true;
    takeScreenshotForStitch();
    ElMessage.success('已开始连续拼接');
  }

  function stopAutoStitch() {
    isAutoStitching.value = false;
    pendingStitch.value = false;
    if (autoStitchTimer) {
      clearTimeout(autoStitchTimer);
      autoStitchTimer = null;
    }
    ElMessage.info('已停止连续拼接');
  }

  function clearStitch() {
    ipc.invoke(ipcApiRoute.sendToPython, {
      type: 'clear_stitch',
    }).catch((error) => {
      console.error("清空拼接失败:", error);
    });
    stitchedImage.value = null;
    stitchCount.value = 0;
    lastStitchConfidence.value = 0;
    ElMessage.info('已清空拼接结果');
  }

  async function handleSaveStitchedImage() {
    if (!stitchedImage.value) {
      ElMessage.warning('没有拼接结果可保存');
      return;
    }
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const result = await ipc.invoke(ipcApiRoute.openSaveDialog, {
        defaultName: `stitched_${timestamp}.png`,
      });
      if (!result.success || result.canceled) return;

      const base64Data = stitchedImage.value.replace(/^data:image\/\w+;base64,/, '');
      const saveResult = await ipc.invoke(ipcApiRoute.saveBase64Image, {
        filePath: result.filePath,
        imageData: base64Data,
      });

      if (saveResult.success) {
        ElMessage.success(`拼接图已保存: ${result.filePath}`);
      } else {
        ElMessage.error(`保存失败: ${saveResult.error || '未知错误'}`);
      }
    } catch (error) {
      console.error("保存拼接图失败:", error);
      ElMessage.error(`保存失败: ${error.message || '未知错误'}`);
    }
  }

  async function handleSaveProcessedImage() {
    if (!processedImage.value) {
      ElMessage.warning('没有管线处理结果可保存');
      return;
    }
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const result = await ipc.invoke(ipcApiRoute.openSaveDialog, {
        defaultName: `processed_${timestamp}.png`,
      });
      if (!result.success || result.canceled) return;

      const base64Data = processedImage.value.replace(/^data:image\/\w+;base64,/, '');
      const saveResult = await ipc.invoke(ipcApiRoute.saveBase64Image, {
        filePath: result.filePath,
        imageData: base64Data,
      });

      if (saveResult.success) {
        ElMessage.success(`处理结果已保存: ${result.filePath}`);
      } else {
        ElMessage.error(`保存失败: ${saveResult.error || '未知错误'}`);
      }
    } catch (error) {
      console.error("保存处理结果失败:", error);
      ElMessage.error(`保存失败: ${error.message || '未知错误'}`);
    }
  }

  async function handleSaveFloodFillImage() {
    if (!floodFillResult.value) {
      ElMessage.warning('没有洪水填充结果可保存');
      return;
    }
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const result = await ipc.invoke(ipcApiRoute.openSaveDialog, {
        defaultName: `flood_fill_${timestamp}.png`,
      });
      if (!result.success || result.canceled) return;

      const base64Data = floodFillResult.value.replace(/^data:image\/\w+;base64,/, '');
      const saveResult = await ipc.invoke(ipcApiRoute.saveBase64Image, {
        filePath: result.filePath,
        imageData: base64Data,
      });

      if (saveResult.success) {
        ElMessage.success(`填充结果已保存: ${result.filePath}`);
      } else {
        ElMessage.error(`保存失败: ${saveResult.error || '未知错误'}`);
      }
    } catch (error) {
      console.error("保存填充结果失败:", error);
      ElMessage.error(`保存失败: ${error.message || '未知错误'}`);
    }
  }

  function initIpcListeners() {
    // no-op: image clicks are now handled directly in the same window
  }

  function cleanup() {
    if (socket) socket.disconnect();
    if (processDebounceTimer) clearTimeout(processDebounceTimer);
    if (autoStitchTimer) clearTimeout(autoStitchTimer);
    isAutoStitching.value = false;
  }

  return {
    imageFileName,
    originalImageUrl,
    processing,
    imageLoaded,
    processedImage,
    pipeline,
    dragIndex,

    // 独立洪水填充
    floodFillSource,
    floodFillX,
    floodFillY,
    floodFillResult,
    floodFillProcessing,
    isSelectingFloodFillPoint,

    deviceDialogVisible,
    deviceList,
    deviceLoading,
    selectedDeviceId,
    currentDeviceId,
    screenshotLoading,
    captureWindowLoading,
    deviceTab,

    // 拼接状态
    stitchedImage,
    stitchCount,
    isAutoStitching,
    stitchLoading,
    lastStitchConfidence,
    stitchMaxDx,
    stitchMaxDy,
    stitchInterval,
    previewMode,

    getColorPreview,
    addStep,
    updateStepParams,
    toggleStepExpand,
    removeStep,
    clearAllSteps,
    handleImageSelect,
    handleSaveImage,
    handleDragStart,
    handleDragOver,
    handleDrop,
    handleDragEnd,
    startProcessing,

    // 独立洪水填充方法
    startFloodFillPointSelection,
    handleFloodFillImageClick,
    executeFloodFill,
    showFloodFillAnimation,

    openDeviceDialog,
    refreshDevices,
    connectSelectedDevice,
    captureScreenshot,
    openCaptureWindow,
    captureWindowScreenshot,

    // 拼接功能
    stitchBatchFiles,
    batchStitching,
    addStitchFiles,
    removeStitchFile,
    clearStitchFiles,
    doBatchStitch,
    startAutoStitch,
    stopAutoStitch,
    clearStitch,
    handleSaveStitchedImage,
    handleSaveProcessedImage,
    handleSaveFloodFillImage,

    initSocket,
    initIpcListeners,
    cleanup,
  };
}
