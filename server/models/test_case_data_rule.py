from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, ForeignKey
from database import Base


class TestCaseDataRule(Base):
    """用例数据规则 - 可视化数据传递配置"""
    __tablename__ = "test_case_data_rules"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    test_case_id = Column(Integer, ForeignKey("api_test_cases.id", ondelete="CASCADE"), nullable=False)

    # 基础字段
    name = Column(String(100), nullable=False)  # 变量名
    rule_type = Column(String(30), nullable=False)  # extract/static/generate/transform/conditional
    enabled = Column(Boolean, default=True)
    description = Column(String(500))
    default_value = Column(Text)  # 通用默认值
    sort_order = Column(Integer, default=0)

    # extract 类型专用（从响应提取）
    source = Column(String(30))  # jsonpath/regex/header
    expression = Column(String(1000))  # 提取表达式

    # static 类型专用
    static_value = Column(Text)  # 静态值

    # generate 类型专用
    generator = Column(String(30))  # timestamp/uuid/random_int/random_string/now
    generator_params = Column(JSON)  # 生成器参数

    # transform 类型专用（对已有变量做变换）
    source_variable = Column(String(100))  # 源变量名
    transform_type = Column(String(30))  # substring/concat/replace/upper/lower/trim/to_int/to_string/format_date
    transform_params = Column(JSON)  # 变换参数

    # conditional 类型专用
    condition_variable = Column(String(100))  # 条件变量名
    condition_operator = Column(String(20))  # equals/not_equals/contains/is_empty/is_not_empty/greater_than/less_than
    condition_value = Column(String(500))  # 条件值
    true_value = Column(String(1000))  # 条件为真时设置的值
    false_value = Column(String(1000))  # 条件为假时设置的值
