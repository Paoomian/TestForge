<template>
  <div class="monkey-test">
    <!-- 标题区域 -->
    <div class="monkey-header">
      <div class="header-info">
        <h3>Monkey 稳定性测试</h3>
        <span class="header-desc">Android 设备压力测试，随机生成用户事件检测应用稳定性</span>
      </div>
      <a-space>
        <a-button type="outline" @click="refreshDevices" :loading="deviceLoading">
          <template #icon><icon-refresh /></template>
          刷新设备
        </a-button>
        <a-button
          type="primary"
          status="danger"
          @click="handleStop"
          :disabled="!isRunning"
          :loading="stopping"
        >
          <template #icon><icon-record-stop /></template>
          停止测试
        </a-button>
        <a-button
          type="primary"
          @click="handleStart"
          :disabled="isRunning || !selectedDevice"
          :loading="starting"
        >
          <template #icon><icon-play-arrow /></template>
          启动测试
        </a-button>
      </a-space>
    </div>

    <div class="monkey-body">
      <!-- 左侧：配置区域 -->
      <div class="config-panel">
        <!-- 设备选择 -->
        <div class="config-section">
          <div class="section-title">设备选择</div>
          <a-select
            v-model="selectedDevice"
            placeholder="选择已连接的设备"
            :loading="deviceLoading"
            allow-clear
          >
            <a-option
              v-for="d in devices"
              :key="d.serial"
              :value="d.serial"
              :disabled="d.status !== 'device'"
            >
              {{ d.model || d.serial }}
              <a-tag v-if="d.status === 'device'" color="green" size="small">在线</a-tag>
              <a-tag v-else color="red" size="small">{{ d.status }}</a-tag>
            </a-option>
            <template #empty>
              <div class="select-empty">暂无可用设备</div>
            </template>
          </a-select>
          <div v-if="devices.length === 0 && !deviceLoading" class="empty-tip">
            未检测到设备，请确认 USB 调试已开启
          </div>
        </div>

        <!-- 基本参数 -->
        <div class="config-section">
          <div class="section-title">基本参数</div>
          <a-form :model="config" layout="vertical" size="small">
            <a-row :gutter="16">
              <a-col :span="8">
                <a-form-item label="事件总数">
                  <a-input-number v-model="config.event_count" :min="1" :max="1000000" />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="事件间隔(ms)">
                  <a-input-number v-model="config.interval" :min="0" :max="10000" />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="随机种子">
                  <a-input-number v-model="config.seed" :min="0" placeholder="留空随机" allow-clear />
                </a-form-item>
              </a-col>
            </a-row>
            <a-form-item label="目标包名（可选）">
              <a-input v-model="config.package" placeholder="com.example.app" allow-clear />
            </a-form-item>
          </a-form>
          <div class="estimated-time">
            <icon-clock-circle />
            <span>预计执行时长：{{ estimatedTime }}</span>
          </div>
        </div>

        <!-- 事件类型百分比 -->
        <div class="config-section">
          <div class="section-title">
            事件类型百分比
            <span class="pct-total">总和: {{ pctTotal }}%</span>
          </div>
          <!-- 预设管理 -->
          <div class="preset-bar">
            <a-select
              v-model="selectedPreset"
              placeholder="选择预设配置"
              allow-clear
              :loading="presetLoading"
              style="flex: 1"
              @change="applyPreset"
            >
              <a-option v-for="p in defaultPresets" :key="p.id" :value="p.id">
                ⭐ {{ p.name }}
              </a-option>
              <a-option v-for="p in userPresets" :key="p.id" :value="p.id">
                📋 {{ p.name }}
              </a-option>
              <template #empty>
                <div class="select-empty">暂无预设配置</div>
              </template>
            </a-select>
            <a-button type="outline" size="small" @click="openSaveDialog">
              <template #icon><icon-save /></template>
              保存
            </a-button>
            <a-button
              type="outline"
              size="small"
              status="danger"
              @click="handleDeletePreset"
            >
              <template #icon><icon-delete /></template>
            </a-button>
          </div>
          <div class="pct-grid">
            <div v-for="item in pctFields" :key="item.key" class="pct-item">
              <div class="pct-label">{{ item.label }}</div>
              <div class="pct-control">
                <a-slider
                  v-model="config[item.key]"
                  :min="0"
                  :max="100"
                  :step="1"
                  :style="{ flex: 1 }"
                />
                <a-input-number
                  v-model="config[item.key]"
                  :min="0"
                  :max="100"
                  :style="{ width: '65px' }"
                  size="small"
                />
                <span class="pct-unit">%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：日志区域 -->
      <div class="log-panel">
        <div class="log-header">
          <span class="section-title">运行日志</span>
          <a-tag v-if="taskStatus === 'running'" color="green" size="small">运行中</a-tag>
          <a-tag v-else-if="taskStatus === 'completed'" color="green" size="small">已完成</a-tag>
          <a-tag v-else-if="taskStatus === 'stopped'" color="orange" size="small">已停止</a-tag>
          <a-tag v-else-if="taskStatus === 'failed'" color="red" size="small">失败</a-tag>
          <a-button size="mini" type="outline" :disabled="logLines.length === 0" @click="exportLogs">
            <template #icon><icon-download /></template>
            导出
          </a-button>
        </div>
        <div class="log-content" ref="logContainer">
          <template v-if="logLines.length > 0">
            <div v-for="(line, i) in logLines" :key="i" class="log-line">{{ line }}</div>
          </template>
          <a-empty v-else description="等待测试启动..." />
        </div>
      </div>
    </div>

    <!-- 保存预设对话框 -->
    <a-modal
      v-model:visible="saveDialogVisible"
      title="保存预设配置"
      @ok="handleSavePreset"
      :mask-closable="false"
    >
      <a-form layout="vertical">
        <a-form-item label="配置名称" required>
          <a-input
            v-model="savePresetName"
            placeholder="请输入配置名称"
            :max-length="100"
            allow-clear
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { IconRefresh, IconPlayArrow, IconRecordStop, IconClockCircle, IconDownload, IconSave, IconDelete } from '@arco-design/web-vue/es/icon'
import { getDevices, startMonkey, stopMonkey, getDefaultMonkeyPresets, getMonkeyPresets, createMonkeyPreset, deleteMonkeyPreset } from '@/api/monkey'
import type { DeviceInfo, MonkeyConfig, MonkeyPreset } from '@/api/monkey'

