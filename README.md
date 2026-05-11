# TestForge 测试平台

集UI自动化、接口自动化和接口调试于一体的现代化测试平台。

## 功能特性

- 🔌 **接口自动化测试**
  - 接口用例管理（模块化组织、用例编号）
  - 单用例调试执行
  - 批量执行（并发控制、失败策略）
  - 任务配置（测试套件）
  - 断言与变量提取
  - 脚本执行（Pre/Post Script）

- 🐛 **接口调试工具**
  - 类Postman的接口调试
  - 支持多种请求方式
  - 环境变量管理
  - cURL导入

- 📊 **测试报告**
  - 测试摘要（通过率、统计）
  - 性能统计（P50/P90/P95、Top5）
  - 失败分析（分类统计、断言详情）

- 🎯 **UI自动化测试**（待开发）
  - 基于Playwright的UI自动化录制
  - 智能元素定位
  - 可视化用例编排

## 技术栈

### 后端
- FastAPI - 高性能Web框架
- SQLAlchemy - ORM
- MySQL 8.0 - 数据库
- Redis - 缓存
- Celery - 异步任务
- httpx - HTTP客户端

### 前端
- Vue 3 + TypeScript
- Arco Design Vue - UI组件库
- Pinia - 状态管理
- ECharts - 图表

## 快速开始

### 后端

```bash
cd server
python -m pip install -r requirements_core.txt
python -m pip install email-validator "bcrypt<4.0.0"
python init_db.py  # 仅首次
python migrations/add_batch_run_fields.py  # 升级已有数据库（首次升级时）

# 终端1：启动 FastAPI
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 终端2：启动 Celery Worker（批量执行功能需要）
celery -A celery_app worker --loglevel=info
```

### 前端

```bash
cd frontend
npm install  # 仅首次
npm run dev
```

### 默认账号

- 用户名: admin
- 密码: admin123

## 项目结构

```
TestForge/
├── server/                     # 后端代码
│   ├── api/                   # API路由
│   ├── core/                  # 核心功能（配置、依赖注入）
│   ├── models/                # 数据模型
│   ├── schemas/               # Pydantic模型
│   ├── services/              # 业务服务（执行引擎）
│   ├── tasks/                 # Celery任务
│   ├── migrations/            # 数据库迁移脚本
│   └── main.py                # 入口文件
├── frontend/                  # 前端代码
│   ├── src/
│   │   ├── api/              # API封装
│   │   ├── components/       # 通用组件
│   │   ├── layouts/          # 布局
│   │   ├── router/           # 路由
│   │   ├── stores/           # 状态管理
│   │   └── views/            # 页面
│   └── package.json
└── docs/                      # 文档
    └── progress.md            # 开发进度
```

## 开发进度

- [x] 用户认证与权限管理（JWT双Token + RBAC）
- [x] 项目管理
- [x] 环境管理
- [x] 接口调试功能
- [x] 用例管理（模块化、子表设计）
- [x] 单用例调试执行
- [x] 批量执行（Celery异步、并发控制）
- [x] 任务配置（测试套件）
- [x] 测试报告（摘要、性能、失败分析）
- [ ] UI自动化录制与执行
- [ ] 定时任务调度
- [ ] CI/CD集成

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License
