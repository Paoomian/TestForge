"""为 api_test_cases 表添加 environment_id 列"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from database import engine


def migrate():
    with engine.connect() as conn:
        # 检查列是否已存在
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("api_test_cases")]
        if "environment_id" in columns:
            print("environment_id 列已存在，跳过")
            return

        conn.execute(text("ALTER TABLE api_test_cases ADD COLUMN environment_id INTEGER NULL"))
        conn.commit()
    print("api_test_cases 表添加 environment_id 列成功")


if __name__ == "__main__":
    migrate()
