#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Probe: can we read a 32-bit (WOW64) thread's EIP from 64-bit Python?

We must use Wow64GetThreadContext on a WOW64 thread. This probe:
  1. checks whether kernel32 exports Wow64GetThreadContext,
  2. launches gamemd.exe, samples every thread BOTH ways,
  3. reports how many EIPs land inside gamemd's .text (0x401000..0x7E038D).
The method whose EIPs land in .text is the correct one. Read-only: no writes to
the target; suspend/resume only.
"""
import ctypes
import struct
import subprocess
import sys
import time
from ctypes import wintypes as wt

SANDBOX = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out\sandbox_game"
TEXT_LO, TEXT_HI = 0x00401000, 0x007E038D

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenThread.restype = wt.HANDLE
k32.CreateToolhelp32Snapshot.restype = wt.HANDLE

print("Wow64GetThreadContext present:", hasattr(k32, "Wow64GetThreadContext"))
if hasattr(k32, "Wow64GetThreadContext"):
    k32.Wow64GetThreadContext.argtypes = [wt.HANDLE, ctypes.c_void_p]
    k32.Wow64GetThreadContext.restype = wt.BOOL
k32.GetThreadContext.argtypes = [wt.HANDLE, ctypes.c_void_p]
k32.GetThreadContext.restype = wt.BOOL

THREADENTRY32_SIZE = 28


class THREADENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                ("th32ThreadID", wt.DWORD), ("th32OwnerProcessID", wt.DWORD),
                ("tpBasePri", ctypes.c_long), ("tpDeltaPri", ctypes.c_long),
                ("dwFlags", wt.DWORD)]


def game_pids():
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-Process gamemd -ErrorAction SilentlyContinue | "
                        "Select-Object -ExpandProperty Id"],
                       capture_output=True, text=True, timeout=60)
    return [int(x) for x in (r.stdout or "").split() if x.strip().isdigit()]


def kill_all():
    for p in game_pids():
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p)],
                       capture_output=True, text=True, timeout=60)
    time.sleep(2.0)


def launch():
    ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
          "-Arguments @{CommandLine='cmd.exe /c cd /d \"%s\" && start \"\" \"gamemd.exe\"'}; "
          "Write-Output ('{0}|{1}' -f $r.ProcessId, $r.ReturnValue)" % SANDBOX)
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   capture_output=True, text=True, timeout=120)
    t0 = time.time()
    while time.time() - t0 < 120:
        p = game_pids()
        if p:
            return p[0]
        time.sleep(1.0)
    raise RuntimeError("no start")


def thread_ids(pid):
    snap = k32.CreateToolhelp32Snapshot(0x00000004, 0)
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


def read_eips(pid, use_wow64, buf_size=0x400):
    """return list of (tid, eip, ok) for all threads"""
    out = []
    for tid in thread_ids(pid):
        h = k32.OpenThread(0x0002 | 0x0008 | 0x0040, False, tid)  # SUSPEND|GETCONTEXT|QUERY
        if not h:
            continue
        try:
            if k32.SuspendThread(h) == 0xFFFFFFFF:
                continue
            try:
                buf = ctypes.create_string_buffer(buf_size)
                # ContextFlags at offset 0: CONTEXT_i386|CONTEXT_CONTROL = 0x00010001
                struct.pack_into("<I", buf, 0, 0x00010001)
                if use_wow64:
                    ok = k32.Wow64GetThreadContext(h, ctypes.byref(buf))
                else:
                    ok = k32.GetThreadContext(h, ctypes.byref(buf))
                eip = struct.unpack_from("<I", buf.raw, 0xB8)[0]
                out.append((tid, eip, bool(ok)))
            finally:
                k32.ResumeThread(h)
        finally:
            k32.CloseHandle(h)
    return out


def main():
    kill_all()
    pid = launch()
    print("pid=%d, waiting 8s for startup" % pid)
    time.sleep(8.0)

    for use_wow64 in (False, True):
        label = "Wow64GetThreadContext" if use_wow64 else "GetThreadContext"
        if use_wow64 and not hasattr(k32, "Wow64GetThreadContext"):
            print("\n%s: NOT AVAILABLE" % label)
            continue
        tot = inbox = okc = 0
        sample = []
        for _ in range(20):
            for tid, eip, ok in read_eips(pid, use_wow64):
                tot += 1
                okc += 1 if ok else 0
                if TEXT_LO <= eip < TEXT_HI:
                    inbox += 1
                if len(sample) < 8:
                    sample.append((tid, eip, ok))
            time.sleep(0.05)
        print("\n=== %s ===" % label)
        print("  samples=%d  call-ok=%d  EIP inside .text=%d (%.0f%%)"
              % (tot, okc, inbox, 100.0 * inbox / max(tot, 1)))
        print("  first samples: " + ", ".join("tid%d:0x%X(%s)" % (t, e, o) for t, e, o in sample))

    kill_all()
    print("\nresidual after kill: %r" % game_pids())
    return 0


if __name__ == "__main__":
    sys.exit(main())
