<template>
  <div class="login-container">
    <!-- 左上角品牌标识 -->
    <div class="brand-logo">
      <div class="logo-icon">
        <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect width="32" height="32" rx="8" fill="url(#logo-gradient)"/>
          <path d="M10 16L14 20L22 12" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          <defs>
            <linearGradient id="logo-gradient" x1="0" y1="0" x2="32" y2="32">
              <stop stop-color="#A78BFA"/>
              <stop offset="1" stop-color="#818CF8"/>
            </linearGradient>
          </defs>
        </svg>
      </div>
      <div class="logo-text">
        <span class="logo-name">Paomian</span>
        <span class="logo-project">TestForge</span>
      </div>
    </div>

    <!-- 左侧插画区 -->
    <div class="login-left">
      <div class="illustration-wrapper">
        <!-- 插画图片 -->
        <div class="illustration-container">
          <img
            src="@/assets/images/login-illustration.png"
            alt="智能测试插画"
            class="illustration-img"
          />
        </div>

        <!-- 文字说明 -->
        <div class="illustration-text">
          <h2 class="illustration-title">智能测试，高效交付</h2>
          <p class="illustration-subtitle">UI自动化 · 接口自动化 · 接口调试</p>
        </div>
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="login-right">
      <!-- 背景装饰 -->
      <div class="bg-decoration">
        <div class="bg-circle bg-circle-1"></div>
        <div class="bg-circle bg-circle-2"></div>
        <div class="bg-circle bg-circle-3"></div>
        <div class="bg-dots"></div>
      </div>

      <div class="login-content">
        <div class="login-box">
          <div class="login-header">
            <h2 class="login-title">{{ isLogin ? 'Sign In' : 'Sign Up' }}</h2>
            <p class="login-subtitle">{{ isLogin ? '欢迎回来，请登录您的账号' : '创建新账号，开始您的测试之旅' }}</p>
          </div>

          <a-form
            :model="formData"
            layout="vertical"
            @submit="handleSubmit"
            class="login-form"
          >
            <a-form-item
              field="username"
              :rules="[{ required: true, message: '请输入用户名' }]"
            >
              <a-input
                v-model="formData.username"
                placeholder="用户名 / Username"
                size="large"
                class="form-input"
              >
                <template #prefix>
                  <icon-user />
                </template>
              </a-input>
            </a-form-item>

            <a-form-item
              v-if="!isLogin"
              field="email"
              :rules="[
                { required: true, message: '请输入邮箱' },
                { type: 'email', message: '邮箱格式不正确' }
              ]"
            >
              <a-input
                v-model="formData.email"
                placeholder="邮箱 / Email"
                size="large"
                class="form-input"
              >
                <template #prefix>
                  <icon-email />
                </template>
              </a-input>
            </a-form-item>

            <a-form-item
              field="password"
              :rules="[
                { required: true, message: '请输入密码' },
                { minLength: 6, message: '密码至少6位' }
              ]"
            >
              <a-input-password
                v-model="formData.password"
                placeholder="密码 / Password"
                size="large"
                class="form-input"
              >
                <template #prefix>
                  <icon-lock />
                </template>
              </a-input-password>
            </a-form-item>

            <div v-if="isLogin" class="form-options">
              <a-checkbox>记住我</a-checkbox>
              <a-link class="forgot-link">忘记密码？</a-link>
            </div>

            <a-form-item>
              <a-button
                type="primary"
                html-type="submit"
                size="large"
                long
                :loading="loading"
                class="submit-btn"
              >
                {{ isLogin ? '登 录' : '注 册' }}
              </a-button>
            </a-form-item>
          </a-form>

          <div class="login-footer">
            <span class="footer-text">
              {{ isLogin ? '还没有账号？' : '已有账号？' }}
            </span>
            <a-link class="toggle-link" @click="toggleMode">
              {{ isLogin ? '立即注册' : '立即登录' }}
            </a-link>
          </div>
        </div>

        <!-- 功能特性介绍 -->
        <div class="features-section">
          <div class="feature-card">
            <div class="feature-icon">
              <!-- Bug 追踪图标 -->
              <svg viewBox="0 0 28 28" width="28" height="28" fill="none">
                <circle cx="14" cy="14" r="12" stroke="#818CF8" stroke-width="1.5" fill="#EDE9FE"/>
                <path d="M10 11C10 11 11 9 14 9C17 9 18 11 18 11" stroke="#818CF8" stroke-width="1.5" stroke-linecap="round"/>
                <circle cx="11" cy="13" r="1.5" fill="#818CF8"/>
                <circle cx="17" cy="13" r="1.5" fill="#818CF8"/>
                <path d="M10 17C10 17 11 19 14 19C17 19 18 17 18 17" stroke="#818CF8" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M8 14H20" stroke="#818CF8" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M8 11L6 9" stroke="#818CF8" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M20 11L22 9" stroke="#818CF8" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M8 17L6 19" stroke="#818CF8" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M20 17L22 19" stroke="#818CF8" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="feature-info">
              <h4 class="feature-title">Bug 追踪</h4>
              <p class="feature-desc">缺陷全生命周期管理</p>
            </div>
          </div>
          <div class="feature-card">
            <div class="feature-icon">
              <!-- 自动化测试图标 -->
              <svg viewBox="0 0 28 28" width="28" height="28" fill="none">
                <circle cx="14" cy="14" r="12" stroke="#A78BFA" stroke-width="1.5" fill="#EDE9FE"/>
                <path d="M14 8V14L18 16" stroke="#A78BFA" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M10 10L8 8" stroke="#A78BFA" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M18 10L20 8" stroke="#A78BFA" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M14 6V4" stroke="#A78BFA" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M14 24V22" stroke="#A78BFA" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M6 14H4" stroke="#A78BFA" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M24 14H22" stroke="#A78BFA" stroke-width="1.5" stroke-linecap="round"/>
                <circle cx="14" cy="14" r="3" fill="#A78BFA" opacity="0.3"/>
                <path d="M12 14L14 12L16 14L14 16Z" fill="#A78BFA"/>
              </svg>
            </div>
            <div class="feature-info">
              <h4 class="feature-title">自动化测试</h4>
              <p class="feature-desc">一键录制与回放执行</p>
            </div>
          </div>
          <div class="feature-card">
            <div class="feature-icon">
              <!-- 测试报告图标 -->
              <svg viewBox="0 0 28 28" width="28" height="28" fill="none">
                <rect x="4" y="2" width="20" height="24" rx="3" stroke="#C4B5FD" stroke-width="1.5" fill="#EDE9FE"/>
                <path d="M9 8H19" stroke="#C4B5FD" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M9 12H19" stroke="#C4B5FD" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M9 16H15" stroke="#C4B5FD" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M9 22L12 19L15 21L19 17" stroke="#818CF8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="19" cy="17" r="2" fill="#818CF8"/>
              </svg>
            </div>
            <div class="feature-info">
              <h4 class="feature-title">测试报告</h4>
              <p class="feature-desc">可视化数据分析</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { useUserStore } from '@/stores/user'
