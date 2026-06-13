# TestForge 测试平台

一站式智能测试平台，覆盖 **UI 自动化测试**、**接口自动化测试**、**AI 生成用例**、**接口调试**、**仪表盘**、**定时任务**、**Monkey 测试** 和 **开发工具箱**，助力团队高效保障软件质量。

## 功能特性

### UI 自动化测试

#### 用例录制

- 嵌入式浏览器录制，在平台内直接操作目标网页
- 实时截图流展示，所见即所得
- 自动捕获操作：点击、输入、导航、按键、拖拽、滚动等
- 智能元素定位：自动生成 CSS Selector 和 XPath
- **录制暂停/恢复**：暂停录制做准备工作，再继续
- **步骤插入**：在任意位置插入新步骤（导航/点击/输入/按键/等待/断言）
- **步骤拖拽排序**：拖拽调整步骤执行顺序
- **步骤编辑**：修改已录制步骤的参数，实时生效
- **录制回放预览**：录制完成后预览回放效果
- 输入框点击弹出输入弹窗，避免误录制
- 断言功能：选择元素后添加多种断言类型
- URL 参数化：选择环境后自动替换为变量，支持多环境复用
- <img width="2559" height="1599" alt="UI自动化-脚本录制" src="https://github.com/user-attachments/assets/a35dd20b-8a9b-4916-b4fe-db59eaf2b048" />

#### 用例管理

- 左侧项目树 + 右侧用例列表布局
- 用例列表按项目分组，显示用例数量
- 步骤详情查看，时间线展示执行流程
- 用例编辑与删除
- 单用例调试执行，实时显示执行画面

#### 执行调试

- 嵌入式浏览器实时执行画面
- 逐步显示执行状态（成功/失败）
- 失败步骤自动截图
- 支持环境变量替换（多环境执行）
- 执行结果统计（通过率、耗时）
- <img width="2559" height="1599" alt="UI自动化-用例执行" src="https://github.com/user-attachments/assets/6f09002e-07d8-4af6-873a-597845a7f6ad" />

---

### 接口自动化测试

#### 用例管理

- 模块化组织，用例编号自动生成（TC-{模块码}-{序号}）
- Excel 批量导入（含数据提取规则），快速迁移存量用例
- cURL 一键导入，从浏览器/Postman 直接粘贴
- 用例模板功能，快速创建相似用例
- 断言配置（状态码 / JSONPath / 响应头 / 响应时间）
- 前置/后置脚本（PyMiniRacer 沙箱，5 秒超时保护）
- <img width="2559" height="1599" alt="接口自动化-用例管理" src="https://github.com/user-attachments/assets/60ab32cf-0875-4f24-8c60-7a564b850ea2" />

#### 场景编排引擎

- 可视化流程编排，流程图 + 属性面板双栏布局
- 4 种节点类型：接口调用 / 条件判断 / 等待延时 / 数据赋值
- 条件分支 Y 形可视化，真/假双列展示，活跃分支高亮
- 节点间变量传递，上游提取自动注入下游请求
- <img width="2559" height="1599" alt="接口自动化-场景编排" src="https://github.com/user-attachments/assets/3cbdce60-b5a9-49bc-8c49-ee917775e1b0" />

#### 数据规则引擎

- 5 种规则类型：响应提取 / 静态值 / 数据生成 / 表达式变换 / 条件赋值
- 规则按序执行，前序输出可供后续引用
- Excel 批量导入时自动解析数据提取规则

#### 执行与报告

- Celery 异步批量执行，支持并发控制与失败策略
- 编排模式通过率智能计算（跳过节点不计入分母）
- 场景编排专属报告：流程图 + 节点详情面板
- 性能统计（P50 / P90 / P95、Top5 慢接口）
- <img width="2559" height="1599" alt="接口自动化-任务执行结果" src="https://github.com/user-attachments/assets/267804f5-c9c5-4db8-bb29-59a2686a3066" />

#### 接口调试

- 类 Postman 可视化调试，cURL 一键导入
- 多环境切换 + 临时变量覆盖
- 请求快照完整展示（变量替换后）

