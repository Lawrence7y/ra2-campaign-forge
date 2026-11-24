#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""NEXT_RE_20261112_R02 / W14 —— UI 观察者（独立进程，1s 周期，只读）。

设计动机：采样器进程在 6 ms 高频下必须零 GIL 争用 —— 若 UI 扫描（EnumWindows/
EnumChildWindows，持 GIL 的 Python 回调）与采样器同进程，单次扫描的停顿会污染
采样间隔分布并制造伪「Δframe≥2 / ≥64ms」事件。故本进程独立于采样器进程
（由探针经 WMI 启动，脱离探针进程树），每 1s 写一次：
  out\ui_watch.ndjson   完整观察记录（逐行 flush）
  out\state.json        原子替换的当前状态（采样器 ~1s 读一次）
状态字段：t_mono_ns/t_utc_iso/fg/alive/last_input_dwtime/continue_hits/
natural_end/natural_end_t_mono_ns/natural_end_buttons。

自然结束判定（与 W13 同口径）：连续 2 次扫描发现可见 Button text 含 "continue"
（不分大小写）⇒ natural_end=True（记第二次扫描的 t_mono_ns）。

退出条件（任一）：out\watcher_stop.json 存在；游戏进程消失；硬超时。
本进程零输入（只读枚举）；写 out\watcher_done.txt 作为退出标记。
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import datetime
import json
import os
import sys
import time
from pathlib import Path

u = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)

for fn, rt, at in [
    ("GetWindowThreadProcessId", wt.DWORD, [wt.HWND, ctypes.POINTER(wt.DWORD)]),
    ("GetWindowTextLengthW", ctypes.c_int, [wt.HWND]),
    ("GetWindowTextW", ctypes.c_int, [wt.HWND, wt.LPWSTR, ctypes.c_int]),
    ("GetClassNameW", ctypes.c_int, [wt.HWND, wt.LPWSTR, ctypes.c_int]),
    ("EnumWindows", wt.BOOL, [ctypes.c_void_p, wt.LPARAM]),
    ("EnumChildWindows", wt.BOOL, [wt.HWND, ctypes.c_void_p, wt.LPARAM]),
    ("IsWindowVisible", wt.BOOL, [wt.HWND]),
    ("GetForegroundWindow", wt.HWND, []),
    ("GetLastInputInfo", wt.BOOL, [ctypes.c_void_p]),
]:
    f = getattr(u, fn)
    f.restype = rt
    f.argtypes = at

k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.GetExitCodeProcess.restype = wt.BOOL
k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
k32.GetCurrentProcess.restype = wt.HANDLE
k32.SetPriorityClass.argtypes = [wt.HANDLE, wt.DWORD]

ENUM = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
STILL_ACTIVE = 259


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.UINT), ("dwTime", wt.DWORD)]


def utc_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def controls_texts(pid):
    """枚举 pid 的全部窗口与子控件，返回 [(class, text, visible)]。"""
    tops = []

    def cb(h, l):
        q = wt.DWORD(0)
        u.GetWindowThreadProcessId(h, ctypes.byref(q))
        if q.value == pid:
            tops.append(h)
        return True

    u.EnumWindows(ENUM(cb), 0)
    out, seen = [], set()

    def wtxt(h):
        n = u.GetWindowTextLengthW(h)
        b = ctypes.create_unicode_buffer(max(n + 1, 2))
        u.GetWindowTextW(h, b, n + 1)
        return b.value

    def wcls(h):
        b = ctypes.create_unicode_buffer(256)
        u.GetClassNameW(h, b, 256)
        return b.value

    def walk(h):
        kids = []

        def ccb(kk, l):
            kids.append(kk)
            return True

        u.EnumChildWindows(h, ENUM(ccb), 0)
        for kk in kids:
            if kk not in seen:
                seen.add(kk)
                out.append((wcls(kk), wtxt(kk), bool(u.IsWindowVisible(kk))))
            walk(kk)

    for t in tops:
        walk(t)
    return out


def fg_is(pid):
    fg = u.GetForegroundWindow()
    p = wt.DWORD(0)
    u.GetWindowThreadProcessId(fg, ctypes.byref(p))
    return p.value == pid


