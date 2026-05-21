from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SceneNodeCreate(BaseModel):
    """创建场景节点"""
    suite_id: int
    node_type: str  # api_call / condition / wait / data_assign
    name: str
    enabled: bool = True
    sort_order: int = 0

    # 接口调用字段
    case_id: Optional[int] = None

    # 条件判断字段
    condition_variable: Optional[str] = None
    condition_operator: Optional[str] = None  # eq/neq/gt/lt/gte/lte/contains/not_contains/empty/not_empty
    condition_value: Optional[str] = None
    true_branch: Optional[List[int]] = None
    false_branch: Optional[List[int]] = None

    # 等待字段
    wait_seconds: int = 5

    # 数据赋值字段
    assign_variable: Optional[str] = None
    assign_value: Optional[str] = None
    assign_source: str = "static"  # static / expression


class SceneNodeUpdate(BaseModel):
    """更新场景节点"""
    name: Optional[str] = None
    enabled: Optional[bool] = None
    sort_order: Optional[int] = None

    # 接口调用字段
    case_id: Optional[int] = None

    # 条件判断字段
    condition_variable: Optional[str] = None
    condition_operator: Optional[str] = None
    condition_value: Optional[str] = None
    true_branch: Optional[List[int]] = None
    false_branch: Optional[List[int]] = None

    # 等待字段
    wait_seconds: Optional[int] = None

    # 数据赋值字段
    assign_variable: Optional[str] = None
    assign_value: Optional[str] = None
    assign_source: Optional[str] = None


class SceneNodeInfo(BaseModel):
    """场景节点详情"""
    id: int
    suite_id: int
    node_type: str
    name: str
    enabled: bool = True
    sort_order: int = 0

    # 接口调用字段
    case_id: Optional[int] = None
    case_name: Optional[str] = None  # 关联用例名称（只读）

    # 条件判断字段
    condition_variable: Optional[str] = None
    condition_operator: Optional[str] = None
    condition_value: Optional[str] = None
    true_branch: Optional[List[int]] = None
    false_branch: Optional[List[int]] = None

    # 等待字段
    wait_seconds: int = 5

    # 数据赋值字段
    assign_variable: Optional[str] = None
    assign_value: Optional[str] = None
    assign_source: str = "static"

    # 审计字段
    creator_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SceneNodeBatchSort(BaseModel):
    """批量排序请求"""
    suite_id: int
    node_ids: List[int]  # 按新顺序排列的节点ID列表
