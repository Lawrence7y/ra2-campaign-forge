"""d1_body.py — disassemble 0x0045A640 from raw bytes with a self-written CFG
walk (no function_atlas.tsv entry+size involved) and classify every memory
access as stack / global / object-field.

Output: EVIDENCE/body_disasm.txt  (human)  +  work/body.json (machine)

Why a CFG walk instead of a linear sweep: the question "is this function 62 or
63 bytes" and "does the loop exist" both depend on the function *extent*, and
taking that from atlas entry+size would be exactly the single-source channel
the card forbids.  We therefore follow branch targets, stop following
unconditional jumps that leave the body, and stop at ret.
"""
import json
import os
import sys

from capstone import (CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM, CS_OP_REG,
                      Cs)
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_REG_EBP, X86_REG_ESP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import open_pe

ENTRY = 0x0045A640
HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(os.path.dirname(HERE), "EVIDENCE")

RMW = {"add", "sub", "and", "or", "xor", "adc", "sbb", "inc", "dec", "neg",
       "not", "shl", "shr", "sar", "rol", "ror", "xadd"}
JCC = {"jo", "jno", "js", "jns", "je", "jz", "jne", "jnz", "jb", "jnae", "jc",
       "jnb", "jae", "jnc", "jbe", "jna", "ja", "jnbe", "jl", "jnge", "jge",
       "jnl", "jle", "jng", "jg", "jnle", "jp", "jpe", "jnp", "jpo", "jcxz",
       "jecxz"}
WRITE_ONLY = {"mov", "movzx", "movsx", "lea", "movd", "movq"}


def classify_mem(insn, op):
    """Return (kind, text) for a capstone mem operand."""
    base = insn.reg_name(op.mem.base) or ""
    idx = insn.reg_name(op.mem.index) or ""
    disp = op.mem.disp
    if base in ("esp", "ebp") and not idx:
        if base == "esp":
            return "stack", f"[esp{disp:+#x}]" if disp else "[esp]"
        return "stack", f"[ebp{disp:+#x}]" if disp else "[ebp]"
    if not base and not idx:
        return "global", f"[{disp & 0xFFFFFFFF:#010x}]"
    parts = [base] if base else []
    if idx:
        parts.append(f"{idx}*{op.mem.scale}")
    inner = "+".join(parts)
    if disp:
        inner += f"{disp:+#x}"
    return "field", f"[{inner}]"


def walk(text_va, text_bytes, md):
    """CFG walk. Returns dict addr -> (size, mnemonic, op_str, raw)."""
    seen = {}
    work = [ENTRY]
    while work:
        pc = work.pop()
        if pc in seen:
            continue
        limit = 0
        while True:
            limit += 1
            if limit > 400:
                raise SystemExit(f"runaway block at {pc:#x}")
            if pc not in range(0x401000, 0x7DF38D):
                break
            off = pc - text_va
            code = text_bytes[off:off + 16]
            got = list(md.disasm(code, pc, 1))
            if not got:
                print(f"  !! undecodable at {pc:#010x}", file=sys.stderr)
                break
            ins = got[0]
            if pc in seen:
                break
            seen[pc] = (ins.size, ins.mnemonic, ins.op_str, bytes(ins.bytes))
            mn = ins.mnemonic
            if mn.startswith("ret") or mn in ("jmp", "ljmp"):
                # unconditional transfer: only follow jmp targets that stay
                # inside the plausible body window (self-contained loops)
                if mn == "jmp" and ins.operands and ins.operands[0].type == CS_OP_IMM:
                    tgt = ins.operands[0].imm
                    if ENTRY <= tgt < ENTRY + 0x100:
                        work.append(tgt)
                break
            if mn in JCC:
                if ins.operands and ins.operands[0].type == CS_OP_IMM:
                    tgt = ins.operands[0].imm
                    if ENTRY <= tgt < ENTRY + 0x100:
                        work.append(tgt)
                        pc = pc + ins.size
                        continue
                    else:
                        # fallthrough continues, target outside body
                        pc = pc + ins.size
                        continue
                pc += ins.size
                continue
            pc += ins.size
    return seen


