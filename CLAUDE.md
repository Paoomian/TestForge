# 测试平台项目文档

## 项目概述

一个集UI自动化、接口自动化和接口调试于一体的现代化测试平台。

**技术栈**:
- 后端: FastAPI + SQLAlchemy + MySQL 8.0 + Redis
- 前端: Vue 3 + TypeScript + Arco Design Vue + Pinia
- 认证: JWT (Access Token + Refresh Token)
- 权限: RBAC (基于角色的访问控制)

## 项目结构

```
testing-platform/
├── server/                 # 后端 (FastAPI)
│   ├── api/               # API路由
│   │   ├── auth.py        # 认证接口 (登录/注册/获取用户信息)
│   │   ├── projects.py    # 项目管理
│   │   ├── api_cases.py   # 接口用例和调试
│   │   └── ui_cases.py    # UI用例
│   ├── core/              # 核心功能
│   │   ├── config.py      # 配置管理 (Pydantic Settings)
│   │   ├── security.py    # JWT token生成和密码哈希
│   │   ├── auth.py        # 认证逻辑 (登录/注册/角色初始化)
│   │   └── deps.py        # 依赖注入 (获取当前用户/权限检查)
│   ├── models/            # 数据模型 (SQLAlchemy)
│   │   ├── user.py        # 用户模型
│   │   ├── role.py        # 角色模型
│   │   ├── user_role.py   # 用户-角色关联表
│   │   ├── project.py     # 项目模型
│   │   ├── api_case.py    # 接口用例模型
│   │   ├── ui_case.py     # UI用例模型
│   │   ├── environment.py # 环境变量模型
│   │   └── test_run.py    # 测试运行记录模型
│   ├── schemas/           # Pydantic模型 (请求/响应)
│   │   ├── auth.py        # 认证相关schema
│   │   ├── project.py     # 项目相关schema
│   │   └── api_case.py    # 接口用例相关schema
│   ├── alembic/           # 数据库迁移
│   │   └── versions/
│   │       └── 001_init_database.py  # 初始化数据库表
│   ├── database.py        # 数据库连接配置
│   ├── main.py            # FastAPI应用入口
│   ├── init_db.py         # 数据库初始化脚本
│   ├── .env               # 环境变量配置
│   ├── requirements.txt   # Python依赖 (完整版，包含mitmproxy)
│   └── requirements_core.txt  # 核心依赖 (不含mitmproxy，用于Python 3.13)
├── frontend/              # 前端 (Vue 3)
│   ├── src/
│   │   ├── api/          # API封装
│   │   │   └── auth.ts   # 认证API
│   │   ├── components/   # 公共组件
│   │   ├── layouts/      # 布局组件
│   │   │   └── MainLayout.vue  # 主布局 (侧边栏+顶栏)
│   │   ├── router/       # 路由配置
│   │   │   └── index.ts  # 路由定义和导航守卫
│   │   ├── stores/       # 状态管理 (Pinia)
│   │   │   └── user.ts   # 用户状态 (token/userInfo)
│   │   ├── types/        # TypeScript类型定义
│   │   │   └── auth.ts   # 认证相关类型
│   │   ├── utils/        # 工具函数
│   │   │   └── request.ts  # Axios封装 (拦截器/错误处理)
│   │   ├── views/        # 页面组件
│   │   │   ├── Login.vue      # 登录页面
│   │   │   ├── Dashboard.vue  # 仪表盘
│   │   │   └── api-debug/
│   │   │       └── Index.vue  # 接口调试页面
│   │   ├── App.vue       # 根组件
│   │   └── main.ts       # 应用入口
│   ├── package.json      # 前端依赖
│   └── vite.config.ts    # Vite配置 (代理/插件)
├── docker-compose.yml    # Docker编排 (MySQL + Redis + Backend + Frontend)
├── README.md             # 项目说明
├── SETUP_MYSQL.md        # MySQL版本启动指南
└── CLAUDE.md             # 本文件 - 项目上下文文档

```

