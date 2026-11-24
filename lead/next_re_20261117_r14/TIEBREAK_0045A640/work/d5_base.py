"""d5_base.py — baseline for the *broad* reading of D-42 ③b②.

The row under judgement has no non-stack write, no call, no jump table and no
memory-shape assertion.  Its only candidate ③b ground is "the body returns a
falsifiable bool via two distinct exit paths".  Before accepting that reading,
measure how discriminating it is: pick function starts mechanically (no
function_atlas.tsv), apply the predicate, and report the base rate
(R14_COMMON §8.2 技术④: report N/N only after measuring "would N random picks
also pass?").

Function-start heuristic (disclosed, atlas-free): an address A that directly
follows a decoded `ret`-family instruction, modulo 0x90/0xCC padding, and from
which at least 8 valid instructions decode.

Predicate B(c): the body has >=2 exit paths whose last write to AL/EAX is a
constant, and the constants differ.  (Approximation: the last 10 instructions
before each ret are scanned for the last AL/EAX-writing instruction; a
`xor al,al` / `mov al,imm` counts as a constant.  It can over-count when the
value comes from a merge point, so the reported rate is an UPPER bound.)
"""
import json
import os
import random
import sys

from capstone import CS_ARCH_X86, CS_MODE_32, Cs
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import open_pe

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(os.path.dirname(HERE), "EVIDENCE")

RMW = {"add", "sub", "and", "or", "xor", "adc", "sbb", "inc", "dec", "neg", "not"}
STORE = {"mov", "movzx", "movsx"}
JCC = {"jo", "jno", "js", "jns", "je", "jz", "jne", "jnz", "jb", "jnae", "jc",
       "jnb", "jae", "jnc", "jbe", "jna", "ja", "jnbe", "jl", "jnge", "jge",
       "jnl", "jle", "jng", "jg", "jnle", "jp", "jpe", "jnp", "jpo", "jecxz"}
SAMPLES = 300
SEED = 20261119


