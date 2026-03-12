"""
Main entry point for OpenCLAW Token Usage Monitor.

Usage:
    python -m openclaw_monitor --view realtime --plan medium
    python -m openclaw_monitor --view daily
"""

from openclaw_monitor.cli.main import main

if __name__ == "__main__":
    main()
