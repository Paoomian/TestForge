from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models.user import User
from models.ai_skill import AISkill
from models.ai_generate import AIGenerateTask
from schemas.ai_skill import AISkillCreate, AISkillUpdate, AISkillOut
from core.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=List[AISkillOut])
async def get_skills(
    generate_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的技能列表"""
    query = db.query(AISkill).filter(AISkill.user_id == current_user.id)
    if generate_type:
        query = query.filter(AISkill.generate_type == generate_type)
    return query.order_by(AISkill.is_default.desc(), AISkill.created_at.desc()).all()


@router.post("/", response_model=AISkillOut)
async def create_skill(
    data: AISkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建技能"""
    if "{input_content}" not in data.user_prompt:
        raise HTTPException(status_code=400, detail="User Prompt 必须包含 {input_content} 占位符")

    # 如果设为默认，取消同类型其他默认
    if data.is_default:
        db.query(AISkill).filter(
            AISkill.user_id == current_user.id,
            AISkill.generate_type == data.generate_type,
            AISkill.is_default == True
        ).update({"is_default": False})

    skill = AISkill(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        generate_type=data.generate_type,
        system_prompt=data.system_prompt,
        user_prompt=data.user_prompt,
        is_default=data.is_default
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.put("/{skill_id}", response_model=AISkillOut)
async def update_skill(
    skill_id: int,
    data: AISkillUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新技能"""
    skill = db.query(AISkill).filter(
        AISkill.id == skill_id,
        AISkill.user_id == current_user.id
    ).first()
    if not skill:
        raise HTTPException(status_code=404, detail="技能不存在")

    if data.user_prompt is not None and "{input_content}" not in data.user_prompt:
        raise HTTPException(status_code=400, detail="User Prompt 必须包含 {input_content} 占位符")

    # 如果设为默认，取消同类型其他默认
    if data.is_default:
        generate_type = data.generate_type or skill.generate_type
        db.query(AISkill).filter(
            AISkill.user_id == current_user.id,
            AISkill.generate_type == generate_type,
            AISkill.is_default == True,
            AISkill.id != skill_id
        ).update({"is_default": False})

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(skill, key, value)

    db.commit()
    db.refresh(skill)
    return skill


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除技能"""
    skill = db.query(AISkill).filter(
        AISkill.id == skill_id,
        AISkill.user_id == current_user.id
    ).first()
    if not skill:
        raise HTTPException(status_code=404, detail="技能不存在")

    # 先解除引用该技能的任务关联
    db.query(AIGenerateTask).filter(AIGenerateTask.skill_id == skill_id).update({"skill_id": None})

    db.delete(skill)
    db.commit()
    return {"message": "已删除"}


@router.post("/init-defaults")
async def init_default_skills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """初始化默认技能模板"""
    # 检查是否已有默认技能
    existing = db.query(AISkill).filter(AISkill.user_id == current_user.id).first()
    if existing:
        return {"message": "已有技能数据，跳过初始化"}

    # 新模式：system_prompt 是完整的 Prompt 模板（含 {input_content} 占位符），user_prompt 为空
    defaults = [
        {
            "name": "功能测试专家",
            "description": "根据需求文档生成功能测试用例，覆盖正常/异常/边界值/组合/后端验证",
            "generate_type": "functional",
            "system_prompt": '你是一个资深的测试工程师，擅长根据需求文档生成功能测试用例。\n\n## 核心原则\n需求文档中的每一条功能描述、校验规则、约束条件都必须至少有一条对应的测试用例（可追溯）。\n\n## 必须覆盖的测试类型（5种，缺一不可）\n1. normal - 正常流程（happy path）\n2. exception - 异常流程（每个校验规则至少一个违反场景）\n3. boundary - 边界值（每个数值/长度/时间边界必须包含：最小值-1、最小值、最大值、最大值+1，写出具体数值，禁止用"超过""不足"等模糊描述，时间边界精确到秒，优先级至少P1）\n4. combination - 组合测试（必须使用 Pairwise 方法，至少8条，必须包含参数表和组合矩阵）\n5. backend_ui - 后端一致性验证（通过UI触发并用Network面板验证后端响应，至少3条，优先级至少P1）\n\n## 领域专长\n- 熟悉等价类划分、边界值分析、因果图、Pairwise等测试设计方法\n- 关注安全性：SQL注入、XSS、信息泄露、暴力破解防护\n- 关注数据一致性：状态流转、并发操作、超时机制\n- 关注用户体验：输入保留、错误提示友好性、键盘快捷键\n\n## 输出质量要求\n- 用例名称简洁明确，不带编号\n- 前置条件具体到数据库级别的可验证状态\n- 测试步骤可由初级测试工程师直接执行\n- 预期结果只描述系统响应，不描述操作\n\n请根据以下需求文档生成测试用例：\n\n{input_content}',
            "user_prompt": "",
            "is_default": True
        },
        {
            "name": "接口测试专家",
            "description": "根据接口文档生成接口测试用例，包含正向、参数校验、边界值用例",
            "generate_type": "api",
            "system_prompt": '你是一个接口测试专家，擅长根据接口文档生成接口测试用例。\n\n## 核心原则\n每个接口的每种请求方式、参数组合、错误场景都必须有对应用例。\n\n## 必须覆盖的测试类型\n1. 正向用例：正常请求成功\n2. 参数校验：必填缺失、类型错误、格式错误\n3. 边界值：数值边界、长度边界\n4. 认证鉴权：无token、过期token、无权限\n\n## 输出质量要求\n- 用例名称简洁明确\n- 断言覆盖状态码、关键字段、响应时间\n- 请求配置完整（method、url、headers、body）\n\n请根据以下接口文档生成测试用例：\n\n{input_content}',
            "user_prompt": "",
            "is_default": True
        }
    ]

    for data in defaults:
        skill = AISkill(user_id=current_user.id, **data)
        db.add(skill)

    db.commit()
    return {"message": f"已初始化 {len(defaults)} 个默认技能"}
