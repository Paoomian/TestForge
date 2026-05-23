from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional
from database import get_db
from schemas.api_test_case import (
    APITestCaseCreate,
    APITestCaseUpdate,
    APITestCaseInDB,
    BatchDeleteRequest,
    CreateModuleRequest,
    RenameModuleRequest,
    CurlImportRequest,
)
from models import (
    APITestCase, User,
    TestCaseHeader, TestCaseQueryParam, TestCaseBodyForm, TestCaseBodyRaw,
    TestCaseAssertion, TestCaseAuth, TestCaseDataRule,
)
from core.deps import get_current_user, check_permission
from core.case_number import generate_case_number
from core.curl_parser import parse_curl
from core.templates import get_templates
from schemas.excel_import import ExcelImportRequest, ExcelImportResult
from core.excel_import_service import import_excel_cases

router = APIRouter()


def _load_nested(case: APITestCase) -> dict:
    """将ORM对象及其子表转为dict供Pydantic序列化"""
    return {
        "id": case.id,
        "project_id": case.project_id,
        "environment_id": case.environment_id,
        "environment_name": case.environment.name if case.environment else None,
        "case_number": case.case_number,
        "module": case.module,
        "name": case.name,
        "description": case.description,
        "preconditions": case.preconditions,
        "remark": case.remark,
        "method": case.method,
        "url": case.url,
        "body_type": case.body_type,
        "auth_type": case.auth_type,
        "setup_script": case.setup_script,
        "teardown_script": case.teardown_script,
        "priority": case.priority,
        "status": case.status,
        "creator_id": case.creator_id,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
        "headers": [
            {"enabled": h.enabled, "key": h.key, "value": h.value, "description": h.description, "sort_order": h.sort_order}
            for h in (case.headers or [])
        ],
        "query_params": [
            {"enabled": p.enabled, "key": p.key, "value": p.value, "description": p.description, "sort_order": p.sort_order}
            for p in (case.query_params or [])
        ],
        "body_form": [
            {"enabled": f.enabled, "key": f.key, "value": f.value, "param_type": f.param_type, "description": f.description, "sort_order": f.sort_order}
            for f in (case.body_form or [])
        ],
        "body_raw": {"content": case.body_raw.content} if case.body_raw else None,
        "assertions": [
            {"assertion_type": a.assertion_type, "operator": a.operator, "field": a.field, "expected": a.expected, "description": a.description, "sort_order": a.sort_order}
            for a in (case.assertions or [])
        ],
        "data_rules": [
            {
                "name": r.name, "rule_type": r.rule_type, "enabled": r.enabled,
                "description": r.description, "default_value": r.default_value, "sort_order": r.sort_order,
                "source": r.source, "expression": r.expression,
                "static_value": r.static_value,
                "generator": r.generator, "generator_params": r.generator_params,
                "source_variable": r.source_variable, "transform_type": r.transform_type, "transform_params": r.transform_params,
                "condition_variable": r.condition_variable, "condition_operator": r.condition_operator,
                "condition_value": r.condition_value, "true_value": r.true_value, "false_value": r.false_value,
            }
            for r in (case.data_rules or [])
        ],
        "auth": {
            "auth_type": case.auth.auth_type,
            "token": case.auth.token,
            "username": case.auth.username,
            "password": case.auth.password,
            "api_key_name": case.auth.api_key_name,
            "api_key_value": case.auth.api_key_value,
            "api_key_location": case.auth.api_key_location,
        } if case.auth else None,
    }


