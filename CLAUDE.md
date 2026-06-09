# TestForge 测试平台

## 项目概述

集UI自动化、接口自动化和接口调试于一体的现代化测试平台。

**技术栈**:

- 后端: FastAPI + SQLAlchemy + MySQL 8.0 + Redis + Celery
- 前端: Vue 3 + TypeScript + Arco Design Vue + Pinia
- 认证: JWT双Token (Access Token 30min + Refresh Token 7天)
- 权限: RBAC (基于角色的访问控制)

## 启动步骤

### 后端

```bash
cd server
python -m pip install -r requirements_core.txt
python -m pip install email-validator "bcrypt<4.0.0"
python init_db.py  # 仅首次（全新安装）
python migrations/upgrade_all.py  # 升级已有数据库（合并所有迁移，可重复执行）

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

**默认账号**: admin / admin123

## 重要技术细节

### 1. 导入方式

**所有Python文件使用绝对导入**，不使用相对导入（支持直接运行脚本）。

```python
# ✅ 正确
from models import User
from core.config import settings

# ❌ 错误
from ..models import User
from .config import settings
```

### 2. JWT Token

`sub`字段必须是字符串: `{"sub": str(user.id)}`

### 3. bcrypt版本

使用 `bcrypt<4.0.0` 以兼容 `passlib`。

### 4. 双Token刷新机制

- 前端请求拦截器自动注入Token
- 401时自动用refresh_token刷新access_token
- 并发请求通过队列机制避免重复刷新

## 开发规范

### 沟通规范

- **语言**: 所有对话、思考过程、代码注释均使用中文
- **代码注释**: 关键逻辑处添加简洁的中文注释，不写废话注释

### 代码风格

- **Python**: 遵循PEP 8，使用类型提示
- **TypeScript**: 使用严格模式，明确类型定义
- **Vue**: 使用 Composition API + `<script setup>`

### 数据库规范

**涉及数据库字段、表结构的改动，必须同步更新数据库升级脚本**：

- 新增表：在 `server/migrations/upgrade_all.py` 中添加 `ensure_xxx` 函数
- 新增字段：在对应的 `upgrade_xxx_columns` 函数中添加 `safe_add_column` 调用
- 修改字段：在升级脚本中添加兼容性处理（检查后再修改）

升级脚本要求：
- 可重复执行，不会产生副作用
- 使用 `table_exists` / `column_exists` 检查后再操作
- 添加清晰的中文注释说明每步操作

### Celery 任务规范

**新增 Celery 任务必须注册到 `celery_app.py`**：

```python
# server/celery_app.py
celery_app.conf.include = [
    "tasks.batch_run_task",
    "tasks.scene_run_task",
    "tasks.ai_generate_tasks",
    "tasks.ui_batch_run_task",  # 新增任务
]
```

任务文件规范：
- 任务文件放在 `server/tasks/` 目录下
- 使用 `@celery_app.task(bind=True, name="tasks.xxx")` 装饰器
- 任务内部使用 `asyncio.run()` 执行异步代码

### UI 设计规范

**风格**: 淡蓝紫低饱和渐变、清新科技感。详细规范见 `frontend/UI_STYLE_GUIDE.md`。

核心规则：

- 使用 CSS 变量（`--primary-*`, `--radius-*`, `--space-*`），禁止硬编码颜色值
- 颜色用 Arco 内置色板（blue, green, orange, red, purple, gray）
- 卡片左彩边 + hover 阴影：`border-left: 4px solid` + `box-shadow`
- 表单垂直布局 `layout="vertical"`，标签宽 `80px`
- 所有状态变化加 `transition: all 0.2s ease`
- UI 文案使用中文

### 进度管理

**每次完成功能开发后，自动更新 `docs/progress.md`**：

- 每完成一个功能，更新进度清单（打勾、补充说明）
- 每遇到重要的技术决策，记录决策内容和原因
- 记录当前阻塞点和待办事项
- 格式保持简洁，用 checkbox 列表

示例格式：

```markdown
## 已完成功能

### 接口自动化
- [x] 接口调试（单接口调试）
- [x] 接口用例管理（CRUD）
- [x] 接口自动化执行（单用例调试执行）
- [x] 接口自动化批量执行（含进度跟踪）
- [x] 用例场景编排（条件/循环/变量）
- [x] 测试报告生成（统计/性能/失败分析）
- [x] 任务配置（可保存、反复执行）

### UI自动化
- [x] UI用例录制（Playwright录制）
- [x] UI用例管理（CRUD）
- [x] UI用例单个执行
- [x] UI用例批量执行（含实时截图）
- [x] UI任务配置（可保存、反复执行）
- [x] 批量任务列表和详情

### 通用功能
- [x] 仪表盘（统计/趋势/通过率）
- [x] 项目管理
- [x] 环境管理
- [x] Monkey稳定性测试
- [x] AI生成用例
- [x] 工具箱（JSON/时间戳/编解码等）

## 待开发功能

- [ ] 定时任务调度 (Celery Beat)
- [ ] CI/CD集成
- [ ] 测试数据管理
- [ ] Mock服务
- [ ] 性能测试
- [ ] 接口自动化录制 (mitmproxy)

## 故障排查

### 后端无法启动

1. 检查MySQL服务: `sc query MySQL80`
2. 检查数据库配置: `server/.env`
3. 检查端口占用: `netstat -ano | findstr 8000`

### 前端无法访问后端

1. 检查后端健康: `curl http://localhost:8000/health`
2. 检查CORS配置和前端代理配置

---

**最后更新**: 2026-06-09（新增UI自动化批量执行、任务配置、Celery任务规范）
```
