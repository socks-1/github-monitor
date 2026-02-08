#!/usr/bin/env python3
"""
Continuous monitoring loop that checks repositories at regular intervals.
Alternative to cron for containerized environments.
"""

import time
import sys
import signal
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from monitor_check import main as run_check


class MonitorLoop:
    """Runs monitoring checks in a loop."""

    def __init__(self, interval_minutes: int = 20):
        self.interval_minutes = interval_minutes
        self.interval_seconds = interval_minutes * 60
        self.running = True

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\n\nReceived signal {signum}, shutting down...")
        self.running = False

    def run(self):
        """Main loop."""
        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        print(f"GitHub Monitor - Starting continuous loop")
        print(f"Check interval: {self.interval_minutes} minutes")
        print(f"Press Ctrl+C to stop\n")
        print("=" * 80)

        iteration = 0
        while self.running:
            iteration += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"\n[{timestamp}] Starting check #{iteration}")
            print("-" * 80)

            try:
                run_check()
            except Exception as e:
                print(f"\n❌ Error during monitoring check: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc()

            if not self.running:
                break

            print(f"\n[{timestamp}] Check complete. Next check in {self.interval_minutes} minutes.")
            print("=" * 80)

            # Sleep in small increments to be responsive to shutdown signals
            for _ in range(self.interval_seconds):
                if not self.running:
                    break
                time.sleep(1)

        print("\n✓ Monitor loop stopped cleanly")


if __name__ == "__main__":
    # Allow interval to be specified as command-line arg
    interval = 20
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            print(f"Invalid interval: {sys.argv[1]}, using default: 20 minutes")

    loop = MonitorLoop(interval_minutes=interval)
    loop.run()
