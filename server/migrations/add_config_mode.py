"""添加 test_suites.config_mode 字段"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from database import engine


def column_exists(conn, table_name, column_name):
    """检查列是否存在"""
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    """添加 config_mode 字段"""
    with engine.connect() as conn:
        if not column_exists(conn, "test_suites", "config_mode"):
            conn.execute(text(
                "ALTER TABLE test_suites ADD COLUMN config_mode VARCHAR(20) DEFAULT 'simple'"
            ))
            conn.commit()
            print("已添加 config_mode 字段")
        else:
            print("config_mode 字段已存在，跳过")


def downgrade():
    """移除 config_mode 字段"""
    with engine.connect() as conn:
        if column_exists(conn, "test_suites", "config_mode"):
            conn.execute(text("ALTER TABLE test_suites DROP COLUMN config_mode"))
            conn.commit()
            print("已移除 config_mode 字段")
        else:
            print("config_mode 字段不存在，跳过")


if __name__ == "__main__":
    upgrade()
