import os
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db, SessionLocal
from models.user import User
from models.ai_generate import AIProviderConfig, AIGenerateTask
from schemas.ai_generate import (
    AIProviderConfigCreate,
    AIProviderConfigUpdate,
    AIProviderConfigOut,
    AIConfigTestResult,
    AIGenerateTaskCreate,
    AIGenerateTaskOut,
    AIGenerateTaskListOut,
    DocumentUploadOut,
    SaveCasesRequest,
    SaveCasesResult,
)
from services.ai_service import AIServiceFactory
from services.document_parser import DocumentParser
from tasks.ai_generate_tasks import generate_test_cases
from core.deps import get_current_user
from utils.crypto import encrypt_api_key, decrypt_api_key
from core.config import settings

router = APIRouter()


def run_generate_sync(task_id: int, config_id: int):
    """同步执行生成任务（Celery 不可用时）"""
    try:
        from tasks.ai_generate_tasks import generate_test_cases
        generate_test_cases(task_id, config_id)
    except Exception as e:
        import traceback
        print(f"[AI生成] 后台任务执行失败 task_id={task_id}: {e}")
        traceback.print_exc()
        # 线程异常时也要更新任务状态
        try:
            db = SessionLocal()
            task = db.query(AIGenerateTask).filter(AIGenerateTask.id == task_id).first()
            if task and task.status not in ("completed", "cancelled"):
                task.status = "failed"
                task.error_message = f"后台执行异常: {str(e)[:300]}"
                db.commit()
            db.close()
        except Exception:
            pass


# ==================== AI 配置管理 ====================