def main():
    pe = open_pe()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    txt = next(s for s in pe.sections if s["name"] == ".text")
    tb = pe.buf[txt["rawptr"]:txt["rawptr"] + txt["rawsize"]]
    tva = pe.image_base + txt["vaddr"]
    tend = tva + txt["rawsize"]

    def dec(va, n=1):
        off = va - tva
        if off < 0 or off >= len(tb):
            return []
        return list(md.disasm(tb[off:off + 16], va, n))

    # ---- linear sweep: collect ret instructions and their end addresses ----
    ret_ends = []
    pc = tva
    n_instr = 0
    while pc < tend:
        g = dec(pc)
        if not g:
            pc += 1
            continue
        ins = g[0]
        n_instr += 1
        if ins.mnemonic.startswith("ret"):
            ret_ends.append(pc + ins.size)
        pc += ins.size

    # ---- candidate function starts ---------------------------------------
    cand = []
    for e in ret_ends:
        a = e
        while a < tend and tb[a - tva] in (0x90, 0xCC):
            a += 1
        if a >= tend:
            continue
        g = list(md.disasm(tb[a - tva:a - tva + 32], a, 8))
        if len(g) >= 8 and all(x.size for x in g):
            cand.append(a)
    cand = sorted(set(cand))

    rng = random.Random(SEED)
    sample = rng.sample(cand, min(SAMPLES, len(cand)))

    def walk(entry, cap=0x500):
        seen = {}
        work = [entry]
        while work:
            p = work.pop()
            while True:
                if p in seen or len(seen) > 3000 or not (entry <= p < entry + cap):
                    break
                g = dec(p)
                if not g:
                    break
                ins = g[0]
                seen[p] = ins
                mn = ins.mnemonic
                if mn.startswith("ret"):
                    break
                if mn in JCC and ins.operands and ins.operands[0].type == X86_OP_IMM:
                    t = ins.operands[0].imm
                    if entry <= t < entry + cap:
                        work.append(t)
                if mn == "jmp":
                    if ins.operands and ins.operands[0].type == X86_OP_IMM \
                            and entry <= ins.operands[0].imm < entry + cap:
                        work.append(ins.operands[0].imm)
                    break
                p += ins.size
        return seen

    def const_return(seen):
        """distinct constants returned in AL/EAX over the exit paths"""
        order = sorted(seen)
        vals = set()
        for i, a in enumerate(order):
            ins = seen[a]
            if not ins.mnemonic.startswith("ret"):
                continue
            # scan back up to 10 instructions
            for b in reversed(order[max(0, i - 10):i]):
                j = seen[b]
                _, wregs = j.regs_access()
                names = {j.reg_name(r) for r in wregs}
                if not ({"al", "eax", "ax"} & names):
                    continue
                if j.mnemonic == "xor" and len(j.operands) == 2 \
                        and j.operands[0].type == X86_OP_REG \
                        and j.operands[1].type == X86_OP_REG \
                        and j.operands[0].reg == j.operands[1].reg:
                    vals.add(0)
                    break
                if j.mnemonic in ("mov", "movzx", "movsx") and j.operands \
                        and j.operands[-1].type == X86_OP_IMM:
                    vals.add(j.operands[-1].imm & 0xFFFFFFFF)
                    break
                break
        return vals

    def has_nonstack_write(seen):
        for a, ins in seen.items():
            for i, op in enumerate(ins.operands):
                if op.type != X86_OP_MEM:
                    continue
                base = ins.reg_name(op.mem.base) or ""
                idx = ins.reg_name(op.mem.index) or ""
                if base in ("esp", "ebp") and not idx:
                    continue
                if bool(op.access & 2) or (i == 0 and ins.mnemonic in RMW) \
                        or (i == 0 and ins.mnemonic in STORE):
                    return True
        return False

    def has_loop(seen):
        for a, ins in seen.items():
            if (ins.mnemonic in JCC or ins.mnemonic == "jmp") and ins.op_str:
                try:
                    t = int(ins.op_str.split()[0], 16)
                except ValueError:
                    continue
                if t < a:
                    return True
        return False

    n_bool = n_bool_nowrite = n_loop = n_loop_nowrite = 0
    rows = []
    for e in sample:
        seen = walk(e)
        if not seen:
            continue
        v = const_return(seen)
        b = len(v) >= 2
        nw = has_nonstack_write(seen) is False
        lp = has_loop(seen)
        n_bool += b
        n_bool_nowrite += (b and nw)
        n_loop += lp
        n_loop_nowrite += (lp and nw)
        rows.append(dict(entry=e, n=len(seen), returns=sorted(v), bool_ret=b,
                         no_nonstack_write=nw, loop=lp))

    N = len(rows)
    summary = dict(
        candidate_starts=len(cand), sweep_instrs=n_instr, sampled=N, seed=SEED,
        bool_two_const_returns=n_bool, bool_rate=round(n_bool / N, 4),
        bool_and_no_nonstack_write=n_bool_nowrite,
        bool_nowrite_rate=round(n_bool_nowrite / N, 4),
        loop=n_loop, loop_rate=round(n_loop / N, 4),
        loop_and_no_nonstack_write=n_loop_nowrite,
        loop_nowrite_rate=round(n_loop_nowrite / N, 4))

    L = ["# baseline for the broad reading of ③b②  ('a falsifiable bool return is enough')", ""]
    L.append(f"# .text sweep instrs          {n_instr}")
    L.append(f"# candidate function starts   {len(cand)}   (atlas-free: post-ret + padding, >=8 valid instrs)")
    L.append(f"# sampled                      {N}   (seed {SEED})")
    L.append("")
    L.append(f"# predicate B  : >=2 exit paths whose last AL/EAX write is a distinct constant")
    L.append(f"#                {n_bool}/{N} = {n_bool/N:.2%}   (upper bound; see docstring)")
    L.append(f"# predicate B ∧ no non-stack write  (exactly 0045A640's shape)")
    L.append(f"#                {n_bool_nowrite}/{N} = {n_bool_nowrite/N:.2%}")
    L.append(f"# has a loop                  {n_loop}/{N} = {n_loop/N:.2%}")
    L.append(f"# loop ∧ no non-stack write   {n_loop_nowrite}/{N} = {n_loop_nowrite/N:.2%}")
    L.append("")
    L.append("# first 25 sampled rows: entry, instrs, distinct constant returns, flags")
    for r in rows[:25]:
        L.append(f"  {r['entry']:#010x} n={r['n']:<4} returns={r['returns']} "
                 f"bool={r['bool_ret']} no_write={r['no_nonstack_write']} loop={r['loop']}")

    text = "\n".join(L)
    with open(os.path.join(EV, "baseline_bool_3b2.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    with open(os.path.join(HERE, "base.json"), "w", encoding="utf-8") as f:
        json.dump(dict(summary=summary, rows=rows), f, indent=1)
    print(text)


if __name__ == "__main__":
    main()
