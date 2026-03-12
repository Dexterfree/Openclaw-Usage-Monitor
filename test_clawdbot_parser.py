#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for Clawdbot parser.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')

from src.openclaw_monitor.data.parsers.clawdbot import (
    parse_clawdbot_directory,
    load_clawdbot_logs,
    parse_clawdbot_log_line
)

print('=' * 50)
print('Testing Clawdbot Parser')
print('=' * 50)
print()

LOG_DIR = r'C:\tmp\clawdbot'

# First, let's look at a few raw log lines to understand the format
print('1. Examining raw log format...')
print('-' * 50)
import os
log_files = [f for f in os.listdir(LOG_DIR) if f.endswith('.log')]
print(f"   Found {len(log_files)} log files: {log_files}")

# Read a few sample lines
sample_lines = []
for log_file in sorted(log_files)[-1:]:  # Check latest file
    full_path = os.path.join(LOG_DIR, log_file)
    with open(full_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 5:
                break
            sample_lines.append(line.strip())

print(f"\n   Sample log lines ({len(sample_lines)}):")
for i, line in enumerate(sample_lines[:3]):
    print(f"   [{i+1}] {line[:150]}...")
    parsed = parse_clawdbot_log_line(line)
    if parsed:
        print(f"       Parsed: type={parsed.get('type', 'N/A')}, subsystem={parsed.get('subsystem', 'N/A')}")
print()

# Load all raw logs
print('2. Loading raw logs from last 24 hours...')
print('-' * 50)
raw_logs = load_clawdbot_logs(LOG_DIR, hours_back=24)
print(f"   Total log entries: {len(raw_logs)}")

# Count by type
type_counts = {}
for log in raw_logs:
    log_type = log.get('type', log.get('subsystem', 'unknown'))
    type_counts[log_type] = type_counts.get(log_type, 0) + 1

print(f"   Entry types: {dict(list(type_counts.items())[:5])}")
print()

# Extract token usage
print('3. Extracting token usage entries...')
print('-' * 50)
token_entries = parse_clawdbot_directory(LOG_DIR, hours_back=24)
print(f"   Token usage entries: {len(token_entries)}")
print()

if token_entries:
    print('4. Token usage details:')
    print('-' * 50)
    for entry in token_entries[:5]:
        print(f"   Model: {entry.get('model', 'unknown')}")
        print(f"   Provider: {entry.get('provider', 'unknown')}")
        print(f"   Tokens: {entry.get('input_tokens', 0)} + {entry.get('output_tokens', 0)}")
        if entry.get('cache_read_tokens'):
            print(f"   Cache: {entry.get('cache_read_tokens')} read, {entry.get('cache_creation_tokens')} write")
        if entry.get('metadata', {}).get('cost_usd'):
            print(f"   Cost: ${entry.get('metadata').get('cost_usd'):.4f}")
        print()

    # Summary
    total_input = sum(e.get('input_tokens', 0) for e in token_entries)
    total_output = sum(e.get('output_tokens', 0) for e in token_entries)
    total_cache_read = sum(e.get('cache_read_tokens', 0) for e in token_entries)
    total_cache_write = sum(e.get('cache_creation_tokens', 0) for e in token_entries)

    print('5. Summary:')
    print('-' * 50)
    print(f"   Total requests: {len(token_entries)}")
    print(f"   Input tokens: {total_input:,}")
    print(f"   Output tokens: {total_output:,}")
    print(f"   Cache read: {total_cache_read:,}")
    print(f"   Cache write: {total_cache_write:,}")
    print(f"   Total tokens: {total_input + total_output + total_cache_read + total_cache_write:,}")
else:
    print('   No token usage entries found!')
    print()
    print('   Possible reasons:')
    print('   - Clawdbot diagnostics are not enabled')
    print('   - No LLM calls have been made since diagnostics were enabled')
    print('   - Token usage is logged elsewhere (OpenTelemetry, etc.)')
    print()
    print('   To enable diagnostics, add to ~/.openclaw/openclaw.json:')
    print('   {"diagnostics": {"enabled": true}}')

print()
print('=' * 50)
print('Test Complete')
print('=' * 50)
