"""添加 api_test_cases 表索引优化查询性能"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine


def index_exists(conn, table_name, index_name):
    """检查索引是否存在"""
    result = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.statistics "
        "WHERE table_schema = DATABASE() AND table_name = :table AND index_name = :index"
    ), {"table": table_name, "index": index_name})
    return result.scalar() > 0


def upgrade():
    """添加索引"""
    indexes = [
        ("idx_case_project_module", "api_test_cases", "(project_id, module)"),
        ("idx_case_project_id", "api_test_cases", "(project_id)"),
        ("idx_case_module", "api_test_cases", "(module)"),
    ]

    with engine.connect() as conn:
        for idx_name, table, cols in indexes:
            if not index_exists(conn, table, idx_name):
                conn.execute(text(f"CREATE INDEX {idx_name} ON {table} {cols}"))
                print(f"已创建索引: {idx_name}")
            else:
                print(f"索引已存在，跳过: {idx_name}")

        conn.commit()
        print("索引添加完成")


def downgrade():
    """移除索引"""
    with engine.connect() as conn:
        for idx_name in ["idx_case_project_module", "idx_case_project_id", "idx_case_module"]:
            if index_exists(conn, "api_test_cases", idx_name):
                conn.execute(text(f"DROP INDEX {idx_name} ON api_test_cases"))
                print(f"已移除索引: {idx_name}")
        conn.commit()
        print("索引移除完成")


if __name__ == "__main__":
    upgrade()
