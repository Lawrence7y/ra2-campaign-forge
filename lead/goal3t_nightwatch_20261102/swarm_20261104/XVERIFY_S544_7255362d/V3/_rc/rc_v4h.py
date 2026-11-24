"""Drill into l3_1101v4h / v4a / v4b (harness8_v4, flag armed) and the 'degraded' verdicts."""
import json, os

ROOT = 'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/'
for d in ['l3_1101v4a', 'l3_1101v4b', 'l3_1101v4c', 'l3_1101v4d', 'l3_1101v4e',
          'l3_1101v4f', 'l3_1101v4g', 'l3_1101v4h', 'l3_1101v3c']:
    p = ROOT + d
    print('=====', d)
    lj = os.path.join(p, '_launch_result.json')
    if os.path.exists(lj):
        j = json.load(open(lj, encoding='utf-8'))
        argv = j.get('argv') or []
        try:
            i = argv.index('--h7-measure-start-frame')
            tail = argv[i:]
        except ValueError:
            tail = ['NO FLAG']
        print('   launch rc', j.get('rc'), 'dur', j.get('duration_s'), 'argv tail:', tail)
    fj = os.path.join(p, 'qc151_fields.json')
    if os.path.exists(fj):
        g = {(r['group'], r['key']): r['value'] for r in json.load(open(fj, encoding='utf-8'))}
        for k in ['started', 'finished', 'trip_id', 'trip_seconds']:
            print('   META.' + k, '=', g.get(('META', k)))
        for k in ['verdict', 'gate', 'h7_frame_wait', 'h7_gate_override', 'w1_u0400_tier',
                  'h7_nav_to_measure', 'settle_seconds']:
            if ('MEASURE', k) in g:
                print('   MEASURE.' + k, '=', str(g[('MEASURE', k)])[:220])
        for (grp, k), v in g.items():
            if grp in ('MEASURE', 'CLOSE', 'TERM') and ('degrad' in str(v).lower() or 'warn' in k.lower()):
                print('   ', grp, k, '=', str(v)[:200])
    else:
        print('   no qc151_fields.json; files =', sorted(os.listdir(p))[:30])
    for w in ['measure_w0.json']:
        wp = os.path.join(p, w)
        if os.path.exists(wp):
            j = json.load(open(wp, encoding='utf-8'))
            print('   ', w, 'verdict', j.get('verdict'), 'span', j.get('span_s'),
                  'h8', json.dumps(j.get('h8'), ensure_ascii=False)[:200] if j.get('h8') else None,
                  'error', str(j.get('error'))[:120])
