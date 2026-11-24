# -*- coding: utf-8 -*-
# _w2v_probe2.py — 独占句柄（share-mode=0）双时点拦截 + 进程自退出即句柄释放（R6）
# 子进程为本探针自写 python 脚本（非游戏进程、非 taskkill，自行退出）。
import ctypes
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / r"lead\w2_samecause_20261109"
CASE = WD / "_w2v_case2"
OUT2 = WD / "_w2v_out2"
CHILD = WD / "_w2v_child.py"
CAND = ROOT / r"lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py"

for d in (CASE, OUT2):
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
d = CASE / "hndt"
d.mkdir()
f = d / "except.txt"
f.write_bytes(b"held\n")

CHILD.write_text(
    "import os, sys, time, ctypes\n"
    "GENERIC_READ  = 0x80000000\n"
    "GENERIC_WRITE = 0x40000000\n"
    "OPEN_EXISTING = 3\n"
    "h = ctypes.windll.kernel32.CreateFileW(sys.argv[1],\n"
    "      GENERIC_READ | GENERIC_WRITE, 0, None, OPEN_EXISTING, 0, None)\n"
    "assert h not in (-1, 0xFFFFFFFFFFFFFFFF), ctypes.GetLastError()\n"
    "open(sys.argv[2], 'w').write('held')\n"
    "for _ in range(300):\n"
    "    if os.path.exists(sys.argv[3]):\n"
    "        break\n"
    "    time.sleep(0.1)\n"
    "ctypes.windll.kernel32.CloseHandle(h)\n"
    "open(sys.argv[2] + '.done', 'w').write('closed')\n",
    encoding="utf-8")

spec = importlib.util.spec_from_file_location("qc151_candidate_w2v2", str(CAND))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

marker = CASE / "held.marker"
done = CASE / "released.marker"
if done.exists():
    done.unlink()
proc = subprocess.Popen([sys.executable, "-I", "-X", "utf8", str(CHILD),
                         str(f), str(marker), str(done)])
for _ in range(100):
    if marker.exists():
        break
    time_slept = True
    import time
    time.sleep(0.1)
print("child holds exclusive handle:", marker.exists())

ex = f.exists()
try:
    f.stat()
    statres = "ok"
except Exception as exc:
    statres = "%s w%s" % (type(exc).__name__, getattr(exc, "winerror", None))
try:
    with open(f, "rb") as fh:
        fh.read()
    openres = "readable"
except Exception as exc:
    openres = "%s errno=%s winerror=%s" % (type(exc).__name__,
                                           getattr(exc, "errno", None),
                                           getattr(exc, "winerror", None))
print("HELD: exists=%s stat=%s open=%s" % (ex, statres, openres))
snap = mod.make_pre_freshness_snapshot(f)
print("HELD make_pre(T0) ->", snap["state"], (snap["error"] or "")[:80])
rec = mod.Recorder()
raised = None
try:
    mod.copy_post_except_evidence(rec, d, OUT2, pre_freshness_snapshot=snap)
except Exception as exc:
    raised = exc
FG = mod.FRESHNESS_GROUP
FKP = mod.FRESHNESS_KEY_PREFIX
v = [r["value"] for r in rec.rows
     if r["group"] == FG and r["key"] == FKP + "verdict"]
p = [r["value"] for r in rec.rows
     if r["group"] == FG and r["key"] == "pre_snapshot_state"]
print("HELD copy_post(T1) raised:", type(raised).__name__ if raised else None,
      "verdict=", v, "pre_snapshot_state=", p)

# 释放：子进程自行退出（R6：进程终止 ⇒ 内核关闭句柄）
done.write_text("go")
proc.wait(timeout=40)
try:
    with open(f, "rb") as fh:
        fh.read()
    openres2 = "readable"
except Exception as exc:
    openres2 = "%s w%s" % (type(exc).__name__, getattr(exc, "winerror", None))
print("AFTER CHILD SELF-EXIT: open=", openres2)

pass_all = (ex is True and statres == "ok" and openres != "readable"
            and snap["state"] == "error" and v == ["post_read_error"]
            and p == ["error"] and openres2 == "readable")
print("W2V_PROBE2", "PASS" if pass_all else "FAIL")
