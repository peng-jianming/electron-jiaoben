<template>
  <router-view />
</template>
<script setup>
import { onMounted } from 'vue';

onMounted(() => {
  const loadingElement = document.getElementById('loadingPage');
  if (loadingElement) {
    loadingElement.remove();
  }
});
</script>
<style>
.el-button + .el-button {
  margin-left: 0;
}
.el-form-item {
  margin-bottom: 5px;
}
/* 全局消除 el-divider 的默认 margin */
.el-divider--horizontal {
  margin: 6px 0;
}
</style>
