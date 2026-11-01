#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 对账探针 p09：§487「强杀 0/自然走完」vs TERM 行、抓帧件同一性、路径长度「100≤130」口径、
   C-2 预登记在卡片/台账中的落地、__pycache__ 留置件数。只读。"""
import json, io, sys, os, hashlib, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
R = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

print("=" * 78)
print("(1) ha/hb 收尾形态（§487「强杀 0（两趟自然走完 rc=0）」）")
print("=" * 78)
for d in ("l3_20261031ha", "l3_20261031hb", "l3_20261023q", "l3_20261023r"):
    f = json.load(open(f"{R}/{d}/qc151_fields.json", encoding="utf-8"))
    def gv(g, k):
        v = [e["value"] for e in f if e.get("group") == g and e.get("key") == k]
        return v[-1] if v else None
    lr = json.load(open(f"{R}/{d}/_launch_result.json", encoding="utf-8"))
    print(f"  {d}: harness_rc={lr['rc']} duration={lr['duration_s']} "
          f"CLOSE.close_mode={gv('CLOSE','close_mode')!r} close_posted={gv('CLOSE','close_posted')} "
          f"TERM.term_requested={gv('TERM','term_requested')} terminate_sent={gv('TERM','terminate_sent')} "
          f"wait_returncode={gv('TERM','wait_returncode')} termination_verdict={gv('TERM','termination_verdict')!r}")
print("  判读依据：harness8:1423 `proc.terminate()`（Windows ⇒ TerminateProcess）；"
      "1419-1421 注释「缺省 terminate ⇒ 控制流与 harness5 一致」；"
      "rc=0 是 harness 脚本退出码（_launch_result.json 的 rc 由发射器 os.spawnv 取子进程退出码），"
      "wait_returncode=1 才是游戏进程退出码。")

print("\n" + "=" * 78)
print("(2) 抓帧件同一性（跨趟证据独立性）")
print("=" * 78)
for d in ("l3_20261031ha", "l3_20261031hb", "l3_20261023q", "l3_20261023r", "l3_20261021"):
    for fn in ("frame_target_01.png", "frame_early_01.png", "navsig_burst_00_g.png"):
        p = f"{R}/{d}/{fn}"
        if os.path.isfile(p):
            b = open(p, "rb").read()
            print(f"  {d}/{fn}: {len(b)}B sha16={hashlib.sha256(b).hexdigest()[:16]}")

print("\n" + "=" * 78)
print("(3) 路径长度口径（§486「两后缀 100≤130」/ 卡片「130 门禁」）")
print("=" * 78)
for suf in ("ha", "hb"):
    trip = f"D:\\Project\\ra2-campaign-forge\\{R}\\l3_20261031{suf}"
    planned = os.path.join(trip, "ct", "c_" + "0" * 12 + "_12345")
    print(f"  {suf}: 趟目录 len={len(trip)}  预演载体 len={len(planned)}")
for d in ("l3_20261031ha", "l3_20261031hb"):
    f = json.load(open(f"{R}/{d}/qc151_fields.json", encoding="utf-8"))
    pl = [e["value"] for e in f if e.get("key") == "pathlen_near_limit"]
    for v in pl[:1]:
        for dd in v.get("dirs", []):
            print(f"  {d} 实测载体 len={dd.get('chars')} dir={os.path.basename(dd.get('dir',''))}")

print("\n" + "=" * 78)
print("(4) C-2 预登记（jump ⇒ 等待期 ≥96ms 停顿证据）在卡片/台账的落地文字")
print("=" * 78)
for p in ["lead/codex_round_20261030/LEADER_battle/GOAL1_BATCH_H8_FRAMEBOUND_20261031.md",
          "lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"]:
    s = open(p, encoding="utf-8", errors="replace").read()
    for kw in ("96", "jump", "噪声重排"):
        hits = [i + 1 for i, l in enumerate(s.splitlines()) if kw in l]
        print(f"  {os.path.basename(p)} 含 '{kw}' 行号: {hits[:12]}")

print("\n" + "=" * 78)
print("(5) reviewer __pycache__ 留置（§486）")
print("=" * 78)
for d in ("lead/goal1_harness8_20261031", "lead/codex_round_20261030/XVERIFY_H8_20261031"):
    pyc = glob.glob(f"{d}/__pycache__/*")
    print(f"  {d}/__pycache__: {len(pyc)} 件 {[os.path.basename(x) for x in pyc][:6]}")

print("\n" + "=" * 78)
print("(6) 2C 趟 _rec 键存在性 vs §485 用词（killed_on_cleanup / stop_triggered）")
print("=" * 78)
rec = json.load(open("lead/qc161_u0400_trip/c2ab_x/20261031T154139_9001_P3e_E12_T1/_rec.json", encoding="utf-8"))
print("  'killed_on_cleanup' in rec =", "killed_on_cleanup" in rec, "| stop_triggered in rec =",
      "stop_triggered" in rec, "值=", rec.get("stop_triggered"))
print("  对照既往自然退趟（键缺席=无清扫强杀，probe_v2:458-468 仅 survivors 非空才写键）：")
for dd in ("20261028T205108_9001_P3e_EARLY_MENU", "20261030T211741_9001_P3e_E12_T1",
           "20261031T083340_9001_P3e_E12_T1"):
    r2 = json.load(open(f"lead/qc161_u0400_trip/c2ab_x/{dd}/_rec.json", encoding="utf-8"))
    print(f"    {dd[:24]}: has_key={('killed_on_cleanup' in r2)} val={r2.get('killed_on_cleanup','-')}")