import type { LoginForm, RegisterForm } from '@/types/auth'

const router = useRouter()
const userStore = useUserStore()

const isLogin = ref(true)
const loading = ref(false)

const formData = reactive<LoginForm & RegisterForm>({
  username: '',
  email: '',
  password: ''
})

const toggleMode = () => {
  isLogin.value = !isLogin.value
  formData.username = ''
  formData.email = ''
  formData.password = ''
}

const handleSubmit = async () => {
  loading.value = true
  try {
    if (isLogin.value) {
      await userStore.loginAction({
        username: formData.username,
        password: formData.password
      })
      Message.success('登录成功')
      router.push('/')
    } else {
      await userStore.registerAction({
        username: formData.username,
        email: formData.email,
        password: formData.password
      })
      Message.success('注册成功，请登录')
      isLogin.value = true
      formData.password = ''
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  width: 100%;
  height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  position: relative;
  overflow: hidden;
}

/* 品牌标识 */
.brand-logo {
  position: absolute;
  top: 24px;
  left: 32px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 10;
}

.logo-icon {
  width: 40px;
  height: 40px;
}

.logo-icon svg {
  width: 100%;
  height: 100%;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-name {
  font-size: 14px;
  font-weight: 600;
  color: #6366f1;
  line-height: 1.2;
}

.logo-project {
  font-size: 18px;
  font-weight: 700;
  color: #4f46e5;
  line-height: 1.2;
}

/* 左侧插画区 */
.login-left {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80px 60px 60px;
  background: linear-gradient(135deg, #EDE9FE 0%, #E0E7FF 50%, #DBEAFE 100%);
  position: relative;
}

.login-left::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at 30% 50%, rgba(167, 139, 250, 0.1) 0%, transparent 50%),
              radial-gradient(circle at 70% 50%, rgba(129, 140, 248, 0.1) 0%, transparent 50%);
  animation: float 20s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-20px, -20px); }
}

.illustration-wrapper {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 40px;
}

.illustration-container {
  position: relative;
  width: 100%;
  max-width: 520px;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(99, 102, 241, 0.2),
              0 8px 24px rgba(129, 140, 248, 0.15);
}

/* 图片边缘柔和处理 - 渐变遮罩 */
.illustration-container::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    linear-gradient(to right, rgba(237, 233, 254, 0.8) 0%, transparent 15%, transparent 85%, rgba(224, 231, 255, 0.8) 100%),
    linear-gradient(to bottom, rgba(237, 233, 254, 0.6) 0%, transparent 10%, transparent 90%, rgba(219, 234, 254, 0.6) 100%);
  pointer-events: none;
  border-radius: 24px;
}

.illustration-img {
  width: 100%;
  height: auto;
  display: block;
  object-fit: cover;
  max-height: 420px;
}

