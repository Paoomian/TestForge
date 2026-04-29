# 测试平台 - 快速启动指南

## 环境要求

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

## 快速启动

### 方式一：Docker Compose（推荐）

1. 启动所有服务
```bash
docker-compose up -d
```

2. 初始化数据库
```bash
docker-compose exec backend python init_db.py
```

3. 访问应用
- 前端: http://localhost:5173
- 后端: http://localhost:8000
- API文档: http://localhost:8000/docs

### 方式二：本地开发

#### 1. 启动数据库服务

```bash
# 使用Docker启动PostgreSQL和Redis
docker run -d --name postgres -p 5432:5432 \
  -e POSTGRES_USER=testplatform \
  -e POSTGRES_PASSWORD=testplatform123 \
  -e POSTGRES_DB=testplatform \
  postgres:15-alpine

docker run -d --name redis -p 6379:6379 redis:7-alpine
```

#### 2. 启动后端

```bash
cd server

# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium

# 复制环境变量文件
cp .env.example .env

# 初始化数据库
python init_db.py

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 默认账号

- 用户名: `admin`
- 密码: `admin123`

**⚠️ 请在生产环境中修改默认密码！**

## 常用命令

### 后端

```bash
# 创建数据库迁移
alembic revision --autogenerate -m "description"

# 执行数据库迁移
alembic upgrade head

# 回滚数据库迁移
alembic downgrade -1

# 启动Celery Worker
celery -A tasks.celery_app worker --loglevel=info
```

### 前端

```bash
# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

## 项目功能

### 已完成
- ✅ 用户认证与授权（JWT）
- ✅ 角色权限管理（RBAC）
- ✅ 项目管理
- ✅ 接口调试工具
- ✅ 美观的登录页面
- ✅ 响应式主布局

### 待开发
- ⏳ UI自动化录制
- ⏳ UI自动化执行
- ⏳ 接口自动化录制
- ⏳ 接口自动化执行
- ⏳ 测试报告生成
- ⏳ 定时任务调度

## 技术架构

### 后端技术栈
- FastAPI - Web框架
- SQLAlchemy - ORM
- PostgreSQL - 数据库
- Redis - 缓存
- Celery - 异步任务
- Playwright - UI自动化
- JWT - 认证

### 前端技术栈
- Vue 3 - 前端框架
- TypeScript - 类型系统
- Arco Design Vue - UI组件库
- Pinia - 状态管理
- Vue Router - 路由
- Axios - HTTP客户端

## 目录结构

```
testing-platform/
├── server/                 # 后端
│   ├── api/               # API路由
│   ├── core/              # 核心功能（认证、配置等）
│   ├── models/            # 数据库模型
│   ├── schemas/           # Pydantic模型
│   ├── alembic/           # 数据库迁移
│   └── main.py            # 应用入口
├── frontend/              # 前端
│   ├── src/
│   │   ├── api/          # API封装
│   │   ├── layouts/      # 布局组件
│   │   ├── router/       # 路由配置
│   │   ├── stores/       # Pinia状态
│   │   ├── views/        # 页面组件
│   │   └── utils/        # 工具函数
│   └── package.json
└── docker-compose.yml     # Docker编排
```

## 故障排查

### 后端无法启动
1. 检查PostgreSQL是否运行: `docker ps | grep postgres`
2. 检查环境变量配置: `cat server/.env`
3. 查看日志: `docker-compose logs backend`

### 前端无法访问后端
1. 检查后端是否运行: `curl http://localhost:8000/health`
2. 检查CORS配置: `server/.env` 中的 `BACKEND_CORS_ORIGINS`
3. 检查代理配置: `frontend/vite.config.ts`

### 数据库连接失败
1. 确认PostgreSQL运行: `docker ps | grep postgres`
2. 测试连接: `psql -h localhost -U testplatform -d testplatform`
3. 检查DATABASE_URL配置

## 下一步

1. 登录系统: http://localhost:5173
2. 创建第一个项目
3. 尝试接口调试功能
4. 查看API文档: http://localhost:8000/docs

## 需要帮助？

- 查看完整文档: [README.md](README.md)
- 提交Issue: GitHub Issues
- 查看API文档: http://localhost:8000/docs
