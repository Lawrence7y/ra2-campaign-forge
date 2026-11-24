# -*- coding: utf-8 -*-
# N16-4: window tail time = t_abs0 + span_s (+settle_s) from measure_w*.json;
# png mtime offset vs window tail and vs forensics ts.
# Also: zero-progress classification (f0, df, logic_frames) per window, and p (blue-ratio, auxiliary only).
import os, json, glob, datetime, zlib, struct

ROOT = r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
DIRS = ['archive_T33','archive_T34','archive_T36','archive_T38','archive_T39',
        'archive_T40','archive_T41','archive_T42','archive_T43','archive_T44',
        'archive_T45','archive_T49_u0800','l1_20261023e4','l3_20261023r','ROOT']

def png_mtime(p):
    return datetime.datetime.fromtimestamp(os.stat(p).st_mtime)

def png_mtime_micro(p):
    st = os.stat(p)
    st_ns = st.st_mtime_ns
    return st_ns

for sub in DIRS:
    d = ROOT if sub == 'ROOT' else os.path.join(ROOT, sub)
    print('='*110)
    print('DIR', sub)
    # forensics ts per window
    fts = {}
    fp = os.path.join(d, 'qc151_fields.json')
    if os.path.exists(fp):
        with open(fp, 'r', encoding='utf-8') as f:
            items = json.load(f)
        for it in items:
            if isinstance(it, dict) and it.get('key','').startswith('measure_forensics_w'):
                w = it['value'].get('window')
                fts[w] = it.get('ts')
    for mf in sorted(glob.glob(os.path.join(d, 'measure_w*.json'))):
        base = os.path.basename(mf)
        w = base[len('measure_'):-len('.json')]
        png = os.path.join(d, base[:-len('.json')] + '_end_x.png')
        with open(mf, 'r', encoding='utf-8') as f:
            m = json.load(f)
        t_abs0 = m.get('t_abs0'); span = m.get('span_s'); settle = m.get('settle_s')
        tail = t_abs0 + (span or 0) + (settle or 0)
        tail_dt = datetime.datetime.fromtimestamp(tail)
        f0 = m['samples']['f'][0] if m.get('samples') and m['samples'].get('f') else None
        flist = m.get('samples', {}).get('f', [])
        fmin = min(flist) if flist else None
        fmax = max(flist) if flist else None
        lf = m.get('stats', {}).get('logic_frames')
        ne = m.get('stats', {}).get('n_edges')
        note = m.get('stats', {}).get('note')
        ts = fts.get(int(w[1:])) if w[1:].isdigit() else None
        line = '%s: tail=%s f0=%s fmin=%s fmax=%s lf=%s n_edges=%s note=%r' % (
            base, tail_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], f0, fmin, fmax, lf, ne, note)
        if os.path.exists(png):
            mt_ns = png_mtime_micro(png)
            mt_dt = datetime.datetime.fromtimestamp(mt_ns/1e9)
            off_tail = mt_ns/1e9 - tail
            line += ' | PNG mtime=%s off_tail=%+.3fs' % (mt_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], off_tail)
            if ts:
                tsv = datetime.datetime.fromisoformat(ts).timestamp()
                line += ' off_forensics_ts=%+.3fs' % (mt_ns/1e9 - tsv)
            if ts:
                tsv_dt = datetime.datetime.fromisoformat(ts)
                line += ' | forensics ts=%s off_ts_vs_tail=%+.3fs' % (ts, datetime.datetime.fromisoformat(ts).timestamp() - tail)
        else:
            line += ' | PNG MISSING'
        print(' ', line)
