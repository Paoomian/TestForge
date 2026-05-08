from sqlalchemy import Column, Integer, String, Text, ForeignKey
from database import Base


class TestCaseAuth(Base):
    __tablename__ = "test_case_auth"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    test_case_id = Column(Integer, ForeignKey("api_test_cases.id", ondelete="CASCADE"), unique=True, nullable=False)
    auth_type = Column(String(20), nullable=False, default="none")  # none/bearer/basic/api_key
    token = Column(Text)
    username = Column(String(200))
    password = Column(String(200))
    api_key_name = Column(String(200))
    api_key_value = Column(Text)
    api_key_location = Column(String(20))  # header / query
