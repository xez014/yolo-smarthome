import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { title: '实时监控', icon: '📡' }
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('../views/SearchView.vue'),
    meta: { title: '物品检索', icon: '🔍' }
  },
  {
    path: '/stats',
    name: 'Stats',
    component: () => import('../views/StatsView.vue'),
    meta: { title: '数据统计', icon: '📊' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.afterEach((to) => {
  document.title = `${to.meta.title || 'YOLO-SmartHome'} - 智能家居视觉感知系统`
})

export default router
