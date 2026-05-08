from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from database import Base


class TestCaseBodyForm(Base):
    __tablename__ = "test_case_body_form"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    test_case_id = Column(Integer, ForeignKey("api_test_cases.id", ondelete="CASCADE"), nullable=False)
    enabled = Column(Boolean, default=True)
    key = Column(String(200), nullable=False)
    value = Column(Text)
    param_type = Column(String(20), default="text")  # text / file
    description = Column(String(500))
    sort_order = Column(Integer, default=0)


class TestCaseBodyRaw(Base):
    __tablename__ = "test_case_body_raw"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    test_case_id = Column(Integer, ForeignKey("api_test_cases.id", ondelete="CASCADE"), unique=True, nullable=False)
    content = Column(Text)
