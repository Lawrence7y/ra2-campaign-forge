#!/usr/bin/env python3
"""Resume the R17 goal after a daily budget reset following a Budget-Guard pause."""

import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen


GUARDIAN = "http://127.0.0.1:8896"
GOAL_PATH = Path("/home/t628/apps/harness/data/re_goal.json")
DAILY_PAUSE = "[re-guardian][alert] [Budget-Guard] Goal 已自动暂停：今日 "
GOAL_UPDATE = "[re-guardian][info] Goal updated via :8896 UI:"
ACTIVE_STATUSES = {"queued", "running", "pending", "starting"}


def last_goal_event():
    result = subprocess.run(
        ["journalctl", "-q", "-u", "t628-re-guardian", "-n", "1", "-o", "json",
         "--no-pager", "--grep", re.escape(DAILY_PAUSE) + "|" + re.escape(GOAL_UPDATE)],
        check=True, capture_output=True, text=True, timeout=10,
    )
    return json.loads(result.stdout) if result.stdout.strip() else {}


def may_resume(overview, event, goal_mtime):
    if not overview.get("ok") or not overview.get("all_invariants_ok"):
        return False
    goal = overview["goal"]
    spend = overview["spend"]
    if goal["active"] or goal.get("manual_compact_requested"):
        return False
    message = event.get("MESSAGE", "")
    if not message.startswith(DAILY_PAUSE) or "单轮预算" in message:
        return False
    paused_at = int(event["__REALTIME_TIMESTAMP"]) / 1_000_000
    if not (abs(goal_mtime - paused_at) <= 10 or
            paused_at < goal["last_compact_at"] and
            abs(goal_mtime - goal["last_compact_at"]) <= 10):
        return False
    if not paused_at < spend["today_started_at"]:
        return False
    if not (0 <= spend["today_usd"] < spend["daily_budget_usd"] and
            0 <= spend["current_round_usd"] < spend["round_budget_usd"]):
        return False
    return not any(
        session["status"] in ACTIVE_STATUSES
        for kind in ("main_sessions", "subagent_sessions")
        for session in overview[kind]
    )


def request(path, body=None):
    req = Request(GUARDIAN + path, data=body, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=10) as response:
        return json.load(response)


def main():
    goal_stat = GOAL_PATH.stat()
    overview = request("/api/overview")
    if overview.get("goal", {}).get("active"):
        return
    if not may_resume(overview, last_goal_event(), goal_stat.st_mtime):
        return
    if "--check" in sys.argv[1:]:
        print("Eligible for automatic resume after daily budget reset")
        return
    if GOAL_PATH.stat().st_mtime_ns != goal_stat.st_mtime_ns:
        return
    resumed = request("/api/goal", b'{"action":"resume"}')
    if not resumed.get("ok") or not resumed.get("goal", {}).get("active"):
        raise RuntimeError("Guardian did not confirm resume")
    print(f"Resumed R17 after daily budget reset at R{overview['goal']['current_round']}")


if __name__ == "__main__":
    main()
