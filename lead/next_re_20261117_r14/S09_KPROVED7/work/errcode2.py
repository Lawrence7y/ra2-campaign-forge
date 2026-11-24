"""Corrected detector for jump tables / sentinels / neg1 returns across all candidates."""
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
    # indirect jmp with index
    indjmp = [l for l in dis if 'jmp' in l and 'ptr' in l]
    # -1 patterns
    neg1 = [l for l in dis if '0xffffffff' in l or 'ffffffff' in l or '-1' in l]
    # error-style constants
    hres = [l for l in dis if '80004' in l]
    if indjmp or neg1 or hres:
        print('### %s %s sz=%d indjmp=%d neg1=%d hres=%d' % (r['entry'], r['name'], d['size'], len(indjmp), len(neg1), len(hres)))
        for l in (indjmp+neg1+hres)[:15]:
            print('   ', l)
