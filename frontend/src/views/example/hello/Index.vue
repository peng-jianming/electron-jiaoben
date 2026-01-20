<template>
  <div class="image-processor">
    <!-- Tab 切换 -->
    <el-tabs v-model="activeTab"  type="border-card">
      <!-- 图片处理 Tab -->
      <el-tab-pane label="图片处理" name="image-processor">
        <ImageProcessorTab />
      </el-tab-pane>

      <!-- 调色 Tab -->
      <el-tab-pane label="调色" name="coloring">
        <ColoringTab ref="coloringTabRef" />
      </el-tab-pane>

      <!-- 寻路测试 Tab -->
      <el-tab-pane label="寻路测试" name="pathfinding">
        <PathfindingTab />
      </el-tab-pane>
    </el-tabs>

    <!-- 处理状态指示器 -->
    <transition name="fade">
      <div v-if="coloringTabRef?.processing" class="processing-indicator">
        <div class="spinner"></div>
        <span>处理中...</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from "vue";
import ImageProcessorTab from "./components/ImageProcessor/ImageProcessorTab.vue";
import ColoringTab from "./components/ColoringTab/ColoringTab.vue";
import PathfindingTab from "./components/PathfindingTab/PathfindingTab.vue";

// Tab 切换
const activeTab = ref("image-processor");

// 调色 Tab 的引用
const coloringTabRef = ref(null);
</script>

<style scoped>
/* 基础变量 */
.image-processor {
  --primary-color: #6366f1;
  --primary-light: #818cf8;
  --primary-dark: #4f46e5;
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --danger-color: #ef4444;
  --bg-dark: #0f172a;
  --bg-card: #1e293b;
  --bg-card-hover: #334155;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --border-color: #334155;
  --shadow-lg: 0 10px 40px rgba(0, 0, 0, 0.3);

  height: 100vh;
  background: linear-gradient(135deg, var(--bg-dark) 0%, #1a1a2e 50%, #16213e 100%);
  color: var(--text-primary);
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}

/* 顶部标题栏 */
.app-header {
  background: rgba(30, 41, 59, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1600px;
  margin: 0 auto;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.logo-icon svg {
  width: 24px;
  height: 24px;
  color: white;
}

.logo-section h1 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  background: linear-gradient(90deg, var(--text-primary), var(--primary-light));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

:deep(.el-tabs__content) {
  padding: 2px;
}



/* 处理状态指示器 */
.processing-indicator {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  background: var(--bg-card);
  border: 1px solid var(--primary-color);
  border-radius: 12px;
  box-shadow: var(--shadow-lg);
  z-index: 1000;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
