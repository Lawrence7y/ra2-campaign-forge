#!/usr/bin/env python3
# R130 r130a: full-.text scan for "table iteration" loops, to answer R129 todo (1):
#   is 0x6bc342's loop (mov esi,<head> / add esi,8 / cmp esi,<bound> / jl) unique,
#   or are there sibling tables of the same shape elsewhere?
# Memory discipline: disasm_lite streaming only; bounded deque of recent insns;
# no detail=True anywhere; no list of the whole .text.
import io
import json
import os
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r130/r130a_tables.json'

BACK_JCC = {
    'jl', 'jle', 'jb', 'jbe', 'jne', 'jns', 'jno', 'jnp', 'js', 'jo', 'jp',
    'jna', 'jnb', 'jnae', 'jnbe', 'jnc', 'jc', 'jz', 'jnz',
}
JCC_ALL = BACK_JCC | {'jmp'}

REG32 = ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp']


def load_text():
    pe = pefile.PE(EXE, fast_load=True)
    for s in pe.sections:
        if s.Name.rstrip(b'\x00') == b'.text':
            va = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
            data = s.get_data()
            return va, data, pe
    raise SystemExit('.text not found')


def imm32_of(op_str):
    """Return int if operand is a bare 0x... constant (no registers/mem)."""
    s = op_str.strip()
    if not s.startswith('0x'):
        return None
    try:
        return int(s, 16)
    except ValueError:
        return None


def scan():
    va, data, pe = load_text()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = False
    md.skipdata = True
    recent = []          # deque-ish list of (addr, mnem, op_str, size)
    n_insn = 0
    loops = []           # back-edge candidates
    for ins in md.disasm_lite(data, va):
        addr, size, mnem, op_str = ins
        n_insn += 1
        if mnem in BACK_JCC:
            tgt = imm32_of(op_str)
            if tgt is not None and tgt < addr:
                # collect body from tgt..addr using recent window
                body = [r for r in recent if tgt <= r[0] < addr]
                if body:
                    loops.append({
                        'loop_head': tgt, 'back_edge': addr, 'jcc': mnem,
                        'body_len': len(body),
                        'body': [(b[0], b[1], b[2]) for b in body],
                    })
        recent.append((addr, mnem, op_str, size))
        # prune: keep only last 0x2000 bytes of coverage
        while recent and recent[0][0] < addr - 0x2000:
            recent.pop(0)
    return va, data, loops, n_insn, pe


def classify(loop):
    """A 'table iteration' loop: add REG,imm + cmp REG,immbound, same reg, upper bound."""
    add_c = []
    cmp_c = []
    for a, m, o in loop['body']:
        if m == 'add':
            parts = [x.strip() for x in o.split(',')]
            if len(parts) == 2 and parts[0] in REG32:
                v = imm32_of(parts[1])
                if v is not None:
                    add_c.append((a, parts[0], v))
        elif m == 'cmp':
            parts = [x.strip() for x in o.split(',')]
            if len(parts) == 2 and parts[0] in REG32:
                v = imm32_of(parts[1])
                if v is not None:
                    cmp_c.append((a, parts[0], v))
    for (aa, ar, step) in add_c:
        for (ca, cr, bound) in cmp_c:
            if ar == cr:
                return {
                    'reg': ar, 'step': step, 'bound': bound,
                    'add_at': aa, 'cmp_at': ca,
                    'loop_head': loop['loop_head'], 'back_edge': loop['back_edge'],
                    'jcc': loop['jcc'], 'body_len': loop['body_len'],
                    'span': bound - loop['loop_head'],
                }
    return None


def main():
    va, data, loops, n_insn, pe = scan()
    hits = [h for h in (classify(l) for l in loops) if h]
    hits.sort(key=lambda h: h['loop_head'])
    # image mapped ranges, to say whether a head/bound is a real VA or not
    rec = {
        'text_va': hex(va), 'text_raw_len': len(data), 'insn_count': n_insn,
        'back_edge_total': len(loops), 'table_loops_total': len(hits),
        'hits': [],
    }
    for h in hits:
        rec['hits'].append({
            'loop_head': hex(h['loop_head']), 'bound': hex(h['bound']),
            'step': h['step'], 'span': h['span'],
            'span_div_step': (h['span'] / h['step']) if h['step'] else None,
            'reg': h['reg'], 'add_at': hex(h['add_at']), 'cmp_at': hex(h['cmp_at']),
            'back_edge': hex(h['back_edge']), 'jcc': h['jcc'],
            'body_len': h['body_len'],
        })
    with io.open(OUT, 'w', encoding='utf-8') as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print('insn_count', n_insn)
    print('back_edges', len(loops))
    print('table_loops', len(hits))
    for h in rec['hits']:
        print(h['loop_head'], 'bound', h['bound'], 'step', h['step'],
              'span', hex(h['span']), 'reg', h['reg'], 'jcc', h['jcc'])


if __name__ == '__main__':
    main()
