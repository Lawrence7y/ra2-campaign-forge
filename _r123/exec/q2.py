#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q2 · 解析 70 个 vptr 的 MSVC x86 RTTI，并核第二个类是否在第一个类的基类数组里。

布局（x86，32 位 RTTI）：
  [vtable-4] -> CompleteObjectLocator，24 字节：
     +0 signature(=0) +4 this-offset +8 cdOffset +12 pTypeDescriptor
     +16 pClassDescriptor +20 pSelf
  TypeDescriptor: +8 = 修饰名（.?AV...）
  ClassHierarchyDescriptor: +0 sig +4 attr +8 numBaseClasses +12 pBaseClassArray
  BaseClassDescriptor(24B): +0 pTypeDescriptor +4 numContainedBases +8 mdisp ...

序列：每个对象的两个写入站点按站点地址升序 => writes[0]=第一个, writes[1]=第二个。

正控：至少一个对象 writes[1] 是 VectorClass 版本、writes[0] 是 DynamicVectorClass 版本。
反控：vtable+4 后解不出合法类名（COL signature != 0 或类名不以 .?AV 开头）。

用法：timeout 300 python3 q2.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_r123 as C

OUT = os.path.join(C.OUTDIR, "q2.json")


def q1_rows():
    """复用本目录 q1.json 的 35 个对象及其站点（同一轮产物，口径一致）。"""
    p = os.path.join(C.OUTDIR, "q1.json")
    if not os.path.exists(p):
        raise SystemExit("先跑 q1.py")
    with open(p) as f:
        d = json.load(f)
    return [(int(r["obj"], 16),
             sorted([(int(w["site"], 16), int(w["imm"], 16)) for w in r["writes"]]))
            for r in d["objects"]]


def is_dyn(n):
    return bool(n) and n.startswith(".?AV?$DynamicVectorClass@")


def is_vec(n):
    return bool(n) and n.startswith(".?AV?$VectorClass@")


