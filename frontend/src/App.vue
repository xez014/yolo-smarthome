<template>
  <div class="app-layout dark" :class="{ 'no-sidebar': isSetupPage }">
    <!-- 侧边栏 -->
    <aside class="sidebar" v-if="!isSetupPage">
      <div class="sidebar-header">
        <div class="sidebar-logo">
          <div class="logo-icon">🏠</div>
          <div>
            <div class="logo-text">SmartHome</div>
            <div class="logo-sub">YOLO 视觉感知系统</div>
          </div>
        </div>
      </div>
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          active-class="active"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
      <div style="padding: 16px 12px; border-top: 1px solid var(--border-color);">
        <div style="font-size: 11px; color: var(--text-muted); text-align: center;">
          YOLOv11 · FastAPI · Vue 3
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <KeepAlive include="DashboardView">
            <component :is="Component" />
          </KeepAlive>
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isSetupPage = computed(() => route.path === '/setup')

const navItems = [
  { path: '/dashboard', icon: '📡', label: '实时监控' },
  { path: '/search', icon: '🔍', label: '物品检索' },
  { path: '/stats', icon: '📊', label: '数据统计' },
]
</script>

<style scoped>
/* App-level overrides are in global.css */
.no-sidebar {
  display: block; /* 取消 grid 布局 */
}
.no-sidebar .main-content {
  padding: 0;
  height: 100vh;
}
</style>
