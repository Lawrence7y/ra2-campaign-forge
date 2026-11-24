"""Verify: v4e h8_wait_trace recompute; harness W1 threshold; LA/TERM/S4/EXCEPT fields."""
import json, os, collections

ROOT = 'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/'
DIRS = ['l3_1101v4e', 'l3_1101v4f', 'l3_1101v4g']

# --- A. h8_wait_trace for v4e ---
p = ROOT + 'l3_1101v4e/h8_wait_trace.json'
j = json.load(open(p, encoding='utf-8'))
sm = j['samples']
print('h8_wait_trace v4e: n =', j.get('n'), 'verdict =', j.get('verdict'),
      'wait_s =', j.get('wait_s'), 'samples =', len(sm))
print('  first sample =', sm[0], 'last =', sm[-1])
zeros = [s for s in sm if s[1] == 0]
print('  count of f==0 =', len(zeros))
nz = next((s for s in sm if s[1] > 0), None)
print('  first f>0 =', nz)
run0 = 0
for s in sm:
    if s[1] == 0:
        run0 += 1
    else:
        break
print('  leading consecutive f==0 =', run0)
nf = next((s for s in sm if s[1] >= 800), None)
print('  first f>=800 =', nf)
fs = [s[1] for s in sm]
print('  f monotone non-decreasing?', all(b >= a for a, b in zip(fs, fs[1:])))
print('  distinct f values =', len(set(fs)), 'fmax =', max(fs))

# --- B. harness threshold constants ---
HP = 'D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py'
src = open(HP, encoding='utf-8').read()
for name in ['MEASURE_W1_UNITS0_MIN', 'MEASURE_GATE_FPS15_MIN', 'MEASURE_GATE_SPAN_S',
             'MEASURE_SETTLE_S', 'MEASURE_HZ', 'H8_MEASURE_START_FRAME', 'TACTICAL_COLOR_FLOOR']:
    for i, line in enumerate(src.splitlines(), 1):
        if line.strip().startswith(name + ' =') or line.strip().startswith(name + '='):
            print('  harness line', i, ':', line.strip()[:120])

# --- C. fields: LA / TERM / S4 / EXCEPT / protocol across three trips ---
fields = {}
for d in DIRS:
    fields[d] = {(r['group'], r['key']): r for r in
                 json.load(open(ROOT + d + '/qc151_fields.json', encoding='utf-8'))}
for grp, key in [('LA', 'in_tactical_target'), ('LA', 'features_target'),
                 ('MEASURE', 'protocol'), ('TERM', 'termination_verdict'),
                 ('TERM', 'wait_returncode'), ('S4', 'ra2loader_hits'), ('S4', 'ra2render_hits'),
                 ('S4', 's4_gate'), ('S4', 'hit_count'), ('S4', 'modules_total'),
                 ('EXCEPT', 'set_diff'), ('EXCEPT', 'post_file'),
                 ('MEASURE', 'w1_u0400_tier'), ('MEASURE', 'h7_gate_override'),
                 ('MEASURE', 'h7_frame_wait'), ('META', 'h7_measure_start_frame'),
                 ('META', 'h8_wait_trace')]:
    vals = []
    for d in DIRS:
        r = fields[d].get((grp, key))
        vals.append('ABSENT' if r is None else str(r['value'])[:200])
    print(f'{grp}.{key}: ' + ('SAME' if len(set(vals)) == 1 else 'DIFF'))
    for d, v in zip(DIRS, vals):
        print('    ', d, v)

# --- E. except_set_diff.json byte identity ---
for d in DIRS:
    q = ROOT + d + '/except_set_diff.json'
    b = open(q, 'rb').read()
    print(d, 'except_set_diff size', len(b), 'content', b.decode('utf-8')[:250].replace('\n', ' '))

# --- I. module table line counts ---
for d in DIRS:
    q = ROOT + d + '/s4_module_table.txt'
    txt = open(q, encoding='utf-8', errors='replace').read()
    print(d, 'module table lines', len(txt.splitlines()), 'apphelp?', 'apphelp' in txt.lower())
    print('   ', [l.strip()[:70] for l in txt.splitlines()][:13])
