# AI 生成测试用例功能设计文档

## 1. 概述

### 1.1 功能目标

为 TestForge 测试平台添加 AI 生成测试用例功能，支持根据 PRD 文档、接口文档和自然语言描述自动生成多种类型的测试用例。

### 1.2 核心需求

- **输入源支持**：PRD 文档（Word/PDF）、接口文档（Swagger/OpenAPI）、自然语言描述
- **用例类型**：功能测试用例、接口测试用例、边界值测试、组合测试用例
- **AI 模型**：支持多种模型（Claude、OpenAI GPT、DeepSeek 等）
- **API Key 管理**：用户自行配置，平台不承担成本
- **结果处理**：可编辑后保存，接口测试用例直接保存到用例系统
- **批量生成**：支持一次生成一批相关用例

### 1.3 技术选型

- **生成方案**：异步生成（基于 Celery 任务队列）
- **前端框架**：Vue 3 + TypeScript + Arco Design Vue
- **后端框架**：FastAPI + SQLAlchemy + Celery

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      前端 (Vue 3)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ 文档上传    │  │ 文本输入    │  │ 结果编辑    │      │
│  │ 组件        │  │ 组件        │  │ 组件        │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    后端 (FastAPI)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ 文档解析    │  │ Prompt      │  │ 结果解析    │      │
│  │ 服务        │  │ 引擎        │  │ 服务        │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│         │                │                │              │
│         └────────────────┼────────────────┘              │
│                          ▼                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │              AI 服务层（支持多模型）             │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │    │
│  │  │ Claude   │  │ OpenAI   │  │ 其他模型 │       │    │
│  │  └──────────┘  └──────────┘  └──────────┘       │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                 任务队列 (Celery)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ 任务创建    │  │ 任务执行    │  │ 状态更新    │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 数据模型设计

### 3.1 AI Provider 配置表

```python
class AIProviderConfig(Base):
    """用户 AI 模型配置"""
    __tablename__ = "ai_provider_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # claude / openai / deepseek / custom
    api_key = Column(String(500), nullable=False)  # 加密存储
    model_name = Column(String(100), nullable=False)  # claude-3-opus / gpt-4 / etc
    
    # 自定义 API 端点（支持中转站）
    api_base_url = Column(String(500), nullable=True)  # 自定义 API 地址
    
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="ai_configs")
```

**字段说明**：
- `provider`: AI 提供商标识，支持 claude、openai、deepseek、custom（自定义）
- `api_key`: 用户的 API Key，存储时进行加密
- `model_name`: 具体模型名称，如 claude-3-opus-20240229、gpt-4-turbo
- `api_base_url`: 自定义 API 端点地址，用于中转站或自建服务。为空时使用官方默认地址
- `is_default`: 是否为默认配置，每个用户只能有一个默认配置

**中转站使用示例**：
- OpenAI 中转站：`https://api.example.com/v1`
- Claude 中转站：`https://claude-proxy.example.com`
- 自建服务：`http://localhost:11434`（Ollama）

### 3.2 AI 生成任务表

```python
class AIGenerateTask(Base):
    """AI 生成任务"""
    __tablename__ = "ai_generate_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # 输入配置
    input_type = Column(String(20), nullable=False)  # prd / swagger / text
    input_content = Column(Text)  # 原始输入内容（文本类型）
    input_file_path = Column(String(500))  # 上传文件路径（文档类型）
    input_file_name = Column(String(200))  # 原始文件名
    
    # 生成配置
    generate_type = Column(String(20), nullable=False)  # functional / api / boundary / combination
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    target_count = Column(Integer, default=10)  # 目标生成数量
    
    # 任务状态
    status = Column(String(20), default="pending")  # pending / processing / completed / failed / cancelled
    progress = Column(Integer, default=0)  # 0-100
    error_message = Column(Text)
    
    # 结果
    generated_cases = Column(JSON)  # 生成的用例数据（JSON 数组）
    cases_count = Column(Integer, default=0)  # 实际生成的用例数量
    
    # 审计
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # 关系
    user = relationship("User")
    project = relationship("Project")
```

**状态流转**：
```
pending → processing → completed
                    → failed
                    → cancelled
```

### 3.3 数据库迁移

新增迁移文件 `server/migrations/add_ai_tables.py`：

```python
"""添加 AI 生成相关表

迁移 ID: add_ai_tables
创建时间: 2026-05-23
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # 创建 ai_provider_configs 表
    op.create_table(
        'ai_provider_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('api_key', sa.String(500), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_provider_configs_id'), 'ai_provider_configs', ['id'], unique=False)
    op.create_index(op.f('ix_ai_provider_configs_user_id'), 'ai_provider_configs', ['user_id'], unique=False)
    
    # 创建 ai_generate_tasks 表
    op.create_table(
        'ai_generate_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('input_type', sa.String(20), nullable=False),
        sa.Column('input_content', sa.Text(), nullable=True),
        sa.Column('input_file_path', sa.String(500), nullable=True),
        sa.Column('input_file_name', sa.String(200), nullable=True),
        sa.Column('generate_type', sa.String(20), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('target_count', sa.Integer(), default=10),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('progress', sa.Integer(), default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('generated_cases', sa.JSON(), nullable=True),
        sa.Column('cases_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_generate_tasks_id'), 'ai_generate_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_ai_generate_tasks_user_id'), 'ai_generate_tasks', ['user_id'], unique=False)
    op.create_index(op.f('ix_ai_generate_tasks_project_id'), 'ai_generate_tasks', ['project_id'], unique=False)
    op.create_index(op.f('ix_ai_generate_tasks_status'), 'ai_generate_tasks', ['status'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_ai_generate_tasks_status'), table_name='ai_generate_tasks')
    op.drop_index(op.f('ix_ai_generate_tasks_project_id'), table_name='ai_generate_tasks')
    op.drop_index(op.f('ix_ai_generate_tasks_user_id'), table_name='ai_generate_tasks')
    op.drop_index(op.f('ix_ai_generate_tasks_id'), table_name='ai_generate_tasks')
    op.drop_table('ai_generate_tasks')
    
    op.drop_index(op.f('ix_ai_provider_configs_user_id'), table_name='ai_provider_configs')
    op.drop_index(op.f('ix_ai_provider_configs_id'), table_name='ai_provider_configs')
    op.drop_table('ai_provider_configs')
```

---

## 4. 后端实现设计

### 4.1 目录结构

```
server/
├── api/
│   └── ai_generate.py          # AI 生成相关接口
├── models/
│   └── ai_generate.py          # AI 生成相关模型
├── schemas/
│   └── ai_generate.py          # AI 生成相关 Schema
├── services/
│   ├── ai_service.py           # AI 服务层（多模型支持）
│   ├── document_parser.py      # 文档解析服务
│   ├── prompt_engine.py        # Prompt 引擎
│   ├── case_generator.py       # 用例生成服务
│   └── case_converter.py       # 用例转换服务
├── tasks/
│   └── ai_generate_tasks.py    # Celery 任务
└── utils/
    └── crypto.py               # 加密工具（API Key 加密）
```

### 4.2 AI 服务层设计

```python
# server/services/ai_service.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx

class AIProvider(ABC):
    """AI 提供商抽象基类"""
    
    def __init__(self, api_key: str, api_base_url: Optional[str] = None):
        self.api_key = api_key
        self.api_base_url = api_base_url
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], model: str) -> str:
        """发送对话请求"""
        pass
    
    @abstractmethod
    def validate_api_key(self) -> bool:
        """验证 API Key 是否有效"""
        pass

class ClaudeProvider(AIProvider):
    """Claude API 提供商"""
    
    def __init__(self, api_key: str, api_base_url: Optional[str] = None):
        super().__init__(api_key, api_base_url)
        # 默认 API 地址
        self.base_url = api_base_url or "https://api.anthropic.com"
    
    async def chat(self, messages: List[Dict[str, str]], model: str) -> str:
        """调用 Claude API"""
        import anthropic
        
        client = anthropic.AsyncAnthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # 提取 system 消息
        system_message = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)
        
        response = await client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_message,
            messages=user_messages
        )
        
        return response.content[0].text
    
    def validate_api_key(self) -> bool:
        """验证 Claude API Key"""
        try:
            import anthropic
            client = anthropic.Anthropic(
                api_key=self.api_key,
                base_url=self.base_url
            )
            # 发送测试请求
            client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception:
            return False

class OpenAIProvider(AIProvider):
    """OpenAI API 提供商"""
    
    def __init__(self, api_key: str, api_base_url: Optional[str] = None):
        super().__init__(api_key, api_base_url)
        # 默认 API 地址
        self.base_url = api_base_url or "https://api.openai.com/v1"
    
    async def chat(self, messages: List[Dict[str, str]], model: str) -> str:
        """调用 OpenAI API"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=4096
        )
        
        return response.choices[0].message.content
    
    def validate_api_key(self) -> bool:
        """验证 OpenAI API Key"""
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            # 发送测试请求
            client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            return True
        except Exception:
            return False

class DeepSeekProvider(OpenAIProvider):
    """DeepSeek API 提供商（兼容 OpenAI 接口）"""
    
    def __init__(self, api_key: str, api_base_url: Optional[str] = None):
        super().__init__(api_key, api_base_url or "https://api.deepseek.com/v1")

class CustomProvider(OpenAIProvider):
    """自定义 API 提供商（兼容 OpenAI 接口）"""
    
    def __init__(self, api_key: str, api_base_url: str):
        if not api_base_url:
            raise ValueError("自定义提供商必须提供 api_base_url")
        super().__init__(api_key, api_base_url)

class AIServiceFactory:
    """AI 服务工厂"""
    
    @staticmethod
    def create_provider(
        provider: str,
        api_key: str,
        api_base_url: Optional[str] = None
    ) -> AIProvider:
        """创建 AI 提供商实例"""
        providers = {
            "claude": ClaudeProvider,
            "openai": OpenAIProvider,
            "deepseek": DeepSeekProvider,
            "custom": CustomProvider,
        }
        
        if provider not in providers:
            raise ValueError(f"不支持的 AI 提供商: {provider}")
        
        return providers[provider](api_key, api_base_url)
```

