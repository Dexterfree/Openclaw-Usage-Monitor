#!/usr/bin/env node
/**
 * Standalone test for OpenCLAW Token Logger
 * This script tests the complete flow: emit diagnostic events -> logger captures them -> write to file
 */

import { emitDiagnosticEvent, onDiagnosticEvent } from 'file:///C:/Users/39643/AppData/Roaming/npm/node_modules/openclaw-cn/dist/infra/diagnostic-events.js';
import fs from 'node:fs/promises';
import path from 'path';

const LOG_DIR = "C:/Users/39643/.openclaw/logs/openclaw";

// Ensure log directory exists
await fs.mkdir(LOG_DIR, { recursive: true });

console.log("=".repeat(60));
console.log("OpenCLAW Token Logger - Standalone Test");
console.log("=".repeat(60));
console.log();

// Define the toOpenclawFormat function (same as in token logger)
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
      source: "clawdbot-test",
      session_key: sessionKey,
      channel: channel,
      cost_usd: costUsd,
      duration_ms: durationMs,
      context_limit: context?.limit,
      context_used: context?.used,
    }
  };
}

// Define the writeTokenUsage function
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

// Register the listener
onDiagnosticEvent((event) => {
  console.log(`[DEBUG] Received event: ${event.type}`);
  writeTokenUsage(event).catch(err => {
    console.error("[OpenCLAW] Failed to handle diagnostic event:", err);
  });
});

console.log("[OpenCLAW] Token logger registered");
console.log(`[OpenCLAW] Logging to: ${LOG_DIR}`);
console.log();

// Emit test events
const testEvents = [
  {
    type: "model.usage",
    model: "minimax/MiniMax-M2.5",
    provider: "minimax",
    sessionId: "test-session-001",
    sessionKey: "test-key",
    channel: "test",
    usage: {
      input: 1500,
      output: 300,
      cacheRead: 0,
      cacheWrite: 0,
      promptTokens: 1500,
      total: 1800
    },
    context: {
      limit: 200000,
      used: 1800
    },
    costUsd: 0.027,
    durationMs: 1250,
    ts: Date.now()
  },
  {
    type: "model.usage",
    model: "dexter/Qwen3-32B-Instruct",
    provider: "dexter",
    sessionId: "test-session-002",
    usage: {
      input: 800,
      output: 150,
      cacheRead: 100,
      cacheWrite: 0,
      total: 950
    },
    context: {
      limit: 128000,
      used: 950
    },
    costUsd: 0,
    durationMs: 800,
    ts: Date.now()
  },
  {
    type: "model.usage",
    model: "minimax/MiniMax-M2.5",
    provider: "minimax",
    sessionId: "test-session-003",
    usage: {
      input: 2500,
      output: 500,
      cacheRead: 200,
      cacheWrite: 100,
      total: 3000
    },
    context: {
      limit: 200000,
      used: 3000
    },
    costUsd: 0.045,
    durationMs: 2100,
    ts: Date.now()
  }
];

console.log("[TEST] Emitting", testEvents.length, "model.usage events...");
console.log();

testEvents.forEach((event, i) => {
  emitDiagnosticEvent(event);
  console.log(`[TEST] Emitted event ${i + 1}: ${event.model} - ${event.usage.input + event.usage.output} tokens`);
});

console.log();
console.log("=".repeat(60));
console.log("Test Complete. Check log file for results.");
console.log("=".repeat(60));
