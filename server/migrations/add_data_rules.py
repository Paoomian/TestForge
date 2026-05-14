"""创建 test_case_data_rules 表"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine


def migrate():
    """执行迁移"""
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_case_data_rules (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    test_case_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    rule_type VARCHAR(30) NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    description VARCHAR(500),
                    default_value TEXT,
                    sort_order INTEGER DEFAULT 0,
                    source VARCHAR(30),
                    expression VARCHAR(1000),
                    static_value TEXT,
                    generator VARCHAR(30),
                    generator_params JSON,
                    source_variable VARCHAR(100),
                    transform_type VARCHAR(30),
                    transform_params JSON,
                    condition_variable VARCHAR(100),
                    condition_operator VARCHAR(20),
                    condition_value VARCHAR(500),
                    true_value VARCHAR(1000),
                    false_value VARCHAR(1000),
                    FOREIGN KEY (test_case_id) REFERENCES api_test_cases(id) ON DELETE CASCADE
                )
            """))
            print("  ✓ 创建表: test_case_data_rules")
        except Exception as e:
            if "already exists" in str(e):
                print("  - 表已存在: test_case_data_rules")
            else:
                print(f"  ✗ 创建表失败: {e}")

        conn.commit()
        print("\n迁移完成!")


if __name__ == "__main__":
    migrate()
