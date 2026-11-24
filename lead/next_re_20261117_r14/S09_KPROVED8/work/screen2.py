#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Refined screening using classification extents (reliable function bounds) for ③b.
Writes screening2.json / screening2_top.tsv."""
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


def features(insns):
    f = dict(n=len(insns), e8=0, indjmp=0, backjcc=0, loops=[], cmpneg1=0,
             hres=0, nonstack_writes=0, calltgts=set(), rets=[])
    n = len(insns)
    for k, ins in enumerate(insns):
        m = ins.mnemonic
        if ins.mnemonic == '.byte' or ins.id == 0:
            continue
        ops = ins.operands
        if m == 'call' and len(ins.bytes) >= 5 and ins.bytes[0] == 0xE8:
            f['e8'] += 1
            ims = L.imm_ops(ins)
            if ims:
                f['calltgts'].add(ims[0])
        if m == 'jmp' and ops and ops[0].type == X86_OP_MEM and ops[0].mem.scale in (2, 4, 8):
            f['indjmp'] += 1
        if m.startswith('j') and m != 'jmp' and ops and ops[0].type == X86_OP_IMM:
            t = ops[0].imm
            if t < ins.address:
                f['backjcc'] += 1
                f['loops'].append((hex(ins.address), hex(t), m))
        if m.startswith('cmp') and ops:
            for im in L.imm_ops(ins):
                if im in (-1, 0xFFFFFFFF):
                    f['cmpneg1'] += 1
                if im in (0x80004002, 0x80004003, 0x80070057):
                    f['hres'] += 1
        if m in ('mov', 'movzx', 'movsx', 'and', 'or', 'xor', 'add', 'sub', 'inc', 'dec') and ops and ops[0].type == X86_OP_MEM:
            mm = ops[0].mem
            bn = ins.reg_name(mm.base) if mm.base is not None else None
            if bn not in ('esp', 'ebp', None):
                f['nonstack_writes'] += 1
        if m == 'ret':
            v = None
            for j in range(max(0, k - 5), k):
                p = insns[j]
                if p.mnemonic == 'xor' and p.op_str.replace(' ', '') == 'eax,eax':
                    v = 0
                if p.mnemonic == 'mov' and p.op_str.startswith('eax,'):
                    ims = L.imm_ops(p)
                    if ims:
                        v = ims[0]
                if p.mnemonic == 'sbb' and 'eax' in p.op_str:
                    v = 'sbb'
            f['rets'].append(v)
    f['calltgts'] = len(f['calltgts'])
    return f


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
        if not insns:
            continue
        hits = L.tables_holding(tables, entry)
        names = sorted(set(h[0]['name'] for h in hits))
        sites = L.direct_sites_for(entry, calls, lo, hi)
        ok_sites = [hex(s['site']) for s in sites if s['ok']]
        ft = features(insns)
        out.append(dict(entry=e, name=c['name'], lo=lo, hi=hi, size=hi - lo,
                        n_hits=len(hits), slots=sorted(set(h[1] for h in hits)), names=names,
                        ok_sites=ok_sites, **ft))
    with open(os.path.join(WORK, 'screening2.json'), 'w', encoding='utf-8') as fh:
        json.dump(out, fh, indent=1)

    def score(r):
        s = min(len(r['ok_sites']), 5) * 4
        s += min(r['indjmp'], 3) * 12
        s += min(r['backjcc'], 8) * 3
        s += min(r['nonstack_writes'], 25) * 0.25
        s += min(r['cmpneg1'], 5) * 3
        s += min(r['hres'], 3) * 5
        s += min(r['calltgts'], 12) * 0.4
        # distinct ret values >1 signals falsifiable convention
        s += 3 if len([v for v in r['rets'] if v is not None]) >= 2 else 0
        return s

    out.sort(key=score, reverse=True)
    with open(os.path.join(WORK, 'screening2_top.tsv'), 'w', encoding='utf-8') as fh:
        fh.write('entry\tname\tsize\tok4\tindjmp\tbackjcc\tnsw\tneg1\thres\tcalltgts\trets\tscore\tnames\n')
        for r in out[:150]:
            fh.write('\t'.join([r['entry'], r['name'], str(r['size']), str(len(r['ok_sites'])),
                                str(r['indjmp']), str(r['backjcc']), str(r['nonstack_writes']),
                                str(r['cmpneg1']), str(r['hres']), str(r['calltgts']),
                                ';'.join(str(x) for x in r['rets']), '%.2f' % score(r),
                                ';'.join(r['names'][:5])]) + '\n')
    print('analyzed', len(out))
    for r in out[:50]:
        print('%s %-30s sz=%-5d ok4=%-2d ij=%d bl=%-2d nsw=%-3d neg1=%d hres=%d ct=%-2d rets=%s score=%.1f' % (
            r['entry'], r['name'][:30], r['size'], len(r['ok_sites']), r['indjmp'], r['backjcc'],
            r['nonstack_writes'], r['cmpneg1'], r['hres'], r['calltgts'],
            ';'.join(str(x) for x in r['rets'])[:20], score(r)))


if __name__ == '__main__':
    main()
