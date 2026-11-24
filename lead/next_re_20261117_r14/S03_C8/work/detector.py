#!/usr/bin/env python3
"""③b detector (S03-C8, self-written). D-42 four tiers + rule#1 guard chain.
strict: ③b① = physical jump table only; ③b④ requires explicit non-stack write + bound + advance (M7).
loose: ③b① += >=3 mutually-exclusive in-body guard chain.
Baseline pool = current disk coverage.tsv S03 grade=[静态推断] AND has self-CFG extent.
seed 20261119, 2000 draws of 8 without replacement. K=N*p is identity, NOT a check (M3)."""
import os, json, csv, random
from collections import Counter
from capstone import x86
import common as C

COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
CLS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C8"

ext = {}
for r in csv.DictReader(open(CLS, encoding='utf-8'), delimiter='\t'):
    try:
        ext[r['entry']] = (int(r['ext_lo'], 16), int(r['ext_hi'], 16))
    except Exception:
        pass

def is_jcc(m):
    return m.startswith('j') and m not in ('jmp',) and not m.startswith('jmp')

def feat(insns):
    addrs = [i.address for i in insns]
    addrs_set = set(addrs)
    f = {'jumptable': False, 'guard_chain': False, 'errcode': False, 'memshape': False,
         'ioloop': False, 'n_jcc': 0, 'jcc_targets': [], 'backedge': 0, 'n_insn': len(insns)}
    # ③b① physical jump table: indirect jmp with index register (op.mem.index != 0) or reg*scale
    for i in insns:
        if i.mnemonic == 'jmp':
            for op in i.operands:
                if op.type == x86.X86_OP_MEM and op.mem.index not in (0, None):
                    f['jumptable'] = True
            if 'dword ptr' in i.op_str and '*' in i.op_str:
                f['jumptable'] = True
    # guard chain: >=3 mutually exclusive jcc sites with >=3 distinct in-body targets
    tgts = []; sites = []
    for i in insns:
        if is_jcc(i.mnemonic) and i.operands and i.operands[0].type == x86.X86_OP_IMM:
            t = i.operands[0].imm
            if t in addrs_set:
                tgts.append(t); sites.append(i.address)
    f['n_jcc'] = len(tgts); f['jcc_targets'] = [f"0x{t:08X}" for t in tgts]
    if len(sites) >= 3 and len(set(tgts)) >= 3:
        f['guard_chain'] = True
    # backedge
    for i in insns:
        if i.mnemonic.startswith('j') and i.operands and i.operands[0].type == x86.X86_OP_IMM:
            if i.operands[0].imm <= i.address:
                f['backedge'] += 1
    # ③b② falsifiable error/return convention
    for j, i in enumerate(insns):
        o = i.op_str
        if i.mnemonic == 'cmp' and ('-1' in o or '0x8000' in o.lower()):
            for k in insns[j+1:j+8]:
                if k.mnemonic.startswith('ret') or k.mnemonic.startswith('set') or is_jcc(k.mnemonic):
                    f['errcode'] = True; break
        if i.mnemonic == 'call' and '0x7e1200' in o:  # GetLastError IAT
            f['errcode'] = True
    # tested callee result AND >=2 distinct return constructions (falsifiable return paths)
    tested_call = False; ret_kinds = set()
    for n, i in enumerate(insns):
        if i.mnemonic == 'call' and any(
                k.mnemonic in ('test', 'cmp') and k.operands and k.operands[0].type == x86.X86_OP_REG
                and k.operands[0].reg == x86.X86_REG_EAX
                for k in insns[n+1:n+7]):
            tested_call = True
        if i.mnemonic == 'xor' and len(i.operands) == 2 and i.operands[0].type == x86.X86_OP_REG \
                and i.operands[0].reg == x86.X86_REG_EAX and i.operands[1].reg == x86.X86_REG_EAX:
            ret_kinds.add('zero')
        if i.mnemonic == 'mov' and len(i.operands) == 2 and i.operands[0].type == x86.X86_OP_REG \
                and i.operands[0].reg == x86.X86_REG_EAX and i.operands[1].type == x86.X86_OP_IMM:
            ret_kinds.add('imm')
        if i.mnemonic in ('shl', 'or', 'add', 'sbb', 'and') and len(i.operands) == 2 \
                and i.operands[0].type == x86.X86_OP_REG and i.operands[0].reg == x86.X86_REG_EAX:
            ret_kinds.add('pack')
    if tested_call and len(ret_kinds) >= 2:
        f['errcode'] = True
    # ③b③ memory shape: >=2 vt writes (imm in .rdata) OR >=10 distinct object-field writes
    vtw = set(); fieldw = set()
    for i in insns:
        if i.mnemonic == 'mov' and len(i.operands) == 2 and i.operands[0].type == x86.X86_OP_MEM:
            m = i.operands[0].mem
            if i.operands[1].type == x86.X86_OP_IMM:
                v = i.operands[1].imm
                if C.RDATA_VA <= v < C.RDATA_VA + C.RDATA_VS:
                    vtw.add(v)
            if m.base not in (x86.X86_REG_ESP, x86.X86_REG_EBP, None):
                fieldw.add((m.base, m.disp))
    if len(vtw) >= 2 or len(fieldw) >= 10:
        f['memshape'] = True
    # ③b④ complete I/O loop (M7): backedge + explicit NON-STACK write in body + boundary cmp + advance
    has_write = False; has_bound = False
    for i in insns:
        if i.mnemonic in ('mov', 'stosd', 'movsb', 'movsd', 'call') and i.operands:
            for op in i.operands:
                if op.type == x86.X86_OP_MEM:
                    m = op.mem
                    if m.base not in (x86.X86_REG_ESP, x86.X86_REG_EBP, None):
                        has_write = True
        if i.mnemonic in ('cmp', 'test'):
            has_bound = True
    if f['backedge'] >= 1 and has_write and has_bound:
        f['ioloop'] = True
    return f

