#!/usr/bin/env python3
"""R108-EXEC supplement:
 (1) fixed negative control (exclude H' itself, which is in A by construction),
 (2) Q4 frame-size test: does each ret's `add esp,N` match an enclosing `sub esp,N`?
 (3) is post-ret code a dword inside a switch/jump table (indirect dispatch) ?
"""
import json
import random
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = 'ra2bench/gamemd.exe'
OUT = '_r108/_exec/'

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
sections = [(s.Name.rstrip(b'\x00').decode(), s.VirtualAddress + IB,
             max(s.Misc_VirtualSize, s.SizeOfRawData), s.PointerToRawData) for s in pe.sections]
with open(EXE, 'rb') as f:
    raw = f.read()
tsec = [x for x in sections if x[0] == '.text'][0]
TEXT_VA, TEXT_END = tsec[1], tsec[1] + tsec[2]


def read_bytes(va, n):
    for _, a, sz, praw in sections:
        if a <= va < a + sz and va + n <= a + sz:
            return raw[praw + (va - a):praw + (va - a) + n]
    return None


ac = json.load(open(OUT + 'ac_sets.json'))
bs = json.load(open(OUT + 'bset.json'))
A = {int(k, 16) for k in ac['A']}
C = {int(k, 16): [[int(a), m] for a, m in v] for k, v in ac['C'].items()}
B = {int(k, 16) for k in bs['B']}
Cset = set(C)

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
JCC = {'jo','jno','jb','jae','je','jne','jbe','ja','js','jns','jp','jnp',
       'jl','jge','jle','jg','jcxz','jecxz'}

TABLES = [(0x46f5a0,0x46de20,0x46e4be),(0x5001e4,0x4ffd90,0x4ffde9),
          (0x58bda4,0x58bc20,0x58bd85),(0x71f2c0,0x71e940,0x71eea2),
          (0x71f328,0x71e940,0x71f092),(0x79f028,0x79da90,0x79ed73)]


def sweep(start, end):
    insns, resync = [], []
    mv = memoryview(read_bytes(start, end - start))
    off = 0
    while off < end - start:
        consumed = 0
        for (addr, size, mn, ops) in md.disasm_lite(mv[off:], start + off):
            insns.append((addr, size, mn, ops))
            consumed += size
        if consumed == 0:
            resync.append(start + off)
            off += 1
        else:
            off += consumed
    return insns, resync


# ---------- (1) negative control, FIXED ----------
rng = random.Random(20261117)
pool = sorted(A)
sample = rng.sample(pool, 200)
res = {}
for mode in ('closed_incl_H', 'open_excl_H'):
    fired = []
    evald = 0
    for Sp in sample:
        nxt = next((x for x in pool if x > Sp), None)
        if nxt is None or nxt - Sp > 0x40000:
            continue
        evald += 1
        lo, hi = Sp + 1, (nxt if mode == 'closed_incl_H' else nxt - 1)
        a = [x for x in A if lo <= x <= hi]
        b = [x for x in B if lo <= x <= hi]
        c = [t for t in Cset if lo <= t <= hi
             and any(not (Sp <= s < nxt) for s, m in C[t])]
        tot = len(a) + len(b) + len(c)
        if tot > 0:
            fired.append({'S': hex(Sp), 'H': hex(nxt), 'total': tot,
                          'a': [hex(x) for x in a], 'b': [hex(x) for x in b],
                          'c': [hex(x) for x in c]})
    res[mode] = {'evaluated': evald, 'fired': len(fired),
                 'ratio': len(fired) / evald if evald else 0.0,
                 'examples': fired[:8]}

