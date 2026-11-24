#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detailed per-candidate analysis using classification extents (not CFG over-traverse).
Produces full disassembly + feature annotations for chosen entries.
Usage: python detail.py <entry> [<entry> ...]
"""
import csv, os, sys, json
import s09lib8 as L
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG, X86_GRP_JUMP, X86_GRP_CALL

R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
WORK = os.path.join(R14, 'S09_KPROVED8', 'work')
EV = os.path.join(R14, 'S09_KPROVED8', 'EVIDENCE')
CLASS = os.path.join(R14, 'SURVEY_RING24', 'EVIDENCE', 'classification.tsv')


def load_cls():
    d = {}
    with open(CLASS, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            d[r['entry'].strip().upper()] = r
    return d


def main():
    cls = load_cls()
    tables = L.rtti_tables()
    _, calls = L.full_e8_sweep()
    for ea in sys.argv[1:]:
        e = ea.upper()
        entry = int(e, 16)
        c = cls.get(e, {})
        lo = int(c.get('ext_lo', e), 16)
        hi = int(c.get('ext_hi', e), 16)
        if hi <= lo or hi - lo > 6000:
            hi = lo + min(int(c.get('atlas_size', '200') or 200) * 4, 3000)
        insns = L.decode_range(lo, hi)
        hits = L.tables_holding(tables, entry)
        sites = L.direct_sites_for(entry, calls, lo, hi)
        lines = []
        lines.append('=== %s  name=%s ext=[%08X,%08X) size=%d ===' % (e, c.get('name', ''), lo, hi, hi - lo))
        lines.append('has2_rtti=%s rtti_vt=%s rtti_slot=%s has4_strict=%s n_direct_out=%s' % (
            c.get('has2_rtti', ''), c.get('rtti_vt', ''), c.get('rtti_slot', ''),
            c.get('has4_strict', ''), c.get('n_direct_out', '')))
        lines.append('② all holding tables (%d):' % len(hits))
        for t, slot in hits:
            lines.append('  vt=%08X slot=%d col=%08X td=%08X name=%s' % (
                t['vt'], slot, t['col'], t['td'], t['name']))
        lines.append('④ direct E8 sites (%d total, %d ok):' % (len(sites), sum(1 for s in sites if s['ok'])))
        for s in sites:
            lines.append('  site=%08X rel=%d target=%08X inbody=%s self=%s ok=%s raw=%s' % (
                s['site'], s['rel'], s['target'], s['in_body'], s['selfloop'], s['ok'], s['raw']))
        lines.append('--- disassembly ---')
        for ins in insns:
            mark = ''
            if ins.mnemonic == 'jmp' and ins.operands and ins.operands[0].type == X86_OP_MEM:
                mark = '  <<< INDIRECT JMP (jump table?)'
            elif ins.mnemonic.startswith('j') and ins.operands and ins.operands[0].type == X86_OP_IMM:
                t = ins.operands[0].imm
                if t < ins.address:
                    mark = '  <<< BACKWARD JCC'
            elif ins.mnemonic.startswith('cmp'):
                ims = L.imm_ops(ins)
                if any(x == -1 or x == 0xFFFFFFFF for x in ims):
                    mark = '  <<< CMP -1 sentinel'
            elif ins.mnemonic.startswith('ret'):
                mark = '  <<< RET'
            lines.append('%08X  %-22s %-8s %s%s' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))
        out = os.path.join(EV, 'DETAIL_%s.txt' % e)
        with open(out, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        print('wrote', out, 'lines', len(lines), 'insns', len(insns), 'hits', len(hits), 'sites', len(sites))


if __name__ == '__main__':
    main()
