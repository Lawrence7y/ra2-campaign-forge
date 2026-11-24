#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump bytes + disassembly for the selected 100 UNDECIDABLE rows, read-only."""
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
RES2WORK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_RESIDUAL_2\work"
sys.path.insert(0, RES2WORK)
import res2_common as C

SEL = os.path.join(os.path.dirname(HERE), "SELECTED_100.tsv")

def load_sel():
    rows = []
    with open(SEL, encoding="utf-8") as f:
        h = f.readline().rstrip("\n").split("\t")
        for ln in f:
            if not ln.strip():
                continue
            p = ln.rstrip("\n").split("\t")
            rows.append(dict(zip(h, p)))
    return rows

def disasm_seq(pe, va, span=96, n=10):
    d = pe.try_read(va, span)
    if not d:
        return []
    md = C.md32(True)
    out = []
    for ins in md.disasm(d, va):
        if ins.id == 0:
            out.append((ins.address, ".byte", "0x%02x" % ins.bytes[0], ins.size))
        else:
            out.append((ins.address, ins.mnemonic, ins.op_str, ins.size))
        if len(out) >= n:
            break
    return out

def main():
    pe = C.PE()
    rows = load_sel()
    print("PE .text = [%08X, %08X)  IB=%08X" % (pe.tlo, pe.thi, pe.IB))
    for i, r in enumerate(rows, 1):
        a = int(r["address"], 16)
        raw = pe.try_read(a, 16)
        hx = raw.hex(" ") if raw else ""
        seq = disasm_seq(pe, a, 96, 10)
        parts = []
        for (ad, mn, op, sz) in seq:
            if mn == ".byte":
                parts.append(".byte")
            else:
                parts.append(mn + " " + op)
        body = " | ".join(parts)
        ev = r["evidence"]
        tail = ev.split("tail=")[-1].split(";")[0] if "tail=" in ev else "?"
        print("%3d %s fb=%s pred=%-4s tail=%-4s  raw=%-47s" % (i, r["address"], r["first_byte"], r["predecessor"], tail, hx))
        print("      %s" % body[:300])

if __name__ == "__main__":
    main()
