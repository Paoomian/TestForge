"""
迁移脚本: 移除用例历史表和版本字段
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine


def upgrade():
    """移除历史表和版本字段"""
    with engine.connect() as conn:
        # 删除历史表
        conn.execute(text("DROP TABLE IF EXISTS api_test_case_histories"))
        print("已删除 api_test_case_histories 表")

        # 移除 version 字段
        result = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_name = 'api_test_cases'
            AND column_name = 'version'
        """))
        if result.scalar() > 0:
            conn.execute(text("ALTER TABLE api_test_cases DROP COLUMN version"))
            print("已移除 version 字段")
        else:
            print("version 字段不存在，跳过")

        conn.commit()


if __name__ == "__main__":
    upgrade()
