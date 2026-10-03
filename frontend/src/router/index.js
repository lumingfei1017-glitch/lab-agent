import { getToken } from '@/utils/auth'
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/manager/home' },
    {
      path: '/manager',
      name: 'Layout',
      component: () => import('@/layouts/Layout.vue'),
      children: [
        { path: 'home', name: 'Home', component: () => import('@/views/Home.vue') },
        { path: 'lab', name: 'Lab', component: () => import('@/views/Lab.vue') }
      ]
    },
    { path: '/login', name: 'login', component: () => import('@/views/Login.vue') },
    { path: '/register', name: 'register', component: () => import('@/views/Register.vue') }
  ]
})

//路由守卫：验证token
router.beforeEach((to, from) => {
  const token = getToken()
  if (to.path === '/login' || to.path === '/register') {
    return true
  } else {
    console.log('当前前往页面：', to.path)
    return token ? true : '/login'
  }
})

export default router
