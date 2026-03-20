import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { storeToRefs } from "pinia";
import { useImageProcessingStore } from "@/stores/imageProcessing";
import { useFloodFillStore } from "@/stores/floodFill";
import { getMatchSocket } from "@/utils/matchSocket";

export const usePathFindingStore = defineStore("pathFinding", () => {
  const imageProcessingStore = useImageProcessingStore();
  const floodFillStore = useFloodFillStore();
  const { isBackendReady } = storeToRefs(imageProcessingStore);

  const inputImage = ref({ source: "path", id: "" }); // source: path | processing
  const inputPreview = ref("");

  const skeletonImage = ref("");
  const resultImage = ref("");
  const lastErrorMessage = ref("");

  const startPoint = ref({ x: null, y: null });
  const endPoint = ref({ x: null, y: null });
  const imageNaturalWidth = ref(0);
  const imageNaturalHeight = ref(0);

  const isGettingSkeleton = ref(false);
  const isFinding = ref(false);

  const pendingUploadResolvers = ref({});

  const hasImage = computed(() => {
    return !!(inputImage.value?.id || inputPreview.value);
  });

  const hasStart = computed(() => startPoint.value?.x !== null && startPoint.value?.y !== null);
  const hasEnd = computed(() => endPoint.value?.x !== null && endPoint.value?.y !== null);

  const inputDisplayImageSrc = computed(() => {
    if (inputImage.value.source === "processing") return imageProcessingStore.displayImageSrc || "";
    return inputPreview.value || "";
  });

  const sendToBackend = (类型, extra = {}) => {
    if (!isBackendReady.value) return;
    imageProcessingStore.sendToBackend(类型, extra);
  };

  const handlePathImageUpload = (payload) => {
    const safe = payload || {};
    const path = safe.path || "";
    const preview = safe.preview || "";
    if (!path) return;

    inputPreview.value = preview || "";
    inputImage.value = { source: "path", id: "" };
    skeletonImage.value = "";
    resultImage.value = "";
    lastErrorMessage.value = "";
    startPoint.value = { x: null, y: null };
    endPoint.value = { x: null, y: null };

    const requestId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    pendingUploadResolvers.value[requestId] = () => {};
    sendToBackend("路线规划上传缓存", { 图片路径: path, requestId });
  };

  const handlePathImageUploaded = (payload) => {
    const data = payload || {};
    const requestId = data.requestId;
    const hasRequestId = typeof requestId === "string" && !!requestId;
    const hasPendingRequest =
      hasRequestId &&
      !!pendingUploadResolvers.value &&
      Object.prototype.hasOwnProperty.call(pendingUploadResolvers.value, requestId);

    // 忽略不属于当前寻路模块发起的上传回包，避免和其他页面/功能串数据
    if (hasRequestId && !hasPendingRequest) return;

    if (typeof data.imageId === "string") {
      inputImage.value = { source: "path", id: data.imageId };
    }
    if (typeof data.preview === "string") {
      inputPreview.value = data.preview;
    }

    if (requestId && hasPendingRequest) {
      try {
        const resolver = pendingUploadResolvers.value[requestId];
        if (typeof resolver === "function") {
          resolver({ imageId: data.imageId, preview: data.preview });
        }
      } finally {
        delete pendingUploadResolvers.value[requestId];
      }
    }
  };

  const uploadBase64AsInput = async (dataUrl) => {
    if (!dataUrl) return null;
    const requestId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const p = new Promise((resolve) => {
      pendingUploadResolvers.value[requestId] = resolve;
    });

    sendToBackend("路线规划上传base64缓存", { dataUrl, requestId });
    const res = await p;
    if (res?.imageId) inputImage.value = { source: "path", id: res.imageId };
    return res?.imageId || null;
  };

  const useFloodFillResultAsInput = async () => {
    const dataUrl = floodFillStore.resultDisplayImageSrc;
    if (!dataUrl) return null;

    inputPreview.value = dataUrl;
    inputImage.value = { source: "path", id: "" };
    skeletonImage.value = "";
    resultImage.value = "";
    lastErrorMessage.value = "";
    startPoint.value = { x: null, y: null };
    endPoint.value = { x: null, y: null };

    return await uploadBase64AsInput(dataUrl);
  };

  const setImageNaturalSize = (width, height) => {
    imageNaturalWidth.value = width || 0;
    imageNaturalHeight.value = height || 0;
  };

  const setPointByImagePoint = ({ type, x, y }) => {
    if (x === null || y === null || x === undefined || y === undefined) return;
    const nx = Math.max(0, Math.min((imageNaturalWidth.value || 0) - 1, Math.round(Number(x))));
    const ny = Math.max(0, Math.min((imageNaturalHeight.value || 0) - 1, Math.round(Number(y))));
    if (!Number.isFinite(nx) || !Number.isFinite(ny)) return;

    if (type === "start") startPoint.value = { x: nx, y: ny };
    if (type === "end") endPoint.value = { x: nx, y: ny };
  };

  const getSkeleton = () => {
    const imageId = inputImage.value?.id;
    if (!imageId) return;
    isGettingSkeleton.value = true;
    skeletonImage.value = "";
    lastErrorMessage.value = "";
    sendToBackend("路线规划获取骨干网", {
      imageId,
      imageSource: inputImage.value.source || "path",
    });
  };

  const handleSkeletonResult = (payload) => {
    const data = payload || {};
    skeletonImage.value = data.image || "";
    isGettingSkeleton.value = false;
  };

  const startFinding = () => {
    const imageId = inputImage.value?.id;
    if (!imageId) return;
    if (!hasStart.value || !hasEnd.value) return;

    isFinding.value = true;
    resultImage.value = "";
    lastErrorMessage.value = "";

    sendToBackend("路线规划计算", {
      imageId,
      imageSource: inputImage.value.source || "path",
      start: { x: startPoint.value.x, y: startPoint.value.y },
      end: { x: endPoint.value.x, y: endPoint.value.y },
    });
  };

  const handleFindingResult = (payload) => {
    const data = payload || {};
    resultImage.value = data.image || "";
    isFinding.value = false;
  };

  const handleError = (payload) => {
    const msg = (payload && payload.message) || "寻路失败";
    lastErrorMessage.value = String(msg);
    isGettingSkeleton.value = false;
    isFinding.value = false;
  };

  const socket = getMatchSocket();
  socket.on("route-path-image-uploaded", (data) => handlePathImageUploaded(data || {}));
  socket.on("route-skeleton-result", (data) => handleSkeletonResult(data || {}));
  socket.on("route-finding-result", (data) => handleFindingResult(data || {}));
  socket.on("route-finding-error", (data) => handleError(data || {}));

  return {
    // state
    inputImage,
    inputPreview,
    skeletonImage,
    resultImage,
    lastErrorMessage,
    startPoint,
    endPoint,
    imageNaturalWidth,
    imageNaturalHeight,
    isGettingSkeleton,
    isFinding,

    // computed
    hasImage,
    hasStart,
    hasEnd,
    inputDisplayImageSrc,

    // actions
    handlePathImageUpload,
    useFloodFillResultAsInput,
    setImageNaturalSize,
    setPointByImagePoint,
    getSkeleton,
    startFinding,
  };
});