def _create_children(db: Session, case_id: int, data: APITestCaseCreate):
    """创建用例的所有子表记录"""
    for i, h in enumerate(data.headers):
        db.add(TestCaseHeader(test_case_id=case_id, enabled=h.enabled, key=h.key, value=h.value, description=h.description, sort_order=i))
    for i, p in enumerate(data.query_params):
        db.add(TestCaseQueryParam(test_case_id=case_id, enabled=p.enabled, key=p.key, value=p.value, description=p.description, sort_order=i))
    for i, f in enumerate(data.body_form):
        db.add(TestCaseBodyForm(test_case_id=case_id, enabled=f.enabled, key=f.key, value=f.value, param_type=f.param_type, description=f.description, sort_order=i))
    if data.body_raw and data.body_raw.content:
        db.add(TestCaseBodyRaw(test_case_id=case_id, content=data.body_raw.content))
    for i, a in enumerate(data.assertions):
        db.add(TestCaseAssertion(test_case_id=case_id, assertion_type=a.assertion_type, operator=a.operator, field=a.field, expected=a.expected, description=a.description, sort_order=i))
    for i, r in enumerate(data.data_rules):
        db.add(TestCaseDataRule(
            test_case_id=case_id, name=r.name, rule_type=r.rule_type, enabled=r.enabled,
            description=r.description, default_value=r.default_value, sort_order=i,
            source=r.source, expression=r.expression, static_value=r.static_value,
            generator=r.generator, generator_params=r.generator_params,
            source_variable=r.source_variable, transform_type=r.transform_type, transform_params=r.transform_params,
            condition_variable=r.condition_variable, condition_operator=r.condition_operator,
            condition_value=r.condition_value, true_value=r.true_value, false_value=r.false_value,
        ))
    if data.auth and data.auth.auth_type != "none":
        db.add(TestCaseAuth(
            test_case_id=case_id, auth_type=data.auth.auth_type,
            token=data.auth.token, username=data.auth.username, password=data.auth.password,
            api_key_name=data.auth.api_key_name, api_key_value=data.auth.api_key_value, api_key_location=data.auth.api_key_location,
        ))


def _delete_children(db: Session, case_id: int):
    """删除用例的所有子表记录"""
    db.query(TestCaseHeader).filter(TestCaseHeader.test_case_id == case_id).delete()
    db.query(TestCaseQueryParam).filter(TestCaseQueryParam.test_case_id == case_id).delete()
    db.query(TestCaseBodyForm).filter(TestCaseBodyForm.test_case_id == case_id).delete()
    db.query(TestCaseBodyRaw).filter(TestCaseBodyRaw.test_case_id == case_id).delete()
    db.query(TestCaseAssertion).filter(TestCaseAssertion.test_case_id == case_id).delete()
    db.query(TestCaseDataRule).filter(TestCaseDataRule.test_case_id == case_id).delete()
    db.query(TestCaseAuth).filter(TestCaseAuth.test_case_id == case_id).delete()


# ============================================================
# 列表
# ============================================================

@router.get("", response_model=List[APITestCaseInDB])
def list_test_cases(
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    module: Optional[str] = None,
    keyword: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:read"))
):
    query = db.query(APITestCase).options(
        joinedload(APITestCase.environment)
    ).filter(
        ~APITestCase.name.like("__module_placeholder_%")
    )

    if project_id:
        query = query.filter(APITestCase.project_id == project_id)
    if module:
        query = query.filter(
            or_(APITestCase.module == module, APITestCase.module.like(f"{module}/%"))
        )
    if keyword:
        query = query.filter(
            or_(
                APITestCase.name.contains(keyword),
                APITestCase.case_number.contains(keyword),
                APITestCase.description.contains(keyword),
            )
        )
    if priority:
        query = query.filter(APITestCase.priority == priority)
    if status:
        query = query.filter(APITestCase.status == status)

    cases = query.order_by(APITestCase.id.desc()).offset(skip).limit(limit).all()
    return [_load_nested(c) for c in cases]


# ============================================================
# 创建
# ============================================================

