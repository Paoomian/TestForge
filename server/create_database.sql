-- 创建测试平台数据库
CREATE DATABASE IF NOT EXISTS testplatform
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE testplatform;

-- 显示数据库信息
SELECT
    SCHEMA_NAME as '数据库名',
    DEFAULT_CHARACTER_SET_NAME as '字符集',
    DEFAULT_COLLATION_NAME as '排序规则'
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME = 'testplatform';
