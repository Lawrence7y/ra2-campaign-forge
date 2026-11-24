#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探索脚本：枚举 A-E 五通道候选，报告计数与重叠。不写正式交付。"""
import os
import sys
import struct
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from resid_common import (EXE, SHA256, sha256_file, RawPE, Sweep, Atlas, md_new,
                          ATLAS, COVERAGE, PROBE, OUTSIDE, disasm_at, predecessor,
                          trailing_pad, JCC, TERM_KINDS)


def load_entries(path, col=0, skip_header=True):
    out = set()
    with open(path, encoding="utf-8", errors="replace") as f:
        if skip_header:
            f.readline()
        for ln in f:
            if not ln.strip():
                continue
            tok = ln.rstrip("\n").split("\t")
            try:
                v = int(tok[col], 16)
            except Exception:
                continue
            out.add(v)
    return out


def in_text(v, TLO, THI):
    return TLO <= v < THI


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("sha256:", sha256_file(), "MATCH" if sha256_file() == SHA256 else "MISMATCH")
    pe = RawPE()
    t = pe.byname[".text"]
    TLO = pe.imagebase + t["va"]
    THI = TLO + t["vsize"]
    sw = Sweep(pe, TLO, THI)
    at = Atlas()
    print(".text=[%08X,%08X) sweep=%d insn atlas=%d rows overlaps=%d"
          % (TLO, THI, sw.n, at.n, at._overlaps))

    cov = load_entries(COVERAGE, 0)
    probe = load_entries(PROBE, 0)
    outside = load_entries(OUTSIDE, 0)
    print("coverage=%d probe=%d outside=%d" % (len(cov), len(probe), len(outside)))

    # ---- Channel A: E8/E9 rel32 targets ----
    chA = set()
    for i in range(sw.n):
        b = sw.bytes_list[i]
        if len(b) == 5 and b[0] in (0xE8, 0xE9):
            rel = struct.unpack("<i", b[1:5])[0]
            tgt = sw.starts[i] + 5 + rel
            if in_text(tgt, TLO, THI) and not at.in_atlas(tgt):
                chA.add(tgt)
    print("Channel A (E8/E9 rel32, not in atlas):", len(chA))

    # ---- Channel B: EB rel8 targets ----
    chB = set()
    for i in range(sw.n):
        b = sw.bytes_list[i]
        if len(b) == 2 and b[0] == 0xEB:
            rel = struct.unpack("<b", b[1:2])[0]
            tgt = sw.starts[i] + 2 + rel
            if in_text(tgt, TLO, THI) and not at.in_atlas(tgt):
                chB.add(tgt)
    print("Channel B (EB rel8, not in atlas):", len(chB))

    # ---- Channel C: vftable slots self-derived ----
    r = pe.byname[".rdata"]
    rlo = pe.imagebase + r["va"]
    buf = pe.read(rlo, r["rawsize"])
    nw = len(buf) // 4
    words = list(struct.unpack_from("<%dI" % nw, buf, 0))

    def col_name(colp):
        if not (pe.imagebase <= colp < pe.imagebase + pe.sizeofimage):
            return None
        d = pe.try_read(colp, 16)
        if len(d) < 16:
            return None
        sig, off, cd, tdp = struct.unpack("<IIII", d)
        if sig not in (0, 1):
            return None
        if not (pe.imagebase <= tdp < pe.imagebase + pe.sizeofimage):
            return None
        nm = pe.try_read(tdp + 8, 256)
        if not nm:
            return None
        z = nm.find(b"\x00")
        nm = nm[:z] if z > 0 else nm
        if nm.startswith(b".?AV") or nm.startswith(b".?AU"):
            return nm
        return None

    runs = []
    i = 0
    while i < nw:
        if in_text(words[i], TLO, THI):
            j = i
            while j < nw and in_text(words[j], TLO, THI):
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1
    tables = []
    bare = []
    for i, j in runs:
        va = rlo + 4 * i
        colp = words[i - 1] if i >= 1 else 0
        cls = col_name(colp)
        rec = dict(vt=va, n=j - i, slots=words[i:j])
        (tables if cls else bare).append(rec)
    print("Channel C: vftable COL-verified=%d tables / %d slots; bare=%d runs / %d slots"
          % (len(tables), sum(x["n"] for x in tables), len(bare), sum(x["n"] for x in bare)))
    chC = set()
    for tb in tables:
        for S in tb["slots"]:
            if in_text(S, TLO, THI) and not at.in_atlas(S):
                chC.add(S)
    chC_bare = set()
    for tb in bare:
        for S in tb["slots"]:
            if in_text(S, TLO, THI) and not at.in_atlas(S):
                chC_bare.add(S)
    print("Channel C distinct not-in-atlas targets (COL tables):", len(chC))
    print("Channel C distinct not-in-atlas targets (bare runs):", len(chC_bare))

    # ---- Channel D: forward/orphan scan ----
    chD = set()
    chD_all = set()
    for A in range((TLO + 15) & ~15, THI, 16):
        if at.in_atlas(A):
            continue
        pr = predecessor(pe, sw, A)
        if pr["kind"] not in TERM_KINDS:
            continue
        raw3 = pe.read(A, 3)
        prologue = raw3 and (raw3[0] == 0x55 or
                             (len(raw3) > 1 and raw3[0] in (0x83, 0x81) and raw3[1] == 0xEC))
        first = disasm_at(pe, A, n=3, span=24)
        fmn = first[0][0] if first else ".byte"
        # leaf shape: body >=2B and ends with ret/jmp (checked later in adjudication)
        if not prologue:
            # allow leaf shape candidates too (will adjudicate)
            pass
        if fmn in JCC:
            continue
        if fmn == ".byte":
            continue
        chD_all.add(A)
        if prologue:
            chD.add(A)
    print("Channel D (16-align, prev term, non-JCC):", len(chD_all), "with prologue:", len(chD))

    # ---- unions ----
    allcand = chA | chB | chC | chC_bare | chD_all | chD
    print("Union all channels (not in atlas):", len(allcand))
    # after dedup vs coverage/probe/outside
    residual = allcand - cov - probe - outside
    print("Residual (minus coverage/probe/outside):", len(residual))
    print("  by channel (exclusive contribution after dedup):")
    print("    A only:", len((chA - cov - probe - outside)))
    print("    B only:", len((chB - cov - probe - outside)))
    print("    C COL only:", len((chC - cov - probe - outside)))
    print("    C bare only:", len((chC_bare - cov - probe - outside)))
    print("    D (prev term+nonJCC) only:", len((chD_all - cov - probe - outside)))
    print("    D with prologue only:", len((chD - cov - probe - outside)))

    # overlaps of residual with coverage categories
    print("\ncheck: are the 476 outside entries all in coverage?",
          len(outside & cov), "of", len(outside))
    print("check: chC vs outside:", len(chC & outside), "of", len(chC))
    print("check: chC vs cov:", len(chC & cov))
    print("check: chD_all vs outside:", len(chD_all & outside))
    print("check: chD_all vs cov:", len(chD_all & cov))
    print("check: chA vs outside:", len(chA & outside), "chA vs cov:", len(chA & cov))
    print("check: chB vs outside:", len(chB & outside), "chB vs cov:", len(chB & cov))

    # write residual set to a temp file for inspection
    with open(os.path.join(HERE, "_explore_residual.txt"), "w", encoding="utf-8") as f:
        for x in sorted(residual):
            f.write("%08X\n" % x)


if __name__ == "__main__":
    main()
