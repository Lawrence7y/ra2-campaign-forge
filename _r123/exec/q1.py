#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q1 · 独立复算 35 个全局容器对象及其 vptr 的 c7 05 写入站点。

口径：
  1) 对象地址**不**从 _r122 读，而是自己从二进制重导：
     扫 .text 里 call rel32 目标落在 [0x67fdf0,0x680f80) 的站点，
     取站点前 7 字节形态 ba <imm32> 8b ce（mov edx,imm32 ; mov ecx,esi）的 imm32。
     （_r122/r122a_objs35.json 只在「正控对照」里用来比对站点地址。）
  2) 站点 = 指令边界上恰好 10 字节、字节序列 c7 05 <disp32> <imm32> 的指令，
     且 disp32 == 对象地址，imm32 能按 MSVC RTTI 解出 .?AV 类名（即确实写了 vptr）。
  3) 正控：站点地址集合与 R122 落盘的逐对象站点地址比对。
  4) 反控：目标地址 +4 再扫，vptr 命中数必须为 0。

用法：timeout 300 python3 q1.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_r123 as C

OUT = os.path.join(C.OUTDIR, "q1.json")
R122 = "/home/t628/projects/ra2-campaign-forge/_r122/r122a_objs35.json"


def main():
    ck = C.Checks()
    C.preflight(ck)
    ins = C.Insns()

    # ---- 对象地址：自己从二进制重导
    twins = C.twin_targets(ins)
    ck.add("孪生站点数 == 35", len(twins) == 35, "measured=%d" % len(twins))
    objs = [o for _, o in twins]
    ck.add("35 个对象地址互不相同", len(set(objs)) == 35, "distinct=%d" % len(set(objs)))

    # ---- 站点：指令边界 + c7 05 + imm 可解 RTTI
    sites = C.sites_by_target(ins)
    rows = []
    n_sites = 0
    for site, obj in twins:
        cand = sorted(sites.get(obj, []))
        keep = []
        for s, imm in cand:
            r = C.rtti(imm)
            keep.append({"site": "0x%08x" % s, "imm": "0x%08x" % imm,
                         "rtti": r["name"] if r else None,
                         "rtti_ok": bool(r)})
        vptr_sites = [k for k in keep if k["rtti_ok"]]
        n_sites += len(vptr_sites)
        rows.append({"obj": "0x%08x" % obj, "edx_site": "0x%08x" % site,
                     "c705_sites_total": len(keep),
                     "c705_sites_with_vptr": len(vptr_sites),
                     "writes": keep})
    rows.sort(key=lambda r: int(r["obj"], 16))

    hist = {}
    for r in rows:
        hist[str(r["c705_sites_with_vptr"])] = hist.get(str(r["c705_sites_with_vptr"]), 0) + 1
    ck.add("每个对象都恰有 2 个 vptr 写入站点", hist == {"2": 35}, "hist=%s" % hist)
    ck.add("站点总数 == 70", n_sites == 70, "measured=%d" % n_sites)
    ck.add("全部 70 个 imm 都能按 RTTI 解出类名",
           all(w["rtti_ok"] for r in rows for w in r["writes"]),
           "unresolved=%d" % sum(1 for r in rows for w in r["writes"] if not w["rtti_ok"]))

    # ---- 正控：与 R122 落盘逐对象比对
    ref = {}
    if os.path.exists(R122):
        for o in json.load(open(R122))["objects"]:
            ref[int(o["obj"], 16)] = sorted(int(w["site"], 16) for w in o["writes"])
    mine = {int(r["obj"], 16): sorted(int(w["site"], 16)
                                      for w in r["writes"] if w["rtti_ok"]) for r in rows}
    same_obj = sum(1 for k in mine if ref.get(k) == mine[k])
    same_any = sum(1 for k in mine if k in ref and set(mine[k]) & set(ref[k]))
    ck.add("正控：至少一个对象的站点地址集合与 R122 完全相同", same_obj >= 1,
           "identical_objects=%d/35" % same_obj)
    ck.add("正控：35 个对象全部逐站一致", same_obj == 35 and set(mine) == set(ref),
           "identical=%d/35 ; obj_set_equal=%s" % (same_obj, set(mine) == set(ref)))
    ck.add("正控：对照文件本身可读（存在性）", bool(ref), "ref_objects=%d" % len(ref))

    # ---- 反控：目标 +4
    idx = C.sites_by_target(ins)
    plus4_raw = 0
    plus4_vptr = 0
    plus4_detail = []
    minus4_vptr = 0
    for r in rows:
        obj = int(r["obj"], 16)
        for cand, acc in ((obj + 4, "p4"), (obj - 4, "m4")):
            for s, imm in idx.get(cand, []):
                rr = C.rtti(imm)
                if acc == "p4":
                    plus4_raw += 1
                    if rr:
                        plus4_vptr += 1
                    plus4_detail.append({"target": "0x%08x" % cand, "site": "0x%08x" % s,
                                         "imm": "0x%08x" % imm,
                                         "rtti": rr["name"] if rr else None})
                else:
                    if rr:
                        minus4_vptr += 1
    ck.add("反控：目标 +4 后 vptr 命中数 == 0（不是宽匹配）", plus4_vptr == 0,
           "raw_c705_hits=%d, vptr_hits=%d, raw_imms=%s"
           % (plus4_raw, plus4_vptr, [d["imm"] for d in plus4_detail]))
    ck.add("反控：目标 -4 后 vptr 命中数 == 0", minus4_vptr == 0, "vptr_hits=%d" % minus4_vptr)

    res = {
        "q": "Q1",
        "binary": C.EXE,
        "sha256": C.sha256(),
        "object_derivation": "call rel32 -> [0x67fdf0,0x680f80) 且站点前 7B == ba<imm32>8bce",
        "n_objects": len(rows),
        "n_sites": n_sites,
        "sites_per_object_hist": hist,
        "all_70_imms_rtti_ok": all(w["rtti_ok"] for r in rows for w in r["writes"]),
        "poscontrol_identical_to_r122": same_obj,
        "poscontrol_any_overlap": same_any,
        "negcontrol_target_plus4": {"raw_c705_hits": plus4_raw, "vptr_hits": plus4_vptr,
                                    "detail": plus4_detail},
        "negcontrol_target_minus4": {"vptr_hits": minus4_vptr},
        "objects": rows,
        "checks": ck.rows,
        "selftest": ck.summary(),
    }
    with open(OUT, "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: res[k] for k in ("n_objects", "n_sites", "sites_per_object_hist",
                                          "poscontrol_identical_to_r122",
                                          "negcontrol_target_plus4", "selftest")},
                     ensure_ascii=False))
    return 0 if res["selftest"]["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
