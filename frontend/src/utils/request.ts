import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { Message } from '@arco-design/web-vue'
import { useUserStore } from '@/stores/user'
import router from '@/router'

// 扩展Axios类型，让拦截器返回response.data
declare module 'axios' {
  interface AxiosInstance {
    <T = any>(config: AxiosRequestConfig): Promise<T>
    <T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
  }
}

const service: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 是否正在刷新token
let isRefreshing = false
// 等待刷新的请求队列
let pendingRequests: Array<(token: string) => void> = []

// 处理队列中的请求（刷新成功后用新token重试）
const processQueue = (newToken: string) => {
  pendingRequests.forEach(callback => callback(newToken))
  pendingRequests = []
}

// 请求拦截器：自动注入token
service.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：处理401自动刷新
service.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  async (error) => {
    const originalRequest = error.config

    if (error.response) {
      const { status, data } = error.response

      // 401且不是刷新/登录请求 → 尝试用refresh_token续期
      if (status === 401 && !originalRequest._retry
        && !originalRequest.url.includes('/auth/refresh')
        && !originalRequest.url.includes('/auth/login')) {

        const userStore = useUserStore()

        // 没有refresh_token → 直接跳登录
        if (!userStore.refreshToken) {
          userStore.logout()
          router.push('/login')
          Message.error('登录已过期，请重新登录')
          return Promise.reject(error)
        }

        // 如果正在刷新中，把当前请求加入队列等待
        if (isRefreshing) {
          return new Promise((resolve) => {
            pendingRequests.push((newToken: string) => {
              originalRequest.headers.Authorization = `Bearer ${newToken}`
              resolve(service(originalRequest))
            })
          })
        }

        // 开始刷新
        isRefreshing = true
        originalRequest._retry = true

        try {
          // 直接调用刷新接口（用axios原始实例，避免拦截器死循环）
          const res = await axios.post('/api/v1/auth/refresh', null, {
            params: { refresh_token: userStore.refreshToken }
          })

          const { access_token, refresh_token } = res.data
          // 更新token
          userStore.setToken(access_token, refresh_token)
          // 处理队列中的请求
          processQueue(access_token)
          // 重试原始请求
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return service(originalRequest)
        } catch (refreshError) {
          // 刷新失败 → 清除登录态，跳转登录页
          userStore.logout()
          router.push('/login')
          Message.error('登录已过期，请重新登录')
          pendingRequests = []
          return Promise.reject(refreshError)
        } finally {
          isRefreshing = false
        }
      }

      // 其他错误正常处理
      if (status === 403) {
        Message.error('没有权限访问')
      } else if (status === 404) {
        Message.error('请求的资源不存在')
      } else if (status === 500) {
        Message.error('服务器错误')
      } else if (status !== 401) {
        Message.error(data.detail || '请求失败')
      }
    } else {
      Message.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default service
