"""Find candidates with falsifiable 0/1 return contract (③b②) / setcc-return."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT = BASE + r'\S09_KPROVED7\work'
pool = json.load(open(OUT + r'\features.json', encoding='utf-8'))
for r in sorted(pool, key=lambda x: x['entry']):
    d = r['_det']
    if d['size'] > 3000: continue
    dis = r['_disasm']
    txt = '\n'.join(dis)
    has_ret0 = ('xor eax, eax' in txt or 'mov eax, 0' in txt)
    has_ret1 = ('mov eax, 1' in txt or 'mov al, 1' in txt)
    ret_count = sum(1 for l in dis if ' ret' in l.split(' ',2)[-1] if False)  # placeholder
    ret_count = sum(1 for l in dis if (' ret' in l) and ('ret' in l.split(':',1)[-1].strip().split(' ')[0:2]))
    setcc = [l for l in dis if ' set' in l.split(':',1)[-1]]
    if (has_ret0 and has_ret1) or setcc:
        print('### %s %s sz=%d ret0=%s ret1=%s setcc=%d' % (r['entry'], r['name'], d['size'], has_ret0, has_ret1, len(setcc)))
