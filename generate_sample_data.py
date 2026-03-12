"""
生成示例 Token 使用日志数据

用于演示 OpenCLAW Monitor 的功能。
"""

import json
import random
from datetime import datetime, timedelta

# 日志目录
LOG_DIR = "./logs"


def generate_sample_entries(days=7, entries_per_day=20):
    """生成示例日志条目"""
    entries = []

    # 模型配置
    models = [
        ("claude-3-5-sonnet", "anthropic", 0.6),  # 60% 概率
        ("claude-3-opus", "anthropic", 0.15),
        ("claude-3-haiku", "anthropic", 0.10),
        ("gpt-4o", "openai", 0.10),
        ("gpt-4o-mini", "openai", 0.05),
    ]

    # 生成日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    for day in range(days):
        current_date = start_date + timedelta(days=day)

        # 每天生成多个条目
        for _ in range(entries_per_day):
            # 随机选择模型
            model_info = random.choices(
                [m[:2] for m in models],
                weights=[m[2] for m in models]
            )[0]
            model, provider = model_info

            # 生成 token 数量（模拟真实使用）
            input_tokens = random.randint(500, 5000)
            output_tokens = random.randint(200, 3000)

            # 10% 概率有缓存
            if random.random() < 0.3:
                cache_read = random.randint(50, 500)
                cache_write = random.randint(0, 200) if random.random() < 0.3 else 0
            else:
                cache_read = 0
                cache_write = 0

            # 随机时间（白天）
            hour = random.randint(8, 22)
            minute = random.randint(0, 59)
            timestamp = current_date.replace(
                hour=hour, minute=minute, second=random.randint(0, 59)
            )

            entry = {
                "timestamp": timestamp.isoformat() + "Z",
                "model": model,
                "provider": provider,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_tokens": cache_read,
                "cache_creation_tokens": cache_write,
                "request_id": f"req_{random.randint(100000, 999999)}",
            }
            entries.append(entry)

    # 按时间排序
    entries.sort(key=lambda x: x["timestamp"])
    return entries


def main():
    """生成示例数据"""
    import os
    from pathlib import Path

    # 创建日志目录
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    print("正在生成示例 Token 使用数据...")

    # 生成最近 7 天的数据
    entries = generate_sample_entries(days=7, entries_per_day=25)

    # 按日期分组写入文件
    from collections import defaultdict
    daily_entries = defaultdict(list)

    for entry in entries:
        # 提取日期
        timestamp = entry["timestamp"]
        date_str = timestamp.split("T")[0]
        daily_entries[date_str].append(entry)

    # 写入每个日期的日志文件
    for date_str, date_entries in daily_entries.items():
        log_file = log_dir / f"usage_{date_str}.jsonl"

        with open(log_file, "w", encoding="utf-8") as f:
            for entry in date_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        print(f"  [OK] 已写入: {log_file} ({len(date_entries)} 条记录)")

    # 统计信息
    total_tokens = sum(
        e["input_tokens"] + e["output_tokens"] +
        e["cache_read_tokens"] + e["cache_creation_tokens"]
        for e in entries
    )

    print(f"\n统计信息:")
    print(f"  总记录数: {len(entries)}")
    print(f"  总 Token 数: {total_tokens:,}")
    print(f"  日期范围: {min(daily_entries.keys())} 到 {max(daily_entries.keys())}")
    print(f"\n日志文件保存在: {log_dir.absolute()}")


if __name__ == "__main__":
    main()