## 环境配置

### 数据库配置 (server/.env)

```env
# Database
DATABASE_URL=mysql+pymysql://root:zzh000801@localhost:3306/testplatform?charset=utf8mb4

# Security
SECRET_KEY=your-secret-key-change-this-in-production-please-use-a-strong-random-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Admin User
FIRST_SUPERUSER_EMAIL=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin123
```

### MySQL配置

- **数据库名**: `testplatform`
- **字符集**: `utf8mb4`
- **排序规则**: `utf8mb4_unicode_ci`
- **Root密码**: `zzh000801`
- **MySQL配置文件**: `D:/DataBase/my.ini`
- **数据目录**: `D:/DataBase/Data`

## 启动步骤

### 1. 后端启动

```bash
cd server

# 使用Python 3.11 (推荐) 或 3.13
py -3.11 -m pip install -r requirements_core.txt
py -3.11 -m pip install email-validator
py -3.11 -m pip install "bcrypt<4.0.0"

# 初始化数据库 (仅首次)
py -3.11 init_db.py

# 启动后端服务
py -3.11 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**后端地址**:
- API: http://localhost:8000
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 2. 前端启动

```bash
cd frontend

# 安装依赖 (仅首次)
npm install

# 启动开发服务器
npm run dev
```

**前端地址**: http://localhost:5173

## 默认账号

- **用户名**: `admin`
- **密码**: `admin123`
- **邮箱**: `admin@example.com`
- **角色**: 超级管理员

## 重要技术细节

### 1. 导入方式

**所有Python文件使用绝对导入，不使用相对导入**。

❌ 错误示例:
```python
from ..models import User
from .config import settings
```

✅ 正确示例:
```python
from models import User
from core.config import settings
```

**原因**: 项目需要支持直接运行脚本 (如 `python init_db.py`)，相对导入会导致 `ImportError: attempted relative import with no known parent package`。

### 2. JWT Token格式

**重要**: JWT的`sub`字段必须是字符串类型，不能是整数。

```python
# 生成token时
access_token = create_access_token(data={"sub": str(user.id)})  # ✅ 正确

# 验证token时
payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
user_id = int(payload["sub"])  # 转回整数查询数据库
```

**TokenPayload定义**:
```python
class TokenPayload(BaseModel):
    sub: Optional[str] = None  # 必须是字符串
    type: Optional[str] = None
```

### 3. bcrypt版本兼容性

使用 `bcrypt<4.0.0` 以兼容 `passlib`。

```bash
pip install "bcrypt<4.0.0"
```

### 4. 前端请求拦截器

**Token自动注入** (frontend/src/utils/request.ts):
```typescript
service.interceptors.request.use((config) => {
  const userStore = useUserStore()
  if (userStore.token) {
    config.headers.Authorization = `Bearer ${userStore.token}`
  }
  return config
})
```

**401自动跳转登录**:
```typescript
service.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      router.push('/login')
      Message.error('登录已过期，请重新登录')
    }
    return Promise.reject(error)
  }
)
```

### 5. 路由守卫

**前端路由守卫** (frontend/src/router/index.ts):
```typescript
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.token) {
    next('/login')
  } else if (to.path === '/login' && userStore.token) {
    next('/')
  } else {
    next()
  }
})
```

### 6. RBAC权限系统

**默认角色**:
- `admin`: 管理员，拥有所有权限 (`["*"]`)
- `tester`: 测试人员，拥有测试执行权限
- `viewer`: 查看者，只读权限 (`["*:read"]`)

**权限检查** (backend):
```python
from core.deps import check_permission

@router.post("/debug")
async def debug_api(
    request: APIDebugRequest,
    current_user: User = Depends(check_permission("debug:use"))
):
    # 只有拥有 debug:use 权限的用户才能访问
    pass
