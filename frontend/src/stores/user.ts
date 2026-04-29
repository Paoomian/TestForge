import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login, register, getUserInfo } from '@/api/auth'
import type { LoginForm, RegisterForm, UserInfo } from '@/types/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<UserInfo | null>(null)

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const clearToken = () => {
    token.value = ''
    localStorage.removeItem('token')
  }

  const loginAction = async (loginForm: LoginForm) => {
    const res = await login(loginForm)
    setToken(res.access_token)
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
    userInfo,
    loginAction,
    registerAction,
    fetchUserInfo,
    logout
  }
})
