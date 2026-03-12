"""
LLM API 包装器 - 自动记录 Token 使用

提供对 OpenAI、Claude 等 LLM API 的包装，自动记录 token 使用情况。
"""

from functools import wraps
from typing import Any, Callable, Dict, Optional, Union
from openclaw_logger import TokenUsageLogger, get_logger


class OpenAIWrapper:
    """
    OpenAI API 包装器，自动记录 token 使用。
    """

    def __init__(
        self,
        api_key: str,
        log_dir: str = "./logs",
        logger: Optional[TokenUsageLogger] = None,
    ):
        """
        初始化 OpenAI 包装器。

        Args:
            api_key: OpenAI API 密钥
            log_dir: 日志目录
            logger: 自定义日志记录器
        """
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.logger = logger or get_logger(log_dir=log_dir)

    def chat(
        self,
        model: str,
        messages: list,
        **kwargs
    ) -> Any:
        """
        调用 OpenAI Chat API 并记录使用。

        Args:
            model: 模型名称
            messages: 消息列表
            **kwargs: 其他 API 参数

        Returns:
            API 响应
        """
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )

        # 记录使用
        self.logger.log_openai_response(response, model)

        return response

    def completion(
        self,
        model: str,
        prompt: str,
        **kwargs
    ) -> Any:
        """
        调用 OpenAI Completion API 并记录使用。

        Args:
            model: 模型名称
            prompt: 提示文本
            **kwargs: 其他 API 参数

        Returns:
            API 响应
        """
        response = self.client.completions.create(
            model=model,
            prompt=prompt,
            **kwargs
        )

        # 记录使用
        self.logger.log_openai_response(response, model)

        return response


