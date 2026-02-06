<template>
  <div class="app-container">
    <!-- 顶部标题栏 - 固定高度40px -->
    <TitleBar title="图色助手" />
    
    <!-- 主内容区域 -->
    <div class="main-wrapper">
      <!-- Tab 导航栏 -->
      <div class="tab-nav">
        <div 
          v-for="tab in tabs" 
          :key="tab.name"
          class="tab-item"
          :class="{ active: activeTab === tab.name }"
          @click="activeTab = tab.name"
        >
          <component :is="tab.icon" class="tab-icon" />
          <span>{{ tab.label }}</span>
        </div>
        <!-- 状态指示器 -->
        <div class="status-indicator" :class="{ processing: isProcessing }">
          <span class="status-dot"></span>
          <span>{{ isProcessing ? '处理中' : '就绪' }}</span>
        </div>
      </div>
      
      <!-- 路由内容区域 -->
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
import { ref, computed, watch, watchEffect, onUnmounted, h } from "vue";
import { useRoute, useRouter } from "vue-router";
import TitleBar from "@/components/TitleBar.vue";

const route = useRoute();
const router = useRouter();

// 导航图标组件
const IconImage = () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor', class: 'tab-icon-svg' }, [
  h('path', { d: 'M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z' })
]);

const IconPalette = () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor', class: 'tab-icon-svg' }, [
  h('path', { d: 'M12 2C6.49 2 2 6.49 2 12s4.49 10 10 10c1.38 0 2.5-1.12 2.5-2.5 0-.61-.23-1.2-.64-1.67-.08-.1-.13-.21-.13-.33 0-.28.22-.5.5-.5H16c3.31 0 6-2.69 6-6 0-4.96-4.49-9-10-9zm-5.5 9c-.83 0-1.5-.67-1.5-1.5S5.67 8 6.5 8 8 8.67 8 9.5 7.33 11 6.5 11zm3-4C8.67 7 8 6.33 8 5.5S8.67 4 9.5 4s1.5.67 1.5 1.5S10.33 7 9.5 7zm5 0c-.83 0-1.5-.67-1.5-1.5S13.67 4 14.5 4s1.5.67 1.5 1.5S15.33 7 14.5 7zm3 4c-.83 0-1.5-.67-1.5-1.5S16.67 8 17.5 8s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z' })
]);

const IconRoute = () => h('svg', { viewBox: '0 0 24 24', fill: 'currentColor', class: 'tab-icon-svg' }, [
  h('path', { d: 'M9.78 11.16l-1.42 1.42a7.282 7.282 0 01-1.79-2.94l1.94-.49c.32.89.77 1.5 1.27 2.01zM11 6L7 2 3 6h3.02c.02.81.08 1.54.19 2.17l1.94-.49C8.08 7.2 8.03 6.63 8.02 6H11zm10 0l-4-4-4 4h2.99c-.1 3.68-1.28 4.75-2.54 5.88-.5.44-1.01.92-1.45 1.55-.34-.49-.73-.88-1.13-1.24L9.46 13.6c.93.85 1.54 1.54 1.54 3.4v5h2v-5c0-2.02.71-2.66 1.79-3.63 1.38-1.24 3.08-2.78 3.2-7.37H21z' })
]);

// Tab配置
const tabs = [
  { name: 'image-processor', label: '图片处理', icon: IconImage },
  { name: 'coloring', label: '调色面板', icon: IconPalette },
  { name: 'pathfinding', label: '寻路测试', icon: IconRoute }
];

// Tab 切换 - 从路由获取当前激活的 tab
const activeTab = computed({
  get: () => {
    const routeName = route.name;
    if (routeName === 'Coloring') return 'coloring';
    if (routeName === 'Pathfinding') return 'pathfinding';
    return 'image-processor';
  },
  set: (value) => {
    const routeName = value === 'image-processor' ? 'ImageProcessor' : value === 'coloring' ? 'Coloring' : 'Pathfinding';
    router.push({ name: routeName });
  }
});

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
/* ===== 设计系统变量 ===== */
@primary: #6366f1;
@primary-light: #818cf8;
@primary-dark: #4f46e5;
@success: #10b981;
@warning: #f59e0b;
@danger: #ef4444;

/* 浅色主题 */
@bg-main: #f8fafc;
@bg-content: #ffffff;
@bg-hover: #f1f5f9;
@text-primary: #1e293b;
@text-secondary: #64748b;
@text-muted: #94a3b8;
@border: #e2e8f0;
@shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);

/* 固定尺寸 */
@title-bar-height: 40px;
@tab-nav-height: 36px;

/* ===== 容器布局 ===== */
.app-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: @bg-main;
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  overflow: hidden;
}

/* ===== 主内容包装器 ===== */
.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

/* ===== Tab 导航栏 ===== */
.tab-nav {
  height: @tab-nav-height;
  min-height: @tab-nav-height;
  max-height: @tab-nav-height;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 12px;
  background: @bg-content;
  border-bottom: 1px solid @border;
  box-sizing: border-box;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: @text-secondary;
  transition: all 0.2s ease;
  
  &:hover {
    background: @bg-hover;
    color: @text-primary;
  }
  
  &.active {
    background: fade(@primary, 10%);
    color: @primary;
    
    .tab-icon-svg {
      color: @primary;
    }
  }
}

.tab-icon-svg {
  width: 16px;
  height: 16px;
}

/* 状态指示器 */
.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  margin-left: auto;
  background: fade(@success, 10%);
  border-radius: 16px;
  font-size: 12px;
  color: @success;
  transition: all 0.3s ease;
  
  &.processing {
    background: fade(@primary, 10%);
    color: @primary;
    
    .status-dot {
      background: @primary;
      animation: blink 1s ease-in-out infinite;
    }
  }
}

.status-dot {
  width: 6px;
  height: 6px;
  background: @success;
  border-radius: 50%;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* ===== 路由内容容器 ===== */
.router-view-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background: @bg-main;
  display: flex;
  flex-direction: column;
}

/* 确保子组件中的 tabs 内容正常显示 */
.router-view-container :deep(.el-tabs__content) {
  display: block !important;
}

/* ===== 处理遮罩层 ===== */
.processing-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
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
  padding: 32px 48px;
  background: @bg-content;
  border-radius: 16px;
  box-shadow: @shadow-lg;
}

.spinner-ring {
  width: 48px;
  height: 48px;
  border: 3px solid @border;
  border-radius: 50%;
  position: relative;
  animation: spin 1.5s linear infinite;
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
