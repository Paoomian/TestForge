from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from database import get_db
from schemas.auth import UserLogin, Token, TokenPayload, UserCreate, UserInDB
from core.auth import login_user, create_user
from core.config import settings
from core.security import create_access_token, create_refresh_token
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


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """用refresh_token换取新的access_token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 解析refresh_token
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)

        # 验证token类型必须是refresh
        if token_data.sub is None or token_data.type != "refresh":
            raise credentials_exception

        user_id = int(token_data.sub)
    except (JWTError, ValueError):
        raise credentials_exception

    # 验证用户存在且有效
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception

    # 生成新的token对
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )
