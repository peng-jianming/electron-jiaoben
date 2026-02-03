<template>
  <div>
    <el-table :data="list" border size="small" empty-text="没有发现设备~">
      <el-table-column type="index" label="序号"> </el-table-column>
      <el-table-column label="设备ID" prop="设备ID" width="180"> </el-table-column>
      <el-table-column label="当前账号" width="120">
        <template #default="scope">
          {{ scope.row.当前账号?.账号 || "-" }}
        </template>
      </el-table-column>
      <el-table-column label="是否暂停" prop="已暂停"> </el-table-column>
      <el-table-column label="当前任务" prop="当前任务"> </el-table-column>
      <el-table-column label="下一任务" prop="下一任务"> </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button type="text" size="small" @click="emit('startTask', scope.row)"
            >开始</el-button
          >
          <el-button
            v-if="!scope.row.已暂停"
            type="text"
            size="small"
            @click="emit('pauseTask', scope.row)"
            >暂停</el-button
          >
          <el-button
            v-else
            type="text"
            size="small"
            @click="emit('resumeTask', scope.row)"
            >恢复</el-button
          >
          <el-button type="text" size="small" @click="emit('endTask', scope.row)"
            >结束</el-button
          >
        </template>
      </el-table-column>
    </el-table>

    <el-button >全部开始</el-button>
    <el-button >全部暂停</el-button>
    <el-button >全部恢复</el-button>
    <el-button >全部结束</el-button>
    <el-button @click="emit('getDeviceList')">设备检测</el-button>
    {{ taskList }}
    
  </div>
</template>

<script setup>
import { defineProps, defineEmits, ref } from "vue";

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

</script>

<style scoped></style>
