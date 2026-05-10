# TestForge 后台UI风格规范

## 一、设计原则

| 原则 | 说明 |
|------|------|
| 淡蓝紫低饱和 | 主色调采用淡紫色(#A78BFA)、靛蓝(#818CF8)，辅助色为淡蓝(#DBEAFE)、淡青(#ECFEFF) |
| 清新科技感 | 浅色背景、极淡渐变、柔和阴影，营造清爽专业的视觉感受 |
| 统一性 | 所有页面、组件、交互状态保持一致的视觉语言 |
| 可读性优先 | 数据展示区域以清晰可读为首要目标，不牺牲功能做装饰 |

---

## 二、色彩系统

### 2.1 主色 (Primary)

| 用途 | 色值 | CSS变量 |
|------|------|---------|
| 主色极浅 | `#f5f3ff` | `--primary-50` |
| 主色浅 | `#ede9fe` | `--primary-100` |
| 主色中浅 | `#ddd6fe` | `--primary-200` |
| 主色中 | `#c4b5fd` | `--primary-300` |
| 主色 | `#a78bfa` | `--primary-400` |
| 主色深 | `#8b5cf6` | `--primary-500` |

### 2.2 辅助色: 靛蓝 (Indigo)

| 用途 | 色值 | CSS变量 |
|------|------|---------|
| 靛蓝浅 | `#e0e7ff` | `--indigo-100` |
| 靛蓝中 | `#818cf8` | `--indigo-400` |
| 靛蓝 | `#6366f1` | `--indigo-500` |
| 靛蓝深 | `#4f46e5` | `--indigo-600` |
| 靛蓝极深 | `#1e1b4b` | `--indigo-950` |

### 2.3 中性色 (Gray)

| 用途 | 色值 | CSS变量 |
|------|------|---------|
| 背景 | `#f9fafb` | `--gray-50` |
| 浅灰背景 | `#f3f4f6` | `--gray-100` |
| 边框 | `#e5e7eb` | `--gray-200` |
| 次要文字 | `#6b7280` | `--gray-500` |
| 主要文字 | `#374151` | `--gray-700` |
| 标题文字 | `#1f2937` | `--gray-800` |

### 2.4 功能色

| 状态 | 色值 | CSS变量 |
|------|------|---------|
| 成功 | `#10b981` | `--success-main` |
| 警告 | `#f59e0b` | `--warning-main` |
| 危险 | `#ef4444` | `--danger-main` |
| 信息 | `#3b82f6` | `--info-main` |

---

## 三、渐变规范

| 用途 | 渐变值 | CSS变量 |
|------|--------|---------|
| 主色渐变(按钮) | `linear-gradient(135deg, #a78bfa, #818cf8)` | `--gradient-primary` |
| 页面背景 | `linear-gradient(135deg, #f5f7fa, #e8ecf1)` | `--gradient-bg` |
| 柔和背景 | `linear-gradient(135deg, #faf5ff, #eff6ff)` | `--gradient-bg-soft` |
| 侧边栏 | `linear-gradient(180deg, #f9fafb, #f5f3ff)` | `--gradient-sidebar` |
| 头部导航 | `linear-gradient(90deg, rgba(255,255,255,0.95), rgba(245,243,255,0.95))` | `--gradient-header` |

---

## 四、圆角规范

| 场景 | 圆角值 | CSS变量 |
|------|--------|---------|
| 小元素(Tag、Badge) | `6px` | `--radius-sm` |
| 中等元素(Input、Button) | `10px` | `--radius-md` |
| 大元素(Card、Modal) | `14px` | `--radius-lg` |
| 超大元素(Drawer) | `20px` | `--radius-xl` |
| 特殊容器 | `24px` | `--radius-2xl` |

---

## 五、阴影规范

| 场景 | 阴影值 | CSS变量 |
|------|--------|---------|
| 卡片 | `0 1px 3px rgba(0,0,0,0.02), 0 4px 12px rgba(99,102,241,0.06)` | `--shadow-card` |
| 卡片悬浮 | `0 4px 12px rgba(0,0,0,0.03), 0 8px 24px rgba(99,102,241,0.1)` | `--shadow-card-hover` |
| 主色按钮 | `0 4px 12px rgba(129,140,248,0.3)` | `--shadow-primary` |
| 头部导航 | `0 1px 3px rgba(0,0,0,0.02), 0 2px 8px rgba(99,102,241,0.04)` | `--shadow-header` |

---

## 六、组件规范

### 6.1 按钮 (Button)

| 类型 | 样式 |
|------|------|
| Primary | 主色渐变背景、白色文字、主色阴影、hover时上移1px并增强阴影 |
| Secondary/Outline | 主色边框、主色文字、hover时背景变为primary-50 |
| Text | 无边框、主色文字、hover时背景变为primary-50 |

### 6.2 输入框 (Input/Textarea/Select)

- 圆角: `10px` (--radius-md)
- 默认边框: `#e5e7eb` (--gray-200)
- Hover边框: `#c4b5fd` (--primary-300)
- Focus边框: `#a78bfa` (--primary-400) + `0 0 0 3px rgba(167,139,250,0.12)` 光晕

### 6.3 卡片 (Card)

- 圆角: `14px` (--radius-lg)
- 边框: `1px solid rgba(224,212,252,0.3)`
- 阴影: `--shadow-card`
- Hover: 阴影增强 + 边框变色
- 头部标题: 字重600、颜色gray-800

### 6.4 表格 (Table)

- 表头背景: `linear-gradient(135deg, #f9fafb, #f5f3ff)`
- 表头文字: 字重600、颜色gray-700
- 行悬浮: 背景 `rgba(237,233,254,0.3)`
- 边框颜色: `rgba(224,212,252,0.3)`

### 6.5 弹窗 (Modal)

- 圆角: `20px` (--radius-xl)
- 头部/底部分割线: `rgba(224,212,252,0.3)`
- 标题: 字重600、颜色gray-800

### 6.6 侧边栏 (Sidebar)

- 背景: `linear-gradient(180deg, #f9fafb, #f5f3ff)`
- 右边框: `1px solid rgba(224,212,252,0.25)`
- 菜单项圆角: `10px`
- 选中项: 主色渐变背景 + 白色文字 + 主色阴影
- Hover项: `rgba(237,233,254,0.5)` 背景

### 6.7 标签 (Tag)

- 圆角: `6px` (--radius-sm)
- 蓝色: 背景 `#eef2ff`、文字 `#4f46e5`、边框 `#c7d2fe`
- 绿色: 背景 `#ecfdf5`、文字 `#065f46`、边框 `rgba(16,185,129,0.2)`

---

## 七、排版规范

### 7.1 字体

```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
```

### 7.2 字号层级

| 用途 | 字号 | CSS变量 |
|------|------|---------|
| 极小文字 | 12px | `--font-size-xs` |
| 辅助文字 | 13px | `--font-size-sm` |
| 正文 | 14px | `--font-size-base` |
| 副标题 | 16px | `--font-size-lg` |
| 小标题 | 18px | `--font-size-xl` |
| 页面标题 | 20px | `--font-size-2xl` |
| 区域标题 | 24px | `--font-size-3xl` |
| 大标题 | 32px | `--font-size-4xl` |

### 7.3 字重

| 用途 | 字重 | CSS变量 |
|------|------|---------|
| 正文 | 400 | `--font-weight-normal` |
| 强调 | 500 | `--font-weight-medium` |
| 标题 | 600 | `--font-weight-semibold` |
| 大标题 | 700 | `--font-weight-bold` |

---

## 八、间距规范

| 用途 | 间距 | CSS变量 |
|------|------|---------|
| 极小间距 | 4px | `--space-xs` |
| 小间距 | 8px | `--space-sm` |
| 中间距 | 12px | `--space-md` |
| 大间距 | 16px | `--space-lg` |
| 超大间距 | 24px | `--space-xl` |
| 特大间距 | 32px | `--space-2xl` |

---

## 九、动画规范

| 用途 | 时长 | CSS变量 |
|------|------|---------|
| 快速动画 | 0.15s | `--transition-fast` |
| 普通动画 | 0.2s | `--transition-normal` |
| 慢速动画 | 0.3s | `--transition-slow` |

所有动画使用 `ease` 缓动函数。

---

## 十、文件结构

```
frontend/src/
├── theme.css    # 主题变量定义 (CSS Custom Properties)
├── style.css    # 全局样式覆盖 (Arco Design组件覆盖)
└── layouts/
    └── MainLayout.vue  # 布局组件样式
```

---

*最后更新: 2026-05-10*
