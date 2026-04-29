<template>
  <a-layout class="layout-container">
    <a-layout-header class="layout-header">
      <div class="header-left">
        <div class="logo">测试平台</div>
      </div>
      <div class="header-right">
        <a-dropdown>
          <div class="user-info">
            <a-avatar :size="32">
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

    <a-layout>
      <a-layout-sider
        :width="200"
        :collapsed="collapsed"
        collapsible
        @collapse="handleCollapse"
      >
        <a-menu
          :default-selected-keys="[currentRoute]"
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
            <a-menu-item key="api-cases">用例管理</a-menu-item>
            <a-menu-item key="api-record">录制用例</a-menu-item>
            <a-menu-item key="api-run">执行测试</a-menu-item>
          </a-sub-menu>

          <a-menu-item key="api-debug">
            <template #icon>
              <icon-bug />
            </template>
            接口调试
          </a-menu-item>

          <a-sub-menu key="reports">
            <template #icon>
              <icon-file />
            </template>
            <template #title>测试报告</template>
            <a-menu-item key="report-list">报告列表</a-menu-item>
          </a-sub-menu>
        </a-menu>
      </a-layout-sider>

      <a-layout-content class="layout-content">
        <div class="content-wrapper">
          <router-view />
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
const currentRoute = computed(() => route.name as string)

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
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  border-bottom: 1px solid #e5e6eb;
  padding: 0 24px;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  font-size: 20px;
  font-weight: 600;
  color: #1d2129;
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
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.user-info:hover {
  background: #f7f8fa;
}

.username {
  font-size: 14px;
  color: #1d2129;
}

.layout-content {
  background: #f7f8fa;
  overflow: auto;
}

.content-wrapper {
  padding: 24px;
  min-height: calc(100vh - 60px);
}
</style>
