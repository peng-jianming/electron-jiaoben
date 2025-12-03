<template>
  <div>
    <el-button @click="handleStart(deviceList)">全部开始 </el-button>
    <el-button @click="handleStop(deviceList)">全部停止 </el-button>
    <el-table :data="deviceList" border>
      <el-table-column prop="hwnd" label="句柄" width="180"> </el-table-column>
      <el-table-column prop="name" label="窗口名" width="180"> </el-table-column>
      <el-table-column prop="status" label="当前任务" width="180"> </el-table-column>
      <el-table-column prop="action" label="当前动作" width="180"> </el-table-column>
      <el-table-column label="操作">
        <template slot-scope="scope">
          <el-button @click="handleStart([scope.row])" type="text" size="small"
            >开始</el-button
          >
          <el-button @click="handleStop([scope.row])" type="text" size="small"
            >结束</el-button
          >
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";

const props = defineProps({
  deviceList: {
    type: Array,
    default() {
      return [];
    },
  },
  socket: {
    type: WebSocket,
    default: null,
  },
});

const handleStart = async (list) => {
  socket.value.send(
    JSON.stringify({
      type: "start",
      deviceList: list,
      taskList: ["shimen"],
    })
  );
  console.log("发送开始指令");
};
const handleStop = async (list) => {
  socket.value.send(
    JSON.stringify({
      type: "stop",
      deviceList: list,
      data: {},
    })
  );
  console.log("发送停止指令");
};
</script>

<style scoped></style>