def last_input_dwtime():
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if u.GetLastInputInfo(ctypes.byref(lii)):
        return int(lii.dwTime)
    return None


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, required=True)
    ap.add_argument("--interval-ms", type=float, default=1000.0)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--hard-timeout-s", type=float, default=1500.0)
    a = ap.parse_args()
    outdir = Path(a.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    stop_file = outdir / "watcher_stop.json"
    state_file = outdir / "state.json"
    state_tmp = outdir / "state.json.tmp"
    ndjson_path = outdir / "ui_watch.ndjson"

    try:
        k32.SetPriorityClass(k32.GetCurrentProcess(), 0x00004000)
    except Exception:
        pass

    hproc = k32.OpenProcess(0x0400, False, a.pid)  # QUERY_INFORMATION 只读
    nd_f = ndjson_path.open("w", encoding="utf-8", newline="\n")
    n_lines = 0

    def wrec(rec):
        nonlocal n_lines
        nd_f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":"), default=str) + "\n")
        nd_f.flush()
        n_lines += 1

    def wstate(data):
        try:
            with state_tmp.open("w", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False, sort_keys=True,
                                   default=str))
            os.replace(state_tmp, state_file)     # 原子替换，采样器无半读
        except Exception:
            pass

    t0 = time.perf_counter_ns()
    prev_cont = []
    natural_end = False
    natural_end_t = None
    natural_end_buttons = None
    reason = None
    try:
        wstate({"t_mono_ns": t0, "t_utc_iso": utc_iso(), "alive": True,
                "fg": False, "continue_hits": [], "natural_end": False,
                "watcher_pid": os.getpid(), "watching_pid": a.pid})
        while True:
            now = time.perf_counter_ns()
            if (now - t0) / 1e9 >= a.hard_timeout_s:
                reason = "hard_timeout"
                break
            if stop_file.exists():
                reason = "stop_file"
                break
            ec = wt.DWORD(0)
            alive = False
            if hproc:
                alive = bool(k32.GetExitCodeProcess(hproc, ctypes.byref(ec))
                             and ec.value == STILL_ACTIVE)
            else:
                alive = False
            if not alive:
                reason = "game_process_exited"
                break
            try:
                btns = [(t, bool(v)) for (c, t, v) in controls_texts(a.pid)
                        if c == "Button"]
                vis = [t for (t, v) in btns if v]
                cont = [t for t in vis if "continue" in (t or "").lower()]
                fg = fg_is(a.pid)
                li = last_input_dwtime()
                rec = {"kind": "ui_watch", "t_mono_ns": now,
                       "t_utc_iso": utc_iso(), "win_foreground": fg,
                       "alive": alive, "button_texts_visible": vis,
                       "continue_hits": cont, "last_input_dwtime": li}
                wrec(rec)
                if cont and prev_cont and not natural_end:
                    natural_end = True
                    natural_end_t = now
                    natural_end_buttons = cont
                    wrec({"kind": "event", "t_mono_ns": now,
                          "t_utc_iso": utc_iso(), "event": "natural_end",
                          "buttons": cont,
                          "rule": "连续 2 次 ui_watch 发现可见 continue 类 Button"})
                prev_cont = cont
                wstate({"t_mono_ns": now, "t_utc_iso": utc_iso(),
                        "fg": fg, "alive": alive, "last_input_dwtime": li,
                        "continue_hits": cont, "natural_end": natural_end,
                        "natural_end_t_mono_ns": natural_end_t,
                        "natural_end_buttons": natural_end_buttons,
                        "watcher_pid": os.getpid(), "watching_pid": a.pid,
                        "n_scans": n_lines})
            except Exception as e:
                wrec({"kind": "event", "t_mono_ns": time.perf_counter_ns(),
                      "t_utc_iso": utc_iso(), "event": "watcher_scan_error",
                      "detail": repr(e)})
            time.sleep(a.interval_ms / 1000.0)
    finally:
        try:
            wrec({"kind": "ui_watch_end", "t_mono_ns": time.perf_counter_ns(),
                  "t_utc_iso": utc_iso(), "reason": reason or "finally",
                  "n_lines": n_lines})
        except Exception:
            pass
        try:
            wstate({"t_mono_ns": time.perf_counter_ns(), "t_utc_iso": utc_iso(),
                    "alive": None, "fg": None, "continue_hits": [],
                    "natural_end": natural_end,
                    "natural_end_t_mono_ns": natural_end_t,
                    "natural_end_buttons": natural_end_buttons,
                    "watcher_pid": os.getpid(), "watching_pid": a.pid,
                    "stopped": True, "reason": reason or "finally"})
        except Exception:
            pass
        try:
            (outdir / "watcher_done.txt").write_text(
                "reason=%s\nlines=%d\nended_utc=%s\n" %
                (reason or "finally", n_lines, utc_iso()), encoding="utf-8")
        except Exception:
            pass
        try:
            nd_f.close()
        except Exception:
            pass
        if hproc:
            try:
                k32.CloseHandle(hproc)
            except Exception:
                pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
