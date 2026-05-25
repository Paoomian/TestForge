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

    @abstractmethod
    async def list_models(self) -> List[Dict[str, str]]:
        """获取可用模型列表，返回 [{"id": "model-id", "name": "Model Name"}, ...]"""
        pass


class ClaudeProvider(AIProvider):
    """Claude API 提供商"""

    def __init__(self, api_key: str, api_base_url: Optional[str] = None):
        super().__init__(api_key, api_base_url)
        # anthropic 库期望的 base_url 不带 /v1，它会自己加
        self.base_url = (api_base_url or "https://api.anthropic.com").rstrip('/')
        # 用于 OpenAI 兼容查询模型的 URL（需要 /v1）
        if api_base_url:
            url = api_base_url.rstrip('/')
            self._openai_base_url = url if url.endswith('/v1') else url + '/v1'
        else:
            self._openai_base_url = None

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
            max_tokens=16384,
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

    async def list_models(self) -> List[Dict[str, str]]:
        # 如果配置了中转站，使用 OpenAI 兼容方式查询（失败时抛出错误）
        if self._openai_base_url:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self._openai_base_url
            )
            models = await client.models.list()
            return [{"id": m.id, "name": m.id} for m in models.data]

        # 官方 Claude API 没有 /v1/models 端点，返回已知模型
        return [
            {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4"},
            {"id": "claude-haiku-4-20250514", "name": "Claude Haiku 4"},
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet"},
            {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
            {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"},
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
        ]


class OpenAIProvider(AIProvider):
    """OpenAI API 提供商"""

    def __init__(self, api_key: str, api_base_url: Optional[str] = None):
        super().__init__(api_key, api_base_url)
        self.base_url = self._normalize_base_url(api_base_url or "https://api.openai.com/v1")

    @staticmethod
    def _normalize_base_url(url: str) -> str:
        """规范化 base_url，确保以 /v1 结尾（如果还不是的话）"""
        url = url.rstrip('/')
        if not url.endswith('/v1'):
            url = url + '/v1'
        return url

    async def chat(self, messages: List[Dict[str, str]], model: str) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=16384
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

    async def list_models(self) -> List[Dict[str, str]]:
        """通过 /v1/models 端点获取模型列表"""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        models = await client.models.list()
        result = []
        for model in models.data:
            result.append({"id": model.id, "name": model.id})
        # 按名称排序
        result.sort(key=lambda x: x["id"])
        return result


class DeepSeekProvider(OpenAIProvider):
    """DeepSeek API 提供商（兼容 OpenAI 接口）"""

    def __init__(self, api_key: str, api_base_url: Optional[str] = None):
        super().__init__(api_key, api_base_url or "https://api.deepseek.com/v1")

    async def list_models(self) -> List[Dict[str, str]]:
        # 使用自定义端点时，失败应抛出错误
        if self.api_base_url:
            return await super().list_models()
        # 官方 DeepSeek API，静默返回已知模型
        try:
            return await super().list_models()
        except Exception:
            return [
                {"id": "deepseek-chat", "name": "DeepSeek Chat"},
                {"id": "deepseek-coder", "name": "DeepSeek Coder"},
            ]


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
