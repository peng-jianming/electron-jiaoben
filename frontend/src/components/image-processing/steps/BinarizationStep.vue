<template>
  <div class="binarization-step">
    <div class="label-row">
      <span class="label">阈值：</span>
      <span class="value">{{ data.threshold }}</span>
    </div>
    <input
      type="range"
      min="0"
      max="255"
      v-model.number="data.threshold"
      class="slider"
    />
  </div>
</template>

<script setup>
import { ref, watch } from "vue";

const props = defineProps({
  data: {
    type: Object,
    default() {
      return {};
    },
  },
});
</script>

<style scoped>
.binarization-step {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label {
  color: #4b5563;
}

.value {
  color: #111827;
  font-weight: 600;
}

.slider {
  width: 100%;
}
</style>
