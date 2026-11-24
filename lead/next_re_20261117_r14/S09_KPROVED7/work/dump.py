"""Dump disassembly for selected entries from features.json, plus holdings."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT = BASE + r'\S09_KPROVED7\work'
pool = {r['entry']: r for r in json.load(open(OUT + r'\features.json', encoding='utf-8'))}
ents = sys.argv[1:]
for e in ents:
    r = pool.get(e)
    if not r:
        print('NOT FOUND', e); continue
    d = r['_det']
    print('=' * 100)
    print('%s  %s  size=%d ins=%d direct=%d holds=%d' % (e, r['name'], d['size'], d['nins'], r['n_direct'], r['n_holds']))
    print('holds:', r['holds'])
    print('direct_sites:', r['direct_sites'])
    print('jt:', d['jt'])
    print('loops:', d['loops'])
    print('sentinel:', d['sentinel'][:10])
    print('nonstack_writes(%d):' % d['nwrites'], d['writes'][:20])
    print('--- disasm ---')
    for l in r['_disasm']:
        print(l)
