"""s3: family-wide byte analysis of the 35 candidate slots (34 coverage rows +
0x6805F0) plus a positive/negative control set.

Per slot it prints, from raw bytes only:
  * md5 of the body, body length up to the closing ret
  * detected backward jumps (= loops): back-edge addr, target addr, span
  * memory WRITE instructions inside the loop range, classified stack/non-stack
  * every call: address, kind (rel32 / IAT abs / vtable [reg+disp]) and target
  * every test/cmp on eax followed by a conditional jump (HRESULT checks)

Nothing here reads function_atlas.tsv or any audited artefact.
"""
import hashlib
import json

import capstone

import pe

SLOTS = ["0067FDF0", "0067FE70", "0067FEF0", "0067FF70", "0067FFF0",
         "00680070", "006800F0", "00680170", "006801F0", "00680270",
         "006802F0", "00680370", "006803F0", "00680470", "006804F0",
         "00680570", "006805F0", "00680670", "006806F0", "00680770",
         "006807F0", "00680870", "006808F0", "00680970", "006809F0",
         "00680A70", "00680AF0", "00680B70", "00680BF0", "00680C70",
         "00680CF0", "00680D70", "00680DF0", "00680E70", "00680EF0"]
SAMPLE = ["0067FDF0", "006800F0", "00680470", "006807F0", "00680B70", "00680EF0"]

# mnemonics whose first operand, when it is memory, is genuinely written
WRITE_MNEM = {
    "mov", "movzx", "movsx", "movsxd", "add", "adc", "sub", "sbb", "and",
    "or", "xor", "inc", "dec", "neg", "not", "shl", "shr", "sar", "sal",
    "rol", "ror", "rcl", "rcr", "xchg", "cmpxchg", "xadd", "stosb", "stosd",
    "stosw", "movsb", "movsd", "movsw", "bts", "btr", "btc", "seta", "setae",
    "setb", "setbe", "sete", "setg", "setge", "setl", "setle", "setne",
    "imul", "fstp", "fst", "fadd", "fmul", "lea",  # lea never writes mem
}
# lea must be excluded explicitly (its "memory" operand is an address)
NO_WRITE = {"lea", "cmp", "test", "nop", "prefetch"}

COND_JMP = {"ja", "jae", "jb", "jbe", "je", "jg", "jge", "jl", "jle",
            "jne", "jns", "jo", "jp", "js", "jz", "jnz", "jno", "jnp"}


def unit():
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = True
    return m


def body_insns(p, va, maxlen=0x80):
    """Linear sweep from va; stop after the first ret/ret-n that is followed
    by padding (0x90 / 0xCC / 0x00) or by the next slot boundary."""
    out = []
    for ins in unit().disasm(p.raw(va, maxlen), va):
        out.append(ins)
        if ins.mnemonic in ("ret", "retf") or ins.mnemonic.startswith("ret "):
            nxt = ins.address + ins.size
            pad = p.raw(nxt, 1)[0]
            if pad in (0x90, 0xCC, 0x00):
                break
    return out


def frame_uses_ebp(insns):
    for i in insns[:8]:
        if i.mnemonic == "mov" and i.op_str.replace(" ", "") == "ebp,esp":
            return True
    return False


def classify_mem(ins, ebp_frame):
    """-> list of (operand_index, base_reg, disp, is_stack, text)"""
    res = []
    for k, op in enumerate(ins.operands):
        if op.type != capstone.x86.X86_OP_MEM:
            continue
        base = ins.reg_name(op.mem.base) if op.mem.base else ""
        idx = ins.reg_name(op.mem.index) if op.mem.index else ""
        stack = base in ("esp", "rsp") or (base in ("ebp", "rbp") and ebp_frame)
        res.append((k, base, idx, op.mem.disp, stack,
                    f"[{base}{'+' + idx if idx else ''}"
                    f"{'+0x%x' % op.mem.disp if op.mem.disp else ''}]"))
    return res


