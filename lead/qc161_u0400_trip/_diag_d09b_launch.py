#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""d09b 首跑失效形态的现场诊断：建载体→放 loader→每 2 s 打窗口/日志/工作集，120 s。

只诊断不判定：回答「gamemd 活着但窗口/日志为什么迟迟不出现」。
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import _probe_d09b_hang as P
import subprocess, os, json

MYCARD = P.MYCARD / "diag"
out = MYCARD / time.strftime("%Y%m%dT%H%M%S_diag")
carrier = out / "ct" / ("c" + "0" * 10)
out.mkdir(parents=True, exist_ok=True)
extra = [P.GUARD_DIR / "rc4_loader.exe", P.GUARD_DIR / "ra2rc4guard.dll"]
n = P.build_carrier(carrier, extra, 1)
print("carrier files:", n, "len:", len(str(carrier)))

env = dict(os.environ); env["PYTHONDONTWRITEBYTECODE"] = "1"
proc = subprocess.Popen([str(carrier / "rc4_loader.exe"), "ra2rc4guard.dll"],
                        cwd=str(carrier), env=env,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("loader pid:", proc.pid)

P.MOD = P.load_their()
pid = None
t0 = time.time()
while time.time() - t0 < 60:
    time.sleep(0.5)
    for p, nm in P.MOD.list_procs().items():
        if nm.lower() == "gamemd.exe":
            img = P.MOD.query_image(p)
            if img and P.MOD.under_carrier(img, carrier):
                pid = p
                break
    if pid:
        break
print("gamemd pid:", pid, "at t=%.1f" % (time.time() - t0))
if not pid:
    print("!! gamemd 根本没出现")
    proc.terminate()
    sys.exit(1)

h = P.k32.OpenProcess(0x0400 | 0x0010 | 0x100000, False, pid)
for k in range(60):
    time.sleep(2)
    res = P.k32.WaitForSingleObject(h, 0)
    alive = res == 258
    wins = P.enum_windows_for(pid) if alive else []
    logf = carrier / "ra2render.log"
    guard = []
    if logf.exists():
        guard = [l for l in logf.read_text(encoding="utf-8", errors="replace").splitlines()
                 if "[ra2rc4guard]" in l]
    frame = P.rpm_u32(h, P.G_FRAME) if alive else None
    t = time.time() - t0
    print("t=%5.1f alive=%-5s ws=%-8s frame=%-7s wins=%s guard_lines=%d"
          % (t, alive, P.working_set_kb(h) if alive else None, frame,
             [(w["class"][:12], w["title"][:20], w["visible"]) for w in wins],
             len(guard)))
    if not alive:
        ex = P.wt.DWORD(0)
        P.k32.GetExitCodeProcess(h, P.ctypes.byref(ex))
        print("!! 进程于 t=%.1f 退出 code=0x%X" % (t, ex.value))
        break
    if any(w["class"] == "Yuri's Revenge" and w["visible"] for w in wins):
        print(">> 游戏窗出现 t=%.1f" % t)
        break
P.k32.CloseHandle(h)
for p, nm in list(P.MOD.list_procs().items()):
    if nm.lower() in ("gamemd.exe", "rc4_loader.exe"):
        img = P.MOD.query_image(p)
        if img and P.MOD.under_carrier(img, carrier):
            hh = P.k32.OpenProcess(0x0001 | 0x100000, False, p)
            if hh:
                P.k32.TerminateProcess(hh, 1); P.k32.CloseHandle(hh)
try:
    proc.wait(timeout=5)
except Exception:
    pass
import shutil
shutil.rmtree(carrier.parent, ignore_errors=True)
print("diag done; leftover:", P.MOD.game_procs() or "0")