### 4.3 Prompt 引擎设计

```python
# server/services/prompt_engine.py

from typing import Dict, Any

PROMPT_TEMPLATES = {
    "functional": {
        "system": """你是一个资深的测试工程师，擅长根据需求文档生成功能测试用例。
        
要求：
1. 用例覆盖正常流程、异常流程、边界条件
2. 每个用例包含：用例名称、前置条件、测试步骤、预期结果、优先级
3. 使用 markdown 表格格式输出
4. 用例名称简洁明确，步骤可执行""",
        
        "user": """请根据以下需求文档生成功能测试用例：

{input_content}

请生成 {count} 个测试用例，覆盖以下维度：
- 正常流程测试
- 异常流程测试
- 边界值测试
- 权限测试（如适用）

请以 JSON 格式返回，结构如下：
```json
[
  {{
    "name": "用例名称",
    "priority": "P1",
    "preconditions": "前置条件",
    "steps": ["步骤1", "步骤2"],
    "expected_result": "预期结果",
    "test_type": "normal/exception/boundary"
  }}
]
```"""
    },
    
    "api": {
        "system": """你是一个接口测试专家，擅长根据接口文档生成接口测试用例。

要求：
1. 每个接口生成：正向用例、参数校验用例、边界值用例
2. 输出格式为 JSON，包含完整的请求配置和断言
3. 断言覆盖状态码、响应时间、关键字段
4. 考虑认证、鉴权场景""",
        
        "user": """请根据以下接口文档生成接口测试用例：

{input_content}

请为每个接口生成测试用例，包含：
- 请求方法、URL、Headers
- 请求体（如适用）
- 预期状态码和响应断言
- 数据提取规则（如需要）

请以 JSON 格式返回，结构如下：
```json
[
  {{
    "name": "用例名称",
    "method": "GET",
    "url": "/api/users",
    "headers": [{{"key": "Content-Type", "value": "application/json"}}],
    "query_params": [],
    "body_type": "none",
    "body_content": null,
    "priority": "P1",
    "assertions": [
      {{
        "assertion_type": "status_code",
        "operator": "equals",
        "expected": "200"
      }}
    ]
  }}
]
```"""
    },
    
    "boundary": {
        "system": """你是一个边界值测试专家，擅长分析输入参数的边界条件。

要求：
1. 识别所有输入参数
2. 分析每个参数的边界值（最小值、最大值、空值、特殊字符）
3. 生成边界值测试用例
4. 包含预期结果和错误提示""",
        
        "user": """请分析以下功能描述的边界条件：

{input_content}

请生成边界值测试用例，覆盖：
- 数值边界（最小值、最大值、临界值）
- 字符串边界（空字符串、最大长度、特殊字符）
- 日期时间边界
- 集合边界（空集合、单元素、最大数量）

请以 JSON 格式返回，结构如下：
```json
[
  {{
    "name": "用例名称",
    "parameter": "参数名",
    "boundary_type": "min/max/empty/special",
    "test_value": "测试值",
    "expected_result": "预期结果",
    "priority": "P2"
  }}
]
```"""
    },
    
    "combination": {
        "system": """你是一个组合测试专家，擅长使用正交表和 Pairwise 方法生成组合测试用例。

要求：
1. 识别所有输入参数及其取值
2. 使用 Pairwise 方法生成最小覆盖集
3. 输出测试用例矩阵
4. 标注每个用例的覆盖情况""",
        
        "user": """请分析以下功能的输入参数组合：

{input_content}

请使用 Pairwise 方法生成组合测试用例，要求：
- 识别所有参数及取值
- 生成最小测试用例集
- 确保两两覆盖
- 输出用例矩阵

请以 JSON 格式返回，结构如下：
```json
[
  {{
    "name": "用例名称",
    "parameters": {{
      "参数1": "值1",
      "参数2": "值2"
    }},
    "coverage": ["参数1-值1,参数2-值2"],
    "priority": "P2"
  }}
]
```"""
    }
}

class PromptEngine:
    """Prompt 引擎"""
    
    @staticmethod
    def build_messages(
        generate_type: str,
        input_content: str,
        count: int = 10
    ) -> list:
        """构建 AI 对话消息"""
        template = PROMPT_TEMPLATES.get(generate_type)
        if not template:
            raise ValueError(f"不支持的生成类型: {generate_type}")
        
        return [
            {"role": "system", "content": template["system"]},
            {"role": "user", "content": template["user"].format(
                input_content=input_content,
                count=count
            )}
        ]
```

### 4.4 文档解析服务设计

```python
# server/services/document_parser.py

from typing import Dict, Any
import json

class DocumentParser:
    """文档解析器"""
    
    @staticmethod
    def parse_prd(file_path: str) -> Dict[str, Any]:
        """
        解析 PRD 文档
        
        支持格式：.docx, .pdf, .md
        
        返回结构：
        {
            "title": "文档标题",
            "content": "文档内容（纯文本）",
            "sections": [
                {
                    "title": "章节标题",
                    "content": "章节内容"
                }
            ]
        }
        """
        # 根据文件扩展名选择解析器
        if file_path.endswith('.docx'):
            return DocumentParser._parse_docx(file_path)
        elif file_path.endswith('.pdf'):
            return DocumentParser._parse_pdf(file_path)
        elif file_path.endswith('.md'):
            return DocumentParser._parse_markdown(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_path}")
    
    @staticmethod
    def parse_swagger(file_path: str) -> Dict[str, Any]:
        """
        解析 Swagger/OpenAPI 文档
        
        支持格式：.json, .yaml
        
        返回结构：
        {
            "info": {
                "title": "API 标题",
                "version": "版本",
                "description": "描述"
            },
            "endpoints": [
                {
                    "path": "/api/users",
                    "method": "GET",
                    "summary": "获取用户列表",
                    "parameters": [...],
                    "request_body": {...},
                    "responses": {...}
                }
            ]
        }
        """
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.endswith('.json'):
                content = json.load(f)
            elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
                import yaml
                content = yaml.safe_load(f)
            else:
                raise ValueError(f"不支持的文件格式: {file_path}")
        
        # 解析 Swagger/OpenAPI 文档
        return DocumentParser._parse_swagger_content(content)
    
    @staticmethod
    def _parse_docx(file_path: str) -> Dict[str, Any]:
        """解析 Word 文档"""
        # 使用 python-docx 库解析
        pass
    
    @staticmethod
    def _parse_pdf(file_path: str) -> Dict[str, Any]:
        """解析 PDF 文档"""
        # 使用 PyPDF2 或 pdfplumber 库解析
        pass
    
    @staticmethod
    def _parse_markdown(file_path: str) -> Dict[str, Any]:
        """解析 Markdown 文档"""
        pass
    
    @staticmethod
    def _parse_swagger_content(content: Dict) -> Dict[str, Any]:
        """解析 Swagger 内容"""
        # 提取基本信息
        info = content.get('info', {})
        
        # 提取接口信息
        endpoints = []
        paths = content.get('paths', {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    endpoint = {
                        'path': path,
                        'method': method.upper(),
                        'summary': details.get('summary', ''),
                        'description': details.get('description', ''),
                        'parameters': details.get('parameters', []),
                        'request_body': details.get('requestBody', {}),
                        'responses': details.get('responses', {})
                    }
                    endpoints.append(endpoint)
        
        return {
            'info': info,
            'endpoints': endpoints
        }
```

### 4.5 API 接口设计

