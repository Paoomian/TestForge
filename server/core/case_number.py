from sqlalchemy.orm import Session
from sqlalchemy import func


def generate_case_number(db: Session, project_id: int, module: str, model_class=None) -> str:
    """生成用例编号，支持接口用例和UI用例"""
    if model_class is None:
        from models.api_test_case import APITestCase
        model_class = APITestCase

    if module:
        module_code = module.split("/")[0].upper()[:6]
    else:
        module_code = "DEFAULT"

    # UI用例使用 UI- 前缀，接口用例使用 TC- 前缀
    from models.ui_case import UICase
    if model_class == UICase:
        prefix = f"UI-{module_code}-"
    else:
        prefix = f"TC-{module_code}-"

    max_seq = db.query(
        func.max(model_class.case_number)
    ).filter(
        model_class.project_id == project_id,
        model_class.case_number.like(f"{prefix}%")
    ).scalar()

    if max_seq:
        try:
            last_num = int(max_seq.split("-")[-1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = 1
    else:
        next_num = 1

    return f"{prefix}{next_num:04d}"
