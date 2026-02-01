#!/usr/bin/env python3
"""
Soaking reminders for tomorrow's breakfast, lunch, and snacks.

Run at 5pm UTC. Sends WhatsApp at 5pm *today* about soaking items for *tomorrow's*
breakfast, lunch, and snacks.

Usage (Railway cron, UTC):
    Schedule: 0 17 * * *   (5pm UTC daily)
    Command:  python cron_jobs/send_soaking_reminders_tomorrow_meals.py
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
    SOAKING_FOR_TOMORROW_MEALS,
)

if __name__ == "__main__":
    result = asyncio.run(run_soaking_reminders(soaking_for=SOAKING_FOR_TOMORROW_MEALS))
    sys.exit(0 if result.get("success", False) else 1)
