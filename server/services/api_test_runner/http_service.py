import time
import httpx
from typing import Any
from .variable_service import VariableService


# 响应体截断阈值
MAX_BODY_SIZE = 500 * 1024  # 500KB

# 模块级共享客户端，复用连接池避免每次请求重建TCP连接
_default_client = httpx.AsyncClient(timeout=30, follow_redirects=True)


def _get_default_client() -> httpx.AsyncClient:
    global _default_client
    if _default_client.is_closed:
        _default_client = httpx.AsyncClient(timeout=30, follow_redirects=True)
    return _default_client


class HttpService:
    """HTTP请求封装服务"""

    def __init__(self, shared_client: httpx.AsyncClient | None = None):
        self.variable_service = VariableService()
        self._shared_client = shared_client

    async def send_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        query_params: dict[str, str] | None = None,
        body: Any = None,
        body_type: str = "none",
        auth_config: dict[str, Any] | None = None,
        timeout: int = 30,
    ) -> dict:
        """
        发送HTTP请求，返回请求快照和响应信息
        """
        # 构建请求头
        final_headers = dict(headers or {})
        final_params = dict(query_params or {})

        # 处理认证
        if auth_config and auth_config.get("auth_type") != "none":
            self._apply_auth(auth_config, final_headers, final_params)

        # 构建请求体
        request_body, content_type = self._build_body(body, body_type)
        if content_type and "content-type" not in {k.lower() for k in final_headers}:
            final_headers["Content-Type"] = content_type

        # 请求快照（脱敏）
        request_snapshot = {
            "method": method.upper(),
            "url": url,
            "headers": self.variable_service.mask_sensitive(final_headers),
            "params": final_params,
            "body": body,
            "body_type": body_type,
        }

        # 发送请求
        start_time = time.monotonic()
        try:
            client = self._shared_client or _get_default_client()
            response = await client.request(
                method=method.upper(),
                url=url,
                headers=final_headers,
                params=final_params,
                content=request_body if isinstance(request_body, (bytes, str)) else None,
                json=request_body if isinstance(request_body, dict) and body_type == "raw-json" else None,
            )
        except httpx.TimeoutException:
            elapsed = int((time.monotonic() - start_time) * 1000)
            return {
                "request_snapshot": request_snapshot,
                "response_info": None,
                "error": f"请求超时（{timeout}秒）",
                "elapsed_ms": elapsed,
            }
        except httpx.RequestError as e:
            elapsed = int((time.monotonic() - start_time) * 1000)
            return {
                "request_snapshot": request_snapshot,
                "response_info": None,
                "error": f"请求失败: {str(e)}",
                "elapsed_ms": elapsed,
            }

        elapsed = int((time.monotonic() - start_time) * 1000)

        # 解析响应
        response_body = response.text
        truncated = False
        if len(response_body.encode("utf-8")) > MAX_BODY_SIZE:
            response_body = response_body[:MAX_BODY_SIZE] + "\n... [truncated]"
            truncated = True

        response_info = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response_body,
            "elapsed_ms": elapsed,
            "size_bytes": len(response.content),
            "truncated": truncated,
        }

        return {
            "request_snapshot": request_snapshot,
            "response_info": response_info,
            "error": None,
            "elapsed_ms": elapsed,
        }

    def _apply_auth(
        self,
        auth_config: dict,
        headers: dict[str, str],
        params: dict[str, str],
    ):
        """应用认证配置"""
        auth_type = auth_config.get("auth_type")

        if auth_type == "bearer":
            token = auth_config.get("token", "")
            if token:
                headers["Authorization"] = f"Bearer {token}"

        elif auth_type == "basic":
            username = auth_config.get("username", "")
            password = auth_config.get("password", "")
            import base64
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"

        elif auth_type == "api_key":
            key_name = auth_config.get("api_key_name", "")
            key_value = auth_config.get("api_key_value", "")
            location = auth_config.get("api_key_location", "header")
            if key_name and key_value:
                if location == "header":
                    headers[key_name] = key_value
                else:
                    params[key_name] = key_value

    def _build_body(self, body: Any, body_type: str) -> tuple[Any, str | None]:
        """构建请求体，返回 (body_content, content_type)"""
        if body_type == "none" or not body:
            return None, None

        if body_type == "raw-json":
            if isinstance(body, dict):
                return body, "application/json"
            return body, "application/json"

        if body_type == "raw-xml":
            return body, "application/xml"

        if body_type == "raw-text":
            return body, "text/plain"

        if body_type == "form-data":
            # body 是 dict
            if isinstance(body, dict):
                return body, None  # httpx 自动处理 multipart
            return body, None

        if body_type == "x-www-form-urlencoded":
            if isinstance(body, dict):
                return body, "application/x-www-form-urlencoded"
            return body, "application/x-www-form-urlencoded"

        return body, None
