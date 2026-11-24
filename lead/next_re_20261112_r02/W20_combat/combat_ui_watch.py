#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""NEXT_RE_20261112_R02 / W20 —— UI+线程观察者（独立进程，1s 周期，只读）。

RE-N04i 战斗维度（[8]试验地_Pro_ProvingGrounds.yrm / [8] Proving Grounds，52 建筑，
零输入 600 s）专用观察者；源：W15 tick_ui_watch.py → W18 → W19 load_u800_ui_watch.py
同链，仅改模块导入（ThreadTable 来自 combat_probe）与卡名，行为与 W15/W18/W19 一致：
每 1s 写 out\ui_watch.ndjson 与原子 state.json（fg/alive/last_input/natural_end/
thread_rows 含 ctx）。设计动机不变：采样器 6 ms 高频下必须零 GIL 争用，UI 扫描放
独立进程；状态供采样器 ~1s 读一次。

自然结束判定（与 W13/W14/W15/W19 同口径）：连续 2 次扫描发现可见 Button text 含
"continue"（不分大小写）⇒ natural_end=True（记第二次扫描的 t_mono_ns）。

★ W15 起线程表（辅助通道，主通道在采样器=窗口线程 GetThreadTimes/cycle）。
  GetThreadTimes 实签名 4 出参 = creation/exit/kernel/user，无 context switches
  出参。本进程用 NtQuerySystemInformation(SystemProcessInformation) 1Hz 只读获取
  每线程 KernelTime/UserTime/ContextSwitches，x64 布局解析并做 tid 集合校验
  （与 Toolhelp 快照一致才采信；不一致置 valid=False、thread_rows=None）。
  该通道与采样器零 GIL 争用。

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
import struct
import sys
import time
from pathlib import Path

u = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
nt = ctypes.WinDLL("ntdll")

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
k32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
k32.Thread32First.restype = wt.BOOL
k32.Thread32First.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
k32.Thread32Next.restype = wt.BOOL
k32.Thread32Next.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

nt.NtQuerySystemInformation.restype = ctypes.c_long      # NTSTATUS
nt.NtQuerySystemInformation.argtypes = [ctypes.c_ulong, ctypes.c_void_p,
                                        ctypes.c_ulong,
                                        ctypes.POINTER(ctypes.c_ulong)]

ENUM = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
STILL_ACTIVE = 259
STATUS_INFO_LENGTH_MISMATCH = 0xC0000004
SystemProcessInformation = 5
# x64 phnt 布局：进程头 256B 起 Threads[]，步长 80B；
# 线程内偏移 KernelTime=0 / UserTime=8 / ThreadId=48 / ContextSwitches=64
PROC_UNIQ_PID_OFF = 80
PROC_THREADS_OFF = 256
THREAD_STRIDE = 80
THREAD_TID_OFF = 48
THREAD_CTX_OFF = 64


class THREADENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
        ("th32ThreadID", wt.DWORD), ("th32OwnerProcessID", wt.DWORD),
        ("tpDeltaPri", ctypes.c_long), ("dwFlags", wt.DWORD),
        # 本机实测系统要求 dwSize=28（SDK 文档为 24）：补尾随 4 字节
        ("_pad_dwSize28", wt.DWORD),
    ]


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.UINT), ("dwTime", wt.DWORD)]


def utc_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def snapshot_tids(pid):
    snap = k32.CreateToolhelp32Snapshot(0x00000004, 0)
    if not snap or snap == ctypes.c_void_p(-1).value:
        return None
    tids = []
    try:
        te = THREADENTRY32W()
        te.dwSize = ctypes.sizeof(THREADENTRY32W)
        ok = k32.Thread32First(snap, ctypes.byref(te))
        while ok:
            if int(te.th32OwnerProcessID) == int(pid):
                tids.append(int(te.th32ThreadID))
            ok = k32.Thread32Next(snap, ctypes.byref(te))
    finally:
        k32.CloseHandle(snap)
    return tids


