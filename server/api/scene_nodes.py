from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import User, SceneNode, TestSuite, APITestCase
from schemas.scene_node import (
    SceneNodeCreate, SceneNodeUpdate, SceneNodeInfo, SceneNodeBatchSort
)
from core.deps import get_current_user, check_permission
from typing import List

router = APIRouter()


@router.get("", response_model=List[SceneNodeInfo])
async def list_scene_nodes(
    suite_id: int = Query(..., description="任务配置ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取场景节点列表"""
    # 验证 suite 存在
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="任务配置不存在")

    nodes = db.query(SceneNode).filter(
        SceneNode.suite_id == suite_id
    ).order_by(SceneNode.sort_order).all()

    # 填充关联用例名称
    case_ids = [n.case_id for n in nodes if n.case_id]
    cases = db.query(APITestCase).filter(APITestCase.id.in_(case_ids)).all() if case_ids else []
    case_map = {c.id: c.name for c in cases}

    result = []
    for node in nodes:
        info = SceneNodeInfo.model_validate(node)
        if node.case_id:
            info.case_name = case_map.get(node.case_id)
        result.append(info)

    return result


@router.post("", response_model=SceneNodeInfo)
async def create_scene_node(
    req: SceneNodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:execute")),
):
    """创建场景节点"""
    # 验证 suite 存在
    suite = db.query(TestSuite).filter(TestSuite.id == req.suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="任务配置不存在")

    # 验证用例存在（如果是接口调用节点）
    if req.node_type == "api_call" and req.case_id:
        case = db.query(APITestCase).filter(APITestCase.id == req.case_id).first()
        if not case:
            raise HTTPException(status_code=400, detail="用例不存在")

    node = SceneNode(
        suite_id=req.suite_id,
        node_type=req.node_type,
        name=req.name,
        enabled=req.enabled,
        sort_order=req.sort_order,
        case_id=req.case_id,
        condition_variable=req.condition_variable,
        condition_operator=req.condition_operator,
        condition_value=req.condition_value,
        true_branch=req.true_branch,
        false_branch=req.false_branch,
        wait_seconds=req.wait_seconds,
        assign_variable=req.assign_variable,
        assign_value=req.assign_value,
        assign_source=req.assign_source,
        creator_id=current_user.id,
    )
    db.add(node)
    db.commit()
    db.refresh(node)

    info = SceneNodeInfo.model_validate(node)
    if node.case_id:
        case = db.query(APITestCase).filter(APITestCase.id == node.case_id).first()
        info.case_name = case.name if case else None

    return info


@router.put("/batch-sort")
async def batch_sort_scene_nodes(
    req: SceneNodeBatchSort,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:execute")),
):
    """批量排序场景节点"""
    # 验证 suite 存在
    suite = db.query(TestSuite).filter(TestSuite.id == req.suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="任务配置不存在")

    # 验证所有节点属于该 suite
    nodes = db.query(SceneNode).filter(
        SceneNode.id.in_(req.node_ids),
        SceneNode.suite_id == req.suite_id
    ).all()

    if len(nodes) != len(req.node_ids):
        found_ids = {n.id for n in nodes}
        missing = [nid for nid in req.node_ids if nid not in found_ids]
        raise HTTPException(status_code=400, detail=f"节点不存在或不属于该配置: {missing}")

    # 更新排序
    node_map = {n.id: n for n in nodes}
    for order, node_id in enumerate(req.node_ids):
        node_map[node_id].sort_order = order

    db.commit()

    return {"message": "排序成功"}


@router.put("/{node_id}", response_model=SceneNodeInfo)
async def update_scene_node(
    node_id: int,
    req: SceneNodeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:execute")),
):
    """更新场景节点"""
    node = db.query(SceneNode).filter(SceneNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")

    # 验证用例存在（如果更新了 case_id）
    if req.case_id is not None:
        if req.case_id:
            case = db.query(APITestCase).filter(APITestCase.id == req.case_id).first()
            if not case:
                raise HTTPException(status_code=400, detail="用例不存在")

    # 更新字段
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(node, key, value)

    db.commit()
    db.refresh(node)

    info = SceneNodeInfo.model_validate(node)
    if node.case_id:
        case = db.query(APITestCase).filter(APITestCase.id == node.case_id).first()
        info.case_name = case.name if case else None

    return info


@router.delete("/{node_id}")
async def delete_scene_node(
    node_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:execute")),
):
    """删除场景节点"""
    node = db.query(SceneNode).filter(SceneNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")

    db.delete(node)
    db.commit()

    return {"message": "删除成功"}
