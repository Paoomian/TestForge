import enum
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class SceneNodeType(str, enum.Enum):
    """场景节点类型"""
    API_CALL = "api_call"          # 接口调用
    CONDITION = "condition"        # 条件判断
    WAIT = "wait"                  # 等待延时
    DATA_ASSIGN = "data_assign"    # 数据赋值


class ConditionOperator(str, enum.Enum):
    """条件运算符"""
    EQ = "eq"                      # 等于
    NEQ = "neq"                    # 不等于
    GT = "gt"                      # 大于
    LT = "lt"                      # 小于
    GTE = "gte"                    # 大于等于
    LTE = "lte"                    # 小于等于
    CONTAINS = "contains"          # 包含
    NOT_CONTAINS = "not_contains"  # 不包含
    EMPTY = "empty"                # 为空
    NOT_EMPTY = "not_empty"        # 不为空


class AssignSource(str, enum.Enum):
    """赋值来源"""
    STATIC = "static"              # 静态值
    EXPRESSION = "expression"      # 表达式


class SceneNode(Base):
    """场景编排节点"""
    __tablename__ = "scene_nodes"

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False)
    node_type = Column(String(20), nullable=False)  # api_call / condition / wait / data_assign
    name = Column(String(200), nullable=False)
    enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    # 接口调用字段
    case_id = Column(Integer, ForeignKey("api_test_cases.id", ondelete="SET NULL"), nullable=True)

    # 条件判断字段
    condition_variable = Column(String(200), nullable=True)
    condition_operator = Column(String(20), nullable=True)  # eq/neq/gt/lt/gte/lte/contains/not_contains/empty/not_empty
    condition_value = Column(Text, nullable=True)
    true_branch = Column(JSON, nullable=True)   # 条件为真时执行的节点ID列表
    false_branch = Column(JSON, nullable=True)  # 条件为假时执行的节点ID列表

    # 等待字段
    wait_seconds = Column(Integer, default=5)

    # 数据赋值字段
    assign_variable = Column(String(200), nullable=True)
    assign_value = Column(Text, nullable=True)
    assign_source = Column(String(20), default="static")  # static / expression

    # 审计字段
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    suite = relationship("TestSuite", back_populates="scene_nodes")
    case = relationship("APITestCase")
    creator = relationship("User")
