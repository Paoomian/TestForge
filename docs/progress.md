# TestForge 开发进度

## 项目初始化

- [x] FastAPI后端框架搭建
- [x] Vue 3 + TypeScript前端框架搭建
- [x] 数据库设计与初始化
- [x] JWT认证系统
- [x] RBAC权限系统

## 接口调试功能

- [x] HTTP请求发送
- [x] 请求参数编辑
- [x] 响应展示

## 用例管理功能 (v2重构)

### Phase 1: 数据库基础
- [x] 创建6个子表模型 (headers/query_params/body_form/body_raw/assertions/extracts/auth)
- [x] 修改api_test_case模型 (新增列、删除JSON列、添加关系)
- [x] 修改environment模型 (新增base_url)
- [x] 更新models/__init__.py

### Phase 2: 后端Schema和工具
- [x] 创建case_number.py (编号生成器)
- [x] 创建curl_parser.py (cURL解析器)
- [x] 创建templates.py (模板数据)
- [x] 重写schemas/api_test_case.py (嵌套Schema)

### Phase 3: 后端API路由
- [x] 重写api_test_cases.py的create/get/update端点
- [x] 新增import-curl和templates端点
- [x] 创建api/environments.py
- [x] 注册新路由到main.py

### Phase 4: 前端API层和通用组件
- [x] 更新apiTestCase.ts接口和函数
- [x] 创建api/environment.ts
- [x] 创建KeyValueEditor.vue
- [x] 创建monacoVariables.ts

### Phase 5: 前端Tab组件
- [x] 创建BasicInfoTab.vue
- [x] 创建HttpMethodSelect.vue、EnvironmentSelect.vue、UrlInput.vue
- [x] 创建BodyEditor.vue、AuthConfig.vue
- [x] 创建RequestConfigTab.vue
- [x] 增强AssertionEditor.vue
- [x] 创建ExtractEditor.vue、AssertionExtractTab.vue
- [x] 创建ScriptTab.vue

### Phase 6: 抽屉集成
- [x] 重写TestCaseDrawer.vue (4Tab编排器)
- [x] 实现表单校验
- [x] 实现暂存草稿/保存逻辑
- [x] 实现模板选择弹窗
- [x] 实现cURL导入弹窗

### Phase 7: 列表和树更新
- [x] 更新TestCaseList.vue (case_number列、P0-P3优先级)

## 认证系统增强

- [x] 双Token机制 (access_token + refresh_token)
- [x] /auth/refresh接口
- [x] 前端401自动刷新拦截器
- [x] 并发请求队列机制

## Bug修复

- [x] 用例关联模块 (BasicInfoTab添加项目/模块选择)
- [x] datetime序列化错误 (编辑用例500错误)
- [x] 断言和变量提取按钮无响应 (a-form缺少model属性导致组件渲染失败)
- [x] TypeScript编译错误修复 (类型不匹配、未使用变量等)
- [x] 断言卡片内容不显示 (watch循环触发导致数据被覆盖)
- [x] 删除按钮不显示 (Arco Design图标未全局注册)

---

### 技术决策记录

1. **子表更新策略**: 采用删旧插新方式，每次更新时先删除所有子表记录再重新插入，简化逻辑
2. **用例编号格式**: `TC-{MODULE_CODE}-{4位序号}`，保存后自动生成
3. **cURL解析**: 使用Python shlex模块解析cURL命令
4. **双Token刷新**: refresh_token有效期7天，access_token 30分钟，401时自动刷新
5. **Arco Design a-form**: 必须提供`:model`属性，否则组件会静默失败

## 环境管理功能

- [x] 后端环境模型和CRUD API
- [x] 前端环境API调用层
- [x] 创建EnvironmentDrawer.vue环境管理抽屉组件
- [x] 项目列表添加环境管理入口

### 技术决策

- 环境管理放在项目管理模块下，UI和接口测试可共用
- 采用抽屉(Drawer)形式，无需新增路由
- 环境变量支持Key-Value编辑

### 当前待办

- [ ] 端到端测试完整用例管理流程

---

**最后更新**: 2026-05-08