---

### AI 生成测试用例

基于大语言模型，从需求文档或接口文档自动生成测试用例，支持在线编辑、导出和保存到项目。

#### 输入源

- **PRD 文档**：上传 `.docx` / `.pdf` / `.md` 格式的需求文档
- **接口文档**：上传 `.json` / `.yaml` 格式的 Swagger/OpenAPI 文档
- **文本输入**：直接粘贴需求描述或接口定义
- <img width="2559" height="1599" alt="AI生成用例png" src="https://github.com/user-attachments/assets/93b17eea-84a2-4bc9-967b-5a2d9831c942" />

#### 生成能力

- **功能测试用例**：覆盖正常流程、异常流程、边界值、Pairwise 组合、后端一致性验证
- **接口测试用例**：覆盖正向调用、参数校验、边界值、认证鉴权
- **Skill 技能系统**：可复用的 Prompt 模板，支持自定义技能，内置功能/接口测试专家默认技能
- **多模型支持**：OpenAI / Claude / DeepSeek / 自定义兼容端点（中转站、Ollama 等）
- <img width="2559" height="1599" alt="AI生成用例管理技能Prompt" src="https://github.com/user-attachments/assets/c4b048d1-f680-4516-9d48-8d95af9564e4" />

#### 结果处理

- 在线编辑生成的用例，支持全选/批量操作
- 导出为 Excel（格式与导入模板一致）
- 接口测试用例一键保存到项目（自动生成编号、按模块分组）
- <img width="2551" height="1599" alt="AI生成用例结果" src="https://github.com/user-attachments/assets/63e30d0b-82ef-4828-9e94-bc1ac2eeb24e" />

---

### 仪表盘

实时展示测试执行概况，帮助团队快速了解质量状态。

- **统计概览**：项目总数、UI 用例数、接口用例数、今日执行数
- **执行趋势**：近 7 天/30 天执行趋势图表，展示通过/失败/错误分布
- **通过率**：环形图展示整体通过率，按任务类型分类统计
- **最近执行**：展示最近执行记录，点击可跳转详情
- **快捷入口**：常用功能快速访问

---

### 定时任务调度

基于 Celery Beat 实现定时执行，支持可视化配置执行计划。

- **可视化配置**：无需编写 Cron 表达式，选择执行频率即可（每天/工作日/每周/自定义间隔）
- **统一管理**：支持 UI 自动化和接口自动化任务统一配置
- **套件关联**：关联已有测试套件，套件变更自动同步
- **立即执行**：支持手动触发立即执行一次
- **执行记录**：查看历史执行记录，跳转查看详情
- **启用/禁用**：一键开关定时任务

---

### Monkey 稳定性测试

基于随机操作的稳定性测试工具，用于发现潜在的崩溃和异常。

- **随机操作**：自动执行随机点击、滑动、输入等操作
- **参数配置**：可配置操作间隔、事件总数、各事件比例
- **实时监控**：实时显示执行进度和日志
- **异常捕获**：自动捕获崩溃、ANR 等异常
- **报告生成**：生成测试报告，记录异常信息

---

### 开发工具

集成 17 个测试开发常用工具，左侧分类导航，右侧即用即走。

- **数据格式化**：JSON / XML / YAML 格式化与压缩，语法高亮
- **编解码**：Base64 / URL / HTML / Unicode 编解码
- **哈希加密**：MD5 / SHA1 / SHA256 计算、JWT 解析、AES/DES 加解密
- **生成工具**：UUID、随机字符串、测试数据（姓名/手机/身份证等）、二维码
- **时间转换**：时间戳互转、Cron 表达式生成、进制转换
- <img width="2559" height="1599" alt="常用工具JSON格式化" src="https://github.com/user-attachments/assets/33a251a0-8df9-4456-b00f-76a632f4d650" />

## 技术栈

**后端** | FastAPI · SQLAlchemy · MySQL 8.0 · Redis · Celery · Celery Beat · Playwright · httpx · PyMiniRacer · OpenAI SDK · croniter

