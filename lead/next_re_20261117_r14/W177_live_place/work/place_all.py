#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动放置 NAPOWR ≥10 次，每次前/后只读快照。输出 JSONL 到 out 文件。
用 (a) count_types.scan 做只读快照，(b) 合成输入进入建造模式并点击空地。
"""
import argparse
import ctypes
import json
import subprocess
import sys
import time
from ctypes import wintypes as wt

import w177_core as W
from count_types import scan as scan_types

u32 = ctypes.windll.user32
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.mouse_event.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD, wt.DWORD, ctypes.c_size_t]
u32.SetForegroundWindow.argtypes = [wt.HWND]
u32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
u32.GetForegroundWindow.restype = wt.HWND
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
LEFTDOWN, LEFTUP = 0x0002, 0x0004


def pid_of():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process gamemd -ErrorAction SilentlyContinue).Id"],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


def game_hwnd(pid):
    found = []

    def cb(hwnd, lp):
        t = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(t))
        if t.value == pid and u32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    EP = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    u32.EnumWindows(EP(cb), 0)
    return found[0] if found else None


def click_at(x, y, hold=0.28):
    u32.SetCursorPos(x, y)
    time.sleep(0.35)
    u32.SetCursorPos(x + 2, y + 2)
    time.sleep(0.12)
    u32.SetCursorPos(x, y)
    time.sleep(0.45)
    u32.mouse_event(LEFTDOWN, 0, 0, 0, 0)
    time.sleep(hold)
    u32.mouse_event(LEFTUP, 0, 0, 0, 0)
    time.sleep(0.45)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--target", type=int, default=11)
    ap.add_argument("--coords", default="1100,900;1300,700;900,500;1500,600;600,900;1200,400;800,650;1400,850;1000,350;700,550;1600,750;900,800;1050,600;1350,900;750,400")
    a = ap.parse_args()
    try:
        u32.SetProcessDPIAware()
    except Exception:
        pass
    pid = pid_of()
    if not pid:
        print("no gamemd")
        return 2
    hwnd = game_hwnd(pid)
    if hwnd:
        u32.SetForegroundWindow(hwnd)
        time.sleep(0.2)
    coords = []
    for c in a.coords.split(";"):
        x, y = c.split(",")
        coords.append((int(x), int(y)))
    f = open(a.out, "w", encoding="utf-8")

    def log(rec):
        f.write(json.dumps(rec) + "\n")
        f.flush()
        print(json.dumps({k: rec[k] for k in ("attempt", "x", "y", "frame_before", "frame_after",
                                              "yapowr_before", "yapowr_after", "ok")}))

    attempt = 0
    # 只在开头进入一次建造模式；之后连续点击坐标（重复点建造栏会取消模式）
    click_at(2340, 467, hold=0.10)
    time.sleep(0.3)
    for x, y in coords:
        before = scan_types(pid)
        yb = before["types"].get("YAPOWR", 0)
        if yb >= a.target:
            log({"attempt": attempt, "x": x, "y": y, "note": "target reached",
                 "yapowr_before": yb, "yapowr_after": yb,
                 "frame_before": before["frame"], "frame_after": before["frame"], "ok": True})
            break
        # 放置（不再重新点建造栏）
        click_at(x, y, hold=0.28)
        time.sleep(1.0)
        after = scan_types(pid)
        ya = after["types"].get("YAPOWR", 0)
        attempt += 1
        ok = ya > yb
        if not ok:
            # 可能模式被取消，重新进入一次
            click_at(2340, 467, hold=0.10)
            time.sleep(0.3)
        rec = {"attempt": attempt, "x": x, "y": y,
               "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
               "frame_before": before["frame"], "frame_after": after["frame"],
               "mode_before": before["mode"], "mode_after": after["mode"],
               "objects_before": before["objects"], "objects_after": after["objects"],
               "yapowr_before": yb, "yapowr_after": ya, "ok": ok,
               "before": before, "after": after}
        log(rec)
    f.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
