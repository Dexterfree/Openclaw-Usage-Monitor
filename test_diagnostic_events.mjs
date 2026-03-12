
import { emitDiagnosticEvent } from 'file:///C:/Users/39643/AppData/Roaming/npm/node_modules/openclaw-cn/dist/infra/diagnostic-events.js';

// Simulate multiple model.usage events as if they came from LLM calls
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

testEvents.forEach((event, i) => {
  emitDiagnosticEvent(event);
  console.log(`[TEST] Emitted event ${i + 1}: ${event.model} - ${event.usage.input + event.usage.output} tokens`);
});

console.log("[TEST] All events emitted. Check log directory for files.");