// 设备相关
const devices = ref<DeviceInfo[]>([])
const selectedDevice = ref<string>('')
const deviceLoading = ref(false)

// 预设相关
const defaultPresets = ref<MonkeyPreset[]>([])
const userPresets = ref<MonkeyPreset[]>([])
const selectedPreset = ref<number | null>(null)
const presetLoading = ref(false)
const saveDialogVisible = ref(false)
const savePresetName = ref('')

// 合并预设列表用于显示
const allPresets = computed(() => [...defaultPresets.value, ...userPresets.value])

// 配置
const config = reactive<MonkeyConfig>({
  device_serial: '',
  event_count: 1000,
  interval: 300,
  seed: undefined,
  package: '',
  pct_touch: 15,
  pct_motion: 10,
  pct_trackball: 15,
  pct_nav: 20,
  pct_majornav: 15,
  pct_syskeys: 5,
  pct_appswitch: 2,
  pct_anyevent: 18,
})

// 百分比字段定义
const pctFields = [
  { key: 'pct_touch', label: '触摸事件' },
  { key: 'pct_motion', label: '滑动事件' },
  { key: 'pct_trackball', label: '轨迹球' },
  { key: 'pct_nav', label: '基本导航' },
  { key: 'pct_majornav', label: '主要导航' },
  { key: 'pct_syskeys', label: '系统按键' },
  { key: 'pct_appswitch', label: 'Activity切换' },
  { key: 'pct_anyevent', label: '其他事件' },
] as const

const pctTotal = computed(() => {
  return pctFields.reduce((sum, item) => sum + (config[item.key] || 0), 0)
})

