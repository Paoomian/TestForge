# AI 生成测试用例功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 TestForge 测试平台添加 AI 生成测试用例功能，支持 PRD 文档、接口文档和自然语言描述作为输入源，生成多种类型的测试用例

**Architecture:** 基于异步任务队列（Celery）的架构，前端上传文档或输入文本，后端解析后调用 AI API 生成测试用例，用户可编辑后保存到用例系统。支持多模型（Claude、OpenAI、DeepSeek）和中转站配置

**Tech Stack:** FastAPI + SQLAlchemy + Celery + Vue 3 + TypeScript + Arco Design Vue

---

## 文件结构

### 后端文件

| 文件 | 职责 |
|------|------|
| `server/models/ai_generate.py` | AI 配置和生成任务的数据模型 |
| `server/schemas/ai_generate.py` | Pydantic schemas，请求/响应验证 |
| `server/utils/crypto.py` | API Key 加密/解密工具 |
| `server/services/ai_service.py` | AI 服务层，支持多模型和中转站 |
| `server/services/prompt_engine.py` | Prompt 模板引擎 |
| `server/services/document_parser.py` | 文档解析服务（PRD/Swagger） |
| `server/services/case_converter.py` | AI 生成结果转换为测试用例模型 |
| `server/tasks/ai_generate_tasks.py` | Celery 异步任务 |
| `server/api/ai_generate.py` | API 接口 |
| `server/migrations/add_ai_tables.py` | 数据库迁移 |

### 前端文件

| 文件 | 职责 |
|------|------|
| `frontend/src/api/aiGenerate.ts` | API 接口定义和类型 |
| `frontend/src/views/ai-generate/index.vue` | 页面入口 |
| `frontend/src/views/ai-generate/AIGeneratePage.vue` | 主页面组件 |
| `frontend/src/views/ai-generate/components/AIConfig.vue` | AI 配置管理（支持中转站） |
| `frontend/src/views/ai-generate/components/FileUpload.vue` | 文件上传组件 |
| `frontend/src/views/ai-generate/components/TextInput.vue` | 文本输入组件 |
| `frontend/src/views/ai-generate/components/TaskList.vue` | 任务列表组件 |
| `frontend/src/views/ai-generate/components/TaskDetail.vue` | 任务详情组件 |
| `frontend/src/views/ai-generate/components/CaseEditor.vue` | 用例编辑组件 |

---

## Task 1: 安装依赖

**Files:**
- Modify: `server/requirements_core.txt`

- [ ] **Step 1: 添加后端依赖**

```bash
cd server
pip install anthropic>=0.18.0 openai>=1.12.0 python-docx>=0.8.11 PyPDF2>=3.0.0 pyyaml>=6.0 cryptography>=41.0.0
```

- [ ] **Step 2: 更新 requirements_core.txt**

在 `server/requirements_core.txt` 末尾添加：

```
# AI 生成功能依赖
anthropic>=0.18.0
openai>=1.12.0
python-docx>=0.8.11
PyPDF2>=3.0.0
pyyaml>=6.0
cryptography>=41.0.0
```

- [ ] **Step 3: 验证安装**

```bash
cd server
python -c "import anthropic; import openai; import docx; import PyPDF2; import yaml; from cryptography.fernet import Fernet; print('所有依赖安装成功')"
```

Expected: `所有依赖安装成功`

- [ ] **Step 4: 提交**

```bash
git add server/requirements_core.txt
git commit -m "chore: 添加 AI 生成功能依赖"
```

---

## Task 2: 数据库模型和迁移

**Files:**
- Create: `server/models/ai_generate.py`
- Create: `server/migrations/add_ai_tables.py`
- Modify: `server/models/__init__.py`

- [ ] **Step 1: 创建数据模型**

创建 `server/models/ai_generate.py`：

```python
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
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)

    # 输入配置
    input_type = Column(String(20), nullable=False)  # prd / swagger / text
    input_content = Column(Text)  # 原始输入内容（文本类型或解析后的 JSON）
    input_file_path = Column(String(500))  # 上传文件路径
    input_file_name = Column(String(200))  # 原始文件名

    # 生成配置
    generate_type = Column(String(20), nullable=False)  # functional / api / boundary / combination
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
```

- [ ] **Step 2: 更新模型索引**

在 `server/models/__init__.py` 中添加导入：

```python
from models.ai_generate import AIProviderConfig, AIGenerateTask
```

- [ ] **Step 3: 创建迁移文件**

创建 `server/migrations/add_ai_tables.py`：

```python
"""添加 AI 生成相关表

迁移 ID: add_ai_tables
创建时间: 2026-05-23
"""

from migrations.base import BaseMigration


class Migration(BaseMigration):
    """添加 AI 生成相关表"""

    def upgrade(self):
        # 创建 ai_provider_configs 表
        self.execute("""
            CREATE TABLE IF NOT EXISTS ai_provider_configs (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                user_id INTEGER NOT NULL,
                provider VARCHAR(50) NOT NULL,
                api_key VARCHAR(500) NOT NULL,
                model_name VARCHAR(100) NOT NULL,
                api_base_url VARCHAR(500),
                is_default BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                INDEX ix_ai_provider_configs_user_id (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 创建 ai_generate_tasks 表
        self.execute("""
            CREATE TABLE IF NOT EXISTS ai_generate_tasks (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                user_id INTEGER NOT NULL,
                project_id INTEGER NOT NULL,
                input_type VARCHAR(20) NOT NULL,
                input_content TEXT,
                input_file_path VARCHAR(500),
                input_file_name VARCHAR(200),
                generate_type VARCHAR(20) NOT NULL,
                provider VARCHAR(50) NOT NULL,
                model_name VARCHAR(100) NOT NULL,
                target_count INTEGER DEFAULT 10,
                status VARCHAR(20) DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                error_message TEXT,
                generated_cases JSON,
                cases_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (project_id) REFERENCES projects(id),
                INDEX ix_ai_generate_tasks_user_id (user_id),
                INDEX ix_ai_generate_tasks_project_id (project_id),
                INDEX ix_ai_generate_tasks_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

    def downgrade(self):
        self.execute("DROP TABLE IF EXISTS ai_generate_tasks")
        self.execute("DROP TABLE IF EXISTS ai_provider_configs")


# 实例化迁移对象供升级工具使用
migration = Migration()
```

