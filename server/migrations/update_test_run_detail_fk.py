"""
迁移脚本：修改 test_run_details 表的外键约束
允许删除用例时将 case_id 设为 NULL，而不是阻止删除
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine


def upgrade():
    """修改外键约束"""
    with engine.connect() as conn:
        # 1. 先删除原有的外键约束
        conn.execute(text("""
            ALTER TABLE test_run_details
            DROP FOREIGN KEY test_run_details_ibfk_2
        """))

        # 2. 修改字段允许为空
        conn.execute(text("""
            ALTER TABLE test_run_details
            MODIFY COLUMN case_id INT NULL
        """))

        # 3. 重新添加外键约束，设置级联删除为 SET NULL
        conn.execute(text("""
            ALTER TABLE test_run_details
            ADD CONSTRAINT test_run_details_ibfk_2
            FOREIGN KEY (case_id) REFERENCES api_test_cases(id)
            ON DELETE SET NULL
        """))

        conn.commit()
        print("迁移完成：外键约束已更新")


def downgrade():
    """回滚外键约束"""
    with engine.connect() as conn:
        # 1. 删除外键约束
        conn.execute(text("""
            ALTER TABLE test_run_details
            DROP FOREIGN KEY test_run_details_ibfk_2
        """))

        # 2. 修改字段不允许为空（需要先清理 NULL 值）
        # 注意：如果有 NULL 值，需要先处理
        conn.execute(text("""
            UPDATE test_run_details SET case_id = 0 WHERE case_id IS NULL
        """))

        conn.execute(text("""
            ALTER TABLE test_run_details
            MODIFY COLUMN case_id INT NOT NULL
        """))

        # 3. 重新添加原来的外键约束
        conn.execute(text("""
            ALTER TABLE test_run_details
            ADD CONSTRAINT test_run_details_ibfk_2
            FOREIGN KEY (case_id) REFERENCES api_test_cases(id)
        """))

        conn.commit()
        print("回滚完成：外键约束已恢复")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()