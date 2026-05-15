"""重置数据库 - 删除并重建所有表"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from core.config import settings
from database import Base, engine

# 导入所有模型以确保 Base.metadata 包含所有表
from models import *


def reset_database():
    print("警告: 此操作将删除所有数据并重建数据库!")
    confirm = input("确认执行? (输入 yes 继续): ")
    if confirm.lower() != "yes":
        print("已取消")
        return

    print("删除所有表...")
    Base.metadata.drop_all(bind=engine)
    print("所有表已删除")

    print("重新创建所有表...")
    Base.metadata.create_all(bind=engine)
    print("所有表已创建成功")

    # 重新初始化管理员和角色
    from core.auth import init_roles
    from core.security import get_password_hash
    from models import User, Role
    from database import SessionLocal

    db = SessionLocal()
    try:
        init_roles(db)

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

        print("管理员用户已创建")
        print(f"账号: admin")
        print(f"密码: {settings.FIRST_SUPERUSER_PASSWORD}")
    finally:
        db.close()

    print("数据库重置完成!")


if __name__ == "__main__":
    reset_database()
