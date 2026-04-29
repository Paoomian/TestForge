from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.ui_case import UICaseCreate, UICaseUpdate, UICaseInDB
from models import UICase
from core.deps import get_current_user, check_permission
from models import User

router = APIRouter()


@router.get("/", response_model=List[UICaseInDB])
def list_ui_cases(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:read"))
):
    cases = db.query(UICase).filter(UICase.project_id == project_id).offset(skip).limit(limit).all()
    return cases


@router.post("/", response_model=UICaseInDB)
def create_ui_case(
    case_in: UICaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("ui_test:write"))
):
    case = UICase(**case_in.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


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
