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
            <a-menu-item key="ui-run">任务配置</a-menu-item>
            <a-menu-item key="ui-batch-tasks">任务记录</a-menu-item>
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
            <template #title>工具箱</template>
            <a-menu-item key="tools">实用工具</a-menu-item>
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
import { ref, computed, watch, nextTick } from 'vue'
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
  'ui-batch-run-detail': 'ui-batch-tasks',
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

// 调试：收起/展开后在控制台执行 debugMenu() 查看对比
function debugMenu() {
  const sider = document.querySelector('.layout-sider')
  if (!sider) { console.log('找不到 .layout-sider'); return }

  const isCollapsed = !!sider.querySelector('.arco-menu-collapsed')

  // 收起时 sub-menu 可能用 pop 模式（.arco-menu-pop-header）而非 inline 模式
  const firstItem = sider.querySelector('.arco-menu-item')
  const firstHeader = sider.querySelector('.arco-menu-inline-header, .arco-menu-pop-header')

  if (!firstItem) { console.log('找不到 .arco-menu-item'); return }
  if (!firstHeader) {
    // 打印所有子元素 class 帮助定位
    console.log('找不到 inline-header / pop-header，当前 sider 内的 class 列表：')
    sider.querySelectorAll('[class*="arco-menu"]').forEach(el => {
      const rect = el.getBoundingClientRect()
      if (rect.height > 0) console.log(`  .${el.className.split(' ').join('.')}  height=${rect.height.toFixed(1)} width=${rect.width.toFixed(1)}`)
    })
    return
  }

  // 收集所有可见行
  const allItems = sider.querySelectorAll('.arco-menu-item')
  const allHeaders = sider.querySelectorAll('.arco-menu-inline-header, .arco-menu-pop-header')
  const allVisibleRows = [...Array.from(allItems), ...Array.from(allHeaders)]
    .filter(el => el.getBoundingClientRect().height > 0)

  const heights = allVisibleRows.map(el => el.getBoundingClientRect().height)
  const widths = allVisibleRows.map(el => el.getBoundingClientRect().width)

  console.group(`%c菜单 ${isCollapsed ? '收起' : '展开'} 状态`, 'color: #8b5cf6; font-weight: bold; font-size: 14px')

  console.log('%c可见行数:', 'color: #3b82f6', allVisibleRows.length)
  console.log('%c行高:', 'color: #3b82f6', heights.map(h => h.toFixed(1)).join(', '))
  console.log('%c行宽:', 'color: #3b82f6', widths.map(w => w.toFixed(1)).join(', '))
  console.log('行高一致?', heights.every(h => Math.abs(h - heights[0]) < 1) ? '✅' : '❌')

  const ir = firstItem.getBoundingClientRect()
  const hr = firstHeader.getBoundingClientRect()
  console.log(`%cmenu-item:`, 'color: #3b82f6', `top=${ir.top.toFixed(1)} height=${ir.height.toFixed(1)} width=${ir.width.toFixed(1)}`)
  console.log(`%csub-menu-header:`, 'color: #10b981', `top=${hr.top.toFixed(1)} height=${hr.height.toFixed(1)} width=${hr.width.toFixed(1)} class=${firstHeader.className}`)
  console.log('高度差:', Math.abs(ir.height - hr.height).toFixed(1) + 'px', Math.abs(ir.height - hr.height) < 1 ? '✅' : '❌')
  console.log('宽度差:', Math.abs(ir.width - hr.width).toFixed(1) + 'px', Math.abs(ir.width - hr.width) < 1 ? '✅' : '❌')

  const itemIcon = firstItem.querySelector('.arco-icon')
  const headerIcon = firstHeader.querySelector('.arco-icon')
  if (itemIcon && headerIcon) {
    const iir = itemIcon.getBoundingClientRect()
    const hir = headerIcon.getBoundingClientRect()
    console.log('%c图标对比:', 'color: #f59e0b')
    console.log('  item   icon:', `left=${iir.left.toFixed(1)} top=${iir.top.toFixed(1)} center=${(iir.left + iir.width / 2).toFixed(1)}`)
    console.log('  header icon:', `left=${hir.left.toFixed(1)} top=${hir.top.toFixed(1)} center=${(hir.left + hir.width / 2).toFixed(1)}`)
    console.log('  水平对齐?', Math.abs(iir.left - hir.left) < 1 ? '✅' : `❌ 差${Math.abs(iir.left - hir.left).toFixed(1)}px`)
  } else {
    console.log('找不到图标元素', { itemIcon: !!itemIcon, headerIcon: !!headerIcon })
  }

  console.groupEnd()
}

;(window as any).debugMenu = debugMenu

const handleMenuClick = (key: string) => {
  console.log('菜单点击:', key)
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

<style>
/*
 * 侧边栏菜单收起状态修复
 * 收起时 Arco 把 sub-menu 渲染为 .arco-menu-pop（popup 模式），
 * 与 .arco-menu-item 宽度/内边距不同，导致图标不对齐。
 * 修复：统一尺寸、清零所有内边距/外边距，用 flex 居中图标。
 */

/* 统一外层容器 */
.layout-sider .arco-menu-collapsed .arco-menu-item,
.layout-sider .arco-menu-collapsed .arco-menu-pop {
  width: 40px !important;
  height: 40px !important;
  padding: 0 !important;
  margin: 0 !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  box-sizing: border-box !important;
}

/* 清零图标容器的 margin/padding */
.layout-sider .arco-menu-collapsed .arco-menu-item .arco-menu-icon,
.layout-sider .arco-menu-collapsed .arco-menu-pop .arco-menu-icon {
  margin: 0 !important;
  padding: 0 !important;
}

/* 清零图标本身的 margin */
.layout-sider .arco-menu-collapsed .arco-menu-item .arco-icon,
.layout-sider .arco-menu-collapsed .arco-menu-pop .arco-icon {
  margin: 0 !important;
}

/* 隐藏文字 */
.layout-sider .arco-menu-collapsed .arco-menu-item .arco-menu-title,
.layout-sider .arco-menu-collapsed .arco-menu-pop .arco-menu-title {
  display: none !important;
}

/* 隐藏子菜单箭头 */
.layout-sider .arco-menu-collapsed .arco-menu-pop .arco-menu-icon-suffix {
  display: none !important;
}
</style>
