# -*- coding: utf-8 -*-
"""把 18 行的函数体 + ④ 各安装点宿主函数体 dump 到 _work/dump_<entry>.txt。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

WORK = os.path.dirname(os.path.abspath(__file__))
ROWS = json.load(open(os.path.join(WORK, "b2_rows.json"), encoding="utf-8"))
SUR = {s["entry"]: s for s in json.load(open(os.path.join(WORK, "survey.json"), encoding="utf-8"))}

for r in ROWS:
    e = r["entry"]
    ea = int(e, 16)
    size = C.ATLAS.get(e, {}).get("size") or 0
    parts = []
    parts.append("# ROW %s  %s  size=%d" % (e, r["name"], size))
    parts.append("\n## 本行函数体\n")
    parts.append(C.dump(ea, size))
    s = SUR[e]
    # ④ 宿主函数体
    hosts = set()
    if s.get("ring4"):
        for st in s["ring4"]["stores"]:
            if st["in_func_va"]:
                hosts.add(st["in_func_va"])
    for h in sorted(hosts):
        hk = C.hx(h)
        hsz = C.ATLAS.get(hk, {}).get("size") or 96
        parts.append("\n## ④ 宿主函数 %s (size=%d)  [atexit=%s]\n" % (hk, hsz, C.is_atexit(h)))
        parts.append(C.dump(h, hsz))
    # ③ 站点被调函数体（只对有 imm 目标的）
    if s.get("sites_3b2"):
        seen = set()
        for t in s["sites_3b2"]:
            if not t["callee"] or t["callee"] in seen:
                continue
            seen.add(t["callee"])
            cv = int(t["callee"], 16)
            if not C.in_text(cv):
                continue
            cs = C.ATLAS.get(t["callee"], {}).get("size") or 0
            parts.append("\n## ③ 站点被调 %s (size=%d)  [站点 %s]\n" % (t["callee"], cs, t["call"]))
            parts.append(C.dump(cv, min(cs, 400)))
    open(os.path.join(WORK, "dump_%s.txt" % e), "w", encoding="utf-8").write("\n".join(parts) + "\n")
    print("dumped", e, len("\n".join(parts)))
