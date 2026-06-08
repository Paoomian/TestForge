<template>
  <a-layout class="layout-container">
    <a-layout-header class="layout-header">
      <div class="header-left">
        <div class="logo">
          <div class="logo-icon">
            <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="32" height="32" rx="8" fill="url(#header-logo-grad)"/>
              <path d="M10 16L14 20L22 12" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
              <defs>
                <linearGradient id="header-logo-grad" x1="0" y1="0" x2="32" y2="32">
                  <stop stop-color="#A78BFA"/>
                  <stop offset="1" stop-color="#818CF8"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <span class="logo-text">TestForge</span>
        </div>
      </div>
      <div class="header-right">
        <a-dropdown>
          <div class="user-info">
            <a-avatar :size="32" class="user-avatar">
              <icon-user />
            </a-avatar>
            <span class="username">{{ userStore.userInfo?.username }}</span>
          </div>
          <template #content>
            <a-doption>
              <template #icon>
                <icon-user />
              </template>
              个人中心
            </a-doption>
            <a-doption>
              <template #icon>
                <icon-settings />
              </template>
              设置
            </a-doption>
            <a-doption @click="handleLogout">
              <template #icon>
                <icon-export />
              </template>
              退出登录
            </a-doption>
          </template>
        </a-dropdown>
      </div>
    </a-layout-header>

    <a-layout class="layout-body">
      <a-layout-sider
        :width="220"
        :collapsed="collapsed"
        collapsible
        @collapse="handleCollapse"
        class="layout-sider"
      >
        <a-menu
          :selected-keys="[activeMenuKey]"
          :style="{ width: '100%' }"
          @menu-item-click="handleMenuClick"
        >
          <a-menu-item key="dashboard">
            <template #icon>
              <icon-dashboard />
            </template>
            仪表盘
          </a-menu-item>

          <a-sub-menu key="projects">
            <template #icon>
              <icon-folder />
            </template>
            <template #title>项目管理</template>
            <a-menu-item key="project-list">项目列表</a-menu-item>
          </a-sub-menu>

          <a-sub-menu key="ui-test">
            <template #icon>
              <icon-desktop />
            </template>
            <template #title>UI自动化</template>
            <a-menu-item key="ui-cases">用例管理</a-menu-item>
            <a-menu-item key="ui-record">录制用例</a-menu-item>
            <a-menu-item key="ui-run">执行测试</a-menu-item>
          </a-sub-menu>

          <a-sub-menu key="api-test">
            <template #icon>
              <icon-code />
            </template>
            <template #title>接口自动化</template>
            <a-menu-item key="api-debug">接口调试</a-menu-item>
            <a-menu-item key="api-test-manage">用例管理</a-menu-item>
            <a-menu-item key="api-run">任务配置</a-menu-item>
            <a-menu-item key="api-batch-tasks">任务记录</a-menu-item>
          </a-sub-menu>

          <a-menu-item key="ai-generate">
            <template #icon>
              <icon-robot />
            </template>
            AI 生成用例
          </a-menu-item>

          <a-sub-menu key="tools">
            <template #icon>
              <icon-tool />
            </template>
            <template #title>常用工具</template>
            <a-menu-item key="tools">工具目录</a-menu-item>
            <a-menu-item key="monkey">Monkey测试</a-menu-item>
          </a-sub-menu>
        </a-menu>
      </a-layout-sider>

      <a-layout-content class="layout-content">
        <div class="content-wrapper">
          <router-view v-slot="{ Component }">
            <keep-alive :include="cachedViews">
              <component :is="Component" />
            </keep-alive>
          </router-view>
        </div>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Modal, Message } from '@arco-design/web-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const collapsed = ref(false)

// 子路由 → 父菜单项映射
const childRouteMap: Record<string, string> = {
  'api-batch-task-detail': 'api-batch-tasks',
  'api-test-debug': 'api-debug',
}

const activeMenuKey = computed(() => {
  const name = route.name as string
  return childRouteMap[name] || name
})

// 需要缓存的页面组件名称
const cachedViews = ['TestCaseManage']

const handleCollapse = (val: boolean) => {
  collapsed.value = val
}

const handleMenuClick = (key: string) => {
  router.push({ name: key })
}

const handleLogout = () => {
  Modal.confirm({
    title: '确认退出',
    content: '确定要退出登录吗？',
    onOk: () => {
      userStore.logout()
      Message.success('已退出登录')
      router.push('/login')
    }
  })
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  background: var(--gray-50);
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--gradient-header);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(224, 212, 252, 0.3);
  padding: 0 24px;
  height: 60px;
  box-shadow: var(--shadow-header);
  position: relative;
  z-index: 10;
}

/* 底部渐变装饰线 */
.layout-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--gradient-primary);
  opacity: 0.4;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.logo-icon svg {
  width: 100%;
  height: 100%;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.3px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: var(--radius-md);
  transition: all var(--transition-normal);
}

.user-info:hover {
  background: var(--primary-50);
}

.user-avatar {
  background: var(--gradient-primary) !important;
  color: white !important;
}

.username {
  font-size: var(--font-size-base);
  color: var(--gray-700);
  font-weight: var(--font-weight-medium);
}

.layout-sider {
  background: var(--gradient-sidebar) !important;
  border-right: 1px solid rgba(224, 212, 252, 0.25) !important;
  box-shadow: 2px 0 8px rgba(99, 102, 241, 0.03);
  overflow: hidden !important;
}

.layout-sider :deep(.arco-layout-sider-children) {
  overflow: hidden !important;
}

.layout-sider :deep(.arco-menu) {
  overflow: hidden !important;
}

.layout-sider :deep(.arco-menu-inner) {
  overflow: hidden !important;
}

.layout-body {
  flex: 1;
  overflow: hidden;
}

.layout-content {
  background: var(--gray-50);
  overflow: auto;
}

.content-wrapper {
  padding: var(--content-padding);
  min-height: calc(100vh - var(--header-height));
}
</style>
