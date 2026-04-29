from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.api_case import APICaseCreate, APICaseUpdate, APICaseInDB, APIDebugRequest
from models import APICase
from core.deps import get_current_user, check_permission
from models import User
import httpx
import json

router = APIRouter()


@router.get("/", response_model=List[APICaseInDB])
def list_api_cases(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:read"))
):
    cases = db.query(APICase).filter(APICase.project_id == project_id).offset(skip).limit(limit).all()
    return cases


@router.post("/", response_model=APICaseInDB)
def create_api_case(
    case_in: APICaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    case = APICase(**case_in.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("/{case_id}", response_model=APICaseInDB)
def get_api_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:read"))
):
    case = db.query(APICase).filter(APICase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="API case not found")
    return case


@router.put("/{case_id}", response_model=APICaseInDB)
def update_api_case(
    case_id: int,
    case_in: APICaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    case = db.query(APICase).filter(APICase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="API case not found")

    for field, value in case_in.model_dump(exclude_unset=True).items():
        setattr(case, field, value)

    db.commit()
    db.refresh(case)
    return case


@router.delete("/{case_id}")
def delete_api_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission("api_test:write"))
):
    case = db.query(APICase).filter(APICase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="API case not found")

    db.delete(case)
    db.commit()
    return {"message": "API case deleted successfully"}


@router.post("/debug")
async def debug_api(
    request: APIDebugRequest,
    current_user: User = Depends(check_permission("debug:use"))
):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            body_data = None
            if request.body:
                if request.body_type == "json":
                    body_data = json.loads(request.body)
                else:
                    body_data = request.body

            response = await client.request(
                method=request.method.value,
                url=request.url,
                headers=request.headers,
                params=request.query_params,
                json=body_data if request.body_type == "json" else None,
                data=body_data if request.body_type != "json" else None
            )

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
                "elapsed": response.elapsed.total_seconds()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
