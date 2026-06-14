# TestForge 部署指南

## 一键部署（首次使用）

双击运行 `setup.bat`，自动完成所有配置并启动服务。

```
deploy/
├── setup.bat              # 一键部署脚本（首次使用）
├── uninstall.bat          # 一键卸载脚本
├── ecosystem.config.js    # PM2 进程配置文件
├── logs/                  # 日志目录（自动生成）
│   ├── backend-out.log
│   ├── backend-error.log
│   ├── celery-worker-out.log
│   ├── celery-worker-error.log
│   ├── celery-beat-out.log
│   ├── celery-beat-error.log
│   ├── frontend-out.log
│   └── frontend-error.log
└── README.md              # 本文档
```

---

## 服务架构

| 服务 | 说明 | 端口 |
|------|------|------|
| testforge-backend | FastAPI 后端 | :8000 |
| testforge-celery-worker | Celery 异步任务（批量执行） | - |
| testforge-celery-beat | Celery 定时任务调度 | - |
| testforge-frontend | Vue 前端开发服务器 | :5173 |

---

## 常用命令

### 服务管理

```bash
# 启动所有服务（首次或手动停止后）
pm2 start C:\project\TestForge\TestForge\deploy\ecosystem.config.js

# 停止所有服务
pm2 stop all

# 重启所有服务
pm2 restart all

# 重启单个服务
pm2 restart testforge-backend
pm2 restart testforge-celery-worker
pm2 restart testforge-celery-beat
pm2 restart testforge-frontend

# 删除所有服务（彻底移除进程列表）
pm2 delete all
```

### 状态查看

```bash
# 查看服务状态
pm2 status

# 实时监控面板（CPU、内存、日志）
pm2 monit

# 查看某个服务的详细信息
pm2 show testforge-backend
```

### 日志查看

```bash
# 实时查看所有服务日志
pm2 logs

# 只看后端日志
pm2 logs testforge-backend

# 只看 Celery Worker 日志
pm2 logs testforge-celery-worker

# 只看 Celery Beat 日志
pm2 logs testforge-celery-beat

# 只看前端日志
pm2 logs testforge-frontend

# 查看最近 100 行日志
pm2 logs --lines 100

# 清空所有日志
pm2 flush
```

### 进程持久化

```bash
# 保存当前进程列表（重启后可恢复）
pm2 save

# 恢复上次保存的进程列表
pm2 resurrect
```

> **注意**：Windows 上 PM2 不支持 `pm2 startup`，已通过 Windows 任务计划程序实现开机自启（任务名：TestForge-PM2）。

---

## 日志轮转配置（pm2-logrotate）

已安装 `pm2-logrotate` 插件，自动管理日志文件大小。

### 当前配置

| 配置项 | 当前值 | 说明 |
|--------|--------|------|
| max_size | 10MB | 单个日志文件超过 10MB 自动轮转 |
| retain | 7 | 最多保留 7 个历史日志文件 |
| compress | true | 旧日志自动 gzip 压缩 |
| rotateInterval | 0 0 * * * | 每天凌晨检查一次 |
| workerInterval | 30 | 每 30 秒检查一次文件大小 |

### 修改配置

```bash
# 修改单个文件大小上限（例如改为 50MB）
pm2 set pm2-logrotate:max_size 50M

# 修改保留份数（例如保留 14 份）
pm2 set pm2-logrotate:retain 14

# 关闭压缩
pm2 set pm2-logrotate:compress false

# 开启压缩
pm2 set pm2-logrotate:compress true

# 查看当前所有配置
pm2 conf
```

---

## 配置文件说明（ecosystem.config.js）

```javascript
module.exports = {
  apps: [
    {
      name: 'testforge-backend',        // 服务名称
      cwd: '...',                        // 工作目录
      script: '...',                     // 可执行文件路径
      args: '...',                       // 启动参数
      autorestart: true,                 // 崩溃后自动重启
      watch: false,                      // 是否监听文件变化自动重启
      max_restarts: 10,                  // 最大重启次数
      restart_delay: 3000,               // 重启间隔（毫秒）
      error_file: '...',                 // 错误日志路径
      out_file: '...',                   // 输出日志路径
    },
  ],
}
```

### 常用调整

**开启文件监听（开发模式，代码变更自动重启）：**
```javascript
watch: true,
ignore_watch: ['node_modules', 'logs', '*.pyc', '__pycache__'],
```

**调整重启策略：**
```javascript
max_restarts: 30,          // 最多重启 30 次
restart_delay: 5000,       // 每次重启间隔 5 秒
min_uptime: 10000,         // 运行超过 10 秒才算启动成功
max_memory_restart: '500M', // 内存超过 500MB 自动重启
```

修改后需要重新加载配置：
```bash
pm2 restart ecosystem.config.js --update-env
```

---

## Windows 任务计划程序

已创建计划任务 `TestForge-PM2`，实现开机自动恢复 PM2 进程。

```bash
# 查看任务状态
schtasks /query /tn "TestForge-PM2"

# 手动触发（测试用）
schtasks /run /tn "TestForge-PM2"

# 删除任务
schtasks /delete /tn "TestForge-PM2" /f

# 重新创建（在 deploy 目录下执行）
powershell -Command "
$action = New-ScheduledTaskAction -Execute 'C:\Users\Administrator\AppData\Roaming\npm\pm2.cmd' -Argument 'resurrect' -WorkingDirectory 'C:\project\TestForge\TestForge\deploy'
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName 'TestForge-PM2' -Action $action -Trigger $trigger -Settings $settings -User 'SYSTEM' -RunLevel Highest -Force
"
```

---

## 故障排查

### 服务启动失败

```bash
# 查看错误日志
pm2 logs testforge-backend --err --lines 50

# 查看详细信息
pm2 show testforge-backend
```

### 服务反复重启

```bash
# 查看重启次数
pm2 status  # 看 ↻ 列

# 查看最近的错误日志
pm2 logs testforge-backend --err --lines 20
```

### 端口被占用

```bash
# 查看 8000 端口占用
netstat -ano | findstr 8000

# 杀掉占用进程
taskkill /PID <进程ID> /F
```

### PM2 守护进程异常

```bash
# 杀掉 PM2 守护进程
pm2 kill

# 重新启动
pm2 resurrect
```

---

## 完整操作流程

### 首次部署

**一键完成（推荐）：**

```
双击运行 deploy\setup.bat
```

**手动执行：**

```bash
# 1. 安装 PM2
npm install -g pm2

# 2. 安装日志轮转插件
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
pm2 set pm2-logrotate:compress true

# 3. 启动服务
cd C:\project\TestForge\TestForge\deploy
pm2 start ecosystem.config.js

# 4. 保存进程列表
pm2 save
```

### 卸载

```
双击运行 deploy\uninstall.bat
```

### 日常维护

```bash
# 查看状态
pm2 status

# 查看日志
pm2 logs

# 重启服务
pm2 restart all
```

### 更新代码后

```bash
# 重启后端（Python 代码变更）
pm2 restart testforge-backend

# 重启 Celery（任务代码变更）
pm2 restart testforge-celery-worker
pm2 restart testforge-celery-beat

# 前端热更新一般不需要手动重启
# 如果需要重启
pm2 restart testforge-frontend
```
