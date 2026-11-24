#!/usr/bin/env python3
"""R108-EXEC: Q2 (entries per interval), Q3 (negative control), Q4 (ret analysis).

Disassembly policy: every region disassembled here is at most ~0x1300 bytes and
is swept with disasm_lite (no operand objects retained).  The whole-.text scan
lives in scan.py and never uses detail=True.
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
sections = []
for s in pe.sections:
    sections.append((s.Name.rstrip(b'\x00').decode(), s.VirtualAddress + IB,
                     max(s.Misc_VirtualSize, s.SizeOfRawData), s.PointerToRawData))
with open(EXE, 'rb') as f:
    raw = f.read()
tsec = [x for x in sections if x[0] == '.text'][0]
TEXT_VA, TEXT_END = tsec[1], tsec[1] + tsec[2]


def va2off(va, n=1):
    for _, a, sz, praw in sections:
        if a <= va < a + sz and va + n <= a + sz:
            return praw + (va - a)
    return None


def read_bytes(va, n):
    o = va2off(va, n)
    if o is None:
        return None
    return raw[o:o + n]


ac = json.load(open(OUT + 'ac_sets.json'))
bs = json.load(open(OUT + 'bset.json'))
A = {int(k, 16): [int(x) for x in v] for k, v in ac['A'].items()}
C = {int(k, 16): [[int(a), m] for a, m in v] for k, v in ac['C'].items()}
B = {int(k, 16): v for k, v in bs['B'].items()}
Aset, Cset, Bset = set(A), set(C), set(B)

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
JCC = {'jo','jno','jb','jae','je','jne','jbe','ja','js','jns','jp','jnp',
       'jl','jge','jle','jg','jcxz','jecxz'}
TB = {'ret', 'retn', 'retf', 'jmp', 'call'} | JCC

TABLES = [
    (0x46f5a0, 0x46de20, 0x46e4be),
    (0x5001e4, 0x4ffd90, 0x4ffde9),
    (0x58bda4, 0x58bc20, 0x58bd85),
    (0x71f2c0, 0x71e940, 0x71eea2),
    (0x71f328, 0x71e940, 0x71f092),
    (0x79f028, 0x79da90, 0x79ed73),
]


def sweep(start, end):
    """Linear sweep [start,end). Returns (insns, resync_addrs).
    insn = (addr, size, mnemonic, op_str)."""
    insns = []
    resync = []
    data = read_bytes(start, end - start)
    mv = memoryview(data)
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


def region_counts(S, H, tmap):
    """Q2 a/b/c/d machinery. Interval is the OPEN-closed (S, H]."""
    lo, hi = S + 1, H  # addr in [lo, hi]
    a = sorted(x for x in tmap['A'] if lo <= x <= hi)
    b = sorted(x for x in tmap['B'] if lo <= x <= hi)
    c_ext, c_ext_src = [], {}
    c_internal_only = []
    for t in sorted(tmap['C']):
        if not (lo <= t <= hi):
            continue
        srcs = C[t]
        ext = [s for s, m in srcs if not (S <= s < H)]
        inn = [s for s, m in srcs if S <= s < H]
        if ext:
            c_ext.append(t)
            c_ext_src[hex(t)] = [[hex(s), m, hex(t)] for s, m in srcs if not (S <= s < H)]
        if inn and not ext:
            c_internal_only.append(t)
    return a, b, c_ext, c_ext_src, c_internal_only


# ---------- Q2 ----------
q2 = []
for tbl, S, H in TABLES:
    a, b, c, csrc, cintern = region_counts(S, H, {'A': Aset, 'B': Bset, 'C': Cset})
    sa = sorted(x for x in A.get(S, []))
    q2.append({
        'table': hex(tbl), 'S': hex(S), 'H': hex(H),
        'a_call_targets': len(a), 'a_addrs': [hex(x) for x in a],
        'b_vtable_slots': len(b), 'b_addrs': [hex(x) for x in b],
        'b_owners': {hex(x): B[x] for x in b},
        'c_external_jumps': len(c), 'c_addrs': [hex(x) for x in c],
        'c_sources_external': csrc,
        'c_internal_only_count': len(cintern),
        'c_internal_only': [hex(x) for x in cintern],
        'd_S_in_A': S in Aset, 'd_S_in_A_callers': [hex(x) for x in sa],
        'd_S_in_B': S in Bset,
        'd_S_in_B_owners': B.get(S),
        'd_S_in_C': S in Cset,
        'internal_total': len(a) + len(b) + len(c),
    })

# ---------- Q3 negative control ----------
rng = random.Random(20261117)
pool = sorted(Aset)
sample = rng.sample(pool, 200)
neg = []
fired = []
skipped = 0
for Sp in sample:
    nxt = None
    for x in pool:
        if x > Sp:
            nxt = x
            break
    if nxt is None or nxt - Sp > 0x40000:
        skipped += 1
        continue
    a, b, c, csrc, cintern = region_counts(Sp, nxt, {'A': Aset, 'B': Bset, 'C': Cset})
    tot = len(a) + len(b) + len(c)
    rec = {'S': hex(Sp), 'H': hex(nxt), 'span': nxt - Sp,
           'a': [hex(x) for x in a], 'b': [hex(x) for x in b], 'c': [hex(x) for x in c],
           'total': tot}
    neg.append(rec)
    if tot > 0:
        fired.append(rec)
ratio = len(fired) / len(neg) if neg else 0.0
q3 = {'seed': 20261117, 'sampled': 200, 'skipped_too_far': skipped,
      'evaluated': len(neg), 'fired': len(fired), 'ratio': ratio,
      'examples_fired': fired[:10],
      'note': 'fired = interval (S\',H\'] contains >=1 of a) call target b) vtable slot c) external-jump target'}

# ---------- Q4 rets ----------
q4 = []
for tbl, S, H in TABLES:
    insns, resync = sweep(S, H)
    by_addr = {i[0]: i for i in insns}
    order = [i[0] for i in insns]

    # reachability from S inside [S,H): fallthrough + intra-region branch targets
    startset = {S}
    # external entries into region = A/B/vtable/callers, plus anything the linear
    # sweep produced a jump to from outside
    ext_entries = set()

    # call the S itself plus every address that is a branch target from outside
    for t, srcs in C.items():
        if S <= t < H:
            if any(not (S <= s < H) for s, m in srcs):
                ext_entries.add(t)

    stack = [S]
    seen = set()
    while stack:
        cur = stack.pop()
        if cur in seen or cur not in by_addr:
            continue
        seen.add(cur)
        a0, sz, mn, ops = by_addr[cur]
        nxt = cur + sz
        tgt = None
        if ops.startswith('0x') and (mn == 'jmp' or mn in JCC):
            tgt = int(ops, 16)
        if mn in ('ret', 'retn', 'retf'):
            continue
        if mn == 'jmp' and tgt is None:
            continue  # indirect jmp: unknown
        if tgt is not None and S <= tgt < H:
            stack.append(tgt)
        if mn not in ('jmp',) and nxt < H:
            stack.append(nxt)

    rets = []
    for idx, addr in enumerate(order):
        a0, sz, mn, ops = by_addr[addr]
        if mn not in ('ret', 'retn', 'retf'):
            continue
        rawb = read_bytes(a0, sz)
        prev = by_addr[order[idx - 1]] if idx > 0 else None
        prevrec = None
        if prev is not None:
            pa, psz, pmn, pops = prev
            pb = read_bytes(pa, psz)
            prevrec = {'addr': hex(pa), 'bytes': pb.hex(), 'text': (pmn + ' ' + pops).strip(),
                       'reachable_from_S': pa in seen}
        after = a0 + sz
        nextrec = {'addr': hex(after)}
        if after in by_addr:
            na, nsz, nmn, nops = by_addr[after]
            nextrec['next_text'] = (nmn + ' ' + nops).strip()
        nextrec['is_A'] = after in Aset
        nextrec['is_B'] = after in Bset
        nextrec['is_C_target'] = after in Cset
        nextrec['is_external_entry'] = after in ext_entries
        nextrec['reachable_from_S'] = after in seen
        rets.append({'ret': hex(a0), 'bytes': rawb.hex(), 'text': (mn + ' ' + ops).strip(),
                     'prev': prevrec, 'after': nextrec})

    # classify: how many distinct "function-start-looking" addresses after a ret
    sep_starts = [r['after']['addr'] for r in rets
                  if not r['after']['reachable_from_S'] and not r['prev']['reachable_from_S']]
    q4.append({'table': hex(tbl), 'S': hex(S), 'H': hex(H),
               'insn_count': len(insns), 'resync': [hex(x) for x in resync],
               'ret_count': len(rets),
               'reachable_insn_count': len(seen),
               'unreachable_after_ret': sep_starts,
               'rets': rets})

json.dump({'text_va': TEXT_VA, 'text_end': TEXT_END,
           'A_size': len(Aset), 'B_size': len(Bset), 'C_size': len(Cset),
           'tables': q2}, open(OUT + 'entries.json', 'w'), indent=1)
json.dump(q3, open(OUT + 'negctl.json', 'w'), indent=1)
json.dump({'tables': q4}, open(OUT + 'rets.json', 'w'), indent=1)

print('A,B,C', len(Aset), len(Bset), len(Cset))
for r in q2:
    print(r['table'], 'a=%d b=%d c=%d total=%d | S in A=%s B=%s C=%s' % (
        r['a_call_targets'], r['b_vtable_slots'], r['c_external_jumps'],
        r['internal_total'], r['d_S_in_A'], r['d_S_in_B'], r['d_S_in_C']))
print('negctl fired %d/%d = %.4f (skipped %d)' % (len(fired), len(neg), ratio, skipped))
for r in q4:
    print(r['table'], 'insns=%d rets=%d reachable=%d unreach_after_ret=%s' % (
        r['insn_count'], r['ret_count'], r['reachable_insn_count'],
        r['unreachable_after_ret']))