class AnthropicWrapper:
    """
    Anthropic Claude API 包装器，自动记录 token 使用。
    """

    def __init__(
        self,
        api_key: str,
        log_dir: str = "./logs",
        logger: Optional[TokenUsageLogger] = None,
    ):
        """
        初始化 Anthropic 包装器。

        Args:
            api_key: Anthropic API 密钥
            log_dir: 日志目录
            logger: 自定义日志记录器
        """
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("请安装 anthropic 包: pip install anthropic")

        self.client = Anthropic(api_key=api_key)
        self.logger = logger or get_logger(log_dir=log_dir)

    def messages(
        self,
        model: str,
        messages: list,
        max_tokens: int = 1024,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用 Claude Messages API 并记录使用。

        Args:
            model: 模型名称
            messages: 消息列表
            max_tokens: 最大生成 token 数
            **kwargs: 其他 API 参数

        Returns:
            API 响应字典
        """
        response = self.client.messages.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            **kwargs
        )

        # 转换为字典并记录
        response_dict = response.model_dump()
        self.logger.log_claude_response(response_dict, model)

        return response_dict

    def stream(
        self,
        model: str,
        messages: list,
        max_tokens: int = 1024,
        **kwargs
    ):
        """
        调用 Claude Stream API（注意：流式响应无法准确记录输出 token）。

        Args:
            model: 模型名称
            messages: 消息列表
            max_tokens: 最大生成 token 数
            **kwargs: 其他 API 参数

        Returns:
            流式响应迭代器
        """
        response = self.client.messages.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )

        # 记录输入 token（输出 token 需要估算或手动记录）
        # 流式响应无法直接获取输出 token 数
        return response


class LLMLogger:
    """
    通用 LLM 日志记录器，可以包装任何 LLM 调用。
    """

    def __init__(
        self,
        log_dir: str = "./logs",
        auto_log: bool = True,
    ):
        """
        初始化 LLM 日志记录器。

        Args:
            log_dir: 日志目录
            auto_log: 是否自动记录
        """
        self.logger = get_logger(log_dir=log_dir)
        self.auto_log = auto_log

    def log_call(
        self,
        model: str,
        prompt: str = None,
        input_tokens: int = None,
        output_tokens: int = None,
        response_text: str = None,
        **kwargs
    ) -> None:
        """
        手动记录一次 LLM 调用。

        Args:
            model: 模型名称
            prompt: 提示文本（用于估算 token）
            input_tokens: 输入 token 数量
            output_tokens: 输出 token 数量
            response_text: 响应文本（用于估算 token）
            **kwargs: 额外参数
        """
        # 如果没有提供 token 数，尝试估算
        if input_tokens is None and prompt:
            input_tokens = self._estimate_tokens(prompt)

        if output_tokens is None and response_text:
            output_tokens = self._estimate_tokens(response_text)

        self.logger.log(
            model=model,
            input_tokens=input_tokens or 0,
            output_tokens=output_tokens or 0,
            **kwargs
        )

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """
        粗略估算文本的 token 数量。

        这个估算不精确，但可以在无法获取真实 token 数时使用。
        """
        # 英文大约 4 字符 = 1 token，中文大约 2 字符 = 1 token
        import re

        # 统计中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # 统计非中文字符
        other_chars = len(text) - chinese_chars

        return int(chinese_chars / 2 + other_chars / 4)


def track_llm(
    model: str = None,
    log_dir: str = "./logs",
    estimate: bool = False,
):
    """
    装饰器：自动跟踪 LLM 函数调用。

    使用方法:
        @track_llm(model="gpt-4o")
        def my_llm_function(prompt):
            # 你的代码
            return response

    Args:
        model: 模型名称
        log_dir: 日志目录
        estimate: 是否在无法获取 token 时进行估算
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger_obj = get_logger(log_dir=log_dir)

            result = func(*args, **kwargs)

            # 尝试从结果中提取并记录
            _try_log_result(result, model, logger_obj, estimate)

            return result
        return wrapper
    return decorator


def _try_log_result(
    result: Any,
    model: str,
    logger: TokenUsageLogger,
    estimate: bool = False
) -> None:
    """
    尝试从结果中提取并记录 token 使用。
    """
    # OpenAI 格式
    if hasattr(result, 'usage') and hasattr(result.usage, 'prompt_tokens'):
        logger.log_openai_response(result, model or "unknown")
        return

    # 字典格式
    if isinstance(result, dict):
        # Claude 格式
        if 'usage' in result:
            logger.log_claude_response(result, model or "unknown")
            return

        # 其他字典格式
        if 'prompt_tokens' in result or 'input_tokens' in result:
            logger.log_generic(model or "unknown", **result)
            return

    # 如果启用估算且有文本响应
    if estimate and isinstance(result, str):
        logger.log(
            model=model or "unknown",
            input_tokens=0,  # 无法估算输入
            output_tokens=logger._estimate_tokens(result) if hasattr(logger, '_estimate_tokens') else len(result) // 4,
        )


# ==================== 便捷函数 ====================

def create_openai_client(api_key: str, log_dir: str = "./logs") -> OpenAIWrapper:
    """创建带日志记录的 OpenAI 客户端。"""
    return OpenAIWrapper(api_key=api_key, log_dir=log_dir)


def create_anthropic_client(api_key: str, log_dir: str = "./logs") -> AnthropicWrapper:
    """创建带日志记录的 Anthropic 客户端。"""
    return AnthropicWrapper(api_key=api_key, log_dir=log_dir)


# ==================== 使用示例 ====================

if __name__ == "__main__":
    print("LLM API 包装器 - 使用示例")
    print()

    # 示例 1: 手动记录
    llm_logger = LLMLogger(log_dir="./logs")
    llm_logger.log_call(
        model="gpt-4o",
        prompt="解释什么是机器学习",
        response_text="机器学习是人工智能的一个分支...",
    )

    # 示例 2: 使用装饰器
    @track_llm(model="claude-3-5-sonnet")
    def my_llm_call(prompt):
        return {"usage": {"input_tokens": 1000, "output_tokens": 500}}

    my_llm_call("写一段代码")

    print("✓ 示例执行完成，查看 ./logs/ 目录中的日志文件")
