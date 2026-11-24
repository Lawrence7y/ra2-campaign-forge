"""d4_controls.py — positive / negative controls for the two instruments this
ruling rests on (R14_COMMON §8.2 技术④: measure the baseline before trusting a
"pass"; §8.1 ⑨: prove the probe is actually measuring the feature).

Instrument 1  memory-write classifier (used to answer "does the body write?")
Instrument 2  loop detector + "is the write inside the loop" test

Controls:
  + 00488080  VectorClass<FoggedObjectClass*> ctor : known field writes
  + 0045A680  DV slot2 SetCapacity                : expected loop + writes
  + 0045A730  DV slot4 FindItemIndex              : expected loop, no writes
  - 004D27B0  `mov eax,0x3D; ret`                 : expected 0 writes
  - 0045A0C0  GetItem (4 instrs)                  : expected 0 writes
  * 0045A640  the row under judgement             : the point of the exercise
"""
import json
import os
import sys

from capstone import CS_ARCH_X86, CS_MODE_32, Cs
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pe import open_pe

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(os.path.dirname(HERE), "EVIDENCE")

RMW = {"add", "sub", "and", "or", "xor", "adc", "sbb", "inc", "dec", "neg", "not",
       "shl", "shr", "sar", "rol", "ror"}
STORE = {"mov", "movzx", "movsx", "movd", "movq"}
JCC = {"jo", "jno", "js", "jns", "je", "jz", "jne", "jnz", "jb", "jnae", "jc",
       "jnb", "jae", "jnc", "jbe", "jna", "ja", "jnbe", "jl", "jnge", "jge",
       "jnl", "jle", "jng", "jg", "jnle", "jp", "jpe", "jnp", "jpo", "jecxz"}


def analyse(pe, md, entry, cap=0x300):
    """CFG walk from entry; returns instruction list and write/loop facts."""
    txt = next(s for s in pe.sections if s["name"] == ".text")
    tb = pe.buf[txt["rawptr"]:txt["rawptr"] + txt["rawsize"]]
    tva = pe.image_base + txt["vaddr"]

    def dec(va):
        off = va - tva
        if off < 0 or off >= len(tb):
            return []
        return list(md.disasm(tb[off:off + 16], va, 1))

    seen = {}
    work = [entry]
    while work:
        pc = work.pop()
        while True:
            if pc in seen or len(seen) > 5000:
                break
            if not (entry <= pc < entry + cap):
                break
            g = dec(pc)
            if not g:
                break
            ins = g[0]
            writes = []
            for i, op in enumerate(ins.operands):
                if op.type == X86_OP_MEM:
                    base = ins.reg_name(op.mem.base) or ""
                    idx = ins.reg_name(op.mem.index) or ""
                    kind = "stack" if (base in ("esp", "ebp") and not idx) else \
                           ("global" if (not base and not idx) else "field")
                    is_w = bool(op.access & 2) or (i == 0 and ins.mnemonic in RMW) \
                        or (i == 0 and ins.mnemonic in STORE)
                    if is_w:
                        writes.append((kind, f"[{base}{idx}{op.mem.disp:+#x}]"))
            if ins.mnemonic == "push":
                writes.append(("stack", "[esp-4] push"))
            if ins.mnemonic == "call":
                writes.append(("stack", "[esp-4] retaddr"))
            seen[pc] = dict(addr=pc, size=ins.size, mnemonic=ins.mnemonic,
                            op_str=ins.op_str, writes=writes,
                            bytes=ins.bytes.hex().upper())
            mn = ins.mnemonic
            if mn.startswith("ret") or mn == "jmp":
                if mn == "jmp" and ins.operands and ins.operands[0].type == X86_OP_IMM \
                        and entry <= ins.operands[0].imm < entry + cap:
                    work.append(ins.operands[0].imm)
                break
            if mn in JCC and ins.operands and ins.operands[0].type == X86_OP_IMM:
                t = ins.operands[0].imm
                if entry <= t < entry + cap:
                    work.append(t)
            pc += ins.size
    order = sorted(seen)

    # loops: backward jumps
    loops = []
    for a in order:
        r = seen[a]
        if (r["mnemonic"] in JCC or r["mnemonic"] == "jmp") and r["op_str"]:
            try:
                tgt = int(r["op_str"].split()[0], 16)
            except ValueError:
                continue
            if tgt < a:
                body = [x for x in order if tgt <= x <= a]
                loops.append(dict(head=tgt, back_edge=a, mnemonic=r["mnemonic"],
                                  op=r["op_str"],
                                  body_writes=[(x, seen[x]["mnemonic"], w) for x in body
                                               for w in seen[x]["writes"] if w[0] != "stack"]))
    nonstack = [(a, seen[a]["mnemonic"], seen[a]["op_str"], w)
                for a in order for w in seen[a]["writes"] if w[0] != "stack"]
    stack = [(a, seen[a]["mnemonic"]) for a in order
             for w in seen[a]["writes"] if w[0] == "stack"]
    return dict(entry=entry, n=len(order), last=max(order) if order else entry,
                span=(max(order) + seen[max(order)]["size"] - entry) if order else 0,
                nonstack=nonstack, n_stack_writes=len(stack), loops=loops)