```python
# server/api/ai_generate.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models.user import User
from models.ai_generate import AIProviderConfig, AIGenerateTask
from schemas.ai_generate import (
    AIProviderConfigCreate,
    AIProviderConfigUpdate,
    AIProviderConfigOut,
    AIGenerateTaskCreate,
    AIGenerateTaskOut,
    AIGenerateTaskListOut
)
from services.ai_service import AIServiceFactory
from services.document_parser import DocumentParser
from tasks.ai_generate_tasks import generate_test_cases
from utils.auth import get_current_user
from utils.crypto import encrypt_api_key, decrypt_api_key

router = APIRouter(prefix="/ai-generate", tags=["AI 生成"])

# ==================== AI 配置管理 ====================

@router.post("/configs", response_model=AIProviderConfigOut)
async def create_ai_config(
    config: AIProviderConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建 AI 配置"""
    # 验证 API Key 是否有效
    provider = AIServiceFactory.create_provider(config.provider, config.api_key)
    if not provider.validate_api_key(config.api_key):
        raise HTTPException(status_code=400, detail="API Key 无效")
    
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
    ).all()
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
    
    # 验证新的 API Key
    if config.api_key:
        provider = AIServiceFactory.create_provider(
            config.provider or db_config.provider,
            config.api_key
        )
        if not provider.validate_api_key(config.api_key):
            raise HTTPException(status_code=400, detail="API Key 无效")
        db_config.api_key = encrypt_api_key(config.api_key)
    
    # 更新其他字段
    if config.provider:
        db_config.provider = config.provider
    if config.model_name:
        db_config.model_name = config.model_name
    if config.is_default is not None:
        if config.is_default:
            db.query(AIProviderConfig).filter(
                AIProviderConfig.user_id == current_user.id,
                AIProviderConfig.is_default == True
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

@router.post("/configs/{config_id}/test")
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
        provider = AIServiceFactory.create_provider(db_config.provider, api_key)
        
        # 发送测试请求
        messages = [{"role": "user", "content": "Hello"}]
        response = await provider.chat(messages, db_config.model_name)
        
        return {"success": True, "message": "配置有效"}
    except Exception as e:
        return {"success": False, "message": str(e)}

# ==================== 文档上传 ====================

@router.post("/upload/prd")
async def upload_prd(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传 PRD 文档"""
    # 验证文件类型
    allowed_types = ['.docx', '.pdf', '.md']
    file_ext = '.' + file.filename.split('.')[-1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型，支持: {', '.join(allowed_types)}")
    
    # 保存文件
    file_path = f"uploads/prd/{current_user.id}/{file.filename}"
    # 实现文件保存逻辑
    
    # 解析文档
    parsed = DocumentParser.parse_prd(file_path)
    
    return {
        "file_path": file_path,
        "file_name": file.filename,
        "parsed_content": parsed
    }

@router.post("/upload/swagger")
async def upload_swagger(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传 Swagger 文档"""
    # 验证文件类型
    allowed_types = ['.json', '.yaml', '.yml']
    file_ext = '.' + file.filename.split('.')[-1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型，支持: {', '.join(allowed_types)}")
    
    # 保存文件
    file_path = f"uploads/swagger/{current_user.id}/{file.filename}"
    # 实现文件保存逻辑
    
    # 解析文档
    parsed = DocumentParser.parse_swagger(file_path)
    
    return {
        "file_path": file_path,
        "file_name": file.filename,
        "parsed_content": parsed
    }

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
        provider=db_config.provider,
        model_name=db_config.model_name,
        target_count=task.target_count
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # 异步执行生成任务
    generate_test_cases.delay(db_task.id)
    
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
    
    # 重置任务状态
    task.status = "pending"
    task.progress = 0
    task.error_message = None
    db.commit()
    
    # 重新执行任务
    generate_test_cases.delay(task.id)
    
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
    
    if task.status != "processing":
        raise HTTPException(status_code=400, detail="只能取消进行中的任务")
    
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
    
    return {"cases": task.generated_cases}

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
    
    if case_index < 0 or case_index >= len(task.generated_cases):
        raise HTTPException(status_code=400, detail="用例索引无效")
    
    # 更新用例
    task.generated_cases[case_index] = case_data
    db.commit()
    
    return {"message": "用例已更新"}

@router.post("/tasks/{task_id}/save")
async def save_cases_to_project(
    task_id: int,
    case_indices: List[int] = None,
    module: str = None,
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
    
    # 确定要保存的用例
    cases_to_save = task.generated_cases
    if case_indices:
        cases_to_save = [task.generated_cases[i] for i in case_indices if i < len(task.generated_cases)]
    
    # 转换并保存用例
    saved_count = 0
    for case_data in cases_to_save:
        try:
            test_case = convert_to_test_case(
                case_data=case_data,
                project_id=task.project_id,
                generate_type=task.generate_type,
                module=module,
                creator_id=current_user.id
            )
            db.add(test_case)
            saved_count += 1
        except Exception as e:
            # 记录错误但继续处理其他用例
            print(f"保存用例失败: {e}")
    
    db.commit()
    
    return {"message": f"成功保存 {saved_count} 个用例", "saved_count": saved_count}
```

### 4.6 Celery 任务设计

```python
# server/tasks/ai_generate_tasks.py

from celery import shared_task
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio

from database import SessionLocal
from models.ai_generate import AIGenerateTask, AIProviderConfig
from services.ai_service import AIServiceFactory
from services.prompt_engine import PromptEngine
from utils.crypto import decrypt_api_key

def run_async(coro):
    """在同步上下文中运行异步函数"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@shared_task(bind=True)
def generate_test_cases(self, task_id: int):
    """生成测试用例的 Celery 任务"""
    db = SessionLocal()
    
    try:
        # 获取任务
        task = db.query(AIGenerateTask).filter(AIGenerateTask.id == task_id).first()
        if not task:
            return
        
        # 更新任务状态
        task.status = "processing"
        task.progress = 10
        db.commit()
        
        # 获取 AI 配置
        config = db.query(AIProviderConfig).filter(
            AIProviderConfig.user_id == task.user_id,
            AIProviderConfig.provider == task.provider,
            AIProviderConfig.model_name == task.model_name
        ).first()
        
        if not config:
            task.status = "failed"
            task.error_message = "AI 配置不存在"
            db.commit()
            return
        
        # 创建 AI 服务
        api_key = decrypt_api_key(config.api_key)
        provider = AIServiceFactory.create_provider(task.provider, api_key)
        
        # 更新进度
        task.progress = 30
        db.commit()
        
        # 构建 Prompt
        messages = PromptEngine.build_messages(
            generate_type=task.generate_type,
            input_content=task.input_content,
            count=task.target_count
        )
        
        # 更新进度
        task.progress = 50
        db.commit()
        
        # 调用 AI 生成（同步调用异步函数）
        response = run_async(provider.chat(messages, task.model_name))
        
        # 更新进度
        task.progress = 80
        db.commit()
        
        # 解析结果
        import json
        try:
            # 尝试从响应中提取 JSON
            json_match = response.strip()
            if json_match.startswith('```json'):
                json_match = json_match[7:]
            if json_match.endswith('```'):
                json_match = json_match[:-3]
            
            generated_cases = json.loads(json_match)
        except json.JSONDecodeError:
            # 如果解析失败，尝试提取 JSON 部分
            import re
            json_pattern = r'\[[\s\S]*\]'
            match = re.search(json_pattern, response)
            if match:
                generated_cases = json.loads(match.group())
            else:
                task.status = "failed"
                task.error_message = "无法解析 AI 返回的结果"
                db.commit()
                return
        
        # 更新任务结果
        task.generated_cases = generated_cases
        task.cases_count = len(generated_cases)
        task.status = "completed"
        task.progress = 100
        task.completed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        # 任务失败
        task.status = "failed"
        task.error_message = str(e)
        db.commit()
        raise
    
    finally:
        db.close()
```

### 4.7 用例转换服务

```python
# server/services/case_converter.py

from typing import Dict, Any
from models.api_test_case import APITestCase

def convert_to_test_case(
    case_data: Dict[str, Any],
    project_id: int,
    generate_type: str,
    module: str = None,
    creator_id: int = None
) -> APITestCase:
    """
    将 AI 生成的用例数据转换为测试用例模型
    
    Args:
        case_data: AI 生成的用例数据
        project_id: 项目 ID
        generate_type: 生成类型
        module: 模块名称
        creator_id: 创建者 ID
    
    Returns:
        APITestCase 实例
    """
    if generate_type == "api":
        return _convert_api_case(case_data, project_id, module, creator_id)
    elif generate_type == "functional":
        return _convert_functional_case(case_data, project_id, module, creator_id)
    elif generate_type == "boundary":
        return _convert_boundary_case(case_data, project_id, module, creator_id)
    elif generate_type == "combination":
        return _convert_combination_case(case_data, project_id, module, creator_id)
    else:
        raise ValueError(f"不支持的生成类型: {generate_type}")