**前端** | Vue 3 · TypeScript · Arco Design Vue · Pinia · ECharts · Monaco Editor · xlsx · ExcelJS

## 快速开始

### 后端

```bash
cd server
python -m pip install -r requirements_core.txt
python -m pip install email-validator "bcrypt<4.0.0"
python -m pip install openai           # AI 模型获取（可选）
python -m playwright install chromium  # UI 自动化录制需要（首次使用时安装）
```

**配置 `.env`**：

```env
# 数据库
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/testplatform?charset=utf8mb4

# 安全
SECRET_KEY=your-secret-key-here
AI_ENCRYPTION_KEY=your-fernet-key-here   # AI 配置加密，必填
```

> `AI_ENCRYPTION_KEY` 可通过 `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` 生成。

**初始化 / 升级数据库**：

```bash
python init_db.py                    # 全新安装
python migrations/upgrade_all.py     # 升级已有数据库（自动转换 MyISAM → InnoDB）
```

**启动服务**：

```bash
# 终端1：启动 FastAPI
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 终端2：启动 Celery Worker（批量执行和定时任务需要）
celery -A celery_app worker --loglevel=info

# 终端3：启动 Celery Beat（定时任务调度需要，可选）
celery -A celery_app beat --loglevel=info
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

**默认账号**: admin / admin123

## 项目结构

```
TestForge/
├── server/                          # 后端
│   ├── api/                        # API 路由
│   │   ├── auth.py                # 认证授权
│   │   ├── projects.py            # 项目管理
│   │   ├── api_cases.py           # 接口用例 CRUD
│   │   ├── ui_cases.py            # UI 用例 CRUD
│   │   ├── ui_recordings.py       # UI 录制会话管理
│   │   ├── ui_runner.py           # UI 用例执行 API
│   │   ├── ws_ui_record.py        # 录制 WebSocket 端点
│   │   ├── ws_ui_run.py           # 执行 WebSocket 端点
│   │   ├── ai_generate.py         # AI 生成用例
│   │   └── ...
│   ├── models/                    # 数据模型
│   ├── schemas/                   # Pydantic 模型
│   ├── services/                  # 业务服务
│   │   ├── ui_recorder.py         # UI 录制核心服务（Playwright）
│   │   ├── ui_executor.py         # UI 用例执行器
│   │   ├── ui_batch_runner.py     # UI 批量执行引擎
│   │   ├── scene_runner.py        # 场景编排执行引擎
│   │   ├── batch_runner.py        # 接口批量执行引擎
│   │   ├── ai_service.py          # AI 模型调用
│   │   └── ...
│   ├── tasks/                     # Celery 任务
│   │   ├── batch_run_task.py      # 接口批量执行任务
│   │   ├── ui_batch_run_task.py   # UI 批量执行任务
│   │   ├── scene_run_task.py      # 场景编排执行任务
│   │   ├── scheduler_task.py      # 定时调度任务
│   │   └── ai_generate_tasks.py   # AI 生成任务
│   └── migrations/                # 数据库迁移
├── frontend/                      # 前端
│   └── src/
│       ├── api/                  # API 封装
│       │   ├── uiCase.ts         # UI 用例 + 录制 API
│       │   ├── apiTestCase.ts    # 接口用例 API
│       │   └── ...
│       ├── components/           # 通用组件
│       ├── views/
│       │   ├── Dashboard.vue     # 仪表盘
│       │   ├── ui-test/          # UI 自动化
│       │   │   ├── Record.vue    # 录制页面
│       │   │   ├── CaseList.vue  # 用例管理
│       │   │   ├── RunDebug.vue  # 执行调试
│       │   │   └── components/   # 子组件
│       │   ├── api-test/         # 接口自动化
│       │   ├── ai-generate/      # AI 生成
│       │   ├── scheduled/        # 定时任务
│       │   ├── reports/          # 测试报告
│       │   ├── tools/            # 开发工具 & Monkey 测试
│       │   └── ...
│       ├── layouts/              # 布局组件
│       ├── stores/               # 状态管理
│       └── router/               # 路由配置
└── docs/                          # 文档
```

## 作者

By：Zzh（Paoomian）