- [ ] **Step 4: 运行迁移**

```bash
cd server
python migrations/upgrade_all.py
```

Expected: 迁移成功执行

- [ ] **Step 5: 验证表创建**

```bash
cd server
python -c "
from database import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print('ai_provider_configs' in tables)
print('ai_generate_tasks' in tables)
"
```

Expected: `True` `True`

- [ ] **Step 6: 提交**

```bash
git add server/models/ai_generate.py server/migrations/add_ai_tables.py server/models/__init__.py
git commit -m "feat: 添加 AI 生成相关数据库模型和迁移"
```

---

## Task 3: 加密工具

**Files:**
- Create: `server/utils/crypto.py`
- Modify: `server/core/config.py`
- Modify: `server/.env.example`

- [ ] **Step 1: 更新配置**

在 `server/core/config.py` 的 `Settings` 类中添加：

```python
# AI 功能配置
AI_ENCRYPTION_KEY: str = ""  # API Key 加密密钥
AI_FILE_UPLOAD_DIR: str = "uploads/ai"  # 文件上传目录
```

- [ ] **Step 2: 更新 .env.example**

在 `server/.env.example` 末尾添加：

```
# AI 功能配置
AI_ENCRYPTION_KEY=your-encryption-key-here
AI_FILE_UPLOAD_DIR=uploads/ai
```

- [ ] **Step 3: 创建加密工具**

创建 `server/utils/crypto.py`：

```python
from cryptography.fernet import Fernet
from core.config import settings


def get_fernet() -> Fernet:
    """获取 Fernet 加密实例"""
    key = settings.AI_ENCRYPTION_KEY
    if not key:
        raise ValueError("AI_ENCRYPTION_KEY 未配置，请在 .env 文件中设置")
    # 确保 key 是有效的 Fernet key
    if len(key) != 44 or not key.endswith('='):
        # 如果不是有效的 Fernet key，使用它生成一个
        import hashlib
        key = hashlib.sha256(key.encode()).digest()
        import base64
        key = base64.urlsafe_b64encode(key)
    return Fernet(key)


def encrypt_api_key(api_key: str) -> str:
    """加密 API Key"""
    f = get_fernet()
    return f.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """解密 API Key"""
    f = get_fernet()
    return f.decrypt(encrypted_key.encode()).decode()


def generate_encryption_key() -> str:
    """生成新的加密密钥"""
    return Fernet.generate_key().decode()
```

- [ ] **Step 4: 测试加密工具**

```bash
cd server
python -c "
import os
os.environ['AI_ENCRYPTION_KEY'] = 'test-key-for-development-only-1234'
from utils.crypto import encrypt_api_key, decrypt_api_key

# 测试加密解密
original = 'sk-test-api-key-12345'
encrypted = encrypt_api_key(original)
decrypted = decrypt_api_key(encrypted)

print(f'原始: {original}')
print(f'加密: {encrypted}')
print(f'解密: {decrypted}')
print(f'验证: {original == decrypted}')
"
```

Expected: `验证: True`

- [ ] **Step 5: 生成正式密钥**

```bash
cd server
python -c "
from utils.crypto import generate_encryption_key
print(generate_encryption_key())
"
```

将生成的密钥添加到 `server/.env` 文件：

```
AI_ENCRYPTION_KEY=<生成的密钥>
```

- [ ] **Step 6: 提交**

```bash
git add server/utils/crypto.py server/core/config.py server/.env.example
git commit -m "feat: 添加 API Key 加密工具"
```

---

## Task 4: AI 服务层

**Files:**
- Create: `server/services/ai_service.py`

- [ ] **Step 1: 创建 AI 服务层**

创建 `server/services/ai_service.py`：

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


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
    async def validate_api_key(self) -> bool:
        """验证 API Key 是否有效"""
        pass


