from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.project import ProjectCreate, ProjectUpdate, ProjectInDB
from models import Project
from models.environment import Environment
from models.test_suite import TestSuite
from models.test_run import TestRun, TestRunDetail
from models.api_test_case import APITestCase
from models.ai_generate import AIGenerateTask
from core.deps import get_current_user, check_permission
from models import User

router = APIRouter()


@router.get("", response_model=List[ProjectInDB])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("project:read"))
):
    projects = db.query(Project).offset(skip).limit(limit).all()
    return projects


@router.post("", response_model=ProjectInDB)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("project:write"))
):
    project = Project(**project_in.model_dump(), creator_id=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectInDB)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("project:read"))
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectInDB)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("project:write"))
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for field, value in project_in.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("project:write"))
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 获取该项目下所有环境ID
    env_ids = [e.id for e in db.query(Environment.id).filter(Environment.project_id == project_id).all()]

    if env_ids:
        # 解除 test_suites/test_runs/api_test_cases 对环境的引用
        db.query(TestSuite).filter(TestSuite.environment_id.in_(env_ids)).update(
            {"environment_id": None}, synchronize_session=False
        )
        db.query(TestRun).filter(TestRun.environment_id.in_(env_ids)).update(
            {"environment_id": None}, synchronize_session=False
        )
        db.query(APITestCase).filter(APITestCase.environment_id.in_(env_ids)).update(
            {"environment_id": None}, synchronize_session=False
        )

    # 删除关联的 test_runs（含 details）和 test_suites
    run_ids = [r.id for r in db.query(TestRun.id).filter(TestRun.project_id == project_id).all()]
    if run_ids:
        db.query(TestRunDetail).filter(TestRunDetail.test_run_id.in_(run_ids)).delete(synchronize_session=False)
    db.query(TestRun).filter(TestRun.project_id == project_id).delete(synchronize_session=False)
    db.query(TestSuite).filter(TestSuite.project_id == project_id).delete(synchronize_session=False)

    # 解除 AI 生成任务对项目的引用
    db.query(AIGenerateTask).filter(AIGenerateTask.project_id == project_id).update(
        {"project_id": None}, synchronize_session=False
    )

    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}
