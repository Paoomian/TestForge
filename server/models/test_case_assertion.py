from sqlalchemy import Column, Integer, String, Text, ForeignKey
from database import Base


class TestCaseAssertion(Base):
    __tablename__ = "test_case_assertions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    test_case_id = Column(Integer, ForeignKey("api_test_cases.id", ondelete="CASCADE"), nullable=False)
    assertion_type = Column(String(30), nullable=False)  # status_code/response_time/jsonpath/header/body_contains
    operator = Column(String(20), nullable=False)  # equals/not_equals/contains/greater_than/less_than/regex/exists
    field = Column(String(500))  # jsonpath expression, header name, etc.
    expected = Column(Text)
    description = Column(String(500))
    sort_order = Column(Integer, default=0)
