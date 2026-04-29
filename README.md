# 测试平台

一个集UI自动化、接口自动化和接口调试于一体的现代化测试平台。

## 功能特性

- 🎯 **UI自动化测试**
  - 基于Playwright的UI自动化录制
  - 智能元素定位
  - 可视化用例编排
  - 支持多浏览器执行

- 🔌 **接口自动化测试**
  - 接口用例管理
  - 支持代理录制
  - 参数化与数据驱动
  - 断言与变量提取

- 🐛 **接口调试工具**
  - 类Postman的接口调试
  - 支持多种请求方式
  - 环境变量管理
  - 请求历史记录

- 📊 **测试报告**
  - 详细的测试报告
  - 数据统计与分析
  - 执行日志查看

## 技术栈

### 后端
- FastAPI - 高性能Web框架
- SQLAlchemy - ORM
- MySQL 8.0 - 数据库
- Redis - 缓存
- Celery - 异步任务
- Playwright - UI自动化
- httpx - HTTP客户端

### 前端
- Vue 3 - 前端框架
- TypeScript - 类型支持
- Arco Design Vue - UI组件库
- Pinia - 状态管理
- Vue Router - 路由管理
- Axios - HTTP客户端

## 快速开始

### 使用Docker Compose（推荐）

1. 克隆项目
```bash
git clone <repository-url>
cd testing-platform
```

2. 复制环境变量文件
```bash
cp server/.env.example server/.env
```

3. 启动服务
```bash
docker-compose up -d
```

4. 访问应用
- 前端: http://localhost:5173
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 本地开发

#### 后端

1. 创建MySQL数据库
```bash
mysql -u root -p -e "CREATE DATABASE testplatform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

2. 安装依赖
```bash
cd server
pip install -r requirements.txt
playwright install chromium
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置MySQL连接信息
# DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/testplatform?charset=utf8mb4
```

4. 初始化数据库
```bash
python init_db.py
```

5. 启动服务
```bash
uvicorn main:app --reload
```

#### 前端

1. 安装依赖
```bash
cd frontend
npm install
```

2. 启动开发服务器
```bash
npm run dev
```

## 默认账号

首次启动后，系统会自动创建管理员账号：
- 用户名: admin
- 密码: admin123

**请在生产环境中修改默认密码！**

## 项目结构

```
testing-platform/
├── server/                 # 后端代码
│   ├── api/               # API路由
│   ├── core/              # 核心功能
│   ├── models/            # 数据模型
│   ├── schemas/           # Pydantic模型
│   ├── tasks/             # Celery任务
│   └── main.py            # 入口文件
├── frontend/              # 前端代码
│   ├── src/
│   │   ├── api/          # API封装
│   │   ├── components/   # 组件
│   │   ├── layouts/      # 布局
│   │   ├── router/       # 路由
│   │   ├── stores/       # 状态管理
│   │   ├── types/        # 类型定义
│   │   ├── utils/        # 工具函数
│   │   └── views/        # 页面
│   └── package.json
└── docker-compose.yml     # Docker编排
```

## 开发计划

- [x] 用户认证与权限管理
- [x] 项目管理
- [x] 接口调试功能
- [ ] UI自动化录制
- [ ] UI自动化执行
- [ ] 接口自动化录制
- [ ] 接口自动化执行
- [ ] 测试报告生成
- [ ] 定时任务调度
- [ ] CI/CD集成

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License
