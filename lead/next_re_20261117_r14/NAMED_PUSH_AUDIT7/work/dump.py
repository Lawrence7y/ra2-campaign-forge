"""AUDIT7: dump bodies + call/imm-ref analysis per row."""
import sys, json
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work")
from core import *
from probe import ROWS, body

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work"


def dump(entry):
    ins = body(entry)
    lines = []
    for i in ins:
        t = i.mnemonic + (' ' + i.op_str if i.op_str else '')
        lines.append(f"{i.address:08X}  {i.bytes.hex(' '):<24} {t}")
    return ins, lines


def callsites(target):
    """all direct call/jmp sites to target across .text (linear sweep, cached)."""
    import os, pickle
    cache = os.path.join(OUT, 'sweep.pkl')
    if not os.path.exists(cache):
        idx = {}
        o = va2off(TEXT_LO)
        end = va2off(TEXT_HI)
        for insn in md.disasm(DATA[o:end], TEXT_LO):
            if insn.mnemonic in ('call', 'jmp') and insn.operands and insn.operands[0].type == 2:
                idx.setdefault(insn.operands[0].imm, []).append((insn.address, insn.mnemonic))
        pickle.dump(idx, open(cache, 'wb'))
    else:
        idx = pickle.load(open(cache, 'rb'))
    return idx.get(target, [])


if __name__ == '__main__':
    for entry, sub, name, slot, vtb in ROWS:
        ins, lines = dump(entry)
        p = f"{OUT}\\body_{entry:08X}.txt"
        open(p, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
        print(f"{entry:08X} {sub} {name}: {len(ins)} insns, skip={sum(1 for i in ins if i.id==0)} -> {p}")
        print("   direct calls from entry:", sorted({hex(o.imm) for i in ins if i.mnemonic == 'call' and i.operands and i.operands[0].type == 2 for o in i.operands}))
        cs = callsites(entry)
        print(f"   direct call-sites to entry ({len(cs)}):", [(hex(a), m) for a, m in cs[:10]])
