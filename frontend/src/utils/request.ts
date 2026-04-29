import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { Message } from '@arco-design/web-vue'
import { useUserStore } from '@/stores/user'
import router from '@/router'

const service: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

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

service.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response

      if (status === 401) {
        const userStore = useUserStore()
        userStore.logout()
        router.push('/login')
        Message.error('登录已过期，请重新登录')
      } else if (status === 403) {
        Message.error('没有权限访问')
      } else if (status === 404) {
        Message.error('请求的资源不存在')
      } else if (status === 500) {
        Message.error('服务器错误')
      } else {
        Message.error(data.detail || '请求失败')
      }
    } else {
      Message.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default service
