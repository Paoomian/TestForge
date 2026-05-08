from sqlalchemy import Column, Integer, String, Text, ForeignKey
from database import Base


class TestCaseExtract(Base):
    __tablename__ = "test_case_extracts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    test_case_id = Column(Integer, ForeignKey("api_test_cases.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)  # variable name
    source = Column(String(30), nullable=False)  # jsonpath/regex/header
    expression = Column(String(1000), nullable=False)
    default_value = Column(Text)
    description = Column(String(500))
    sort_order = Column(Integer, default=0)
