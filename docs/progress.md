# TestForge 开发进度

## 已完成功能

### 基础框架
- [x] FastAPI后端 + Vue 3前端框架搭建
- [x] 数据库设计与初始化
- [x] JWT双Token认证系统（access 30min + refresh 7天）
- [x] RBAC权限系统

### 接口调试
- [x] HTTP请求发送、参数编辑、响应展示

### 用例管理 (v2重构)
- [x] 6个子表模型（headers/query_params/body_form/body_raw/assertions/extracts/auth）
- [x] 嵌套Schema + CRUD API（含cURL导入、模板功能）
- [x] 前端4Tab组件（基本信息/请求配置/断言提取/脚本）
- [x] 用例编号自动生成（TC-{模块码}-{4位序号}）

### 环境管理
- [x] 后端环境模型和CRUD API
- [x] 前端EnvironmentDrawer.vue抽屉组件
- [x] 项目列表添加环境管理入口

### 单用例调试执行
- [x] 执行引擎拆分：变量替换/脚本执行/HTTP请求/断言/提取
- [x] 前端调试台（CaseConfigPanel + DebugResultPanel + TestCaseDebug）
- [x] 环境自动加载、路由配置

### 批量执行
- [x] TestRun + TestRunDetail模型，Celery异步任务
- [x] 前端任务列表（按日期分组）+ 任务详情（1.5s轮询）
- [x] 实时统计、进度条、用例详情抽屉

### 任务配置（测试套件）
- [x] TestSuite模型 + CRUD + 运行API
- [x] 前端卡片列表（4列/行）+ 编辑抽屉（用例筛选、执行配置）

### 测试报告
- [x] 统计计算（通过率、P50/P90/P95、Top5、失败分类）
- [x] 前端报告面板（摘要卡片、性能统计条形图、失败分析饼图）

### 可视化数据传递
- [x] TestCaseDataRule模型 + DataRuleService执行引擎
- [x] 5种规则类型：extract/static/generate/transform/conditional
- [x] 前端DataRuleCard + DataRuleEditor组件
- [x] 批量执行中数据规则变量传递
- [x] 合并test_case_extracts到test_case_data_rules（消除冗余表）

### Excel批量导入
- [x] 后端Schema定义（ExcelImportRequest/ExcelCaseItem/ExcelImportResult）
- [x] 后端导入服务（校验 + 批量创建）
- [x] 后端API端点（POST /api-test-cases/import-excel）
- [x] 前端xlsx依赖安装
- [x] 前端Excel解析工具（excelParser.ts）
- [x] 前端导入API层（excelImport.ts）
- [x] 前端导入弹窗组件（ExcelImportModal.vue）
- [x] 集成到用例列表页

### 接口自动化执行详情优化
- [x] 执行详情窗口宽度从680px增加到900px
- [x] 请求快照中新增Query Params展示（GET请求参数可见）
- [x] 移除Authorization/Token的脱敏处理，Headers完整显示
- [x] 修复批量执行与单用例调试的脱敏一致性（重启Celery生效）

### 用例场景编排
- [x] 前端SceneOrchestrator.vue编排器组件
- [x] 前端SceneNodeCard.vue节点卡片组件
- [x] 4种节点类型：接口调用/条件判断/等待延时/数据赋值
- [x] ApiCallNodeForm/ConditionNodeForm/WaitNodeForm/DataAssignNodeForm表单组件
- [x] 前端API层（sceneNode.ts）
- [x] 后端SceneNode模型 + CRUD API（2026-05-21完成）
- [x] 后端场景执行引擎SceneRunner（2026-05-22完成）
- [x] 条件节点分支跳转配置（2026-05-22完成）
- [x] 任务详情页适配节点类型展示（2026-05-22完成）
- [x] UI重构：左侧流程图+右侧属性面板布局（2026-05-22完成）
- [x] 条件分支可视化：Y形分叉+真/假双列展示（2026-05-22完成）
- [x] 编排抽屉近全屏宽度（2026-05-22完成）
- [x] 任务记录列表支持简单/编排模式分类筛选（2026-05-22完成）
- [x] 编排模式专属报告页：流程图+节点详情面板（2026-05-22完成）
- [x] 编排模式通过率修正：skipped不计入分母（2026-05-22完成）
- [x] 条件分支流程图Y形可视化+活跃/非活跃分支区分（2026-05-22完成）
- [x] 节点详情面板：请求快照/响应/断言/变量提取/脚本输出（2026-05-22完成）

### 开发工具页面
- [x] ToolLayout共享布局组件（输入/输出分栏）
- [x] ToolsPage主页面（左侧卡片列表 + 右侧工具内容）
- [x] 路由配置 + 侧边栏菜单
- [x] 数据格式化：JSON/XML/YAML格式化（3个工具）
- [x] 编解码：Base64/URL/HTML/Unicode编解码（4个工具）
- [x] 哈希加密：哈希计算/JWT解析/AES-DES加解密（3个工具）
- [x] 生成工具：UUID/随机字符串/测试数据/二维码生成（4个工具）
- [x] 时间转换：时间戳转换/Cron生成器/进制转换（3个工具）

