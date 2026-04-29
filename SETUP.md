# 测试平台 - 本地开发启动步骤

## 前置准备

确保已安装：
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

## 启动步骤

### 1. 启动数据库（使用Docker）

```bash
# 启动PostgreSQL
docker run -d --name testplatform-postgres \
  -e POSTGRES_USER=testplatform \
  -e POSTGRES_PASSWORD=testplatform123 \
  -e POSTGRES_DB=testplatform \
  -p 5432:5432 \
  postgres:15-alpine

# 启动Redis
docker run -d --name testplatform-redis \
  -p 6379:6379 \
  redis:7-alpine
```

### 2. 启动后端

```bash
# 进入后端目录
cd server

# 创建虚拟环境（可选但推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium

# 初始化数据库
python init_db.py

# 启动后端服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端将运行在: http://localhost:8000
API文档: http://localhost:8000/docs

### 3. 启动前端

打开新的终端窗口：

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在: http://localhost:5173

### 4. 登录系统

访问 http://localhost:5173，使用默认账号登录：
- 用户名: `admin`
- 密码: `admin123`

## 使用Docker Compose（更简单）

如果你想一键启动所有服务：

```bash
# 在项目根目录执行
docker-compose up -d

# 初始化数据库
docker-compose exec backend python init_db.py

# 查看日志
docker-compose logs -f
```

## 验证安装

1. 访问后端健康检查: http://localhost:8000/health
2. 访问API文档: http://localhost:8000/docs
3. 访问前端: http://localhost:5173
4. 使用admin账号登录

## 常见问题

### 后端启动失败

**问题**: `ModuleNotFoundError: No module named 'pydantic_settings'`
**解决**: 确保安装了所有依赖 `pip install -r requirements.txt`

**问题**: 数据库连接失败
**解决**: 
1. 检查PostgreSQL是否运行: `docker ps | grep postgres`
2. 检查.env文件中的DATABASE_URL配置

### 前端启动失败

**问题**: `Cannot find module '@arco-design/web-vue'`
**解决**: 重新安装依赖 `npm install`

**问题**: 无法连接后端API
**解决**: 
1. 确认后端已启动: `curl http://localhost:8000/health`
2. 检查vite.config.ts中的proxy配置

### 数据库初始化失败

**问题**: `relation "users" already exists`
**解决**: 数据库已初始化，可以直接使用

**问题**: `could not connect to server`
**解决**: 确保PostgreSQL正在运行并且端口5432未被占用

## 下一步

1. ✅ 登录系统
2. ✅ 创建第一个项目
3. ✅ 尝试接口调试功能
4. ⏳ 开发UI自动化功能
5. ⏳ 开发接口自动化功能

## 项目结构说明

```
testing-platform/
├── server/                 # 后端FastAPI项目
│   ├── api/               # API路由（auth, projects, ui_cases, api_cases）
│   ├── core/              # 核心功能（认证、配置、依赖注入）
│   ├── models/            # SQLAlchemy数据库模型
│   ├── schemas/           # Pydantic请求/响应模型
│   ├── alembic/           # 数据库迁移文件
│   ├── main.py            # FastAPI应用入口
│   ├── database.py        # 数据库连接配置
│   └── init_db.py         # 数据库初始化脚本
│
├── frontend/              # 前端Vue3项目
│   ├── src/
│   │   ├── api/          # API请求封装
│   │   ├── layouts/      # 布局组件（MainLayout）
│   │   ├── router/       # Vue Router配置
│   │   ├── stores/       # Pinia状态管理（user store）
│   │   ├── types/        # TypeScript类型定义
│   │   ├── utils/        # 工具函数（axios封装）
│   │   └── views/        # 页面组件
│   │       ├── Login.vue           # 登录页
│   │       ├── Dashboard.vue       # 仪表盘
│   │       ├── projects/           # 项目管理
│   │       ├── ui-test/            # UI自动化
│   │       ├── api-test/           # 接口自动化
│   │       ├── api-debug/          # 接口调试
│   │       └── reports/            # 测试报告
│   └── vite.config.ts    # Vite配置
│
├── docker-compose.yml     # Docker编排配置
├── README.md             # 项目说明
└── QUICKSTART.md         # 快速启动指南
```

## 技术亮点

### 后端
- ✅ FastAPI异步框架，高性能
- ✅ JWT认证 + RBAC权限控制
- ✅ SQLAlchemy ORM + Alembic迁移
- ✅ Pydantic数据验证
- ✅ 完整的RESTful API设计
- ✅ 接口调试功能（类Postman）

### 前端
- ✅ Vue 3 Composition API
- ✅ TypeScript类型安全
- ✅ Arco Design Vue美观UI
- ✅ Pinia状态管理
- ✅ Axios请求拦截器
- ✅ 路由守卫与权限控制
- ✅ 渐变色登录页面
- ✅ 响应式侧边栏布局

## 已实现功能

- ✅ 用户注册与登录
- ✅ JWT Token认证
- ✅ 角色权限管理（admin/tester/viewer）
- ✅ 项目管理CRUD
- ✅ UI用例管理接口
- ✅ 接口用例管理接口
- ✅ 接口调试工具（发送HTTP请求）
- ✅ 美观的前端界面
- ✅ 完整的路由和布局

## 待开发功能

- ⏳ UI自动化录制（Playwright Codegen集成）
- ⏳ UI自动化执行引擎
- ⏳ 接口录制（mitmproxy代理）
- ⏳ 接口自动化执行引擎
- ⏳ 测试报告生成与展示
- ⏳ 定时任务调度（Celery）
- ⏳ WebSocket实时日志推送
- ⏳ 数据驱动测试
- ⏳ 环境变量管理

## 开发建议

1. **后端开发**: 从`server/api/`目录开始，添加新的路由
2. **前端开发**: 从`frontend/src/views/`目录开始，完善页面功能
3. **数据库变更**: 使用Alembic创建迁移 `alembic revision --autogenerate -m "description"`
4. **API测试**: 访问 http://localhost:8000/docs 使用Swagger UI测试

祝开发顺利！🚀