class ClaudeProvider(AIProvider):
    """Claude API 提供商"""

    def __init__(self, api_key: str, api_base_url: Optional[str] = None):
        super().__init__(api_key, api_base_url)
        self.base_url = api_base_url or "https://api.anthropic.com"

    async def chat(self, messages: List[Dict[str, str]], model: str) -> str:
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

    async def validate_api_key(self) -> bool:
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(
                api_key=self.api_key,
                base_url=self.base_url
            )
            await client.messages.create(
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
        self.base_url = api_base_url or "https://api.openai.com/v1"

    async def chat(self, messages: List[Dict[str, str]], model: str) -> str:
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

    async def validate_api_key(self) -> bool:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            await client.chat.completions.create(
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

    _providers = {
        "claude": ClaudeProvider,
        "openai": OpenAIProvider,
        "deepseek": DeepSeekProvider,
        "custom": CustomProvider,
    }

    @classmethod
    def create_provider(
        cls,
        provider: str,
        api_key: str,
        api_base_url: Optional[str] = None
    ) -> AIProvider:
        """创建 AI 提供商实例"""
        if provider not in cls._providers:
            raise ValueError(f"不支持的 AI 提供商: {provider}，支持: {', '.join(cls._providers.keys())}")

        return cls._providers[provider](api_key, api_base_url)

    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """获取支持的提供商列表"""
        return list(cls._providers.keys())
```

- [ ] **Step 2: 测试 AI 服务层**

```bash
cd server
python -c "
from services.ai_service import AIServiceFactory

# 测试工厂方法
providers = AIServiceFactory.get_supported_providers()
print(f'支持的提供商: {providers}')

# 测试创建实例
provider = AIServiceFactory.create_provider('openai', 'test-key')
print(f'创建 OpenAI 提供商成功: {type(provider).__name__}')

provider = AIServiceFactory.create_provider('claude', 'test-key')
print(f'创建 Claude 提供商成功: {type(provider).__name__}')

# 测试自定义提供商
provider = AIServiceFactory.create_provider('custom', 'test-key', 'https://api.example.com/v1')
print(f'创建自定义提供商成功: {type(provider).__name__}')

print('AI 服务层测试通过')
"
```

Expected: `AI 服务层测试通过`

- [ ] **Step 3: 提交**

```bash
git add server/services/ai_service.py
git commit -m "feat: 实现 AI 服务层，支持多模型和中转站"
```

---

## Task 5: Prompt 引擎

**Files:**
- Create: `server/services/prompt_engine.py`

- [ ] **Step 1: 创建 Prompt 引擎**

创建 `server/services/prompt_engine.py`：

```python
from typing import List, Dict


PROMPT_TEMPLATES = {
    "functional": {
        "system": """你是一个资深的测试工程师，擅长根据需求文档生成功能测试用例。

要求：
1. 用例覆盖正常流程、异常流程、边界条件
2. 每个用例包含：用例名称、前置条件、测试步骤、预期结果、优先级
3. 用例名称简洁明确，步骤可执行
4. 必须以 JSON 格式返回，不要包含其他内容""",

        "user": """请根据以下需求文档生成功能测试用例：

{input_content}

请生成 {count} 个测试用例，覆盖以下维度：
- 正常流程测试
- 异常流程测试
- 边界值测试
- 权限测试（如适用）

请严格以 JSON 数组格式返回，结构如下：
[
  {{
    "name": "用例名称",
    "priority": "P1",
    "preconditions": "前置条件",
    "steps": ["步骤1", "步骤2"],
    "expected_result": "预期结果",
    "test_type": "normal/exception/boundary"
  }}
]"""
    },

    "api": {
        "system": """你是一个接口测试专家，擅长根据接口文档生成接口测试用例。

要求：
1. 每个接口生成：正向用例、参数校验用例、边界值用例
2. 输出格式为 JSON，包含完整的请求配置和断言
3. 断言覆盖状态码、响应时间、关键字段
4. 考虑认证、鉴权场景
5. 必须以 JSON 格式返回，不要包含其他内容""",

        "user": """请根据以下接口文档生成接口测试用例：

{input_content}

请为每个接口生成测试用例，包含：
- 请求方法、URL、Headers
- 请求体（如适用）
- 预期状态码和响应断言
- 数据提取规则（如需要）

请严格以 JSON 数组格式返回，结构如下：
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
]"""
    },

    "boundary": {
        "system": """你是一个边界值测试专家，擅长分析输入参数的边界条件。

要求：
1. 识别所有输入参数
2. 分析每个参数的边界值（最小值、最大值、空值、特殊字符）
3. 生成边界值测试用例
4. 包含预期结果和错误提示
5. 必须以 JSON 格式返回，不要包含其他内容""",

        "user": """请分析以下功能描述的边界条件：

{input_content}

请生成边界值测试用例，覆盖：
- 数值边界（最小值、最大值、临界值）
- 字符串边界（空字符串、最大长度、特殊字符）
- 日期时间边界
- 集合边界（空集合、单元素、最大数量）

请严格以 JSON 数组格式返回，结构如下：
[
  {{
    "name": "用例名称",
    "parameter": "参数名",
    "boundary_type": "min/max/empty/special",
    "test_value": "测试值",
    "expected_result": "预期结果",
    "priority": "P2"
  }}
]"""
    },

    "combination": {
        "system": """你是一个组合测试专家，擅长使用正交表和 Pairwise 方法生成组合测试用例。

要求：
1. 识别所有输入参数及其取值
2. 使用 Pairwise 方法生成最小覆盖集
3. 输出测试用例矩阵
4. 标注每个用例的覆盖情况
5. 必须以 JSON 格式返回，不要包含其他内容""",

        "user": """请分析以下功能的输入参数组合：

{input_content}

请使用 Pairwise 方法生成组合测试用例，要求：
- 识别所有参数及取值
- 生成最小测试用例集
- 确保两两覆盖
- 输出用例矩阵

请严格以 JSON 数组格式返回，结构如下：
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
]"""
    }
}


class PromptEngine:
    """Prompt 引擎"""

    @staticmethod
    def build_messages(
        generate_type: str,
        input_content: str,
        count: int = 10
    ) -> List[Dict[str, str]]:
        """构建 AI 对话消息

        Args:
            generate_type: 生成类型 (functional/api/boundary/combination)
            input_content: 输入内容
            count: 期望生成的用例数量

        Returns:
            消息列表，包含 system 和 user 消息
        """
        template = PROMPT_TEMPLATES.get(generate_type)
        if not template:
            raise ValueError(f"不支持的生成类型: {generate_type}，支持: {', '.join(PROMPT_TEMPLATES.keys())}")

        return [
            {"role": "system", "content": template["system"]},
            {"role": "user", "content": template["user"].format(
                input_content=input_content,
                count=count
            )}
        ]

    @staticmethod
    def get_supported_types() -> List[str]:
        """获取支持的生成类型"""
        return list(PROMPT_TEMPLATES.keys())
```

- [ ] **Step 2: 测试 Prompt 引擎**

```bash
cd server
python -c "
from services.prompt_engine import PromptEngine

# 测试构建消息
messages = PromptEngine.build_messages('api', 'GET /api/users', 5)
print(f'消息数量: {len(messages)}')
print(f'System 消息长度: {len(messages[0][\"content\"])}')
print(f'User 消息包含输入: {\"GET /api/users\" in messages[1][\"content\"]}')

# 测试支持的类型
types = PromptEngine.get_supported_types()
print(f'支持的类型: {types}')

print('Prompt 引擎测试通过')
"
```

Expected: `Prompt 引擎测试通过`

- [ ] **Step 3: 提交**

```bash
git add server/services/prompt_engine.py
git commit -m "feat: 实现 Prompt 引擎"
```

---

## Task 6: Schemas

**Files:**
- Create: `server/schemas/ai_generate.py`

- [ ] **Step 1: 创建 Schemas**

创建 `server/schemas/ai_generate.py`：

```python
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel


# ==================== AI 配置 Schemas ====================

class AIProviderConfigCreate(BaseModel):
    """创建 AI 配置请求"""
    provider: str  # claude / openai / deepseek / custom
    api_key: str
    model_name: str
    api_base_url: Optional[str] = None
    is_default: bool = False


class AIProviderConfigUpdate(BaseModel):
    """更新 AI 配置请求"""
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    api_base_url: Optional[str] = None
    is_default: Optional[bool] = None


class AIProviderConfigOut(BaseModel):
    """AI 配置响应"""
    id: int
    user_id: int
    provider: str
    model_name: str
    api_base_url: Optional[str] = None
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIConfigTestResult(BaseModel):
    """AI 配置测试结果"""
    success: bool
    message: str


# ==================== 生成任务 Schemas ====================

class AIGenerateTaskCreate(BaseModel):
    """创建生成任务请求"""
    project_id: int
    input_type: str  # prd / swagger / text
    input_content: Optional[str] = None
    input_file_path: Optional[str] = None
    input_file_name: Optional[str] = None
    generate_type: str  # functional / api / boundary / combination
    config_id: Optional[int] = None  # 指定使用哪个配置，不传则使用默认
    target_count: int = 10


class AIGenerateTaskOut(BaseModel):
    """生成任务响应"""
    id: int
    user_id: int
    project_id: int
    input_type: str
    input_content: Optional[str] = None
    input_file_path: Optional[str] = None
    input_file_name: Optional[str] = None
    generate_type: str
    provider: str
    model_name: str
    target_count: int
    status: str
    progress: int
    error_message: Optional[str] = None
    generated_cases: Optional[List[Any]] = None
    cases_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIGenerateTaskListOut(BaseModel):
    """生成任务列表响应（不含生成结果）"""
    id: int
    user_id: int
    project_id: int
    input_type: str
    input_file_name: Optional[str] = None
    generate_type: str
    provider: str
    model_name: str
    target_count: int
    status: str
    progress: int
    cases_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 文档上传响应 ====================

class DocumentUploadOut(BaseModel):
    """文档上传响应"""
    file_path: str
    file_name: str
    parsed_content: Any


# ==================== 结果操作 ====================

class SaveCasesRequest(BaseModel):
    """保存用例请求"""
    case_indices: Optional[List[int]] = None  # 不传则保存全部
    module: Optional[str] = None


class SaveCasesResult(BaseModel):
    """保存用例结果"""
    message: str
    saved_count: int


class GeneratedCaseUpdate(BaseModel):
    """更新生成的用例"""
    # 接受任意字段
    class Config:
        from_attributes = True
```

- [ ] **Step 2: 提交**

```bash
git add server/schemas/ai_generate.py
git commit -m "feat: 添加 AI 生成相关 Schemas"
```

---

## Task 7: API 接口

**Files:**
- Create: `server/api/ai_generate.py`
- Modify: `server/main.py`

- [ ] **Step 1: 创建 API 接口**

创建 `server/api/ai_generate.py`：

```python
import os
import json
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
from utils.auth import get_current_user
from utils.crypto import encrypt_api_key, decrypt_api_key
from core.config import settings

router = APIRouter(prefix="/ai-generate", tags=["AI 生成"])


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

    return DocumentUploadOut(
        file_path=file_path,
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

    return DocumentUploadOut(
        file_path=file_path,
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
        provider=db_config.provider,
        model_name=db_config.model_name,
        target_count=task.target_count
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # 异步执行生成任务
    generate_test_cases.delay(db_task.id, db_config.id)

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
    generate_test_cases.delay(task.id, db_config.id)

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

    # 确定要保存的用例
    cases_to_save = task.generated_cases
    if request.case_indices:
        cases_to_save = [
            task.generated_cases[i]
            for i in request.case_indices
            if 0 <= i < len(task.generated_cases)
        ]

    # 转换并保存用例
    saved_count = 0
    errors = []
    for idx, case_data in enumerate(cases_to_save):
        try:
            test_case = convert_to_test_case(
                case_data=case_data,
                project_id=task.project_id,
                generate_type=task.generate_type,
                module=request.module,
                creator_id=current_user.id
            )
            db.add(test_case)
            saved_count += 1
        except Exception as e:
            errors.append(f"用例 {idx + 1}: {str(e)}")

    db.commit()

    message = f"成功保存 {saved_count} 个用例"
    if errors:
        message += f"，{len(errors)} 个失败"

    return SaveCasesResult(message=message, saved_count=saved_count)
```

- [ ] **Step 2: 注册路由**

在 `server/main.py` 中添加：

```python
from api.ai_generate import router as ai_generate_router

app.include_router(ai_generate_router, prefix="/api")
```

- [ ] **Step 3: 提交**

```bash
git add server/api/ai_generate.py server/main.py
git commit -m "feat: 实现 AI 生成相关 API 接口"
```

---

## Task 8: 文档解析服务

**Files:**
- Create: `server/services/document_parser.py`

- [ ] **Step 1: 创建文档解析服务**

创建 `server/services/document_parser.py`：

```python
import os
import json
from typing import Dict, Any, List


class DocumentParser:
    """文档解析器"""

    @staticmethod
    def parse_prd(file_path: str) -> Dict[str, Any]:
        """解析 PRD 文档

        支持格式：.docx, .pdf, .md

        Returns:
            {
                "title": "文档标题",
                "content": "文档内容（纯文本）",
                "sections": [{"title": "章节标题", "content": "章节内容"}]
            }
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.docx':
            return DocumentParser._parse_docx(file_path)
        elif ext == '.pdf':
            return DocumentParser._parse_pdf(file_path)
        elif ext == '.md':
            return DocumentParser._parse_markdown(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

    @staticmethod
    def parse_swagger(file_path: str) -> Dict[str, Any]:
        """解析 Swagger/OpenAPI 文档

        支持格式：.json, .yaml

        Returns:
            {
                "info": {"title": "API 标题", "version": "版本", "description": "描述"},
                "endpoints": [{"path": "/api/users", "method": "GET", ...}]
            }
        """
        ext = os.path.splitext(file_path)[1].lower()

        with open(file_path, 'r', encoding='utf-8') as f:
            if ext == '.json':
                content = json.load(f)
            elif ext in ['.yaml', '.yml']:
                import yaml
                content = yaml.safe_load(f)
            else:
                raise ValueError(f"不支持的文件格式: {ext}")

        return DocumentParser._parse_swagger_content(content)

    @staticmethod
    def _parse_docx(file_path: str) -> Dict[str, Any]:
        """解析 Word 文档"""
        from docx import Document

        doc = Document(file_path)
        sections = []
        current_section = {"title": "", "content": ""}

        for para in doc.paragraphs:
            if para.style.name.startswith('Heading'):
                # 保存当前章节
                if current_section["content"].strip():
                    sections.append(current_section.copy())
                # 开始新章节
                current_section = {
                    "title": para.text.strip(),
                    "content": ""
                }
            else:
                current_section["content"] += para.text + "\n"

        # 保存最后一个章节
        if current_section["content"].strip():
            sections.append(current_section)

        # 提取标题
        title = sections[0]["title"] if sections else os.path.basename(file_path)

        # 合并所有内容
        full_content = "\n\n".join([
            f"{s['title']}\n{s['content']}" if s['title'] else s['content']
            for s in sections
        ])

        return {
            "title": title,
            "content": full_content,
            "sections": sections
        }

    @staticmethod
    def _parse_pdf(file_path: str) -> Dict[str, Any]:
        """解析 PDF 文档"""
        from PyPDF2 import PdfReader

        reader = PdfReader(file_path)
        content = ""

        for page in reader.pages:
            content += page.extract_text() + "\n"

        return {
            "title": os.path.basename(file_path),
            "content": content.strip(),
            "sections": [{"title": "全文", "content": content.strip()}]
        }

    @staticmethod
    def _parse_markdown(file_path: str) -> Dict[str, Any]:
        """解析 Markdown 文档"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 简单按 # 标题分割
        sections = []
        current_section = {"title": "", "content": ""}

        for line in content.split('\n'):
            if line.startswith('# '):
                if current_section["content"].strip():
                    sections.append(current_section.copy())
                current_section = {
                    "title": line[2:].strip(),
                    "content": ""
                }
            elif line.startswith('## '):
                if current_section["content"].strip():
                    sections.append(current_section.copy())
                current_section = {
                    "title": line[3:].strip(),
                    "content": ""
                }
            else:
                current_section["content"] += line + "\n"

        if current_section["content"].strip():
            sections.append(current_section)

        title = sections[0]["title"] if sections else os.path.basename(file_path)

        return {
            "title": title,
            "content": content,
            "sections": sections
        }

    @staticmethod
    def _parse_swagger_content(content: Dict) -> Dict[str, Any]:
        """解析 Swagger 内容"""
        info = content.get('info', {})

        endpoints = []
        paths = content.get('paths', {})

        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                    # 提取参数
                    parameters = details.get('parameters', [])

                    # 提取请求体
                    request_body = details.get('requestBody', {})

                    # 提取响应
                    responses = details.get('responses', {})

                    endpoint = {
                        'path': path,
                        'method': method.upper(),
                        'summary': details.get('summary', ''),
                        'description': details.get('description', ''),
                        'parameters': parameters,
                        'request_body': request_body,
                        'responses': responses,
                        'tags': details.get('tags', [])
                    }
                    endpoints.append(endpoint)

        return {
            'info': {
                'title': info.get('title', 'Unknown API'),
                'version': info.get('version', '1.0.0'),
                'description': info.get('description', '')
            },
            'endpoints': endpoints
        }

    @staticmethod
    def format_swagger_for_prompt(swagger_data: Dict[str, Any]) -> str:
        """将 Swagger 数据格式化为适合 Prompt 的文本"""
        lines = []
        info = swagger_data.get('info', {})
        lines.append(f"API: {info.get('title', 'Unknown')}")
        lines.append(f"版本: {info.get('version', '1.0.0')}")
        if info.get('description'):
            lines.append(f"描述: {info['description']}")
        lines.append("")

        for endpoint in swagger_data.get('endpoints', []):
            lines.append(f"### {endpoint['method']} {endpoint['path']}")
            if endpoint.get('summary'):
                lines.append(f"说明: {endpoint['summary']}")
            if endpoint.get('description'):
                lines.append(f"描述: {endpoint['description']}")

            # 参数
            if endpoint.get('parameters'):
                lines.append("参数:")
                for param in endpoint['parameters']:
                    param_type = param.get('schema', {}).get('type', 'string')
                    required = '必填' if param.get('required') else '可选'
                    lines.append(f"  - {param.get('name', '')} ({param_type}, {required}): {param.get('description', '')}")

            # 请求体
            if endpoint.get('request_body'):
                rb = endpoint['request_body']
                if 'content' in rb:
                    for content_type, content_data in rb['content'].items():
                        lines.append(f"请求体 ({content_type}):")
                        if 'schema' in content_data:
                            lines.append(f"  Schema: {json.dumps(content_data['schema'], ensure_ascii=False, indent=2)}")

            # 响应
            if endpoint.get('responses'):
                lines.append("响应:")
                for status, resp in endpoint['responses'].items():
                    desc = resp.get('description', '')
                    lines.append(f"  - {status}: {desc}")

            lines.append("")

        return "\n".join(lines)
```

- [ ] **Step 2: 测试文档解析**

```bash
cd server
python -c "
from services.document_parser import DocumentParser

# 测试 Swagger 解析
swagger_content = {
    'info': {'title': 'Test API', 'version': '1.0'},
    'paths': {
        '/api/users': {
            'get': {
                'summary': '获取用户列表',
                'parameters': [{'name': 'page', 'in': 'query', 'schema': {'type': 'integer'}}],
                'responses': {'200': {'description': '成功'}}
            }
        }
    }
}

result = DocumentParser._parse_swagger_content(swagger_content)
print(f'端点数量: {len(result[\"endpoints\"])}')
print(f'第一个端点: {result[\"endpoints\"][0][\"method\"]} {result[\"endpoints\"][0][\"path\"]}')

# 测试格式化
formatted = DocumentParser.format_swagger_for_prompt(result)
print(f'格式化后长度: {len(formatted)}')

print('文档解析服务测试通过')
"
```

Expected: `文档解析服务测试通过`

- [ ] **Step 3: 提交**

```bash
git add server/services/document_parser.py
git commit -m "feat: 实现文档解析服务"
```

---

## Task 9: 用例转换服务

**Files:**
- Create: `server/services/case_converter.py`

- [ ] **Step 1: 创建用例转换服务**

创建 `server/services/case_converter.py`：

```python
from typing import Dict, Any, List, Optional
from models.api_test_case import APITestCase


def convert_to_test_case(
    case_data: Dict[str, Any],
    project_id: int,
    generate_type: str,
    module: Optional[str] = None,
    creator_id: Optional[int] = None
) -> APITestCase:
    """将 AI 生成的用例数据转换为测试用例模型

    Args:
        case_data: AI 生成的用例数据
        project_id: 项目 ID
        generate_type: 生成类型
        module: 模块名称
        creator_id: 创建者 ID

    Returns:
        APITestCase 实例
    """
    converters = {
        "api": _convert_api_case,
        "functional": _convert_functional_case,
        "boundary": _convert_boundary_case,
        "combination": _convert_combination_case,
    }

    converter = converters.get(generate_type)
    if not converter:
        raise ValueError(f"不支持的生成类型: {generate_type}")

    return converter(case_data, project_id, module, creator_id)


def _convert_api_case(
    case_data: Dict[str, Any],
    project_id: int,
    module: Optional[str],
    creator_id: Optional[int]
) -> APITestCase:
    """转换接口测试用例"""
    # 转换 headers
    headers = []
    for h in case_data.get("headers", []):
        headers.append({
            "enabled": True,
            "key": h.get("key", ""),
            "value": h.get("value", ""),
            "sort_order": len(headers)
        })

    # 转换 query_params
    query_params = []
    for p in case_data.get("query_params", []):
        query_params.append({
            "enabled": True,
            "key": p.get("key", ""),
            "value": p.get("value", ""),
            "sort_order": len(query_params)
        })

    # 转换 assertions
    assertions = []
    for a in case_data.get("assertions", []):
        assertions.append({
            "assertion_type": a.get("assertion_type", "status_code"),
            "operator": a.get("operator", "equals"),
            "field": a.get("field", ""),
            "expected": a.get("expected", ""),
            "sort_order": len(assertions)
        })

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
        headers=headers,
        query_params=query_params,
        assertions=assertions
    )


def _convert_functional_case(
    case_data: Dict[str, Any],
    project_id: int,
    module: Optional[str],
    creator_id: Optional[int]
) -> APITestCase:
    """转换功能测试用例"""
    # 构建描述
    preconditions = case_data.get("preconditions", "无")
    steps = case_data.get("steps", [])
    expected_result = case_data.get("expected_result", "")

    description_parts = [f"前置条件: {preconditions}", "", "测试步骤:"]
    for i, step in enumerate(steps, 1):
        description_parts.append(f"{i}. {step}")
    description_parts.extend(["", f"预期结果: {expected_result}"])

    return APITestCase(
        project_id=project_id,
        module=module,
        name=case_data.get("name", "未命名用例"),
        description="\n".join(description_parts),
        preconditions=preconditions,
        method="GET",  # 默认值，用户需要手动修改
        url="/",  # 默认值，用户需要手动修改
        priority=case_data.get("priority", "P2"),
        status="draft",
        creator_id=creator_id
    )


def _convert_boundary_case(
    case_data: Dict[str, Any],
    project_id: int,
    module: Optional[str],
    creator_id: Optional[int]
) -> APITestCase:
    """转换边界值测试用例"""
    parameter = case_data.get("parameter", "")
    boundary_type = case_data.get("boundary_type", "")
    test_value = case_data.get("test_value", "")
    expected_result = case_data.get("expected_result", "")

    description = f"参数: {parameter}\n边界类型: {boundary_type}\n测试值: {test_value}\n预期结果: {expected_result}"

    return APITestCase(
        project_id=project_id,
        module=module,
        name=case_data.get("name", "未命名用例"),
        description=description,
        method="GET",
        url="/",
        priority=case_data.get("priority", "P2"),
        status="draft",
        creator_id=creator_id
    )


def _convert_combination_case(
    case_data: Dict[str, Any],
    project_id: int,
    module: Optional[str],
    creator_id: Optional[int]
) -> APITestCase:
    """转换组合测试用例"""
    parameters = case_data.get("parameters", {})
    coverage = case_data.get("coverage", [])

    param_desc = "\n".join([f"  {k}: {v}" for k, v in parameters.items()])
    coverage_desc = "\n".join([f"  - {c}" for c in coverage])

    description = f"参数组合:\n{param_desc}\n\n覆盖情况:\n{coverage_desc}"

    return APITestCase(
        project_id=project_id,
        module=module,
        name=case_data.get("name", "未命名用例"),
        description=description,
        method="GET",
        url="/",
        priority=case_data.get("priority", "P2"),
        status="draft",
        creator_id=creator_id
    )
```

- [ ] **Step 2: 提交**

```bash
git add server/services/case_converter.py
git commit -m "feat: 实现用例转换服务"
```

---

## Task 10: Celery 任务

**Files:**
- Create: `server/tasks/ai_generate_tasks.py`

- [ ] **Step 1: 创建 Celery 任务**

创建 `server/tasks/ai_generate_tasks.py`：

```python
import json
import re
import asyncio
from datetime import datetime
from celery import shared_task

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


def extract_json_from_response(response: str) -> list:
    """从 AI 响应中提取 JSON 数组"""
    # 尝试直接解析
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass

    # 尝试提取 ```json ... ``` 代码块
    json_block_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
    match = re.search(json_block_pattern, response)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 尝试提取 [...] JSON 数组
    array_pattern = r'\[[\s\S]*\]'
    match = re.search(array_pattern, response)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError("无法从 AI 响应中提取有效的 JSON 数组")


@shared_task(bind=True, max_retries=2)
def generate_test_cases(self, task_id: int, config_id: int):
    """生成测试用例的 Celery 任务

    Args:
        task_id: 任务 ID
        config_id: AI 配置 ID
    """
    db = SessionLocal()

    try:
        # 获取任务
        task = db.query(AIGenerateTask).filter(AIGenerateTask.id == task_id).first()
        if not task:
            return

        # 检查任务状态
        if task.status == "cancelled":
            return

        # 更新任务状态
        task.status = "processing"
        task.progress = 10
        db.commit()

        # 获取 AI 配置
        config = db.query(AIProviderConfig).filter(AIProviderConfig.id == config_id).first()
        if not config:
            task.status = "failed"
            task.error_message = "AI 配置不存在"
            db.commit()
            return

        # 创建 AI 服务
        api_key = decrypt_api_key(config.api_key)
        provider = AIServiceFactory.create_provider(
            config.provider,
            api_key,
            config.api_base_url
        )

        # 更新进度
        task.progress = 30
        db.commit()

        # 准备输入内容
        input_content = task.input_content
        if task.input_type == "swagger" and input_content:
            # 如果是 Swagger 文档，格式化为更易读的文本
            try:
                swagger_data = json.loads(input_content)
                from services.document_parser import DocumentParser
                input_content = DocumentParser.format_swagger_for_prompt(swagger_data)
            except (json.JSONDecodeError, Exception):
                pass  # 使用原始内容

        # 构建 Prompt
        messages = PromptEngine.build_messages(
            generate_type=task.generate_type,
            input_content=input_content or "",
            count=task.target_count
        )

        # 更新进度
        task.progress = 50
        db.commit()

        # 调用 AI 生成
        response = run_async(provider.chat(messages, task.model_name))

        # 更新进度
        task.progress = 80
        db.commit()

        # 解析结果
        try:
            generated_cases = extract_json_from_response(response)
        except ValueError as e:
            task.status = "failed"
            task.error_message = f"解析 AI 返回结果失败: {str(e)}"
            db.commit()
            return

        # 验证结果是列表
        if not isinstance(generated_cases, list):
            task.status = "failed"
            task.error_message = "AI 返回的结果不是数组格式"
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
        task = db.query(AIGenerateTask).filter(AIGenerateTask.id == task_id).first()
        if task:
            task.status = "failed"
            task.error_message = str(e)[:500]  # 限制错误消息长度
            db.commit()

        # 重试
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=5)

    finally:
        db.close()
```

- [ ] **Step 2: 提交**

```bash
git add server/tasks/ai_generate_tasks.py
git commit -m "feat: 实现 Celery 生成任务"
```

---

## Task 11: 前端 API 和类型

**Files:**
- Create: `frontend/src/api/aiGenerate.ts`

- [ ] **Step 1: 创建 API 文件**

创建 `frontend/src/api/aiGenerate.ts`：

```typescript
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

- [ ] **Step 2: 提交**

```bash
git add frontend/src/api/aiGenerate.ts
git commit -m "feat: 添加 AI 生成前端 API 和类型定义"
```

---

## Task 12: 前端路由和页面入口

**Files:**
- Create: `frontend/src/views/ai-generate/index.vue`
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: 创建页面入口**

创建 `frontend/src/views/ai-generate/index.vue`：

```vue
<template>
  <AIGeneratePage />
</template>

<script setup lang="ts">
import AIGeneratePage from './AIGeneratePage.vue'
</script>
```

- [ ] **Step 2: 添加路由**

在 `frontend/src/router/index.ts` 中添加路由：

```typescript
{
  path: '/ai-generate',
  name: 'AIGenerate',
  component: () => import('@/views/ai-generate/index.vue'),
  meta: {
    title: 'AI 生成测试用例',
    requiresAuth: true
  }
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/ai-generate/index.vue frontend/src/router/index.ts
git commit -m "feat: 添加 AI 生成页面路由"
```

---

## Task 13: AI 配置组件

**Files:**
- Create: `frontend/src/views/ai-generate/components/AIConfig.vue`

- [ ] **Step 1: 创建 AI 配置组件**

创建 `frontend/src/views/ai-generate/components/AIConfig.vue`（内容见设计文档 5.8 节）

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/ai-generate/components/AIConfig.vue
git commit -m "feat: 实现 AI 配置管理组件（支持中转站）"
```

---

## Task 14: 文件上传和文本输入组件

**Files:**
- Create: `frontend/src/views/ai-generate/components/FileUpload.vue`
- Create: `frontend/src/views/ai-generate/components/TextInput.vue`

- [ ] **Step 1: 创建文件上传组件**

创建 `frontend/src/views/ai-generate/components/FileUpload.vue`：

```vue
<template>
  <div class="file-upload">
    <a-upload
      :accept="accept"
      :show-file-list="false"
      :before-upload="handleBeforeUpload"
      :custom-request="handleUpload"
    >
      <template #upload-button>
        <div class="upload-area">
          <div v-if="!uploadedFile" class="upload-placeholder">
            <icon-upload :size="40" />
            <p>点击或拖拽文件到此处上传</p>
            <p class="upload-hint">支持格式：{{ accept }}</p>
          </div>
          <div v-else class="upload-success">
            <icon-file :size="40" />
            <p>{{ uploadedFile.name }}</p>
            <a-button size="small" @click.stop="handleRemove">重新选择</a-button>
          </div>
        </div>
      </template>
    </a-upload>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'

const props = defineProps<{
  accept: string
}>()

const emit = defineEmits<{
  upload: [file: File]
}>()

const uploadedFile = ref<File | null>(null)

const handleBeforeUpload = (file: File) => {
  // 验证文件大小（最大 10MB）
  if (file.size > 10 * 1024 * 1024) {
    Message.error('文件大小不能超过 10MB')
    return false
  }
  return true
}

const handleUpload = (option: any) => {
  uploadedFile.value = option.fileItem.file
  emit('upload', option.fileItem.file)
}

const handleRemove = () => {
  uploadedFile.value = null
}
</script>

<style scoped>
.file-upload {
  width: 100%;
}

.upload-area {
  width: 100%;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed #e5e6eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-area:hover {
  border-color: #165dff;
  background: #f2f3ff;
}

.upload-placeholder,
.upload-success {
  text-align: center;
  color: #86909c;
}

.upload-placeholder p,
.upload-success p {
  margin: 8px 0;
}

.upload-hint {
  font-size: 12px;
  color: #c9cdd4;
}
</style>
```

- [ ] **Step 2: 创建文本输入组件**

创建 `frontend/src/views/ai-generate/components/TextInput.vue`：

```vue
<template>
  <div class="text-input">
    <a-textarea
      :model-value="modelValue"
      @update:model-value="$emit('update:modelValue', $event)"
      placeholder="请输入功能描述、需求说明或测试点..."
      :max-length="10000"
      show-word-limit
      :auto-size="{ minRows: 10, maxRows: 20 }"
    />
    <div class="input-hint">
      <p>提示：详细描述功能需求，AI 将根据描述生成测试用例</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: string
}>()

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<style scoped>
.text-input {
  width: 100%;
}

.input-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #86909c;
}
</style>
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/ai-generate/components/FileUpload.vue frontend/src/views/ai-generate/components/TextInput.vue
git commit -m "feat: 实现文件上传和文本输入组件"
```

---

## Task 15: 任务列表组件

**Files:**
- Create: `frontend/src/views/ai-generate/components/TaskList.vue`

- [ ] **Step 1: 创建任务列表组件**

创建 `frontend/src/views/ai-generate/components/TaskList.vue`（内容见设计文档 5.4 节）

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/ai-generate/components/TaskList.vue
git commit -m "feat: 实现任务列表组件"
```

