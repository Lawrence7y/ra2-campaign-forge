# -*- coding: utf-8 -*-
"""深度 RTTI 槽解析：core2.resolve_slot 只回扫 k<=40，这里扩大到 k<=400，
以覆盖 slot43/45 (off 0xAC/0xB4) 等高位槽。对每行 entry 的所有 dword 引用，
判定其所属 vtable_base / slot_off / RTTI 名，并核对 slot 线索号。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2

WORK = os.path.dirname(os.path.abspath(__file__))
ROWS = json.load(open(os.path.join(WORK, "b1_rows.json"), encoding="utf-8"))

def resolve_deep(refva, kmax=400):
    """从 refva 回扫，找 [vt-4]=COL(sig=0, TD 名 .?AV) 的 vtable_base。"""
    hits = []
    for k in range(0, kmax):
        vb = refva - 4 * k
        c = C2.u32(vb - 4)
        if not c:
            continue
        ci = C2.parse_col(c)
        if not ci or ci["sig"] != 0:
            continue
        tdi = C2.parse_td(ci["td"])
        if tdi and tdi["name"] and ".?AV" in tdi["name"]:
            hits.append({"vtable_base": vb, "slot_off": 4 * k,
                         "col": ci["col"], "td": tdi["td"],
                         "rtti_name": tdi["name"], "k": k})
            break
    return hits

import re
m = re.compile(r"::slot(\d+)$")
for r in ROWS:
    entry = r["entry"]
    clue_slot = None
    mm = m.search(r["name"])
    if mm:
        clue_slot = int(mm.group(1))
    ea = int(entry, 16)
    refs = C2.find_dword_refs(ea)
    print("=" * 100)
    print("%s  %s  clue_slot=%s  dword_refs=%d" % (entry, r["name"], clue_slot, len(refs)))
    for refva, sec in refs:
        dh = resolve_deep(refva)
        if not dh:
            print("   ref %08X [%s] -> NO RTTI chain (k<=400)" % (refva, sec))
            continue
        for d in dh:
            slotno = d["slot_off"] // 4
            match = "" if clue_slot is None else (" MATCH" if slotno == clue_slot else " MISMATCH")
            print("   ref %08X [%s] -> vbase=%08X off=%d slot#=%d name=%s%s" % (
                refva, sec, d["vtable_base"], d["slot_off"], slotno, d["rtti_name"], match))
