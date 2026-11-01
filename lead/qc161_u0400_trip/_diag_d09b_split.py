#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""d09b 首跑失效根因分离（三步，一趟到底）：

Q1  A 路直启 gamemd（无调试器）能出窗口吗？        → 分离「调试器必需」vs「loader 路坏」
Q2  loader+守卫关 无调试器能出窗口吗？             →（d09b 已答：不能，wins=0）
Q3  在 Q2 的卡死进程中途挂调试器+泵事件，窗口出现吗？ → 若是，ab24 的「有窗」全靠 attach 改变了时序
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _probe_d09b_hang as P
import subprocess, os

P.MOD = P.load_their()
mod = P.MOD
BASE = P.MYCARD / ("diag2_%s" % time.strftime("%H%M%S"))
BASE.mkdir(parents=True, exist_ok=True)


def wait_window(pid, carrier, secs, dbg=None):
    t0 = time.time()
    while time.time() - t0 < secs:
        time.sleep(2)
        wins = P.enum_windows_for(pid)
        gw = [w for w in wins if w["class"] == "Yuri's Revenge"]
        if gw:
            return round(time.time() - t0, 1), gw[0]
        if dbg is not None and time.time() - t0 > dbg["attach_at"] and not dbg["done"]:
            dbg["done"] = mod.k32.DebugActiveProcess(pid)
            print("    [t=%.1f] DebugActiveProcess => %s" % (time.time() - t0, dbg["done"]))
            # 泵 3s 事件
            import ctypes
            DE = mod.DEBUG_EVENT()
            te = time.time()
            while time.time() - te < 3.0:
                if mod.k32.WaitForDebugEvent(ctypes.byref(DE), 100):
                    mod.k32.ContinueDebugEvent(DE.dwProcessId, DE.dwThreadId, 0x00010002)
            dbg["pump_end"] = time.time()
        h = P.k32.OpenProcess(0x0400, False, pid)
        if h:
            res = P.k32.WaitForSingleObject(h, 0)
            P.k32.CloseHandle(h)
            if res == 0:
                return "DEAD", None
    return None, None


def step(tag, use_loader, guard_enable, pump_at=None, secs=60):
    out = BASE / tag
    carrier = out / "ct" / ("c" + "0" * 10)
    out.mkdir(parents=True, exist_ok=True)
    extra = ([P.GUARD_DIR / "rc4_loader.exe", P.GUARD_DIR / "ra2rc4guard.dll"]
             if use_loader else None)
    P.build_carrier(carrier, extra, guard_enable)
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if use_loader:
        cmd = [str(carrier / "rc4_loader.exe"), "ra2rc4guard.dll"]
    else:
        cmd = [str(carrier / "gamemd.exe")]
    proc = subprocess.Popen(cmd, cwd=str(carrier), env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pid = None
    for _ in range(150):
        time.sleep(0.1)
        for p, nm in mod.list_procs().items():
            if nm.lower() == "gamemd.exe":
                img = mod.query_image(p)
                if img and mod.under_carrier(img, carrier):
                    pid = p
                    break
        if pid:
            break
    print("[%s] gamemd pid=%s (t+%.1fs)" % (tag, pid, time.time() - proc.creation_time if False else 0))
    if pid is None:
        print("[%s] ABORT no gamemd" % tag)
        return None
    t_win, gw = wait_window(pid, carrier, secs,
                            ({"attach_at": pump_at, "done": False} if pump_at else None))
    print("[%s] window: %s %s" % (tag, t_win, gw["title"][:40] if gw else ""))
    for p, nm in list(mod.list_procs().items()):
        if nm.lower() in ("gamemd.exe", "rc4_loader.exe"):
            img = mod.query_image(p)
            if img and mod.under_carrier(img, carrier):
                try:
                    mod.k32.DebugActiveProcessStop(p)
                except Exception:
                    pass
                hh = P.k32.OpenProcess(0x0001 | 0x100000, False, p)
                if hh:
                    P.k32.TerminateProcess(hh, 1)
                    P.k32.CloseHandle(hh)
    try:
        proc.wait(timeout=5)
    except Exception:
        pass
    import shutil
    shutil.rmtree(carrier.parent, ignore_errors=True)
    return t_win


s1 = step("Q1_A_direct_noDbg", False, None, secs=45)
s2 = step("Q2_loader_off_noDbg", True, 0, secs=45)
s3 = step("Q3_loader_off_pump@20", True, 0, pump_at=20.0, secs=45)
print("\nSUMMARY  Q1=%s  Q2=%s  Q3=%s" % (s1, s2, s3))
