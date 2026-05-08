from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.api_test_case import EnvironmentCreate, EnvironmentUpdate, EnvironmentInDB
from models import Environment, User
from core.deps import get_current_user, check_permission

router = APIRouter()


@router.get("", response_model=List[EnvironmentInDB])
def list_environments(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:read"))
):
    return db.query(Environment).filter(Environment.project_id == project_id).all()


@router.post("", response_model=EnvironmentInDB)
def create_environment(
    env_in: EnvironmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    env = Environment(**env_in.model_dump())
    db.add(env)
    db.commit()
    db.refresh(env)
    return env


@router.put("/{env_id}", response_model=EnvironmentInDB)
def update_environment(
    env_id: int,
    env_in: EnvironmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    env = db.query(Environment).filter(Environment.id == env_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    for field, value in env_in.model_dump(exclude_unset=True).items():
        setattr(env, field, value)

    db.commit()
    db.refresh(env)
    return env


@router.delete("/{env_id}")
def delete_environment(
    env_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    env = db.query(Environment).filter(Environment.id == env_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")

    db.delete(env)
    db.commit()
    return {"message": "Environment deleted successfully"}
