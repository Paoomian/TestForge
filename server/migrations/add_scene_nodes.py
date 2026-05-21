"""创建 scene_nodes 表（场景编排节点）"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from database import engine


def table_exists(conn, table_name):
    """检查表是否存在"""
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade():
    """创建 scene_nodes 表"""
    with engine.connect() as conn:
        if not table_exists(conn, "scene_nodes"):
            conn.execute(text("""
                CREATE TABLE scene_nodes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    suite_id INT NOT NULL,
                    node_type VARCHAR(20) NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    sort_order INT DEFAULT 0,

                    -- 接口调用字段
                    case_id INT NULL,

                    -- 条件判断字段
                    condition_variable VARCHAR(200) NULL,
                    condition_operator VARCHAR(20) NULL,
                    condition_value TEXT NULL,
                    true_branch JSON NULL,
                    false_branch JSON NULL,

                    -- 等待字段
                    wait_seconds INT DEFAULT 5,

                    -- 数据赋值字段
                    assign_variable VARCHAR(200) NULL,
                    assign_value TEXT NULL,
                    assign_source VARCHAR(20) DEFAULT 'static',

                    -- 审计字段
                    creator_id INT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,

                    -- 外键约束
                    FOREIGN KEY (suite_id) REFERENCES test_suites(id) ON DELETE CASCADE,
                    FOREIGN KEY (case_id) REFERENCES api_test_cases(id) ON DELETE SET NULL,
                    FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE SET NULL,

                    -- 索引
                    INDEX idx_scene_node_suite (suite_id),
                    INDEX idx_scene_node_sort (suite_id, sort_order)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            conn.commit()
            print("已创建 scene_nodes 表")
        else:
            print("scene_nodes 表已存在，跳过")


def downgrade():
    """删除 scene_nodes 表"""
    with engine.connect() as conn:
        if table_exists(conn, "scene_nodes"):
            conn.execute(text("DROP TABLE scene_nodes"))
            conn.commit()
            print("已删除 scene_nodes 表")
        else:
            print("scene_nodes 表不存在，跳过")


if __name__ == "__main__":
    upgrade()
