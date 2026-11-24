#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rtti_scan.py — 扫描所有 RTTI COL/TD, 反查 vtable 与类名。"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
import wbase as W

def inline_name(td):
    o = W.va2off(td + 8)
    if o is None:
        return None
    b = bytearray()
    for i in range(256):
        c = W.DATA[o + i] if o + i < len(W.DATA) else 0
        if c == 0 or not (32 <= c < 127):
            break
        b.append(c)
    s = bytes(b).decode("latin1")
    return s

def scan():
    hits = []
    # 扫 .data + .rdata 中每个 4 字节对齐位置, 看它是否是 TD(+8 有合法类名)
    for name, v, vs, raw, rsz in W.SECS:
        if name not in (".rdata", ".data"):
            continue
        start = v
        end = v + max(vs, rsz) - 4
        # TD 的 vftable[0] 应指向一个合法地址(.rdata 的 RTTI vt)
        # 简化: 检查 +8 处是否为 .?AV/.?AU 类名串
        for va in range(start, end, 4):
            o = W.va2off(va + 8)
            if o is None:
                continue
            if W.DATA[o:o+4] == b".?AV" or W.DATA[o:o+4] == b".?AU":
                nm = inline_name(va)
                if nm and nm.startswith((".?AV", ".?AU")):
                    hits.append((va, nm))
    return hits

def find_vtables_for_td(td):
    """找所有 COL 使 [COL+0xC]==td, 再找所有 vtable 使 [vt-4]==COL"""
    cols = []
    for name, v, vs, raw, rsz in W.SECS:
        if name not in (".rdata", ".data"):
            continue
        for va in range(v, v + max(vs, rsz) - 0x10, 4):
            if W.rd32(va + 0xC) == td:
                cols.append(va)
    vts = []
    # vtable 定义处: 任意 X 使 [X-4]==COL (即 vtable[-1]=COL)
    for col in cols:
        for name, v, vs, raw, rsz in W.SECS:
            if name not in (".rdata", ".data"):
                continue
            for va in range(v + 4, v + max(vs, rsz) - 4, 4):
                if W.rd32(va - 4) == col:
                    # 候选 vtable 首槽必须落在 .text
                    first = W.rd32(va)
                    if first and W.in_text(first):
                        vts.append((col, va))
    return cols, vts

if __name__ == "__main__":
    want = sys.argv[1] if len(sys.argv) > 1 else None
    hits = scan()
    print("TD-like descriptors:", len(hits))
    if want:
        hits = [h for h in hits if want.lower() in h[1].lower()]
    for td, nm in sorted(hits, key=lambda x: x[1]):
        cols, vts = find_vtables_for_td(td)
        vtstr = ", ".join("vt@0x%x" % vt for _, vt in vts) if vts else "-"
        print("TD=0x%08X %-52s %s" % (td, nm, vtstr))
