"""添加批量执行相关字段到 test_runs 表，并创建 test_run_details 表"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine, Base
from models import TestRun, TestRunDetail


def migrate():
    """执行迁移"""
    with engine.connect() as conn:
        # 1. 添加新字段到 test_runs 表
        columns_to_add = [
            ("environment_id", "INTEGER"),
            ("concurrency", "INTEGER DEFAULT 1"),
            ("failure_strategy", "VARCHAR(20) DEFAULT 'continue'"),
            ("variables", "JSON"),
            ("celery_task_id", "VARCHAR(200)"),
            ("cancelled", "BOOLEAN DEFAULT FALSE"),
            ("total_count", "INTEGER DEFAULT 0"),
            ("pass_count", "INTEGER DEFAULT 0"),
            ("fail_count", "INTEGER DEFAULT 0"),
            ("error_count", "INTEGER DEFAULT 0"),
            ("creator_id", "INTEGER"),
            ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        ]

        for col_name, col_type in columns_to_add:
            try:
                conn.execute(text(f"ALTER TABLE test_runs ADD COLUMN {col_name} {col_type}"))
                print(f"  ✓ 添加字段: {col_name}")
            except Exception as e:
                if "Duplicate column" in str(e) or "already exists" in str(e):
                    print(f"  - 字段已存在: {col_name}")
                else:
                    print(f"  ✗ 添加字段失败 {col_name}: {e}")

        # 2. 创建 test_run_details 表
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_run_details (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    test_run_id INTEGER NOT NULL,
                    case_id INTEGER NOT NULL,
                    execution_order INTEGER DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'pending',
                    request_snapshot JSON,
                    response_info JSON,
                    assertions JSON,
                    extracted_vars JSON,
                    script_output JSON,
                    error_message TEXT,
                    duration_ms INTEGER DEFAULT 0,
                    started_at DATETIME,
                    finished_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (test_run_id) REFERENCES test_runs(id) ON DELETE CASCADE,
                    FOREIGN KEY (case_id) REFERENCES api_test_cases(id)
                )
            """))
            print("  ✓ 创建表: test_run_details")
        except Exception as e:
            if "already exists" in str(e):
                print("  - 表已存在: test_run_details")
            else:
                print(f"  ✗ 创建表失败: {e}")

        # 3. 将 test_runs.status 和 test_run_details.status 改为 VARCHAR 类型
        try:
            conn.execute(text("ALTER TABLE test_runs MODIFY COLUMN status VARCHAR(20) DEFAULT 'pending'"))
            print("  ✓ 修改 test_runs.status 为 VARCHAR")
        except Exception as e:
            print(f"  ✗ 修改 test_runs.status 失败: {e}")

        try:
            conn.execute(text("ALTER TABLE test_run_details MODIFY COLUMN status VARCHAR(20) DEFAULT 'pending'"))
            print("  ✓ 修改 test_run_details.status 为 VARCHAR")
        except Exception as e:
            print(f"  ✗ 修改 test_run_details.status 失败: {e}")

        # 4. 给已存在的 test_run_details 表添加缺失的字段
        detail_columns_to_add = [
            ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        ]

        for col_name, col_type in detail_columns_to_add:
            try:
                conn.execute(text(f"ALTER TABLE test_run_details ADD COLUMN {col_name} {col_type}"))
                print(f"  ✓ 给 test_run_details 添加字段: {col_name}")
            except Exception as e:
                if "Duplicate column" in str(e) or "already exists" in str(e):
                    print(f"  - 字段已存在: {col_name}")
                else:
                    print(f"  ✗ 添加字段失败 {col_name}: {e}")

        conn.commit()
        print("\n迁移完成!")


if __name__ == "__main__":
    migrate()
