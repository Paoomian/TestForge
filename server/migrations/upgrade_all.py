"""
统一数据库升级脚本
适用于已存在的数据库，合并所有增量迁移为一次执行。

用法：
    cd server
    python migrations/upgrade_all.py

说明：
    - 全新安装请使用 python init_db.py（自动从 ORM 模型创建所有表）
    - 本脚本适用于已有数据库的升级，会自动跳过已完成的操作
    - 可重复执行，不会产生副作用
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from database import engine


def table_exists(conn, table_name):
    """检查表是否存在"""
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def column_exists(conn, table_name, column_name):
    """检查列是否存在"""
    inspector = inspect(conn)
    try:
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception:
        return False


def index_exists(conn, table_name, index_name):
    """检查索引是否存在"""
    result = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.statistics "
        "WHERE table_schema = DATABASE() AND table_name = :table AND index_name = :index"
    ), {"table": table_name, "index": index_name})
    return result.scalar() > 0


def fk_exists(conn, table_name, fk_name):
    """检查外键约束是否存在"""
    result = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.table_constraints "
        "WHERE table_schema = DATABASE() AND table_name = :table "
        "AND constraint_name = :fk AND constraint_type = 'FOREIGN KEY'"
    ), {"table": table_name, "fk": fk_name})
    return result.scalar() > 0


def safe_add_column(conn, table, column, col_type):
    """安全添加列（跳过已存在的）"""
    if not column_exists(conn, table, column):
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
        print(f"  + {table}.{column}")
        return True
    return False


# ==================== 表创建 ====================

def ensure_test_suites(conn):
    """创建 test_suites 表（如不存在）"""
    if table_exists(conn, "test_suites"):
        return
    conn.execute(text("""
        CREATE TABLE test_suites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            project_id INT NOT NULL,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            case_ids JSON,
            environment_id INT,
            concurrency INT DEFAULT 1,
            failure_strategy VARCHAR(20) DEFAULT 'continue',
            variables JSON,
            tags JSON,
            config_mode VARCHAR(20) DEFAULT 'simple',
            creator_id INT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (environment_id) REFERENCES environments(id),
            FOREIGN KEY (creator_id) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    print("  + 创建表 test_suites")


