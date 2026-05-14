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

## 单用例调试执行功能

### 后端执行引擎
- [x] 新增依赖 (py-mini-racer, jsonpath-ng)
- [x] 创建执行Schema (schemas/test_run.py)
- [x] 创建变量替换服务 (variable_service.py)
- [x] 创建JS脚本执行服务 (script_service.py)
- [x] 创建HTTP请求服务 (http_service.py)
- [x] 创建断言执行服务 (assertion_service.py)
- [x] 创建变量提取服务 (extract_service.py)
- [x] 创建主执行器 (runner.py)
- [x] 创建API路由 (api/test_runner.py)

### 前端调试台
- [x] apiTestCase.ts 增加 RunRequest/RunResult 类型和 runTestCase 函数
- [x] 创建 CaseConfigPanel.vue（左侧用例配置展示）
- [x] 创建 DebugResultPanel.vue（右侧操作+结果区）
- [x] 创建 TestCaseDebug.vue（调试台页面容器）
- [x] TestCaseList.vue 操作列增加「调试」按钮
- [x] router 增加 /api-test-debug/:caseId 路由
- [x] 环境自动加载（根据用例 project_id，默认选中第一个）

### 技术决策

- 执行引擎按职责拆分：变量替换、脚本执行、HTTP请求、断言、提取各自独立
- JS脚本使用 PyMiniRacer 沙箱，5秒超时强制中断
- 响应体超过10KB截断，敏感字段脱敏
- 每条断言独立执行，互不影响
- 变量优先级：临时变量 > 脚本设置 > 环境变量 > 全局变量
- API路径：POST /api/v1/test-runner/{case_id}/run

### 待办

- [ ] 端到端测试完整用例管理流程

## 批量执行功能

### 后端
- [x] 扩展TestRun模型（environment_id, concurrency, failure_strategy, variables等）
- [x] 新增TestRunDetail模型（用例执行明细）
- [x] 创建批量执行服务 (batch_runner.py) - asyncio.gather并发控制
- [x] Celery异步任务 (tasks/batch_run_task.py)
- [x] 批量执行API (api/batch_runs.py) - 创建/列表/详情/取消/删除
- [x] 实时统计计算（从明细表实时聚合pass/fail/error数量）
- [x] 数据库迁移脚本 (migrations/add_batch_run_fields.py)

### 前端
- [x] batchRun.ts API层（创建/列表/详情/取消/删除/批量删除）
- [x] BatchRunTaskList.vue 任务列表页（按日期分组显示 + 批量删除）
- [x] BatchRunDetail.vue 任务详情页（1.5s轮询实时更新）
- [x] BatchRunProgress.vue 进度条组件
- [x] CaseResultDetail.vue 用例执行详情抽屉
- [x] 断言类型/运算符中文本地化（状态码、JSONPath、等于、包含等）

### 技术决策
- 使用Celery + Redis异步执行，worker_pool=solo兼容Windows
- 轮询替代WebSocket（1.5s间隔），WebSocket实现在ws_batch.py但未使用
- 变量隔离：每条用例获取只读快照，提取变量串行合并回主上下文
- MySQL ENUM改VARCHAR(20)避免截断问题
- datetime使用naive模式避免timezone偏移错误
- 任务列表按日期分组（今天/昨天/前天/3天前/4-7天前/更早），使用a-collapse嵌套a-table实现
- 批量删除API：POST /batch-runs/batch-delete，自动过滤运行中的任务

## 任务配置功能（测试套件）

### 后端
- [x] TestSuite模型 (models/test_suite.py)
- [x] Pydantic Schema (schemas/test_suite.py)
- [x] CRUD + 运行API (api/test_suites.py)
- [x] 数据库迁移脚本 (migrations/add_test_suites.py)

### 前端
- [x] testSuite.ts API层
- [x] TestSuiteList.vue 卡片列表（4列/行，显示项目名、用例数、环境、并发模式）
- [x] TestSuiteDrawer.vue 编辑抽屉（用例筛选、执行配置、标签）

### 技术决策
- 任务配置复用批量执行逻辑，/run端点创建TestRun后触发Celery任务
- 运行时可覆盖默认配置（环境、并发数、失败策略、变量）
- 卡片布局span=6（4列），展示项目名蓝色标签

## 测试报告功能 (2026-05-11)

