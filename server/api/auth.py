from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas.auth import UserLogin, Token, UserCreate, UserInDB
from core.auth import login_user, create_user
from core.deps import get_current_user
from models import User

router = APIRouter()


@router.post("/login", response_model=Token)
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    return login_user(db, user_login.username, user_login.password)


@router.post("/register", response_model=UserInDB)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user_in)


@router.get("/me", response_model=UserInDB)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Successfully logged out"}
