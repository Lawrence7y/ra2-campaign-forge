"""Recheck A3 + gate mechanics: recompute pre_fps15/units0/gate from raw measure_w0.json."""
import json, collections

ROOT = 'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/'
for d in ['l3_1101v4e', 'l3_1101v4f', 'l3_1101v4g']:
    p = ROOT + d + '/measure_w0.json'
    j = json.load(open(p, encoding='utf-8'))
    s = j['samples']
    ts, fs = s['t'], s['f']
    print('===', d)
    print('  window =', j.get('window'), 'verdict =', j.get('verdict'),
          'span_s =', j.get('span_s'), 'settle_s =', j.get('settle_s'),
          'hz =', j.get('hz'), 'trip_id =', j.get('trip_id'))
    print('  map_sha256 =', j.get('map_sha256'), 'gamemd_sha256 =', j.get('gamemd_sha256'))
    print('  samples n_t =', len(ts), 'n_f =', len(fs))
    print('  t range =', ts[0], '->', ts[-1])
    print('  f distinct values =', len(set(fs)), 'f[0] =', fs[0], 'f[-1] =', fs[-1], 'fmax =', max(fs))
    # recompute pre_fps15 exactly as harness :5184-5191
    SETTLE = j.get('settle_s')
    gate = j['gate']
    gspan = gate.get('gate_span_s')
    t_cut = ts[0] + SETTLE - gspan
    pts = [(t, f) for t, f in zip(ts, fs) if t >= t_cut]
    pre = (pts[-1][1] - pts[0][1]) / (pts[-1][0] - pts[0][0]) if pts and (pts[-1][0] - pts[0][0]) > 0 else None
    print('  gate_block =', json.dumps(gate, ensure_ascii=False))
    print('  RECOMPUTED pre_fps15 =', None if pre is None else round(pre, 3),
          '| recorded', gate.get('pre_fps15'), '| match:',
          (pre is None and gate.get('pre_fps15') is None) or
          (pre is not None and abs(round(pre, 3) - gate.get('pre_fps15')) < 1e-9))
    rows = j.get('counters') or []
    units0 = None
    for r in rows:
        if r.get('units') is not None:
            units0 = r['units']
            break
    print('  RECOMPUTED units0(first row w/ units) =', units0, '| recorded', gate.get('units0'))
    print('  hz_effective =', j.get('stats', {}).get('hz_effective'), ' full stats =', json.dumps(j.get('stats'), ensure_ascii=False)[:400])
    print('  counters rows n =', len(rows))
    for r in rows:
        print('    ', json.dumps(r, ensure_ascii=False))
    print('  w1 =', json.dumps(j.get('w1'), ensure_ascii=False))
    print('  protocol keys:', json.dumps(j.get('protocol'), ensure_ascii=False) if 'protocol' in j else 'ABSENT')
    print('  other top keys:', sorted(k for k in j if k not in ('samples', 'counters', 'frame_edges')))
