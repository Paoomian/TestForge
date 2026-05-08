import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login, register, getUserInfo } from '@/api/auth'
import type { LoginForm, RegisterForm, UserInfo } from '@/types/auth'

export const useUserStore = defineStore('user', () => {
  // access_token（短期，30分钟）
  const token = ref<string>(localStorage.getItem('token') || '')
  // refresh_token（长期，7天）
  const refreshToken = ref<string>(localStorage.getItem('refresh_token') || '')
  const userInfo = ref<UserInfo | null>(null)

  // 设置token（登录/刷新时调用）
  const setToken = (newToken: string, newRefreshToken?: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
    if (newRefreshToken) {
      refreshToken.value = newRefreshToken
      localStorage.setItem('refresh_token', newRefreshToken)
    }
  }

  const clearToken = () => {
    token.value = ''
    refreshToken.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
  }

  const loginAction = async (loginForm: LoginForm) => {
    const res = await login(loginForm)
    setToken(res.access_token, res.refresh_token)
    await fetchUserInfo()
    return res
  }

  const registerAction = async (registerForm: RegisterForm) => {
    return await register(registerForm)
  }

  const fetchUserInfo = async () => {
    const res = await getUserInfo()
    userInfo.value = res
    return res
  }

  const logout = () => {
    clearToken()
    userInfo.value = null
  }

  return {
    token,
    refreshToken,
    userInfo,
    setToken,
    loginAction,
    registerAction,
    fetchUserInfo,
    logout
  }
})