def main():
    pe = open_pe()
    txt = next(s for s in pe.sections if s["name"] == ".text")
    text_va = pe.image_base + txt["vaddr"]
    text_bytes = pe.buf[txt["rawptr"]:txt["rawptr"] + txt["rawsize"]]

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    insns = walk(text_va, text_bytes, md)
    order = sorted(insns)

    rows = []
    for a in order:
        size, mn, ops, raw = insns[a]
        got = list(md.disasm(raw, a, 1))[0]
        rec = dict(addr=a, off=a - ENTRY, size=size, bytes=raw.hex().upper(),
                   mnemonic=mn, op_str=ops, writes=[], reads=[])
        # explicit operands
        for i, op in enumerate(got.operands):
            if op.type == X86_OP_MEM:
                kind, txtop = classify_mem(got, op)
                is_w = (got.regs_access()[1] and op.access & 2) or \
                       (i == 0 and mn in RMW) or (i == 0 and mn in WRITE_ONLY)
                if is_w:
                    rec["writes"].append(dict(kind=kind, op=txtop,
                                              cls="RMW" if mn in RMW else "W"))
                else:
                    rec["reads"].append(dict(kind=kind, op=txtop))
            elif op.type == X86_OP_REG:
                rec.setdefault("regops", []).append(
                    ("W" if op.access & 2 else "R") + got.reg_name(op.reg))
        # implicit stack traffic
        if mn == "push":
            rec["writes"].append(dict(kind="stack", op="[esp-4] (push)", cls="implicit"))
        if mn in ("call",):
            rec["writes"].append(dict(kind="stack", op="[esp-4] (call retaddr)", cls="implicit"))
        if mn == "pop":
            rec["reads"].append(dict(kind="stack", op="[esp] (pop)", cls="implicit"))
        # transfer annotations
        if mn in JCC or mn in ("jmp", "call"):
            if got.operands and got.operands[0].type == CS_OP_IMM:
                rec["target"] = got.operands[0].imm
                rec["target_kind"] = ("internal" if ENTRY <= got.operands[0].imm < ENTRY + 0x100 else "external")
        rows.append(rec)

    body_end = max(a + r["size"] for a, r in zip(order, rows))
    nonstack = [r for r in rows if any(w["kind"] != "stack" for w in r["writes"])]

    meta = dict(entry=ENTRY, last_insn=order[-1], body_len=body_end - ENTRY,
                n_instr=len(rows), nonstack_write_insns=len(nonstack),
                body_hex=pe.bytes_at(ENTRY, body_end - ENTRY).hex().upper())

    # ---------- human dump ----------
    L = []
    L.append(f"# 0045A640 body — self-written CFG walk, capstone 5.0.7 (32-bit)")
    L.append(f"# exe SHA-256 {pe.sha256}")
    L.append(f"# atlas NOT consulted (extent from CFG walk only)")
    L.append(f"# body 0x{ENTRY:08X}..0x{body_end:08X}  len={body_end-ENTRY} B  "
             f"instrs={len(rows)}")
    L.append("")
    L.append(f"{'addr':>10} {'off':>7} {'sz':>2}  {'bytes':<24} {'insn':<40} writes")
    L.append("-" * 118)
    for r in rows:
        ws = "; ".join(f"{w['op']}({w['kind']},{w['cls']})" for w in r["writes"]) or "-"
        tgt = ""
        if "target" in r:
            tgt = f"  -> {r['target']:#010x} [{r['target_kind']}]"
        L.append(f"{r['addr']:#010x} {r['off']:+7d} {r['size']:>2}  "
                 f"{r['bytes']:<24} {r['mnemonic']+' '+r['op_str']:<40} {ws}{tgt}")
    L.append("")
    L.append("## non-stack writes (object field / global)")
    if nonstack:
        for r in nonstack:
            L.append(f"  {r['addr']:#010x} (+{r['off']:#x}) {r['mnemonic']} {r['op_str']} :: "
                     + "; ".join(f"{w['op']} {w['kind']}" for w in r["writes"]))
    else:
        L.append("  <NONE>")
    L.append("")
    L.append("## raw bytes")
    L.append(pe.hexdump(ENTRY, body_end - ENTRY))
    txtout = "\n".join(L)
    with open(os.path.join(EV, "body_disasm.txt"), "w", encoding="utf-8") as f:
        f.write(txtout + "\n")
    with open(os.path.join(HERE, "body.json"), "w", encoding="utf-8") as f:
        json.dump(dict(meta=meta, rows=rows), f, indent=1)
    print(txtout)


if __name__ == "__main__":
    main()
