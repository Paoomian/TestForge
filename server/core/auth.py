from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models import User, Role
from core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from schemas.auth import UserCreate, Token


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_user(db: Session, user_in: UserCreate) -> User:
    existing_user = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    db_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def login_user(db: Session, username: str, password: str) -> Token:
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user.last_login = datetime.utcnow()
    db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


def init_roles(db: Session):
    roles_data = [
        {
            "name": "admin",
            "description": "Administrator with full access",
            "permissions": ["*"]
        },
        {
            "name": "tester",
            "description": "Tester with test execution permissions",
            "permissions": [
                "ui_test:read", "ui_test:write", "ui_test:execute",
                "api_test:read", "api_test:write", "api_test:execute",
                "debug:use", "project:read", "project:write"
            ]
        },
        {
            "name": "viewer",
            "description": "Viewer with read-only access",
            "permissions": ["*:read"]
        }
    ]

    for role_data in roles_data:
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing_role:
            role = Role(**role_data)
            db.add(role)

    db.commit()