@router.post("", response_model=APITestCaseInDB)
def create_test_case(
    case_in: APITestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    case_number = generate_case_number(db, case_in.project_id, case_in.module or "")

    data = case_in.model_dump(exclude={"headers", "query_params", "body_form", "body_raw", "assertions", "data_rules", "auth"})
    test_case = APITestCase(**data, case_number=case_number, creator_id=current_user.id)
    db.add(test_case)
    db.flush()

    _create_children(db, test_case.id, case_in)
    db.commit()
    db.refresh(test_case)
    return _load_nested(test_case)


# ============================================================
# 详情
# ============================================================

@router.get("/templates")
def list_templates():
    return get_templates()


@router.post("/import-curl")
def import_curl(req: CurlImportRequest):
    try:
        result = parse_curl(req.curl_command)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 模块管理
# ============================================================

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

    tree = {}
    for proj_id, module in results:
        if proj_id not in tree:
            tree[proj_id] = set()
        if module:
            tree[proj_id].add(module)

    tree_list = []
    for proj_id, modules in tree.items():
        tree_list.append({
            "project_id": proj_id,
            "modules": sorted(list(modules))
        })

    return tree_list


@router.post("/modules")
def create_module(
    data: CreateModuleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    from models import Project
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    existing = db.query(APITestCase).filter(
        APITestCase.project_id == data.project_id,
        APITestCase.module == data.module
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Module already exists")

    placeholder = APITestCase(
        project_id=data.project_id,
        module=data.module,
        name=f"__module_placeholder_{data.module}__",
        method="GET",
        url="",
        priority="P2",
        status="draft",
        creator_id=current_user.id
    )
    db.add(placeholder)
    db.commit()

    return {"message": "Module created successfully"}


@router.delete("/modules")
def delete_module(
    project_id: int,
    module: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    # 删除占位用例
    placeholder = db.query(APITestCase).filter(
        APITestCase.project_id == project_id,
        APITestCase.name == f"__module_placeholder_{module}__"
    ).first()

    if placeholder:
        db.delete(placeholder)

    # 删除该模块及其子模块下的所有真实用例
    real_cases = db.query(APITestCase).filter(
        APITestCase.project_id == project_id,
        or_(
            APITestCase.module == module,
            APITestCase.module.like(f"{module}/%")
        )
    ).all()

    deleted_count = 0
    for case in real_cases:
        db.delete(case)
        deleted_count += 1

    db.commit()

    return {"message": f"Module deleted, {deleted_count} test cases removed"}


@router.put("/modules")
def rename_module(
    data: RenameModuleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    # 查询旧模块下的所有用例（含子模块）
    cases = db.query(APITestCase).filter(
        APITestCase.project_id == data.project_id,
        or_(
            APITestCase.module == data.old_module,
            APITestCase.module.like(f"{data.old_module}/%")
        )
    ).all()

    if not cases:
        raise HTTPException(status_code=404, detail="Module not found")

    # 检查新模块是否已存在
    new_exists = db.query(APITestCase).filter(
        APITestCase.project_id == data.project_id,
        or_(
            APITestCase.module == data.new_module,
            APITestCase.module.like(f"{data.new_module}/%")
        )
    ).first()
    if new_exists:
        raise HTTPException(status_code=400, detail="Target module already exists")

    # 级联更新 module 字段
    for case in cases:
        if case.module == data.old_module:
            case.module = data.new_module
        else:
            # 子模块：替换前缀
            suffix = case.module[len(data.old_module):]
            case.module = data.new_module + suffix

        # 更新占位用例的 name
        if case.name.startswith(f"__module_placeholder_{data.old_module}"):
            case.name = f"__module_placeholder_{data.new_module}__"

    db.commit()
    return {"message": f"Module renamed, {len(cases)} records updated"}


# ============================================================
# 单个用例操作（放在 /modules 之后避免路由冲突）
# ============================================================

@router.get("/{case_id}", response_model=APITestCaseInDB)
def get_test_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:read"))
):
    test_case = db.query(APITestCase).options(
        joinedload(APITestCase.headers),
        joinedload(APITestCase.query_params),
        joinedload(APITestCase.body_form),
        joinedload(APITestCase.body_raw),
        joinedload(APITestCase.assertions),
        joinedload(APITestCase.data_rules),
        joinedload(APITestCase.auth),
    ).filter(APITestCase.id == case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    return _load_nested(test_case)


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

    # 更新主表字段
    main_fields = case_in.model_dump(exclude={"headers", "query_params", "body_form", "body_raw", "assertions", "data_rules", "auth"}, exclude_unset=True)
    for field, value in main_fields.items():
        setattr(test_case, field, value)

    # 如果传了子表数据，删除旧的并重新创建
    has_nested = any(
        getattr(case_in, f) is not None
        for f in ("headers", "query_params", "body_form", "body_raw", "assertions", "data_rules", "auth")
    )
    if has_nested:
        _delete_children(db, test_case.id)
        # 构造一个Create对象来复用_create_children
        create_data = APITestCaseCreate(
            project_id=test_case.project_id,
            name=test_case.name,
            method=test_case.method,
            url=test_case.url,
            headers=case_in.headers or [],
            query_params=case_in.query_params or [],
            body_form=case_in.body_form or [],
            body_raw=case_in.body_raw,
            assertions=case_in.assertions or [],
            data_rules=case_in.data_rules or [],
            auth=case_in.auth,
        )
        _create_children(db, test_case.id, create_data)

    db.commit()
    db.refresh(test_case)
    return _load_nested(test_case)


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


@router.post("/batch-delete")
def batch_delete(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    deleted_count = db.query(APITestCase).filter(APITestCase.id.in_(
        request.case_ids)).delete(synchronize_session=False)
    db.commit()
    return {"message": f"Successfully deleted {deleted_count} test cases"}


@router.post("/{case_id}/copy", response_model=APITestCaseInDB)
def copy_test_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    original = db.query(APITestCase).options(
        joinedload(APITestCase.headers),
        joinedload(APITestCase.query_params),
        joinedload(APITestCase.body_form),
        joinedload(APITestCase.body_raw),
        joinedload(APITestCase.assertions),
        joinedload(APITestCase.data_rules),
        joinedload(APITestCase.auth),
    ).filter(APITestCase.id == case_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Test case not found")

    case_number = generate_case_number(db, original.project_id, original.module or "")

    new_case = APITestCase(
        project_id=original.project_id,
        environment_id=original.environment_id,
        case_number=case_number,
        module=original.module,
        name=f"{original.name} (副本)",
        description=original.description,
        preconditions=original.preconditions,
        remark=original.remark,
        method=original.method,
        url=original.url,
        body_type=original.body_type,
        auth_type=original.auth_type,
        setup_script=original.setup_script,
        teardown_script=original.teardown_script,
        priority=original.priority,
        status=original.status,
        creator_id=current_user.id,
    )
    db.add(new_case)
    db.flush()

    # 复制子表
    for h in (original.headers or []):
        db.add(TestCaseHeader(test_case_id=new_case.id, enabled=h.enabled, key=h.key, value=h.value, description=h.description, sort_order=h.sort_order))
    for p in (original.query_params or []):
        db.add(TestCaseQueryParam(test_case_id=new_case.id, enabled=p.enabled, key=p.key, value=p.value, description=p.description, sort_order=p.sort_order))
    for f in (original.body_form or []):
        db.add(TestCaseBodyForm(test_case_id=new_case.id, enabled=f.enabled, key=f.key, value=f.value, param_type=f.param_type, description=f.description, sort_order=f.sort_order))
    if original.body_raw:
        db.add(TestCaseBodyRaw(test_case_id=new_case.id, content=original.body_raw.content))
    for a in (original.assertions or []):
        db.add(TestCaseAssertion(test_case_id=new_case.id, assertion_type=a.assertion_type, operator=a.operator, field=a.field, expected=a.expected, description=a.description, sort_order=a.sort_order))
    for r in (original.data_rules or []):
        db.add(TestCaseDataRule(
            test_case_id=new_case.id, name=r.name, rule_type=r.rule_type, enabled=r.enabled,
            description=r.description, default_value=r.default_value, sort_order=r.sort_order,
            source=r.source, expression=r.expression, static_value=r.static_value,
            generator=r.generator, generator_params=r.generator_params,
            source_variable=r.source_variable, transform_type=r.transform_type, transform_params=r.transform_params,
            condition_variable=r.condition_variable, condition_operator=r.condition_operator,
            condition_value=r.condition_value, true_value=r.true_value, false_value=r.false_value,
        ))
    if original.auth:
        db.add(TestCaseAuth(
            test_case_id=new_case.id, auth_type=original.auth.auth_type,
            token=original.auth.token, username=original.auth.username, password=original.auth.password,
            api_key_name=original.auth.api_key_name, api_key_value=original.auth.api_key_value, api_key_location=original.auth.api_key_location,
        ))

    db.commit()
    db.refresh(new_case)
    return _load_nested(new_case)


# ============================================================
# Excel 批量导入
# ============================================================

@router.post("/import-excel", response_model=ExcelImportResult)
def import_excel(
    req: ExcelImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    """Excel 批量导入用例"""
    from models import Project

    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    result = import_excel_cases(
        db=db,
        cases=req.cases,
        project_id=req.project_id,
        creator_id=current_user.id,
    )

    return result
