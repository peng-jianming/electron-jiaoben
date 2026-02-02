<template>
  <el-tabs type="border-card">
    <el-tab-pane label="设备列表"><Device/></el-tab-pane>
    <el-tab-pane label="账号列表"><Account/></el-tab-pane>
    <el-tab-pane label="任务配置">任务配置</el-tab-pane>
  </el-tabs>
</template>

<script setup>
import Account from './account/index.vue';
import Device from './device/index.vue';
</script>

<style scoped>

</style>
