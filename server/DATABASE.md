# MySQL数据库配置说明

## 数据库连接信息

默认配置使用本地MySQL，请根据实际情况修改：

```
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/testplatform?charset=utf8mb4
```

参数说明：
- `root`: MySQL用户名
- `your_password`: MySQL密码
- `localhost`: MySQL主机地址
- `3306`: MySQL端口
- `testplatform`: 数据库名称

## 创建数据库

在启动项目前，需要先创建数据库：

```sql
CREATE DATABASE testplatform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

或使用命令行：

```bash
mysql -u root -p -e "CREATE DATABASE testplatform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

## 安装依赖

```bash
cd server
pip install -r requirements.txt
```

## 初始化数据库

```bash
python init_db.py
```

## 注意事项

1. 确保MySQL服务正在运行
2. 确保MySQL用户有足够的权限
3. 数据库字符集必须是utf8mb4
4. 如果遇到连接问题，检查MySQL的bind-address配置