### 后端
- [x] 新增测试报告 Schema (TestSummary, PerformanceStats, FailureAnalysis, BatchRunReport)
- [x] 新增 GET /batch-runs/{id}/report 接口
- [x] 实现统计计算逻辑（通过率、P50/P90/P95、Top5、失败分类）
- [x] 实现失败原因分类（断言失败/请求超时/连接失败/执行异常）

### 前端
- [x] batchRun.ts 新增 getBatchRunReport API 和类型定义
- [x] 创建 TestSummaryCard.vue（测试摘要卡片）
- [x] 创建 PerformanceStatsCard.vue（性能统计 + echarts 条形图）
- [x] 创建 FailureAnalysisCard.vue（失败分析 + echarts 饼图）
- [x] 创建 TestReportPanel.vue（Tab 切换容器）
- [x] 集成到 BatchRunDetail.vue

### 技术决策
- 测试报告实时计算，不存储冗余数据
- P90/P95 使用 nearest-rank 算法
- 失败分类基于 error_message 关键词匹配
- 报告仅在任务完成后显示（done/error/cancelled）

## 可视化数据传递功能 (2026-05-12)

### 后端
- [x] 新增 TestCaseDataRule 模型 (models/test_case_data_rule.py)
- [x] 新增 DataRuleService 执行引擎 (services/api_test_runner/data_rule_service.py)
- [x] 数据库迁移脚本 (migrations/add_data_rules.py)
- [x] Schema 新增 DataRuleItem + 主表 Schema 新增 data_rules 字段
- [x] API CRUD 支持 data_rules（创建/更新/删除/复制/列表序列化）
- [x] runner.py 集成数据规则执行（变量提取之后、断言之前）
- [x] RunResult 新增 data_rule_variables 字段
- [x] batch_runner.py 合并数据规则变量到共享变量

### 前端
- [x] apiTestCase.ts 新增 DataRuleItem 接口 + RunResult 新增 data_rule_variables
- [x] 创建 DataRuleCard.vue（单条规则卡片，根据 rule_type 动态切换表单）
- [x] 创建 DataRuleEditor.vue（规则列表编辑器，本地副本 + emitChange 模式）
- [x] 修改 AssertionExtractTab.vue（新增第三个 Tab "数据规则"）
- [x] 修改 TestCaseDrawer.vue（formData 新增 data_rules，数据流打通）
- [x] 修改 DebugResultPanel.vue（展示数据规则变量）

### 技术决策
- 新建独立子表 test_case_data_rules，不复用 ExtractEditor 结构
- 数据规则在变量提取之后执行，transform 类型可对提取的变量做二次处理
- 5种规则类型：extract/static/generate/transform/conditional
- 规则按 sort_order 顺序执行，前面规则的输出可供后续规则引用
- 批量执行中数据规则变量合并到 extracted_vars 中传递给后续用例

## Bug修复与优化 (2026-05-11)

- [x] 修复任务详情环境显示问题（显示环境名称而非ID）
- [x] 修复批量删除用例外键约束错误（外键改为 ON DELETE SET NULL）
- [x] 任务配置执行时检查用例是否存在（已删除则提示）
- [x] 导航名称优化："执行任务" → "任务记录"
- [x] 任务详情页优化：精简任务信息卡片，执行中显示进度/完成后显示报告

## Bug修复与优化 (2026-05-14)

- [x] 修复数据规则输入框无法输入（Arco Design a-input 的 @change 改为 @input）
- [x] 移除"变量提取"Tab（数据规则 extract 类型完全覆盖，后端共用 ExtractService）
- [x] 修复批量执行跨用例变量传递失败（asyncio.gather 后 ORM 对象 session 过期，改用 result 对象判断状态）
- [x] 批量执行用例支持拖拽排序（HTML5 原生拖拽，零依赖）

---

## 待开发功能规划

> 基于测试开发工程师视角的功能评估，按优先级排列

### P0 - 核心能力补齐

#### ~~1. 可视化数据传递（解决脚本门槛）~~ ✅ 已完成

**问题**：前置/后置脚本需要手写JavaScript，非开发人员无法使用接口关联功能

**方案**：新增"数据规则"模块，支持5种规则类型（从响应提取/设置静态值/生成数据/数据变换/条件赋值），通过表单配置完成变量提取和传递

