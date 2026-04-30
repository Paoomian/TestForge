from sqlalchemy import Column, Integer, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class APITestCaseHistory(Base):
    __tablename__ = "api_test_case_histories"

    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("api_test_cases.id"), nullable=False)
    version = Column(Integer, nullable=False)

    # 快照所有字段
    snapshot = Column(JSON, nullable=False)

    # 变更信息
    change_description = Column(Text)
    changed_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    test_case = relationship("APITestCase", back_populates="histories")
    user = relationship("User")
