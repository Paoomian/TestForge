from sqlalchemy.orm import Session
from core.auth import init_roles, create_user
from core.security import get_password_hash
from models import User, Role
from schemas.auth import UserCreate
from database import SessionLocal, engine, Base
from core.config import settings


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        init_roles(db)

        admin_user = db.query(User).filter(User.email == settings.FIRST_SUPERUSER_EMAIL).first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email=settings.FIRST_SUPERUSER_EMAIL,
                password_hash=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                is_superuser=True,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            admin_role = db.query(Role).filter(Role.name == "admin").first()
            if admin_role:
                admin_user.roles.append(admin_role)
                db.commit()

            print("Admin user created successfully")
            print(f"Email: {settings.FIRST_SUPERUSER_EMAIL}")
            print(f"Password: {settings.FIRST_SUPERUSER_PASSWORD}")
        else:
            print("Admin user already exists")

    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")
