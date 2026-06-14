import re
from urllib.parse import urlparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from core.auth import init_roles, create_user
from core.security import get_password_hash
from models import User, Role
from schemas.auth import UserCreate
from database import SessionLocal, engine, Base
from core.config import settings


def ensure_database_exists():
    """确保数据库存在，不存在则自动创建"""
    # 从 DATABASE_URL 解析连接信息
    # 格式: mysql+pymysql://user:password@host:port/dbname?charset=utf8mb4
    url = settings.DATABASE_URL

    # 提取数据库名（去掉查询参数）
    # 先去掉 mysql+pymysql:// 前缀
    db_name = url.split("/")[-1].split("?")[0]

    # 构建连接到 MySQL 服务器的 URL（不指定数据库）
    # 用正则提取 user:password@host:port 部分
    match = re.search(r"mysql\+pymysql://([^@]+)@([^/]+)/", url)
    if not match:
        print(f"无法解析数据库 URL: {url}")
        return

    credentials = match.group(1)  # user:password
    host_port = match.group(2)    # host:port

    server_url = f"mysql+pymysql://{credentials}@{host_port}/"

    # 连接到 MySQL 服务器并创建数据库
    server_engine = create_engine(server_url)
    try:
        with server_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            conn.commit()
            print(f"数据库 '{db_name}' 已就绪")
    except Exception as e:
        print(f"创建数据库失败: {e}")
        raise
    finally:
        server_engine.dispose()


def init_db():
    ensure_database_exists()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        init_roles(db)

        admin_user = db.query(User).filter(User.email == settings.FIRST_SUPERUSER_EMAIL).first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email=settings.FIRST_SUPERUSER_EMAIL,
                password_hash=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                is_superuser=True,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            admin_role = db.query(Role).filter(Role.name == "admin").first()
            if admin_role:
                admin_user.roles.append(admin_role)
                db.commit()

            print("Admin user created successfully")
            print(f"Email: {settings.FIRST_SUPERUSER_EMAIL}")
            print(f"Password: {settings.FIRST_SUPERUSER_PASSWORD}")
        else:
            print("Admin user already exists")

    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")
