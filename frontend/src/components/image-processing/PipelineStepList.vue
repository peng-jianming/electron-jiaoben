<template>
  <div class="pipeline-step-list">
    <div class="toolbar">
      <label class="toolbar-label">添加处理模块：</label>
      <select v-model="selectedModule" class="module-select">
        <option disabled value="">请选择模块</option>
        <option v-for="item in enumList" :key="item.type" :value="item.type">
          {{ item.type }}
        </option>
      </select>
      <button class="add-btn" @click="addModule" :disabled="!selectedModule">添加</button>
    </div>

    <div class="steps-container">
      <div v-if="!steps.length" class="empty-tip">
        暂未添加任何处理步骤，请在上方选择模块后点击添加。
      </div>
      <VueDraggable
        v-if="steps.length"
        v-model="steps"
        item-key="id"
        handle=".step-header"
      >
        <div
          v-for="(step, index) in steps"
          :key="step.id"
          class="step-item"
        >
          <div class="step-header">
            <span class="step-title">
              {{ index + 1 }}. {{ step.type }}
            </span>
            <button class="remove-btn" @click="removeStep(index)">删除</button>
          </div>
          <div class="step-body">
            <BinarizationStep v-if="step.type === '二值化'" :data="step.params" />
            <ColorFilterStep
              v-else-if="step.type === '颜色过滤'"
              :data="step.params"
              :image-src="props.imageSrc"
              :image-id="props.imageId"
            />
          </div>
        </div>
      </VueDraggable>
    </div>

    <div class="footer">
      <button
        class="process-btn"
        @click="handleProcess"
        :disabled="!steps.length || !canProcess"
      >
        处理
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { VueDraggable } from "vue-draggable-plus";
import BinarizationStep from "./steps/BinarizationStep.vue";
import ColorFilterStep from "./steps/ColorFilterStep.vue";

const props = defineProps({
  canProcess: {
    type: Boolean,
    default: true,
  },
  imageId: {
    type: String,
    default: "",
  },
  imageSrc: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["process"]);

const selectedModule = ref("");
const steps = ref([]);
const enumList = [
  {
    type: "二值化",
    params: {
      threshold: 127,
    },
  },
  {
    type: "颜色过滤",
    params: {},
  },
];

const addModule = () => {
  if (!selectedModule.value) return;

  const base = JSON.parse(
    JSON.stringify(enumList.find((item) => item.type === selectedModule.value))
  );

  steps.value.push({
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    ...base,
  });
};

const removeStep = (index) => {
  steps.value.splice(index, 1);
};

const handleProcess = () => {
  const paramsArr = steps.value.map((step) => ({
    type: step.type,
    params: { ...step.params },
  }));
  console.log(paramsArr, "process");
  
  emit("process", paramsArr);
};
</script>

<style scoped>
.pipeline-step-list {
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  padding: 12px;
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-label {
  font-size: 13px;
  color: #4b5563;
}

.module-select {
  flex: 1;
  min-width: 0;
  height: 28px;
  padding: 0 8px;
  font-size: 13px;
  border-radius: 4px;
  border: 1px solid #d1d5db;
  box-sizing: border-box;
}

.add-btn {
  padding: 4px 10px;
  font-size: 13px;
  border-radius: 4px;
  border: 1px solid #3b82f6;
  background-color: #3b82f6;
  color: #ffffff;
  cursor: pointer;
}

.add-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.steps-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 260px;
  overflow-y: auto;
}

.empty-tip {
  font-size: 12px;
  color: #9ca3af;
}

.step-item {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 8px;
  background-color: #f9fafb;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.step-title {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.remove-btn {
  padding: 2px 8px;
  font-size: 12px;
  border-radius: 4px;
  border: 1px solid #ef4444;
  background-color: #ffffff;
  color: #ef4444;
  cursor: pointer;
}

.step-body {
  padding-top: 4px;
}

.footer {
  display: flex;
  justify-content: flex-end;
}

.process-btn {
  padding: 6px 16px;
  font-size: 13px;
  border-radius: 4px;
  border: none;
  background-color: #10b981;
  color: #ffffff;
  cursor: pointer;
}

.process-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
</style>
