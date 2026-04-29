<template>
  <div class="dashboard">
    <a-row :gutter="16">
      <a-col :span="6">
        <a-card title="项目总数" :bordered="false">
          <a-statistic :value="stats.projects" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card title="UI用例" :bordered="false">
          <a-statistic :value="stats.uiCases" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card title="接口用例" :bordered="false">
          <a-statistic :value="stats.apiCases" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card title="执行次数" :bordered="false">
          <a-statistic :value="stats.executions" />
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="24">
        <a-card title="欢迎使用测试平台" :bordered="false">
          <p>这是一个集UI自动化、接口自动化和接口调试于一体的测试平台</p>
          <a-space>
            <a-button type="primary" @click="$router.push({ name: 'project-list' })">
              创建项目
            </a-button>
            <a-button @click="$router.push({ name: 'api-debug' })">
              接口调试
            </a-button>
          </a-space>
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
</style>
