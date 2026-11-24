# -*- coding: utf-8 -*-
"""独立复核环②：全镜像（含 .text）逐 4 对齐/非对齐扫 dword==entry，
并查 entry 是否作为立即数/取址出现在别处；同时列出 direct caller 所在 atlas 函数。
只读。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W

WORK = os.path.dirname(os.path.abspath(__file__))
j = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))

# 全 section 原始 bytes（含 .text），按 VA
SECS = []
for s in R._pe.sections:
    nm = s.Name.rstrip(b"\x00").decode("latin1")
    va = R.IB + s.VirtualAddress
    sz = max(s.Misc_VirtualSize, s.SizeOfRawData)
    SECS.append((nm, va, sz, s.get_data()[:sz]))

def scan_dword_all(target):
    needle = struct.pack("<I", target)
    hits = []
    for nm, v0, sz, data in SECS:
        st = 0
        while True:
            i = data.find(needle, st)
            if i < 0: break
            hits.append((nm, "%08X" % (v0 + i), i % 4 == 0))
            st = i + 1
    return hits

out = {}
for r in j:
    e = r["entry"]; ea = int(e, 16)
    dwh = scan_dword_all(ea)
    # 每个 direct caller 归属的 atlas 函数
    callers = []
    for c in r["direct_callers"]:
        f = W.find_containing_atlas_func(int(c, 16))
        callers.append({"site": c, "func": ("%08X" % f[0]) if f else None,
                        "func_size": f[2] if f else None})
    out[e] = {
        "entry": e,
        "dword_refs_all_sections": [{"sec": s, "va": v, "aligned4": a} for s, v, a in dwh],
        "direct_callers_with_func": callers,
        "first_insns": r["first_insns"],
    }
    print("%s dword_refs=%d direct=%d" % (e, len(dwh), len(callers)), flush=True)

json.dump(out, open(os.path.join(WORK, "verify2.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("wrote verify2.json")
