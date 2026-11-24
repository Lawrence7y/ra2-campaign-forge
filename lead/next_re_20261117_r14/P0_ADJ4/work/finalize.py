#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-ADJ4 final generator: ADJ_100.tsv / EVIDENCE / coverage_delta.tsv / UNKNOWNS / DISAGREE.
Read-only on gamemd.exe. Uses criterion.Engine (byte-only, atlas-independent channels)."""
import os, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
RES2WORK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_RESIDUAL_2\work"
sys.path.insert(0, RES2WORK); sys.path.insert(0, HERE)
import res2_common as C
from criterion import Engine

OUT = os.path.dirname(HERE)  # P0_ADJ4
EVID = os.path.join(OUT, "EVIDENCE")
os.makedirs(EVID, exist_ok=True)

def load_sel():
    rows = []
    with open(os.path.join(OUT, "SELECTED_100.tsv"), encoding="utf-8") as f:
        h = f.readline().rstrip("\n").split("\t")
        for ln in f:
            if not ln.strip(): continue
            rows.append(dict(zip(h, ln.rstrip("\n").split("\t"))))
    return rows

def head_desc(f):
    """Map head mnemonic + first bytes to a one-line static-inferred semantics."""
    mn = f["first_mn"]
    if mn.startswith("f") or mn in ("fld","fild","fstp","fcom","fdiv","fmul","fsub"):
        return "FPU leaf: load/const op -> store global -> ret"
    if mn == "xor":
        return "zero-init: xor reg,reg -> store -> ret"
    if mn in ("mov","movzx","movsx","lea"):
        return "getter/short leaf: mov/lea reg,[this+off|global] -> ret"
    if mn in ("test","cmp"):
        return "compare leaf: test/cmp -> setcc/branch -> ret"
    if mn == "push":
        return "thiscall helper: push reg; body; balanced pop; ret"
    if mn in ("add","sub","inc","dec"):
        return "adjust/arith leaf: add|sub reg,imm; ret|jmp (thunk-like)"
    if mn in ("sete","setne","setz","setnz","seta","setb","setg","setl"):
        return "flag-to-byte leaf: setcc -> ret"
    return "short leaf function (static shape)"

def crit_reason(f):
    good = []
    if f["g1a"]: good.append("A16")
    if f["g1b"]: good.append("P=%s" % f["pred_kind"])
    if f["c1"]: good.append("H!")
    if f["c2"]: good.append("!JCC")
    if f["c3"]: good.append("HS=%s" % f["first_mn"])
    if f["c4"]: good.append("SAVEBAL")
    if f["c5"]: good.append("TERM=%s" % f["term"])
    return "+".join(good)

def main():
    pe = C.PE()
    eng = Engine(pe)
    rows = load_sel()
    recs = []
    for r in rows:
        va = int(r["address"], 16)
        f = eng.features(va)
        recs.append((r, f, va))

    # --- ADJ_100.tsv: address / verdict / criteria_basis / key_bytes ---
    p = os.path.join(OUT, "ADJ_100.tsv")
    with open(p, "w", encoding="utf-8", newline="") as fout:
        fout.write("address\tverdict\tcriteria_basis\tkey_bytes\n")
        for r, f, va in recs:
            raw = pe.try_read(va, 16)
            hx = raw.hex(" ") if raw else ""
            basis = ("FUNC:" if f["func"] else "NOT_FUNC:") + crit_reason(f)
            fout.write("%s\t%s\t%s\t%s\n" % (r["address"], "FUNC" if f["func"] else "NOT_FUNC", basis, hx))

    # --- EVIDENCE/ADJUDICATION_DETAIL.tsv: full per-row byte evidence ---
    p = os.path.join(EVID, "ADJUDICATION_DETAIL.tsv")
    with open(p, "w", encoding="utf-8", newline="") as fout:
        cols = ["address", "verdict", "align16", "pred_kind", "pred_mn", "first_byte", "first_mn",
                "G1a", "G1b", "C1", "C2", "C3", "C4", "C5", "term", "term_va", "n_ins",
                "jcc_target", "pre_push_restore", "bytes16", "disasm12", "enum_evidence"]
        fout.write("\t".join(cols) + "\n")
        for r, f, va in recs:
            raw = pe.try_read(va, 16)
            hx = raw.hex(" ") if raw else ""
            data = pe.try_read(va, 64)
            seq = []
            if data:
                for ins in C.md32(True).disasm(data, va):
                    mn = ins.mnemonic + " " + ins.op_str if ins.id else ".byte"
                    seq.append(mn)
                    if len(seq) >= 12: break
            disasm = " | ".join(seq)
            ppr = ("%08X:%s %s" % f["pre_push_restore"]) if f["pre_push_restore"] else "-"
            vals = [r["address"], "FUNC" if f["func"] else "NOT_FUNC",
                    "Y" if va % 16 == 0 else "N", f["pred_kind"], f["pred_mn"],
                    "0x%02x" % f["fb"], f["first_mn"],
                    int(f["g1a"]), int(f["g1b"]), int(f["c1"]), int(f["c2"]), int(f["c3"]),
                    int(f["c4"]), int(f["c5"]), f["term"] or "-",
                    ("%08X" % f["term_va"]) if f["term_va"] else "-", f["n_ins"],
                    int(va in eng.jcc_targets), ppr, hx, disasm, r["evidence"]]
            fout.write("\t".join(str(x) for x in vals) + "\n")

    # --- EVIDENCE/NOT_FUNC_DETAIL.tsv: the 5 NOT_FUNC with full reason ---
    p = os.path.join(EVID, "NOT_FUNC_DETAIL.tsv")
    with open(p, "w", encoding="utf-8", newline="") as fout:
        fout.write("address\tfailed_channels\tfirst_insn\tcontext\n")
        for r, f, va in recs:
            if f["func"]: continue
            fails = []
            for k in ("g1a","g1b","c1","c2","c3","c4","c5"):
                if not f[k]: fails.append(k)
            ctx = ("jcc-target" if va in eng.jcc_targets else "not-jcc-target")
            if f["pre_push_restore"]:
                ctx += "; restore-before-push@%08X" % f["pre_push_restore"][0]
            fout.write("%s\t%s\t%s\t%s\n" % (r["address"], ",".join(fails), r["first_insn"], ctx))

    # --- coverage_delta.tsv: FUNC rows only, static-inferred semantics ---
    p = os.path.join(OUT, "coverage_delta.tsv")
    n_delta = 0
    with open(p, "w", encoding="utf-8", newline="") as fout:
        fout.write("entry(hex8)\tsubsystem(Sxx)\tname\tone_line_semantics\tgrade\tevidence_path\n")
        for r, f, va in recs:
            if not f["func"]: continue
            sem = "[静态推断] " + head_desc(f)
            fout.write("%s\tS22\tsub_%s\t%s\t[静态推断]\tEVIDENCE/ADJUDICATION_DETAIL.tsv#%s\n" % (
                r["address"], r["address"], sem, r["address"]))
            n_delta += 1

    # summary
    nf = sum(1 for r, f, va in recs if f["func"])
    print("ADJ_100.tsv: 100 rows, FUNC=%d NOT_FUNC=%d" % (nf, 100-nf))
    print("coverage_delta.tsv: %d rows (all FUNC, grade=[静态推断], subsystem=S22)" % n_delta)
    print("EVIDENCE/: ADJUDICATION_DETAIL.tsv (100), NOT_FUNC_DETAIL.tsv (%d)" % (100-nf))

if __name__ == "__main__":
    main()