def _convert_api_case(
    case_data: Dict[str, Any],
    project_id: int,
    module: str,
    creator_id: int
) -> APITestCase:
    """转换接口测试用例"""
    return APITestCase(
        project_id=project_id,
        module=module,
        name=case_data.get("name", "未命名用例"),
        description=case_data.get("description", ""),
        method=case_data.get("method", "GET"),
        url=case_data.get("url", ""),
        body_type=case_data.get("body_type", "none"),
        priority=case_data.get("priority", "P2"),
        status="draft",
        creator_id=creator_id,
        headers=case_data.get("headers", []),
        query_params=case_data.get("query_params", []),
        assertions=case_data.get("assertions", [])
    )

def _convert_functional_case(
    case_data: Dict[str, Any],
    project_id: int,
    module: str,
    creator_id: int
) -> APITestCase:
    """转换功能测试用例"""
    # 功能测试用例需要转换为接口测试用例格式
    # 这里假设用户会手动补充接口信息
    return APITestCase(
        project_id=project_id,
        module=module,
        name=case_data.get("name", "未命名用例"),
        description=f"前置条件: {case_data.get('preconditions', '无')}\n\n测试步骤:\n" + "\n".join(case_data.get("steps", [])),
        preconditions=case_data.get("preconditions", ""),
        method="GET",  # 默认值，用户需要手动修改
        url="/",  # 默认值，用户需要手动修改
        priority=case_data.get("priority", "P2"),
        status="draft",
        creator_id=creator_id
    )

def _convert_boundary_case(
    case_data: Dict[str, Any],
    project_id: int,
    module: str,
    creator_id: int
) -> APITestCase:
    """转换边界值测试用例"""
    return APITestCase(
        project_id=project_id,
        module=module,
        name=case_data.get("name", "未命名用例"),
        description=f"参数: {case_data.get('parameter', '')}\n边界类型: {case_data.get('boundary_type', '')}\n测试值: {case_data.get('test_value', '')}",
        method="GET",  # 默认值，用户需要手动修改
        url="/",  # 默认值，用户需要手动修改
        priority=case_data.get("priority", "P2"),
        status="draft",
        creator_id=creator_id
    )

def _convert_combination_case(
    case_data: Dict[str, Any],
    project_id: int,
    module: str,
    creator_id: int
) -> APITestCase:
    """转换组合测试用例"""
    parameters = case_data.get("parameters", {})
    param_desc = "\n".join([f"{k}: {v}" for k, v in parameters.items()])
    
    return APITestCase(
        project_id=project_id,
        module=module,
        name=case_data.get("name", "未命名用例"),
        description=f"参数组合:\n{param_desc}",
        method="GET",  # 默认值，用户需要手动修改
        url="/",  # 默认值，用户需要手动修改
        priority=case_data.get("priority", "P2"),
        status="draft",
        creator_id=creator_id
    )
```

---

## 5. 前端实现设计

### 5.1 目录结构

```
frontend/src/
├── api/
│   └── aiGenerate.ts           # AI 生成相关 API
├── views/
│   └── ai-generate/
│       ├── AIGeneratePage.vue  # 主页面
│       ├── components/
│       │   ├── FileUpload.vue  # 文件上传组件
│       │   ├── TextInput.vue   # 文本输入组件
│       │   ├── TaskList.vue    # 任务列表组件
│       │   ├── TaskDetail.vue  # 任务详情组件
│       │   ├── CaseEditor.vue  # 用例编辑组件
│       │   └── AIConfig.vue    # AI 配置组件
│       └── index.vue           # 页面入口
└── router/
    └── index.ts                # 路由配置
```

### 5.2 API 接口定义

```typescript
// frontend/src/api/aiGenerate.ts

import request from '@/utils/request'

// ==================== 类型定义 ====================

export interface AIProviderConfig {
  id: number
  user_id: number
  provider: string
  model_name: string
  api_base_url?: string
  is_default: boolean
  created_at: string
  updated_at?: string
}

export interface AIProviderConfigCreate {
  provider: string
  api_key: string
  model_name: string
  api_base_url?: string
  is_default?: boolean
}

export interface AIProviderConfigUpdate {
  provider?: string
  api_key?: string
  model_name?: string
  api_base_url?: string
  is_default?: boolean
}

export interface AIGenerateTask {
  id: number
  user_id: number
  project_id: number
  input_type: string
  input_content?: string
  input_file_path?: string
  input_file_name?: string
  generate_type: string
  provider: string
  model_name: string
  target_count: number
  status: string
  progress: number
  error_message?: string
  generated_cases?: any[]
  cases_count: number
  created_at: string
  updated_at?: string
  completed_at?: string
}

export interface AIGenerateTaskCreate {
  project_id: number
  input_type: 'prd' | 'swagger' | 'text'
  input_content?: string
  input_file_path?: string
  input_file_name?: string
  generate_type: 'functional' | 'api' | 'boundary' | 'combination'
  config_id?: number
  target_count?: number
}

// ==================== API 函数 ====================

// AI 配置管理
export const getAIConfigs = () => {
  return request<AIProviderConfig[]>({
    url: '/ai-generate/configs',
    method: 'get'
  })
}

export const createAIConfig = (data: AIProviderConfigCreate) => {
  return request<AIProviderConfig>({
    url: '/ai-generate/configs',
    method: 'post',
    data
  })
}

export const updateAIConfig = (id: number, data: AIProviderConfigUpdate) => {
  return request<AIProviderConfig>({
    url: `/ai-generate/configs/${id}`,
    method: 'put',
    data
  })
}

export const deleteAIConfig = (id: number) => {
  return request({
    url: `/ai-generate/configs/${id}`,
    method: 'delete'
  })
}

export const testAIConfig = (id: number) => {
  return request<{ success: boolean; message: string }>({
    url: `/ai-generate/configs/${id}/test`,
    method: 'post'
  })
}

