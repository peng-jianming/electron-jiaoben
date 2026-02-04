<template>
  <div class="device-container">
    <!-- 操作按钮栏 -->
    <div class="toolbar-section">
      <div class="task-info">
        <span class="task-info-label">已选任务：</span>
        <span v-if="taskSelectValue.selectedTasks.length" class="task-info-value">
          {{ taskSelectValue.selectedTasks.join(" → ") }}
        </span>
        <span v-else class="task-info-empty">未选择任务，请到"任务"页面配置</span>
      </div>
      <div class="action-buttons">
        <el-button
          type="primary"
          @click="handleBatchStart"
          :disabled="!taskSelectValue.selectedTasks.length"
          >全部开始</el-button
        >
        <el-button type="warning" @click="handleBatchPause">全部暂停</el-button>
        <el-button type="success" @click="handleBatchResume">全部恢复</el-button>
        <el-button type="danger" @click="handleBatchEnd">全部结束</el-button>
      </div>
    </div>

    <div class="table-container">
      <el-table
        :data="list"
        row-key="设备ID"
        :expand-row-keys="expandedRowKeys"
        @expand-change="onExpandChange"
        :row-class-name="tableRowClassName"
        border
        size="small"
        empty-text="没有发现设备~"
        height="100%"
        stripe
        highlight-current-row
      >
      <el-table-column type="expand">
      <template #default="props">
        <p v-for="item in props.row.日志" :key="item">{{ item }}</p>
      </template>
    </el-table-column>
        <el-table-column type="index" label="序号" width="60" align="center">
        </el-table-column>
        <el-table-column label="设备ID" prop="设备ID" show-overflow-tooltip width="150">
        </el-table-column>
        <el-table-column label="状态" prop="已暂停" align="center" width="100">
          <template #default="scope">
            <el-tag type="warning" v-if="scope.row.已暂停" size="small">已暂停</el-tag>
            <el-tag type="success" v-else-if="scope.row.当前任务" size="small"
              >运行中</el-tag
            >
            <el-tag type="info" v-else size="small">空闲</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="当前任务" prop="当前任务" show-overflow-tooltip>
        </el-table-column>
        <el-table-column label="下一任务" prop="下一任务" show-overflow-tooltip>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right" align="center">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              :disabled="!props.taskSelectValue.selectedTasks.length"
              @click="handleStart(scope.row)"
              >开始</el-button
            >
            <el-button
              v-if="!scope.row.已暂停"
              type="warning"
              size="small"
              @click="emit('pauseTask', scope.row)"
              >暂停</el-button
            >
            <el-button
              v-else
              type="success"
              size="small"
              @click="emit('resumeTask', scope.row)"
              >恢复</el-button
            >
            <el-button type="danger" size="small" @click="emit('endTask', scope.row)"
              >结束</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </div>
    <!-- 统计信息 -->
    <div class="statistics-info">
      <div class="statistics-info-item statistics-info-item--total">
        <div class="statistics-info-item-main">
          <span class="statistics-info-item-label">总设备数</span>
          <span class="statistics-info-item-value">{{ list.length }}</span>
        </div>
      </div>
      <div class="statistics-info-item statistics-info-item--running">
        <div class="statistics-info-item-main">
          <span class="statistics-info-item-label">运行中设备</span>
          <span class="statistics-info-item-value">{{
            list.filter((item) => !item.已暂停 && item.当前任务).length
          }}</span>
        </div>
      </div>
      <div class="statistics-info-item statistics-info-item--idle">
        <div class="statistics-info-item-main">
          <span class="statistics-info-item-label">空闲设备</span>
          <span class="statistics-info-item-value">{{
            list.filter((item) => !item.已暂停 && !item.当前任务).length
          }}</span>
        </div>
      </div>
      <div class="statistics-info-item statistics-info-item--paused">
        <div class="statistics-info-item-main">
          <span class="statistics-info-item-label">已暂停设备</span>
          <span class="statistics-info-item-value">{{
            list.filter((item) => item.已暂停).length
          }}</span>
        </div>
      </div>
      <div
        class="statistics-info-item statistics-info-item--fault"
        :class="{ 'fault-animate': list.some((item) => item.故障) }"
      >
        <div class="statistics-info-item-main">
          <span class="statistics-info-item-label">故障设备</span>
          <span class="statistics-info-item-value">{{
            list.filter((item) => item.故障).length
          }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits } from "vue";
import { ElMessage } from "element-plus";

const props = defineProps({
  list: {
    type: Array,
    default: () => [],
  },
  taskSelectValue: {
    type: Object,
    default: () => ({ selectedTasks: [], taskConfig: {} }),
  },
});

const emit = defineEmits([
  "startTask",
  "pauseTask",
  "resumeTask",
  "endTask",
  "getDeviceList",
]);

// 受控展开行：数据更新时保持已展开行不收起
const expandedRowKeys = ref([]);
watch(
  () => props.list,
  (list) => {
    // 仅保留当前列表中仍存在的设备 ID，避免残留无效 key
    expandedRowKeys.value = expandedRowKeys.value.filter((key) =>
      list.some((row) => row.设备ID === key)
    );
  },
  { deep: true }
);
function onExpandChange(_row, expandedRows) {
  expandedRowKeys.value = expandedRows.map((r) => r.设备ID);
}

const tableRowClassName = ({ row }) => {
  return row.故障 ? "fault-row" : "";
};

function handleStart(row) {
  const { selectedTasks, taskConfig } = props.taskSelectValue;
  if (!selectedTasks.length) {
    ElMessage.warning("请先到「任务」页面选择任务");
    return;
  }

  emit("startTask", row, {
    任务队列: JSON.parse(JSON.stringify([...selectedTasks])),
    任务配置: JSON.parse(JSON.stringify({ ...taskConfig })),
  });
}

