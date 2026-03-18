<template>
  <div class="morph-step">
    <div class="form-row">
      <label class="form-label">核大小 (奇数)：</label>
      <input
        class="form-input"
        type="number"
        min="1"
        step="2"
        v-model.number="inner.kernelSize"
      />
    </div>
    <div class="form-row">
      <label class="form-label">迭代次数：</label>
      <input
        class="form-input"
        type="number"
        min="1"
        step="1"
        v-model.number="inner.iterations"
      />
    </div>
    <div class="form-row">
      <label class="form-label">核形状：</label>
      <select class="form-select" v-model="inner.kernelShape">
        <option value="rect">矩形</option>
        <option value="cross">十字形</option>
        <option value="ellipse">椭圆</option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { watch, reactive } from "vue";

const props = defineProps({
  data: {
    type: Object,
    default: () => ({}),
  },
});

const inner = reactive({
  kernelSize: props.data.kernelSize ?? 3,
  iterations: props.data.iterations ?? 1,
  kernelShape: props.data.kernelShape ?? "rect",
});

const normalize = () => {
  if (!Number.isFinite(inner.kernelSize)) inner.kernelSize = 3;
  if (!Number.isFinite(inner.iterations)) inner.iterations = 1;

  inner.kernelSize = Math.max(1, Math.round(inner.kernelSize));
  if (inner.kernelSize % 2 === 0) {
    inner.kernelSize += 1;
  }
  inner.iterations = Math.max(1, Math.round(inner.iterations));

  if (!["rect", "cross", "ellipse"].includes(inner.kernelShape)) {
    inner.kernelShape = "rect";
  }
};

watch(
  inner,
  (val) => {
    normalize();
    props.data.kernelSize = val.kernelSize;
    props.data.iterations = val.iterations;
    props.data.kernelShape = val.kernelShape;
  },
  { deep: true, immediate: true }
);
</script>

<style scoped>
.morph-step {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: center;
}

.form-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.form-label {
  font-size: 12px;
  color: #4b5563;
}

.form-input,
.form-select {
  width: 80px;
  height: 24px;
  padding: 0 6px;
  font-size: 12px;
  border-radius: 4px;
  border: 1px solid #d1d5db;
  box-sizing: border-box;
}
</style>

