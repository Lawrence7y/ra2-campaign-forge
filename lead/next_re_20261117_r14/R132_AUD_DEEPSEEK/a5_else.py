#!/usr/bin/env python3
"""R132 task A5 detail: else-block self-containment + jump classification."""
import json
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
t = [s for s in pe.sections if s.Name.rstrip(b"\x00") == b".text"][0]
TEXT_VA = IB + t.VirtualAddress
TEXT_SZ = min(t.Misc_VirtualSize, t.SizeOfRawData)
raw = open(EXE, "rb").read()
CODE = raw[t.PointerToRawData:t.PointerToRawData + TEXT_SZ]
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

JCC = ("jo jno js jns je jz jne jnz jb jnae jc jnb jae jnc jbe jna ja jnbe "
       "jl jnge jge jnl jle jng jg jnle jp jpe jnp jpo jcxz jecxz loop loope loopne").split()


def cfg(entry):
    seen, work, hi, lo = {}, [entry], entry, entry
    order = []
    while work:
        a = work.pop()
        if a in seen or not (TEXT_VA <= a < TEXT_VA + TEXT_SZ):
            continue
        ins = next(md.disasm(CODE[a - TEXT_VA:a - TEXT_VA + 16], a, 1), None)
        if ins is None:
            continue
        seen[a] = (ins.mnemonic, ins.op_str, ins.size)
        order.append(a)
        e = a + ins.size
        hi = max(hi, e); lo = min(lo, a)
        if ins.mnemonic.startswith("ret"):
            continue
        if ins.mnemonic in JCC:
            work.append(int(ins.op_str, 16)); work.append(e)
        elif ins.mnemonic == "jmp":
            work.append(int(ins.op_str, 16))
        else:
            work.append(e)
    return seen, order, lo, hi


res = {}
for tag, entry in (("A", 0x6BEDB0), ("B", 0x41C250)):
    seen, order, lo, hi = cfg(entry)
    lin = 0
    a = entry
    while True:
        ins = next(md.disasm(CODE[a - TEXT_VA:a - TEXT_VA + 16], a, 1))
        lin += ins.size; a += ins.size
        if ins.mnemonic.startswith("ret"):
            break
    boundary = a
    seen2, order2, lo2, hi2 = cfg(boundary)
    # jumps out of else block?
    esc = []
    for x in order2:
        m, ops, sz = seen2[x]
        if m in JCC or m == "jmp":
            tgt = int(ops, 16)
            if not (lo2 <= tgt < hi2):
                esc.append({"at": hex(x), "mnem": m, "target": hex(tgt)})
    res[tag] = {
        "cfg_len": hi - entry, "first_ret_len": lin, "boundary": hex(boundary),
        "else_len": hi2 - lo2, "else_lo": hex(lo2), "else_hi": hex(hi2),
        "else_insn_count": len(order2),
        "else_escape_jumps": esc,
        "else_insns": [{"addr": hex(x), "mnem": seen2[x][0], "op": seen2[x][1]} for x in sorted(order2)],
        "cfg_insn_count": len(order),
        "total_gap": (hi - entry) - lin,
    }
    print(tag, {k: v for k, v in res[tag].items() if k not in ("else_insns",)})
    print("   else insns:", [(hex(x), seen2[x][0], seen2[x][1]) for x in sorted(order2)])

json.dump(res, open("a5_else.json", "w"), indent=1)