// 预估执行时长（小时）
const estimatedTime = computed(() => {
  const totalMs = (config.event_count || 0) * (config.interval || 0)
  const hours = totalMs / 1000 / 3600
  if (hours < 1) {
    return `约 ${(hours * 60).toFixed(1)} 分钟`
  }
  return `约 ${hours.toFixed(1)} 小时`
})

// 任务状态
const taskId = ref('')
const taskStatus = ref('')
const isRunning = computed(() => taskStatus.value === 'running')
const starting = ref(false)
const stopping = ref(false)

// 日志
const logLines = ref<string[]>([])
const logContainer = ref<HTMLElement | null>(null)
let ws: WebSocket | null = null

// 刷新设备列表
async function refreshDevices() {
  deviceLoading.value = true
  try {
    devices.value = await getDevices()
    if (devices.value.length > 0 && !selectedDevice.value) {
      selectedDevice.value = devices.value[0].serial
    }
  } catch (e: any) {
    Message.error(e?.detail || '获取设备列表失败')
  } finally {
    deviceLoading.value = false
  }
}

// 加载预设列表
async function loadPresets() {
  presetLoading.value = true
  try {
    const [defaults, userPresetList] = await Promise.all([
      getDefaultMonkeyPresets(),
      getMonkeyPresets(),
    ])
    // 为默认预设添加标识
    defaultPresets.value = defaults.map(p => ({ ...p, isDefault: true }))
    userPresets.value = userPresetList
  } catch (e: any) {
    Message.error(e?.detail || '获取预设列表失败')
  } finally {
    presetLoading.value = false
  }
}

// 应用预设
function applyPreset(presetId: number | null) {
  if (!presetId) return
  const preset = allPresets.value.find(p => p.id === presetId)
  if (!preset) return
  // 填充配置
  config.pct_touch = preset.pct_touch
  config.pct_motion = preset.pct_motion
  config.pct_trackball = preset.pct_trackball
  config.pct_nav = preset.pct_nav
  config.pct_majornav = preset.pct_majornav
  config.pct_syskeys = preset.pct_syskeys
  config.pct_appswitch = preset.pct_appswitch
  config.pct_anyevent = preset.pct_anyevent
  config.event_count = preset.event_count
  config.interval = preset.interval
  Message.success(`已加载预设: ${preset.name}`)
}

// 打开保存对话框
function openSaveDialog() {
  savePresetName.value = ''
  saveDialogVisible.value = true
}

// 保存预设
async function handleSavePreset() {
  if (!savePresetName.value.trim()) {
    Message.warning('请输入配置名称')
    return
  }
  try {
    await createMonkeyPreset({
      name: savePresetName.value.trim(),
      pct_touch: config.pct_touch,
      pct_motion: config.pct_motion,
      pct_trackball: config.pct_trackball,
      pct_nav: config.pct_nav,
      pct_majornav: config.pct_majornav,
      pct_syskeys: config.pct_syskeys,
      pct_appswitch: config.pct_appswitch,
      pct_anyevent: config.pct_anyevent,
      event_count: config.event_count,
      interval: config.interval,
    })
    Message.success('预设已保存')
    saveDialogVisible.value = false
    loadPresets()
  } catch (e: any) {
    Message.error(e?.detail || '保存失败')
  }
}

// 删除预设
async function handleDeletePreset() {
  if (!selectedPreset.value) {
    Message.warning('请先选择要删除的预设')
    return
  }
  // 不允许删除默认预设（id 为负数）
  if (selectedPreset.value < 0) {
    Message.warning('默认预设不能删除')
    return
  }
  const preset = userPresets.value.find(p => p.id === selectedPreset.value)
  if (!preset) return

  Modal.confirm({
    title: '确认删除',
    content: `确定删除预设「${preset.name}」吗？`,
    onOk: async () => {
      try {
        await deleteMonkeyPreset(selectedPreset.value!)
        Message.success('已删除')
        selectedPreset.value = null
        loadPresets()
      } catch (e: any) {
        Message.error(e?.detail || '删除失败')
      }
    },
  })
}