// 文档上传
export const uploadPRD = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return request<{
    file_path: string
    file_name: string
    parsed_content: any
  }>({
    url: '/ai-generate/upload/prd',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const uploadSwagger = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return request<{
    file_path: string
    file_name: string
    parsed_content: any
  }>({
    url: '/ai-generate/upload/swagger',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 生成任务管理
export const createGenerateTask = (data: AIGenerateTaskCreate) => {
  return request<AIGenerateTask>({
    url: '/ai-generate/tasks',
    method: 'post',
    data
  })
}

export const getGenerateTasks = (params?: {
  project_id?: number
  status?: string
  skip?: number
  limit?: number
}) => {
  return request<AIGenerateTask[]>({
    url: '/ai-generate/tasks',
    method: 'get',
    params
  })
}

export const getGenerateTask = (id: number) => {
  return request<AIGenerateTask>({
    url: `/ai-generate/tasks/${id}`,
    method: 'get'
  })
}

export const deleteGenerateTask = (id: number) => {
  return request({
    url: `/ai-generate/tasks/${id}`,
    method: 'delete'
  })
}

export const retryGenerateTask = (id: number) => {
  return request({
    url: `/ai-generate/tasks/${id}/retry`,
    method: 'post'
  })
}

export const cancelGenerateTask = (id: number) => {
  return request({
    url: `/ai-generate/tasks/${id}/cancel`,
    method: 'post'
  })
}

// 结果操作
export const getGeneratedCases = (taskId: number) => {
  return request<{ cases: any[] }>({
    url: `/ai-generate/tasks/${taskId}/cases`,
    method: 'get'
  })
}

export const updateGeneratedCase = (taskId: number, caseIndex: number, caseData: any) => {
  return request({
    url: `/ai-generate/tasks/${taskId}/cases/${caseIndex}`,
    method: 'put',
    data: caseData
  })
}

export const saveCasesToProject = (taskId: number, data: {
  case_indices?: number[]
  module?: string
}) => {
  return request<{ message: string; saved_count: number }>({
    url: `/ai-generate/tasks/${taskId}/save`,
    method: 'post',
    data
  })
}
```

### 5.3 主页面组件

```vue
<!-- frontend/src/views/ai-generate/AIGeneratePage.vue -->

<template>
  <div class="ai-generate-page">
    <div class="page-header">
      <h2>AI 生成测试用例</h2>
      <a-button type="primary" @click="showConfigModal = true">
        <template #icon><icon-settings /></template>
        AI 配置
      </a-button>
    </div>
    
    <div class="page-content">
      <!-- 输入区域 -->
      <div class="input-section">
        <a-card title="输入配置">
          <!-- 输入类型选择 -->
          <a-tabs v-model:activeKey="inputType">
            <a-tab-pane key="prd" tab="PRD 文档">
              <FileUpload
                accept=".docx,.pdf,.md"
                @upload="handlePRDUpload"
              />
            </a-tab-pane>
            <a-tab-pane key="swagger" tab="接口文档">
              <FileUpload
                accept=".json,.yaml,.yml"
                @upload="handleSwaggerUpload"
              />
            </a-tab-pane>
            <a-tab-pane key="text" tab="文本输入">
              <TextInput v-model="textContent" />
            </a-tab-pane>
          </a-tabs>
          
          <!-- 生成配置 -->
          <div class="generate-config">
            <a-form layout="vertical">
              <a-row :gutter="16">
                <a-col :span="8">
                  <a-form-item label="生成类型">
                    <a-select v-model="generateType">
                      <a-option value="functional">功能测试用例</a-option>
                      <a-option value="api">接口测试用例</a-option>
                      <a-option value="boundary">边界值测试</a-option>
                      <a-option value="combination">组合测试用例</a-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="AI 模型">
                    <a-select v-model="selectedConfig" placeholder="选择 AI 配置">
                      <a-option
                        v-for="config in aiConfigs"
                        :key="config.id"
                        :value="config.id"
                      >
                        {{ config.provider }} - {{ config.model_name }}
                      </a-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="生成数量">
                    <a-input-number
                      v-model="targetCount"
                      :min="1"
                      :max="50"
                      placeholder="10"
                    />
                  </a-form-item>
                </a-col>
              </a-row>
            </a-form>
          </div>
          
          <!-- 生成按钮 -->
          <div class="generate-actions">
            <a-button
              type="primary"
              size="large"
              :loading="generating"
              :disabled="!canGenerate"
              @click="handleGenerate"
            >
              开始生成
            </a-button>
          </div>
        </a-card>
      </div>
      
      <!-- 任务列表 -->
      <div class="task-section">
        <a-card title="生成任务">
          <TaskList
            :tasks="tasks"
            @refresh="loadTasks"
            @view="handleViewTask"
            @delete="handleDeleteTask"
            @retry="handleRetryTask"
            @cancel="handleCancelTask"
          />
        </a-card>
      </div>
    </div>
    
    <!-- AI 配置弹窗 -->
    <a-modal
      v-model:visible="showConfigModal"
      title="AI 配置管理"
      :width="800"
      :footer="null"
    >
      <AIConfig />
    </a-modal>
    
    <!-- 任务详情弹窗 -->
    <a-modal
      v-model:visible="showTaskDetail"
      title="任务详情"
      :width="1200"
      :footer="null"
    >
      <TaskDetail
        v-if="currentTask"
        :task="currentTask"
        @save="handleSaveCases"
      />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import FileUpload from './components/FileUpload.vue'
import TextInput from './components/TextInput.vue'
import TaskList from './components/TaskList.vue'
import TaskDetail from './components/TaskDetail.vue'
import AIConfig from './components/AIConfig.vue'
import {
  getAIConfigs,
  uploadPRD,
  uploadSwagger,
  createGenerateTask,
  getGenerateTasks,
  deleteGenerateTask,
  retryGenerateTask,
  cancelGenerateTask,
  saveCasesToProject
} from '@/api/aiGenerate'
import type {
  AIProviderConfig,
  AIGenerateTask,
  AIGenerateTaskCreate
} from '@/api/aiGenerate'

// 状态
const inputType = ref<'prd' | 'swagger' | 'text'>('text')
const textContent = ref('')
const generateType = ref<'functional' | 'api' | 'boundary' | 'combination'>('api')
const selectedConfig = ref<number | undefined>()
const targetCount = ref(10)
const generating = ref(false)
const showConfigModal = ref(false)
const showTaskDetail = ref(false)
const currentTask = ref<AIGenerateTask | null>(null)

// 数据
const aiConfigs = ref<AIProviderConfig[]>([])
const tasks = ref<AIGenerateTask[]>([])

// 上传的文件信息
const uploadedFile = ref<{
  path: string
  name: string
  content: any
} | null>(null)

// 计算属性
const canGenerate = computed(() => {
  if (inputType.value === 'text') {
    return textContent.value.trim() && selectedConfig.value
  }
  return uploadedFile.value && selectedConfig.value
})

// 加载数据
const loadConfigs = async () => {
  try {
    aiConfigs.value = await getAIConfigs()
    // 自动选择默认配置
    const defaultConfig = aiConfigs.value.find(c => c.is_default)
    if (defaultConfig) {
      selectedConfig.value = defaultConfig.id
    }
  } catch (error) {
    console.error('加载 AI 配置失败:', error)
  }
}

const loadTasks = async () => {
  try {
    tasks.value = await getGenerateTasks()
  } catch (error) {
    console.error('加载任务列表失败:', error)
  }
}

// 事件处理
const handlePRDUpload = async (file: File) => {
  try {
    const result = await uploadPRD(file)
    uploadedFile.value = {
      path: result.file_path,
      name: result.file_name,
      content: result.parsed_content
    }
    Message.success('PRD 文档上传成功')
  } catch (error) {
    Message.error('PRD 文档上传失败')
  }
}

const handleSwaggerUpload = async (file: File) => {
  try {
    const result = await uploadSwagger(file)
    uploadedFile.value = {
      path: result.file_path,
      name: result.file_name,
      content: result.parsed_content
    }
    Message.success('接口文档上传成功')
  } catch (error) {
    Message.error('接口文档上传失败')
  }
}

const handleGenerate = async () => {
  if (!canGenerate.value) {
    Message.warning('请完善输入配置')
    return
  }
  
  generating.value = true
  
  try {
    const taskData: AIGenerateTaskCreate = {
      project_id: 1, // TODO: 从当前项目获取
      input_type: inputType.value,
      generate_type: generateType.value,
      config_id: selectedConfig.value,
      target_count: targetCount.value
    }
    
    if (inputType.value === 'text') {
      taskData.input_content = textContent.value
    } else if (uploadedFile.value) {
      taskData.input_file_path = uploadedFile.value.path
      taskData.input_file_name = uploadedFile.value.name
      taskData.input_content = JSON.stringify(uploadedFile.value.content)
    }
    
    await createGenerateTask(taskData)
    Message.success('生成任务已创建')
    
    // 刷新任务列表
    await loadTasks()
    
    // 清空输入
    textContent.value = ''
    uploadedFile.value = null
  } catch (error) {
    Message.error('创建生成任务失败')
  } finally {
    generating.value = false
  }
}

const handleViewTask = (task: AIGenerateTask) => {
  currentTask.value = task
  showTaskDetail.value = true
}

const handleDeleteTask = async (taskId: number) => {
  try {
    await deleteGenerateTask(taskId)
    Message.success('任务已删除')
    await loadTasks()
  } catch (error) {
    Message.error('删除任务失败')
  }
}

const handleRetryTask = async (taskId: number) => {
  try {
    await retryGenerateTask(taskId)
    Message.success('任务已重新提交')
    await loadTasks()
  } catch (error) {
    Message.error('重试任务失败')
  }
}

const handleCancelTask = async (taskId: number) => {
  try {
    await cancelGenerateTask(taskId)
    Message.success('任务已取消')
    await loadTasks()
  } catch (error) {
    Message.error('取消任务失败')
  }
}

const handleSaveCases = async (taskId: number, caseIndices: number[], module?: string) => {
  try {
    const result = await saveCasesToProject(taskId, {
      case_indices: caseIndices,
      module
    })
    Message.success(result.message)
    showTaskDetail.value = false
  } catch (error) {
    Message.error('保存用例失败')
  }
}

// 初始化
onMounted(() => {
  loadConfigs()
  loadTasks()
})
</script>

<style scoped>
.ai-generate-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-section,
.task-section {
  width: 100%;
}

.generate-config {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e5e6eb;
}

.generate-actions {
  margin-top: 20px;
  text-align: center;
}
</style>
```

### 5.4 任务列表组件

```vue
<!-- frontend/src/views/ai-generate/components/TaskList.vue -->

<template>
  <div class="task-list">
    <a-table
      :columns="columns"
      :data="tasks"
      :pagination="false"
      :loading="loading"
    >
      <template #status="{ record }">
        <a-tag :color="getStatusColor(record.status)">
          {{ getStatusText(record.status) }}
        </a-tag>
      </template>
      
      <template #progress="{ record }">
        <a-progress
          v-if="record.status === 'processing'"
          :percent="record.progress"
          size="small"
        />
        <span v-else-if="record.status === 'completed'">100%</span>
        <span v-else>-</span>
      </template>
      
      <template #input_type="{ record }">
        <a-tag>{{ getInputTypeText(record.input_type) }}</a-tag>
      </template>
      
      <template #generate_type="{ record }">
        <a-tag>{{ getGenerateTypeText(record.generate_type) }}</a-tag>
      </template>
      
      <template #created_at="{ record }">
        {{ formatTime(record.created_at) }}
      </template>
      
      <template #actions="{ record }">
        <a-space>
          <a-button
            v-if="record.status === 'completed'"
            type="text"
            size="small"
            @click="$emit('view', record)"
          >
            查看结果
          </a-button>
          <a-button
            v-if="record.status === 'failed'"
            type="text"
            size="small"
            @click="$emit('retry', record.id)"
          >
            重试
          </a-button>
          <a-button
            v-if="record.status === 'processing'"
            type="text"
            size="small"
            status="danger"
            @click="$emit('cancel', record.id)"
          >
            取消
          </a-button>
          <a-button
            v-if="record.status !== 'processing'"
            type="text"
            size="small"
            status="danger"
            @click="handleDelete(record.id)"
          >
            删除
          </a-button>
        </a-space>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Modal } from '@arco-design/web-vue'
import type { AIGenerateTask } from '@/api/aiGenerate'

const props = defineProps<{
  tasks: AIGenerateTask[]
  loading?: boolean
}>()

const emit = defineEmits<{
  refresh: []
  view: [task: AIGenerateTask]
  delete: [taskId: number]
  retry: [taskId: number]
  cancel: [taskId: number]
}>()

const columns = [
  { title: 'ID', dataIndex: 'id', width: 80 },
  { title: '输入类型', dataIndex: 'input_type', slotName: 'input_type', width: 120 },
  { title: '生成类型', dataIndex: 'generate_type', slotName: 'generate_type', width: 140 },
  { title: '状态', dataIndex: 'status', slotName: 'status', width: 100 },
  { title: '进度', dataIndex: 'progress', slotName: 'progress', width: 150 },
  { title: '生成数量', dataIndex: 'cases_count', width: 100 },
  { title: '创建时间', dataIndex: 'created_at', slotName: 'created_at', width: 180 },
  { title: '操作', slotName: 'actions', width: 200, fixed: 'right' }
]

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'blue',
    processing: 'orange',
    completed: 'green',
    failed: 'red',
    cancelled: 'gray'
  }
  return colors[status] || 'gray'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '等待中',
    processing: '生成中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const getInputTypeText = (type: string) => {
  const texts: Record<string, string> = {
    prd: 'PRD 文档',
    swagger: '接口文档',
    text: '文本输入'
  }
  return texts[type] || type
}

const getGenerateTypeText = (type: string) => {
  const texts: Record<string, string> = {
    functional: '功能测试',
    api: '接口测试',
    boundary: '边界值测试',
    combination: '组合测试'
  }
  return texts[type] || type
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const handleDelete = (taskId: number) => {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这个任务吗？',
    onOk: () => {
      emit('delete', taskId)
    }
  })
}
</script>

