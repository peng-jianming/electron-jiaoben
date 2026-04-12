<template>
  <div class="app-container">
    <!-- 顶部标题栏 - 固定高度40px -->
    <TitleBar title="图色助手" />
    
    <!-- 主内容区域 -->
    <div class="main-wrapper">
      <!-- 内容区域 -->
      <div class="router-view-container">
        <router-view v-slot="{ Component }">
          <component 
            :is="Component" 
            ref="currentComponentRef"
          />
        </router-view>
      </div>
    </div>
    
    <!-- 全局处理遮罩 -->
    <transition name="fade">
      <div v-if="isProcessing" class="processing-overlay">
        <div class="processing-card">
          <div class="spinner-ring">
            <div class="spinner-ring-inner"></div>
          </div>
          <span class="processing-text">正在处理，请稍候...</span>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, watch, watchEffect, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import TitleBar from "@/components/TitleBar.vue";

const route = useRoute();

// 处理状态
const isProcessing = ref(false);
const currentComponentRef = ref(null);

// 监听组件实例的 processing 状态
let stopWatcher = null;

watchEffect(() => {
  if (currentComponentRef.value) {
    const component = currentComponentRef.value;
    
    if (component.processing !== undefined) {
      if (typeof component.processing === 'object' && 'value' in component.processing) {
        if (stopWatcher) {
          stopWatcher();
        }
        stopWatcher = watch(
          () => component.processing.value,
          (newVal) => {
            isProcessing.value = newVal;
          },
          { immediate: true }
        );
      } else {
        isProcessing.value = component.processing;
      }
    } else {
      isProcessing.value = false;
      if (stopWatcher) {
        stopWatcher();
        stopWatcher = null;
      }
    }
  } else {
    isProcessing.value = false;
    if (stopWatcher) {
      stopWatcher();
      stopWatcher = null;
    }
  }
});

// 监听路由变化，重置处理状态
watch(() => route.name, () => {
  isProcessing.value = false;
  if (stopWatcher) {
    stopWatcher();
    stopWatcher = null;
  }
});

onUnmounted(() => {
  if (stopWatcher) {
    stopWatcher();
  }
});
</script>

<style scoped lang="less">
/* ===== 设计令牌 ===== */
@primary: #6366f1;
@primary-light: #818cf8;
@primary-dark: #4f46e5;
@success: #10b981;
@warning: #f59e0b;
@danger: #ef4444;

@bg-main: #eef0f4;
@bg-content: #ffffff;
@bg-hover: #f1f5f9;
@text-primary: #1e293b;
@text-secondary: #64748b;
@text-muted: #94a3b8;
@border: #e2e8f0;
@border-strong: #cbd5e1;
@shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
@shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -2px rgba(0, 0, 0, 0.06);
@shadow-lg: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.06);

/* 固定尺寸（与 electron/config/config.default.js 窗口 1920×1080 一致） */
@app-width: 1920px;
@app-height: 1080px;
@title-bar-height: 40px;
@content-height: @app-height - @title-bar-height;

/* ===== 容器 ===== */
.app-container {
  width: @app-width;
  height: @app-height;
  max-width: @app-width;
  max-height: @app-height;
  min-width: @app-width;
  min-height: @app-height;
  display: flex;
  flex-direction: column;
  background: @bg-main;
  font-family: -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  overflow: hidden;
  box-sizing: border-box;
}

/* ===== 主包装器 ===== */
.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: calc(@app-height - @title-bar-height);
  min-height: 0;
  overflow: hidden;
}

/* ===== 内容容器 ===== */
.router-view-container {
  height: @content-height;
  max-height: @content-height;
  min-height: 0;
  overflow: hidden;
  background: @bg-main;
  display: flex;
  flex-direction: column;
}

/* 勿对全局 el-tabs__content 写 display:block !important，会打断图色处理器右侧 Tab 的 flex 链，导致配置页无法滚动 */

/* 图色处理器页铺满内容区高度 */
.router-view-container :deep(.image-processor-tab) {
  flex: 1;
  min-height: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* ===== 处理遮罩层 ===== */
.processing-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.processing-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 36px 52px;
  background: @bg-content;
  border-radius: 16px;
  box-shadow: @shadow-lg;
  border: 1px solid rgba(99, 102, 241, 0.08);
}

.spinner-ring {
  width: 44px;
  height: 44px;
  border: 3px solid @border;
  border-radius: 50%;
  position: relative;
  animation: spin 1.2s linear infinite;
}

.spinner-ring-inner {
  position: absolute;
  top: -3px;
  left: -3px;
  right: -3px;
  bottom: -3px;
  border: 3px solid transparent;
  border-top-color: @primary;
  border-radius: 50%;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.processing-text {
  font-size: 14px;
  color: @text-secondary;
  font-weight: 500;
  letter-spacing: 0.3px;
}

/* ===== 过渡动画 ===== */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
