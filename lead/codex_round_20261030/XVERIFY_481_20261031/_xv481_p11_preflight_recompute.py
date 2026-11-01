#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账（§481 批）探针 p11：preflight 各 OK 项的盘上独立复算（探针件指纹/游戏源件数/进程残留）。"""
import hashlib, io, sys, os, glob, json, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def s16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

print("== preflight 8 项 OK 的盘上复算（pin 常量 _drive_c2_x_probe_v2.py:59-63 / checks :762-772）==")
ITEMS = [
    ("gamemd 母本 sha", "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L1_sf8_20261020/gamemd.exe", "73201cc021497c95"),
    ("loader sha", "lead/goal2_rc4_fixv5_20261022/src/rc4_loader.exe", "ebddf6a61273c874"),
    ("harness7 批准指纹", "lead/goal1_harness7_20261023/qc151_trip.harness7.py", "d019e8beecfb5fd8"),
    ("探针批准指纹", "lead/goal2_rc4_fixv5_20261022/_rc4_ab_probe.py", "b063052cd02df28c"),
    ("v2 终钉", "lead/qc161_u0400_trip/codex_e12_e5_20261030/candidate/_drive_c2_x_probe_v2.py", "6afe2711136c3b52"),
    ("earlyclose 终钉", "lead/qc161_u0400_trip/codex_e12_e5_20261030/candidate/_drive_c2_x_earlyclose.py", "2e970eec43fe37ff"),
    ("源 ra2render.ini sha16", "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L1_sf8_20261020/ra2render.ini", "27c9a60c55a8a1b4"),
]
for name, p, want in ITEMS:
    if not os.path.isfile(p):
        print(f"  {name:<22} 缺文件 → UNVERIFIED  ({p})"); continue
    got = s16(p)
    print(f"  {name:<22} 盘上={got}  pin={want}  match={got == want}  bytes={os.path.getsize(p)}")
ini = ITEMS[-1][1]
print(f"  源 ra2render.ini size={os.path.getsize(ini)} 钉=16496 match={os.path.getsize(ini) == 16496}")

SRC = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L1_sf8_20261020"
n = len([f for f in glob.glob(SRC + "/*") if os.path.isfile(f)])
print(f"  游戏源件数={n} 钉=88 match={n == 88}")

print("\n== c2 DLL sha256 全值 ==")
dll = "lead/qc161_u0400_trip/d09a_c2_candidate/ra2rc4guard_c2.dll"
print("  ", hashlib.sha256(open(dll, "rb").read()).hexdigest())
print("   pin edb9a0cde129c105e087db61f6661b4722a80787e5b5949bd0b0890e0354f2de")

print("\n== 当前残留游戏进程（只读查询，非趟内读数）==")
try:
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq gamemd.exe"], capture_output=True, text=True, timeout=30)
    print("  gamemd:", out.stdout.strip().splitlines()[-1][:80] if out.stdout.strip() else "(空)")
    out2 = subprocess.run(["tasklist", "/FI", "IMAGENAME eq rc4_loader.exe"], capture_output=True, text=True, timeout=30)
    print("  loader:", out2.stdout.strip().splitlines()[-1][:80] if out2.stdout.strip() else "(空)")
except Exception as e:
    print("  tasklist 查询失败:", repr(e))

print("\n== 本批两趟载体目录残留（ct 应为不存在）==")
for d in ("20261031T083340_9001_P3e_E12_T1", "20261031T083611_9001_P3e_E12_T1"):
    p = f"lead/qc161_u0400_trip/c2ab_x/{d}/ct"
    print(f"  {d}/ct exists={os.path.exists(p)}")