# ---------- (2)+(3) per-table ret forensics ----------
tables_out = []
for tbl, S, H in TABLES:
    insns, resync = sweep(S, H)
    prog = {}   # addr -> (mov ebp,esp) flag  ... identify prologue candidates
    subs = []   # (addr, imm) for sub esp,imm
    addsub_pairs = []
    for (a0, sz, mn, ops) in insns:
        if mn in ('sub', 'add') and ops.startswith('esp, '):
            try:
                imm = int(ops.split(', ')[1], 16)
            except Exception:
                imm = None
            if imm is not None:
                subs.append((a0, mn, imm, ops))
    rets = [i for i in insns if i[2] in ('ret', 'retn', 'retf')]

    # switch / jump table dword membership: scan .rdata and .text for dwords equal
    # to candidate addresses is expensive; instead test the 6 known tables + any
    # run of >=4 consecutive .text dwords starting at each table base.
    def table_slots(base, maxslots=512):
        vals = []
        for i in range(maxslots):
            ch = read_bytes(base + 4 * i, 4)
            if ch is None:
                break
            v = struct.unpack('<I', ch)[0]
            if TEXT_VA <= v < TEXT_END:
                vals.append(v)
            else:
                break
        return vals
    slots = {}
    for t, _, _ in TABLES:
        slots[t] = table_slots(t)
    # union of all six tables' slot values
    all_slot_vals = set()
    for t in slots:
        all_slot_vals |= set(slots[t])

    detail = []
    for (a0, sz, mn, ops) in rets:
        prev_add = None
        for (b0, bsz, bmn, bops) in insns:
            if b0 + bsz == a0 and bmn in ('add', 'sub') and bops.startswith('esp, '):
                try:
                    prev_add = (b0, int(bops.split(', ')[1], 16), bops)
                except Exception:
                    pass
        after = a0 + sz
        matching_sub = [] if prev_add is None else [(hex(x), o) for x, m, i, o in subs
                                                    if m == 'sub' and i == prev_add[1]]
        detail.append({
            'ret': hex(a0), 'bytes': read_bytes(a0, sz).hex(),
            'text': (mn + ' ' + ops).strip(),
            'cleanup': None if prev_add is None else {'addr': hex(prev_add[0]),
                                                     'imm': prev_add[1], 'text': prev_add[2]},
            'matching_sub_esp_in_region': matching_sub,
            'matching_sub_count': len(matching_sub),
            'after': hex(after),
            'after_is_switch_slot_value': after in all_slot_vals,
            'after_is_A': after in A, 'after_is_B': after in B,
            'after_is_C_target': after in Cset,
            'after_bytes': (read_bytes(after, 8) or b'').hex(),
        })

    # distinct cleanup constants across rets -> frame-size diversity
    consts = sorted({d['cleanup']['imm'] for d in detail if d['cleanup']})
    tables_out.append({
        'table': hex(tbl), 'S': hex(S), 'H': hex(H), 'ret_count': len(rets),
        'cleanup_consts': [hex(c) for c in consts],
        'distinct_cleanup_consts': len(consts),
        'sub_esp_all': [{'addr': hex(x), 'imm': hex(i), 'text': o} for x, m, i, o in subs],
        'any_after_in_switch_slots': any(d['after_is_switch_slot_value'] for d in detail),
        'rets': detail,
    })

json.dump({'seed': 20261117, 'sampled': 200, 'variants': res,
           'bug_note': ("variant closed_incl_H reproduces the card's literal spec; H' is in A "
                        "by construction so it self-counts every time => 100% is an artifact, "
                        "not discriminating power. open_excl_H removes that."),
           }, open(OUT + 'negctl.json', 'w'), indent=1)
json.dump({'tables': tables_out}, open(OUT + 'rets_forensic.json', 'w'), indent=1)

for k, v in res.items():
    print(k, v['evaluated'], 'fired', v['fired'], 'ratio %.4f' % v['ratio'])
for t in tables_out:
    print(t['table'], 'rets=%d consts=%s distinct=%d after_in_switch=%s' % (
        t['ret_count'], t['cleanup_consts'], t['distinct_cleanup_consts'],
        t['any_after_in_switch_slots']))
