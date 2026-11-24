#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W136b: read-only EIP sampler for gamemd.exe (poor-man's profiler).

Purpose: without injecting anything, find out WHICH code the process is executing.
Each sample suspends every thread for the minimum time needed to read its context
and immediately resumes it.  Nothing is written to the target process.

This answers questions the static work cannot:
  - Is the `Conquer.CPP` game loop `0x0048CCC0` actually running?
  - Is the per-frame update `0x0055D360` actually executing?
  - Which functions dominate wall time (a histogram, not a guess)?

Grading: a histogram of samples is EVIDENCE OF WHERE THE CPU IS, not a cycle count.
It cannot see time spent blocked in a syscall, and a function that is fast but
called often can look the same as one that is slow and called rarely.

Usage:
    python -X utf8 w136b_eipsample.py --launch --secs 30 --out eip.tsv
    python -X utf8 w136b_eipsample.py --pid 1234 --secs 30
"""
import argparse
import bisect
import collections
import ctypes
import io
import os
import struct
import subprocess
import sys
import time
from ctypes import wintypes as wt

SANDBOX = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out\sandbox_game"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

THREAD_SUSPEND_RESUME = 0x0002
THREAD_GET_CONTEXT = 0x0008
THREAD_QUERY_INFORMATION = 0x0040
PROCESS_VM_READ = 0x0010
CONTEXT_i386 = 0x00010000
CONTEXT_CONTROL = CONTEXT_i386 | 0x00000001

# Areas of interest (from ledger §881/§883)
WATCH = {
    0x0048CCC0: "Conquer.CPP game loop",
    0x0055D360: "per-frame update",
    0x00647260: "event pump",
    0x0064C380: "event ring consumer",
    0x0067D300: "7-array coordinator",
    0x006DD8B0: "TAction executor",
    0x007265C0: "TAction queue driver",
    0x0048C8B0: "Conquer.CPP helper",
    0x0052D9A0: "Init.CPP (frame tail)",
    0x006BD8B0: "",  # placeholder, unused
}

THREADENTRY32_SIZE = 28


class THREADENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                ("th32ThreadID", wt.DWORD), ("th32OwnerProcessID", wt.DWORD),
                ("tpBasePri", ctypes.c_long), ("tpDeltaPri", ctypes.c_long),
                ("dwFlags", wt.DWORD)]


class CONTEXT(ctypes.Structure):
    _fields_ = [("ContextFlags", wt.DWORD)] + [("pad", wt.DWORD)] * 20


k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
k32.OpenThread.restype = wt.HANDLE
k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
# MUST use the WOW64 variant: this Python is 64-bit, the target is 32-bit.
k32.Wow64GetThreadContext.argtypes = [wt.HANDLE, ctypes.c_void_p]
k32.Wow64GetThreadContext.restype = wt.BOOL


def load_atlas():
    fns = []
    for ln in io.open(ATLAS, encoding="utf-8").read().splitlines()[1:]:
        p = ln.split("\t")
        if len(p) >= 2:
            try:
                fns.append((int(p[0], 16), int(p[1])))   # size column is DECIMAL
            except ValueError:
                pass
    fns.sort()
    return fns, [a for a, _ in fns]


def owner(va, fns, starts):
    i = bisect.bisect_right(starts, va) - 1
    if i < 0:
        return None
    a, s = fns[i]
    return a if s and a <= va < a + s else None


def thread_ids(pid):
    snap = k32.CreateToolhelp32Snapshot(0x00000004, 0)   # TH32CS_SNAPTHREAD
    if snap == wt.HANDLE(-1).value:
        return []
    out = []
    te = THREADENTRY32()
    te.dwSize = THREADENTRY32_SIZE
    ok = k32.Thread32First(snap, ctypes.byref(te))
    while ok:
        if te.th32OwnerProcessID == pid:
            out.append(te.th32ThreadID)
        ok = k32.Thread32Next(snap, ctypes.byref(te))
    k32.CloseHandle(snap)
    return out


def sample_eip(pid, tids):
    """suspend -> GetThreadContext -> resume, for every thread; return list of (tid, eip)"""
    res = []
    for tid in tids:
        h = k32.OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT |
                           THREAD_QUERY_INFORMATION, False, tid)
        if not h:
            continue
        try:
            if k32.SuspendThread(h) == 0xFFFFFFFF:
                continue
            try:
                buf = ctypes.create_string_buffer(0x400)
                struct.pack_into("<I", buf, 0, 0x00010001)   # CONTEXT_i386|CONTEXT_CONTROL
                if k32.Wow64GetThreadContext(h, ctypes.byref(buf)):
                    eip = struct.unpack_from("<I", buf.raw, 0xB8)[0]
                    res.append((tid, eip))
            finally:
                k32.ResumeThread(h)
        finally:
            k32.CloseHandle(h)
    return res


def game_pids():
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-Process gamemd -ErrorAction SilentlyContinue | "
                        "Select-Object -ExpandProperty Id"],
                       capture_output=True, text=True, timeout=60)
    return [int(x) for x in (r.stdout or "").split() if x.strip().isdigit()]


def launch(extra=""):
    ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
          "-Arguments @{CommandLine='cmd.exe /c cd /d \"%s\" && start \"\" \"gamemd.exe\" %s'}; "
          "Write-Output ('{0}|{1}' -f $r.ProcessId, $r.ReturnValue)" % (SANDBOX, extra))
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   capture_output=True, text=True, timeout=120)
    t0 = time.time()
    while time.time() - t0 < 120:
        p = game_pids()
        if p:
            return p[0]
        time.sleep(1.0)
    raise RuntimeError("gamemd did not start")


def kill_all():
    for p in game_pids():
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p)],
                       capture_output=True, text=True, timeout=60)
    time.sleep(2.0)
    return game_pids()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int)
    ap.add_argument("--launch", action="store_true")
    ap.add_argument("--game-args", default="")
    ap.add_argument("--secs", type=float, default=30.0)
    ap.add_argument("--interval", type=float, default=0.01)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if not a.pid and not a.launch:
        ap.error("give --pid or --launch")

    launched = False
    if a.launch:
        pre = game_pids()
        if pre:
            kill_all()
        pid = launch(a.game_args)
        launched = True
        time.sleep(6.0)     # let it get to the menu
    else:
        pid = a.pid
    print("sampling pid=%d  (suspend/GetThreadContext/resume only; no writes)" % pid)

    fns, starts = load_atlas()
    hist = collections.Counter()
    per_thread = collections.Counter()
    watches = collections.Counter()
    total = 0
    t0 = time.time()
    rows = []

    while time.time() - t0 < a.secs:
        pids = game_pids()
        if pid not in pids:
            print("PROCESS_GONE")
            break
        tids = thread_ids(pid)
        for tid, eip in sample_eip(pid, tids):
            total += 1
            per_thread[tid] += 1
            fn = owner(eip, fns, starts)
            hist[fn if fn else eip] += 1
            for w, lbl in WATCH.items():
                if fn == w:
                    watches[w] += 1
            rows.append((time.time() - t0, tid, eip, fn))
        time.sleep(a.interval)

    print("\n=== %d samples in %.1fs across %d threads ===" % (total, time.time() - t0, len(per_thread)))
    print("threads by sample count:", per_thread.most_common(6))

    print("\n=== top 20 functions by sample count ===")
    print("%-12s %-7s %-8s %s" % ("entry", "size", "samples", "share"))
    for fn, n in hist.most_common(20):
        if isinstance(fn, int):
            s = dict(fns).get(fn, "?")
            print("%-12s %-7s %-8d %.1f%%" % ("0x%06X" % fn, s, n, 100.0 * n / max(total, 1)))
        else:
            print("%-12s %-7s %-8d %.1f%%" % ("0x%06X" % n, "-", 1, 100.0 / max(total, 1)))

    print("\n=== watched areas ===")
    for w, lbl in WATCH.items():
        if not lbl:
            continue
        n = watches.get(w, 0)
        print("  %-12s %-24s %d samples%s" % ("0x%06X" % w, lbl, n,
                                              "" if n == 0 else "   <<< SEEN"))

    if a.out:
        with io.open(a.out, "w", encoding="utf-8") as f:
            f.write("t\ttid\teip\tfn\n")
            for t, tid, eip, fn in rows:
                f.write("%.4f\t%d\t%08X\t%s\n" % (t, tid, eip,
                                                  ("%08X" % fn) if fn else ""))
        print("\nwrote %s" % a.out)

    if launched:
        print("residual: %r" % kill_all())
    return 0


if __name__ == "__main__":
    sys.exit(main())
