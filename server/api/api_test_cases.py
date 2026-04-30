from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from database import get_db
from schemas.api_test_case import (
    APITestCaseCreate,
    APITestCaseUpdate,
    APITestCaseInDB,
    APITestCaseHistoryInDB,
    BatchTagRequest,
    BatchDeleteRequest
)
from models import APITestCase, APITestCaseHistory, User
from core.deps import get_current_user, check_permission

router = APIRouter()


@router.get("", response_model=List[APITestCaseInDB])
def list_test_cases(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    module: Optional[str] = None,
    keyword: Optional[str] = None,
    tags: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:read"))
):
    query = db.query(APITestCase)

    if project_id:
        query = query.filter(APITestCase.project_id == project_id)
    if module:
        query = query.filter(APITestCase.module.like(f"{module}%"))
    if keyword:
        query = query.filter(
            or_(
                APITestCase.name.contains(keyword),
                APITestCase.description.contains(keyword)
            )
        )
    if tags:
        tag_list = tags.split(",")
        for tag in tag_list:
            query = query.filter(APITestCase.tags.contains([tag]))
    if priority:
        query = query.filter(APITestCase.priority == priority)
    if status:
        query = query.filter(APITestCase.status == status)

    return query.offset(skip).limit(limit).all()


@router.post("", response_model=APITestCaseInDB)
def create_test_case(
    case_in: APITestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    test_case = APITestCase(**case_in.model_dump(), creator_id=current_user.id)
    db.add(test_case)
    db.commit()
    db.refresh(test_case)
    return test_case


@router.get("/{case_id}", response_model=APITestCaseInDB)
def get_test_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:read"))
):
    test_case = db.query(APITestCase).filter(APITestCase.id == case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    return test_case


@router.put("/{case_id}", response_model=APITestCaseInDB)
def update_test_case(
    case_id: int,
    case_in: APITestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    test_case = db.query(APITestCase).filter(APITestCase.id == case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    # 创建历史版本
    snapshot = {
        "name": test_case.name,
        "description": test_case.description,
        "module": test_case.module,
        "method": test_case.method,
        "url": test_case.url,
        "headers": test_case.headers,
        "body": test_case.body,
        "query_params": test_case.query_params,
        "variables": test_case.variables,
        "setup_script": test_case.setup_script,
        "teardown_script": test_case.teardown_script,
        "assertions": test_case.assertions,
        "tags": test_case.tags,
        "priority": test_case.priority,
        "status": test_case.status,
    }
    history = APITestCaseHistory(
        test_case_id=test_case.id,
        version=test_case.version,
        snapshot=snapshot,
        changed_by=current_user.id
    )
    db.add(history)

    # 更新用例
    for field, value in case_in.model_dump(exclude_unset=True).items():
        setattr(test_case, field, value)

    test_case.version += 1
    db.commit()
    db.refresh(test_case)
    return test_case


@router.delete("/{case_id}")
def delete_test_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    test_case = db.query(APITestCase).filter(APITestCase.id == case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    db.delete(test_case)
    db.commit()
    return {"message": "Test case deleted successfully"}


@router.post("/batch-tag")
def batch_tag(
    request: BatchTagRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    cases = db.query(APITestCase).filter(APITestCase.id.in_(request.case_ids)).all()

    for case in cases:
        if request.operation == "add":
            existing_tags = set(case.tags or [])
            existing_tags.update(request.tags)
            case.tags = list(existing_tags)
        elif request.operation == "remove":
            existing_tags = set(case.tags or [])
            existing_tags.difference_update(request.tags)
            case.tags = list(existing_tags)

    db.commit()
    return {"message": f"Successfully tagged {len(cases)} test cases"}


@router.post("/batch-delete")
def batch_delete(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    deleted_count = db.query(APITestCase).filter(APITestCase.id.in_(request.case_ids)).delete(synchronize_session=False)
    db.commit()
    return {"message": f"Successfully deleted {deleted_count} test cases"}


@router.post("/{case_id}/copy", response_model=APITestCaseInDB)
def copy_test_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    original = db.query(APITestCase).filter(APITestCase.id == case_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Test case not found")

    new_case = APITestCase(
        project_id=original.project_id,
        module=original.module,
        name=f"{original.name} (副本)",
        description=original.description,
        method=original.method,
        url=original.url,
        headers=original.headers,
        body=original.body,
        query_params=original.query_params,
        variables=original.variables,
        setup_script=original.setup_script,
        teardown_script=original.teardown_script,
        assertions=original.assertions,
        tags=original.tags,
        priority=original.priority,
        status=original.status,
        creator_id=current_user.id
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return new_case


@router.get("/{case_id}/histories", response_model=List[APITestCaseHistoryInDB])
def get_histories(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:read"))
):
    test_case = db.query(APITestCase).filter(APITestCase.id == case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    histories = db.query(APITestCaseHistory).filter(
        APITestCaseHistory.test_case_id == case_id
    ).order_by(APITestCaseHistory.version.desc()).all()

    return histories


@router.post("/{case_id}/rollback/{version}", response_model=APITestCaseInDB)
def rollback_version(
    case_id: int,
    version: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    test_case = db.query(APITestCase).filter(APITestCase.id == case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    history = db.query(APITestCaseHistory).filter(
        APITestCaseHistory.test_case_id == case_id,
        APITestCaseHistory.version == version
    ).first()

    if not history:
        raise HTTPException(status_code=404, detail="Version not found")

    # 保存当前版本到历史
    current_snapshot = {
        "name": test_case.name,
        "description": test_case.description,
        "module": test_case.module,
        "method": test_case.method,
        "url": test_case.url,
        "headers": test_case.headers,
        "body": test_case.body,
        "query_params": test_case.query_params,
        "variables": test_case.variables,
        "setup_script": test_case.setup_script,
        "teardown_script": test_case.teardown_script,
        "assertions": test_case.assertions,
        "tags": test_case.tags,
        "priority": test_case.priority,
        "status": test_case.status,
    }
    new_history = APITestCaseHistory(
        test_case_id=test_case.id,
        version=test_case.version,
        snapshot=current_snapshot,
        change_description=f"Rollback to version {version}",
        changed_by=current_user.id
    )
    db.add(new_history)

    # 恢复历史版本
    snapshot = history.snapshot
    for field, value in snapshot.items():
        setattr(test_case, field, value)

    test_case.version += 1
    db.commit()
    db.refresh(test_case)
    return test_case


@router.get("/modules/tree")
def get_module_tree(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:read"))
):
    query = db.query(APITestCase.project_id, APITestCase.module).distinct()

    if project_id:
        query = query.filter(APITestCase.project_id == project_id)

    results = query.all()

    # 构建树形结构
    tree = {}
    for proj_id, module in results:
        if proj_id not in tree:
            tree[proj_id] = set()
        if module:
            tree[proj_id].add(module)

    # 转换为列表
    tree_list = []
    for proj_id, modules in tree.items():
        tree_list.append({
            "project_id": proj_id,
            "modules": sorted(list(modules))
        })

    return tree_list
