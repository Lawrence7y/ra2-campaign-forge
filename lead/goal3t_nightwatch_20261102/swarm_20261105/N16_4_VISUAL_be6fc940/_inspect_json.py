# -*- coding: utf-8 -*-
# N16-4: inspect qc151_fields.json forensics + measure_w*.json window tails for the 14 dirs holding the 25+2 PNGs.
import os, json

ROOT = r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
DIRS = ['archive_T33','archive_T34','archive_T36','archive_T38','archive_T39',
        'archive_T40','archive_T41','archive_T42','archive_T43','archive_T44',
        'archive_T45','archive_T49_u0800','l1_20261023e4','l3_20261023r']

for sub in DIRS:
    d = os.path.join(ROOT, sub)
    files = sorted(os.listdir(d))
    jss = [f for f in files if f.endswith('.json')]
    print('='*100)
    print('DIR', sub)
    print('  json files:', jss)
    # qc151_fields.json forensics
    for cand in ('qc151_fields.json','qc151_fields_post.json'):
        p = os.path.join(d, cand)
        if not os.path.exists(p):
            print('  [%s] MISSING' % cand)
            continue
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print('  [%s] LOAD ERROR %r' % (cand, e))
            continue
        if isinstance(data, dict):
            keys = list(data.keys())
            print('  [%s] top keys: %s' % (cand, keys))
            for key in ('forensics','forensic','capture','screens','screen_caps'):
                if key in data:
                    print('   %s -> %s' % (key, json.dumps(data[key], ensure_ascii=False)[:1200]))
        else:
            print('  [%s] type=%s len=%s' % (cand, type(data).__name__, len(data)))
            for i, item in enumerate(data if isinstance(data, list) else []):
                if isinstance(item, dict) and any('forensic' in str(k).lower() or 'png' in str(item).lower() for k in item):
                    print('   item%d: %s' % (i, json.dumps(item, ensure_ascii=False)[:800]))
    # measure_w*.json window tails
    mw = [f for f in jss if f.startswith('measure_w')]
    for f in mw:
        p = os.path.join(d, f)
        try:
            with open(p, 'r', encoding='utf-8') as g:
                mdata = json.load(g)
        except Exception as e:
            print('  [%s] LOAD ERROR %r' % (f, e))
            continue
        keys = list(mdata.keys()) if isinstance(mdata, dict) else None
        print('  [%s] keys: %s' % (f, keys))
        for key in ('window_end','end_time','t_end','window','meta','ts_end','ended_at','end_iso'):
            if isinstance(mdata, dict) and key in mdata:
                print('   %s = %s' % (key, json.dumps(mdata[key], ensure_ascii=False)[:400]))