<style scoped>
.task-list {
  width: 100%;
}
</style>
```

### 5.5 任务详情组件

```vue
<!-- frontend/src/views/ai-generate/components/TaskDetail.vue -->

<template>
  <div class="task-detail">
    <!-- 任务信息 -->
    <div class="task-info">
      <a-descriptions :column="3" bordered>
        <a-descriptions-item label="任务 ID">{{ task.id }}</a-descriptions-item>
        <a-descriptions-item label="输入类型">{{ getInputTypeText(task.input_type) }}</a-descriptions-item>
        <a-descriptions-item label="生成类型">{{ getGenerateTypeText(task.generate_type) }}</a-descriptions-item>
        <a-descriptions-item label="AI 模型">{{ task.provider }} - {{ task.model_name }}</a-descriptions-item>
        <a-descriptions-item label="生成数量">{{ task.cases_count }} / {{ task.target_count }}</a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="getStatusColor(task.status)">
            {{ getStatusText(task.status) }}
          </a-tag>
        </a-descriptions-item>
      </a-descriptions>
    </div>
    
    <!-- 用例列表 -->
    <div class="case-list" v-if="task.status === 'completed'">
      <div class="case-header">
        <h3>生成的用例</h3>
        <a-space>
          <a-button @click="selectAll">全选</a-button>
          <a-button @click="selectNone">取消全选</a-button>
          <a-button type="primary" :disabled="!selectedCases.length" @click="handleSave">
            保存选中用例 ({{ selectedCases.length }})
          </a-button>
        </a-space>
      </div>
      
      <a-table
        :columns="caseColumns"
        :data="cases"
        :pagination="false"
        :row-selection="rowSelection"
        v-model:selectedKeys="selectedCases"
      >
        <template #name="{ record, rowIndex }">
          <a @click="handleEditCase(rowIndex)">{{ record.name }}</a>
        </template>
        
        <template #priority="{ record }">
          <a-tag :color="getPriorityColor(record.priority)">
            {{ record.priority }}
          </a-tag>
        </template>
        
        <template #actions="{ rowIndex }">
          <a-button type="text" size="small" @click="handleEditCase(rowIndex)">
            编辑
          </a-button>
        </template>
      </a-table>
    </div>
    
    <!-- 错误信息 -->
    <div class="error-info" v-if="task.status === 'failed'">
      <a-alert type="error" :content="task.error_message || '未知错误'" />
    </div>
    
    <!-- 用例编辑弹窗 -->
    <a-modal
      v-model:visible="showCaseEditor"
      title="编辑用例"
      :width="800"
      @ok="handleSaveCase"
    >
      <CaseEditor
        v-if="editingCase"
        v-model="editingCase"
      />
    </a-modal>
    
    <!-- 保存配置弹窗 -->
    <a-modal
      v-model:visible="showSaveConfig"
      title="保存配置"
      @ok="confirmSave"
    >
      <a-form layout="vertical">
        <a-form-item label="目标模块">
          <a-input v-model="saveModule" placeholder="输入模块名称（可选）" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import CaseEditor from './CaseEditor.vue'
import { getGeneratedCases, updateGeneratedCase } from '@/api/aiGenerate'
import type { AIGenerateTask } from '@/api/aiGenerate'

const props = defineProps<{
  task: AIGenerateTask
}>()

const emit = defineEmits<{
  save: [taskId: number, caseIndices: number[], module?: string]
}>()

// 状态
const cases = ref<any[]>([])
const selectedCases = ref<number[]>([])
const showCaseEditor = ref(false)
const editingCase = ref<any>(null)
const editingIndex = ref(-1)
const showSaveConfig = ref(false)
const saveModule = ref('')

// 表格配置
const caseColumns = [
  { title: '用例名称', dataIndex: 'name', slotName: 'name' },
  { title: '优先级', dataIndex: 'priority', slotName: 'priority', width: 100 },
  { title: '操作', slotName: 'actions', width: 100 }
]

const rowSelection = {
  type: 'checkbox',
  showCheckedAll: true
}

// 加载用例
const loadCases = async () => {
  try {
    const result = await getGeneratedCases(props.task.id)
    cases.value = result.cases
  } catch (error) {
    console.error('加载用例失败:', error)
  }
}

// 选择操作
const selectAll = () => {
  selectedCases.value = cases.value.map((_, index) => index)
}

const selectNone = () => {
  selectedCases.value = []
}

// 编辑用例
const handleEditCase = (index: number) => {
  editingIndex.value = index
  editingCase.value = { ...cases.value[index] }
  showCaseEditor.value = true
}

const handleSaveCase = async () => {
  try {
    await updateGeneratedCase(props.task.id, editingIndex.value, editingCase.value)
    cases.value[editingIndex.value] = { ...editingCase.value }
    showCaseEditor.value = false
    Message.success('用例已更新')
  } catch (error) {
    Message.error('更新用例失败')
  }
}

// 保存到项目
const handleSave = () => {
  if (!selectedCases.value.length) {
    Message.warning('请先选择要保存的用例')
    return
  }
  showSaveConfig.value = true
}

const confirmSave = () => {
  emit('save', props.task.id, selectedCases.value, saveModule.value || undefined)
  showSaveConfig.value = false
}

// 辅助函数
const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'blue',
    processing: 'orange',
    completed: 'green',
    failed: 'red',
    cancelled: 'gray'
  }
  return colors[status] || 'gray'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '等待中',
    processing: '生成中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const getInputTypeText = (type: string) => {
  const texts: Record<string, string> = {
    prd: 'PRD 文档',
    swagger: '接口文档',
    text: '文本输入'
  }
  return texts[type] || type
}

const getGenerateTypeText = (type: string) => {
  const texts: Record<string, string> = {
    functional: '功能测试',
    api: '接口测试',
    boundary: '边界值测试',
    combination: '组合测试'
  }
  return texts[type] || type
}

const getPriorityColor = (priority: string) => {
  const colors: Record<string, string> = {
    P0: 'red',
    P1: 'orange',
    P2: 'blue',
    P3: 'gray'
  }
  return colors[priority] || 'gray'
}

// 初始化
onMounted(() => {
  loadCases()
})
</script>

<style scoped>
.task-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.task-info {
  margin-bottom: 20px;
}

.case-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.case-header h3 {
  margin: 0;
}

