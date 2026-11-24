
import sys, os, json
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work')
import importlib.util
spec = importlib.util.spec_from_file_location('eng', r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\engine.py')
eng = importlib.util.module_from_spec(spec); spec.loader.exec_module(eng)

OUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\EVIDENCE'
os.makedirs(OUT, exist_ok=True)

rows = []
for line in open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\weak105.tsv', encoding='utf-8'):
    f = line.rstrip('\n').split('\t')
    if len(f) < 5: continue
    if f[0] == 'entry': continue
    if f[1] == 'S22': continue
    rows.append({'entry':f[0],'sub':f[1],'name':f[2],'cls':f[3],'sem':f[4]})

print('rows', len(rows))
res = []
for r in rows:
    va = int(r['entry'], 16)
    try:
        feats, body = eng.analyze(va)
        feats['sub'] = r['sub']; feats['cls'] = r['cls']; feats['nm'] = r['name']; feats['sem'] = r['sem']
        res.append(feats)
        eng.dump(va, OUT)
    except Exception as e:
        res.append({'entry':r['entry'],'sub':r['sub'],'cls':r['cls'],'nm':r['name'],'sem':r['sem'],'error':str(e)})
json.dump(res, open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\work\feats.json','w',encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('done')
for x in res[:200]:
    if 'error' in x: print('ERR', x['entry'], x['error']); continue
    print('%s %s %-3s n=%-4d jcc=%-2d loops=%d jt=%d calls=%-3d pushsz=%-2d orM1=%d' % (
        x['entry'], x['cls'], x['sub'], x['n_instr'], x['jcc'], x['loop_count'], x['n_jmp_table'], x['n_call'], len(x['push_sizes']), x['or_minus1']))
