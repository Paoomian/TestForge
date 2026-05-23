# 开发工具页面设计文档

## 概述

为TestForge测试平台添加「开发工具」功能，集成测试开发工程师常用工具，包括数据格式化、编解码、哈希加密、生成工具、时间转换五大类共17个工具。

## 设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 导航方式 | 侧边栏单入口 + 页面内左侧卡片列表 | 简洁，不占用菜单空间 |
| 工具联动 | 完全独立 | 简化实现，各工具职责单一 |
| 历史记录 | 不保存 | 使用后即丢，无需持久化 |
| 页面布局 | 单页面 + 动态组件切换 | 路由简单，体验流畅 |

## 页面结构

```
┌─────────────────────────────────────────────────────┐
│  Header                                             │
├──────────┬──────────────────────────────────────────┤
│          │  开发工具                                  │
│ 仪表盘   │                                          │
│ 项目管理 │  ┌──────────┬────────────────────────────┤
│ UI自动化 │  │ 分类标题  │  输入区        │ 输出区     │
│ 接口自动化│  │ ──────── │               │            │
│ 测试报告 │  │ 🔧 JSON  │  [Monaco /    │ [高亮输出 / │
│ ▶ 开发工具│  │   格式化  │   textarea]   │  textarea] │
│          │  ├──────────┤               │            │
│          │  │ 🔧 XML   │               │            │
│          │  │   格式化  │               │            │
│          │  ├──────────┤               │            │
│          │  │ ...      │               │            │
│          │  └──────────┤  ─────────────────────────  │
│          │             │  [操作按钮：格式化/编码/生成] │
│          │             └────────────────────────────┤
└──────────┴──────────────────────────────────────────┘
```

## 组件结构

```
views/tools/
├── ToolsPage.vue           # 主页面（左侧卡片列表 + 右侧工具内容）
├── ToolLayout.vue          # 工具内容共享布局（输入/输出分栏）
├── JsonFormatter.vue       # JSON格式化
├── XmlFormatter.vue        # XML格式化
├── YamlFormatter.vue       # YAML格式化
├── Base64Tool.vue          # Base64编解码
├── UrlEncoder.vue          # URL编解码
├── HtmlEncoder.vue         # HTML编解码
├── UnicodeConverter.vue    # Unicode编解码
├── HashCalculator.vue      # 哈希计算
├── JwtDecoder.vue          # JWT解析
├── AesTool.vue             # AES/DES加解密
├── UuidGenerator.vue       # UUID生成
├── RandomString.vue        # 随机字符串
├── TestDataGenerator.vue   # 测试数据生成
├── QrCodeGenerator.vue     # 二维码生成
├── TimestampConverter.vue  # 时间戳转换
├── CronBuilder.vue         # Cron生成器
└── RadixConverter.vue      # 进制转换
```

## 路由与菜单

### 路由

```typescript
{
  path: '/tools',
  name: 'tools',
  component: () => import('@/views/tools/ToolsPage.vue'),
  meta: { title: '开发工具' }
}
```

### 侧边栏菜单

```xml
<a-sub-menu key="tools">
  <template #icon><icon-tool /></template>
  <template #title>开发工具</template>
  <a-menu-item key="tools">工具目录</a-menu-item>
</a-sub-menu>
```

只有一个入口，不展开二级菜单。

## ToolLayout 共享布局组件

### Props

```typescript
interface Props {
  title: string           // 工具标题
  description?: string    // 简短描述
}
```

### Slots

- `input` - 输入区内容
- `output` - 输出区内容
- `actions` - 操作栏按钮

### 使用示例

```vue
<template>
  <ToolLayout title="JSON格式化" description="粘贴JSON字符串，自动格式化高亮">
    <template #input>
      <JsonEditor v-model="input" language="json" height="400px" />
    </template>
    <template #output>
      <JsonViewer :content="output" max-height="400px" />
    </template>
    <template #actions>
      <a-button type="primary" @click="format">格式化</a-button>
      <a-button @click="clear">清空</a-button>
    </template>
  </ToolLayout>
</template>
```

### 布局规范

- 输入/输出区各占50%宽度，gap: 16px
- 操作栏固定在底部，按钮右对齐
- 窄屏（<768px）自动切换为上下布局

## 工具详细设计

### 一、数据格式化类

#### JSON格式化

| 项目 | 说明 |
|------|------|
| 输入组件 | JsonEditor（Monaco Editor，language=json） |
| 输出组件 | JsonViewer（复用现有，语法高亮 + 折叠） |
| 操作按钮 | 格式化、压缩、复制 |
| 错误处理 | 输入非法JSON时显示错误提示和行号 |

#### XML格式化

| 项目 | 说明 |
|------|------|
| 输入组件 | JsonEditor（Monaco Editor，language=xml） |
| 输出组件 | `<pre>` 标签 + 简单语法高亮 |
| 操作按钮 | 格式化、压缩、复制 |

#### YAML格式化

| 项目 | 说明 |
|------|------|
| 输入组件 | JsonEditor（Monaco Editor，language=yaml） |
| 输出组件 | `<pre>` 标签 + 简单语法高亮 |
| 操作按钮 | 格式化、转JSON、复制 |