def ensure_test_run_details(conn):
    """创建 test_run_details 表（如不存在）"""
    if table_exists(conn, "test_run_details"):
        return
    conn.execute(text("""
        CREATE TABLE test_run_details (
            id INT AUTO_INCREMENT PRIMARY KEY,
            test_run_id INT NOT NULL,
            case_id INT NULL,
            case_name VARCHAR(200) NULL,
            case_number VARCHAR(50) NULL,
            node_id INT NULL,
            node_type VARCHAR(20) DEFAULT 'api_call',
            execution_order INT DEFAULT 0,
            status VARCHAR(20) DEFAULT 'pending',
            request_snapshot JSON,
            response_info JSON,
            assertions JSON,
            extracted_vars JSON,
            script_output JSON,
            error_message TEXT,
            duration_ms INT DEFAULT 0,
            started_at DATETIME,
            finished_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (test_run_id) REFERENCES test_runs(id) ON DELETE CASCADE,
            FOREIGN KEY (case_id) REFERENCES api_test_cases(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    print("  + 创建表 test_run_details")


def ensure_test_case_data_rules(conn):
    """创建 test_case_data_rules 表（如不存在）"""
    if table_exists(conn, "test_case_data_rules"):
        return
    conn.execute(text("""
        CREATE TABLE test_case_data_rules (
            id INT AUTO_INCREMENT PRIMARY KEY,
            test_case_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            rule_type VARCHAR(30) NOT NULL,
            enabled BOOLEAN DEFAULT TRUE,
            description VARCHAR(500),
            default_value TEXT,
            sort_order INT DEFAULT 0,
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    print("  + 创建表 test_case_data_rules")


def ensure_scene_nodes(conn):
    """创建 scene_nodes 表（如不存在）"""
    if table_exists(conn, "scene_nodes"):
        return
    conn.execute(text("""
        CREATE TABLE scene_nodes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            suite_id INT NOT NULL,
            node_type VARCHAR(20) NOT NULL,
            name VARCHAR(200) NOT NULL,
            enabled BOOLEAN DEFAULT TRUE,
            sort_order INT DEFAULT 0,
            case_id INT NULL,
            condition_variable VARCHAR(200) NULL,
            condition_operator VARCHAR(20) NULL,
            condition_value TEXT NULL,
            true_branch JSON NULL,
            false_branch JSON NULL,
            wait_seconds INT DEFAULT 5,
            assign_variable VARCHAR(200) NULL,
            assign_value TEXT NULL,
            assign_source VARCHAR(20) DEFAULT 'static',
            creator_id INT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (suite_id) REFERENCES test_suites(id) ON DELETE CASCADE,
            FOREIGN KEY (case_id) REFERENCES api_test_cases(id) ON DELETE SET NULL,
            FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE SET NULL,
            INDEX idx_scene_node_suite (suite_id),
            INDEX idx_scene_node_sort (suite_id, sort_order)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    print("  + 创建表 scene_nodes")


# ==================== 字段补全 ====================

def upgrade_test_runs_columns(conn):
    """补全 test_runs 表缺失字段"""
    columns = [
        ("environment_id", "INT"),
        ("concurrency", "INT DEFAULT 1"),
        ("failure_strategy", "VARCHAR(20) DEFAULT 'continue'"),
        ("variables", "JSON"),
        ("celery_task_id", "VARCHAR(200)"),
        ("cancelled", "BOOLEAN DEFAULT FALSE"),
        ("total_count", "INT DEFAULT 0"),
        ("pass_count", "INT DEFAULT 0"),
        ("fail_count", "INT DEFAULT 0"),
        ("error_count", "INT DEFAULT 0"),
        ("creator_id", "INT"),
        ("config_mode", "VARCHAR(20) DEFAULT 'simple'"),
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    ]
    for col_name, col_type in columns:
        safe_add_column(conn, "test_runs", col_name, col_type)


def upgrade_test_run_details_columns(conn):
    """补全 test_run_details 表缺失字段"""
    columns = [
        ("case_name", "VARCHAR(200) NULL"),
        ("case_number", "VARCHAR(50) NULL"),
        ("node_id", "INT NULL"),
        ("node_type", "VARCHAR(20) DEFAULT 'api_call'"),
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    ]
    for col_name, col_type in columns:
        safe_add_column(conn, "test_run_details", col_name, col_type)


def upgrade_test_suites_columns(conn):
    """补全 test_suites 表缺失字段"""
    safe_add_column(conn, "test_suites", "config_mode", "VARCHAR(20) DEFAULT 'simple'")


def upgrade_api_test_cases_columns(conn):
    """补全 api_test_cases 表缺失字段"""
    safe_add_column(conn, "api_test_cases", "environment_id", "INT NULL")


# ==================== 一次性操作 ====================

def fix_test_run_detail_fk(conn):
    """修改 test_run_details.case_id 外键为 ON DELETE SET NULL"""
    if not table_exists(conn, "test_run_details"):
        return

    # 检查 case_id 是否允许 NULL
    result = conn.execute(text(
        "SELECT IS_NULLABLE FROM information_schema.columns "
        "WHERE table_schema = DATABASE() AND table_name = 'test_run_details' AND column_name = 'case_id'"
    ))
    row = result.fetchone()
    if row and row[0] == 'YES':
        return  # 已经是可空的，说明已处理过

    # 查找现有外键约束名
    result = conn.execute(text(
        "SELECT constraint_name FROM information_schema.key_column_usage "
        "WHERE table_schema = DATABASE() AND table_name = 'test_run_details' "
        "AND column_name = 'case_id' AND referenced_table_name IS NOT NULL"
    ))
    row = result.fetchone()
    if not row:
        return

    fk_name = row[0]
    try:
        conn.execute(text(f"ALTER TABLE test_run_details DROP FOREIGN KEY {fk_name}"))
        conn.execute(text("ALTER TABLE test_run_details MODIFY COLUMN case_id INT NULL"))
        conn.execute(text(
            f"ALTER TABLE test_run_details ADD CONSTRAINT {fk_name} "
            "FOREIGN KEY (case_id) REFERENCES api_test_cases(id) ON DELETE SET NULL"
        ))
        print(f"  ~ test_run_details.case_id 外键已修改为 SET NULL")
    except Exception as e:
        print(f"  ! 外键修改失败（可忽略）: {e}")


def backfill_case_snapshot(conn):
    """回填 test_run_details 的 case_name/case_number 字段"""
    if not column_exists(conn, "test_run_details", "case_name"):
        return

    result = conn.execute(text(
        "SELECT COUNT(*) FROM test_run_details "
        "WHERE case_name IS NULL AND case_id IS NOT NULL"
    ))
    count = result.scalar()
    if count == 0:
        return

    conn.execute(text("""
        UPDATE test_run_details d
        JOIN api_test_cases c ON d.case_id = c.id
        SET d.case_name = c.name, d.case_number = c.case_number
        WHERE d.case_name IS NULL AND d.case_id IS NOT NULL
    """))
    print(f"  ~ 已回填 {count} 条用例快照数据")


def migrate_extracts_to_data_rules(conn):
    """将 test_case_extracts 数据迁移到 test_case_data_rules，然后删除旧表"""
    if not table_exists(conn, "test_case_extracts"):
        return

    if not table_exists(conn, "test_case_data_rules"):
        print("  ! test_case_data_rules 表不存在，跳过迁移")
        return

    # 迁移数据（按 test_case_id + name 去重）
    result = conn.execute(text("""
        INSERT IGNORE INTO test_case_data_rules
            (test_case_id, name, rule_type, enabled, description, default_value, sort_order, source, expression)
        SELECT
            e.test_case_id, e.name, 'extract', TRUE, e.description, e.default_value, e.sort_order, e.source, e.expression
        FROM test_case_extracts e
        WHERE NOT EXISTS (
            SELECT 1 FROM test_case_data_rules d
            WHERE d.test_case_id = e.test_case_id AND d.name = e.name AND d.rule_type = 'extract'
        )
    """))
    migrated = result.rowcount

    # 删除旧表
    conn.execute(text("DROP TABLE test_case_extracts"))
    print(f"  ~ 已迁移 {migrated} 条提取规则到 test_case_data_rules，已删除 test_case_extracts 表")


def add_case_indexes(conn):
    """添加 api_test_cases 表索引"""
    indexes = [
        ("idx_case_project_module", "api_test_cases", "(project_id, module)"),
        ("idx_case_project_id", "api_test_cases", "(project_id)"),
        ("idx_case_module", "api_test_cases", "(module)"),
    ]
    for idx_name, table, cols in indexes:
        if not index_exists(conn, table, idx_name):
            conn.execute(text(f"CREATE INDEX {idx_name} ON {table} {cols}"))
            print(f"  + 索引 {idx_name}")


# ==================== AI 生成功能 ====================

def ensure_ai_provider_configs(conn):
    """创建 ai_provider_configs 表（如不存在）"""
    if table_exists(conn, "ai_provider_configs"):
        return
    conn.execute(text("""
        CREATE TABLE ai_provider_configs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            provider VARCHAR(50) NOT NULL,
            api_key VARCHAR(500) NOT NULL,
            model_name VARCHAR(100) NOT NULL,
            api_base_url VARCHAR(500),
            is_default BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            INDEX ix_ai_provider_configs_user_id (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    print("  + 创建表 ai_provider_configs")


def ensure_ai_skills(conn):
    """创建 ai_skills 表（如不存在）"""
    if table_exists(conn, "ai_skills"):
        return
    conn.execute(text("""
        CREATE TABLE ai_skills (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            description VARCHAR(500) DEFAULT '',
            generate_type VARCHAR(20) NOT NULL,
            system_prompt TEXT NOT NULL,
            user_prompt TEXT NOT NULL,
            is_default BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            INDEX ix_ai_skills_user_id (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    print("  + 创建表 ai_skills")


def ensure_ai_generate_tasks(conn):
    """创建 ai_generate_tasks 表（如不存在）"""
    if table_exists(conn, "ai_generate_tasks"):
        # 修改 project_id 为可空（功能测试用例不需要项目）
        try:
            conn.execute(text("ALTER TABLE ai_generate_tasks MODIFY COLUMN project_id INT NULL"))
            print("  ~ 修改 ai_generate_tasks.project_id 为可空")
        except Exception:
            pass
        # 添加 skill_id 字段
        if not column_exists(conn, "ai_generate_tasks", "skill_id"):
            try:
                conn.execute(text("ALTER TABLE ai_generate_tasks ADD COLUMN skill_id INT NULL"))
                conn.execute(text("ALTER TABLE ai_generate_tasks ADD INDEX ix_ai_generate_tasks_skill_id (skill_id)"))
                conn.execute(text("ALTER TABLE ai_generate_tasks ADD FOREIGN KEY (skill_id) REFERENCES ai_skills(id)"))
                print("  + 添加 ai_generate_tasks.skill_id 字段")
            except Exception as e:
                print(f"  ! 添加 skill_id 失败: {e}")
        return
    conn.execute(text("""
        CREATE TABLE ai_generate_tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            project_id INT NULL,
            input_type VARCHAR(20) NOT NULL,
            input_content TEXT,
            input_file_path VARCHAR(500),
            input_file_name VARCHAR(200),
            generate_type VARCHAR(20) NOT NULL,
            provider VARCHAR(50) NOT NULL,
            model_name VARCHAR(100) NOT NULL,
            target_count INT DEFAULT 10,
            status VARCHAR(20) DEFAULT 'pending',
            progress INT DEFAULT 0,
            error_message TEXT,
            generated_cases JSON,
            cases_count INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            completed_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (project_id) REFERENCES projects(id),
            INDEX ix_ai_generate_tasks_user_id (user_id),
            INDEX ix_ai_generate_tasks_project_id (project_id),
            INDEX ix_ai_generate_tasks_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    print("  + 创建表 ai_generate_tasks")


def ensure_monkey_presets(conn):
    """创建 monkey_presets 表（如不存在）"""
    if table_exists(conn, "monkey_presets"):
        return
    conn.execute(text("""
        CREATE TABLE monkey_presets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL COMMENT '配置名称',
            user_id INT NOT NULL,
            pct_touch INT DEFAULT 15 COMMENT '触摸事件(%)',
            pct_motion INT DEFAULT 10 COMMENT '滑动事件(%)',
            pct_trackball INT DEFAULT 15 COMMENT '轨迹球(%)',
            pct_nav INT DEFAULT 20 COMMENT '基本导航(%)',
            pct_majornav INT DEFAULT 15 COMMENT '主要导航(%)',
            pct_syskeys INT DEFAULT 5 COMMENT '系统按键(%)',
            pct_appswitch INT DEFAULT 2 COMMENT 'Activity切换(%)',
            pct_anyevent INT DEFAULT 18 COMMENT '其他事件(%)',
            event_count INT DEFAULT 1000 COMMENT '事件总数',
            interval INT DEFAULT 300 COMMENT '事件间隔(ms)',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            INDEX ix_monkey_presets_user_id (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    print("  + 创建表 monkey_presets")


def ensure_ui_test_suites(conn):
    """创建 ui_test_suites 表（如不存在）"""
    if table_exists(conn, "ui_test_suites"):
        return
    conn.execute(text("""
        CREATE TABLE ui_test_suites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            project_id INT NOT NULL,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            case_ids JSON DEFAULT NULL,
            environment_id INT,
            failure_strategy VARCHAR(20) DEFAULT 'continue',
            browser VARCHAR(20) DEFAULT 'chrome',
            viewport_width INT DEFAULT 1280,
            viewport_height INT DEFAULT 720,
            tags JSON DEFAULT NULL,
            creator_id INT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (environment_id) REFERENCES environments(id),
            FOREIGN KEY (creator_id) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    print("  + 创建表 ui_test_suites")


# ==================== 主入口 ====================

def ensure_innodb(conn):
    """将所有 MyISAM 表转换为 InnoDB（外键约束要求）"""
    result = conn.execute(text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND engine = 'MyISAM'"
    ))
    myisam_tables = [row[0] for row in result]
    if not myisam_tables:
        return
    print(f"  发现 {len(myisam_tables)} 个 MyISAM 表，转换为 InnoDB...")
    for table in myisam_tables:
        conn.execute(text(f"ALTER TABLE `{table}` ENGINE=InnoDB"))
        print(f"    ~ {table} -> InnoDB")


def ensure_ui_cases_extended(conn):
    """扩展 ui_cases 表：添加录制相关字段"""
    if not table_exists(conn, "ui_cases"):
        return
    safe_add_column(conn, "ui_cases", "base_url", "VARCHAR(500) DEFAULT NULL")
    safe_add_column(conn, "ui_cases", "browser_config", "JSON DEFAULT NULL")


def upgrade():
    """执行全部升级"""
    print("=" * 50)
    print("TestForge 数据库统一升级")
    print("=" * 50)

    with engine.connect() as conn:
        # 0. 确保所有表使用 InnoDB 引擎
        print("\n[0/6] 检查存储引擎...")
        ensure_innodb(conn)

        # 1. 创建缺失的表
        print("\n[1/6] 创建缺失的表...")
        ensure_test_suites(conn)
        ensure_test_run_details(conn)
        ensure_test_case_data_rules(conn)
        ensure_scene_nodes(conn)
        ensure_ai_provider_configs(conn)
        ensure_ai_skills(conn)
        ensure_ai_generate_tasks(conn)
        ensure_monkey_presets(conn)
        ensure_ui_test_suites(conn)

        # 2. 补全缺失的字段
        print("\n[2/6] 补全缺失的字段...")
        upgrade_test_runs_columns(conn)
        upgrade_test_run_details_columns(conn)
        upgrade_test_suites_columns(conn)
        upgrade_api_test_cases_columns(conn)
        ensure_ui_cases_extended(conn)

        # 3. 修复外键约束
        print("\n[3/6] 修复外键约束...")
        fix_test_run_detail_fk(conn)

        # 4. 回填数据
        print("\n[4/6] 回填数据...")
        backfill_case_snapshot(conn)
        migrate_extracts_to_data_rules(conn)

        # 5. 添加索引
        print("\n[5/6] 添加索引...")
        add_case_indexes(conn)

        # 6. AI 生成功能表（已在步骤 1 创建）

        conn.commit()

    print("\n" + "=" * 50)
    print("升级完成!")
    print("=" * 50)


if __name__ == "__main__":
    upgrade()
