#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/re_gap_spysat_deep.py
Detailed disassembly and analysis of Gap Generator, PsychicReveal, RevealArea, and SpySat routines.
"""
import sys, os, struct, json
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import capstone as _cs

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
SYM = r"D:\Project\ra2-campaign-forge\out\reverse\symbols.json"
IMAGE_BASE = 0x400000

def load_sections():
    data = open(EXE, 'rb').read()
    e_lfanew = struct.unpack_from('<I', data, 0x3C)[0]
    nsec = struct.unpack_from('<H', data, e_lfanew + 6)[0]
    opt_size = struct.unpack_from('<H', data, e_lfanew + 20)[0]
    sec_off = e_lfanew + 24 + opt_size
    secs = []
    for i in range(nsec):
        off = sec_off + i * 40
        name = data[off:off + 8].rstrip(b'\0').decode('ascii', 'replace')
        vsize, vaddr, rawsize, rawptr = struct.unpack_from('<IIII', data, off + 8)
        chars = struct.unpack_from('<I', data, off + 36)[0]
        secs.append(dict(name=name, va=IMAGE_BASE + vaddr, vsize=vsize,
                         raw=data[rawptr:rawptr + rawsize], exec=bool(chars & 0x20000000)))
    return secs

def load_image(secs):
    lo = min(s['va'] for s in secs)
    hi = max(s['va'] + s['vsize'] for s in secs)
    img = bytearray(hi - lo)
    for s in secs:
        o = s['va'] - lo
        n = min(len(s['raw']), s['vsize'])
        img[o:o + n] = s['raw'][:n]
    return img, lo

secs = load_sections()
image, base = load_image(secs)
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

names = {}
if os.path.exists(SYM):
    with open(SYM) as f:
        syms = json.load(f)
    for fn in syms.get('functions', []):
        names[int(fn['address'], 16)] = fn.get('name', '')
    for cname, cinfo in syms.get('classes', {}).items():
        vfuncs = cinfo.get('vfuncs', [])
        for i, vf in enumerate(vfuncs):
            if vf:
                vfa = int(vf, 16)
                if vfa not in names:
                    names[vfa] = f"{cname}::v[{i}]"

def read_bytes(va, n):
    o = va - base
    return bytes(image[o:o+n])

def read_u32(va):
    return struct.unpack_from('<I', read_bytes(va, 4))[0]

def disasm_func(start_va, max_insn=200):
    print(f"\n========================================================")
    print(f"Disassembly of 0x{start_va:08X} ({names.get(start_va, 'Unknown')})")
    print(f"========================================================")
    code = read_bytes(start_va, max_insn * 15)
    count = 0
    for insn in md.disasm(code, start_va):
        extra = ""
        if insn.mnemonic in ('call', 'jmp'):
            for op in insn.operands:
                if op.type == _cs.x86.X86_OP_IMM:
                    target = op.imm & 0xFFFFFFFF
                    tname = names.get(target, "")
                    extra = f"  ; target: 0x{target:08X} {tname}"
        print(f"{insn.address:08X}  {insn.bytes.hex():<20} {insn.mnemonic:<7} {insn.op_str:<30} {extra}")
        count += 1
        if count >= max_insn:
            break
        # Heuristic stop on ret if no open branches
        if insn.mnemonic in ('ret', 'retf') and count > 10:
            # check next bytes for int3 or nop padding
            next_b = read_bytes(insn.address + insn.size, 4)
            if next_b[0] in (0xCC, 0x90):
                break

if __name__ == '__main__':
    targets = [
        0x004555D0, # IsGeneratingGap
        0x004556D0, # CreateGap (Super)
        0x00455820, # CreateGap (Main)
        0x00455980, # DestroyGap (Aux)
        0x00455A80, # DestroyGap (Main)
        0x00487160, # CellClass::sub_487160
        0x00487170, # CellClass::sub_487170
        0x00487180, # CellClass::sub_487180
        0x00487690, # CellClass::+0x134 getter?
        0x00487950, # CellClass::IsShrouded
        0x00586360, # MapClass::IsCellShrouded
        0x00508F60, # SpySat state machine
        0x0050BD10, # SpySat teardown
        0x00577AB0, # Reshroud
        0x00577D90, # RevealArea3
    ]
    for t in targets:
        disasm_func(t, 120)
