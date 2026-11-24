# -*- coding: utf-8 -*-
"""纪律12：调用链上下各一层查层指针是否流到 call[reg+0x1C]。
 (a) 全 .text 立即数/位移 0x7E6060（LayerClass vftable 地址）引用
 (b) chB 层数组引用函数的直接 callee 是否落在 chA 站点函数（下一层）
 (c) chA 站点函数的直接 caller 是否落在 chB 函数（上一层）
"""
from __future__ import annotations
import os
import sys
import struct
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import w173_common as C
import audit_lib

E = C.EVID
VFT = 0x7E6060
LO, HI = C.LAYER_BASE, C.LAYER_END


def main():
    ins = C.text_insns()
    b = C.B()
    L = ["=" * 95, "纪律12 补验：层指针 -> call[reg+0x1C] 的调用链上下各一层"]

    # (a) 0x7E6060 立即数/位移引用
    L.append("")
    L.append("[a] 全 .text 中 0x7E6060 (LayerClass vftable) 的立即数/位移引用")
    hits = []
    for j, r in enumerate(ins):
        for op in r["ops"]:
            if op["kind"] == "imm" and (op["val"] & 0xFFFFFFFF) == VFT:
                hits.append((r["va"], "imm", C.fmt(r)))
            if op["kind"] == "mem" and (op["disp"] & 0xFFFFFFFF) == VFT:
                hits.append((r["va"], "disp", C.fmt(r)))
    L.append("  命中数: %d" % len(hits))
    for va, kind, txt in hits:
        L.append("    %08X %s %s" % (va, kind, txt))
    # 也扫原始字节 60 60 7E 00
    t = b.text
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    pat = struct.pack("<I", VFT)
    rawhits = []
    start = 0
    while True:
        k = data.find(pat, start)
        if k < 0:
            break
        rawhits.append(t["va"] + k)
        start = k + 1
    L.append("  原始字节 60 60 7E 00 命中数: %d -> %s" % (
        len(rawhits), ",".join("%08X" % x for x in rawhits[:40])))

    # 收集 chA 站点与函数
    chA_sites = []
    chA_funcs = set()
    for j, r in enumerate(ins):
        if r["mn"] != "call" or not r["ops"]:
            continue
        op = r["ops"][0]
        if op["kind"] == "mem" and op["base"] and (op["disp"] & 0xFFFFFFFF) == C.ADD_SLOT:
            chA_sites.append(r["va"])
            o = C.owner(r["va"], "atlas")
            if o:
                chA_funcs.add(o[0])

    # 收集 chB 函数（层数组引用所在函数）
    chB_funcs = set()
    for j, r in enumerate(ins):
        for op in r["ops"]:
            if (op["kind"] == "imm" and LO <= (op["val"] & 0xFFFFFFFF) < HI) or \
               (op["kind"] == "mem" and LO <= (op["disp"] & 0xFFFFFFFF) < HI):
                o = C.owner(r["va"], "atlas")
                if o:
                    chB_funcs.add(o[0])
                break

    # sweep_calls: call_target -> sites
    calls, jmps, st = audit_lib.sweep_calls(b)
    # site -> func (atlas 区间包含)
    def site_fn(va):
        o = C.owner(va, "atlas")
        return o[0] if o else None

    # (b) chB 函数的直接 callee 是否落在 chA 站点函数
    L.append("")
    L.append("[b] chB(层数组引用)函数的直接 callee 中是否存在 chA(call[+0x1C])站点函数")
    chb_callee_to_chA = []
    for tgt, sites in calls.items():
        for s in sites:
            f = site_fn(s)
            if f in chB_funcs and tgt in chA_funcs:
                chb_callee_to_chA.append((f, s, tgt))
    L.append("  命中数(chB函数内 call -> 含call[+0x1C]的函数): %d" % len(chb_callee_to_chA))
    for f, s, tgt in chb_callee_to_chA[:60]:
        L.append("    chB fn %08X : call@%08X -> %08X(含call[+0x1C])" % (f, s, tgt))

    # (c) chA 站点函数的直接 caller 是否落在 chB 函数
    L.append("")
    L.append("[c] chA(call[+0x1C])站点函数的直接 caller 中是否存在 chB(层数组引用)函数")
    chA_caller_from_chB = []
    for f in chA_funcs:
        for s in calls.get(f, []):
            cf = site_fn(s)
            if cf in chB_funcs:
                chA_caller_from_chB.append((cf, s, f))
    L.append("  命中数: %d" % len(chA_caller_from_chB))
    for cf, s, f in chA_caller_from_chB[:60]:
        L.append("    chB fn %08X : call@%08X -> chA fn %08X" % (cf, s, f))

    L.append("")
    L.append("chA站点函数数=%d chB函数数=%d 直接函数级交集=%s" % (
        len(chA_funcs), len(chB_funcs),
        ",".join("%08X" % x for x in sorted(chA_funcs & chB_funcs))))

    C.write_text(os.path.join(E, "w173_chain_check.txt"), L)
    print("chain check: 7E6060 refs=%d raw=%d b=%d c=%d funcs chA=%d chB=%d" % (
        len(hits), len(rawhits), len(chb_callee_to_chA), len(chA_caller_from_chB),
        len(chA_funcs), len(chB_funcs)))


if __name__ == "__main__":
    main()
