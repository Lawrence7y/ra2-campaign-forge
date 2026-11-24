# -*- coding: utf-8 -*-
"""打印每行装表点所在函数体内的「装表前 call」与关键字段。"""
import io, json, sys
sys.dont_write_bytecode = True
d = json.load(io.open(r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/R16_AUDIT_F1_B4/verify_out.json",
                      encoding='utf-8'))
for r in d['rows']:
    cs = r['ctor_support']
    print('%-9s %-28s site=%s func=%s  n_calls_before=%d  last=%s'
          % (r['entry'], r['name'], r['decl']['site'], cs['func'],
             cs['n_calls_before'], cs['calls_before_site']))
print()
print('td8 inline check:')
for r in d['rows']:
    print('  %s word=%s is_va=%s' % (r['entry'], r['td8_inline']['word'],
                                     r['td8_inline']['is_image_va']))
print()
print('C3 detail (old 4s):')
for r in d['rows']:
    c = r['C3']
    if c['old_n4'] > 0:
        print('  %s old_n4=%d new_n4=%d clauses=%d same_anchor=%s'
              % (r['entry'], c['old_n4'], c['new_n4'], c['old4_clause_count'],
                 c['same_anchor_two_4']))
        print('     old4_addrs=%s' % c['old4_addrs'])
print()
print('C1 raw hits / tables:')
for r in d['rows']:
    c = r['C1']
    print('  %s raw_hits=%d tables=%d same_slot=%d cls=%d uniq=%s'
          % (r['entry'], c['n_raw_hits'], c['n_candidate_tables'],
             c['n_same_slot'], c['n_same_slot_classmatch'],
             c['chosen_is_unique_classmatch']))