def main():
    ck = C.Checks()
    C.preflight(ck)
    rows = []
    n_both = 0
    n_member = 0
    n_sig_ok = 0
    neg_ok = 0
    neg_fail = []
    for obj, ws in sorted(q1_rows()):
        w0, w1 = ws[0], ws[1]
        r0 = C.rtti(w0[1])
        r1 = C.rtti(w1[1])
        if r0 and r0["sig"] == 0 and r1 and r1["sig"] == 0:
            n_sig_ok += 1
        member = bool(r0) and any(b["name"] == r1["name"] for b in r0["bases"]) if r1 else False
        if member:
            n_member += 1
        base_names = [b["name"] for b in r0["bases"]] if r0 else []
        if is_dyn(r0 and r0["name"]) and is_vec(r1 and r1["name"]):
            n_both += 1
        # 反控：vtable + 4
        n0 = C.rtti(w0[1] + 4)
        n1 = C.rtti(w1[1] + 4)
        if n0 is None and n1 is None:
            neg_ok += 1
        else:
            neg_fail.append({"obj": "0x%08x" % obj,
                             "plus4_first": n0 and n0["name"],
                             "plus4_second": n1 and n1["name"]})
        rows.append({
            "obj": "0x%08x" % obj,
            "site_first": "0x%08x" % w0[0],
            "site_second": "0x%08x" % w1[0],
            "vtable_first": "0x%08x" % w0[1],
            "vtable_second": "0x%08x" % w1[1],
            "name_first": r0["name"] if r0 else None,
            "name_second": r1["name"] if r1 else None,
            "this_off_first": r0["this_off"] if r0 else None,
            "this_off_second": r1["this_off"] if r1 else None,
            "col_first": "0x%08x" % r0["col"] if r0 else None,
            "col_second": "0x%08x" % r1["col"] if r1 else None,
            "col_sig_first": r0["sig"] if r0 else None,
            "col_sig_second": r1["sig"] if r1 else None,
            "nbase_first": (r0["chd"] or {}).get("nbase") if r0 else None,
            "base_names_first": base_names,
            "second_in_first_bases": bool(member),
            "plus4_first_resolves": n0["name"] if n0 else None,
            "plus4_second_resolves": n1["name"] if n1 else None,
        })

    ck.add("35 个对象两处 vptr 全部解出合法 RTTI（COL sig==0）", n_sig_ok == 35,
           "ok=%d/35" % n_sig_ok)
    ck.add("70 个类名互不相同",
           len({r["name_first"] for r in rows} | {r["name_second"] for r in rows}) == 70,
           "distinct=%d" % len({r["name_first"] for r in rows} | {r["name_second"] for r in rows}))
    ck.add("35 个对象的第二个类都能在第一个类的基类数组里找到", n_member == 35,
           "member=%d/35" % n_member)
    ck.add("第一个类的基类数组 nbase == 2 且第二项就是第二个类", all(
        r["nbase_first"] == 2 and r["base_names_first"] and
        r["base_names_first"][-1] == r["name_second"] for r in rows),
        "nbase_hist=%s" % sorted({r["nbase_first"] for r in rows}))
    ck.add("全部 this-offset == 0", all(r["this_off_first"] == 0 and r["this_off_second"] == 0
                                        for r in rows),
           "this_offs=%s" % sorted({(r["this_off_first"], r["this_off_second"]) for r in rows}))
    ck.add("正控：至少一个对象 second=VectorClass / first=DynamicVectorClass", n_both >= 1,
           "count=%d/35" % n_both)
    ck.add("正控（更强）：35 个对象全是 DVC 在前、VC 在后", n_both == 35, "count=%d/35" % n_both)
    ck.add("反控：35 个对象的 vtable+4 全部解不出合法类名", neg_ok == 35,
           "ok=%d/35 fail=%s" % (neg_ok, neg_fail[:3]))
    # 反控细分：vt+4 失败的原因
    reasons = []
    for obj, ws in sorted(q1_rows())[:35]:
        for vt in (ws[0][1], ws[1][1]):
            col = C.u32(vt + 4 - 4)
            b = C.rd(col, 24) if col else None
            if b is None:
                reasons.append("no-COL")
                continue
            import struct as _s
            sig, _toff, _cd, ptd = _s.unpack("<4I", b[:16])
            nm = C.cstr(ptd + 8, 256) if ptd else None
            if sig != 0:
                reasons.append("sig!=0")
            elif not (nm and nm.startswith(".?AV")):
                reasons.append("name-not-AV")
            else:
                reasons.append("BAD")
    ck.add("反控：vt+4 的失败原因全部落在 {sig!=0, 类名非 .?AV, 无 COL}",
           "BAD" not in reasons,
           "reason_hist=%s" % {k: reasons.count(k) for k in sorted(set(reasons))})

    res = {
        "q": "Q2",
        "binary": C.EXE,
        "sha256": C.sha256(),
        "col_layout": "24B: sig/this-off/cdOff/pTD/pCD/pSelf",
        "ordering": "每个对象两个 c7 05 站点按站点地址升序：first 为低地址站点",
        "n_objects": len(rows),
        "n_vtables": 2 * len(rows),
        "poscontrol_dvc_first_vc_second": n_both,
        "negcontrol_vtable_plus4_unresolved": neg_ok,
        "negcontrol_reason_hist": {k: reasons.count(k) for k in sorted(set(reasons))},
        "objects": rows,
        "checks": ck.rows,
        "selftest": ck.summary(),
    }
    with open(OUT, "w") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: res[k] for k in ("n_objects", "n_vtables",
                                          "poscontrol_dvc_first_vc_second",
                                          "negcontrol_vtable_plus4_unresolved",
                                          "negcontrol_reason_hist", "selftest")},
                     ensure_ascii=False))
    return 0 if res["selftest"]["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
