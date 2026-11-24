"""Independent census of the REAL trip tree: verdict, gate, whether the launch argv
carried the frame-wait flag, and settle/window payload shape."""
import json, os, glob

ROOT = 'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/'
rows = []
for d in sorted(os.listdir(ROOT)):
    p = ROOT + d
    if not os.path.isdir(p) or not d.startswith('l'):
        continue
    fj = os.path.join(p, 'qc151_fields.json')
    lj = os.path.join(p, '_launch_result.json')
    rec = {'dir': d}
    if os.path.exists(fj):
        fields = json.load(open(fj, encoding='utf-8'))
        g = {(r['group'], r['key']): r['value'] for r in fields}
        rec['verdict'] = g.get(('MEASURE', 'verdict'))
        rec['gate'] = g.get(('MEASURE', 'gate'))
        rec['trip_id'] = g.get(('META', 'trip_id'))
        rec['trip_seconds'] = g.get(('META', 'trip_seconds'))
        rec['nav_to_measure'] = str(g.get(('MEASURE', 'h7_nav_to_measure')))[:60]
        rec['h7_flag_field'] = ('META', 'h7_measure_start_frame') in g
        rec['h8flag'] = ('META', 'h8_wait_trace') in g
    if os.path.exists(lj):
        j = json.load(open(lj, encoding='utf-8'))
        argv = j.get('argv') or []
        rec['harness'] = os.path.basename(str(j.get('harness')))
        rec['sha16'] = j.get('harness_sha16')
        rec['flag_in_argv'] = '--h7-measure-start-frame' in ' '.join(argv)
        rec['rc'] = j.get('rc')
        rec['dur'] = j.get('duration_s')
    w0 = os.path.join(p, 'measure_w0.json')
    if os.path.exists(w0):
        j = json.load(open(w0, encoding='utf-8'))
        s = j.get('samples') or {}
        fs = s.get('f') or []
        rec['w0_span'] = j.get('span_s')
        rec['w0_verdict'] = j.get('verdict')
        rec['w0_n'] = len(fs)
        rec['w0_f0'] = fs[0] if fs else None
        rec['w0_fmax'] = max(fs) if fs else None
        cnts = j.get('counters') or []
        first_units = next((c['units'] for c in cnts if c.get('units') is not None), None)
        rec['w0_units_firstrow'] = first_units
        nz = [(c['t_rel'], c['units']) for c in cnts if (c.get('units') or 0) > 0]
        rec['w0_first_units_gt0'] = nz[0] if nz else None
        rec['w0_gate'] = j.get('gate')
    rows.append(rec)

hdr = ('dir', 'verdict', 'w0_verdict', 'flag_in_argv', 'h7_flag_field', 'harness', 'sha16',
       'w0_span', 'w0_n', 'w0_f0', 'w0_fmax', 'w0_units_firstrow', 'w0_first_units_gt0',
       'trip_seconds', 'rc', 'dur')
print('\t'.join(hdr))
for r in rows:
    g = {k: r.get(k) for k in hdr}
    gt = g.pop('w0_gate', None)
    out = []
    for k in hdr:
        v = g.get(k) if k in g else r.get(k)
        out.append('' if v is None else str(v))
    print('\t'.join(out))
print()
print('--- gate recorded vs payload gate for the no_advance/units0==0 rows ---')
for r in rows:
    if str(r.get('w0_units_firstrow')) == '0' or r.get('verdict') == 'no_advance':
        print(r['dir'], '| fields gate =', r.get('gate'), '| json gate =', r.get('w0_gate'))
