#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）探针 p05（v2 限定搜索面，去掉全盘递归 glob）：
   冻结/候选件 sha 复验 + 本批产物 mtime 时序 + preflight/selftest 计数 + git 索引旁证。"""
import json, io, sys, os, hashlib, glob, subprocess, re
from datetime import datetime, timezone, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
CST = timezone(timedelta(hours=8))
CB = "lead/qc161_u0400_trip/c2ab_x"

def sh256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def ts(t):
    return datetime.fromtimestamp(t, CST).strftime("%m-%d %H:%M:%S.%f")[:-3]

print("== 驱动/冻结件 sha 前缀复验（限定 lead/qc161_u0400_trip 一层）==")
pats = ["lead/qc161_u0400_trip/_drive_c2_x_*.py", "lead/qc161_u0400_trip/*/*/​_drive_c2_x_*.py".replace("​", ""),
        "lead/qc161_u0400_trip/*/*/_drive_c2_x_*.py"]
seen = set()
for pat in pats:
    for f in glob.glob(pat):
        if f in seen or not os.path.isfile(f):
            continue
        seen.add(f)
        print(f"  {f}  sha={sh256(f)[:8]}  bytes={os.path.getsize(f)}  mtime={ts(os.path.getmtime(f))}")

print("\n== 本批两趟产物 mtime 时序（与 _rec/timeline 记录互证）==")
for tag, d in [("b2-h15.3", "20261031T083340_9001_P3e_E12_T1"), ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1")]:
    base = f"{CB}/{d}"
    r = json.load(open(f"{base}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{base}/timeline.json", encoding="utf-8"))["close_rows"]
    print(f"  {tag}: rows[0].t={rows[0]['t']:.3f} ({ts(rows[0]['t'])})  rows[-1].t={rows[-1]['t']:.3f} ({ts(rows[-1]['t'])})")
    print(f"          wallclock_ms_at_start={r['wallclock_ms_at_start']} ({ts(r['wallclock_ms_at_start']/1000)})  "
          f"tag 目录名时刻={d[:14]}")
    for f in sorted(glob.glob(base + "/*.json") + glob.glob(base + "/*.log") + glob.glob(base + "/shots/*")):
        mt = os.path.getmtime(f)
        inside = rows[0]["t"] - 60 <= mt <= rows[-1]["t"] + 120
        print(f"      {f.replace(base + os.sep, ''):<32} bytes={os.path.getsize(f):<7} mtime={mt:.0f} ({ts(mt)})  时序合理={inside}")

print("\n== 批前件时序与计数 ==")
B = "lead/codex_round_20261030/LEADER_battle/"
for f in (B + "preflight_batch2_20261031.txt", B + "selftest_batch2_20261031.txt", B + "GOAL2_BATCH2_DELTA_AXIS_20261031.md"):
    mt = os.path.getmtime(f)
    print(f"  {os.path.basename(f)}: bytes={os.path.getsize(f)} mtime={mt:.0f} ({ts(mt)})")
pt = open(B + "preflight_batch2_20261031.txt", encoding="utf-8", errors="replace").read()
print("  preflight 全文：")
for l in pt.splitlines():
    print("      " + l)
m = re.search(r"UPTIME\(GetTickCount64\)=(\d+) ms", pt)
up = int(m.group(1)); mt = os.path.getmtime(B + "preflight_batch2_20261031.txt")
print(f"    → preflight 反推 BOOT 墙钟 = {mt:.3f} − {up/1000:.3f} = {mt - up/1000:.3f} ({ts(mt - up/1000)})")
st = open(B + "selftest_batch2_20261031.txt", encoding="utf-8", errors="replace").read()
print(f"  selftest: [RED]={st.count('[RED]')} [OK]={st.count('[OK]')} 行数={len(st.splitlines())}")
for l in st.splitlines():
    if "SELFTEST" in l or "红=" in l or "件 sha" in l or "sha256" in l:
        print("      " + l.strip()[:160])

print("\n== git 索引旁证（只读，限定路径）==")
for tag, d in [("b2-h15.3", "20261031T083340_9001_P3e_E12_T1"), ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1")]:
    p = f"lead/qc161_u0400_trip/c2ab_x/{d}/_rec.json"
    out = subprocess.run(["git", "ls-files", "-s", "--", p], capture_output=True, text=True, timeout=30)
    st2 = subprocess.run(["git", "status", "--porcelain", "--", f"lead/qc161_u0400_trip/c2ab_x/{d}"],
                         capture_output=True, text=True, timeout=30)
    print(f"  {d}: ls-files={'(untracked)' if not out.stdout.strip() else out.stdout.strip()}  status={st2.stdout.strip() or '(clean)'}")
