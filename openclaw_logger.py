"""
OpenCLAW 使用日志记录器

用于记录 LLM API 调用的 token 使用情况，支持 OpenAI、Claude 等多种提供商。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union
from contextlib import contextmanager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TokenUsageLogger:
    """
    Token 使用日志记录器。

    自动记录 LLM API 调用的 token 使用情况到 JSONL 文件。
    """

    def __init__(
        self,
        log_dir: Union[str, Path] = "./logs",
        provider: str = "auto",
        auto_detect_provider: bool = True,
    ):
        """
        初始化日志记录器。

        Args:
            log_dir: 日志文件目录
            provider: 默认提供商 (auto, openai, anthropic, local等)
            auto_detect_provider: 是否自动检测提供商
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.provider = provider
        self.auto_detect_provider = auto_detect_provider

    def _detect_provider(self, model: str) -> str:
        """
        根据模型名称检测提供商。

        Args:
            model: 模型名称

        Returns:
            提供商名称
        """
        if self.provider != "auto":
            return self.provider

        model_lower = model.lower()

        # Claude / Anthropic
        if any(name in model_lower for name in ["claude", "anthropic"]):
            return "anthropic"

        # OpenAI
        if any(name in model_lower for name in ["gpt", "openai", "chatgpt"]):
            return "openai"

        # Google / Gemini
        if any(name in model_lower for name in ["gemini", "palm", "google"]):
            return "google"

        # 本地模型
        if any(name in model_lower for name in ["llama", "mistral", "qwen", "yi", "deepseek"]):
            return "local"

        return "unknown"

    def _get_log_file_path(self) -> Path:
        """
        获取当前日志文件路径（按日期分割）。

        Returns:
            日志文件路径
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.log_dir / f"usage_{today}.jsonl"

    def log(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        provider: Optional[str] = None,
        cache_read_tokens: int = 0,
        cache_creation_tokens: int = 0,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录一次 API 调用的 token 使用情况。

        Args:
            model: 模型名称
            input_tokens: 输入 token 数量
            output_tokens: 输出 token 数量
            provider: 提供商 (自动检测如果为 None)
            cache_read_tokens: 缓存读取 token 数量
            cache_creation_tokens: 缓存创建 token 数量
            request_id: 请求 ID
            metadata: 额外的元数据
        """
        if provider is None and self.auto_detect_provider:
            provider = self._detect_provider(model)
        elif provider is None:
            provider = self.provider

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "provider": provider,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_tokens": cache_read_tokens,
            "cache_creation_tokens": cache_creation_tokens,
            "request_id": request_id or self._generate_request_id(),
        }

        if metadata:
            log_entry["metadata"] = metadata

        # 写入日志文件
        log_file = self._get_log_file_path()
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            logger.debug(f"Logged usage: {input_tokens + output_tokens} tokens for {model}")
        except Exception as e:
            logger.error(f"Failed to write log: {e}")

    def _generate_request_id(self) -> str:
        """生成唯一的请求 ID。"""
        return f"req_{datetime.now(timezone.utc).timestamp()}"

    def log_openai_response(self, response: Any, model: str, **kwargs) -> None:
        """
        记录 OpenAI API 响应。

        Args:
            response: OpenAI API 响应对象
            model: 模型名称
            **kwargs: 额外参数
        """
        try:
            usage = response.usage
            self.log(
                model=model,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
                provider="openai",
                **kwargs,
            )
        except Exception as e:
            logger.error(f"Failed to log OpenAI response: {e}")

    def log_claude_response(self, response: Dict[str, Any], model: str, **kwargs) -> None:
        """
        记录 Claude API 响应。

        Args:
            response: Claude API 响应字典
            model: 模型名称
            **kwargs: 额外参数
        """
        try:
            usage = response.get("usage", {})
            self.log(
                model=model,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                cache_read_tokens=usage.get("cache_read_tokens", 0),
                cache_creation_tokens=usage.get("cache_creation_tokens", 0),
                provider="anthropic",
                **kwargs,
            )
        except Exception as e:
            logger.error(f"Failed to log Claude response: {e}")

    def log_generic(
        self,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        **kwargs
    ) -> None:
        """
        记录通用格式的 token 使用。

        Args:
            model: 模型名称
            prompt_tokens: 提示 token 数量
            completion_tokens: 完成token数量
            total_tokens: 总 token 数量（如果单独数据不可用）
            **kwargs: 额外参数
        """
        input_tokens = prompt_tokens
        output_tokens = completion_tokens

        # 如果只有总 token 数，尝试估算
        if total_tokens > 0 and input_tokens == 0 and output_tokens == 0:
            input_tokens = int(total_tokens * 0.7)
            output_tokens = total_tokens - input_tokens

        self.log(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            **kwargs,
        )


# 全局默认实例
_default_logger: Optional[TokenUsageLogger] = None


def get_logger(
    log_dir: Union[str, Path] = "./logs",
    provider: str = "auto",
) -> TokenUsageLogger:
    """
    获取全局日志记录器实例。

    Args:
        log_dir: 日志目录
        provider: 默认提供商

    Returns:
        TokenUsageLogger 实例
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = TokenUsageLogger(log_dir=log_dir, provider=provider)
    return _default_logger


def log_llm_call(
    model: str = None,
    provider: str = None,
    logger_instance: TokenUsageLogger = None,
):
    """
    装饰器：自动记录 LLM 函数调用的 token 使用。

    使用方法:
        @log_llm_call(model="gpt-4o")
        def call_llm(prompt):
            # 你的 LLM 调用代码
            return response

    Args:
        model: 模型名称
        provider: 提供商
        logger_instance: 自定义日志记录器实例
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # 尝试从结果中提取 token 使用信息
            logger_obj = logger_instance or get_logger()

            # 尝试不同的响应格式
            if hasattr(result, 'usage'):
                # OpenAI 格式
                if hasattr(result.usage, 'prompt_tokens'):
                    logger_obj.log_openai_response(result, model or "unknown")
            elif isinstance(result, dict):
                # 字典格式 (如 Claude)
                if 'usage' in result:
                    logger_obj.log_claude_response(result, model or "unknown")

            return result
        return wrapper
    return decorator


@contextmanager
def track_llm_usage(
    model: str,
    logger_instance: TokenUsageLogger = None,
    **metadata
):
    """
    上下文管理器：用于跟踪 LLM 使用。

    使用方法:
        with track_llm_usage(model="gpt-4o", request_id="my-request"):
            response = openai.chat.completions.create(...)
            # 自动记录

    Args:
        model: 模型名称
        logger_instance: 自定义日志记录器实例
        **metadata: 额外的元数据
    """
    logger_obj = logger_instance or get_logger()

    # 存储原始数据
    context = {"model": model, "metadata": metadata}

    yield context

    # 在上下文退出时记录（如果设置了 token 信息）
    if "input_tokens" in context and "output_tokens" in context:
        logger_obj.log(
            model=model,
            input_tokens=context["input_tokens"],
            output_tokens=context["output_tokens"],
            metadata=metadata,
        )


# 便捷函数
def log_usage(
    model: str,
    input_tokens: int,
    output_tokens: int,
    log_dir: str = "./logs",
    **kwargs
) -> None:
    """
    快速记录 token 使用的便捷函数。

    Args:
        model: 模型名称
        input_tokens: 输入 token 数量
        output_tokens: 输出 token 数量
        log_dir: 日志目录
        **kwargs: 额外参数
    """
    logger_obj = get_logger(log_dir=log_dir)
    logger_obj.log(model, input_tokens, output_tokens, **kwargs)