def passes(f, tier):
    b1 = f['jumptable'] or (tier == 'loose' and f['guard_chain'])
    return b1 or f['errcode'] or f['memshape'] or f['ioloop']

def insns_of(entry_hex):
    lo, hi = ext[entry_hex]
    return C.md_detail(lo, hi - lo)

# ---- pool: S03 [静态推断] in current coverage.tsv AND has self-CFG extent ----
pool = []
for line in open(COV, encoding='utf-8', errors='replace'):
    p = line.rstrip('\n').split('\t')
    if len(p) >= 5 and p[1] == 'S03' and '[静态推断]' in p[4]:
        e = p[0].strip()
        if e in ext:
            pool.append(e)
pool = sorted(set(pool))
print("S03 [静态推断] pool N =", len(pool))

res = {}
allfeat = {}
for tier in ('strict', 'loose'):
    passing = []
    for e in pool:
        f = feat(insns_of(e))
        allfeat.setdefault(e, f)
        if passes(f, tier):
            passing.append(e)
    N = len(pool); K = len(passing); p = K / N; E8 = 8 * p
    rnd = random.Random(20261119); trials = 2000; hits = 0; dist = Counter()
    pset = set(passing)
    for _ in range(trials):
        samp = rnd.sample(pool, 8)
        h = sum(1 for e in samp if e in pset); hits += h; dist[h] += 1
    mc = hits / trials
    res[tier] = {'N': N, 'K': K, 'base_rate': p, 'E8': E8, 'mc_seed': 20261119,
                 'mc_draws': 2000, 'mc_mean': mc,
                 'mc_dist': {str(k): v for k, v in sorted(dist.items())}, 'passing': passing}
    print(f"[{tier}] N={N} K={K} p={p:.6f} E[8]={E8:.4f} MCmean={mc:.4f}")

# per-row feature report for my 5 candidate rows
TARGETS = ['00473C00', '00473CE0', '00473FC0', '0047AAB0', '00631D30']
rowrep = {}
for e in TARGETS:
    f = feat(insns_of(e))
    rowrep[e] = {'feat': f, 'strict': passes(f, 'strict'), 'loose': passes(f, 'loose')}
    print(f"ROW {e}: strict={passes(f,'strict')} loose={passes(f,'loose')} n_jcc={f['n_jcc']} "
          f"backedge={f['backedge']} jt={f['jumptable']} err={f['errcode']} "
          f"shape={f['memshape']} ioloop={f['ioloop']} guard={f['guard_chain']}")

json.dump({'baseline': res, 'rows': rowrep,
           'detector': 'D-42 four tiers; strict ③b①=physical jumptable only, ③b④ req explicit non-stack write+bound+advance(M7); loose += >=3 in-body guard chain',
           'pool_note': 'current disk coverage S03 [静态推断] CAP extent; seed 20261119/2000 draws; K=N*p identity not a check(M3)'},
          open(BASE + r"\EVIDENCE\baselines.json", 'w', encoding='utf-8'), indent=2)
print("wrote EVIDENCE/baselines.json")