---

## Task 16: 任务详情和用例编辑组件

**Files:**
- Create: `frontend/src/views/ai-generate/components/TaskDetail.vue`
- Create: `frontend/src/views/ai-generate/components/CaseEditor.vue`

- [ ] **Step 1: 创建任务详情组件**

创建 `frontend/src/views/ai-generate/components/TaskDetail.vue`（内容见设计文档 5.5 节）

- [ ] **Step 2: 创建用例编辑组件**

创建 `frontend/src/views/ai-generate/components/CaseEditor.vue`（内容见设计文档 5.6 节）

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/ai-generate/components/TaskDetail.vue frontend/src/views/ai-generate/components/CaseEditor.vue
git commit -m "feat: 实现任务详情和用例编辑组件"
```

---

## Task 17: 主页面组件

**Files:**
- Create: `frontend/src/views/ai-generate/AIGeneratePage.vue`

- [ ] **Step 1: 创建主页面组件**

创建 `frontend/src/views/ai-generate/AIGeneratePage.vue`（内容见设计文档 5.3 节）

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/ai-generate/AIGeneratePage.vue
git commit -m "feat: 实现 AI 生成主页面组件"
```

---

## Task 18: 更新进度文档

**Files:**
- Modify: `docs/progress.md`

- [ ] **Step 1: 更新进度**

在 `docs/progress.md` 中添加：

```markdown
## AI 生成测试用例

- [x] AI 配置管理（支持多模型和中转站）
- [x] 文档上传和解析（PRD/Swagger）
- [x] 测试用例生成（功能/接口/边界值/组合）
- [x] 生成任务管理（异步执行、进度跟踪）
- [x] 用例编辑和保存
```

- [ ] **Step 2: 提交**

```bash
git add docs/progress.md
git commit -m "docs: 更新 AI 生成功能进度"
```

---

## 自检清单

完成所有任务后，运行以下验证：

- [ ] 后端启动无错误：`cd server && python -m uvicorn main:app --reload`
- [ ] 前端启动无错误：`cd frontend && npm run dev`
- [ ] 可以创建 AI 配置
- [ ] 可以测试 AI 配置
- [ ] 可以上传文档
- [ ] 可以创建生成任务
- [ ] 任务状态正确更新
- [ ] 可以查看生成结果
- [ ] 可以编辑生成的用例
- [ ] 可以保存用例到项目
