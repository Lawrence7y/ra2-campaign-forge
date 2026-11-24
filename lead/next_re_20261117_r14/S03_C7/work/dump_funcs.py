#!/usr/bin/env python3
"""Dump full disassembly of target functions with entry-relative offsets (+0xNN)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import common as C

ENTRIES = [0x004325C0, 0x00473C00, 0x00473CE0, 0x00473FC0, 0x0047AAB0,
           0x00631D30, 0x0065CCA0, 0x0065D1F0, 0x00432050]

# known callee names (from prior cards / IAT / established facts)
KNOWN = {
    0x7C93E8: 'fclose', 0x7D5408: 'fopen', 0x7CA090: 'memmove',
    0x7C8B3D: 'free', 0x7E11A0: 'WriteFile', 0x7E1208: 'FindFirstFileA',
    0x65CDD0: 'RawFileClass::Write(slot12)', 0x65CF00: 'RawFileClass::Seek(slot10)',
    0x65CB50: 'RawFileClass::Open(slot7)', 0x65CCE0: 'RawFileClass::Read(slot9)',
    0x431DD0: 'CDFile::flush/bufclose', 0x65CAC0: 'RawFile::ReOpen(slot2)',
    0x7C978A: 'atexit', 0x4C9150: 'abstract_GetSize_stub',
}

def annotate(ins):
    extra = []
    if ins.mnemonic in ('call', 'jmp', 'je', 'jne', 'jz', 'jnz', 'jg', 'jl', 'jge', 'jle', 'ja', 'jb', 'jae', 'jbe', 'js', 'jns', 'jo', 'jno', 'jp', 'jnp'):
        for op in ins.operands:
            if op.type == C.capstone.x86.X86_OP_IMM:
                t = op.imm
                if t in KNOWN:
                    extra.append('=>' + KNOWN[t])
    return ' '.join(extra)

base = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C7\EVIDENCE"
for e in ENTRIES:
    # determine extent via atlas size (read from rtti_inherit_extents)
    import json
    j = json.load(open(base + r"\rtti_inherit_extents.json", encoding='utf-8'))['entries'][f"{e:08X}"]
    lo = int(j['ext_lo'], 16); hi = int(j['ext_hi'], 16)
    insns = list(C.disasm_range(lo, hi))
    lines = [f"# DISASM entry={e:08X} range=[{lo:08X},{hi:08X}) size={hi-lo} n_insn={len(insns)}"]
    for ins in insns:
        off = ins.address - e
        a = annotate(ins)
        lines.append(f"+0x{off:03X} {ins.address:08X}: {ins.bytes.hex():<20} {ins.mnemonic} {ins.op_str}".rstrip() + (f"  {a}" if a else ''))
    fn = base + rf"\dis_{e:08X}.txt"
    open(fn, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print(f"{e:08X}: {len(insns)} insns -> dis_{e:08X}.txt")
print("done")
