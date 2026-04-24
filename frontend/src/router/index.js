import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { title: '登录', public: true }
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
  // 1. 公开页面（登录页）直接放行
  if (to.meta.public) {
    next()
    return
  }

  // 2. 检查是否已登录（有 token）
  const token = localStorage.getItem('token')
  if (!token) {
    next('/login')
    return
  }

  // 3. 验证 token 是否有效
  try {
    await axios.get('/api/auth/verify', {
      headers: { Authorization: `Bearer ${token}` }
    })
  } catch (err) {
    // token 无效或过期，清除并跳转登录
    localStorage.removeItem('token')
    next('/login')
    return
  }

  // 4. 已登录，检查系统是否初始化
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
    next()
  }
})

router.afterEach((to) => {
  document.title = `${to.meta.title || 'YOLO-SmartHome'} - 智能家居视觉感知系统`
})

export default router