.error-info {
  margin-top: 20px;
}
</style>
```

### 5.6 用例编辑组件

```vue
<!-- frontend/src/views/ai-generate/components/CaseEditor.vue -->

<template>
  <div class="case-editor">
    <a-form layout="vertical">
      <!-- 基本信息 -->
      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="用例名称">
            <a-input v-model="formData.name" placeholder="输入用例名称" />
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="优先级">
            <a-select v-model="formData.priority">
              <a-option value="P0">P0 - 最高</a-option>
              <a-option value="P1">P1 - 高</a-option>
              <a-option value="P2">P2 - 中</a-option>
              <a-option value="P3">P3 - 低</a-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>
      
      <!-- 接口测试用例特有字段 -->
      <template v-if="isApiCase">
        <a-row :gutter="16">
          <a-col :span="6">
            <a-form-item label="请求方法">
              <a-select v-model="formData.method">
                <a-option value="GET">GET</a-option>
                <a-option value="POST">POST</a-option>
                <a-option value="PUT">PUT</a-option>
                <a-option value="DELETE">DELETE</a-option>
                <a-option value="PATCH">PATCH</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="18">
            <a-form-item label="请求 URL">
              <a-input v-model="formData.url" placeholder="输入请求 URL" />
            </a-form-item>
          </a-col>
        </a-row>
        
        <!-- Headers -->
        <a-form-item label="请求头">
          <div v-for="(header, index) in formData.headers" :key="index" class="key-value-row">
            <a-input v-model="header.key" placeholder="Key" style="width: 200px" />
            <a-input v-model="header.value" placeholder="Value" style="flex: 1" />
            <a-button type="text" status="danger" @click="removeHeader(index)">
              <template #icon><icon-delete /></template>
            </a-button>
          </div>
          <a-button type="dashed" @click="addHeader">
            <template #icon><icon-plus /></template>
            添加请求头
          </a-button>
        </a-form-item>
        
        <!-- 断言 -->
        <a-form-item label="断言">
          <div v-for="(assertion, index) in formData.assertions" :key="index" class="assertion-row">
            <a-select v-model="assertion.assertion_type" style="width: 150px">
              <a-option value="status_code">状态码</a-option>
              <a-option value="jsonpath">JSONPath</a-option>
              <a-option value="body_contains">响应体包含</a-option>
            </a-select>
            <a-select v-model="assertion.operator" style="width: 120px">
              <a-option value="equals">等于</a-option>
              <a-option value="not_equals">不等于</a-option>
              <a-option value="contains">包含</a-option>
            </a-select>
            <a-input v-model="assertion.expected" placeholder="期望值" style="flex: 1" />
            <a-button type="text" status="danger" @click="removeAssertion(index)">
              <template #icon><icon-delete /></template>
            </a-button>
          </div>
          <a-button type="dashed" @click="addAssertion">
            <template #icon><icon-plus /></template>
            添加断言
          </a-button>
        </a-form-item>
      </template>
      
      <!-- 描述 -->
      <a-form-item label="描述">
        <a-textarea v-model="formData.description" placeholder="输入用例描述" :rows="4" />
      </a-form-item>
      
      <!-- 前置条件 -->
      <a-form-item label="前置条件">
        <a-textarea v-model="formData.preconditions" placeholder="输入前置条件" :rows="3" />
      </a-form-item>
    </a-form>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'

const props = defineProps<{
  modelValue: any
}>()

const emit = defineEmits<{
  'update:modelValue': [value: any]
}>()

const formData = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const isApiCase = computed(() => {
  return formData.value.method !== undefined
})

// Headers 操作
const addHeader = () => {
  if (!formData.value.headers) {
    formData.value.headers = []
  }
  formData.value.headers.push({ key: '', value: '' })
}

const removeHeader = (index: number) => {
  formData.value.headers.splice(index, 1)
}

// 断言操作
const addAssertion = () => {
  if (!formData.value.assertions) {
    formData.value.assertions = []
  }
  formData.value.assertions.push({
    assertion_type: 'status_code',
    operator: 'equals',
    expected: ''
  })
}

const removeAssertion = (index: number) => {
  formData.value.assertions.splice(index, 1)
}
</script>

<style scoped>
.case-editor {
  max-height: 60vh;
  overflow-y: auto;
}

.key-value-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}

.assertion-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}
</style>
```

### 5.7 路由配置

```typescript
// frontend/src/router/index.ts

import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // ... 其他路由
    {
      path: '/ai-generate',
      name: 'AIGenerate',
      component: () => import('@/views/ai-generate/index.vue'),
      meta: {
        title: 'AI 生成测试用例',
        requiresAuth: true
      }
    }
  ]
})

export default router
```

### 5.8 AI 配置组件（支持中转站）

```vue
<!-- frontend/src/views/ai-generate/components/AIConfig.vue -->

<template>
  <div class="ai-config">
    <!-- 配置列表 -->
    <div class="config-list">
      <div class="config-header">
        <h3>AI 模型配置</h3>
        <a-button type="primary" @click="showAddModal = true">
          <template #icon><icon-plus /></template>
          添加配置
        </a-button>
      </div>
      
      <a-table :columns="columns" :data="configs" :pagination="false">
        <template #provider="{ record }">
          <a-tag :color="getProviderColor(record.provider)">
            {{ getProviderName(record.provider) }}
          </a-tag>
        </template>
        
        <template #api_base_url="{ record }">
          <span v-if="record.api_base_url" class="url-text">
            {{ record.api_base_url }}
          </span>
          <span v-else class="default-text">官方默认</span>
        </template>
        
        <template #is_default="{ record }">
          <a-tag v-if="record.is_default" color="green">默认</a-tag>
        </template>
        
        <template #actions="{ record }">
          <a-space>
            <a-button type="text" size="small" @click="handleTest(record)">
              测试
            </a-button>
            <a-button type="text" size="small" @click="handleEdit(record)">
              编辑
            </a-button>
            <a-button type="text" size="small" status="danger" @click="handleDelete(record.id)">
              删除
            </a-button>
          </a-space>
        </template>
      </a-table>
    </div>
    
    <!-- 添加/编辑配置弹窗 -->
    <a-modal
      v-model:visible="showAddModal"
      :title="editingConfig ? '编辑配置' : '添加配置'"
      :width="600"
      @ok="handleSave"
      @cancel="resetForm"
    >
      <a-form :model="formData" layout="vertical">
        <!-- 提供商选择 -->
        <a-form-item label="AI 提供商" required>
          <a-select v-model="formData.provider" @change="handleProviderChange">
            <a-option value="openai">OpenAI</a-option>
            <a-option value="claude">Claude (Anthropic)</a-option>
            <a-option value="deepseek">DeepSeek</a-option>
            <a-option value="custom">自定义（兼容 OpenAI 接口）</a-option>
          </a-select>
        </a-form-item>
        
        <!-- API Key -->
        <a-form-item label="API Key" required>
          <a-input-password
            v-model="formData.api_key"
            placeholder="输入 API Key"
          />
        </a-form-item>
        
        <!-- 模型名称 -->
        <a-form-item label="模型名称" required>
          <a-select
            v-if="formData.provider !== 'custom'"
            v-model="formData.model_name"
            :options="modelOptions"
            placeholder="选择模型"
            allow-search
          />
          <a-input
            v-else
            v-model="formData.model_name"
            placeholder="输入模型名称，如 gpt-4-turbo"
          />
        </a-form-item>
        
        <!-- 自定义 API 端点 -->
        <a-form-item
          v-if="formData.provider === 'custom' || showCustomUrl"
          label="API 端点地址"
        >
          <a-input
            v-model="formData.api_base_url"
            :placeholder="apiUrlPlaceholder"
          />
          <div class="form-help">
            支持中转站或自建服务，如：
            <ul>
              <li>OpenAI 中转站：<code>https://api.example.com/v1</code></li>
              <li>本地 Ollama：<code>http://localhost:11434</code></li>
            </ul>
          </div>
        </a-form-item>
        
        <!-- 高级选项：自定义官方 API 地址 -->
        <a-form-item v-if="formData.provider !== 'custom'">
          <a-checkbox v-model="showCustomUrl">
            自定义 API 端点（使用中转站）
          </a-checkbox>
        </a-form-item>
        
        <!-- 设为默认 -->
        <a-form-item>
          <a-checkbox v-model="formData.is_default">设为默认配置</a-checkbox>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import {
  getAIConfigs,
  createAIConfig,
  updateAIConfig,
  deleteAIConfig,
  testAIConfig
} from '@/api/aiGenerate'
import type { AIProviderConfig, AIProviderConfigCreate } from '@/api/aiGenerate'

// 状态
const configs = ref<AIProviderConfig[]>([])
const showAddModal = ref(false)
const editingConfig = ref<AIProviderConfig | null>(null)
const showCustomUrl = ref(false)

