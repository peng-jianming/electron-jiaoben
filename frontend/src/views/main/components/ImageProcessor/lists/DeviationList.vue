<template>
  <div class="deviation-list">
    <div class="deviation-header">偏色列表</div>
    <div>
      <el-scrollbar height="139px" style="padding: 5px">
        <div style="display: flex; flex-direction: column; gap: 5px">
          <el-tag
            :key="tag"
            v-for="tag in selectedDeviations"
            closable
            :color="`#${tag.split('-')[0]}`"
            :disable-transitions="false"
            @close="handleClose(tag)"
          >
            {{ tag }}
          </el-tag>
        </div>
      </el-scrollbar>
    </div>
    <div style="padding: 0 5px">
      <div>
        <el-input
          v-if="inputVisible"
          v-model="inputValue"
          ref="saveTagInput"
          size="small"
          @keyup.enter="handleInputConfirm"
          @blur="handleInputConfirm"
        >
        </el-input>
        <el-button
          v-else
          style="width: 100%"
          size="small"
          type="primary"
          @click="showInput"
          >添加偏色</el-button
        >
      </div>
      <el-button
        type="danger"
        size="small"
        class="clear-all-btn"
        @click="$emit('clear-deviations')"
      >
        清空偏色
      </el-button>
      <el-button
        type="primary"
        size="small"
        class="clear-all-btn"
        @click="copyDeviations"
      >
        复制偏色
      </el-button>
      <el-button
        type="primary"
        size="small"
        class="clear-all-btn"
        @click="$emit('rerender')"
        :disabled="isPreviewEnabled"
      >
        重新渲染
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from "vue";
import { ElMessage } from "element-plus";

const props = defineProps({
  deviationColors: {
    type: Array,
    default: () => [],
  },
  modelValue: {
    type: Array,
    default: () => [],
  },
  isPreviewEnabled: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update:modelValue", "clear-deviations", "rerender"]);

const inputVisible = ref(false);
const InputRef = ref();
const inputValue = ref("");

const selectedDeviations = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});

const copyDeviations = async () => {
  if (selectedDeviations.value.length === 0) {
    ElMessage.warning("请先选择要复制的偏色");
    return;
  }

  const text = selectedDeviations.value.join("|");

  try {
    await navigator.clipboard.writeText(text);
    ElMessage.success("偏色已复制到剪贴板");
  } catch (err) {
    // 降级方案：使用传统的复制方法
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand("copy");
      ElMessage.success("偏色已复制到剪贴板");
    } catch (e) {
      ElMessage.error("复制失败，请手动复制");
    }
    document.body.removeChild(textArea);
  }
};

const handleClose = (tag) => {
  selectedDeviations.value.splice(selectedDeviations.value.indexOf(tag), 1);
};

const showInput = () => {
  inputVisible.value = true;
  nextTick(() => {
    if (InputRef.value && InputRef.value.input) InputRef.value.input.focus();
  });
};

const handleInputConfirm = () => {
  if (inputValue.value) {
    selectedDeviations.value.push(inputValue.value);
  }
  inputVisible.value = false;
  inputValue.value = "";
};
</script>

<style scoped>
.deviation-list {
  color: #909399;
  border: 1px solid #dcdfe6;
  margin-left: 5px;
  width: 170px;
}

.deviation-header {
  font-size: 14px;
  padding: 5px;
  border-bottom: 1px solid #dcdfe6;
}

.clear-all-btn {
  width: 100%;
  margin-top: 5px;
}

.el-checkbox {
  margin-right: 0;
}
.el-button + .el-button {
  margin-left: 0;
}
</style>
