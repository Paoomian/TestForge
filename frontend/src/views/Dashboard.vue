<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <a-row :gutter="20">
      <a-col :span="6">
        <div class="stat-card stat-card-purple">
          <div class="stat-icon-wrapper">
            <icon-folder class="stat-icon" />
          </div>
          <div class="stat-content">
            <div class="stat-label">项目总数</div>
            <div class="stat-value">{{ stats.projects }}</div>
          </div>
        </div>
      </a-col>
      <a-col :span="6">
        <div class="stat-card stat-card-indigo">
          <div class="stat-icon-wrapper">
            <icon-desktop class="stat-icon" />
          </div>
          <div class="stat-content">
            <div class="stat-label">UI用例</div>
            <div class="stat-value">{{ stats.uiCases }}</div>
          </div>
        </div>
      </a-col>
      <a-col :span="6">
        <div class="stat-card stat-card-blue">
          <div class="stat-icon-wrapper">
            <icon-code class="stat-icon" />
          </div>
          <div class="stat-content">
            <div class="stat-label">接口用例</div>
            <div class="stat-value">{{ stats.apiCases }}</div>
          </div>
        </div>
      </a-col>
      <a-col :span="6">
        <div class="stat-card stat-card-cyan">
          <div class="stat-icon-wrapper">
            <icon-play-arrow class="stat-icon" />
          </div>
          <div class="stat-content">
            <div class="stat-label">执行次数</div>
            <div class="stat-value">{{ stats.executions }}</div>
          </div>
        </div>
      </a-col>
    </a-row>

    <!-- 欢迎卡片 -->
    <a-row :gutter="20" style="margin-top: 24px">
      <a-col :span="16">
        <a-card class="welcome-card" :bordered="false">
          <div class="welcome-content">
            <div class="welcome-text">
              <h2 class="welcome-title">欢迎使用 TestForge</h2>
              <p class="welcome-desc">集UI自动化、接口自动化和接口调试于一体的现代化测试平台，助力团队高效交付</p>
              <a-space>
                <a-button type="primary" size="large" @click="$router.push({ name: 'project-list' })">
                  <template #icon><icon-plus /></template>
                  创建项目
                </a-button>
                <a-button size="large" @click="$router.push({ name: 'api-debug' })">
                  <template #icon><icon-bug /></template>
                  接口调试
                </a-button>
              </a-space>
            </div>
            <div class="welcome-illustration">
              <svg viewBox="0 0 200 160" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="20" y="20" width="160" height="120" rx="16" fill="url(#dash-card-grad)" opacity="0.15"/>
                <rect x="40" y="50" width="50" height="6" rx="3" fill="#A78BFA" opacity="0.6"/>
                <rect x="40" y="64" width="80" height="4" rx="2" fill="#C4B5FD" opacity="0.4"/>
                <rect x="40" y="74" width="60" height="4" rx="2" fill="#C4B5FD" opacity="0.3"/>
                <circle cx="150" cy="50" r="20" fill="url(#dash-circle-grad)" opacity="0.2"/>
                <path d="M142 50L148 56L158 44" stroke="#818CF8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                <rect x="40" y="90" width="120" height="30" rx="8" fill="url(#dash-btn-grad)" opacity="0.3"/>
                <rect x="55" y="100" width="40" height="8" rx="4" fill="white" opacity="0.8"/>
                <defs>
                  <linearGradient id="dash-card-grad" x1="20" y1="20" x2="180" y2="140">
                    <stop stop-color="#A78BFA"/>
                    <stop offset="1" stop-color="#818CF8"/>
                  </linearGradient>
                  <linearGradient id="dash-circle-grad" x1="130" y1="30" x2="170" y2="70">
                    <stop stop-color="#A78BFA"/>
                    <stop offset="1" stop-color="#818CF8"/>
                  </linearGradient>
                  <linearGradient id="dash-btn-grad" x1="40" y1="90" x2="160" y2="120">
                    <stop stop-color="#A78BFA"/>
                    <stop offset="1" stop-color="#818CF8"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card class="quick-actions-card" :bordered="false">
          <template #title>
            <span class="card-title">快速操作</span>
          </template>
          <div class="quick-actions">
            <div class="action-item" @click="$router.push({ name: 'project-list' })">
              <div class="action-icon action-icon-purple">
                <icon-folder />
              </div>
              <span class="action-label">项目管理</span>
            </div>
            <div class="action-item" @click="$router.push({ name: 'api-test-manage' })">
              <div class="action-icon action-icon-indigo">
                <icon-code />
              </div>
              <span class="action-label">接口用例</span>
            </div>
            <div class="action-item" @click="$router.push({ name: 'api-debug' })">
              <div class="action-icon action-icon-blue">
                <icon-bug />
              </div>
              <span class="action-label">接口调试</span>
            </div>
            <div class="action-item" @click="$router.push({ name: 'report-list' })">
              <div class="action-icon action-icon-cyan">
                <icon-file />
              </div>
              <span class="action-label">测试报告</span>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'

const stats = reactive({
  projects: 0,
  uiCases: 0,
  apiCases: 0,
  executions: 0
})
</script>

<style scoped>
.dashboard {
  width: 100%;
}

/* ---- 统计卡片 ---- */
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(224, 212, 252, 0.25);
  box-shadow: var(--shadow-card);
  transition: all var(--transition-slow);
  cursor: default;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-card-hover);
  border-color: rgba(167, 139, 250, 0.25);
}

