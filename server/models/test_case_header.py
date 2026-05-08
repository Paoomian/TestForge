from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from database import Base


class TestCaseHeader(Base):
    __tablename__ = "test_case_headers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    test_case_id = Column(Integer, ForeignKey("api_test_cases.id", ondelete="CASCADE"), nullable=False)
    enabled = Column(Boolean, default=True)
    key = Column(String(200), nullable=False)
    value = Column(Text)
    description = Column(String(500))
    sort_order = Column(Integer, default=0)
