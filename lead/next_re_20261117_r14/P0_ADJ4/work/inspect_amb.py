#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspect ambiguous rows + control pool subkinds. Read-only."""
import os, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
RES2WORK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_RESIDUAL_2\work"
sys.path.insert(0, RES2WORK)
import res2_common as C

RESID = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_RESIDUAL\RESIDUAL_ADJUDICATION.tsv"

def show(pe, va, before=24, after=160):
    raw = pe.try_read(va - before, before + after)
    if not raw:
        print("  no bytes"); return
    md = C.md32(True)
    # decode the window but mark target
    for ins in md.disasm(raw, va - before):
        mark = " <<<TARGET" if ins.address == va else ""
        mn = ins.mnemonic if ins.id else ".byte"
        op = ins.op_str if ins.id else ""
        print("  %08X  %-10s %-30s%s" % (ins.address, mn, op, mark))
        if ins.address >= va + after - 8:
            break

def main():
    pe = C.PE()
    for va in (0x402F80, 0x407080, 0x40A600, 0x405AB0, 0x4063A0):
        print("=== %08X ===" % va)
        show(pe, va)
        print()

    # control pool: NOT_FUNC subkinds
    rows = []
    with open(RESID, encoding="utf-8") as f:
        h = f.readline().rstrip("\n").split("\t")
        for ln in f:
            if not ln.strip(): continue
            p = ln.rstrip("\n").split("\t")
            rows.append(dict(zip(h, p)))
    nf = [r for r in rows if r["verdict"] == "NOT_FUNC"]
    fu = [r for r in rows if r["verdict"] == "FUNC"]
    print("NOT_FUNC subkinds:", dict(collections.Counter(r["subkind"] for r in nf)))
    print("FUNC c4b sample:")
    for r in fu[:8]:
        print("  ", r["addr"], r["subkind"], r["evidence"][:90])

if __name__ == "__main__":
    main()
