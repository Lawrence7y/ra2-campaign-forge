#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 s14：(i) STALL_ANATOMY_raw.json 前提件自校（长停顿是否全伴 units 静态）；
   (ii) 11 趟菜单早窗的「闩绝对时刻 / hwnd 归零绝对时刻」带宽重算（检验「非绝对时刻」表述强度）。
"""
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

print("### (i) STALL_ANATOMY：stall>=0.5s 的窗，是否 units 静态（dU≈0 / chpts<=1）")
SA = "lead/codex_round_20261030/LEADER_battle/STALL_ANATOMY_raw.json"
x = json.load(open(SA, encoding="utf-8"))
print("  条目数=", len(x), " 字段=", sorted(x[0].keys()))
big = [e for e in x if (e.get("stall") or 0) >= 0.5]
print(f"  stall>=0.5s 的窗条目={len(big)}")
bad = [e for e in big if abs(e.get("dU") or 0) > 5 or (e.get("chpts") or 0) > 5]
for e in big:
    print(f"   trip={e['trip']:16s} w={e['w']} pre={e['pre']} u0={e['u0']} uf={e['uf']} ul={e['ul']} "
          f"dU={e['dU']} chpts={e['chpts']} stall={round(e['stall'],3)} lr={e['lr']}")
print(f"  ⇒ 长停顿窗中 units 变化>5 或 变化点>5 的条目={len(bad)}  => 台账『全是终局(units 静态)』{'成立' if not bad else '需复核'}")
act = [e for e in x if (e.get("chpts") or 0) > 5 and e["w"] == 0 and (e.get("pre") or 0) >= 25 and (e.get("stall") or 0) >= 0.5]
print(f"  31档(pre>=25) ∧ W0 ∧ 活动(units变化点>5) ∧ 有≥0.5s长停顿 的条目={len(act)} {act}")

print("\n### (ii) 11 趟：闩绝对时刻 与 hwnd 归零绝对时刻 带宽")
CB = "lead/qc161_u0400_trip/c2ab_x"
D = [("hold13", "20261030T211741_9001_P3e_E12_T1"), ("hold14", "20261030T212148_9001_P3e_E12_T1"),
     ("hold15", "20261030T212233_9001_P3e_E12_T1"), ("E5h10", "20261030T072242_9001_P3e_E12_T1"),
     ("E5h15", "20261030T072353_9001_P3e_E12_T1"), ("E5h20", "20261030T072630_9001_P3e_E12_T1"),
     ("1029T2228", "20261029T222811_9001_P3e_E12_T1"), ("1029T2316", "20261029T231621_9001_P3e_E12_T1"),
     ("204123挂死", "20261028T204123_9001_P3e_EARLY_MENU"), ("204921", "20261028T204921_9001_P3e_EARLY_MENU"),
     ("205108", "20261028T205108_9001_P3e_EARLY_MENU")]
hdr = "{:<11} {:>8} {:>9} {:>10} {:>10} {:>9} {:>8}"
print(hdr.format("trip", "close_s", "hwnd0ab", "闩abs", "d(闩-cl)", "n(1)", "exited"))
latchabs, hzabs_nol, hzabs_lat = [], [], []
for tag, d in D:
    r = json.load(open(f"{CB}/{d}/_rec.json", encoding="utf-8"))
    rows = json.load(open(f"{CB}/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    t0 = r["close_delivery"]["t"] - r["closed_at_s"]
    ones = [i for i, x2 in enumerate(rows) if x2.get("exitstate") == 1]
    hz = [i for i, x2 in enumerate(rows) if x2.get("hwnd") == 0]
    la = round(rows[ones[0]]["t"] - t0, 3) if ones else None
    ha = round(rows[hz[0]]["t"] - t0, 3) if hz else None
    print(hdr.format(tag, "%.3f" % r["closed_at_s"], str(ha), str(la),
                     ("%.3f" % (la - r["closed_at_s"])) if la else "-", str(len(ones)), str(r.get("exited"))))
    if la:
        latchabs.append((tag, la))
    if ha:
        (hzabs_lat if la else hzabs_nol).append((tag, ha))
print("\n  闩绝对时刻集合:", [v for _, v in latchabs])
print(f"  => 闩绝对 min={min(v for _, v in latchabs)} max={max(v for _, v in latchabs)} n={len(latchabs)}")
print("  不闩趟 hwnd 归零绝对:", [v for _, v in hzabs_nol])
if hzabs_nol:
    print(f"  => 不闩侧 hwnd0 min={min(v for _, v in hzabs_nol)} max={max(v for _, v in hzabs_nol)}")
print("  闩趟 hwnd 归零绝对(=close+~0.1，早于 21s 带):", [v for _, v in hzabs_lat])