### 二、编解码类

#### Base64编解码

| 项目 | 说明 |
|------|------|
| 输入组件 | a-textarea |
| 输出组件 | a-textarea（只读） |
| 操作按钮 | 编码、解码、复制 |
| 特性 | 支持UTF-8中文 |

#### URL编解码

| 项目 | 说明 |
|------|------|
| 输入组件 | a-textarea |
| 输出组件 | a-textarea（只读） |
| 操作按钮 | 编码（encodeURIComponent）、解码、复制 |

#### HTML编解码

| 项目 | 说明 |
|------|------|
| 输入组件 | a-textarea |
| 输出组件 | a-textarea（只读） |
| 操作按钮 | 编码（转义 <>&"' 等）、解码、复制 |

#### Unicode编解码

| 项目 | 说明 |
|------|------|
| 输入组件 | a-textarea |
| 输出组件 | a-textarea（只读） |
| 操作按钮 | 中文→Unicode、Unicode→中文、复制 |

### 三、哈希/加密类

#### 哈希计算

| 项目 | 说明 |
|------|------|
| 输入组件 | a-textarea（待计算文本） |
| 输出组件 | 三个只读 a-input，分别显示 MD5 / SHA1 / SHA256 |
| 操作按钮 | 计算、每个结果单独复制按钮 |
| 依赖 | crypto-js |

#### JWT解析

| 项目 | 说明 |
|------|------|
| 输入组件 | a-textarea（粘贴JWT Token） |
| 输出组件 | 三段展示：Header（JSON）、Payload（JSON）、签名状态 |
| 操作按钮 | 解析、复制 |
| 特性 | 自动base64解码，时间字段友好展示 |

#### AES/DES加解密

| 项目 | 说明 |
|------|------|
| 输入组件 | a-textarea（文本）+ a-input（密钥）+ 选择器（模式/填充/格式） |
| 输出组件 | a-textarea（只读） |
| 操作按钮 | 加密、解密、复制 |
| 依赖 | crypto-js |

### 四、生成工具类

#### UUID生成

| 项目 | 说明 |
|------|------|
| 输入组件 | 数字输入框（数量1-100）+ 格式选项（带/不带横线、大小写） |
| 输出组件 | a-textarea（只读），每行一个UUID |
| 操作按钮 | 生成、复制全部 |

#### 随机字符串

| 项目 | 说明 |
|------|------|
| 输入组件 | 数字输入框（长度）+ 复选框（字符集）+ 数字输入框（数量） |
| 输出组件 | a-textarea（只读） |
| 操作按钮 | 生成、复制全部 |

#### 测试数据生成

| 项目 | 说明 |
|------|------|
| 输入组件 | 选择器（数据类型：姓名/手机号/身份证/邮箱/地址/银行卡）+ 数量 |
| 输出组件 | a-table 表格展示 |
| 操作按钮 | 生成、复制全部 |
| 实现 | 手写随机生成逻辑，不引入外部依赖 |

#### 二维码生成

| 项目 | 说明 |
|------|------|
| 输入组件 | a-textarea（文本或URL） |
| 输出组件 | 二维码图片 `<img>` |
| 操作按钮 | 生成、下载PNG |
| 依赖 | qrcode |

### 五、时间/转换类

#### 时间戳转换

| 项目 | 说明 |
|------|------|
| 输入组件 | 当前时间戳实时显示 + 数字输入框（时间戳）+ 日期选择器 |
| 输出组件 | 互转结果展示 |
| 操作按钮 | 转换、复制 |

#### Cron生成器

| 项目 | 说明 |
|------|------|
| 输入组件 | 可视化配置（秒/分/时/日/月/周）+ 常用快捷按钮 |
| 输出组件 | Cron表达式 + 最近5次执行时间预览 |
| 操作按钮 | 复制表达式 |

#### 进制转换

| 项目 | 说明 |
|------|------|
| 输入组件 | 数字输入框 + 源进制选择（2/8/10/16） |
| 输出组件 | 四个只读框：2进制、8进制、10进制、16进制 |
| 操作按钮 | 转换、复制 |

## UI设计规范

遵循 `frontend/UI_STYLE_GUIDE.md` 规范：

- 使用 CSS 变量（`--primary-*`, `--radius-*`, `--space-*`）
- 左侧卡片列表：`border-left: 4px solid` + hover阴影
- 按钮：主操作 `type="primary"`，次要 `type="outline"`
- 表单：垂直布局 `layout="vertical"`
- 所有状态变化加 `transition: all 0.2s ease`
- UI文案使用中文

## 依赖

| 依赖 | 用途 | 安装命令 |
|------|------|----------|
| crypto-js | 哈希计算、AES/DES加解密 | `npm install crypto-js @types/crypto-js` |
| qrcode | 二维码生成 | `npm install qrcode @types/qrcode` |

## 范围

- 纯前端实现，无后端API
- 不保存历史记录
- 各工具完全独立，无联动
- 共17个工具组件 + 1个布局组件 + 1个主页面
