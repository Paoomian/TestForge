<template>
  <div class="login-container">
    <div class="login-left">
      <div class="brand-section">
        <h1 class="brand-title">测试平台</h1>
        <p class="brand-subtitle">UI自动化 · 接口自动化 · 接口调试</p>
        <div class="feature-list">
          <div class="feature-item">
            <icon-check-circle-fill :size="20" />
            <span>Playwright UI自动化录制与执行</span>
          </div>
          <div class="feature-item">
            <icon-check-circle-fill :size="20" />
            <span>接口自动化测试与管理</span>
          </div>
          <div class="feature-item">
            <icon-check-circle-fill :size="20" />
            <span>类Postman接口调试工具</span>
          </div>
          <div class="feature-item">
            <icon-check-circle-fill :size="20" />
            <span>测试报告与数据分析</span>
          </div>
        </div>
      </div>
    </div>

    <div class="login-right">
      <div class="login-box">
        <h2 class="login-title">{{ isLogin ? '登录' : '注册' }}</h2>

        <a-form
          :model="formData"
          layout="vertical"
          @submit="handleSubmit"
        >
          <a-form-item
            field="username"
            label="用户名"
            :rules="[{ required: true, message: '请输入用户名' }]"
          >
            <a-input
              v-model="formData.username"
              placeholder="请输入用户名"
              size="large"
            >
              <template #prefix>
                <icon-user />
              </template>
            </a-input>
          </a-form-item>

          <a-form-item
            v-if="!isLogin"
            field="email"
            label="邮箱"
            :rules="[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '邮箱格式不正确' }
            ]"
          >
            <a-input
              v-model="formData.email"
              placeholder="请输入邮箱"
              size="large"
            >
              <template #prefix>
                <icon-email />
              </template>
            </a-input>
          </a-form-item>

          <a-form-item
            field="password"
            label="密码"
            :rules="[
              { required: true, message: '请输入密码' },
              { minLength: 6, message: '密码至少6位' }
            ]"
          >
            <a-input-password
              v-model="formData.password"
              placeholder="请输入密码"
              size="large"
            >
              <template #prefix>
                <icon-lock />
              </template>
            </a-input-password>
          </a-form-item>

          <a-form-item>
            <a-button
              type="primary"
              html-type="submit"
              size="large"
              long
              :loading="loading"
            >
              {{ isLogin ? '登录' : '注册' }}
            </a-button>
          </a-form-item>
        </a-form>

        <div class="login-footer">
          <a-link @click="toggleMode">
            {{ isLogin ? '没有账号？立即注册' : '已有账号？立即登录' }}
          </a-link>
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
}

.login-left {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
}

.brand-section {
  color: white;
  max-width: 500px;
}

.brand-title {
  font-size: 48px;
  font-weight: 700;
  margin: 0 0 16px 0;
}

.brand-subtitle {
  font-size: 20px;
  opacity: 0.9;
  margin: 0 0 60px 0;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
}

.login-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f7f8fa;
  padding: 60px;
}

.login-box {
  width: 100%;
  max-width: 400px;
  background: white;
  padding: 48px;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
}

.login-title {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 32px 0;
  text-align: center;
}

.login-footer {
  text-align: center;
  margin-top: 24px;
}
</style>
