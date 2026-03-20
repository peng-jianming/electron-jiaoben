import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { storeToRefs } from "pinia";
import { useImageProcessingStore } from "@/stores/imageProcessing";
import { getMatchSocket } from "@/utils/matchSocket";

export const usePathFindingTestStore = defineStore("pathFindingTest", () => {
  const imageProcessingStore = useImageProcessingStore();
  const { isBackendReady, displayImageSrc } = storeToRefs(imageProcessingStore);

  const originalMapDisplayImageSrc = ref("");
  const originalMapUploading = ref(false);
  const originalMapUploadRequestId = ref("");
  const originalMapUploadTimeout = ref(null);

  const matchMapImageSrc = ref("");
  const lastErrorMessage = ref("");

  const hasOriginalMap = computed(() => !!originalMapDisplayImageSrc.value);

  const clearOriginalMapUploading = () => {
    originalMapUploadRequestId.value = "";
    originalMapUploading.value = false;
    if (originalMapUploadTimeout.value) {
      clearTimeout(originalMapUploadTimeout.value);
      originalMapUploadTimeout.value = null;
    }
  };

  const sendToBackend = (类型, extra = {}) => {
    if (!isBackendReady.value) return;
    imageProcessingStore.sendToBackend(类型, extra);
  };

  const handleOriginalMapUploaded = (payload = {}) => {
    const data = payload || {};
    if (!originalMapUploadRequestId.value) return;

    const requestId = data.requestId;
    if (!requestId || requestId !== originalMapUploadRequestId.value) return;

    if (typeof data.preview === "string") {
      originalMapDisplayImageSrc.value = data.preview || "";
    }
    clearOriginalMapUploading();
  };

  const handleMatchMapFrame = (payload = {}) => {
    const data = payload || {};
    if (typeof data.image === "string") {
      matchMapImageSrc.value = data.image || "";
    }
  };

  const handleError = (payload = {}) => {
    const msg = (payload && payload.message) || "寻路测试失败";
    lastErrorMessage.value = String(msg);
    clearOriginalMapUploading();
  };

  const uploadOriginalMapByPayload = async (payload = {}, useBase64 = false) => {
    const requestId = `path-finding-test-original-map-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    originalMapUploadRequestId.value = requestId;
    originalMapUploading.value = true;
    lastErrorMessage.value = "";

    if (originalMapUploadTimeout.value) {
      clearTimeout(originalMapUploadTimeout.value);
    }

    originalMapUploadTimeout.value = setTimeout(() => {
      if (originalMapUploadRequestId.value === requestId) {
        lastErrorMessage.value = "原始地图上传超时，请重试";
        clearOriginalMapUploading();
      }
    }, 10000);

    try {
      if (useBase64) {
        const 类型 = "寻路测试上传base64缓存";
        const dataUrl = payload.dataUrl || "";
        sendToBackend(类型, { dataUrl, requestId });
      } else {
        const 类型 = "寻路测试上传缓存";
        const 图片路径 = payload.图片路径 || "";
        sendToBackend(类型, { 图片路径, requestId });
      }
    } catch (e) {
      clearOriginalMapUploading();
      lastErrorMessage.value = "发送原始地图到后端失败";
    }
  };

  const uploadOriginalMapByFile = (filePath) => {
    if (!filePath) return;
    uploadOriginalMapByPayload({ 图片路径: filePath }, false);
  };

  const useImageProcessingResultAsOriginalMap = () => {
    if (!displayImageSrc.value) {
      lastErrorMessage.value = "当前没有图片处理结果可用";
      return;
    }
    uploadOriginalMapByPayload({ dataUrl: displayImageSrc.value }, true);
  };

  // ===== socket 事件订阅（一次性注册即可）=====
  const socket = getMatchSocket();
  if (socket && typeof socket.on === "function") {
    socket.on("path-finding-test-image-uploaded", (data) => handleOriginalMapUploaded(data || {}));
    socket.on("path-finding-test-match-map-frame", (data) => handleMatchMapFrame(data || {}));
    socket.on("path-finding-test-error", (data) => handleError(data || {}));
  }

  return {
    // state
    originalMapDisplayImageSrc,
    originalMapUploading,
    matchMapImageSrc,
    lastErrorMessage,

    // computed
    hasOriginalMap,

    // actions
    uploadOriginalMapByFile,
    useImageProcessingResultAsOriginalMap,
  };
});

