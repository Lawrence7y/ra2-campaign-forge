#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Screen candidates for ③b features + ring ② (all holding tables) + ring ④ (direct sites).
Writes screening results into work/. Read-only on target."""
import csv, os, json, re, struct
import s09lib8 as L
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
WORK = os.path.join(R14, 'S09_KPROVED8', 'work')
CANDS = os.path.join(WORK, 'candidates_base.tsv')


def analyze_features(insns):
    """Return dict of ③b feature signals over an ordered instruction list."""
    n = len(insns)
    addrs = [i.address for i in insns]
    idx = {a: k for k, a in enumerate(addrs)}
    feat = dict(n=n, e8=0, indjmp=0, jmptbl=0, jmptbl_targets=[], backjcc=0,
                backloops=[], cmpneg1=0, cmphres=0, retvals=set(),
                nonstack_writes=0, stack_writes=0, call_direct=0,
                cmp_imm_gates=0, distinct_call_targets=0)
    calltgts = set()
    for ins in insns:
        m = ins.mnemonic
        ops = ins.operands
        if m == 'call':
            if len(ins.bytes) >= 5 and ins.bytes[0] == 0xE8:
                feat['e8'] += 1
                ims = L.imm_ops(ins)
                if ims:
                    calltgts.add(ims[0])
                    feat['call_direct'] += 1
        if m == 'jmp' and ops and ops[0].type == X86_OP_MEM:
            feat['indjmp'] += 1
            mm = ops[0].mem
            if mm.scale in (2, 4, 8):
                feat['jmptbl'] += 1
                # try to read jump table if base is absolute disp
                # capstone: mem.base / mem.index / mem.disp
                # handle [reg*4 + disp] with disp absolute
        if m.startswith('j') and m != 'jmp' and ops and ops[0].type == X86_OP_IMM:
            t = ops[0].imm
            if t < ins.address:
                feat['backjcc'] += 1
                feat['backloops'].append((ins.address, t, m))
        if m.startswith('cmp') and ops:
            ims = L.imm_ops(ins)
            for im in ims:
                if im == 0xFFFFFFFF or im == -1 or im == 0xFFFFFFFF:
                    feat['cmpneg1'] += 1
                if im in (0x80004002, 0x80004003, 0x80070057, 0x8000FFFF):
                    feat['cmphres'] += 1
                if isinstance(im, int) and 0 < abs(im) < 0x10000:
                    feat['cmp_imm_gates'] += 1
        if m.startswith('ret'):
            # detect return value setter nearby handled later
            pass
        # non-stack writes: mov [reg+..], reg/imm where reg != esp/ebp
        if m in ('mov', 'movzx', 'movsx') and ops and ops[0].type == X86_OP_MEM:
            mm = ops[0].mem
            base = mm.base
            base_name = ins.reg_name(base) if base is not None else None
            if base_name not in ('esp', 'ebp', None) or mm.disp and base_name is None:
                feat['nonstack_writes'] += 1
            if base_name in ('esp', 'ebp'):
                feat['stack_writes'] += 1
    feat['distinct_call_targets'] = len(calltgts)
    # distinct ret values from xor eax,eax / mov eax,imm preceding ret
    rets = []
    for k, ins in enumerate(insns):
        if ins.mnemonic.startswith('ret'):
            v = None
            for j in range(max(0, k - 4), k):
                p = insns[j]
                if p.mnemonic == 'xor' and p.op_str.replace(' ', '') in ('eax,eax',):
                    v = 0
                if p.mnemonic == 'mov' and p.op_str.startswith('eax,'):
                    ims = L.imm_ops(p)
                    if ims:
                        v = ims[0]
                if p.mnemonic == 'sbb' and 'eax' in p.op_str:
                    v = 'sbb'
            rets.append(v)
    feat['retvals'] = rets
    return feat


def main():
    tables = L.rtti_tables()
    print('RTTI tables:', len(tables), 'total slots:', sum(len(t['slots']) for t in tables))
    with open(os.path.join(WORK, 'rtti_tables.tsv'), 'w', encoding='utf-8') as f:
        f.write('vt\tcol\ttd\tname\tnslots\n')
        for t in tables:
            f.write('%08X\t%08X\t%08X\t%s\t%d\n' % (t['vt'], t['col'], t['td'], t['name'], len(t['slots'])))
    insns_all, calls = L.full_e8_sweep()
    print('full .text insns:', len(insns_all), 'E8@boundary:', len(calls))

    with open(CANDS, encoding='utf-8') as f:
        cands = [r for r in csv.DictReader(f, delimiter='\t') if r['has2_rtti'] == '1']

    out = []
    for c in cands:
        e = c['entry'].upper()
        entry = int(e, 16)
        lo, hi, ordered, _ = L.cfg_extent(entry)
        if not ordered:
            continue
        hits = L.tables_holding(tables, entry)
        # RTTI names of holding tables
        names = sorted(set(h[0]['name'] for h in hits))
        slots = sorted(set(h[1] for h in hits))
        sites = L.direct_sites_for(entry, calls, lo, hi)
        ok_sites = [hex(s['site']) for s in sites if s['ok']]
        feat = analyze_features(ordered)
        out.append(dict(entry=e, name=c['name'], lo=lo, hi=hi, size=hi - lo,
                        n_hits=len(hits), slots=slots, names=names,
                        n_sites=len(sites), ok_sites=ok_sites, **feat))

    with open(os.path.join(WORK, 'screening.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1)

    # rank: prioritize has jmptbl / backloop+nonstack / cmpneg1 / hres, with direct sites
    def score(r):
        s = 0
        if r['ok_sites']:
            s += 10
        s += min(r['jmptbl'], 3) * 5
        s += min(r['backjcc'], 6) * 2
        s += min(r['nonstack_writes'], 20) * 0.2
        s += min(r['cmpneg1'], 5) * 2
        s += min(r['cmphres'], 3) * 4
        s += min(r['distinct_call_targets'], 10) * 0.5
        return s

    out.sort(key=score, reverse=True)
    with open(os.path.join(WORK, 'screening_top.tsv'), 'w', encoding='utf-8') as f:
        f.write('entry\tname\tsize\tnhit\tslots\tok_sites\tjmptbl\tbackjcc\tnonstack\tcmpneg1\thres\tcalltgts\tscore\tnames\n')
        for r in out[:120]:
            f.write('\t'.join([r['entry'], r['name'], str(r['size']), str(r['n_hits']),
                               ';'.join(map(str, r['slots'])), ','.join(r['ok_sites'][:6]),
                               str(r['jmptbl']), str(r['backjcc']), str(r['nonstack_writes']),
                               str(r['cmpneg1']), str(r['cmphres']), str(r['distinct_call_targets']),
                               '%.2f' % score(r), ';'.join(r['names'][:6])]) + '\n')
    print('candidates analyzed:', len(out))
    print('top 40:')
    for r in out[:40]:
        print('%s %-26s sz=%-5d hit=%-2d slots=%-8s ok4=%-2d jt=%d bl=%d nsw=%d neg1=%d hres=%d ct=%d score=%.1f' % (
            r['entry'], r['name'][:26], r['size'], r['n_hits'], ';'.join(map(str, r['slots'])),
            len(r['ok_sites']), r['jmptbl'], r['backjcc'], r['nonstack_writes'],
            r['cmpneg1'], r['cmphres'], r['distinct_call_targets'], score(r)))


if __name__ == '__main__':
    main()
