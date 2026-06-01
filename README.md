# TestForge 测试平台

一站式测试平台，覆盖接口自动化测试与 UI 自动化测试。

## 功能特性

### UI 自动化测试

#### 录制回放

- 嵌入式浏览器录制，在平台内直接操作目标网页
- 实时截图流展示，所见即所得
- 自动捕获操作：点击、输入、导航、按键等
- 智能元素定位：自动生成 CSS Selector 和 XPath
- 录制步骤在线编辑，支持增删改查
- 用例一键保存到项目，支持导出

#### 用例管理

- 用例列表按项目分组，支持搜索筛选
- 步骤详情查看，时间线展示执行流程
- 用例编辑与删除

---

### 接口自动化测试

#### 用例管理

- 模块化组织，用例编号自动生成（TC-{模块码}-{序号}）
- Excel 批量导入（含数据提取规则），快速迁移存量用例
- cURL 一键导入，从浏览器/Postman 直接粘贴
- 用例模板功能，快速创建相似用例
- 断言配置（状态码 / JSONPath / 响应头 / 响应时间）
- 前置/后置脚本（PyMiniRacer 沙箱，5 秒超时保护）

#### 场景编排引擎

- 可视化流程编排，流程图 + 属性面板双栏布局
- 4 种节点类型：接口调用 / 条件判断 / 等待延时 / 数据赋值
- 条件分支 Y 形可视化，真/假双列展示，活跃分支高亮
- 节点间变量传递，上游提取自动注入下游请求

#### 数据规则引擎

- 5 种规则类型：响应提取 / 静态值 / 数据生成 / 表达式变换 / 条件赋值
- 规则按序执行，前序输出可供后续引用
- Excel 批量导入时自动解析数据提取规则

#### 执行与报告

- Celery 异步批量执行，支持并发控制与失败策略
- 编排模式通过率智能计算（跳过节点不计入分母）
- 场景编排专属报告：流程图 + 节点详情面板
- 性能统计（P50 / P90 / P95、Top5 慢接口）

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

#### 生成能力

- **功能测试用例**：覆盖正常流程、异常流程、边界值、Pairwise 组合、后端一致性验证
- **接口测试用例**：覆盖正向调用、参数校验、边界值、认证鉴权
- **Skill 技能系统**：可复用的 Prompt 模板，支持自定义技能，内置功能/接口测试专家默认技能
- **多模型支持**：OpenAI / Claude / DeepSeek / 自定义兼容端点（中转站、Ollama 等）

#### 结果处理

- 在线编辑生成的用例，支持全选/批量操作
- 导出为 Excel（格式与导入模板一致）
- 接口测试用例一键保存到项目（自动生成编号、按模块分组）

#### 任务管理

- Celery 异步执行，带实时进度追踪
- 支持重试失败任务、取消进行中任务
- AI 响应多重容错解析（代码块提取、截断修复、引号转义等）

---

### 开发工具

集成 17 个测试开发常用工具，左侧分类导航，右侧即用即走。

- **数据格式化**：JSON / XML / YAML 格式化与压缩，语法高亮
- **编解码**：Base64 / URL / HTML / Unicode 编解码
- **哈希加密**：MD5 / SHA1 / SHA256 计算、JWT 解析、AES/DES 加解密
- **生成工具**：UUID、随机字符串、测试数据（姓名/手机/身份证等）、二维码
- **时间转换**：时间戳互转、Cron 表达式生成、进制转换

## 技术栈

**后端** | FastAPI · SQLAlchemy · MySQL 8.0 · Redis · Celery · httpx · PyMiniRacer · OpenAI SDK

**前端** | Vue 3 · TypeScript · Arco Design Vue · Pinia · ECharts · xlsx · ExcelJS

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

# 终端2：启动 Celery Worker（批量执行需要）
celery -A celery_app worker --loglevel=info
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
├── server/                     # 后端
│   ├── api/                   # API 路由
│   ├── models/                # 数据模型
│   ├── schemas/               # Pydantic 模型
│   ├── services/              # 业务服务（执行引擎）
│   ├── tasks/                 # Celery 任务
│   └── migrations/            # 数据库迁移
├── frontend/                  # 前端
│   └── src/
│       ├── api/              # API 封装
│       ├── components/       # 通用组件
│       ├── views/            # 页面
│       └── stores/           # 状态管理
└── docs/                      # 文档
```

## 许可证

MIT License