.stat-icon-wrapper {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
  flex-shrink: 0;
}

.stat-card-purple .stat-icon-wrapper {
  background: linear-gradient(135deg, #ede9fe, #ddd6fe);
  color: #7c3aed;
}

.stat-card-indigo .stat-icon-wrapper {
  background: linear-gradient(135deg, #e0e7ff, #c7d2fe);
  color: #6366f1;
}

.stat-card-blue .stat-icon-wrapper {
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  color: #3b82f6;
}

.stat-card-cyan .stat-icon-wrapper {
  background: linear-gradient(135deg, #cffafe, #a5f3fc);
  color: #0891b2;
}

.stat-icon {
  font-size: 22px;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--gray-500);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: var(--font-weight-bold);
  color: var(--gray-800);
  line-height: 1.2;
}

/* ---- 欢迎卡片 ---- */
.welcome-card {
  height: 100%;
}

.welcome-card :deep(.arco-card-body) {
  padding: 32px;
}

.welcome-content {
  display: flex;
  align-items: center;
  gap: 32px;
}

.welcome-text {
  flex: 1;
}

.welcome-title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--gray-800);
  margin: 0 0 12px 0;
  letter-spacing: -0.5px;
}

.welcome-desc {
  font-size: var(--font-size-base);
  color: var(--gray-500);
  line-height: var(--line-height-relaxed);
  margin: 0 0 24px 0;
}

.welcome-illustration {
  width: 200px;
  flex-shrink: 0;
}

.welcome-illustration svg {
  width: 100%;
  height: auto;
}

/* ---- 快速操作卡片 ---- */
.quick-actions-card {
  height: 100%;
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--gray-800);
}

.quick-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px 16px;
  background: var(--gray-50);
  border-radius: var(--radius-lg);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all var(--transition-slow);
}

.action-item:hover {
  background: white;
  border-color: rgba(167, 139, 250, 0.2);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.action-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  font-size: 20px;
  transition: all var(--transition-slow);
}

.action-icon-purple {
  background: linear-gradient(135deg, #ede9fe, #ddd6fe);
  color: #7c3aed;
}

.action-icon-indigo {
  background: linear-gradient(135deg, #e0e7ff, #c7d2fe);
  color: #6366f1;
}

.action-icon-blue {
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  color: #3b82f6;
}

.action-icon-cyan {
  background: linear-gradient(135deg, #cffafe, #a5f3fc);
  color: #0891b2;
}

.action-label {
  font-size: var(--font-size-sm);
  color: var(--gray-600);
  font-weight: var(--font-weight-medium);
}
</style>