const handleBatchStart = () => {
  const { selectedTasks, taskConfig } = props.taskSelectValue;
  if (!selectedTasks.length) {
    ElMessage.warning("请先到「任务」页面选择任务");
    return;
  }
  props.list.forEach((row) => {
    emit("startTask", row, {
      任务队列: JSON.parse(JSON.stringify([...selectedTasks])),
      任务配置: JSON.parse(JSON.stringify({ ...taskConfig })),
    });
  });
};

const handleBatchPause = () => {
  props.list.forEach((row) => {
    if (!row.已暂停) emit("pauseTask", row);
  });
};

const handleBatchResume = () => {
  props.list.forEach((row) => {
    if (row.已暂停) emit("resumeTask", row);
  });
};

const handleBatchEnd = () => {
  props.list.forEach((row) => {
    emit("endTask", row);
  });
};
</script>

<style scoped lang="less">
@primary-color: #409eff;
@success-color: #67c23a;
@warning-color: #e6a23c;
@danger-color: #f56c6c;
@border-color: #e4e7ed;
@text-secondary: #606266;
@text-muted: #909399;

.device-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.toolbar-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  flex-shrink: 0;
  padding-bottom: 12px;
  border-bottom: 1px solid @border-color;
  margin-bottom: 12px;
}

.task-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.task-info-label {
  font-size: 13px;
  color: @text-secondary;
  flex-shrink: 0;
}

.task-info-value {
  font-size: 13px;
  color: @primary-color;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-info-empty {
  font-size: 13px;
  color: @text-muted;
  font-style: italic;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: nowrap;
  flex-shrink: 0;

  :deep(.el-button) {
    border-radius: 6px;
    font-weight: 500;
    font-size: 13px;
    padding: 8px 15px;

    &--primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border: none;

      &:hover {
        background: linear-gradient(135deg, #5a6fd6 0%, #6a4293 100%);
      }
    }

    &--success {
      background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
      border: none;

      &:hover {
        background: linear-gradient(135deg, #0f8a80 0%, #32d671 100%);
      }
    }

    &--warning {
      background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
      border: none;

      &:hover {
        background: linear-gradient(135deg, #e085ec 0%, #e04d61 100%);
      }
    }

    &--danger {
      background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
      border: none;

      &:hover {
        background: linear-gradient(135deg, #e63a61 0%, #e64327 100%);
      }
    }
  }
}

.table-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;

  :deep(.el-table) {
    border-radius: 8px;

    th.el-table__cell {
      background-color: #f8f9fa !important;
      color: @text-secondary;
      font-weight: 600;
      font-size: 13px;
    }

    .el-table__row {
      transition: background-color 0.2s ease;

      &:hover > td {
        background-color: #f5f7fa !important;
      }
    }

    .el-table__row.fault-row > td {
      animation: fault-row-blink 1s ease-in-out infinite;
    }

    .el-tag {
      border-radius: 4px;
      font-weight: 500;
      // 禁用标签自身的过渡动画，避免行高在状态切换时被“撑开”
      transition: none;
    }
  }
}
.statistics-info {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  flex-shrink: 0;
  padding-top: 6px;
  margin-top: 8px;
  border-top: 1px solid @border-color;
  position: relative;
  z-index: 999;
}

.statistics-info-item {
  position: relative;
  padding: 6px 10px;
  margin: 2px;
  border-radius: 8px;
  background: #f9fafb;
  border: 1px solid fade(@border-color, 50%);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
  display: flex;
  align-items: center;
  justify-content: space-between;
  overflow: hidden;
  transition: all 0.15s ease;

  &::after {
    content: "";
    position: absolute;
    right: -14px;
    top: -14px;
    width: 38px;
    height: 38px;
    border-radius: 999px;
    background: radial-gradient(circle at center, rgba(255, 255, 255, 0.8), transparent);
    opacity: 0.6;
  }

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(15, 23, 42, 0.08);
  }
}

.statistics-info-item-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
  position: relative;
  z-index: 1;
}

.statistics-info-item-label {
  font-size: 11px;
  color: @text-muted;
}

.statistics-info-item-value {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: #1f2933;
}

.statistics-info-item--total {
  background: linear-gradient(135deg, #eef2ff, #e0f2fe);
  border-color: fade(@primary-color, 60%);

  .statistics-info-item-value {
    color: @primary-color;
  }
}

.statistics-info-item--running {
  background: linear-gradient(135deg, #ecfdf3, #dcfce7);
  border-color: fade(@success-color, 60%);

  .statistics-info-item-value {
    color: @success-color;
  }
}

.statistics-info-item--idle {
  background: linear-gradient(135deg, #f8fafc, #e2e8f0);
  border-color: fade(@text-muted, 40%);

  .statistics-info-item-value {
    color: @text-secondary;
  }
}

.statistics-info-item--paused {
  background: linear-gradient(135deg, #fff7ed, #fef3c7);
  border-color: fade(@warning-color, 60%);

  .statistics-info-item-value {
    color: @warning-color;
  }
}

.statistics-info-item--fault {
  background: linear-gradient(135deg, #fee2e2, #fecaca);
  border-color: fade(@danger-color, 60%);

  .statistics-info-item-value {
    color: @danger-color;
  }
}

@keyframes fault-row-blink {
  0%,
  100% {
    background-color: #fff5f5;
  }
  50% {
    background-color: #ffe1e1;
  }
}

@keyframes fault-stat-blink {
  0%,
  100% {
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
  }
  50% {
    box-shadow: 0 0 0 2px fade(@danger-color, 55%);
  }
}

.fault-animate {
  animation: fault-stat-blink 1s ease-in-out infinite;
}
</style>
