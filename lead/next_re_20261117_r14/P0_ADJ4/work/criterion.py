#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-ADJ4 criterion engine (self-written, byte-only).

Criterion PI (all must hold to adjudicate FUNC):
  G1 (given by ENUM): 16B aligned, predecessor in {nop,ret,jmp,int3}, not in atlas/coverage,
      fails (c4a|leaf) form filter.
  C1 head-not-branch : first byte NOT in {E8,E9,EB} (call/jmp rel -- never a function head).
  C2 not-jcc-target  : address is NOT the destination of any conditional jump / loop
      (0x70-0x7f, 0x0f80-0x0f8f, E0-E3) found in the full .text sweep -> not an internal label.
  C3 head-shape      : first decoded instruction is a data/prologue opcode
      (mov/lea/xor/test/cmp/add/sub/push/FPU), NOT {pop,leave,ret,nop,int3,jmp,call}.
  C4 save-before-restore : linear decode from A: before the first push/sub-esp there is no
      pop/leave/add-esp,imm>=4  (callee cannot restore what it never saved).
  C5 self-contained  : within 512 bytes linear decode (skipdata=True) reaches a terminator
      (ret/retn/jmp) and no invalid byte (.byte) before it.

FUNC iff C1&C2&C3&C4&C5 ; otherwise NOT_FUNC.
All channels are pure byte decode + control-flow target scan; NONE uses atlas entry+size.
"""
import os, sys, re, struct, collections
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
RES2WORK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_RESIDUAL_2\work"
sys.path.insert(0, RES2WORK)
import res2_common as C

SEL = os.path.join(os.path.dirname(HERE), "SELECTED_100.tsv")
RESID = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_RESIDUAL\RESIDUAL_ADJUDICATION.tsv"

# head-shape allow-list (mnemonics that can begin a leaf/simple function)
HEAD_OK = {
    "mov", "movzx", "movsx", "lea", "xor", "or", "and", "test", "cmp", "add", "sub",
    "inc", "dec", "neg", "not", "push", "imul", "shl", "shr", "sar", "rol", "ror",
    "fld", "fild", "fstp", "fst", "fcom", "fcomp", "fldz", "fld1", "fldpi", "fnop",
    "fadd", "fsub", "fmul", "fdiv", "fchs", "fabs", "fnstcw", "fldcw", "fprem", "fucom",
    "fucomi", "fcomip", "sete", "setne", "setz", "setnz", "seta", "setb", "setg", "setl",
    "movsd", "movss", "cvtsi2sd", "cvttsd2si", "pxor", "movd", "movq",
}
HEAD_BAD = {"pop", "leave", "ret", "retn", "retf", "nop", "int3", "jmp", "call", "hlt"}
JCC_MN = set(C.JCC)

def load_sel():
    rows = []
    with open(SEL, encoding="utf-8") as f:
        h = f.readline().rstrip("\n").split("\t")
        for ln in f:
            if not ln.strip(): continue
            rows.append(dict(zip(h, ln.rstrip("\n").split("\t"))))
    return rows

def load_resid():
    rows = []
    with open(RESID, encoding="utf-8") as f:
        h = f.readline().rstrip("\n").split("\t")
        for ln in f:
            if not ln.strip(): continue
            rows.append(dict(zip(h, ln.rstrip("\n").split("\t"))))
    return rows

class Engine:
    def __init__(self, pe):
        self.pe = pe
        md = C.md32(True)
        self.jcc_targets = set()
        self.all_targets = set()
        self.starts = []
        self.mns = []
        buf = pe.data[pe.secs[".text"]["raw"]: pe.secs[".text"]["raw"] + pe.secs[".text"]["rawsize"]]
        for ins in md.disasm(buf, pe.tlo):
            if not ins.id:
                continue
            self.starts.append(ins.address)
            self.mns.append(ins.mnemonic)
            if ins.mnemonic in JCC_MN or ins.mnemonic.startswith("loop"):
                m = re.search(r"0x([0-9a-fA-F]+)", ins.op_str)
                if m:
                    self.jcc_targets.add(int(m.group(1), 16))
            m2 = re.search(r"0x([0-9a-fA-F]+)", ins.op_str)
            if ins.mnemonic in ("call", "jmp") and m2:
                self.all_targets.add(int(m2.group(1), 16))
        self.startset = set(self.starts)

    def predecessor_kind(self, va):
        """Decode candidate instruction whose end == va, in [va-15,va). Byte-only."""
        pe = self.pe
        best = None
        for s in range(va - 15, va):
            if s < pe.tlo:
                continue
            d = pe.try_read(s, 16)
            if not d:
                continue
            md = C.md32(True)
            for ins in md.disasm(d, s):
                if ins.id and ins.address + ins.size == va:
                    mn = ins.mnemonic
                    kind = ("nop" if mn == "nop" else "ret" if mn.startswith("ret")
                            else "jmp" if mn == "jmp" else "int3" if mn == "int3" else "other")
                    cand = (0 if s in self.startset else 1, -ins.size, s, kind, mn)
                    if best is None or cand < best:
                        best = cand
                break
        if best is None:
            return "none", "?"
        return best[3], best[4]

    def features(self, va):
        pe = self.pe
        raw4 = pe.try_read(va, 8)
        fb = raw4[0] if raw4 else -1
        # G1a (alignment) / G1b (predecessor terminator) -- now explicit channels
        g1a = (va % 16 == 0)
        pred_kind, pred_mn = self.predecessor_kind(va)
        g1b = pred_kind in ("nop", "ret", "jmp", "int3")
        # C1
        c1 = fb not in (0xE8, 0xE9, 0xEB)
        # C2: jcc target (global scan)
        c2 = va not in self.jcc_targets
        # decode linear sequence from va, up to 512 bytes
        data = pe.try_read(va, 512)
        seq = []
        if data:
            md = C.md32(True)
            for ins in md.disasm(data, va):
                seq.append((ins.address, ins.mnemonic if ins.id else ".byte", ins.op_str, ins.size, ins.id))
                if ins.address - va >= 512:
                    break
        first_mn = seq[0][1] if seq else "?"
        # C3
        c3 = first_mn in HEAD_OK and first_mn not in HEAD_BAD
        # C4: pop/before-push invariant over decoded seq
        pre_push_restore = None
        saw_push = False
        term_idx = None
        invalid_before_term = False
        for i, (ad, mn, op, sz, iid) in enumerate(seq):
            # terminator detection
            if mn.startswith("ret") or mn == "jmp":
                if term_idx is None:
                    term_idx = i
                break
            if iid == 0:
                if term_idx is None:
                    invalid_before_term = True
                continue
            is_push = mn.startswith("push")
            is_subesp = (mn == "sub" and op.startswith("esp,"))
            is_pop = mn.startswith("pop") or mn == "leave"
            is_addesp = (mn == "add" and op.startswith("esp,"))
            if (is_push or is_subesp):
                saw_push = True
            if (is_pop or is_addesp) and not saw_push and pre_push_restore is None:
                pre_push_restore = (ad, mn, op)
        c4 = pre_push_restore is None
        # C5: terminator reached, no invalid byte before it
        c5 = (term_idx is not None) and (not invalid_before_term)
        func = g1a and g1b and c1 and c2 and c3 and c4 and c5
        return dict(fb=fb, first_mn=first_mn, g1a=g1a, g1b=g1b, pred_kind=pred_kind,
                    pred_mn=pred_mn, c1=c1, c2=c2, c3=c3, c4=c4, c5=c5,
                    func=func, pre_push_restore=pre_push_restore,
                    term=(seq[term_idx][1] if term_idx is not None else None),
                    term_va=(seq[term_idx][0] if term_idx is not None else None),
                    n_ins=len(seq))

def main():
    pe = C.PE()
    eng = Engine(pe)
    print("jcc_targets total =", len(eng.jcc_targets), " all branch targets =", len(eng.all_targets))
    rows = load_sel()
    res = []
    for r in rows:
        va = int(r["address"], 16)
        f = eng.features(va)
        res.append((r, f))
    nf = [x for x in res if not x[1]["func"]]
    print("\n== NOT_FUNC among 100 = %d ==" % len(nf))
    for r, f in nf:
        why = []
        if not f["g1a"]: why.append("G1a:unaligned")
        if not f["g1b"]: why.append("G1b:pred=%s" % f["pred_mn"])
        if not f["c1"]: why.append("C1:first=%02X" % f["fb"])
        if not f["c2"]: why.append("C2:jcc-target")
        if not f["c3"]: why.append("C3:head=%s" % f["first_mn"])
        if not f["c4"]: why.append("C4:restore@%s" % (f["pre_push_restore"][0] if f["pre_push_restore"] else "?"))
        if not f["c5"]: why.append("C5:no-term/invalid")
        print("  %s  %-45s %s" % (r["address"], ";".join(why), r["first_insn"]))
    print("\nFUNC = %d / NOT_FUNC = %d" % (100-len(nf), len(nf)))

    # ---- controls ----
    rr = load_resid()
    fu = [r for r in rr if r["verdict"] == "FUNC"]
    nfu = [r for r in rr if r["verdict"] == "NOT_FUNC"]
    # deterministic pick: 5 FUNC evenly spaced; 5 NOT_FUNC evenly spaced
    def pick(lst, n):
        out = []
        for k in range(n):
            idx = (k * len(lst)) // n
            out.append(lst[idx])
        return out
    pos = pick(fu, 5)
    neg = pick(nfu, 5)
    print("\n== POS controls (known FUNC) ==")
    pos_pass = 0
    for r in pos:
        va = int(r["addr"], 16); f = eng.features(va)
        ok = f["func"]
        pos_pass += ok
        print("  %s %s head=%-8s g1a=%d g1b=%d c1=%d c2=%d c3=%d c4=%d c5=%d -> %s" % (
            r["addr"], r["subkind"], f["first_mn"], f["g1a"], f["g1b"],
            f["c1"], f["c2"], f["c3"], f["c4"], f["c5"],
            "PASS" if ok else "FAIL"))
    print("  POS pass = %d/5" % pos_pass)
    print("\n== NEG controls (known NOT_FUNC) ==")
    neg_pass = 0
    for r in neg:
        va = int(r["addr"], 16); f = eng.features(va)
        ok = (not f["func"])
        neg_pass += ok
        print("  %s %-14s head=%-8s g1a=%d g1b=%d c1=%d c2=%d c3=%d c4=%d c5=%d -> %s" % (
            r["addr"], r["subkind"], f["first_mn"], f["g1a"], f["g1b"],
            f["c1"], f["c2"], f["c3"], f["c4"], f["c5"],
            "PASS" if ok else "FAIL"))
    print("  NEG pass = %d/5" % neg_pass)

if __name__ == "__main__":
    main()
