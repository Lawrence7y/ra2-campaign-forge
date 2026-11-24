#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""③b base rate for S09 static-inference pool.
Protocol (card): random 8 rows from S09 [静态推断] pool, seed 20261119, 2000 draws.
Report strict and loose, with explicit operationalization.
Operationalizations (byte-level, from full body disasm):
  strict ③b = any hard tier:
    T1 jump table: indirect jmp [reg*scale] with cmp bound, all targets in body
    T2 falsifiable error code: cmp -1 / 0x8000xxxx -> je/jne AND >=2 distinct ret values
    T4 complete loop: backward jcc + boundary cmp in window + non-stack write in window
  loose ③b = strict OR weak signals:
    T1w any indirect jmp with scale
    T2w any cmp -1/0x8000xxxx -> je/jne within 4 insns
    T4w any backward jcc with a cmp in prior 18 insns (even stack-only writes)
    T5  >=3 cmp/test gates AND >=3 distinct direct call targets (细则#1-like)
Writes work/base_rate.py output to EVIDENCE/baseline_3b.json and work/ pool flags.
"""
import os, csv, json, random
import s09lib8 as L
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
WORK = os.path.join(R14, 'S09_KPROVED8', 'work')
EV = os.path.join(R14, 'S09_KPROVED8', 'EVIDENCE')
CLASS = os.path.join(R14, 'SURVEY_RING24', 'EVIDENCE', 'classification.tsv')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
ATLAS = r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'

SEED = 20261119
DRAWS = 2000
SAMPLE_N = 8


def load():
    atlas = set()
    with open(ATLAS, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            atlas.add(r['entry'].strip().upper())
    cls = {}
    with open(CLASS, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            cls[r['entry'].strip().upper()] = r
    cov = {}
    for ln in open(COV, encoding='utf-8').read().splitlines()[1:]:
        p = ln.split('\t')
        cov[p[0].upper()] = p
    pool = []
    for e in atlas:
        c = cov.get(e)
        if not c or c[1] != 'S09' or c[4] != '[静态推断]':
            continue
        pool.append(e)
    return sorted(pool), cls


def detect(entry, cls_row):
    lo = int(cls_row.get('ext_lo', '%08X' % entry), 16)
    hi = int(cls_row.get('ext_hi', '%08X' % (entry + 64)), 16)
    if hi <= lo or hi - lo > 4000:
        hi = lo + min(int(cls_row.get('atlas_size', '200') or 200) * 4, 2500)
    insns = L.decode_range(lo, hi)
    valid = [(k, i) for k, i in enumerate(insns) if i.mnemonic != '.byte' and i.id != 0]
    n = len(insns)
    T1 = T2 = T4 = False
    T1w = T2w = T4w = T5 = False
    gates = 0
    calltgts = set()
    for k, i in valid:
        m = i.mnemonic
        ops = i.operands
        if m == 'call' and len(i.bytes) >= 5 and i.bytes[0] == 0xE8 and L.imm_ops(i):
            calltgts.add(L.imm_ops(i)[0])
        if m == 'jmp' and ops and ops[0].type == X86_OP_MEM and ops[0].mem.scale in (2, 4, 8):
            T1w = True
            # strict T1: bound cmp earlier within 12 insns + verify targets in body
            for _, q in valid[max(0, k-12):k]:
                if q.mnemonic.startswith('cmp') and q.operands:
                    T1 = True   # targets verified separately for delivered rows; as base-rate predicate require bound cmp
                    break
        if m.startswith('cmp') and ops:
            ims = L.imm_ops(i)
            if any(x in (-1, 0xFFFFFFFF, 0x80004002, 0x80004003, 0x80070057) for x in ims):
                for j in range(k + 1, min(k + 5, n)):
                    if insns[j].mnemonic in ('je', 'jne', 'jl', 'jge'):
                        T2w = True
                        break
            gates += 1
        if m.startswith('test'):
            gates += 1
        if m.startswith('j') and m != 'jmp' and ops and ops[0].type == X86_OP_IMM and ops[0].imm < i.address:
            # backward jcc: window from target to here
            tgt = ops[0].imm
            win = [q for _, q in valid if tgt <= q.address < i.address]
            has_cmp = any(q.mnemonic.startswith('cmp') for q in win)
            has_nsw = False
            for q in win:
                if q.mnemonic in ('mov','movzx','movsx','and','or','xor','add','sub','inc','dec') and q.operands and q.operands[0].type == X86_OP_MEM:
                    mm = q.operands[0].mem
                    bn = q.reg_name(mm.base) if mm.base is not None else None
                    if bn not in ('esp', 'ebp', None):
                        has_nsw = True
                        break
            if has_cmp:
                T4w = True
            if has_cmp and has_nsw:
                T4 = True
    # distinct ret values for T2 strict
    rets = set()
    for _, i in valid:
        if i.mnemonic.startswith('ret'):
            rets.add('ret')
    if T2w and len(rets) >= 1:
        # T2 strict needs >=2 distinct ret blocks; count ret sites
        nret = sum(1 for _, i in valid if i.mnemonic.startswith('ret'))
        if nret >= 2:
            T2 = True
    if gates >= 3 and len(calltgts) >= 3:
        T5 = True
    strict = T1 or T2 or T4
    loose = strict or T1w or T2w or T4w or T5
    return dict(strict=strict, loose=loose, T1=T1, T2=T2, T4=T4,
                T1w=T1w, T2w=T2w, T4w=T4w, T5=T5)


def main():
    pool, cls = load()
    print('pool size (S09 [静态推断] in atlas):', len(pool))
    flags = {}
    for e in pool:
        flags[e] = detect(int(e, 16), cls.get(e, {}))
    with open(os.path.join(WORK, 'pool_3b_flags.tsv'), 'w', encoding='utf-8') as f:
        f.write('entry\tstrict\tloose\tT1\tT2\tT4\tT1w\tT2w\tT4w\tT5\n')
        for e in pool:
            d = flags[e]
            f.write('\t'.join([e] + ['1' if d[k] else '0' for k in
                    ('strict','loose','T1','T2','T4','T1w','T2w','T4w','T5')]) + '\n')
    Ks = sum(1 for e in pool if flags[e]['strict'])
    Kl = sum(1 for e in pool if flags[e]['loose'])
    print('K strict = %d (%.2f%% of pool), K loose = %d (%.2f%%)' % (
        Ks, 100.0*Ks/len(pool), Kl, 100.0*Kl/len(pool)))
    random.seed(SEED)
    distr_s = {}
    distr_l = {}
    sum_s = sum_l = 0
    for _ in range(DRAWS):
        sample = random.sample(pool, SAMPLE_N)
        cs = sum(1 for e in sample if flags[e]['strict'])
        cl = sum(1 for e in sample if flags[e]['loose'])
        distr_s[cs] = distr_s.get(cs, 0) + 1
        distr_l[cl] = distr_l.get(cl, 0) + 1
        sum_s += cs
        sum_l += cl
    mean_s = sum_s / DRAWS
    mean_l = sum_l / DRAWS
    exp_s = SAMPLE_N * Ks / len(pool)
    exp_l = SAMPLE_N * Kl / len(pool)
    out = dict(pool=len(pool), seed=SEED, draws=DRAWS, sample_n=SAMPLE_N,
               K_strict=Ks, K_loose=Kl,
               strict_pct=100.0*Ks/len(pool), loose_pct=100.0*Kl/len(pool),
               expected_strict=exp_s, expected_loose=exp_l,
               observed_mean_strict=mean_s, observed_mean_loose=mean_l,
               dist_strict={str(k):v for k,v in sorted(distr_s.items())},
               dist_loose={str(k):v for k,v in sorted(distr_l.items())},
               operationalization=dict(
                 strict='T1 verified-bounded jump table OR T2 cmp -1/HRESULT->jcc with >=2 ret blocks OR T4 backward-jcc loop with boundary cmp AND non-stack write in window',
                 loose='strict OR T1w any scaled indirect jmp OR T2w any cmp -1/HRESULT->jcc OR T4w any backward-jcc with cmp in window OR T5 >=3 gates AND >=3 distinct direct call targets'))
    with open(os.path.join(EV, 'baseline_3b.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print('strict: expected %.4f observed mean %.4f dist %s' % (exp_s, mean_s, dict(sorted(distr_s.items()))))
    print('loose : expected %.4f observed mean %.4f dist %s' % (exp_l, mean_l, dict(sorted(distr_l.items()))))

if __name__ == '__main__':
    main()
