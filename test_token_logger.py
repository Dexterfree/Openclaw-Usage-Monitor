#!/usr/bin/env python
"""
Test script to generate model.usage diagnostic events.
This simulates what happens when Clawdbot makes an LLM call.
"""

import subprocess
import json
import time
from datetime import datetime

# This will emit a diagnostic event through the running gateway
test_script = '''
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
'''

print("=" * 60)
print("Testing OpenCLAW Token Logger")
print("=" * 60)
print()

# Write the test script to a temp file
temp_file = "D:/software/Openclaw-Usage-Monitor/test_diagnostic_events.mjs"
with open(temp_file, "w") as f:
    f.write(test_script)

print("Running test script to emit diagnostic events...")
print()

# Run the test
result = subprocess.run(
    ["node", temp_file],
    capture_output=True,
    text=True,
    cwd="D:/software/Openclaw-Usage-Monitor"
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

print()
print("=" * 60)
print("Checking for generated log files...")
print("=" * 60)
print()

# Check if log files were created
import os
log_dir = "C:/Users/39643/.openclaw/logs/openclaw"
if os.path.exists(log_dir):
    log_files = [f for f in os.listdir(log_dir) if f.endswith('.jsonl')]
    if log_files:
        print(f"Found log files: {log_files}")
        print()

        # Read and display the latest log file
        latest_log = sorted(log_files)[-1]
        log_path = os.path.join(log_dir, latest_log)
        print(f"Contents of {latest_log}:")
        print("-" * 60)
        with open(log_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                print(f"  Model: {data['model']}")
                print(f"  Tokens: {data['input_tokens']} + {data['output_tokens']}")
                if data.get('cache_read_tokens'):
                    print(f"  Cache: {data['cache_read_tokens']} read, {data['cache_creation_tokens']} write")
                if data.get('metadata', {}).get('cost_usd'):
                    print(f"  Cost: ${data['metadata']['cost_usd']:.4f}")
                print()
    else:
        print("No log files found yet.")
else:
    print(f"Log directory not found: {log_dir}")

print("=" * 60)
print("Test Complete")
print("=" * 60)
