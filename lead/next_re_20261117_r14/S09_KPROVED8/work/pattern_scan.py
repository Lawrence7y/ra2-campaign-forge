#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Targeted ③b pattern scan over all S09 [静态推断] candidates in atlas.
Pattern A: cmp reg,-1 / je + bounded array-shift loop with non-stack write [base+idx*4-4].
Pattern B: indirect jmp [reg*4+table] with cmp bound -> jump table (each path verifiable).
Pattern C: bounded loop with non-stack write + falsifiable 0/1 return.
Writes work/pattern_hits.json / pattern_hits.tsv.
"""
import csv, os, json
import s09lib8 as L
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
WORK = os.path.join(R14, 'S09_KPROVED8', 'work')
CLASS = os.path.join(R14, 'SURVEY_RING24', 'EVIDENCE', 'classification.tsv')
CANDS = os.path.join(WORK, 'candidates_base.tsv')


def load_cls():
    d = {}
    with open(CLASS, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            d[r['entry'].strip().upper()] = r
    return d


def scan(insns):
    A = B = C = 0
    Adet, Bdet, Cdet = [], [], []
    n = len(insns)
    for k, ins in enumerate(insns):
        if ins.mnemonic == '.byte' or ins.id == 0:
            continue
        m = ins.mnemonic
        ops = ins.operands
        if m.startswith('cmp') and ops and any(x in (-1, 0xFFFFFFFF) for x in L.imm_ops(ins)):
            for j in range(k + 1, min(k + 5, n)):
                if insns[j].mnemonic in ('je', 'jne'):
                    A += 1
                    Adet.append(hex(ins.address))
                    break
        if m in ('mov', 'movzx', 'movsx') and ops and ops[0].type == X86_OP_MEM:
            mm = ops[0].mem
            bn = ins.reg_name(mm.base) if mm.base is not None else None
            if mm.scale == 4 and mm.disp == -4 and bn not in ('esp', 'ebp', None):
                for j in range(k + 1, min(k + 14, n)):
                    q = insns[j]
                    if q.mnemonic == '.byte' or q.id == 0:
                        continue
                    if q.mnemonic.startswith('j') and q.mnemonic != 'jmp' and q.operands and q.operands[0].type == X86_OP_IMM:
                        if q.operands[0].imm < q.address:
                            Adet.append('SHIFT@%s' % hex(ins.address))
                            break
        if m == 'jmp' and ops and ops[0].type == X86_OP_MEM and ops[0].mem.scale in (2, 4, 8):
            B += 1
            Bdet.append(hex(ins.address))
        if m.startswith('j') and m != 'jmp' and ops and ops[0].type == X86_OP_IMM and ops[0].imm < ins.address:
            has_w = has_cmp = False
            for j in range(max(0, k - 18), k):
                q = insns[j]
                if q.mnemonic == '.byte' or q.id == 0:
                    continue
                if q.mnemonic in ('mov', 'movzx', 'movsx') and q.operands and q.operands[0].type == X86_OP_MEM:
                    mm = q.operands[0].mem
                    bn = q.reg_name(mm.base) if mm.base is not None else None
                    if bn not in ('esp', 'ebp', None):
                        has_w = True
                if q.mnemonic.startswith('cmp') and q.operands:
                    has_cmp = True
            if has_w and has_cmp:
                C += 1
                Cdet.append(hex(ins.address))
    return A, B, C, Adet, Bdet, Cdet


def main():
    cls = load_cls()
    tables = L.rtti_tables()
    _, calls = L.full_e8_sweep()
    with open(CANDS, encoding='utf-8') as fh:
        cands = [r for r in csv.DictReader(fh, delimiter='\t') if r['has2_rtti'] == '1']
    out = []
    for c in cands:
        e = c['entry'].upper()
        entry = int(e, 16)
        cc = cls.get(e, {})
        lo = int(cc.get('ext_lo', e), 16)
        hi = int(cc.get('ext_hi', e), 16)
        if hi <= lo or hi - lo > 4000:
            hi = lo + min(int(cc.get('atlas_size', '200') or 200) * 4, 2500)
        insns = L.decode_range(lo, hi)
        A, B, C, Ad, Bd, Cd = scan(insns)
        if A == 0 and B == 0 and C == 0:
            continue
        hits = L.tables_holding(tables, entry)
        sites = L.direct_sites_for(entry, calls, lo, hi)
        ok4 = sum(1 for s in sites if s['ok'])
        out.append(dict(entry=e, name=c['name'], lo=lo, hi=hi, size=hi - lo,
                        semineg1=A, jt=B, loopwrite=C,
                        Adet=Ad, Bdet=Bd, Cdet=Cd,
                        n_hits=len(hits), ok4=ok4,
                        names=sorted(set(h[0]['name'] for h in hits)),
                        slots=sorted(set(h[1] for h in hits))))
    json.dump(out, open(os.path.join(WORK, 'pattern_hits.json'), 'w', encoding='utf-8'), indent=1)
    with open(os.path.join(WORK, 'pattern_hits.tsv'), 'w', encoding='utf-8') as fh:
        fh.write('entry\tname\tsize\tsemi_neg1\tjt\tloopwrite\tok4\tnhit\tslots\tnames\n')
        for r in out:
            fh.write('\t'.join([r['entry'], r['name'], str(r['size']), str(r['semineg1']),
                                str(r['jt']), str(r['loopwrite']), str(r['ok4']),
                                str(r['n_hits']), ';'.join(map(str, r['slots'])),
                                ';'.join(r['names'][:6])]) + '\n')
    print('pattern hits:', len(out))
    print('=== Pattern A (neg1+shift loop) ===')
    for r in sorted([x for x in out if any(str(y).startswith('SHIFT') for y in x['Adet'])],
                    key=lambda x: -len(x['Adet'])):
        print(r['entry'], r['name'][:28].ljust(28), 'neg1', r['semineg1'], 'shift',
              sum(1 for y in r['Adet'] if str(y).startswith('SHIFT')), 'ok4', r['ok4'], 'nhit', r['n_hits'])
    print('=== Pattern B (jump table) ===')
    for r in [x for x in out if x['jt'] > 0]:
        print(r['entry'], r['name'][:28].ljust(28), 'jt', r['jt'], r['Bdet'], 'ok4', r['ok4'])
    print('=== Pattern C (bounded loop + nonstack write) top ===')
    for r in sorted([x for x in out if x['loopwrite'] > 0], key=lambda x: -x['loopwrite'])[:30]:
        print(r['entry'], r['name'][:28].ljust(28), 'C', r['loopwrite'], 'ok4', r['ok4'], 'sz', r['size'])


if __name__ == '__main__':
    main()
