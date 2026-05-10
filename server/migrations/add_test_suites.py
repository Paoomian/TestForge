"""创建 test_suites 表"""
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
                CREATE TABLE IF NOT EXISTS test_suites (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    project_id INTEGER NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    case_ids JSON,
                    environment_id INTEGER,
                    concurrency INTEGER DEFAULT 1,
                    failure_strategy VARCHAR(20) DEFAULT 'continue',
                    variables JSON,
                    tags JSON,
                    creator_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (environment_id) REFERENCES environments(id),
                    FOREIGN KEY (creator_id) REFERENCES users(id)
                )
            """))
            print("  ✓ 创建表: test_suites")
        except Exception as e:
            if "already exists" in str(e):
                print("  - 表已存在: test_suites")
            else:
                print(f"  ✗ 创建表失败: {e}")

        conn.commit()
        print("\n迁移完成!")


if __name__ == "__main__":
    migrate()