// 表单数据
const formData = ref<AIProviderConfigCreate>({
  provider: 'openai',
  api_key: '',
  model_name: '',
  api_base_url: '',
  is_default: false
})

// 表格列配置
const columns = [
  { title: '提供商', dataIndex: 'provider', slotName: 'provider', width: 120 },
  { title: '模型', dataIndex: 'model_name', width: 180 },
  { title: 'API 端点', dataIndex: 'api_base_url', slotName: 'api_base_url', width: 250 },
  { title: '默认', dataIndex: 'is_default', slotName: 'is_default', width: 80 },
  { title: '操作', slotName: 'actions', width: 180 }
]

// 模型选项
const modelOptions = computed(() => {
  const models: Record<string, { label: string; value: string }[]> = {
    openai: [
      { label: 'GPT-4 Turbo', value: 'gpt-4-turbo' },
      { label: 'GPT-4', value: 'gpt-4' },
      { label: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' }
    ],
    claude: [
      { label: 'Claude 3 Opus', value: 'claude-3-opus-20240229' },
      { label: 'Claude 3 Sonnet', value: 'claude-3-sonnet-20240229' },
      { label: 'Claude 3 Haiku', value: 'claude-3-haiku-20240307' }
    ],
    deepseek: [
      { label: 'DeepSeek Chat', value: 'deepseek-chat' },
      { label: 'DeepSeek Coder', value: 'deepseek-coder' }
    ]
  }
  return models[formData.value.provider] || []
})

// API 端点占位符
const apiUrlPlaceholder = computed(() => {
  const placeholders: Record<string, string> = {
    openai: 'https://api.openai.com/v1',
    claude: 'https://api.anthropic.com',
    deepseek: 'https://api.deepseek.com/v1',
    custom: '输入 API 端点地址'
  }
  return placeholders[formData.value.provider] || ''
})

// 辅助函数
const getProviderColor = (provider: string) => {
  const colors: Record<string, string> = {
    openai: 'green',
    claude: 'purple',
    deepseek: 'blue',
    custom: 'gray'
  }
  return colors[provider] || 'gray'
}

const getProviderName = (provider: string) => {
  const names: Record<string, string> = {
    openai: 'OpenAI',
    claude: 'Claude',
    deepseek: 'DeepSeek',
    custom: '自定义'
  }
  return names[provider] || provider
}

// 事件处理
const handleProviderChange = () => {
  formData.value.model_name = ''
  formData.value.api_base_url = ''
  showCustomUrl.value = false
}

const handleSave = async () => {
  // 验证表单
  if (!formData.value.api_key) {
    Message.warning('请输入 API Key')
    return
  }
  if (!formData.value.model_name) {
    Message.warning('请选择或输入模型名称')
    return
  }
  if (formData.value.provider === 'custom' && !formData.value.api_base_url) {
    Message.warning('自定义提供商必须输入 API 端点地址')
    return
  }
  
  try {
    if (editingConfig.value) {
      await updateAIConfig(editingConfig.value.id, formData.value)
      Message.success('配置已更新')
    } else {
      await createAIConfig(formData.value)
      Message.success('配置已添加')
    }
    showAddModal.value = false
    resetForm()
    await loadConfigs()
  } catch (error) {
    Message.error('保存配置失败')
  }
}

const handleEdit = (config: AIProviderConfig) => {
  editingConfig.value = config
  formData.value = {
    provider: config.provider,
    api_key: '', // 不回显 API Key
    model_name: config.model_name,
    api_base_url: config.api_base_url || '',
    is_default: config.is_default
  }
  showCustomUrl.value = !!config.api_base_url
  showAddModal.value = true
}

const handleDelete = async (id: number) => {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这个配置吗？',
    onOk: async () => {
      try {
        await deleteAIConfig(id)
        Message.success('配置已删除')
        await loadConfigs()
      } catch (error) {
        Message.error('删除配置失败')
      }
    }
  })
}

const handleTest = async (config: AIProviderConfig) => {
  try {
    const result = await testAIConfig(config.id)
    if (result.success) {
      Message.success('配置有效')
    } else {
      Message.error(`配置无效: ${result.message}`)
    }
  } catch (error) {
    Message.error('测试配置失败')
  }
}

const resetForm = () => {
  formData.value = {
    provider: 'openai',
    api_key: '',
    model_name: '',
    api_base_url: '',
    is_default: false
  }
  editingConfig.value = null
  showCustomUrl.value = false
}

// 加载配置
const loadConfigs = async () => {
  try {
    configs.value = await getAIConfigs()
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

// 初始化
onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.ai-config {
  padding: 16px 0;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.config-header h3 {
  margin: 0;
}

.url-text {
  font-size: 12px;
  color: #86909c;
  word-break: break-all;
}

.default-text {
  color: #c9cdd4;
  font-style: italic;
}

.form-help {
  font-size: 12px;
  color: #86909c;
  margin-top: 4px;
}

.form-help ul {
  margin: 4px 0;
  padding-left: 16px;
}

.form-help code {
  background: #f2f3f5;
  padding: 2px 4px;
  border-radius: 2px;
  font-size: 11px;
}
</style>
```

---

## 6. 加密工具设计

```python
# server/utils/crypto.py

from cryptography.fernet import Fernet
from core.config import settings

# 从配置中获取加密密钥
ENCRYPTION_KEY = settings.AI_ENCRYPTION_KEY

def get_fernet():
    """获取 Fernet 加密实例"""
    return Fernet(ENCRYPTION_KEY.encode())

def encrypt_api_key(api_key: str) -> str:
    """加密 API Key"""
    f = get_fernet()
    return f.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """解密 API Key"""
    f = get_fernet()
    return f.decrypt(encrypted_key.encode()).decode()
```

**配置文件更新**：

```python
# server/core/config.py

class Settings(BaseSettings):
    # ... 其他配置
    
    # AI 功能配置
    AI_ENCRYPTION_KEY: str = ""  # API Key 加密密钥
    AI_FILE_UPLOAD_DIR: str = "uploads/ai"  # 文件上传目录
```

---

## 7. 依赖包

### 7.1 后端依赖

```txt
# requirements.txt 新增

# AI 相关
anthropic>=0.18.0
openai>=1.12.0

# 文档解析
python-docx>=0.8.11
PyPDF2>=3.0.0
pyyaml>=6.0

# 加密
cryptography>=41.0.0
```

### 7.2 前端依赖

```json
// package.json 新增

{
  "dependencies": {
    // ... 其他依赖
  }
}
```

前端无需新增依赖，使用现有的 Arco Design Vue 组件即可。

---

## 8. 实施计划

### Phase 1：基础架构（1-2 天）

1. 创建数据库模型和迁移
2. 实现加密工具
3. 搭建 AI 服务层框架

### Phase 2：后端核心功能（2-3 天）

1. 实现 Claude/OpenAI Provider
2. 实现 Prompt 引擎
3. 实现文档解析服务
4. 实现 Celery 任务
5. 实现 API 接口

### Phase 3：前端实现（2-3 天）

1. 实现 AI 配置管理页面
2. 实现文件上传组件
3. 实现任务列表组件
4. 实现用例编辑组件
5. 集成测试

### Phase 4：优化和完善（1-2 天）

1. 错误处理和边界情况
2. 用户体验优化
3. 文档编写

---

## 9. 风险和注意事项

### 9.1 安全风险

- **API Key 泄露**：必须加密存储，传输时使用 HTTPS
- **文件上传安全**：验证文件类型，限制文件大小，防止路径遍历攻击
- **Prompt 注入**：对用户输入进行清理，防止恶意 Prompt

### 9.2 性能风险

- **大文件处理**：PRD 文档可能很大，需要分块处理
- **批量生成**：大量用例生成可能超时，需要合理设置超时时间
- **并发控制**：限制同时运行的生成任务数量

### 9.3 成本控制

- **API 调用费用**：用户自行承担，平台不垫付
- **Token 用量**：监控每次调用的 Token 消耗，提供用量统计
- **模型选择**：推荐性价比高的模型（如 Claude Haiku）

---

## 10. 后续扩展

### 10.1 功能扩展

- **用例模板**：支持自定义用例模板
- **历史记录**：保存生成历史，支持回溯
- **批量导入**：支持批量导入接口文档
- **智能优化**：根据用户反馈优化 Prompt

### 10.2 模型扩展

- **本地模型**：支持 Ollama 等本地模型
- **自定义模型**：支持用户配置自定义 API 端点
- **模型对比**：支持多模型同时生成，对比结果

### 10.3 集成扩展

- **CI/CD 集成**：支持在 CI/CD 流程中自动生成用例
- **Jira 集成**：从 Jira 导入需求，生成用例后同步回 Jira
- **Swagger 自动同步**：定期从 Swagger URL 同步接口文档

---

**文档版本**：v1.0  
**创建日期**：2026-05-23  
**作者**：TestForge 团队
