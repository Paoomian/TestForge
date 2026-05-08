import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'
import MainLayout from '@/layouts/MainLayout.vue'
import Login from '@/views/Login.vue'
import Dashboard from '@/views/Dashboard.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'dashboard',
        component: Dashboard
      },
      {
        path: 'projects',
        name: 'project-list',
        component: () => import('@/views/projects/ProjectList.vue')
      },
      {
        path: 'ui-cases',
        name: 'ui-cases',
        component: () => import('@/views/ui-test/CaseList.vue')
      },
      {
        path: 'ui-record',
        name: 'ui-record',
        component: () => import('@/views/ui-test/Record.vue')
      },
      {
        path: 'ui-run',
        name: 'ui-run',
        component: () => import('@/views/ui-test/Run.vue')
      },
      {
        path: 'api-cases',
        name: 'api-cases',
        component: () => import('@/views/api-test/CaseList.vue')
      },
      {
        path: 'api-test-manage',
        name: 'api-test-manage',
        component: () => import('@/views/api-test/TestCaseManage.vue')
      },
      {
        path: 'api-record',
        name: 'api-record',
        component: () => import('@/views/api-test/Record.vue')
      },
      {
        path: 'api-run',
        name: 'api-run',
        component: () => import('@/views/api-test/Run.vue')
      },
      {
        path: 'api-debug',
        name: 'api-debug',
        component: () => import('@/views/api-debug/Index.vue')
      },
      {
        path: 'reports',
        name: 'report-list',
        component: () => import('@/views/reports/ReportList.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, _from, next) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth !== false) {
    if (!userStore.token) {
      next('/login')
      return
    }

    if (!userStore.userInfo) {
      try {
        await userStore.fetchUserInfo()
      } catch (error) {
        userStore.logout()
        next('/login')
        return
      }
    }
  }

  if (to.path === '/login' && userStore.token) {
    next('/')
    return
  }

  next()
})

export default router
