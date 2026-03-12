# Clawdbot 集成指南

本文档说明如何将 Clawdbot 的 token 使用数据导入到 OpenCLAW Token Usage Monitor 中。

## Clawdbot 日志分析

### 日志文件位置

Clawdbot 默认日志位置：
- **Windows**: `C:\tmp\clawdbot\`
- **Linux/Mac**: `/tmp/clawdbot/`

日志文件命名格式：`clawdbot-YYYY-MM-DD.log`

### 日志格式

Clawdbot 使用 **JSONL** 格式，每行一个 JSON 对象：

```json
{"0":"{\"subsystem\":\"gateway\"}","1":"feishu_doc: Registered feishu_doc tool","_meta":{...}}
```

### 重要发现

**Clawdbot 的默认日志文件不包含 token 使用数据！**

Token 使用数据通过以下方式记录：

1. **诊断事件** - 需要启用 `diagnostics.enabled`
2. **OpenTelemetry 导出** - 需要 `diagnostics-otel` 插件
3. **命令方式** - 在聊天中使用 `/status` 或 `/usage`

## 方法 1: 启用诊断日志（推荐）

### 步骤 1: 启用诊断功能

编辑 `~/.openclaw/openclaw.json`：

```json
{
  "diagnostics": {
    "enabled": true
  }
}
```

### 步骤 2: 重启 Clawdbot

```bash
# 停止当前运行的 Clawdbot
# 然后重新启动
```

### 步骤 3: 查看诊断日志

启用诊断后，token 使用数据会被记录到诊断日志中。

## 方法 2: 创建 Clawdbot Token 记录适配器

在 Clawdbot 的代码中添加一个适配器，将 token 使用记录到 OpenCLAW 格式：

### 1. 创建适配器脚本

在 Clawdbot 项目中创建 `openclaw-adapter.js`：

```javascript
/**
 * OpenCLAW Token Usage Adapter for Clawdbot
 *
 * This adapter listens for model.usage diagnostic events and writes
 * them to OpenCLAW-compatible log files.
 */

import fs from "node:fs/promises";
import path from "path";
import { fileURLToPath } from "node:url";
import { resolveStateDir } from "./config/paths.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const LOG_DIR = path.join(resolveStateDir(), "logs", "openclaw");

// Ensure log directory exists
await fs.mkdir(LOG_DIR, { recursive: true });

/**
 * Convert a model.usage diagnostic event to OpenCLAW format
 */
function toOpenclawFormat(event) {
  const { usage, context, costUsd, durationMs, timestamp, model, provider, sessionId } = event;

  return {
    timestamp: new Date(timestamp).toISOString(),
    model: model,
    provider: provider || "unknown",
    input_tokens: usage.input || usage.promptTokens || 0,
    output_tokens: usage.output || 0,
    cache_read_tokens: usage.cacheRead || 0,
    cache_creation_tokens: usage.cacheWrite || 0,
    request_id: sessionId,
    metadata: {
      source: "clawdbot",
      cost_usd: costUsd,
      duration_ms: durationMs,
      context_limit: context?.limit,
      context_used: context?.used,
    }
  };
}

/**
 * Write token usage to OpenCLAW format log file
 */
async function writeTokenUsage(event) {
  if (event.type !== "model.usage") {
    return;
  }

  const entry = toOpenclawFormat(event);
  const date = new Date(event.timestamp || event.ts).toISOString().split('T')[0];
  const logFile = path.join(LOG_DIR, `usage_${date}.jsonl`);

  const logLine = JSON.stringify(entry) + "\n";
  await fs.appendFile(logFile, logLine);

  console.log(`[OpenCLAW] Logged ${entry.input_tokens + entry.output_tokens} tokens for ${entry.model}`);
}

/**
 * Register the diagnostic event listener
 */
export function registerOpenclawAdapter() {
  try {
    const { onDiagnosticEvent } = await import("./infra/diagnostic-events.js");

    onDiagnosticEvent((event) => {
      writeTokenUsage(event).catch(err => {
        console.error("[OpenCLAW] Failed to log token usage:", err);
      });
    });

    console.log("[OpenCLAW] Token usage adapter registered successfully");
  } catch (err) {
    console.error("[OpenCLAW] Failed to register adapter:", err);
  }
}

// Auto-register when imported
registerOpenclawAdapter();
```

### 2. 在 Clawdbot 中加载适配器

在 Clawdbot 的入口文件中添加：

```javascript
// Import the adapter
import "./openclaw-adapter.js";
```

### 3. 查看记录的日志

日志会写入到 `~/.openclaw/logs/openclaw/` 目录：

```
~/.openclaw/logs/openclaw/
├── usage_2026-03-11.jsonl
├── usage_2026-03-12.jsonl
└── ...
```

### 4. 使用 OpenCLAW Monitor 查看统计

```bash
# 查看 Clawdbot 的 token 使用
openclaw-monitor --view daily --log-path ~/.openclaw/logs/openclaw

# 查看详细细分
openclaw-monitor --view detailed --log-path ~/.openclaw/logs/openclaw
```

## 方法 3: 手动记录（快速测试）

如果你不想修改 Clawdbot 代码，可以使用 Clawdbot 的装饰器：

```python
# 在你的 Clawdbot 技能中
from openclaw_logger import log_usage

@log_llm_call(model="claude-3-5-sonnet")
def call_llm(prompt):
    # 你的 LLM 调用代码
    response = client.messages.create(...)
    return response
```

## 验证集成

运行以下命令验证集成是否正常工作：

```bash
# 1. 检查日志文件是否生成
ls -la ~/.openclaw/logs/openclaw/

# 2. 查看日志内容
cat ~/.openclaw/logs/openclaw/usage_*.jsonl | head -5

# 3. 使用 OpenCLAW Monitor 查看统计
openclaw-monitor --view daily --log-path ~/.openclaw/logs/openclaw
```

## 故障排查

### 问题：日志文件为空

**原因**: Clawdbot 的诊断功能未启用

**解决方案**:
1. 编辑 `~/.openclaw/openclaw.json`
2. 添加 `"diagnostics": {"enabled": true}`
3. 重启 Clawdbot
4. 进行一次 LLM 调用

### 问题：日志文件中没有 token 数据

**原因**: Clawdbot 没有发送 `model.usage` 事件

**解决方案**:
1. 确认 Clawdbot 确实调用了 LLM
2. 检查 Clawdbot 的日志是否有错误
3. 启用 Clawdbot 的调试模式查看诊断事件

### 问题：OpenCLAW Monitor 显示 0

**原因**: 日志路径不正确或时间范围不对

**解决方案**:
1. 确认日志文件路径正确
2. 使用 `--view detailed` 查看更多细节
3. 检查日志文件的时间戳是否在查询范围内

## 相关文件

- `src/openclaw_monitor/data/parsers/clawdbot.py` - Clawdbot 日志解析器
- `openclaw_logger.py` - OpenCLAW 日志记录器
- `llm_wrapper.py` - LLM API 包装器
- `LOGGING_GUIDE.md` - 完整使用指南
