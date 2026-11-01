#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族对账 s12：(A) 本批发射时点(21:12~21:25)是否存在 preflight/selftest 留档；
   (B) ②「短 TEMP(4 字符)」在趟记录内是否可证；(C) ① 载体外第三方模块清单。
"""
import json, io, sys, os, time, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

print("### (A) 10-30 21:00~21:30 之间 mtime 的 lead/ 下文件（排除 out/re_work）")
hits = []
for root, dirs, files in os.walk("lead"):
    dirs[:] = [d for d in dirs if d not in ("__pycache__", ".mimosa")]
    for fn in files:
        p = os.path.join(root, fn)
        try:
            mt = os.path.getmtime(p)
        except OSError:
            continue
        if 1793365200 <= mt <= 1793366700:  # 21:00~21:25 CST
            hits.append((p, time.strftime("%H:%M:%S", time.localtime(mt))))
for p, ts in sorted(hits, key=lambda x: x[1]):
    print(f"   {ts}  {p}")
print(f"   合计 {len(hits)} 个")
pref = [h for h in hits if "preflight" in h[0].lower() or "selftest" in h[0].lower() or "evidence" in h[0].lower()]
print(f"   其中名字含 preflight/selftest/evidence 的 = {pref}  => 本批时点预检/自检留档 {'存在' if pref else '不存在（盘上最早/最新均为 07:18 E5 批时点）'}")

print("\n### (B) ② _rec 内 TEMP / 载体路径证据")
for tag, d in (("hold13", "20261030T211741_9001_P3e_E12_T1"), ("hold15", "20261030T212233_9001_P3e_E12_T1")):
    txt = open(f"lead/qc161_u0400_trip/c2ab_x/{d}/_rec.json", encoding="utf-8").read()
    r = json.loads(txt)
    print(f"  {tag}: 含 'TEMP'?", "TEMP" in txt, " 含 'tmp'?", "tmp" in txt.lower())
    print(f"     out_dir={r['out_dir']}")
    carrier = f"lead/qc161_u0400_trip/c2ab_x/{d}/ct"
    print(f"     趟目录内 ct/ 存在? {os.path.exists(carrier)}  （carrier_deleted=True ⇒ 已删，无长度留痕）")
    print(f"     是否存在 pathlen 类字段 = {[k for k in r if 'path' in k.lower() or 'len' in k.lower()]}")

print("\n### (C) ① ISOLATION 第三方模块明细")
T = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
for d in ("l3_20261023q", "l3_20261023r"):
    x = json.load(open(f"{T}/{d}/qc151_fields.json", encoding="utf-8"))
    for r in x:
        if r["key"] == "iso_outside_detail":
            print(f"  {d}: iso_outside={json.dumps(r['value'], ensure_ascii=False)}")