```

## 已知问题和解决方案

### 问题1: 接口调试页面输入URL后仍提示"请输入请求URL"

**原因**: 模板中使用了不存在的 `request` 对象，实际定义的是 `requestData`。

**解决**: 已修复所有 `v-model` 绑定为 `requestData`。

### 问题2: 登录成功但获取用户信息返回401

**原因**: JWT的`sub`字段使用了整数，但JWT标准要求必须是字符串。

**解决**: 
- 生成token时将 `user.id` 转为字符串: `str(user.id)`
- 验证token时将字符串转回整数: `int(token_data.sub)`

### 问题3: Python 3.13安装mitmproxy失败

**原因**: mitmproxy依赖的msgpack需要编译，Python 3.13太新，某些包不兼容。

**解决**: 
- 使用Python 3.11 (推荐)
- 或使用 `requirements_core.txt` (不含mitmproxy)

### 问题4: MySQL密码重置

**步骤**:
1. 停止MySQL服务: `net stop MySQL80`
2. 安全模式启动: `mysqld --defaults-file=D:\DataBase\my.ini --skip-grant-tables --shared-memory --console`
3. 连接并重置: `mysql -u root` → `FLUSH PRIVILEGES; ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_password';`
4. 重启服务: `net start MySQL80`

## API接口文档

### 认证接口

#### POST /api/v1/auth/login
登录接口

**请求**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

#### GET /api/v1/auth/me
获取当前用户信息 (需要认证)

**Headers**:
```
Authorization: Bearer <access_token>
```

**响应**:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_active": true,
  "is_superuser": true,
  "avatar": null
}
```

#### POST /api/v1/auth/register
注册新用户

**请求**:
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}
```

### 接口调试

#### POST /api/v1/api-cases/debug
发送HTTP请求进行调试 (需要 `debug:use` 权限)

**请求**:
```json
{
  "method": "GET",
  "url": "https://api.example.com/users",
  "headers": {"Authorization": "Bearer token"},
  "query_params": {"page": "1"},
  "body": "",
  "body_type": "json"
}
```

**响应**:
```json
{
  "status_code": 200,
  "headers": {"content-type": "application/json"},
  "body": "{\"users\": []}",
  "elapsed": 0.234
}
```

## 开发规范

### 1. 代码风格

- **Python**: 遵循PEP 8，使用类型提示
- **TypeScript**: 使用严格模式，明确类型定义
- **Vue**: 使用 Composition API + `<script setup>`

### 2. 提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具链相关
```

### 3. 分支管理

- `main`: 主分支，稳定版本
- `develop`: 开发分支
- `feature/*`: 功能分支
- `fix/*`: 修复分支

## 待开发功能

- [ ] UI自动化录制
- [ ] UI自动化执行
- [ ] 接口自动化录制 (使用mitmproxy)
- [ ] 接口自动化执行
- [ ] 测试报告生成
- [ ] 定时任务调度 (Celery)
- [ ] CI/CD集成
- [ ] 测试数据管理
- [ ] Mock服务
- [ ] 性能测试

## 故障排查

### 后端无法启动

1. 检查MySQL服务是否运行: `sc query MySQL80`
2. 检查数据库连接配置: `server/.env` 中的 `DATABASE_URL`
3. 检查端口占用: `netstat -ano | findstr 8000`
4. 查看错误日志

### 前端无法访问后端

1. 检查后端是否启动: `curl http://localhost:8000/health`
2. 检查CORS配置: `server/.env` 中的 `BACKEND_CORS_ORIGINS`
3. 检查前端代理配置: `frontend/vite.config.ts`
4. 打开浏览器开发者工具查看网络请求

### 登录失败

1. 确认用户名密码正确: `admin` / `admin123`
2. 检查数据库中是否有用户: `SELECT * FROM users WHERE username='admin';`
3. 重新初始化数据库: `py -3.11 init_db.py`

## 联系方式

如有问题，请查看:
- API文档: http://localhost:8000/docs
- GitHub Issues: (待添加)
- 项目文档: 本文件

---

**最后更新**: 2026-04-29
**维护者**: Claude + 用户