// 启动 Monkey 测试
async function handleStart() {
  if (!selectedDevice.value) {
    Message.warning('请先选择设备')
    return
  }
  starting.value = true
  try {
    config.device_serial = selectedDevice.value
    const res = await startMonkey(config)
    taskId.value = res.task_id
    taskStatus.value = 'running'
    logLines.value = []
    // 连接 WebSocket 接收日志
    connectWebSocket(res.task_id)
    Message.success('Monkey 测试已启动')
  } catch (e: any) {
    Message.error(e?.detail || '启动失败')
  } finally {
    starting.value = false
  }
}

// 停止 Monkey 测试
async function handleStop() {
  if (!taskId.value) return
  stopping.value = true
  try {
    await stopMonkey(taskId.value)
    taskStatus.value = 'stopped'
    Message.info('已发送停止命令')
  } catch (e: any) {
    Message.error(e?.detail || '停止失败')
  } finally {
    stopping.value = false
  }
}

// 导出日志
function exportLogs() {
  if (logLines.value.length === 0) return
  const content = logLines.value.join('\n')
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  const now = new Date()
  const ts = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`
  a.href = url
  a.download = `monkey_log_${ts}.txt`
  a.click()
  URL.revokeObjectURL(url)
  Message.success('日志已导出')
}

// WebSocket 连接
function connectWebSocket(tid: string) {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${location.host}/ws/monkey/${tid}`

  ws = new WebSocket(wsUrl)
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'log') {
        const now = new Date()
        const ts = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
        logLines.value.push(`[${ts}] ${data.line}`)
        // 自动滚动到底部
        nextTick(() => {
          if (logContainer.value) {
            logContainer.value.scrollTop = logContainer.value.scrollHeight
          }
        })
      } else if (data.type === 'status') {
        taskStatus.value = data.status
        if (data.status === 'completed') {
          Message.success('Monkey 测试完成')
        } else if (data.status === 'stopped') {
          Message.info('Monkey 测试已停止')
        }
      } else if (data.type === 'error') {
        Message.error(data.message)
      }
    } catch {}
  }
  ws.onclose = () => {
    if (taskStatus.value === 'running') {
      taskStatus.value = 'stopped'
    }
  }
  ws.onerror = () => {
    Message.error('WebSocket 连接失败')
  }
}

onMounted(() => {
  refreshDevices()
  loadPresets()
})

onBeforeUnmount(() => {
  if (ws) {
    ws.close()
    ws = null
  }
})
</script>

<style scoped>
.monkey-test {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--header-height) - var(--content-padding) * 2);
  gap: 16px;
  overflow: hidden;
}

.monkey-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.header-info h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: var(--color-text-1);
}

.header-desc {
  font-size: 13px;
  color: var(--color-text-3);
}

.monkey-body {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.config-panel {
  width: 420px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.config-section {
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  padding: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-1);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pct-total {
  font-size: 12px;
  font-weight: 400;
  color: var(--color-text-3);
}

.pct-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pct-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pct-label {
  font-size: 12px;
  color: var(--color-text-2);
}

.pct-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pct-unit {
  font-size: 12px;
  color: var(--color-text-3);
  width: 16px;
}

.empty-tip {
  font-size: 12px;
  color: var(--color-text-3);
  margin-top: 8px;
}

.select-empty {
  padding: 16px 0;
  text-align: center;
  color: var(--color-text-3);
  font-size: 13px;
}

.preset-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.estimated-time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-text-2);
  padding: 8px 12px;
  background: var(--color-fill-2);
  border-radius: var(--radius-sm);
}

.log-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
}

.log-header .section-title {
  margin-bottom: 0;
  flex: 1;
}

.log-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  line-height: 1.6;
  background: var(--color-bg-1);
}

.log-content:has(.arco-empty) {
  display: flex;
  justify-content: center;
  align-items: center;
}

.log-line {
  color: var(--color-text-2);
  white-space: pre-wrap;
  word-break: break-all;
}

/* 响应式 */
@media (max-width: 900px) {
  .monkey-body {
    flex-direction: column;
  }
  .config-panel {
    width: 100%;
  }
}
</style>