@router.post("/configs", response_model=AIProviderConfigOut)
async def create_ai_config(
    config: AIProviderConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建 AI 配置"""
    # 如果设置为默认，取消其他默认配置
    if config.is_default:
        db.query(AIProviderConfig).filter(
            AIProviderConfig.user_id == current_user.id,
            AIProviderConfig.is_default == True
        ).update({"is_default": False})

    # 创建配置
    db_config = AIProviderConfig(
        user_id=current_user.id,
        provider=config.provider,
        api_key=encrypt_api_key(config.api_key),
        model_name=config.model_name,
        api_base_url=config.api_base_url,
        is_default=config.is_default
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)

    return db_config


@router.get("/configs", response_model=List[AIProviderConfigOut])
async def get_ai_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的所有 AI 配置"""
    configs = db.query(AIProviderConfig).filter(
        AIProviderConfig.user_id == current_user.id
    ).order_by(AIProviderConfig.is_default.desc(), AIProviderConfig.created_at.desc()).all()
    return configs


@router.put("/configs/{config_id}", response_model=AIProviderConfigOut)
async def update_ai_config(
    config_id: int,
    config: AIProviderConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新 AI 配置"""
    db_config = db.query(AIProviderConfig).filter(
        AIProviderConfig.id == config_id,
        AIProviderConfig.user_id == current_user.id
    ).first()

    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 更新字段
    if config.api_key is not None:
        db_config.api_key = encrypt_api_key(config.api_key)
    if config.provider is not None:
        db_config.provider = config.provider
    if config.model_name is not None:
        db_config.model_name = config.model_name
    if config.api_base_url is not None:
        db_config.api_base_url = config.api_base_url
    if config.is_default is not None:
        if config.is_default:
            db.query(AIProviderConfig).filter(
                AIProviderConfig.user_id == current_user.id,
                AIProviderConfig.is_default == True,
                AIProviderConfig.id != config_id
            ).update({"is_default": False})
        db_config.is_default = config.is_default

    db.commit()
    db.refresh(db_config)

    return db_config


@router.delete("/configs/{config_id}")
async def delete_ai_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除 AI 配置"""
    db_config = db.query(AIProviderConfig).filter(
        AIProviderConfig.id == config_id,
        AIProviderConfig.user_id == current_user.id
    ).first()

    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")

    db.delete(db_config)
    db.commit()

    return {"message": "配置已删除"}


@router.post("/configs/{config_id}/test", response_model=AIConfigTestResult)
async def test_ai_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试 AI 配置是否可用"""
    db_config = db.query(AIProviderConfig).filter(
        AIProviderConfig.id == config_id,
        AIProviderConfig.user_id == current_user.id
    ).first()

    if not db_config:
        raise HTTPException(status_code=404, detail="配置不存在")

    try:
        api_key = decrypt_api_key(db_config.api_key)
        provider = AIServiceFactory.create_provider(
            db_config.provider,
            api_key,
            db_config.api_base_url
        )

        # 发送测试请求
        messages = [{"role": "user", "content": "Hi"}]
        response = await provider.chat(messages, db_config.model_name)

        return AIConfigTestResult(success=True, message="配置有效")
    except Exception as e:
        return AIConfigTestResult(success=False, message=str(e))


class FetchModelsRequest(BaseModel):
    """获取模型列表请求"""
    provider: str
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    config_id: Optional[int] = None


@router.post("/fetch-models")
async def fetch_models(
    request: FetchModelsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定端点的可用模型列表"""
    try:
        api_key = request.api_key
        provider_name = request.provider
        api_base_url = request.api_base_url

        # 如果提供了 config_id，从数据库获取配置
        if request.config_id:
            db_config = db.query(AIProviderConfig).filter(
                AIProviderConfig.id == request.config_id,
                AIProviderConfig.user_id == current_user.id
            ).first()
            if not db_config:
                raise HTTPException(status_code=404, detail="配置不存在")
            api_key = decrypt_api_key(db_config.api_key)
            provider_name = db_config.provider
            api_base_url = db_config.api_base_url

        if not api_key:
            raise HTTPException(status_code=400, detail="缺少 API Key")

        provider = AIServiceFactory.create_provider(
            provider_name,
            api_key,
            api_base_url
        )
        models = await provider.list_models()
        return {"models": models}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取模型列表失败: {str(e)}")


# ==================== 文档上传 ====================

@router.post("/upload/prd", response_model=DocumentUploadOut)
async def upload_prd(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传 PRD 文档"""
    # 验证文件类型
    allowed_types = ['.docx', '.pdf', '.md']
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}，支持: {', '.join(allowed_types)}"
        )

    # 保存文件
    upload_dir = os.path.join(settings.AI_FILE_UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 解析文档
    parsed = DocumentParser.parse_prd(file_path)

    # 返回绝对路径，确保 Celery worker 能正确清理文件
    abs_file_path = os.path.abspath(file_path)

    return DocumentUploadOut(
        file_path=abs_file_path,
        file_name=file.filename,
        parsed_content=parsed
    )


@router.post("/upload/swagger", response_model=DocumentUploadOut)
async def upload_swagger(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传 Swagger 文档"""
    # 验证文件类型
    allowed_types = ['.json', '.yaml', '.yml']
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}，支持: {', '.join(allowed_types)}"
        )

    # 保存文件
    upload_dir = os.path.join(settings.AI_FILE_UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 解析文档
    parsed = DocumentParser.parse_swagger(file_path)

    # 返回绝对路径，确保 Celery worker 能正确清理文件
    abs_file_path = os.path.abspath(file_path)

    return DocumentUploadOut(
        file_path=abs_file_path,
        file_name=file.filename,
        parsed_content=parsed
    )


# ==================== 生成任务管理 ====================

@router.post("/tasks", response_model=AIGenerateTaskOut)
async def create_generate_task(
    task: AIGenerateTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建生成任务"""
    # 获取用户的 AI 配置
    if task.config_id:
        db_config = db.query(AIProviderConfig).filter(
            AIProviderConfig.id == task.config_id,
            AIProviderConfig.user_id == current_user.id
        ).first()
    else:
        db_config = db.query(AIProviderConfig).filter(
            AIProviderConfig.user_id == current_user.id,
            AIProviderConfig.is_default == True
        ).first()

    if not db_config:
        raise HTTPException(status_code=400, detail="请先配置 AI 模型")

    # 创建任务
    db_task = AIGenerateTask(
        user_id=current_user.id,
        project_id=task.project_id,
        input_type=task.input_type,
        input_content=task.input_content,
        input_file_path=task.input_file_path,
        input_file_name=task.input_file_name,
        generate_type=task.generate_type,
        skill_id=task.skill_id,
        provider=db_config.provider,
        model_name=db_config.model_name,
        target_count=task.target_count
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # 尝试异步执行生成任务，如果 Celery 不可用则同步执行
    try:
        generate_test_cases.delay(db_task.id, db_config.id)
    except Exception:
        # Celery 不可用，在后台线程中同步执行
        import threading
        thread = threading.Thread(target=run_generate_sync, args=(db_task.id, db_config.id))
        thread.daemon = True
        thread.start()

    return db_task


@router.get("/tasks", response_model=List[AIGenerateTaskListOut])
async def get_generate_tasks(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取生成任务列表"""
    query = db.query(AIGenerateTask).filter(
        AIGenerateTask.user_id == current_user.id
    )

    if project_id:
        query = query.filter(AIGenerateTask.project_id == project_id)
    if status:
        query = query.filter(AIGenerateTask.status == status)

    tasks = query.order_by(AIGenerateTask.created_at.desc()).offset(skip).limit(limit).all()
    return tasks


@router.get("/tasks/{task_id}", response_model=AIGenerateTaskOut)
async def get_generate_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务详情"""
    task = db.query(AIGenerateTask).filter(
        AIGenerateTask.id == task_id,
        AIGenerateTask.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task


@router.delete("/tasks/{task_id}")
async def delete_generate_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除任务"""
    task = db.query(AIGenerateTask).filter(
        AIGenerateTask.id == task_id,
        AIGenerateTask.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status == "processing":
        raise HTTPException(status_code=400, detail="无法删除进行中的任务")

    db.delete(task)
    db.commit()

    return {"message": "任务已删除"}


@router.post("/tasks/{task_id}/retry")
async def retry_generate_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重试失败的任务"""
    task = db.query(AIGenerateTask).filter(
        AIGenerateTask.id == task_id,
        AIGenerateTask.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "failed":
        raise HTTPException(status_code=400, detail="只能重试失败的任务")

    # 获取默认配置
    db_config = db.query(AIProviderConfig).filter(
        AIProviderConfig.user_id == current_user.id,
        AIProviderConfig.provider == task.provider,
        AIProviderConfig.model_name == task.model_name
    ).first()

    if not db_config:
        db_config = db.query(AIProviderConfig).filter(
            AIProviderConfig.user_id == current_user.id,
            AIProviderConfig.is_default == True
        ).first()

    if not db_config:
        raise HTTPException(status_code=400, detail="未找到可用的 AI 配置")

    # 重置任务状态
    task.status = "pending"
    task.progress = 0
    task.error_message = None
    db.commit()

    # 重新执行任务
    try:
        generate_test_cases.delay(task.id, db_config.id)
    except Exception:
        import threading
        thread = threading.Thread(target=run_generate_sync, args=(task.id, db_config.id))
        thread.daemon = True
        thread.start()

    return {"message": "任务已重新提交"}


@router.post("/tasks/{task_id}/cancel")
async def cancel_generate_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消进行中的任务"""
    task = db.query(AIGenerateTask).filter(
        AIGenerateTask.id == task_id,
        AIGenerateTask.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status not in ("processing", "pending"):
        raise HTTPException(status_code=400, detail="只能取消等待中或进行中的任务")

    task.status = "cancelled"
    db.commit()

    return {"message": "任务已取消"}


# ==================== 结果操作 ====================

@router.get("/tasks/{task_id}/cases")
async def get_generated_cases(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取生成的用例列表"""
    task = db.query(AIGenerateTask).filter(
        AIGenerateTask.id == task_id,
        AIGenerateTask.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")

    return {"cases": task.generated_cases or []}


@router.put("/tasks/{task_id}/cases/{case_index}")
async def update_generated_case(
    task_id: int,
    case_index: int,
    case_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """编辑单个生成的用例"""
    task = db.query(AIGenerateTask).filter(
        AIGenerateTask.id == task_id,
        AIGenerateTask.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")

    if not task.generated_cases or case_index < 0 or case_index >= len(task.generated_cases):
        raise HTTPException(status_code=400, detail="用例索引无效")

    # 更新用例
    task.generated_cases[case_index] = case_data
    # 标记 JSON 字段已修改，确保 SQLAlchemy 检测到变化
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(task, 'generated_cases')
    db.commit()

    return {"message": "用例已更新"}


@router.post("/tasks/{task_id}/save", response_model=SaveCasesResult)
async def save_cases_to_project(
    task_id: int,
    request: SaveCasesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存用例到项目"""
    from models.api_test_case import APITestCase
    from services.case_converter import convert_to_test_case

    task = db.query(AIGenerateTask).filter(
        AIGenerateTask.id == task_id,
        AIGenerateTask.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")

    if not task.generated_cases:
        raise HTTPException(status_code=400, detail="没有可保存的用例")

    # 校验目标项目是否存在
    from models import Project
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="目标项目不存在")

    # 确定要保存的用例
    cases_to_save = task.generated_cases
    if request.case_indices:
        cases_to_save = [
            task.generated_cases[i]
            for i in request.case_indices
            if 0 <= i < len(task.generated_cases)
        ]

    # 转换并保存用例
    from core.case_number import generate_case_number
    saved_count = 0
    errors = []
    for idx, case_data in enumerate(cases_to_save):
        try:

            # 生成用例编号，使用用例自身的 module
            case_module = case_data.get("module") or "DEFAULT"
            case_number = generate_case_number(db, request.project_id, case_module)

            test_case = convert_to_test_case(
                case_data=case_data,
                project_id=request.project_id,
                generate_type=task.generate_type,
                module=case_module,
                creator_id=current_user.id,
                case_number=case_number
            )
            db.add(test_case)
            saved_count += 1
        except Exception as e:
            import traceback
            error_detail = f"用例 {idx + 1}: {str(e)}"
            print(f"[保存用例失败] {error_detail}")
            traceback.print_exc()
            errors.append(error_detail)

    db.commit()

    message = f"成功保存 {saved_count} 个用例"
    if errors:
        message += f"，{len(errors)} 个失败"
        # 返回具体错误信息便于调试
        print(f"[保存用例] 失败详情: {errors}")

    return SaveCasesResult(message=message, saved_count=saved_count, errors=errors)
