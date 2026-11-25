#!/usr/bin/env python3
# R130 r130b v3: scan for "data-table iteration" loops, single aligned forward pass.
#
# Shape wanted (R129 found exactly one such loop at 0x6bc34d over table 0x7f3710):
#   mov  <reg>, <HEAD>      ; table head, may be HOISTED just before the loop head
#   <loop head>:
#      ... body ...
#      add <reg>, <STEP>
#      cmp <reg>, <BOUND>
#      jcc <loop head>      ; conditional back-edge, cmp immediately before it
#   with (BOUND - HEAD) % STEP == 0 and 1 <= count <= 4096.
#
# Why a single forward pass with a lookback deque: decoding a window from an
# arbitrary start address desynchronises (it lands mid-instruction), which is exactly
# how v2 produced a false "0 hits" on a loop we know exists. The forward sweep gives
# instruction boundaries that are consistent, so the lookback slice is aligned.
#
# Memory: disasm_lite generator, bounded deque, no detail=True, no whole-file list.
import collections
import io
import json
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = '/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT = '/home/t628/projects/ra2-campaign-forge/_r130/r130b_tables.json'

BACK_JCC = {
    'jl', 'jle', 'jb', 'jbe', 'jne', 'jns', 'jno', 'jnp', 'js', 'jo', 'jp',
    'jna', 'jnb', 'jnae', 'jnbe', 'jnc', 'jc', 'jz', 'jnz',
}
REG32 = {'eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp'}
DATA_SECS = ('.rdata', '.data')
ANY_SECS = ('.rdata', '.data', '.rsrc', '.detour')
LOOKBACK_BYTES = 0x1000     # bytes of history kept for body + hoisted mov
MAX_BODY = 0x800


def load_pe():
    pe = pefile.PE(EXE, fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    secs, text = {}, None
    for s in pe.sections:
        nm = s.Name.rstrip(b'\x00').decode('latin-1')
        lo = base + s.VirtualAddress
        secs[nm] = (lo, lo + max(s.Misc_VirtualSize, s.SizeOfRawData))
        if nm == '.text':
            text = (lo, s.get_data())
    return pe, secs, text


_IMMRE = __import__('re').compile(r'^(0[xX][0-9a-fA-F]+|\d+)$')


def imm(op):
    """Bare immediate, in EITHER form.

    capstone prints small immediates in DECIMAL (add esi, 8 / push 7) and large
    ones in hex (cmp esi, 0x7f3718). Accepting only '0x...' made the known R129
    loop classify as a miss (self-error S-200, same family as R129 S-192).
    """
    s = op.strip()
    if not _IMMRE.match(s):
        return None
    return int(s, 16) if s[:2].lower() == '0x' else int(s, 10)


def in_sec(secs, val, names):
    for n in names:
        if n in secs and secs[n][0] <= val < secs[n][1]:
            return n
    return None


def classify(hist, secs, head, edge, jcc):
    """hist: aligned list of (addr, mnem, op) covering [head-LOOKBACK, edge]."""
    body = [t for t in hist if head <= t[0] <= edge]
    if len(body) < 3 or body[-1][0] != edge:
        return None
    if body[-2][1] != 'cmp':
        return None
    cp = [x.strip() for x in body[-2][2].split(',')]
    if len(cp) != 2 or cp[0] not in REG32:
        return None
    creg, cbound = cp[0], imm(cp[1])
    if cbound is None or not in_sec(secs, cbound, ANY_SECS):
        return None
    head_c = None
    for a, m, o in hist:
        if a >= body[-2][0]:
            break
        p = [x.strip() for x in o.split(',')]
        if m == 'mov' and len(p) == 2 and p[0] == creg:
            v = imm(p[1])
            if v is not None and in_sec(secs, v, DATA_SECS):
                head_c = (a, v)
    if head_c is None:
        return None
    step_c = None
    for a, m, o in body[:-2]:
        p = [x.strip() for x in o.split(',')]
        if m == 'add' and len(p) == 2 and p[0] == creg:
            v = imm(p[1])
            if v is not None and 0 < v <= 0x1000 and a >= head_c[0]:
                step_c = (a, v)
    if step_c is None:
        return None
    delta = cbound - head_c[1]
    if delta <= 0 or delta % step_c[1]:
        return None
    cnt = delta // step_c[1]
    if not (1 <= cnt <= 4096):
        return None
    return {
        'table_head': hex(head_c[1]), 'bound': hex(cbound), 'step': step_c[1],
        'count': cnt,
        'head_sec': in_sec(secs, head_c[1], DATA_SECS),
        'bound_sec': in_sec(secs, cbound, ANY_SECS),
        'loop_head': hex(head), 'back_edge': hex(edge), 'jcc': jcc,
        'mov_at': hex(head_c[0]), 'add_at': hex(step_c[0]),
        'cmp_at': hex(body[-2][0]),
        'mov_hoisted': head_c[0] < head,
        'body_insns': len(body),
    }


def main():
    pe, secs, (text_va, data) = load_pe()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = False
    md.skipdata = True

    hist = collections.deque()
    n_insn = 0
    n_back = 0
    hits = {}
    for addr, size, mnem, op_str in md.disasm_lite(data, text_va):
        n_insn += 1
        if mnem in BACK_JCC:
            t = imm(op_str)
            if t is not None and t < addr and (addr - t) <= MAX_BODY:
                n_back += 1
                # trim history to the lookback window, then classify
                while hist and hist[0][0] < t - LOOKBACK_BYTES:
                    hist.popleft()
                cand = list(hist)
                cand.append((addr, mnem, op_str))
                h = classify(cand, secs, t, addr, mnem)
                if h:
                    hits.setdefault((h['table_head'], h['bound'], h['step']), h)
        hist.append((addr, mnem, op_str))
        while hist and hist[0][0] < addr - LOOKBACK_BYTES:
            hist.popleft()

    rec = {'insn_count': n_insn, 'back_edges_bounded': n_back,
           'table_loops': len(hits), 'hits': [hits[k] for k in sorted(hits)]}
    known = [h for h in rec['hits']
             if h['loop_head'] == '0x6bc34d' and h['mov_at'] == '0x6bc342'
             and h['table_head'] == '0x7f3710' and h['bound'] == '0x7f3718'
             and h['step'] == 8 and h['count'] == 1]
    rec['posctl_r129_loop_found'] = len(known) == 1
    with io.open(OUT, 'w', encoding='utf-8') as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)

    print('insn_count', n_insn, 'back_edges_bounded', n_back,
          'table_loops', len(hits))
    print('posctl R129 loop found:', rec['posctl_r129_loop_found'])
    for k in sorted(hits):
        h = hits[k]
        print(' ', h['table_head'], '->', h['bound'], 'step', h['step'],
              'n', h['count'], h['jcc'], 'loop', h['loop_head'],
              'hoisted' if h['mov_hoisted'] else 'inbody', h['head_sec'])
    return 0 if rec['posctl_r129_loop_found'] else 1


if __name__ == '__main__':
    sys.exit(main())