def analyze(p, va, nbytes=0x80):
    insns = body_insns(p, va, nbytes)
    ebp_frame = frame_uses_ebp(insns)
    end = insns[-1].address + insns[-1].size
    body = p.raw(va, end - va)
    rec = dict(entry=va, md5=hashlib.md5(body).hexdigest(), length=end - va,
               n_insn=len(insns), ebp_frame=ebp_frame)
    # --- loops: backward conditional/unconditional jumps
    loops = []
    for i, ins in enumerate(insns):
        if not (ins.mnemonic.startswith("j") and ins.mnemonic not in ("jmp",)
                or ins.mnemonic == "jmp"):
            continue
        if not ins.operands or ins.operands[0].type != capstone.x86.X86_OP_IMM:
            continue
        tgt = ins.operands[0].imm
        if va <= tgt < ins.address:
            span = [x for x in insns if tgt <= x.address <= ins.address]
            loops.append(dict(back_edge=ins.address, mnem=ins.mnemonic,
                              target=tgt, n_body=len(span), span=span))
    rec["loops"] = []
    for lp in loops:
        writes = []
        for ins in lp["span"]:
            if ins.mnemonic in NO_WRITE or ins.mnemonic not in WRITE_MNEM:
                continue
            mems = classify_mem(ins, ebp_frame)
            if not mems:
                continue
            k, base, idx, disp, stack, txt = mems[0]
            if k != 0:            # only operand 0 is a destination
                continue
            writes.append(dict(addr=ins.address, mn=ins.mnemonic,
                               ops=ins.op_str, bytes=ins.bytes.hex(),
                               base=base, index=idx, disp=disp, stack=stack))
        # pushes inside the loop are stack writes too -- record them separately
        pushes = [x.address for x in lp["span"] if x.mnemonic == "push"]
        rec["loops"].append(dict(back_edge=lp["back_edge"], mnem=lp["mnem"],
                                 target=lp["target"], n_body=lp["n_body"],
                                 writes=writes, pushes=pushes,
                                 nonstack=[w for w in writes if not w["stack"]]))
    # --- calls
    calls = []
    for ins in insns:
        if ins.mnemonic != "call":
            continue
        op = ins.operands[0]
        d = dict(addr=ins.address, off=ins.address - va, bytes=ins.bytes.hex())
        if op.type == capstone.x86.X86_OP_IMM:
            d.update(kind="rel32", target=op.imm)
        elif op.type == capstone.x86.X86_OP_MEM:
            base = ins.reg_name(op.mem.base) if op.mem.base else ""
            idx = ins.reg_name(op.mem.index) if op.mem.index else ""
            if base == "" and idx == "":
                d.update(kind="iat_abs", slot=op.mem.disp)
            else:
                d.update(kind="vtable", base=base, index=idx, disp=op.mem.disp)
        calls.append(d)
    rec["calls"] = calls
    # --- eax checks
    checks = []
    for i, ins in enumerate(insns[:-1]):
        if ins.mnemonic in ("test", "cmp", "or") and ins.op_str.startswith("eax"):
            nx = insns[i + 1]
            if nx.mnemonic in COND_JMP:
                checks.append(dict(cmp=ins.address, cmp_off=ins.address - va,
                                   cmp_txt=f"{ins.mnemonic} {ins.op_str}",
                                   cmp_bytes=ins.bytes.hex(),
                                   jcc=nx.address, jcc_off=nx.address - va,
                                   jcc_mn=nx.mnemonic, jcc_bytes=nx.bytes.hex(),
                                   target=nx.operands[0].imm
                                   if nx.operands[0].type == capstone.x86.X86_OP_IMM else None))
    rec["eax_checks"] = checks
    rec["ret_va"] = end
    return rec


def main():
    p = pe.open_pe()
    recs = {}
    for s in SLOTS:
        recs[s] = analyze(p, int(s, 16))
    # controls: the 0045A640 precedent plus a known-good non-stack writer
    for c in ["0045A640", "00488080", "0045A680"]:
        recs[c] = analyze(p, int(c, 16))
    out = {}
    for s, r in recs.items():
        out[s] = r
        lp = r["loops"][0] if r["loops"] else None
        print(f"\n### {s}  0x{r['entry']:08X}  len={r['length']} "
              f"insn={r['n_insn']} md5={r['md5']}")
        if lp:
            print(f"  loop: back-edge 0x{lp['back_edge']:08X} ({lp['mnem']}) "
                  f"-> target 0x{lp['target']:08X}  body={lp['n_body']} insn")
            print(f"  loop-body writes (dst operand0 mem): {len(lp['writes'])}"
                  f"  non-stack: {len(lp['nonstack'])}")
            for w in lp["writes"]:
                tag = "STACK" if w["stack"] else "NON-STACK"
                print(f"    0x{w['addr']:08X} {w['mn']:<6} {w['ops']:<28} "
                      f"{w['bytes']:<20} {tag}")
            print(f"  pushes in loop: {len(lp['pushes'])} -> "
                  f"{[hex(a) for a in lp['pushes']]}")
        else:
            print("  loop: NONE")
        print(f"  calls: {len(r['calls'])}")
        for c in r["calls"]:
            if c["kind"] == "rel32":
                print(f"    0x{c['addr']:08X} +0x{c['off']:02X} E8 -> "
                      f"0x{c['target']:08X}  [{c['bytes']}]")
            elif c["kind"] == "iat_abs":
                print(f"    0x{c['addr']:08X} +0x{c['off']:02X} IAT slot "
                      f"0x{c['slot']:08X}  [{c['bytes']}]")
            else:
                print(f"    0x{c['addr']:08X} +0x{c['off']:02X} vt "
                      f"[{c['base']}+0x{c['disp']:x}]  [{c['bytes']}]")
        print(f"  eax checks: {len(r['eax_checks'])}")
        for c in r["eax_checks"]:
            print(f"    0x{c['cmp']:08X} +0x{c['cmp_off']:02X} {c['cmp_txt']:<14}"
                  f" [{c['cmp_bytes']}] -> 0x{c['jcc']:08X} +0x{c['jcc_off']:02X}"
                  f" {c['jcc_mn']} 0x{c['target']:08X}  [{c['jcc_bytes']}]")
    with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
              r"\TIEBREAK_ENGFAM\EVIDENCE\family_raw.json", "w") as f:
        json.dump(out, f, indent=1, default=lambda o: hex(o) if isinstance(o, int) else str(o))


if __name__ == "__main__":
    main()
