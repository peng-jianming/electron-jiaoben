import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { storeToRefs } from "pinia";
import { useImageProcessingStore } from "@/stores/imageProcessing";
import { getMatchSocket } from "@/utils/matchSocket";

export const useImageStitchingStore = defineStore("imageStitching", () => {
  const imageProcessingStore = useImageProcessingStore();
  const { isBackendReady } = storeToRefs(imageProcessingStore);

  const isStitching = ref(false);
  const progress = ref(0); // 0-100
  const stage = ref("");
  const progressMessage = ref("");

  const resultImageSrc = ref("");
  const lastErrorMessage = ref("");

  const currentRequestId = ref("");

  const sendToBackend = (类型, extra = {}) => {
    if (!isBackendReady.value) return;
    imageProcessingStore.sendToBackend(类型, extra);
  };

  const reset = () => {
    isStitching.value = false;
    progress.value = 0;
    stage.value = "";
    progressMessage.value = "";
    resultImageSrc.value = "";
    lastErrorMessage.value = "";
    currentRequestId.value = "";
  };

  const startStitching = (imagePaths, options = {}) => {
    if (!Array.isArray(imagePaths) || imagePaths.length < 2) {
      lastErrorMessage.value = "至少选择 2 张图片";
      return null;
    }
    if (!isBackendReady.value) {
      lastErrorMessage.value = "后端未就绪，无法开始拼接";
      return null;
    }
    if (isStitching.value) return currentRequestId.value || null;

    lastErrorMessage.value = "";
    resultImageSrc.value = "";
    progress.value = 0;
    stage.value = "";
    progressMessage.value = "";

    const requestId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    currentRequestId.value = requestId;
    isStitching.value = true;

    sendToBackend("图像拼接", {
      requestId,
      图片路径列表: imagePaths,
    });

    return requestId;
  };

  const startStitchingByDataUrls = (imageDataUrls, options = {}) => {
    if (!Array.isArray(imageDataUrls) || imageDataUrls.length < 2) {
      lastErrorMessage.value = "至少需要 2 帧 dataUrl（可开始截屏模式后获取）";
      return null;
    }
    if (!isBackendReady.value) {
      lastErrorMessage.value = "后端未就绪，无法开始拼接";
      return null;
    }
    if (isStitching.value) return currentRequestId.value || null;

    const list = imageDataUrls.filter((d) => typeof d === "string" && d.startsWith("data:"));
    if (list.length < 2) {
      lastErrorMessage.value = "dataUrl 列表无效";
      return null;
    }

    const skipPipelineSteps = options?.skipPipeline === true;

    lastErrorMessage.value = "";
    resultImageSrc.value = "";
    progress.value = 0;
    stage.value = "";
    progressMessage.value = "";

    const requestId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    currentRequestId.value = requestId;
    isStitching.value = true;

    sendToBackend("图像拼接", {
      requestId,
      图片dataUrl列表: list,
      跳过流水线: skipPipelineSteps,
    });

    return requestId;
  };

  const startIncrementalStitchInitByDataUrl = (dataUrl, sessionId, options = {}) => {
    if (!isBackendReady.value) {
      lastErrorMessage.value = "后端未就绪，无法开始拼接";
      return null;
    }
    if (isStitching.value) return currentRequestId.value || null;
    if (typeof dataUrl !== "string" || !dataUrl.startsWith("data:")) {
      lastErrorMessage.value = "init 需要有效 dataUrl";
      return null;
    }
    if (!sessionId || typeof sessionId !== "string") {
      lastErrorMessage.value = "缺少 sessionId";
      return null;
    }

    const skipPipelineSteps = options?.skipPipeline === true;
    lastErrorMessage.value = "";
    resultImageSrc.value = "";
    progress.value = 0;
    stage.value = "";
    progressMessage.value = "";

    const requestId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    currentRequestId.value = requestId;
    isStitching.value = true;

    sendToBackend("图像拼接", {
      requestId,
      模式: "incremental",
      sessionId,
      增量操作: "init",
      图片dataUrl列表: [dataUrl],
      跳过流水线: skipPipelineSteps,
    });

    return requestId;
  };

  const startIncrementalStitchStepByDataUrl = (dataUrl, sessionId, options = {}) => {
    if (!isBackendReady.value) {
      lastErrorMessage.value = "后端未就绪，无法开始拼接";
      return null;
    }
    if (isStitching.value) return currentRequestId.value || null;
    if (typeof dataUrl !== "string" || !dataUrl.startsWith("data:")) {
      lastErrorMessage.value = "step 需要有效 dataUrl";
      return null;
    }
    if (!sessionId || typeof sessionId !== "string") {
      lastErrorMessage.value = "缺少 sessionId";
      return null;
    }

    const skipPipelineSteps = options?.skipPipeline === true;
    lastErrorMessage.value = "";
    resultImageSrc.value = "";
    progress.value = 0;
    stage.value = "";
    progressMessage.value = "";

    const requestId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    currentRequestId.value = requestId;
    isStitching.value = true;

    sendToBackend("图像拼接", {
      requestId,
      模式: "incremental",
      sessionId,
      增量操作: "step",
      图片dataUrl列表: [dataUrl],
      跳过流水线: skipPipelineSteps,
    });

    return requestId;
  };

  const endIncrementalStitchSession = (sessionId) => {
    if (!isBackendReady.value) return null;
    if (!sessionId || typeof sessionId !== "string") return null;

    const requestId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    // 不改变 store 的 isStitching 状态：只做释放资源
    sendToBackend("图像拼接", {
      requestId,
      模式: "incremental",
      sessionId,
      增量操作: "end",
      图片dataUrl列表: [],
      跳过流水线: true,
    });
    return requestId;
  };

  const handleProgress = (data = {}) => {
    if (!data || typeof data !== "object") return;
    const { requestId } = data;
    if (!requestId || requestId !== currentRequestId.value) return;

    const p = data.progress;
    if (typeof p === "number") {
      progress.value = Math.max(0, Math.min(100, Math.round(p)));
    }
    if (typeof data.stage === "string") stage.value = data.stage;
    if (typeof data.message === "string") progressMessage.value = data.message;
  };

  const handleResult = (data = {}) => {
    if (!data || typeof data !== "object") return;
    const { requestId } = data;
    if (!requestId || requestId !== currentRequestId.value) return;

    isStitching.value = false;
    progress.value = 100;
    stage.value = "done";
    progressMessage.value = "";
    resultImageSrc.value = typeof data.image === "string" ? data.image : "";
  };

  const handleError = (data = {}) => {
    if (!data || typeof data !== "object") return;
    const { requestId } = data;
    if (!requestId || requestId !== currentRequestId.value) return;

    isStitching.value = false;
    stage.value = "error";
    resultImageSrc.value = "";
    lastErrorMessage.value = typeof data.message === "string" ? data.message : "图像拼接失败";
  };

  const socket = getMatchSocket();
  if (socket && typeof socket.on === "function") {
    socket.on("image-stitching-progress", (data) => handleProgress(data || {}));
    socket.on("image-stitching-result", (data) => handleResult(data || {}));
    socket.on("image-stitching-error", (data) => handleError(data || {}));
  }

  const canStart = computed(() => isBackendReady.value && !isStitching.value);

  return {
    // state
    isBackendReady,
    isStitching,
    progress,
    stage,
    progressMessage,
    resultImageSrc,
    lastErrorMessage,

    // computed
    canStart,

    // actions
    reset,
    startStitching,
    startStitchingByDataUrls,
    startIncrementalStitchInitByDataUrl,
    startIncrementalStitchStepByDataUrl,
    endIncrementalStitchSession,
  };
});

