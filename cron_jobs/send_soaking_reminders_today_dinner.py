#!/usr/bin/env python3
"""
Soaking reminders for today's dinner.

Run at 5am UTC. Sends WhatsApp at 5am *today* about soaking items for *today's* dinner.

Usage (Railway cron, UTC):
    Schedule: 0 5 * * *   (5am UTC daily)
    Command:  python cron_jobs/send_soaking_reminders_today_dinner.py
"""

import sys
import os
import asyncio

# Project root and cron_jobs on path so app and send_soaking_reminders are importable
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from send_soaking_reminders import (
    run_soaking_reminders,
    SOAKING_FOR_TODAY_DINNER,
)

if __name__ == "__main__":
    result = asyncio.run(run_soaking_reminders(soaking_for=SOAKING_FOR_TODAY_DINNER))
    sys.exit(0 if result.get("success", False) else 1)
