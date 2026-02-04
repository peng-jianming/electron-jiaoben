<template>
  <div class="device-container">
    <!-- 任务选择与配置 -->
    <div class="toolbar-section">
      <div class="task-select-wrapper">
        <TaskSelect
          :task-list="taskList"
          v-model="taskSelectValue"
        />
      </div>
      <div class="action-buttons">
        <el-button type="primary" @click="handleBatchStart">全部开始</el-button>
        <el-button type="warning" @click="handleBatchPause">全部暂停</el-button>
        <el-button type="success" @click="handleBatchResume">全部恢复</el-button>
        <el-button type="danger" @click="handleBatchEnd">全部结束</el-button>
        <el-button plain @click="emit('getDeviceList')">设备检测</el-button>
      </div>
    </div>

    <div class="table-container">
      <el-table 
        :data="list" 
        border 
        size="small" 
        empty-text="没有发现设备~"
        height="100%"
        stripe
        highlight-current-row
      >
        <el-table-column type="index" label="序号" width="60" align="center"> </el-table-column>
        <el-table-column label="设备ID" prop="设备ID" min-width="150" show-overflow-tooltip> </el-table-column>
        <el-table-column label="当前账号" width="120" show-overflow-tooltip>
          <template #default="scope">
            <el-tag size="small" v-if="scope.row.当前账号?.账号">{{ scope.row.当前账号?.账号 }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" prop="已暂停" width="80" align="center">
            <template #default="scope">
                <el-tag type="warning" v-if="scope.row.已暂停" size="small">已暂停</el-tag>
                <el-tag type="success" v-else size="small">运行中</el-tag>
            </template>
        </el-table-column>
        <el-table-column label="当前任务" prop="当前任务" min-width="120" show-overflow-tooltip> </el-table-column>
        <el-table-column label="下一任务" prop="下一任务" min-width="120" show-overflow-tooltip> </el-table-column>
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="scope">
            <el-button
              link
              type="primary"
              size="small"
              :disabled="!taskSelectValue.selectedTasks.length"
              @click="handleStart(scope.row)"
              >开始</el-button
            >
            <el-button
              v-if="!scope.row.已暂停"
              link
              type="warning"
              size="small"
              @click="emit('pauseTask', scope.row)"
              >暂停</el-button
            >
            <el-button
              v-else
              link
              type="success"
              size="small"
              @click="emit('resumeTask', scope.row)"
              >恢复</el-button
            >
            <el-button link type="danger" size="small" @click="emit('endTask', scope.row)"
              >结束</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, ref, toRaw  } from "vue";
import TaskSelect from "./components/TaskSelect.vue";
import { ElMessage } from "element-plus";

const props = defineProps({
  list: {
    type: Array,
    default: () => [],
  },
  taskList: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits([
  "startTask",
  "pauseTask",
  "resumeTask",
  "endTask",
  "getDeviceList",
]);

// 任务选择：选中的任务顺序 + 每任务配置
const taskSelectValue = ref({
  selectedTasks: [],
  taskConfig: {},
});

function handleStart(row) {
  const { selectedTasks, taskConfig } = taskSelectValue.value;
  if (!selectedTasks.length) {
    ElMessage.warning("请先选择任务");
    return;
  }
  
  emit("startTask", row, {
    任务队列: JSON.parse(JSON.stringify([...selectedTasks])),
    任务配置: JSON.parse(JSON.stringify({...taskConfig})),
  });
}

const handleBatchStart = () => {
    const { selectedTasks, taskConfig } = taskSelectValue.value;
    if (!selectedTasks.length) {
        ElMessage.warning("请先选择任务");
        return;
    }
    props.list.forEach(row => {
        emit("startTask", row, {
            任务队列: JSON.parse(JSON.stringify([...selectedTasks])),
            任务配置: JSON.parse(JSON.stringify({...taskConfig})),
        });
    });
}

const handleBatchPause = () => {
    props.list.forEach(row => {
        if (!row.已暂停) emit("pauseTask", row);
    });
}

const handleBatchResume = () => {
    props.list.forEach(row => {
        if (row.已暂停) emit("resumeTask", row);
    });
}

const handleBatchEnd = () => {
    props.list.forEach(row => {
        emit("endTask", row);
    });
}

</script>

<style scoped lang="less">
.device-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.toolbar-section {
  padding-bottom: 15px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 15px;
}

.task-select-wrapper {
  /* Adjust based on TaskSelect component style */
}

.action-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.table-container {
  flex: 1;
  overflow: hidden;
}
</style>
