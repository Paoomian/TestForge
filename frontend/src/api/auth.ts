import request from '@/utils/request'
import type { LoginForm, RegisterForm, UserInfo, TokenResponse } from '@/types/auth'

export const login = (data: LoginForm) => {
  return request<TokenResponse>({
    url: '/auth/login',
    method: 'post',
    data
  })
}

export const register = (data: RegisterForm) => {
  return request<UserInfo>({
    url: '/auth/register',
    method: 'post',
    data
  })
}

export const getUserInfo = () => {
  return request<UserInfo>({
    url: '/auth/me',
    method: 'get'
  })
}

export const logout = () => {
  return request({
    url: '/auth/logout',
    method: 'post'
  })
}

// 刷新token（直接用axios，不走拦截器，避免死循环）
export const refreshToken = (refresh_token: string) => {
  return request<TokenResponse>({
    url: '/auth/refresh',
    method: 'post',
    params: { refresh_token }
  })
}
