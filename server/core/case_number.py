from sqlalchemy.orm import Session
from sqlalchemy import func
from models.api_test_case import APITestCase


def generate_case_number(db: Session, project_id: int, module: str) -> str:
    if module:
        module_code = module.split("/")[0].upper()[:6]
    else:
        module_code = "DEFAULT"

    prefix = f"TC-{module_code}-"

    max_seq = db.query(
        func.max(APITestCase.case_number)
    ).filter(
        APITestCase.project_id == project_id,
        APITestCase.case_number.like(f"{prefix}%")
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
