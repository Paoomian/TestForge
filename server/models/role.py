from sqlalchemy import Column, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, default=list)

    users = relationship("User", secondary="user_roles", back_populates="roles")
