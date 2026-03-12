/**
 * OpenCLAW Token Usage Logger for Clawdbot
 *
 * This module listens for model.usage diagnostic events and writes
 * them to OpenCLAW-compatible JSONL log files.
 *
 * INSTALLATION:
 * 1. Copy this file to: C:\Users\39643\.openclaw\openclaw-token-logger.js
 * 2. Add to ~/.openclaw/openclaw.json:
 *    {
 *      "diagnostics": {
 *        "enabled": true
 *      },
 *      "hooks": {
 *        "startup": {
 *          "enabled": true,
 *          "entries": {
 *            "token-logger": {
 *              "enabled": true,
 *              "module": "C:\\Users\\39643\\.openclaw\\openclaw-token-logger.js"
 *            }
 *          }
 *        }
 *      }
 *    }
 * 3. Restart Clawdbot: npx openclaw-cn gateway restart
 */

import fs from "node:fs/promises";
import path from "path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const LOG_DIR = path.join(process.env.USERPROFILE || ".", ".openclaw", "logs", "openclaw");

// Ensure log directory exists
await fs.mkdir(LOG_DIR, { recursive: true });

/**
 * Convert a model.usage diagnostic event to OpenCLAW format
 */
function toOpenclawFormat(event) {
  const { usage, context, costUsd, durationMs, ts, model, provider, sessionId, sessionKey, channel } = event;

  return {
    timestamp: new Date(ts).toISOString(),
    model: model,
    provider: provider || "unknown",
    input_tokens: usage.input || usage.promptTokens || 0,
    output_tokens: usage.output || 0,
    cache_read_tokens: usage.cacheRead || 0,
    cache_creation_tokens: usage.cacheWrite || 0,
    request_id: sessionId,
    metadata: {
      source: "clawdbot",
      session_key: sessionKey,
      channel: channel,
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

  try {
    const entry = toOpenclawFormat(event);
    const date = new Date(event.ts).toISOString().split('T')[0];
    const logFile = path.join(LOG_DIR, `usage_${date}.jsonl`);

    const logLine = JSON.stringify(entry) + "\n";
    await fs.appendFile(logFile, logLine);

    console.log(`[OpenCLAW] Logged ${entry.input_tokens + entry.output_tokens} tokens for ${entry.model}`);
  } catch (err) {
    console.error("[OpenCLAW] Failed to log token usage:", err);
  }
}

/**
 * Register the diagnostic event listener
 */
export default async function registerOpenclawTokenLogger({ onDiagnosticEvent }) {
  if (!onDiagnosticEvent) {
    console.error("[OpenCLAW] onDiagnosticEvent not available in hooks context");
    return;
  }

  onDiagnosticEvent((event) => {
    writeTokenUsage(event).catch(err => {
      console.error("[OpenCLAW] Failed to handle diagnostic event:", err);
    });
  });

  console.log("[OpenCLAW] Token usage logger registered successfully");
  console.log(`[OpenCLAW] Logging to: ${LOG_DIR}`);
}

// Alternative: direct import usage
import { onDiagnosticEvent } from "openclaw-cn/dist/infra/diagnostic-events.js";

onDiagnosticEvent((event) => {
  writeTokenUsage(event).catch(err => {
    console.error("[OpenCLAW] Failed to handle diagnostic event:", err);
  });
});

console.log("[OpenCLAW] Token usage logger registered (standalone mode)");
console.log(`[OpenCLAW] Logging to: ${LOG_DIR}`);
