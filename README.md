# OpenCLAW Token Usage Monitor

A universal token usage monitoring tool for all LLM providers. Focuses on token tracking without any cost/price calculations.

## Features

- **Universal LLM Support** - Works with OpenAI, Claude, Gemini, local models, and any other LLM
- **Format Agnostic** - Automatically detects and parses JSON/JSONL logs from various sources
- **Multiple View Modes** - Realtime monitoring, daily reports, and monthly summaries
- **Zero Cost Tracking** - Focuses purely on token usage, no pricing information
- **Session Analysis** - Tracks API usage sessions with configurable gaps
- **Flexible Configuration** - Custom token limits, timezones, and refresh rates

## Installation

```bash
pip install openclaw-monitor
```

Or install from source:

```bash
pip install -e .
```

## Quick Start

### Realtime Monitoring

```bash
openclaw-monitor --view realtime --plan medium --log-path ./logs
```

### Daily Report

```bash
openclaw-monitor --view daily --log-path ./logs
```

### Monthly Report

```bash
openclaw-monitor --view monthly --log-path ./logs
```

## Usage

### Command-Line Options

```
openclaw-monitor [OPTIONS]

Options:
  --view {realtime,daily,monthly}
                          View mode for displaying usage data (default: realtime)
  --plan {small,medium,large,unlimited,custom}
                          Token limit plan (default: medium)
  --custom-limit-tokens N  Custom token limit (required when --plan=custom)
  --log-path PATH          Path to log file or directory containing usage logs
  --refresh-rate SECONDS   Refresh rate in seconds for realtime view (default: 5)
  --timezone TZ            Timezone for displaying timestamps (default: UTC)
  --session-gap-minutes MINUTES
                          Minutes of inactivity before starting a new session (default: 30)
  --session-window-hours HOURS
                          Hours to look back for session tracking (default: 5)
  --warning-threshold PERCENT
                          Percentage threshold for showing warnings (default: 75.0)
  --critical-threshold PERCENT
                          Percentage threshold for showing critical warnings (default: 90.0)
  --color-scheme {auto,light,dark}
                          Color scheme for UI (default: auto)
  --debug                  Enable debug logging
  --verbose                Enable verbose output
  --version                Show version and exit
  -h, --help               Show help message
```

### Plans

The following predefined plans are available:

| Plan    | Token Limit | Description          |
|---------|-------------|----------------------|
| small   | 100,000     | Small project        |
| medium  | 1,000,000   | Medium project       |
| large   | 10,000,000  | Large project        |
| unlimited | 0         | No limit             |
| custom  | (specify)   | Custom token limit   |

## Log Format

OpenCLAW Monitor automatically detects and parses various log formats. Your logs should be JSON or JSONL format with token usage information.

### Supported Formats

The monitor can parse logs from:

- **OpenAI API** - Standard OpenAI response format
- **Claude API** - Anthropic Claude format
- **Generic** - Any JSON with token-related fields
- **OpenCLAW** - Native OpenCLAW format

### Example Log Entries

```jsonl
{"timestamp": "2025-01-01T10:00:00Z", "model": "gpt-4o", "prompt_tokens": 100, "completion_tokens": 50}
{"timestamp": "2025-01-01T10:05:00Z", "model": "claude-3-5-sonnet", "input_tokens": 200, "output_tokens": 100}
{"timestamp": "2025-01-01T10:10:00Z", "model": "llama-3-70b", "tokens_in": 150, "tokens_out": 75}
```

### OpenCLAW Format

For best compatibility, use the native OpenCLAW format:

```json
{
  "timestamp": "2025-01-01T10:00:00Z",
  "model": "gpt-4o",
  "provider": "openai",
  "input_tokens": 100,
  "output_tokens": 50,
  "cache_read_tokens": 0,
  "cache_creation_tokens": 0,
  "request_id": "req_abc123"
}
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/openclaw/openclaw-monitor.git
cd openclaw-monitor

# Install in editable mode
pip install -e ".[dev]"

# Run tests
pytest
```

### Project Structure

```
openclaw_monitor/
├── cli/              # Command-line interface
├── core/             # Core business logic
├── data/             # Data processing and parsing
├── monitoring/       # Realtime monitoring
├── terminal/         # Terminal themes
├── ui/               # User interface components
└── utils/            # Utility functions
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
