"""添加场景编排执行相关字段"""
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
    """添加字段"""
    with engine.connect() as conn:
        # test_runs 表增加 config_mode
        if not column_exists(conn, "test_runs", "config_mode"):
            conn.execute(text(
                "ALTER TABLE test_runs ADD COLUMN config_mode VARCHAR(20) DEFAULT 'simple'"
            ))
            print("已添加 test_runs.config_mode 字段")
        else:
            print("test_runs.config_mode 字段已存在，跳过")

        # test_run_details 表增加 node_id
        if not column_exists(conn, "test_run_details", "node_id"):
            conn.execute(text(
                "ALTER TABLE test_run_details ADD COLUMN node_id INT NULL"
            ))
            print("已添加 test_run_details.node_id 字段")
        else:
            print("test_run_details.node_id 字段已存在，跳过")

        # test_run_details 表增加 node_type
        if not column_exists(conn, "test_run_details", "node_type"):
            conn.execute(text(
                "ALTER TABLE test_run_details ADD COLUMN node_type VARCHAR(20) DEFAULT 'api_call'"
            ))
            print("已添加 test_run_details.node_type 字段")
        else:
            print("test_run_details.node_type 字段已存在，跳过")

        conn.commit()
        print("迁移完成")


def downgrade():
    """移除字段"""
    with engine.connect() as conn:
        for table, column in [
            ("test_runs", "config_mode"),
            ("test_run_details", "node_id"),
            ("test_run_details", "node_type"),
        ]:
            if column_exists(conn, table, column):
                conn.execute(text(f"ALTER TABLE {table} DROP COLUMN {column}"))
                print(f"已移除 {table}.{column}")
        conn.commit()
        print("回滚完成")


if __name__ == "__main__":
    upgrade()
