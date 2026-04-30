# 测试平台 - MySQL版本启动指南

## 前置准备

✅ 你的系统已安装：
- MySQL 8.0.43（已运行在端口3306）
- Python 3.11+
- Node.js 20+

## 快速启动步骤

### 1. 创建MySQL数据库

```bash
# 方式一：使用MySQL命令行
mysql -u root -p

# 在MySQL中执行
CREATE DATABASE testplatform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit;

# 方式二：使用SQL文件
mysql -u root -p < server/create_database.sql
```

### 2. 配置数据库连接

编辑 `server/.env` 文件，修改数据库连接信息：

```env
DATABASE_URL=mysql+pymysql://root:你的MySQL密码@localhost:3306/testplatform?charset=utf8mb4
```

**重要**：将 `你的MySQL密码` 替换为你的实际MySQL root密码

### 3. 安装后端依赖

```bash
cd server

# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium
```

### 4. 初始化数据库

```bash
# 在server目录下执行
python init_db.py
```

你会看到类似输出：
```
Initializing database...
Admin user created successfully
Email: admin@example.com
Password: admin123
Database initialized successfully!
```

### 5. 启动后端服务

```bash
# 在server目录下执行
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端将运行在: http://localhost:8000

### 6. 启动前端（新终端）

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在: http://localhost:5173

### 7. 登录系统

访问 http://localhost:5173，使用默认账号：
- 用户名: `admin`
- 密码: `admin123`

## 验证安装

1. ✅ MySQL服务运行: `sc query MySQL80`
2. ✅ 数据库已创建: `mysql -u root -p -e "SHOW DATABASES LIKE 'testplatform';"`
3. ✅ 后端健康检查: http://localhost:8000/health
4. ✅ API文档: http://localhost:8000/docs
5. ✅ 前端访问: http://localhost:5173

## 常见问题

### 问题1: 数据库连接失败

**错误**: `Can't connect to MySQL server`

**解决**:
1. 确认MySQL服务运行: `sc query MySQL80`
2. 检查端口占用: `netstat -ano | grep 3306`
3. 验证密码是否正确
4. 检查 `.env` 文件中的 `DATABASE_URL` 配置

### 问题2: pymysql安装失败

**错误**: `error: Microsoft Visual C++ 14.0 or greater is required`

**解决**:
```bash
# 使用纯Python实现的pymysql（推荐）
pip install pymysql cryptography
```

### 问题3: 数据库字符集问题

**错误**: `Incorrect string value`

**解决**: 确保数据库使用utf8mb4字符集
```sql
ALTER DATABASE testplatform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 问题4: 表已存在

**错误**: `Table 'users' already exists`

**解决**: 数据库已初始化，直接启动服务即可

## 项目结构

```
testing-platform/
├── server/                 # 后端（FastAPI + MySQL）
│   ├── .env               # 数据库配置（需修改密码）
│   ├── create_database.sql # 数据库创建脚本
│   ├── init_db.py         # 数据库初始化
│   └── requirements.txt   # Python依赖（已改为pymysql）
├── frontend/              # 前端（Vue3）
└── docker-compose.yml     # Docker配置（已改为MySQL）
```

## 数据库配置说明

### 本地MySQL配置
```env
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/testplatform?charset=utf8mb4
```

### Docker MySQL配置
```env
DATABASE_URL=mysql+pymysql://testplatform:testplatform123@mysql:3306/testplatform?charset=utf8mb4
```

## 下一步

1. ✅ 登录系统
2. ✅ 创建第一个项目
3. ✅ 尝试接口调试功能
4. ⏳ 开发UI自动化录制
5. ⏳ 开发接口自动化执行

## 技术栈变更

- ❌ PostgreSQL → ✅ MySQL 8.0
- ❌ psycopg2 → ✅ pymysql
- ✅ 其他技术栈保持不变

## 需要帮助？

- 查看项目文档: [CLAUDE.md](CLAUDE.md)
- 查看完整文档: [README.md](README.md)
- API文档: http://localhost:8000/docs
