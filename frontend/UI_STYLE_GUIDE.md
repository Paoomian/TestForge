# TestForge UI 设计规范

## 设计风格

**淡蓝紫低饱和渐变、清新科技感**。整体风格简洁、现代，避免过于鲜艳的颜色。

---

## 色彩系统

### 主色调

| 用途 | 变量 | 色值 |
|------|------|------|
| 主色 | `--primary-500` | `#8b5cf6` (紫色) |
| 主色-浅 | `--primary-300` | `#c4b5fd` |
| 主色-深 | `--primary-700` | `#6d28d9` |
| 辅助色 | `--indigo-500` | `#6366f1` (靛蓝) |

### 功能色

| 用途 | 色值 | 场景 |
|------|------|------|
| 成功 | `#10b981` | 通过、完成 |
| 警告 | `#f59e0b` | 警告提示 |
| 危险 | `#ef4444` | 错误、删除 |
| 信息 | `#3b82f6` | GET请求、普通信息 |

### 节点类型色（场景编排）

| 类型 | 色值 | 边框色 |
|------|------|--------|
| 接口调用 | `#3370ff` | 蓝色 |
| 条件判断 | `#ff7d00` | 橙色 |
| 等待延时 | `#86909c` | 灰色 |
| 数据赋值 | `#00b42a` | 绿色 |

### HTTP 方法色

| 方法 | 颜色 |
|------|------|
| GET | blue |
| POST | green |
| PUT | orange |
| DELETE | red |
| PATCH | purple |

### 优先级色

| 优先级 | 颜色 |
|--------|------|
| P0 致命 | red |
| P1 严重 | orange |
| P2 一般 | blue |
| P3 轻微 | green |

---

## 圆角规范

| 场景 | 变量 | 值 |
|------|------|-----|
| 小元素（按钮、标签） | `--radius-sm` | 6px |
| 卡片、输入框 | `--radius-md` | 10px |
| 大容器、弹窗 | `--radius-lg` | 14px |
| 特殊圆角 | `--radius-xl` | 20px |

---

## 间距规范

| 名称 | 变量 | 值 | 场景 |
|------|------|----|------|
| xs | `--space-xs` | 4px | 紧凑间距 |
| sm | `--space-sm` | 8px | 元素内部间距 |
| md | `--space-md` | 12px | 表单项间距 |
| lg | `--space-lg` | 16px | 区块间距 |
| xl | `--space-xl` | 24px | 页面边距 |
| 2xl | `--space-2xl` | 32px | 大区块间距 |

---

## 字体规范

| 场景 | 大小 | 字重 |
|------|------|------|
| 辅助文字 | 12px | 400 |
| 正文 | 13-14px | 400 |
| 标题 | 16-18px | 500-600 |
| 大标题 | 20-24px | 600 |

---

## 阴影规范

| 场景 | 变量 |
|------|------|
| 普通卡片 | `--shadow-card` |
| 卡片悬浮 | `--shadow-card-hover` |
| 主色按钮 | `--shadow-primary` |
| 下拉菜单 | `--shadow-lg` |

---

## 组件规范

### 卡片组件

```vue
<a-card class="my-card" :bordered="true" size="small">
  <!-- 卡片内容 -->
</a-card>

<style scoped>
.my-card {
  border-left: 4px solid var(--primary-500);  /* 左侧彩色边框 */
  transition: all 0.2s ease;
}
.my-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
</style>
```

### 表单布局

- 使用 `layout="vertical"` 垂直布局
- 标签宽度：`label-col-flex="80px"`
- 表单项间距：默认或 `margin-bottom: 16px`

### 按钮规范

| 场景 | 类型 |
|------|------|
| 主操作 | `type="primary"` |
| 次要操作 | `type="outline"` 或 默认 |
| 危险操作 | `status="danger"` |
| 文字按钮 | `type="text"` |

### 标签（Tag）

- 使用 `size="small"` 保持紧凑
- 颜色使用 Arco 内置色板：blue, green, orange, red, purple, gray

### 空状态

```vue
<a-empty description="暂无数据" />
```

---

## 布局规范

### 页面结构

```
┌─────────────────────────────────┐
│ Header (60px)                   │
├──────────┬──────────────────────┤
│ Sidebar  │ Content              │
│ (220px)  │ (padding: 24px)      │
│          │                      │
└──────────┴──────────────────────┘
```

### 抽屉宽度

| 场景 | 宽度 |
|------|------|
| 简单表单 | 480-520px |
| 复杂表单 | 640-720px |
| 大型编辑器 | 800-900px |

---

## 动画规范

| 场景 | 时长 |
|------|------|
| 按钮、输入框 | 0.15s ease |
| 卡片、弹窗 | 0.2s ease |
| 页面切换 | 0.3s ease |

---

## Vue 组件模式

### Props 定义

```typescript
interface Props {
  visible: boolean
  editData?: DataType | null
}
const props = defineProps<Props>()
```

### Emits 定义

```typescript
const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}>()
```

### 表单数据

```typescript
const formData = reactive({
  id: undefined as number | undefined,
  name: '',
  items: [] as ItemType[],
})
```

### 子组件数据传递（本地副本模式）

```typescript
const localData = ref<DataItem[]>([])

watch(() => props.modelValue, (val) => {
  localData.value = (val || []).map(item => ({ ...item }))
}, { immediate: true })

function emitChange() {
  emit('update:modelValue', localData.value)
}
```

---

## 注意事项

1. **不要使用纯黑色**：使用 `var(--color-text-1)` ~ `var(--color-text-4)`
2. **不要硬编码颜色值**：使用 CSS 变量或 Arco 内置色板
3. **保持一致的圆角**：统一使用 `--radius-*` 变量
4. **悬浮效果**：卡片和可交互元素需要 `hover` 状态
5. **过渡动画**：所有状态变化添加 `transition`
6. **中文文本**：所有 UI 文案使用中文

---

**最后更新**: 2026-05-15
