from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base


class HTTPMethod(str, enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class APICase(Base):
    __tablename__ = "api_cases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    method = Column(Enum(HTTPMethod), nullable=False)
    url = Column(String(500), nullable=False)
    headers = Column(JSON, default=dict)
    query_params = Column(JSON, default=dict)
    body = Column(Text, nullable=True)
    body_type = Column(String(50), default="json")
    pre_script = Column(Text, nullable=True)
    post_script = Column(Text, nullable=True)
    assertions = Column(JSON, default=list)
    extract_vars = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", back_populates="api_cases")
