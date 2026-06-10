from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from database import get_db
from schemas.ui_case import UICaseCreate, UICaseUpdate, UICaseInDB
from models import UICase
from core.deps import get_current_user, check_permission
from models import User

router = APIRouter()


@router.get("/", response_model=List[UICaseInDB])
def list_ui_cases(
    project_id: int,
    keyword: Optional[str] = None,
    priority: Optional[str] = None,
    module: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:read"))
):
    query = db.query(UICase).filter(UICase.project_id == project_id)
    # 关键词搜索
    if keyword:
        query = query.filter(UICase.name.like(f"%{keyword}%"))
    # 优先级筛选
    if priority:
        query = query.filter(UICase.priority == priority)
    # 模块筛选（匹配当前模块及其子模块）
    if module:
        query = query.filter(
            or_(UICase.module == module, UICase.module.like(f"{module}/%"))
        )
    cases = query.order_by(UICase.id.desc()).offset(skip).limit(limit).all()
    return cases


@router.post("/", response_model=UICaseInDB)
def create_ui_case(
    case_in: UICaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:write"))
):
    from core.case_number import generate_case_number
    case_number = generate_case_number(db, case_in.project_id, case_in.module or "", UICase)
    case = UICase(**case_in.model_dump(), case_number=case_number)
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("/modules/tree")
def get_ui_case_modules(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:read"))
):
    """获取UI用例模块树"""
    cases = db.query(UICase).filter(
        UICase.project_id == project_id,
        UICase.module.isnot(None),
        UICase.module != ""
    ).all()

    # 构建模块树
    modules = set()
    for case in cases:
        if case.module:
            modules.add(case.module)

    # 构建树形结构
    tree = []
    module_map = {}
    for module_path in sorted(modules):
        parts = module_path.split("/")
        for i in range(len(parts)):
            partial = "/".join(parts[:i + 1])
            if partial not in module_map:
                node = {"label": parts[i], "value": partial, "children": []}
                module_map[partial] = node
                if i == 0:
                    tree.append(node)
                else:
                    parent = "/".join(parts[:i])
                    if parent in module_map:
                        module_map[parent]["children"].append(node)

    return tree


@router.get("/{case_id}", response_model=UICaseInDB)
def get_ui_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:read"))
):
    case = db.query(UICase).filter(UICase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="UI case not found")
    return case


@router.put("/{case_id}", response_model=UICaseInDB)
def update_ui_case(
    case_id: int,
    case_in: UICaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:write"))
):
    case = db.query(UICase).filter(UICase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="UI case not found")

    for field, value in case_in.model_dump(exclude_unset=True).items():
        setattr(case, field, value)

    db.commit()
    db.refresh(case)
    return case


@router.delete("/{case_id}")
def delete_ui_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:write"))
):
    case = db.query(UICase).filter(UICase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="UI case not found")

    db.delete(case)
    db.commit()
    return {"message": "UI case deleted successfully"}
