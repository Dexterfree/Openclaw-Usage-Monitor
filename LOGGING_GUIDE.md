# OpenCLAW Token 使用日志记录指南

本指南介绍如何使用 OpenCLAW Token 使用日志记录工具来跟踪你的 LLM API 调用。

## 目录

1. [快速开始](#快速开始)
2. [基础用法](#基础用法)
3. [集成示例](#集成示例)
4. [查看统计数据](#查看统计数据)
5. [常见问题](#常见问题)

---

## 快速开始

### 1. 最简单的使用方式

```python
from openclaw_logger import log_usage

# 记录一次 API 调用
log_usage(
    model="claude-3-5-sonnet",
    input_tokens=1500,
    output_tokens=800,
)
```

### 2. 查看统计数据

```bash
# 实时监控
openclaw-monitor --view realtime --log-path ./logs

# 日报
openclaw-monitor --view daily --log-path ./logs

# 月报
openclaw-monitor --view monthly --log-path ./logs
```

---

## 基础用法

### 使用便捷函数

```python
from openclaw_logger import log_usage

# 基础记录
log_usage(
    model="gpt-4o",
    input_tokens=2000,
    output_tokens=1000,
)

# 带缓存的记录
log_usage(
    model="claude-3-5-sonnet",
    input_tokens=1500,
    output_tokens=800,
    cache_read_tokens=100,
    cache_creation_tokens=200,
)
```

### 使用日志记录器实例

```python
from openclaw_logger import TokenUsageLogger

logger = TokenUsageLogger(log_dir="./logs")

# 记录使用
logger.log(
    model="claude-3-opus",
    input_tokens=2000,
    output_tokens=1500,
    provider="anthropic",
    request_id="my-custom-request-id",
)
```

---

## 集成示例

### OpenAI API

```python
from openai import OpenAI
from openclaw_logger import get_logger

logger = get_logger()

client = OpenAI(api_key="your-api-key")

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)

# 自动记录
logger.log_openai_response(response, "gpt-4o")
```

### 使用装饰器（推荐）

```python
from openclaw_logger import log_llm_call

@log_llm_call(model="gpt-4o")
def call_openai(prompt):
    client = OpenAI()
    return client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

# 调用函数，自动记录
result = call_openai("写一段代码")
```

### Claude API

```python
from anthropic import Anthropic
from openclaw_logger import get_logger

logger = get_logger()

client = Anthropic(api_key="your-api-key")

response = client.messages.create(
    model="claude-3-5-sonnet",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)

# 转换为字典并记录
response_dict = response.model_dump()
logger.log_claude_response(response_dict, "claude-3-5-sonnet")
```

### 使用 LLM Wrapper（更简单）

```python
from llm_wrapper import create_openai_client

# 创建带日志的客户端
client = create_openai_client(api_key="your-api-key", log_dir="./logs")

# 正常调用，自动记录
response = client.chat(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Flask/FastAPI 集成

```python
from flask import Flask
from openclaw_logger import get_logger

app = Flask(__name__)
logger = get_logger()

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    prompt = data["prompt"]

    # 调用 LLM
    response = call_llm(prompt)

    # 记录使用
    logger.log(
        model="claude-3-5-sonnet",
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )

    return jsonify(response)
```

---

## 查看统计数据

### 实时监控

```bash
openclaw-monitor --view realtime --log-path ./logs
```

实时监控显示：
- 当前 token 使用情况
- 消耗速度
- 预计剩余时间
- 活动会话信息

### 日报

```bash
openclaw-monitor --view daily --log-path ./logs
```

日报显示：
- 每日总 token 使用
- 输入/输出 token 分布
- 缓存命中率
- 各模型使用情况

### 月报

```bash
openclaw-monitor --view monthly --log-path ./logs
```

月报显示：
- 每月 token 使用趋势
- 模型分布统计
- 成本分析

### 自定义计划

```bash
# 使用自定义 token 限制
openclaw-monitor --plan custom --custom-limit-tokens 500000 --view realtime

# 设置不同计划
openclaw-monitor --plan small   # 100,000 tokens
openclaw-monitor --plan medium  # 1,000,000 tokens
openclaw-monitor --plan large   # 10,000,000 tokens
```

---

## 日志格式

### OpenCLAW 格式（推荐）

```json
{
  "timestamp": "2026-03-12T10:00:00Z",
  "model": "claude-3-5-sonnet",
  "provider": "anthropic",
  "input_tokens": 1500,
  "output_tokens": 800,
  "cache_read_tokens": 100,
  "cache_creation_tokens": 0,
  "request_id": "req_abc123"
}
```

### 支持的其他格式

工具自动支持多种格式：
- OpenAI API 格式
- Claude API 格式
- 通用 JSON 格式

---

## 常见问题

### Q: 为什么监控器显示 0？

**A:** 检查以下几点：

1. 确认日志文件存在
   ```bash
   ls -la ./logs/
   ```

2. 确认日志格式正确
   ```bash
   cat ./logs/usage_*.jsonl | head -1
   ```

3. 确认时间戳在最近 30 天内（日报）或 12 个月内（月报）

4. 使用 debug 模式查看详细信息
   ```bash
   openclaw-monitor --view daily --log-path ./logs --debug
   ```

### Q: 如何自动记录 API 调用？

**A:** 使用装饰器或包装器：

```python
# 方式 1: 装饰器
@log_llm_call(model="gpt-4o")
def my_llm_function(prompt):
    # API 调用
    return response

# 方式 2: 包装器
from llm_wrapper import create_openai_client
client = create_openai_client(api_key="...")
```

### Q: 日志文件在哪里？

**A:** 默认位置：

- 当前目录: `./logs/`
- 用户目录: `~/.openclaw/logs/`

可以通过 `log_dir` 参数自定义：

```python
logger = TokenUsageLogger(log_dir="/path/to/logs")
```

### Q: 如何按日期分割日志？

**A:** 日志记录器自动按日期分割日志文件：

```
logs/
├── usage_2026-03-10.jsonl
├── usage_2026-03-11.jsonl
├── usage_2026-03-12.jsonl
└── ...
```

### Q: 支持哪些 LLM 提供商？

**A:** 支持所有主流提供商：

- OpenAI (GPT-3.5, GPT-4, GPT-4o 等)
- Anthropic (Claude 3 系列)
- Google (Gemini)
- 本地模型 (Llama, Mistral, Qwen 等)
- 任何其他提供 token 使用信息的 API

---

## 高级用法

### 添加自定义元数据

```python
logger.log(
    model="claude-3-5-sonnet",
    input_tokens=1500,
    output_tokens=800,
    metadata={
        "user_id": "user-123",
        "project": "my-app",
        "function": "code_review",
    }
)
```

### 上下文管理器

```python
from openclaw_logger import track_llm_usage

with track_llm_usage(model="gpt-4o", request_id="custom-123") as ctx:
    response = call_llm()

    # 手动设置（如果自动检测失败）
    ctx["input_tokens"] = response.input_tokens
    ctx["output_tokens"] = response.output_tokens
```

---

## 项目文件

- `openclaw_logger.py` - 核心日志记录器
- `llm_wrapper.py` - LLM API 包装器
- `usage_examples.py` - 使用示例
- `LOGGING_GUIDE.md` - 本指南

---

## 需要帮助？

运行以下命令获取帮助：

```bash
openclaw-monitor --help
```

或查看项目文档和示例代码。
