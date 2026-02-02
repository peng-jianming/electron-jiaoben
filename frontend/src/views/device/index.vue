<template>
  <div>
    <el-table :data="list" border size="small" empty-text="没有发现设备~">
      <el-table-column type="selection" width="55"> </el-table-column>
      <el-table-column type="index" label="序号"> </el-table-column>
      <el-table-column label="设备"> </el-table-column>
      <el-table-column label="账号"> </el-table-column>
      <el-table-column label="即将执行的操作"> </el-table-column>
      <el-table-column label="当前在操作"> </el-table-column>
      <el-table-column label="操作">
        <template #default="scope">
          <el-button type="text" size="small">开始</el-button>
          <el-button type="text" size="small">结束</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-button @click="handleGetDeviceList">设备检测</el-button>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { ipcApiRoute } from "@/api";
import { ipc } from "@/utils/ipcRenderer";
import { io } from "socket.io-client";
const list = ref([]);

let matchSocket = null;

 // 初始化 Socket 连接
 function initMatchSocket() {
    if (matchSocket) {
      return;
    }

    matchSocket = io("ws://localhost:7072");
  
    matchSocket.on("connect", () => {
      console.log("匹配 Socket 连接成功");
    });
  
    // 接收设备列表
    matchSocket.on("device-list", (data) => {
      console.log("收到设备id列表:", data);
      list.value = data;
    });
  
  }

const handleGetDeviceList = () => {
  ipc.invoke(ipcApiRoute.发送到后端, {
    "类型": "获取设备列表",
  });
}

onMounted(() => {
  initMatchSocket();
})
</script>

<style scoped></style>