### AI 生成测试用例
- [x] AI 配置管理（支持多模型和中转站）
- [x] 文档上传和解析（PRD/Swagger）
- [x] 测试用例生成功能（功能/接口/边界值/组合）
- [x] 生成任务管理（异步执行、进度跟踪）
- [x] 用例编辑和保存到项目
- [x] Skill（Prompt 模板）可配置系统（2026-05-24）
- [x] System/User Prompt 合并为单一「Prompt 模板」字段（2026-05-24）
- [x] 系统自动附加 Pairwise 示例 + backend_ui 示例 + JSON 格式要求（2026-05-24）
- [x] JSON 解析增强：未转义引号修复 + 截断恢复（2026-05-24）
- [x] 多项 Bug 修复：retry 回退、cancel 状态、checkbox 全选、外键删除、Excel 双序号、.format() KeyError（2026-05-24）
- [x] 边界值具体数值要求 + expected_results 数组格式支持（2026-05-24）
- [x] 技能管理 UI 优化：布局、宽度、textarea 自适应（2026-05-24）
- [ ] AI 模型对 combination/backend_ui 有系统性盲区，待换更强模型验证（2026-05-24）

---

## 技术决策

| 决策 | 原因 |
|------|------|
| 子表更新采用删旧插新 | 简化逻辑，避免复杂diff |
| JS脚本使用PyMiniRacer沙箱 | 5秒超时强制中断，安全隔离 |
| 轮询替代WebSocket（1.5s间隔） | 实现简单，WebSocket已实现但未使用 |
| 变量提取Tab移除，统一使用数据规则 | 功能重复，数据规则完全覆盖 |
| 批量执行拖拽排序用HTML5原生API | 零依赖实现 |
| MySQL ENUM改VARCHAR(20) | 避免截断问题 |
| datetime使用naive模式 | 避免timezone偏移错误 |
| 迁移脚本合并为upgrade_all.py | 10个独立迁移合并为1个统一脚本，可重复执行 |
| 场景编排UI用流程图+属性面板 | 分支可视化，编辑空间充足，CSS连线零依赖 |
| 分支归属用branch_of字段推导 | 前端渲染用，不改后端模型，从true_branch/false_branch反推 |
| test_case_extracts合并到test_case_data_rules | 消除冗余表，统一用rule_type="extract"表示提取规则 |
| 编排模式通过率=pass/(pass+fail+error) | skipped是条件跳过的分支，不应计入分母拉低通过率 |
| 编排任务详情用node_tree替代flat列表 | 通过detail.node_id反查SceneNode.suite_id构建树结构 |
| batch-delete路由放在/{run_id}之前 | FastAPI按定义顺序匹配，避免"batch-delete"被当作int解析导致422 |
| Prompt模板合并为单一system_prompt字段 | user_prompt留空由后端自动生成，降低用户配置复杂度 |
| JSON解析预处理fix_json_quotes | 逐字符状态机修复AI返回的未转义引号，比正则更可靠 |
| 外键删除前先解除引用 | 删除Skill前将关联Task的skill_id置NULL，避免约束报错 |

---

## 待开发功能

> 按优先级排列，基于测试开发工程师视角

### P0 - 核心能力补齐

#### ~~1. 可视化数据传递~~ ✅ 已完成

#### ~~2. Excel批量导入~~ ✅ 已完成

#### 3. Swagger/OpenAPI 批量导入
- [ ] 后端：Swagger解析服务（解析paths/definitions/parameters）
- [ ] 后端：POST /api-test-cases/import-swagger 接口
- [ ] 前端：导入弹窗（URL输入/文件上传、模块映射、预览确认）

**预估工作量**：中

### P1 - 接口自动化核心能力

#### 3. 数据驱动 / 参数化执行
- [ ] 后端：数据集模型（data_sets表，存储文件路径/列定义/行数）
- [ ] 后端：批量执行引擎改造（用例数 × 数据行数展开）
- [ ] 前端：数据集管理、执行配置选择数据集

**预估工作量**：大

#### ~~4. 用例场景编排~~ ✅ 已完成
- [x] 前端：表单式编排器（4种节点类型）
- [x] 后端：编排节点模型 + CRUD API
- [x] 后端：场景执行引擎（SceneRunner）
- [x] 条件节点分支跳转配置
- [x] 任务详情页适配节点类型

**预估工作量**：大（已完成）

### P2 - 体验与产出增强

#### 5. 测试报告增强
- [ ] 报告导出（PDF/HTML）
- [ ] 历史趋势对比（通过率/响应时间曲线）
- [ ] 报告分享链接（带Token临时访问URL）

**预估工作量**：中

#### 6. 环境变量增强
- [ ] 敏感变量加密存储（前端遮蔽显示）
- [ ] 变量描述字段和类型标记（string/number/secret）
- [ ] 全局变量（跨项目共享）

**预估工作量**：小

#### 7. 断言能力增强
- [ ] JSON Schema 校验断言
- [ ] 断言失败 expected vs actual 对比展示优化

**预估工作量**：小

### P3 - 体验优化

#### 8. 调试体验优化
- [ ] 请求历史记录（最近N次调试结果回看）
- [ ] 响应对比功能（两次执行结果diff）

**预估工作量**：小

#### 9. 用例维护辅助
- [ ] 标签筛选完善
- [ ] 用例执行频率统计（最近执行时间、失败率排行）

**预估工作量**：小

#### 10. Postman Collection 导入
- [ ] 支持导入Postman Collection v2.1 JSON格式

**预估工作量**：中

---

**最后更新**: 2026-05-24（Skill 系统 + Prompt 优化 + 多项 Bug 修复）
