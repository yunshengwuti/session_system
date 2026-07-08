import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/sessions'
  },
  {
    path: '/sessions',
    name: 'Sessions',
    component: () => import('../views/SessionList.vue'),
    meta: { title: '会话列表' }
  },
  {
    path: '/sessions/:id',
    name: 'SessionDetail',
    component: () => import('../views/SessionDetail.vue'),
    meta: { title: '会话详情' }
  },
  {
    path: '/reports/daily',
    name: 'DailyReports',
    component: () => import('../views/DailyReports.vue'),
    meta: { title: '日报管理' }
  },
  {
    path: '/reports/weekly',
    name: 'WeeklyReports',
    component: () => import('../views/WeeklyReports.vue'),
    meta: { title: '周报管理' }
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('../views/Upload.vue'),
    meta: { title: '数据上传' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || '会话数据管理系统'
  next()
})

export default router
