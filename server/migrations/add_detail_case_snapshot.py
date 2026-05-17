"""迁移：为 test_run_details 表添加用例快照字段，并回填已有数据"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine


def migrate():
    with engine.begin() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("SHOW COLUMNS FROM test_run_details LIKE 'case_name'"))
        if result.fetchone():
            print("字段 case_name 已存在，跳过")
            return

        # 添加快照字段
        conn.execute(text("ALTER TABLE test_run_details ADD COLUMN case_name VARCHAR(200) NULL"))
        conn.execute(text("ALTER TABLE test_run_details ADD COLUMN case_number VARCHAR(50) NULL"))
        print("已添加 case_name, case_number 字段")

        # 回填已有数据：从 api_test_cases 表获取用例信息
        conn.execute(text("""
            UPDATE test_run_details d
            JOIN api_test_cases c ON d.case_id = c.id
            SET d.case_name = c.name, d.case_number = c.case_number
            WHERE d.case_id IS NOT NULL
        """))
        print("已回填已有数据的快照字段")


if __name__ == "__main__":
    migrate()
    print("迁移完成")
