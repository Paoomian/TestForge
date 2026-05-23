from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class AIProviderConfig(Base):
    """用户 AI 模型配置"""
    __tablename__ = "ai_provider_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # claude / openai / deepseek / custom
    api_key = Column(String(500), nullable=False)  # 加密存储
    model_name = Column(String(100), nullable=False)  # claude-3-opus / gpt-4 / etc
    api_base_url = Column(String(500), nullable=True)  # 自定义 API 地址（中转站）
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="ai_configs")


class AIGenerateTask(Base):
    """AI 生成任务"""
    __tablename__ = "ai_generate_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)

    # 输入配置
    input_type = Column(String(20), nullable=False)  # prd / swagger / text
    input_content = Column(Text)  # 原始输入内容（文本类型或解析后的 JSON）
    input_file_path = Column(String(500))  # 上传文件路径
    input_file_name = Column(String(200))  # 原始文件名

    # 生成配置
    generate_type = Column(String(20), nullable=False)  # functional / api
    skill_id = Column(Integer, ForeignKey("ai_skills.id"), nullable=True, index=True)  # 使用的技能
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    target_count = Column(Integer, default=10)

    # 任务状态
    status = Column(String(20), default="pending", index=True)  # pending / processing / completed / failed / cancelled
    progress = Column(Integer, default=0)
    error_message = Column(Text)

    # 结果
    generated_cases = Column(JSON)  # 生成的用例数据
    cases_count = Column(Integer, default=0)

    # 审计
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    # 关系
    user = relationship("User")
    project = relationship("Project")
