"""Compact 18-row table for AUDIT6 (boundary-limited, own disassembly)."""
import core, idx, json
from verify import analyze, host_rows, QI, hx

ENTS = ['006C1010','006C1190','006C1310','006C1490','006C1610','006C1790','006C1910','006C1A90',
        '006C1C10','006C1D90','006C1F10','006C2090','006C2210','006C2390','006C2510','006C2690',
        '006C2810','006C2990']

hr, esi = host_rows()
print('esi:', esi)
print()

def fd(e):
    return analyze(int(e, 16))

# map factory ctor -> host seq
ctor2seq = {}
for s in hr:
    if 'ctor' in s:
        ctor2seq.setdefault(s['ctor'], []).append(s)

out = {}
for e in ENTS:
    r = fd(e)
    out[e] = r
    slot = r['slots'][0]
    lines = []
    lines.append('%s n=%d skip=%d last=%s callers=%d range=%s..%s' % (
        e, r['n_insn'], r['skipdata'], r['last'], len(r['callers']), r['range'][0], r['range'][1]))
    lines.append('   [1] imms=' + ', '.join('%s:%s' % (a, t.split(', ')[1]) for a, t, b in r['imms']))
    q = [d for d in r['disp'] if d[1] == 'call dword ptr [eax]']
    rel = [d for d in r['disp'] if '+ 0x20' in d[1]]
    if q:
        a, t, b, seq = q[0]
        lines.append('   [3] QIsite=%s %s [%s] next=%s' % (a, t, b, ' | '.join(seq[:3])))
    if rel:
        lines.append('   [3] release=%s [%s] next=%s' % (rel[0][0], rel[0][2], ' | '.join(rel[0][3][:2])))
    lines.append('   [3] rets=' + ' '.join('%s:%s' % (a, t) for a, t in r['rets']))
    # 2
    for s in r['slots']:
        lines.append('   [2] SLOT %s %s vt=%s idx=%d sig=%s COL=%s TD=%s vt0=%s' % (
            s['slot'], s['sec'], s['vt'], s['idx'], s['sig'], s['col'], s['td'], s['vt0']))
        lines.append('       name=%s' % s['name'])
    # 3 obj ctor
    if 'obj_ctor' in r:
        lines.append('   [3] OBJCTOR %s this=%s' % (r['obj_ctor_call'], r['obj_ctor_this']))
        for a, m, v, b in r['obj_ctor_w0']:
            lines.append('       [%s+0] %s %s = %s' % (r['obj_ctor_this'], a, m, v))
        main = r['obj_main']
        lines.append('       MAIN vt=%s vt0=%s QI=%s name=%s' % (main['vt'], main['vt0'], r['obj_main_qi'], main['name']))
        for m in r['member_vts']:
            lines.append('       member vt=%s vt0=%s name=%s' % (m['vt'], m['vt0'], m['name']))
    # 4 host
    fctor = r.get('obj_ctor')  # placeholder
    print('\n'.join(lines))
    print()

json.dump(out, open('rows_all.json', 'w'), indent=1)
