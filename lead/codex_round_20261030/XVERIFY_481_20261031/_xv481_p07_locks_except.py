#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）探针 p07：批前后冻结件指纹复验 + except.txt 恒值旁证 + p02 族归属一致性打印修正。
   指纹常量取自驱动件 pin 值（_drive_c2_x_probe_v2.py:59-62、preflight checks :762-772），只读盘上实际文件复算。
"""
import json, io, sys, os, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.getcwd()
def sh(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

PINS = {
    "gamemd.exe": ("out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L1_sf8_20261020/gamemd.exe", "73201cc021497c95"),
    "rc4_loader.exe": ("lead/goal2_rc4_fixv5_20261022/src/rc4_loader.exe", "ebddf6a61273c874"),
    "ra2rc4guard_c2.dll": ("lead/qc161_u0400_trip/d09a_c2_candidate/ra2rc4guard_c2.dll", "edb9a0cde129c105e087db61f6661b4722a80787e5b5949bd0b0890e0354f2de"),
    "harness7": ("lead/goal1_harness7_20261023/qc151_trip.harness7.py", "d019e8be"),
    "v2 (frozen)": ("lead/qc161_u0400_trip/codex_e12_e5_20261030/candidate/_drive_c2_x_probe_v2.py", "6afe2711"),
    "earlyclose (frozen)": ("lead/qc161_u0400_trip/codex_e12_e5_20261030/candidate/_drive_c2_x_earlyclose.py", "2e970eec"),
    "e12 driver (candidate)": ("lead/qc161_u0400_trip/codex_e12_e5_20261030/candidate/_drive_c2_x_e12.py", "90a1890a"),
}
print("== 批后盘上指纹复验（对照驱动 pin 常量；pin 值 path:line 见文件头注释）==")
for name, (p, want) in PINS.items():
    if not os.path.isfile(p):
        print(f"  {name:<22} 文件不存在 → UNVERIFIED  {p}"); continue
    got = sh(p)
    print(f"  {name:<22} sha256[:16]={got[:16]}  pin={want}  match={got.startswith(want)}  bytes={os.path.getsize(p)}")

print("\n== except.txt 恒值旁证（母本 vs 本批 _rec 三处读数）==")
EX = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L1_sf8_20261020/except.txt"
b = open(EX, "rb").read()
nl = b.count(b"\n")
print(f"  母本 {EX}: bytes={len(b)} 行数={nl} sha256[:16]={hashlib.sha256(b).hexdigest()[:16]}")
for tag, d in [("b2-h15.3", "20261031T083340_9001_P3e_E12_T1"), ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1"),
               ("hold15(§474)", "20261030T212233_9001_P3e_E12_T1")]:
    r = json.load(open(f"lead/qc161_u0400_trip/c2ab_x/{d}/_rec.json", encoding="utf-8"))
    print(f"  {tag:<14} except_before={r.get('except_before')} close_last={(r.get('except_at') or {}).get('close_last')} "
          f"after_kill={(r.get('except_at') or {}).get('after_kill')} changed={r.get('except_changed')} "
          f"⇒ 与母本一致={r.get('except_before') == hashlib.sha256(b).hexdigest()[:16]}")

print("\n== 本批 2 趟 exitstate 全 1195 行严格逐位复核（含键存在性）==")
for tag, d in [("b2-h15.3", "20261031T083340_9001_P3e_E12_T1"), ("b2-h15.8", "20261031T083611_9001_P3e_E12_T1")]:
    rows = json.load(open(f"lead/qc161_u0400_trip/c2ab_x/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    miss = [i for i, x in enumerate(rows) if "exitstate" not in x]
    bad = [i for i, x in enumerate(rows) if x.get("exitstate") != 0]
    n258 = sum(1 for x in rows if x.get("wait") == 258)
    print(f"  {tag}: 行数={len(rows)} 缺 exitstate 键行={len(miss)} exitstate≠0 行={len(bad)} "
          f"wait==258 行={n258} ⇒ 值域严格{{0}}={len(miss)==0 and len(bad)==0} ; wait 恒 258={n258==len(rows)}")

print("\n== 13 趟 first(hwnd==0) == first(singleton==0) 全量核对（§481 只声称本批 2 趟）==")
ALL = ["20261030T211741_9001_P3e_E12_T1", "20261030T212148_9001_P3e_E12_T1", "20261030T212233_9001_P3e_E12_T1",
       "20261030T072242_9001_P3e_E12_T1", "20261030T072353_9001_P3e_E12_T1", "20261030T072630_9001_P3e_E12_T1",
       "20261029T222811_9001_P3e_E12_T1", "20261029T231621_9001_P3e_E12_T1",
       "20261028T204123_9001_P3e_EARLY_MENU", "20261028T204921_9001_P3e_EARLY_MENU", "20261028T205108_9001_P3e_EARLY_MENU",
       "20261031T083340_9001_P3e_E12_T1", "20261031T083611_9001_P3e_E12_T1"]
allsame = True
for d in ALL:
    rows = json.load(open(f"lead/qc161_u0400_trip/c2ab_x/{d}/timeline.json", encoding="utf-8"))["close_rows"]
    hz = next((i for i, x in enumerate(rows) if x.get("hwnd") == 0), None)
    sg = next((i for i, x in enumerate(rows) if x.get("singleton") == 0), None)
    same = hz is not None and hz == sg
    allsame &= same
    print(f"  {d[:32]:<34} first_hwnd0={hz} first_singleton0={sg} 同行={same}")
print(f"  ⇒ 13/13 同行（含闩族）? {allsame}")
