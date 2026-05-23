<template>
  <ToolLayout title="测试数据生成" description="生成姓名、手机号、身份证等测试数据">
    <template #input>
      <div class="testdata-config">
        <a-form :model="{}" layout="vertical">
          <a-form-item label="数据类型">
            <a-select v-model="dataType" style="width: 100%">
              <a-option value="name">姓名</a-option>
              <a-option value="phone">手机号</a-option>
              <a-option value="idcard">身份证号</a-option>
              <a-option value="email">邮箱</a-option>
              <a-option value="address">地址</a-option>
              <a-option value="bank">银行卡号</a-option>
            </a-select>
          </a-form-item>
          <a-form-item label="生成数量">
            <a-input-number v-model="count" :min="1" :max="100" style="width: 100%" />
          </a-form-item>
        </a-form>
      </div>
    </template>
    <template #output>
      <div class="testdata-output">
        <a-table
          v-if="tableData.length"
          :columns="tableColumns"
          :data="tableData"
          :pagination="false"
          size="small"
          :bordered="false"
        />
        <a-empty v-else description="点击生成查看结果" />
      </div>
    </template>
    <template #actions>
      <a-button @click="clear">清空</a-button>
      <a-button type="outline" @click="copyAll">复制全部</a-button>
      <a-button type="primary" @click="generate">生成</a-button>
    </template>
  </ToolLayout>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Message } from '@arco-design/web-vue'
import ToolLayout from './ToolLayout.vue'

const dataType = ref('name')
const count = ref(10)
const tableData = ref<any[]>([])

const tableColumns = computed(() => [
  { title: '#', dataIndex: 'index', width: 60 },
  { title: '数据', dataIndex: 'value' }
])

const surnames = '赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜'.split('')
const names = '伟芳娜秀英敏静丽强磊洋艳勇军杰娟涛超明刚秀兰飞鑫桂英'.split('')

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

function generateName(): string {
  return surnames[randomInt(0, surnames.length - 1)] +
    names[randomInt(0, names.length - 1)] +
    (Math.random() > 0.5 ? names[randomInt(0, names.length - 1)] : '')
}

function generatePhone(): string {
  const prefixes = ['130', '131', '132', '133', '135', '136', '137', '138', '139', '150', '151', '152', '153', '155', '156', '157', '158', '159', '170', '176', '177', '178', '180', '181', '182', '183', '184', '185', '186', '187', '188', '189']
  return prefixes[randomInt(0, prefixes.length - 1)] + String(randomInt(10000000, 99999999))
}

function generateIdCard(): string {
  const areas = ['110101', '310115', '440305', '510104', '330102']
  const year = randomInt(1970, 2005)
  const month = String(randomInt(1, 12)).padStart(2, '0')
  const day = String(randomInt(1, 28)).padStart(2, '0')
  const seq = String(randomInt(100, 999))
  const base = areas[randomInt(0, areas.length - 1)] + year + month + day + seq
  const weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
  const checks = '10X98765432'
  let sum = 0
  for (let i = 0; i < 17; i++) sum += parseInt(base[i]) * weights[i]
  return base + checks[sum % 11]
}

function generateEmail(): string {
  const domains = ['qq.com', '163.com', 'gmail.com', 'outlook.com', 'foxmail.com']
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
  let name = ''
  for (let i = 0; i < randomInt(5, 10); i++) name += chars[randomInt(0, chars.length - 1)]
  return name + '@' + domains[randomInt(0, domains.length - 1)]
}

function generateAddress(): string {
  const cities = ['北京市朝阳区', '上海市浦东新区', '深圳市南山区', '杭州市西湖区', '成都市武侯区']
  const roads = ['人民路', '解放大道', '中山路', '建设路', '和平街']
  return cities[randomInt(0, cities.length - 1)] + roads[randomInt(0, roads.length - 1)] + randomInt(1, 999) + '号'
}

function generateBank(): string {
  const prefixes = ['622202', '622848', '621700', '622150']
  let card = prefixes[randomInt(0, prefixes.length - 1)]
  for (let i = 0; i < 13; i++) card += randomInt(0, 9)
  return card
}

const generators: Record<string, () => string> = {
  name: generateName,
  phone: generatePhone,
  idcard: generateIdCard,
  email: generateEmail,
  address: generateAddress,
  bank: generateBank
}

function generate() {
  const gen = generators[dataType.value]
  if (!gen) return
  tableData.value = Array.from({ length: count.value }, (_, i) => ({
    index: i + 1,
    value: gen()
  }))
  Message.success(`已生成 ${count.value} 条数据`)
}

function copyAll() {
  if (!tableData.value.length) return
  const text = tableData.value.map(r => r.value).join('\n')
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(text).then(() => Message.success('已复制'))
  } else {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.cssText = 'position:fixed;left:-9999px'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    Message.success('已复制')
  }
}

function clear() {
  tableData.value = []
}
</script>

<style scoped>
.testdata-config {
  padding: 8px 0;
  height: 100%;
}

.testdata-output {
  flex: 1;
  min-height: 0;
  overflow: auto;
}
</style>
