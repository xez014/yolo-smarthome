import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/setup',
    name: 'Setup',
    component: () => import('../views/SetupView.vue'),
    meta: { title: '系统初始化' }
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

import axios from 'axios'

router.beforeEach(async (to, from, next) => {
  try {
    const res = await axios.get('/api/system/status')
    const isSetup = res.data.is_setup
    
    if (!isSetup && to.path !== '/setup') {
      next('/setup')
    } else if (isSetup && to.path === '/setup') {
      next('/dashboard')
    } else {
      next()
    }
  } catch (err) {
    // 若请求连不通，说明可能正在启动，先放行或引至setup
    next()
  }
})

router.afterEach((to) => {
  document.title = `${to.meta.title || 'YOLO-SmartHome'} - 智能家居视觉感知系统`
})

export default router
