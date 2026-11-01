#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 s06：驱动身份可证性 + hold_override/protocol 字段的代码溯源。
台账 GOAL2 声明「驱动=E5 候选件 sha256 90a1890a…38d03」。仓库存在两份同名
_drive_c2_x_e12.py（哈希不同）。趟级 _rec.json 未记录所用驱动自身哈希，
故检查「hold_override / protocol(+%.1fs) / e2_params 键集」能否唯一指认其中一份。
"""
import hashlib, io, sys, json, re, difflib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
A = "lead/qc161_u0400_trip/_drive_c2_x_e12.py"
B = "lead/qc161_u0400_trip/codex_e12_e5_20261030/candidate/_drive_c2_x_e12.py"
C = "lead/qc161_u0400_trip/codex_e12_fix_20261029/candidate/_drive_c2_x_e12.py"
for p in (A, B, C):
    print(hashlib.sha256(open(p, "rb").read()).hexdigest()[:16], p)
sa = open(A, encoding="utf-8").read()
sb = open(B, encoding="utf-8").read()
sc = open(C, encoding="utf-8").read()
print("\n--- 特征串存在性（能否区分三份）")
for feat in ("hold_override", "normalize_hold_s", "module_const_s", "effective_s",
             "early-close (window+%.1fs)", "E2-slow1Hz", "zero_close_samples",
             "wait_error:%d", "present_with_read_fail_rows", "spin_x_hook6_undetermined",
             "latch_plus_30", "interaction_window"):
    print(f"  {feat!r:42s} A={feat in sa}  B={feat in sb}  C={feat in sc}")
print("\n--- A vs B 差异行数/摘要")
d = list(difflib.unified_diff(sa.splitlines(), sb.splitlines(), "A_root", "B_e5candidate", lineterm="", n=0))
print("  diff 行数=", len(d))
for ln in d[:60]:
    print("   ", ln[:160])
print("\n--- 三份文件字节数/行数")
for p, s in (("A", sa), ("B", sb), ("C", sc)):
    print(f"  {p}: bytes={len(s.encode('utf-8'))} lines={s.count(chr(10))+1}")
print("\n--- _rec.json 内是否有驱动自身哈希留痕字段")
for tag, d2 in (("hold13", "20261030T211741_9001_P3e_E12_T1"),):
    r = json.load(open("lead/qc161_u0400_trip/c2ab_x/" + d2 + "/_rec.json", encoding="utf-8"))
    txt = json.dumps(r, ensure_ascii=False)
    print("  keys 含 'e12' 驱动哈希?", [k for k in r if "drive" in k.lower() or "e12" in k.lower()])
    print("  frozen_masters 只含:", list(r["e2_params"]["frozen_masters_sha256_at_import"].keys()))
    print("  90a1890a 在 _rec 中出现?", "90a1890a" in txt, "| f9d3f36a 出现?", "f9d3f36a" in txt)