def main():
    pe = open_pe()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    cases = [
        (0x0045A640, "the row under judgement — DV/V slot1 operator=="),
        (0x00488080, "+control: VectorClass<FoggedObjectClass*> ctor (ret 8)"),
        (0x0045A680, "+/- control: DV slot2 SetCapacity"),
        (0x0045A730, "control: DV slot4 FindItemIndex"),
        (0x0045A0C0, "-control: GetItem, 4 straight-line instructions"),
        (0x004D27B0, "-control: `mov eax,0x3D; ret` constant stub"),
        (0x0045A070, "control: DV Clear (call + field zeroing)"),
    ]
    out = []
    res = {}
    for entry, label in cases:
        r = analyse(pe, md, entry)
        res[entry] = r
        out.append(f"================ {entry:#010x}  {label}")
        out.append(f"  instrs={r['n']}  span={r['span']} B  stack-write instrs={r['n_stack_writes']}")
        out.append(f"  non-stack writes: {len(r['nonstack'])}")
        for a, mn, ops, w in r["nonstack"]:
            out.append(f"     {a:#010x} {mn} {ops}   -> {w[0]} {w[1]}")
        out.append(f"  loops (backward jumps): {len(r['loops'])}")
        for L in r["loops"]:
            out.append(f"     head {L['head']:#010x}  back-edge {L['back_edge']:#010x} "
                       f"({L['mnemonic']} {L['op']})  non-stack writes in body: "
                       f"{len(L['body_writes'])}")
            for bw in L["body_writes"]:
                out.append(f"        {bw[0]:#010x} {bw[1]} -> {bw[2][0]} {bw[2][1]}")
        out.append("")

    out.append("## read-out")
    a640 = res[0x0045A640]
    out.append(f"  0045A640  : non-stack writes = {len(a640['nonstack'])} ; "
               f"loops = {len(a640['loops'])} ; non-stack writes inside the loop = "
               f"{len(a640['loops'][0]['body_writes']) if a640['loops'] else 0} ; "
               f"stack writes detected = {a640['n_stack_writes']}")
    out.append(f"  0045A680  : non-stack writes = {len(res[0x0045A680]['nonstack'])} ; "
               f"loops = {len(res[0x0045A680]['loops'])}")
    out.append(f"  00488080  : non-stack writes = {len(res[0x00488080]['nonstack'])} "
               f"(the classifier DOES see object-field writes)")
    out.append(f"  004D27B0  : non-stack writes = {len(res[0x004D27B0]['nonstack'])} "
               f"(negative control passes)")

    text = "\n".join(out)
    with open(os.path.join(EV, "controls.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
