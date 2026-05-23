from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class AISkill(Base):
    """AI 技能（Prompt 模板）"""
    __tablename__ = "ai_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), default="")
    generate_type = Column(String(20), nullable=False)  # functional / api
    system_prompt = Column(Text, nullable=False)
    user_prompt = Column(Text, nullable=False)  # 必须包含 {input_content} 占位符
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    user = relationship("User")
