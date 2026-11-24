#!/usr/bin/env python3
"""R108-EXEC final assembler: merge Q1/Q2 into entries.json per the card's schema."""
import json

OUT = '_r108/_exec/'
ac = json.load(open(OUT + 'ac_sets.json'))
bs = json.load(open(OUT + 'bset.json'))
q2 = json.load(open(OUT + 'entries.json'))          # from q234.py
ind = json.load(open(OUT + 'indirect.json'))
at = json.load(open(OUT + 'addrtaken.json'))
s2 = json.load(open(OUT + 'supp2.json'))

TABLES = [(0x46f5a0,0x46de20,0x46e4be),(0x5001e4,0x4ffd90,0x4ffde9),
          (0x58bda4,0x58bc20,0x58bd85),(0x71f2c0,0x71e940,0x71eea2),
          (0x71f328,0x71e940,0x71f092),(0x79f028,0x79da90,0x79ed73)]

tables = []
for t, S, H in TABLES:
    key = '%s|%s|%s' % (hex(t), hex(S), hex(H))
    ent = next(x for x in q2['tables'] if x['table'] == hex(t))
    iv = ind['intervals'][key]
    # H is the dispatch instruction, so its own table's slot values are the
    # real entry set; report both spellings of the interval for that set.
    tables.append({
        'table': hex(t), 'S': hex(S), 'H': hex(H), 'span': H - S,
        'Q2_a_call_targets': ent['a_call_targets'], 'Q2_a_addrs': ent['a_addrs'],
        'Q2_b_vtable_slots': ent['b_vtable_slots'], 'Q2_b_addrs': ent['b_addrs'],
        'Q2_b_owners': ent['b_owners'],
        'Q2_c_external_jumps': ent['c_external_jumps'], 'Q2_c_addrs': ent['c_addrs'],
        'Q2_c_sources_external': ent['c_sources_external'],
        'Q2_c_internal_only_count': ent['c_internal_only_count'],
        'Q2_c_internal_only': ent['c_internal_only'],
        'Q2_d_S_in_A': ent['d_S_in_A'],
        'Q2_d_S_in_A_callers': ent['d_S_in_A_callers'],
        'Q2_d_S_in_B': ent['d_S_in_B'],
        'Q2_d_S_in_C': ent['d_S_in_C'],
        'Q2_internal_total': ent['internal_total'],
        'Q2_outer_total_including_S': ent['internal_total'] + (1 if ent['d_S_in_A'] else 0),
        'EXTRA_H_is_dispatch_insn': True,
        'EXTRA_H_bytes_and_text': None,
        'EXTRA_dispatch_sites_inside': iv['dispatch_sites_inside'],
        'EXTRA_indirect_entries_inside': sorted({e['target'] for e in iv['indirect_entries_inside']}),
        'EXTRA_indirect_entry_count': iv['indirect_entry_count'],
        'EXTRA_reachable_mass_pct': None,
    })

json.dump({
    'Q1_sets': {
        'A': {'definition': 'direct call (E8 rel32) targets landing inside .text',
              'size': ac['counts']['A_size'],
              'raw_direct_call_sites': ac['counts']['direct_calls_in_text'],
              'call_targets_outside_text': ac['counts']['call_targets_out_of_text'],
              'crosscheck_raw_E8_bytes': ac['counts']['raw_e8_bytes'],
              'crosscheck_A_minus_E8': ac['counts']['A_minus_e8'],
              'crosscheck_E8_minus_A': ac['counts']['e8_minus_A']},
        'B': {'definition': 'vtable slot values landing inside .text',
              'size': bs['B_size'], 'criterion': bs['criterion'],
              'vtables_read': bs['vtables_read'], 'declared_slots': bs['declared_slots'],
              'slots_in_text': bs['slots_in_text'],
              'alt_mode_B_size': bs['alt_mode_B_size'],
              'alt_mode_symdiff': bs['alt_mode_symdiff']},
        'C': {'definition': 'direct jmp/jcc targets (short and near), landing inside .text',
              'size': ac['counts']['C_size'],
              'raw_sites': ac['counts']['direct_jmp_jcc_in_text'],
              'jump_targets_outside_text': ac['counts']['jump_targets_out_of_text'],
              'loopx_excluded': ac['counts']['loopx_excluded'],
              'warning': ('C excludes ALL indirect jumps. .text holds 811 indirect '
                          'jmp sites over 395 distinct table bases; switch case bodies '
                          'are reachable only through them.')},
    },
    'TEXT': {'va': ac['text_va'], 'end': ac['text_end'], 'size': ac['text_size'],
             'sha256_VirtualSize': ac['text_sha256'],
             'image_sha256': '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'},
    'Q2_tables': tables,
    'Q2_summary': {
        'tables_with_zero_a_b_c': [hex(t) for t, S, H in TABLES
                                   if next(x for x in q2['tables']
                                           if x['table'] == hex(t))['internal_total'] == 0],
        'tables_with_nonzero_a_b_c': [hex(t) for t, S, H in TABLES
                                      if next(x for x in q2['tables']
                                              if x['table'] == hex(t))['internal_total'] != 0],
        'note': ('Only 0x46f5a0 has a non-zero count, and its single hit 0x46e483 is '
                 'NOT an entry: it is the shared epilogue that the switch cases '
                 'converge on (jmp 0x46e483 from 0x46e5ff, 0x46e73e).'),
        'key_structural_fact': ('For all 6 tables H is itself the 7-byte indirect '
                                'dispatch jmp (ff 24 8d/95 ...). Therefore no case '
                                'body can lie in (S,H], and A/B/C are near-empty for '
                                'a structural reason, not because the intervals are '
                                'entry-free.'),
    },
}, open(OUT + 'entries.json', 'w'), indent=1)
print('entries.json written; tables', len(tables))
for t in tables:
    print(t['table'], 'a=%d b=%d c=%d total=%d outer=%d indirect=%d' % (
        t['Q2_a_call_targets'], t['Q2_b_vtable_slots'], t['Q2_c_external_jumps'],
        t['Q2_internal_total'], t['Q2_outer_total_including_S'],
        t['EXTRA_indirect_entry_count']))
