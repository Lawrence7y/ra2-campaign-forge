# -*- coding: utf-8 -*-
"""W173 验证：
 1) 读 .rdata 虚表 0x7E6060 各槽，确认 +0x1C=0x5519B0；并找哪些虚表的 +0x1C 槽=0x5519B0
 2) audit_lib.sweep_calls 确认 0x5519B0 的直接调用者集合
 3) 全镜像扫数据节里 dword 值 ∈ [0x8A0360,0x8A03D8) 的"存储的层指针"
 4) 每个 call[reg+0x1C] 站点：函数内 vptr reg 与 ecx 的最后写入指令（compact）
 5) 每个 chB 层数组引用所在函数是否含 call[reg+0x1C]
"""
from __future__ import annotations
import os
import sys
import bisect
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\_lead_audit")
import w173_common as C
import audit_lib

E = C.EVID
ADD = C.ADD_IMPL
LO, HI = C.LAYER_BASE, C.LAYER_END


def dump_vftable(va, nslots=12):
    b = C.B()
    vals = []
    for i in range(nslots):
        try:
            v = b.u32(va + i * 4)
        except Exception:
            v = None
        vals.append((i, i * 4, v))
    return vals


def main():
    L = []
    b = C.B()

    L.append("=" * 90)
    L.append("[1] LayerClass vftable @0x7E6060 前 12 槽（从 .rdata 原始 dword 读）")
    for i, off, v in dump_vftable(0x7E6060, 12):
        L.append("  slot %d (+0x%02X) = %s%s" % (
            i, off, ("%08X" % v) if v is not None else "N/A",
            "   <== Add (0x5519B0)" if v == ADD else ""))

    raws = []
    for s in b.sections:
        buf = b.pe.__data__[s["raw"]:s["raw"] + s["rawsize"]]
        start = 0
        while True:
            k = buf.find(struct.pack("<I", ADD), start)
            if k < 0:
                break
            va = s["va"] + k
            raws.append((s["name"], va, k - 0x1C if k >= 0x1C else None))
            start = k + 1
    L.append("  全镜像 dword==0x5519B0 出现次数: %d" % len(raws))
    L.append("  作为某地址+0x1C 槽的位置:")
    vft_bases = []
    for sec, va, base in raws:
        if base is None:
            continue
        cand = []
        ok = True
        for i in range(8):
            try:
                x = b.u32(base + i * 4)
            except Exception:
                ok = False
                break
            if not (0x401000 <= x <= 0x900000):
                ok = False
                break
            cand.append("%08X" % x)
        if ok:
            vft_bases.append(base)
            L.append("    vftable@%08X slots[0..7]=%s" % (base, ",".join(cand)))
    L.append("  含 0x5519B0 于 +0x1C 的虚表数: %d -> %s" % (
        len(vft_bases), ",".join("%08X" % x for x in sorted(set(vft_bases)))))

    L.append("")
    L.append("=" * 90)
    L.append("[2] audit_lib.sweep_calls: 0x5519B0 直接调用者")
    calls, jmps, stat = audit_lib.sweep_calls(b)
    L.append("  sweep 统计: %r" % stat)
    sites = sorted(calls.get(ADD, []))
    L.append("  直接调用者站点数: %d" % len(sites))
    for s in sites:
        L.append("    %08X (atlas归属=%s)" % (s, C.owner(s, "atlas")))

    L.append("")
    L.append("=" * 90)
    L.append("[3] 全镜像数据节中 dword 值 ∈ [0x8A0360,0x8A03D8) 的位置（存储的层指针）")
    stored = []
    for sec in b.sections:
        if sec["name"] == ".text":
            continue
        buf = b.pe.__data__[sec["raw"]:sec["raw"] + sec["rawsize"]]
        for k in range(0, len(buf) - 3, 4):
            v = struct.unpack("<I", buf[k:k + 4])[0]
            if LO <= v < HI:
                stored.append((sec["name"], sec["va"] + k, v))
    L.append("  命中数: %d" % len(stored))
    for sec, va, v in stored[:200]:
        L.append("    %s:%08X -> %08X (k=%d)" % (sec, va, v, (v - LO) // C.LAYER_ELEM))

    L.append("")
    L.append("=" * 90)
    L.append("[4] 142 个 call[reg+0x1C]：站点 | vptr reg 最后写 | ecx 最后写 | 是否含层常量")
    ins = C.text_insns()
    v = C.vas()

    def last_write(j, reg):
        r = ins[j]
        o = C.owner(r["va"], "atlas")
        lo = bisect.bisect_left(v, o[0]) if o else max(0, j - 120)
        ws = [k for k in range(lo, j)
              if ins[k]["ops"] and ins[k]["ops"][0]["kind"] == "reg"
              and ins[k]["ops"][0]["name"] == reg
              and ins[k]["mn"] not in ("cmp", "test", "push")]
        if not ws:
            return "NO-WRITE-IN-FUNC"
        return "%08X:%s %s" % (ins[ws[-1]]["va"], ins[ws[-1]]["mn"], ins[ws[-1]]["os"])

    sites = []
    for j, r in enumerate(ins):
        if r["mn"] != "call" or not r["ops"]:
            continue
        op = r["ops"][0]
        if op["kind"] == "mem" and op["base"] and (op["disp"] & 0xFFFFFFFF) == C.ADD_SLOT:
            sites.append((j, r, op["base"]))
    hit_layer = 0
    for j, r, reg in sites:
        ecxl = last_write(j, "ecx")
        vpl = last_write(j, reg)
        consts = []
        for k in range(max(0, j - 40), j + 1):
            for op in ins[k]["ops"]:
                if op["kind"] == "imm" and (LO <= (op["val"] & 0xFFFFFFFF) < HI):
                    consts.append("%08X" % (op["val"] & 0xFFFFFFFF))
                if op["kind"] == "mem" and (LO <= (op["disp"] & 0xFFFFFFFF) < HI):
                    consts.append("disp%08X" % (op["disp"] & 0xFFFFFFFF))
        flag = ""
        if consts:
            flag = "LAYER-CONST:" + ",".join(sorted(set(consts)))
            hit_layer += 1
        L.append("  %08X reg=%-4s vptr<=%s | ecx<=%s | %s" % (
            r["va"], reg, vpl, ecxl, flag))
    L.append("  含层常量的站点数: %d" % hit_layer)

    L.append("")
    L.append("=" * 90)
    L.append("[5] 层数组引用所在函数(atlas) 是否含 call[reg+0x1C]")
    chb_funcs = set()
    for j, r in enumerate(ins):
        has = False
        for op in r["ops"]:
            if op["kind"] == "imm" and (LO <= (op["val"] & 0xFFFFFFFF) < HI):
                has = True
            if op["kind"] == "mem" and (LO <= (op["disp"] & 0xFFFFFFFF) < HI):
                has = True
        if not has:
            continue
        o = C.owner(r["va"], "atlas")
        if o:
            chb_funcs.add(o[0])
    call1c_funcs = set()
    for j, r, reg in sites:
        o = C.owner(r["va"], "atlas")
        if o:
            call1c_funcs.add(o[0])
    for f in sorted(chb_funcs):
        c1c = [s["va"] for j, s, rg in sites
               if C.owner(s["va"], "atlas") and C.owner(s["va"], "atlas")[0] == f]
        L.append("  %08X : call[reg+0x1C]数=%d %s" % (
            f, len(c1c), ",".join("%08X" % x for x in c1c)))
    L.append("  chB函数数=%d  与call1c函数集交集=%s" % (
        len(chb_funcs), ",".join("%08X" % x for x in sorted(chb_funcs & call1c_funcs))))

    C.write_text(os.path.join(E, "w173_verify.txt"), L)
    print("verify written; vftables +0x1C=Add: %d; direct caller sites: %d; chA-layerconst: %d" %
          (len(vft_bases), len(sites), hit_layer))


if __name__ == "__main__":
    main()
