#!/usr/bin/env python3
"""R108-EXEC final assembler for rets.json (Q4)."""
import json

OUT = '_r108/_exec/'
rf = json.load(open(OUT + 'rets_forensic.json'))
q4 = json.load(open(OUT + 'rets.json'))
s2 = json.load(open(OUT + 'supp2.json'))
at = json.load(open(OUT + 'addrtaken.json'))

VERDICTS = {
    '0x46f5a0': 'INTERNAL (early return), 1 exception',
    '0x5001e4': 'INTERNAL (early return)',
    '0x58bda4': 'NOT INTERNAL - separate functions',
    '0x71f2c0': 'INTERNAL (early return)',
    '0x71f328': 'INTERNAL (early return)',
    '0x79f028': 'NOT INTERNAL - multiple functions (3 frame sizes)',
}

out = []
for t in rf['tables']:
    key = t['table']
    reach = next(x for x in q4['tables'] if x['table'] == key)
    sweep = next(x for x in s2['sweep'] if x['table'] == key)
    rets = []
    for r in t['rets']:
        refs = at['targets'].get(r['after'], {}).get('refs', [])
        rets.append({
            'ret': r['ret'], 'ret_bytes': r['bytes'], 'ret_text': r['text'],
            'prev_insn': r['cleanup'] and None or None,
            'prev': None,
            'cleanup_insn': r['cleanup'],
            'matching_sub_esp_in_region': r['matching_sub_esp_in_region'],
            'matching_sub_count': r['matching_sub_count'],
            'after': r['after'], 'after_bytes': r['after_bytes'],
            'after_is_A': r['after_is_A'], 'after_is_B': r['after_is_B'],
            'after_is_C_target': r['after_is_C_target'],
            'after_is_switch_slot': r['after_is_switch_slot_value'],
            'after_refs_immediate_or_data': refs,
        })
    # re-attach previous instruction with bytes from the q234 dump
    q4t = next(x for x in q4['tables'] if x['table'] == key)
    for a, b in zip(rets, q4t['rets']):
        a['prev'] = b['prev']
        a['prev_insn'] = b['prev']
    out.append({
        'table': key, 'S': t['S'], 'H': t['H'],
        'ret_count': t['ret_count'],
        'distinct_cleanup_consts': t['distinct_cleanup_consts'],
        'cleanup_consts': t['cleanup_consts'],
        'sub_esp_in_region': t['sub_esp_all'],
        'reachable_from_S': reach['reachable_insn_count'],
        'insn_count': reach['insn_count'],
        'reachable_pct': round(100.0 * reach['reachable_insn_count'] / reach['insn_count'], 1),
        'unreachable_after_ret': reach['unreachable_after_ret'],
        'verdict': VERDICTS[key],
        'rets': rets,
    })

json.dump({
    'criterion': (
        'Mechanical test used: a ret belongs to the function rooted at S only if the '
        'stack frame it tears down matches the sub esp,N of S. Tearing down a frame '
        'size that no enclosing prologue in the interval allocated means control never '
        'came from S, i.e. a separate function. `ret imm16` must also equal the frame '
        'owner\'s argument bytes. Presence of a ret alone decides nothing.'),
    'why_ret_alone_is_insufficient': (
        'MSVC emits a ret after every early-return path, so one function routinely '
        'contains many rets; conversely NOP padding between functions means consecutive '
        'functions also produce many rets. The two cases are indistinguishable without '
        'checking the frame the ret unwinds against the enclosing prologue.'),
    'verdicts': {
        '0x46f5a0': 'INTERNAL (early return), 1 exception',
        '0x5001e4': 'INTERNAL (early return)',
        '0x58bda4': 'NOT INTERNAL - separate functions',
        '0x71f2c0': 'INTERNAL (early return)',
        '0x71f328': 'INTERNAL (early return)',
        '0x79f028': 'NOT INTERNAL - multiple functions (3 frame sizes)',
    },
    'tables': out,
}, open(OUT + 'rets.json', 'w'), indent=1)
print('rets.json written')
for t in out:
    print(t['table'], 'rets=%d consts=%s reachable %.1f%% verdict=%s' % (
        t['ret_count'], t['cleanup_consts'], t['reachable_pct'], t['verdict']))
