#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Live-vtable witness checker (D-43(A) wide reading, error source 23).
For a target vt, find every write `mov dword ptr [...], vt` / `mov [reg], vt`
in .text, identify the enclosing function, and classify live(ctor) vs dead(atexit dtor).
Writes work/ files only. Read-only on target.
Usage: python livevt.py <vt_hex> [<vt_hex>...]
"""
import os, sys, struct
import s09lib8 as L
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_GRP_CALL

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
WORK = os.path.join(R14, 'S09_KPROVED8', 'work')

# atexit registration: push <fn>; call 0x7C978A  (dtor table installer)
ATEXIT = 0x7C978A


def enclosing_func(insns, site):
    """Heuristic: walk backward to nearest function prologue (push ebp; mov ebp,esp OR
    push ebx/esi/edi chain after a ret/int3/nop padding). Use a simple scan."""
    addrs = [i.address for i in insns]
    idx = None
    for k, a in enumerate(addrs):
        if a == site:
            idx = k
            break
    if idx is None:
        return None
    # walk back to nearest ret/aligned padding boundary
    start = 0
    for k in range(idx, -1, -1):
        i = insns[k]
        if i.mnemonic.startswith('ret'):
            start = k + 1
            break
    return insns[start].address


def main():
    # full linear sweep once
    off = L.TEXT['raw']
    insns = list(L.MD.disasm(L.DATA[off:off + L.TEXT['vsize']], L.TEXT_LO))
    # map address->index
    idx = {i.address: k for k, i in enumerate(insns)}
    for vta in sys.argv[1:]:
        vt = int(vta, 16)
        lines = []
        lines.append('=== vt 0x%08X ===' % vt)
        # atexit-registered dtor functions
        dtors = set()
        for k, i in enumerate(insns):
            if i.mnemonic == 'call' and L.imm_ops(i) and L.imm_ops(i)[0] == ATEXIT:
                # look back for push imm (the dtor)
                for j in range(max(0, k - 6), k):
                    p = insns[j]
                    if p.mnemonic == 'push' and L.imm_ops(p):
                        dtors.add(L.imm_ops(p)[0])
        lines.append('atexit dtor functions: %d' % len(dtors))
        writes = []
        for i in insns:
            if i.mnemonic != 'mov' or not i.operands:
                continue
            dst, src = i.operands[0], i.operands[-1]
            # mov [mem/reg], imm(vt)
            if src.type == X86_OP_IMM and src.imm == vt and dst.type in (X86_OP_MEM, X86_OP_REG):
                ef = enclosing_func(insns, i.address)
                kind = 'DTOR' if ef in dtors else 'CTOR/other'
                writes.append((i.address, i.bytes.hex(), i.mnemonic, i.op_str, ef, kind))
        lines.append('writes of vt as immediate: %d' % len(writes))
        for w in writes:
            lines.append('  site=%08X %-20s %s %s ; enclosing=%s kind=%s' % (
                w[0], w[1], w[2], w[3], ('%08X' % w[4]) if w[4] else '?', w[5]))
        out = os.path.join(WORK, 'LIVEVT_%08X.txt' % vt)
        with open(out, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        print('wrote', out, 'writes', len(writes))


if __name__ == '__main__':
    main()
