"""
OpenCLAW 使用日志记录器 - 使用示例

演示如何在各种场景中使用 token 使用日志记录器。
"""

from openclaw_logger import (
    TokenUsageLogger,
    get_logger,
    log_llm_call,
    track_llm_usage,
    log_usage,
)


# ==================== 示例 1: 基础使用 ====================

def example_basic():
    """最简单的使用方式 - 直接记录 token 使用。"""
    print("示例 1: 基础使用")

    # 方式 1: 使用便捷函数
    log_usage(
        model="claude-3-5-sonnet",
        input_tokens=1500,
        output_tokens=800,
        cache_read_tokens=100,
    )

    # 方式 2: 使用日志记录器实例
    logger = TokenUsageLogger(log_dir="./logs")
    logger.log(
        model="gpt-4o",
        input_tokens=2000,
        output_tokens=1000,
    )

    print("[OK] 日志已写入 ./logs/ 目录\n")


# ==================== 示例 2: OpenAI API 集成 ====================

def example_openai():
    """OpenAI API 使用示例。"""
    print("示例 2: OpenAI API 集成")

    # 模拟 OpenAI API 调用
    class MockOpenAIResponse:
        class Usage:
            prompt_tokens = 1200
            completion_tokens = 800
        usage = Usage()

    class MockOpenAI:
        @staticmethod
        def chat(prompt):
            # 模拟 API 调用
            return MockOpenAIResponse()

    # 使用装饰器自动记录
    @log_llm_call(model="gpt-4o")
    def call_openai(prompt):
        return MockOpenAI.chat(prompt)

    # 调用函数，自动记录
    response = call_openai("Hello, world!")
    print("[OK] OpenAI API 调用已记录\n")


# ==================== 示例 3: Claude API 集成 ====================

def example_claude():
    """Claude API 使用示例。"""
    print("示例 3: Claude API 集成")

    # 模拟 Claude API 响应
    claude_response = {
        "id": "msg_123",
        "type": "message",
        "usage": {
            "input_tokens": 1500,
            "output_tokens": 900,
            "cache_creation_tokens": 200,
            "cache_read_tokens": 50,
        }
    }

    # 记录 Claude 响应
    logger = get_logger()
    logger.log_claude_response(claude_response, model="claude-3-5-sonnet")

    print("[OK] Claude API 调用已记录\n")


# ==================== 示例 4: 使用装饰器 ====================

def example_decorator():
    """使用装饰器自动记录函数调用。"""
    print("示例 4: 装饰器使用")

    logger = TokenUsageLogger(log_dir="./logs")

    @log_llm_call(model="gpt-4o-mini", logger_instance=logger)
    def generate_code(prompt: str):
        """生成代码的函数，自动记录 token 使用。"""
        # 这里是实际的 LLM 调用
        return {"code": "print('Hello, World!')"}

    # 调用函数
    result = generate_code("写一个 Hello World 程序")
    print(f"[OK] 生成结果: {result}\n")


# ==================== 示例 5: 使用上下文管理器 ====================

def example_context_manager():
    """使用上下文管理器跟踪复杂场景。"""
    print("示例 5: 上下文管理器")

    logger = TokenUsageLogger(log_dir="./logs")

    with track_llm_usage(model="claude-3-opus", logger_instance=logger, request_id="custom-123") as ctx:
        # 在这里进行 API 调用
        input_tokens = 2000
        output_tokens = 1500

        # 手动设置 token 数量（如果自动检测失败）
        ctx["input_tokens"] = input_tokens
        ctx["output_tokens"] = output_tokens

    print("[OK] 上下文管理器记录完成\n")


# ==================== 示例 6: 批量记录 ====================

def example_batch():
    """批量记录多次 API 调用。"""
    print("示例 6: 批量记录")

    logger = get_logger()

    # 模拟多次调用
    calls = [
        ("claude-3-5-sonnet", 1000, 500),
        ("claude-3-5-sonnet", 1500, 800),
        ("gpt-4o", 1200, 600),
        ("claude-3-haiku", 800, 400),
    ]

    for model, input_t, output_t in calls:
        logger.log(
            model=model,
            input_tokens=input_t,
            output_tokens=output_t,
        )

    print(f"[OK] 批量记录了 {len(calls)} 次调用\n")


# ==================== 示例 7: 自定义元数据 ====================

def example_metadata():
    """记录额外的元数据。"""
    print("示例 7: 自定义元数据")

    logger = get_logger()

    logger.log(
        model="claude-3-5-sonnet",
        input_tokens=2000,
        output_tokens=1000,
        request_id="req-20250312-001",
        metadata={
            "user_id": "user-123",
            "project": "my-app",
            "function": "code_review",
            "latency_ms": 1500,
            "status": "success",
        }
    )

    print("[OK] 带元数据的日志已记录\n")


# ==================== 示例 8: 实际应用集成 ====================

class LLMService:
    """模拟一个 LLM 服务类，集成日志记录。"""

    def __init__(self, log_dir="./logs"):
        self.logger = TokenUsageLogger(log_dir=log_dir)

    def call_claude(self, prompt: str, model="claude-3-5-sonnet"):
        """调用 Claude API。"""
        # 模拟 API 调用
        input_tokens = len(prompt.split()) * 2  # 粗略估算
        output_tokens = 500

        # 记录使用
        self.logger.log(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            request_id=f"claude-{hash(prompt)}",
        )

        return {"response": "Generated response..."}

    def call_openai(self, prompt: str, model="gpt-4o"):
        """调用 OpenAI API。"""
        input_tokens = len(prompt.split()) * 2
        output_tokens = 400

        self.logger.log(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            request_id=f"openai-{hash(prompt)}",
        )

        return {"response": "Generated response..."}


def example_service():
    """服务类集成示例。"""
    print("示例 8: 服务类集成")

    service = LLMService(log_dir="./logs")

    # 多次调用
    service.call_claude("写一个排序算法")
    service.call_openai("解释什么是递归")
    service.call_claude("帮我重构这段代码", model="claude-3-opus")

    print("[OK] 服务调用已记录\n")


# ==================== 示例 9: 多提供商支持 ====================

def example_multiple_providers():
    """同时使用多个 LLM 提供商。"""
    print("示例 9: 多提供商支持")

    logger = get_logger()

    # 不同提供商的调用
    providers_data = [
        ("claude-3-5-sonnet", "anthropic", 1500, 800),
        ("gpt-4o", "openai", 1200, 600),
        ("gemini-1.5-pro", "google", 1000, 500),
        ("llama-3-70b", "local", 800, 400),
    ]

    for model, provider, inp, out in providers_data:
        logger.log(
            model=model,
            provider=provider,
            input_tokens=inp,
            output_tokens=out,
        )

    print("[OK] 多提供商调用已记录\n")


# ==================== 主程序 ====================

def main():
    """运行所有示例。"""
    print("=" * 60)
    print("OpenCLAW Token 使用日志记录器 - 示例")
    print("=" * 60)
    print()

    examples = [
        example_basic,
        example_openai,
        example_claude,
        example_decorator,
        example_context_manager,
        example_batch,
        example_metadata,
        example_service,
        example_multiple_providers,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"[ERROR] 示例执行出错: {e}\n")

    print("=" * 60)
    print("所有示例执行完成！")
    print(f"日志文件保存在: ./logs/ 目录")
    print()
    print("现在可以运行以下命令查看统计:")
    print("  openclaw-monitor --view daily --log-path ./logs")
    print("  openclaw-monitor --view realtime --log-path ./logs")
    print("=" * 60)


if __name__ == "__main__":
    main()
