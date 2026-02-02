<template>
  <el-tabs type="border-card">
    <el-tab-pane label="设备列表"><Device/></el-tab-pane>
    <el-tab-pane label="账号列表"><Account/></el-tab-pane>
    <el-tab-pane label="任务配置">任务配置</el-tab-pane>
  </el-tabs>
</template>

<!-- <template>
  <div id="hero">
    <div>
      <el-button type="primary" @click="handleGetDeviceList">重置所有</el-button>
      <el-button type="primary" @click="handleStart(list)">全部开始</el-button>
      <el-button type="primary" @click="handleStop(list)">全部结束</el-button>
      <el-table :data="list" border>
        <el-table-column prop="deviceId" label="句柄" width="180"> </el-table-column>
        <el-table-column prop="name" label="窗口名" width="180"> </el-table-column>
        <el-table-column prop="isRunning" label="是否运行" width="180"> </el-table-column>
        <el-table-column prop="currentTask" label="当前任务" width="180">
        </el-table-column>
        <el-table-column prop="logs" label="日志" width="180"> </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button type="primary" @click="handleStart([scope.row])" size="small"
              >开始</el-button
            >
            <el-button type="primary" @click="handleStop([scope.row])" size="small"
              >结束</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template> -->

<script setup>
import Account from './account/index.vue';
import Device from './device/index.vue';
</script>

<style scoped>

</style>
