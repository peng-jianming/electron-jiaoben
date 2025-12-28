import { ref, onMounted, onUnmounted } from "vue";
import { ipc } from "@/utils/ipcRenderer";
import { ipcApiRoute } from "@/api";
import { io } from "socket.io-client";
import { ElMessage } from 'element-plus';

export function useColoring() {
  const imageFileName = ref(null);
  const threshold = ref(127);
  const processing = ref(false);
  const imageLoaded = ref(false);
  const floodFillStartPoint = ref(null);
  const keepColors = ref([]);
  const filterColors = ref([]);

  // 处理步骤列表
  const processingSteps = ref([]);
  const currentStepIndex = ref(0);

  // 拖拽相关
  const dragIndex = ref(null);

  let socket = null;
  let stepIdCounter = 0;
  let hasShownCompleteMessage = false; // 已显示完成提示的标记，避免重复弹出

  // 生成唯一ID
  function generateStepId() {
    return `step_${Date.now()}_${++stepIdCounter}`;
  }

  // 获取颜色预览
  function getColorPreview(colorStr) {
    if (!colorStr) return 'transparent';
    const parts = colorStr.split('-');
    const hex = parts[0];
    if (hex && hex.length === 6) {
      return `#${hex}`;
    }
    return 'transparent';
  }

  // 处理图像选择
  function handleImageSelect(file) {
    const fileObj = file.raw || file;
    if (!fileObj) return;

    imageFileName.value = fileObj.name;
    processing.value = true;
    floodFillStartPoint.value = null;
    imageLoaded.value = true;
    // 清空已完成状态
    processingSteps.value.forEach(step => step.completed = false);

    const imagePath = fileObj.path || fileObj.name;
    
    if (!imagePath) {
      console.error("无法获取文件路径");
      processing.value = false;
      return;
    }

    ipc.invoke(ipcApiRoute.sendToPython, {
      type: 'upload_image',
      path: imagePath
    }).catch((error) => {
      console.error("发送图像路径失败:", error);
      processing.value = false;
    });
  }

  // 保存图片
  async function handleSaveImage() {
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const defaultName = `processed_${timestamp}.png`;
      
      const result = await ipc.invoke(ipcApiRoute.openSaveDialog, {
        defaultName: defaultName
      });
      
      if (!result.success || result.canceled) {
        return;
      }
      
      processing.value = true;
      
      await ipc.invoke(ipcApiRoute.sendToPython, {
        type: 'save_image',
        savePath: result.filePath
      });
      
    } catch (error) {
      console.error("保存图片失败:", error);
      ElMessage.error(`保存失败: ${error.message || '未知错误'}`);
      processing.value = false;
    }
  }

  // 添加保留颜色
  function addKeepColor() {
    keepColors.value.push('');
  }

  // 移除保留颜色
  function removeKeepColor(index) {
    keepColors.value.splice(index, 1);
  }

  // 添加过滤颜色
  function addFilterColor() {
    filterColors.value.push('');
  }

  // 移除过滤颜色
  function removeFilterColor(index) {
    filterColors.value.splice(index, 1);
  }

  // 添加颜色过滤步骤
  function addColorFilterStep() {
    const validKeepColors = keepColors.value.filter(c => c && c.trim());
    const validFilterColors = filterColors.value.filter(c => c && c.trim());
    
    if (validKeepColors.length === 0 && validFilterColors.length === 0) {
      ElMessage.warning('请至少添加一个保留颜色或过滤颜色');
      return;
    }
    
    const step = {
      id: generateStepId(),
      type: 'color_filter',
      title: '颜色过滤',
      description: `保留: ${validKeepColors.length}个, 过滤: ${validFilterColors.length}个`,
      params: {
        keepColors: [...validKeepColors],
        filterColors: [...validFilterColors]
      },
      completed: false
    };
    
    processingSteps.value.push(step);
    ElMessage.success('已添加颜色过滤步骤');
  }

  // 添加二值化步骤
  function addBinaryStep() {
    const step = {
      id: generateStepId(),
      type: 'binary',
      title: '二值化处理',
      description: `阈值: ${threshold.value}`,
      params: {
        threshold: threshold.value
      },
      completed: false
    };
    
    processingSteps.value.push(step);
    ElMessage.success('已添加二值化步骤');
  }

  // 添加洪水填充步骤
  function addFloodFillStep() {
    if (!floodFillStartPoint.value) {
      ElMessage.warning('请先在图片上选择填充起始位置');
      return;
    }
    
    const step = {
      id: generateStepId(),
      type: 'flood_fill',
      title: '洪水填充',
      description: `起点: (${floodFillStartPoint.value.x}, ${floodFillStartPoint.value.y})`,
      params: {
        x: floodFillStartPoint.value.x,
        y: floodFillStartPoint.value.y
      },
      completed: false
    };
    
    processingSteps.value.push(step);
    ElMessage.success('已添加洪水填充步骤');
  }

  // 显示洪水填充动画
  function showFloodFillAnimation(stepIndex, step) {
    if (!step || step.type !== 'flood_fill') {
      return;
    }
    
    // 深拷贝参数确保可序列化
    const params = JSON.parse(JSON.stringify(step.params));
    
    // 发送请求到 Python，使用上一步的图片数据执行洪水填充动画
    ipc.invoke(ipcApiRoute.sendToPython, {
      type: 'flood_fill_animation',
      stepIndex: stepIndex,
      params: params
    }).catch((error) => {
      console.error("显示动画失败:", error);
      ElMessage.error(`显示动画失败: ${error.message || '未知错误'}`);
    });
  }

  // 移除步骤
  function removeStep(index) {
    processingSteps.value.splice(index, 1);
  }

  // 清空所有步骤
  function clearAllSteps() {
    processingSteps.value = [];
    ElMessage.info('已清空所有步骤');
  }

  // 拖拽开始
  function handleDragStart(index, event) {
    dragIndex.value = index;
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', index);
  }

  // 拖拽经过
  function handleDragOver(index, event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }

  // 拖拽放下
  function handleDrop(index, event) {
    event.preventDefault();
    const fromIndex = dragIndex.value;
    if (fromIndex !== null && fromIndex !== index) {
      const item = processingSteps.value.splice(fromIndex, 1)[0];
      processingSteps.value.splice(index, 0, item);
    }
  }

  // 拖拽结束
  function handleDragEnd() {
    dragIndex.value = null;
  }

  // 开始处理
  function startProcessing() {
    if (!imageLoaded.value) {
      ElMessage.warning('请先上传图片');
      return;
    }
    
    // 重置所有步骤的完成状态
    processingSteps.value.forEach(step => step.completed = false);
    currentStepIndex.value = 0;
    processing.value = true;
    hasShownCompleteMessage = false; // 重置提示标记
    
    // 发送处理请求到 Python（深拷贝确保对象可序列化）
    const steps = JSON.parse(JSON.stringify(
      processingSteps.value.map(step => ({
        type: step.type,
        params: step.params
      }))
    ));
    
    ipc.invoke(ipcApiRoute.sendToPython, {
      type: 'process_steps',
      steps: steps
    }).catch((error) => {
      console.error("处理失败:", error);
      ElMessage.error(`处理失败: ${error.message || '未知错误'}`);
      processing.value = false;
    });
  }

  // 处理图片点击事件
  function handleImageClick(x, y) {
    if (!imageLoaded.value) return;
    
    floodFillStartPoint.value = { x, y };
    console.log(`已选择洪水填充起始位置: (${x}, ${y})`);
  }

  // 接收 Python 处理结果
  const handleProcessedImage = (data) => {
    if (data && data.stepIndex !== undefined) {
      // 步骤处理完成
      if (data.stepIndex < processingSteps.value.length) {
        processingSteps.value[data.stepIndex].completed = true;
      }
      currentStepIndex.value = data.stepIndex;
      
      // 如果是最后一步完成（且成功）
      const isLastStep = data.stepIndex >= processingSteps.value.length - 1;
      const isComplete = data.isComplete === true; // Python 端标记处理完全完成
      
      if ((isLastStep || isComplete) && data.success) {
        processing.value = false;
        // 只弹出一次完成提示
        if (!hasShownCompleteMessage) {
          hasShownCompleteMessage = true;
          ElMessage.success('处理完成');
        }
      } else if (!data.success) {
        processing.value = false;
      }
    } else {
      processing.value = false;
    }
    
    // 错误提示只弹一次
    if (data && !data.success && data.error) {
      console.error("图像处理失败:", data.error);
      ElMessage.error(`处理失败: ${data.error}`);
    }
  };

  // 处理保存结果
  const handleSaveResult = (data) => {
    processing.value = false;
    
    if (data && data.success) {
      ElMessage.success(`图片已保存: ${data.path}`);
    } else if (data && data.error) {
      ElMessage.error(`保存失败: ${data.error}`);
    }
  };

  // 初始化 Socket 连接
  function initSocket() {
    socket = io("ws://localhost:7070");
    socket.on("connect", () => {
      console.log("Socket 连接成功");
    });

    socket.on("image-processed", (response) => {
      console.log("收到处理结果:", response);
      handleProcessedImage(response);
    });
    
    socket.on("image-saved", (response) => {
      console.log("收到保存结果:", response);
      handleSaveResult(response);
    });
  }

  // 初始化 IPC 监听
  function initIpcListeners() {
    if (ipc) {
      ipc.on('image-click', (event, data) => {
        console.log("收到图片点击事件:", data);
        handleImageClick(data.x, data.y);
      });
    } else if (window.ipcRenderer) {
      window.ipcRenderer.on('image-click', (event, data) => {
        console.log("收到图片点击事件:", data);
        handleImageClick(data.x, data.y);
      });
    } else if (window.electron && window.electron.ipcRenderer) {
      window.electron.ipcRenderer.on('image-click', (event, data) => {
        console.log("收到图片点击事件:", data);
        handleImageClick(data.x, data.y);
      });
    }
  }

  // 清理
  function cleanup() {
    if (socket) {
      socket.disconnect();
    }
    
    if (ipc) {
      ipc.removeAllListeners('image-click');
    } else if (window.ipcRenderer) {
      window.ipcRenderer.removeAllListeners('image-click');
    } else if (window.electron && window.electron.ipcRenderer) {
      window.electron.ipcRenderer.removeAllListeners('image-click');
    }
  }

  return {
    // 状态
    imageFileName,
    threshold,
    processing,
    imageLoaded,
    floodFillStartPoint,
    keepColors,
    filterColors,
    processingSteps,
    currentStepIndex,
    dragIndex,
    
    // 方法
    getColorPreview,
    handleImageSelect,
    handleSaveImage,
    addKeepColor,
    removeKeepColor,
    addFilterColor,
    removeFilterColor,
    addColorFilterStep,
    addBinaryStep,
    addFloodFillStep,
    removeStep,
    clearAllSteps,
    handleDragStart,
    handleDragOver,
    handleDrop,
    handleDragEnd,
    startProcessing,
    handleImageClick,
    showFloodFillAnimation,
    
    // 生命周期
    initSocket,
    initIpcListeners,
    cleanup
  };
}