.illustration-text {
  text-align: center;
}

.illustration-title {
  font-size: 32px;
  font-weight: 700;
  color: #4338ca;
  margin: 0 0 12px 0;
  letter-spacing: -0.5px;
}

.illustration-subtitle {
  font-size: 16px;
  color: #6366f1;
  margin: 0;
  opacity: 0.8;
}

/* 右侧表单区 */
.login-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(249, 250, 251, 0.95) 100%);
  backdrop-filter: blur(20px);
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.15;
}

.bg-circle-1 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #a78bfa, #818cf8);
  top: -100px;
  right: -80px;
  animation: float-circle 15s ease-in-out infinite;
}

.bg-circle-2 {
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, #c4b5fd, #a78bfa);
  bottom: -60px;
  left: -40px;
  animation: float-circle 12s ease-in-out infinite reverse;
}

.bg-circle-3 {
  width: 150px;
  height: 150px;
  background: linear-gradient(135deg, #e0d4fc, #c4b5fd);
  top: 50%;
  left: 10%;
  animation: float-circle 18s ease-in-out infinite;
}

.bg-dots {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: radial-gradient(circle, #a78bfa 1px, transparent 1px);
  background-size: 30px 30px;
  opacity: 0.05;
}

@keyframes float-circle {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(10px, -15px) scale(1.02); }
  50% { transform: translate(-5px, 10px) scale(0.98); }
  75% { transform: translate(15px, 5px) scale(1.01); }
}

.login-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  width: 100%;
  max-width: 480px;
}

.login-box {
  width: 100%;
  background: white;
  padding: 48px;
  border-radius: 24px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05),
              0 10px 15px -3px rgba(0, 0, 0, 0.05),
              0 20px 40px -4px rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(224, 212, 252, 0.5);
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.login-title {
  font-size: 36px;
  font-weight: 700;
  color: #1e1b4b;
  margin: 0 0 12px 0;
  letter-spacing: -0.5px;
}

.login-subtitle {
  font-size: 15px;
  color: #6b7280;
  margin: 0;
}

.login-form {
  margin-bottom: 24px;
}

.login-form :deep(.arco-form-item) {
  margin-bottom: 20px;
}

.login-form :deep(.arco-form-item:last-child) {
  margin-bottom: 0;
}

.form-input {
  border-radius: 12px !important;
  border: 1.5px solid #e5e7eb !important;
  transition: all 0.2s ease !important;
  height: 48px !important;
}

.form-input:hover {
  border-color: #c4b5fd !important;
}

.form-input:focus,
.form-input:focus-within {
  border-color: #a78bfa !important;
  box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.15) !important;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.forgot-link {
  font-size: 14px;
  color: #6366f1 !important;
}

.submit-btn {
  height: 52px !important;
  border-radius: 14px !important;
  font-size: 17px !important;
  font-weight: 600 !important;
  background: linear-gradient(135deg, #a78bfa 0%, #818cf8 100%) !important;
  border: none !important;
  box-shadow: 0 4px 12px rgba(129, 140, 248, 0.35) !important;
  transition: all 0.2s ease !important;
}

.submit-btn:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 20px rgba(129, 140, 248, 0.45) !important;
}

.submit-btn:active {
  transform: translateY(0) !important;
}

.login-footer {
  text-align: center;
  font-size: 14px;
  color: #6b7280;
  margin-top: 24px;
}

.footer-text {
  margin-right: 4px;
}

.toggle-link {
  color: #6366f1 !important;
  font-weight: 500 !important;
}

/* 功能特性介绍 */
.features-section {
  display: flex;
  gap: 16px;
  width: 100%;
  justify-content: center;
}

.feature-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 16px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 16px;
  border: 1px solid rgba(224, 212, 252, 0.4);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  max-width: 200px;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.12);
  border-color: rgba(167, 139, 250, 0.4);
}

.feature-icon {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #EDE9FE, #E0E7FF);
  border-radius: 14px;
  flex-shrink: 0;
}

.feature-info {
  flex: 1;
  min-width: 0;
}

.feature-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e1b4b;
  margin: 0 0 4px 0;
}

.feature-desc {
  font-size: 12px;
  color: #6b7280;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .features-section {
    flex-direction: column;
    gap: 12px;
    align-items: center;
  }

  .feature-card {
    max-width: 300px;
    width: 100%;
    padding: 12px 16px;
  }
}

@media (max-width: 1024px) {
  .login-left {
    display: none;
  }

  .login-right {
    flex: 1;
    background: linear-gradient(135deg, #EDE9FE 0%, #E0E7FF 50%, #DBEAFE 100%);
  }

  .login-content {
    max-width: 440px;
  }
}

@media (max-width: 480px) {
  .login-right {
    padding: 24px;
  }

  .login-box {
    padding: 32px;
    border-radius: 20px;
  }

  .login-title {
    font-size: 28px;
  }

  .features-section {
    flex-direction: column;
    align-items: center;
  }
}
</style>