def ntquery_thread_rows(pid):
    """NtQuerySystemInformation(SystemProcessInformation) 解析 pid 的线程表。
    带校验：解析 tid 集合须与 Toolhelp 快照一致（±1 容忍瞬时创建/退出）。
    返回 ({tid_str: {kernel_ms,user_ms,ctx}}, valid, note) 或 (None, False, note)。"""
    note = ""
    size = 1 << 20
    data = None
    for _ in range(4):
        buf = ctypes.create_string_buffer(size)
        ret_len = ctypes.c_ulong(0)
        st = nt.NtQuerySystemInformation(SystemProcessInformation, buf, size,
                                         ctypes.byref(ret_len))
        if st == 0:
            data = buf.raw[:ret_len.value] if ret_len.value else buf.raw
            break
        if (st & 0xFFFFFFFF) == STATUS_INFO_LENGTH_MISMATCH:
            size = max(size * 2, ret_len.value or size * 2)
            continue
        return None, False, "ntquery_status=0x%08x" % (st & 0xFFFFFFFF)
    if data is None:
        return None, False, "ntquery_buffer_grow_failed"
    off = 0
    rows = None
    try:
        while off + 8 <= len(data):
            next_off, n_threads = struct.unpack_from("<II", data, off)
            # NextEntryOffset = 相对当前条目的字节偏移（0=末条）；>0 时须 ≥8 且不出界
            if next_off and (next_off < 8 or off + next_off > len(data)):
                return None, False, "bad_next_offset_chain off=%d next=%d" % (off, next_off)
            upid = struct.unpack_from("<Q", data, off + PROC_UNIQ_PID_OFF)[0]
            if upid == pid:
                rows = {}
                for i in range(n_threads):
                    toff = off + PROC_THREADS_OFF + i * THREAD_STRIDE
                    if toff + THREAD_STRIDE > len(data):
                        note = "truncated_thread_array"
                        break
                    ktime, utime = struct.unpack_from("<qq", data, toff)
                    thid = struct.unpack_from("<Q", data, toff + THREAD_TID_OFF)[0]
                    ctx = struct.unpack_from("<I", data, toff + THREAD_CTX_OFF)[0]
                    rows[str(int(thid))] = {"kernel_ms": ktime / 1e4,
                                            "user_ms": utime / 1e4,
                                            "ctx": int(ctx)}
                break
            if next_off == 0:
                break
            off += next_off
    except Exception as e:
        return None, False, "parse_error:%r" % e
    if rows is None:
        return None, False, "pid_not_found_in_system_list"
    snap = snapshot_tids(pid)
    if snap is None:
        return rows, False, "snapshot_unavailable(rows_unvalidated)"
    parsed = {int(t) for t in rows.keys()}
    sset = set(snap)
    if parsed == sset:
        return rows, True, "tids_match"
    if len(parsed - sset) == 0 and len(sset - parsed) <= 1:
        return rows, True, "tids_match_snapshot_extra_1"
    if len(sset - parsed) == 0 and len(parsed - sset) <= 1:
        return rows, True, "tids_match_parsed_extra_1"
    return None, False, "tid_validation_mismatch parsed=%s snap=%s" % (
        sorted(parsed), sorted(sset))


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

    # 复用探针模块中已验证的 ThreadTable（模块级仅 Win32 绑定，import 安全）
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from combat_probe import ThreadTable
    ttable = ThreadTable(a.pid)

    try:
        k32.SetPriorityClass(k32.GetCurrentProcess(), 0x00004000)
    except Exception:
        pass

    hproc = k32.OpenProcess(0x0400, False, a.pid)  # QUERY_INFORMATION 只读
    nd_f = ndjson_path.open("w", encoding="utf-8", newline="\n")
    n_lines = 0
    n_thread_ok = 0
    n_thread_fail = 0
    last_thread_note = None

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
                "watcher_pid": os.getpid(), "watching_pid": a.pid,
                "thread_rows": None, "thread_rows_valid": False})
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
            # ---- 线程表（NtQuery 只读辅助通道，校验失败置 None） ----
            thread_rows, tvalid, tnote = ntquery_thread_rows(a.pid)
            # ---- 全线程扫（GetThreadTimes+CycleTime 求和；本机 Toolhelp 全系统
            #      线程迭代 ~5ms，放本进程 1Hz，保护采样器 6ms 节奏） ----
            sw = ttable.sweep()
            merged = {}
            if sw:
                for tid_s, r in sw["threads"].items():
                    merged[tid_s] = {"kernel_ms": r["kernel_ms"],
                                     "user_ms": r["user_ms"],
                                     "cpu_ms": r["cpu_ms"],
                                     "cycles": r["cycles"],
                                     "ctx": None}
                if thread_rows:
                    for tid_s, r in thread_rows.items():
                        if tid_s in merged:
                            merged[tid_s]["ctx"] = r.get("ctx")
                        else:
                            merged[tid_s] = {"kernel_ms": r.get("kernel_ms"),
                                             "user_ms": r.get("user_ms"),
                                             "cpu_ms": (round((r.get("kernel_ms") or 0)
                                                              + (r.get("user_ms") or 0), 6)),
                                             "cycles": None,
                                             "ctx": r.get("ctx")}
            sweep_valid = bool(sw)
            if tvalid:
                n_thread_ok += 1
            else:
                n_thread_fail += 1
                last_thread_note = tnote
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
                       "continue_hits": cont, "last_input_dwtime": li,
                       "thread_rows_valid": tvalid,
                       "thread_rows": thread_rows,
                       "sweep_valid": sweep_valid,
                       "sweep_n_threads": (sw or {}).get("n_threads"),
                       "sweep_sum_cpu_ms": (sw or {}).get("sum_cpu_ms")}
                wrec(rec)
                if sw:
                    wrec({"kind": "thread_sweep", "t_mono_ns": now,
                          "t_utc_iso": utc_iso(),
                          **sw, "nt_rows": thread_rows,
                          "nt_valid": tvalid, "nt_note": tnote})
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
                        "n_scans": n_lines,
                        "thread_rows": merged if (sweep_valid or tvalid) else None,
                        "thread_rows_valid": bool(sweep_valid or tvalid),
                        "thread_note": tnote,
                        "sum_all_threads_cpu_ms": (sw or {}).get("sum_cpu_ms"),
                        "n_threads": (sw or {}).get("n_threads"),
                        "threads_sweep_t_mono_ns": (sw or {}).get("t_mono_ns")})
            except Exception as e:
                wrec({"kind": "event", "t_mono_ns": time.perf_counter_ns(),
                      "t_utc_iso": utc_iso(), "event": "watcher_scan_error",
                      "detail": repr(e)})
            time.sleep(a.interval_ms / 1000.0)
    finally:
        try:
            wrec({"kind": "ui_watch_end", "t_mono_ns": time.perf_counter_ns(),
                  "t_utc_iso": utc_iso(), "reason": reason or "finally",
                  "n_lines": n_lines,
                  "thread_ok": n_thread_ok, "thread_fail": n_thread_fail,
                  "last_thread_note": last_thread_note})
        except Exception:
            pass
        try:
            wstate({"t_mono_ns": time.perf_counter_ns(), "t_utc_iso": utc_iso(),
                    "alive": None, "fg": None, "continue_hits": [],
                    "natural_end": natural_end,
                    "natural_end_t_mono_ns": natural_end_t,
                    "natural_end_buttons": natural_end_buttons,
                    "watcher_pid": os.getpid(), "watching_pid": a.pid,
                    "thread_rows": None, "thread_rows_valid": False,
                    "stopped": True, "reason": reason or "finally"})
        except Exception:
            pass
        try:
            (outdir / "watcher_done.txt").write_text(
                "reason=%s\nlines=%d\nended_utc=%s\nthread_ok=%d\n"
                "thread_fail=%d\nlast_thread_note=%s\n" %
                (reason or "finally", n_lines, utc_iso(),
                 n_thread_ok, n_thread_fail, last_thread_note),
                encoding="utf-8")
        except Exception:
            pass
        try:
            nd_f.close()
        except Exception:
            pass
        try:
            ttable.close_all()
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