- [x] 后端：TestCaseDataRule 模型 + 迁移脚本
- [x] 后端：DataRuleService 执行引擎（集成到 runner.py）
- [x] 后端：Schema + API CRUD 支持
- [x] 前端：DataRuleCard.vue + DataRuleEditor.vue 可视化配置组件
- [x] 前端：集成到 AssertionExtractTab.vue 作为第三个 Tab
- [x] 前端：调试结果面板展示数据规则变量
- [x] 批量执行中数据规则变量传递

**预估工作量**：中

#### 2. Swagger/OpenAPI 批量导入

**问题**：只能逐条手动创建或cURL导入，新项目接入成本极高

**方案**：支持导入Swagger JSON/YAML，自动解析为用例列表

- [ ] 后端：Swagger解析服务（解析paths/definitions/parameters）
- [ ] 后端：POST /api-test-cases/import-swagger 接口
- [ ] 前端：Swagger导入弹窗（URL输入/文件上传、模块映射、预览确认）
- [ ] 前端：批量导入进度和结果展示

**预估工作量**：中

### P1 - 接口自动化核心能力

#### 3. 数据驱动 / 参数化执行

**问题**：同一用例无法用不同数据集批量执行，只能复制多份用例

**方案**：支持CSV/Excel数据集，用例中用 `{{column_name}}` 引用

- [ ] 后端：数据集模型（data_sets表，存储文件路径/列定义/行数）
- [ ] 后端：数据集CRUD API
- [ ] 后端：批量执行引擎改造（用例数 × 数据行数展开）
- [ ] 后端：执行明细关联数据行索引
- [ ] 前端：数据集管理页面/弹窗
- [ ] 前端：批量执行配置中选择数据集
- [ ] 前端：报告按数据行维度展示

**预估工作量**：大

#### 4. 用例场景编排

**问题**：测试套件只是用例列表，无法实现条件分支、等待、循环等流程控制

**方案**：在套件中支持编排节点类型

- [ ] 后端：编排节点模型（scene_nodes表，支持接口调用/条件判断/等待/数据赋值）
- [ ] 后端：场景执行引擎（按节点类型分发执行）
- [ ] 前端：场景编排器组件（拖拽式或表单式）
- [ ] 前端：集成到TestSuiteDrawer.vue

**预估工作量**：大

### P2 - 体验与产出增强

#### 5. 测试报告增强

- [ ] 报告导出（PDF/HTML格式）
- [ ] 历史趋势对比（通过率/响应时间变化曲线）
- [ ] 报告分享链接（带Token的临时访问URL）
- [ ] 接口覆盖率统计

**预估工作量**：中

#### 6. 环境变量增强

- [ ] 敏感变量加密存储（前端遮蔽显示）
- [ ] 变量描述字段和类型标记（string/number/secret）
- [ ] 全局变量（跨项目共享，当前代码有预留未实现）

**预估工作量**：小

#### 7. 断言能力增强

- [ ] JSON Schema 校验断言
- [ ] 断言失败时 expected vs actual 对比展示优化

**预估工作量**：小

### P3 - 体验优化

#### 8. 调试体验优化

- [ ] 请求历史记录（最近N次调试结果回看）
- [ ] 响应对比功能（两次执行结果diff）
- [ ] cURL导入入口在调试台更显眼位置

**预估工作量**：小

#### 9. 用例维护辅助

- [ ] 标签筛选完善（前端筛选组件对接tags字段）
- [ ] 用例有效性检查（接口URL变更影响分析）
- [ ] 用例执行频率统计（最近执行时间、失败率排行）

**预估工作量**：小

#### 10. Postman Collection 导入

- [ ] 支持导入Postman Collection v2.1 JSON格式
- [ ] 自动转换请求、变量、认证配置

**预估工作量**：中

---

### 技术决策

- Arco Design a-input 的 `@change` 事件只在失焦时触发，需用 `@input` 实现实时输入
- asyncio.gather 返回后 SQLAlchemy ORM 对象可能被 session 过期，跨 await 边界应使用值对象而非 ORM 属性
- 变量提取 Tab 与数据规则 extract 类型功能重复，统一使用数据规则作为变量管理入口
- 批量执行拖拽排序使用 HTML5 原生 drag-and-drop API，零依赖实现
- 任务列表日期分组使用 a-collapse + a-table 组合，支持分组全选和批量删除

**最后更新**: 2026-05-15
