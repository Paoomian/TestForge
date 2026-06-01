from sqlalchemy.orm import Session

from models.api_test_case import APITestCase
from models.test_case_header import TestCaseHeader
from models.test_case_query_param import TestCaseQueryParam
from models.test_case_body import TestCaseBodyRaw, TestCaseBodyForm
from models.test_case_assertion import TestCaseAssertion
from models.test_case_data_rule import TestCaseDataRule
from schemas.excel_import import ExcelCaseItem, ExcelImportResult, ImportError
from core.case_number import generate_case_number


# 有效枚举值
VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}
VALID_BODY_TYPES = {"none", "form-data", "x-www-form-urlencoded", "raw-json", "raw-xml", "raw-text"}
VALID_ASSERTION_TYPES = {"status_code", "jsonpath", "header", "response_time", "body_contains"}
VALID_ASSERTION_OPERATORS = {
    "equals", "not_equals",
    "contains", "not_contains",
    "greater_than", "less_than",
    "greater_than_or_equals", "less_than_or_equals",
    "regex",
    "exists", "not_exists",
    "is_type",
    "length_equals", "length_greater_than", "length_less_than"
}
VALID_EXTRACT_SOURCES = {"jsonpath", "regex", "header"}


def validate_case_item(case: ExcelCaseItem, row: int) -> str | None:
    """校验单条用例数据，返回错误信息或 None"""
    if not case.name or len(case.name) > 200:
        return "用例名称无效（必填，最大200字符）"

    if case.method.upper() not in VALID_METHODS:
        return f"请求方法无效：{case.method}（有效值：{', '.join(VALID_METHODS)}）"

    if not case.url:
        return "请求URL不能为空"

    if case.priority and case.priority not in VALID_PRIORITIES:
        return f"优先级无效：{case.priority}（有效值：{', '.join(VALID_PRIORITIES)}）"

    if case.body_type and case.body_type not in VALID_BODY_TYPES:
        return f"Body类型无效：{case.body_type}（有效值：{', '.join(VALID_BODY_TYPES)}）"

    # 校验断言
    for i, assertion in enumerate(case.assertions):
        if assertion.assertion_type not in VALID_ASSERTION_TYPES:
            return f"断言{i+1}类型无效：{assertion.assertion_type}"
        if assertion.operator not in VALID_ASSERTION_OPERATORS:
            return f"断言{i+1}运算符无效：{assertion.operator}"

    # 校验数据规则（提取类型）
    for i, rule in enumerate(case.data_rules):
        if rule.rule_type == "extract":
            if not rule.name:
                return f"数据规则{i+1}变量名不能为空"
            if rule.source and rule.source not in VALID_EXTRACT_SOURCES:
                return f"数据规则{i+1}来源无效：{rule.source}（有效值：{', '.join(VALID_EXTRACT_SOURCES)}）"
            if not rule.expression:
                return f"数据规则{i+1}表达式不能为空"

    return None


def create_case_from_excel(
    db: Session,
    case: ExcelCaseItem,
    project_id: int,
    creator_id: int,
) -> APITestCase:
    """从 Excel 数据创建用例"""
    # 生成用例编号
    case_number = generate_case_number(db, project_id, case.module or "DEFAULT")

    # 创建主表记录
    db_case = APITestCase(
        project_id=project_id,
        case_number=case_number,
        name=case.name,
        method=case.method.upper(),
        url=case.url,
        module=case.module,
        priority=case.priority or "P2",
        description=case.description,
        preconditions=case.preconditions,
        body_type=case.body_type or "none",
        remark=case.remark,
        creator_id=creator_id,
    )
    db.add(db_case)
    db.flush()  # 获取 ID

    # 创建 Headers
    for i, header in enumerate(case.headers):
        if header.key:  # 跳过空行
            db.add(TestCaseHeader(
                test_case_id=db_case.id,
                enabled=header.enabled,
                key=header.key,
                value=header.value,
                description=header.description,
                sort_order=i,
            ))

    # 创建 Query Params
    for i, param in enumerate(case.query_params):
        if param.key:
            db.add(TestCaseQueryParam(
                test_case_id=db_case.id,
                enabled=param.enabled,
                key=param.key,
                value=param.value,
                description=param.description,
                sort_order=i,
            ))

    # 创建 Body Raw（如果 body_type 是 raw 类型）
    if case.body_type and case.body_type.startswith("raw-") and case.body_raw_content:
        db.add(TestCaseBodyRaw(
            test_case_id=db_case.id,
            content=case.body_raw_content,
        ))

    # 创建 Body Form（如果 body_type 是 form-data 或 x-www-form-urlencoded）
    if case.body_type in ("form-data", "x-www-form-urlencoded"):
        for i, form_item in enumerate(case.body_form):
            if form_item.key:  # 跳过空行
                db.add(TestCaseBodyForm(
                    test_case_id=db_case.id,
                    enabled=form_item.enabled,
                    key=form_item.key,
                    value=form_item.value,
                    param_type=form_item.param_type or "text",
                    description=form_item.description,
                    sort_order=i,
                ))

    # 创建断言
    for i, assertion in enumerate(case.assertions):
        db.add(TestCaseAssertion(
            test_case_id=db_case.id,
            assertion_type=assertion.assertion_type,
            operator=assertion.operator,
            field=assertion.field,
            expected=assertion.expected,
            description=assertion.description,
            sort_order=i,
        ))

    # 创建数据规则
    for i, rule in enumerate(case.data_rules):
        db.add(TestCaseDataRule(
            test_case_id=db_case.id,
            name=rule.name,
            rule_type=rule.rule_type or "extract",
            enabled=True,
            source=rule.source,
            expression=rule.expression,
            default_value=rule.default_value,
            description=rule.description,
            sort_order=i,
        ))

    return db_case


def import_excel_cases(
    db: Session,
    cases: list[ExcelCaseItem],
    project_id: int,
    creator_id: int,
) -> ExcelImportResult:
    """批量导入用例"""
    total = len(cases)
    success = 0
    failed = 0
    created_ids = []
    errors = []

    for i, case in enumerate(cases):
        row = i + 2  # Excel 行号从 2 开始（第 1 行是表头）

        # 校验
        error = validate_case_item(case, row)
        if error:
            failed += 1
            errors.append(ImportError(row=row, name=case.name or f"第{row}行", error=error))
            continue

        try:
            # 创建用例
            db_case = create_case_from_excel(db, case, project_id, creator_id)
            success += 1
            created_ids.append(db_case.id)
        except Exception as e:
            failed += 1
            errors.append(ImportError(row=row, name=case.name, error=str(e)))

    # 提交事务
    if success > 0:
        db.commit()

    return ExcelImportResult(
        total=total,
        success=success,
        failed=failed,
        created_ids=created_ids,
        errors=errors,
    )
