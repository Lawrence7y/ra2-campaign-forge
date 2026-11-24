"""Compact full disasm for all remaining not-yet-examined candidates."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
OUT = BASE + r'\S09_KPROVED7\work'
pool = {r['entry']: r for r in json.load(open(OUT + r'\features.json', encoding='utf-8'))}
ents = ['0048E620','004E1480','004E1A20','004E1A40','004F3B10','005565F0','005BDA80','005BDAA0',
        '005BDF30','005BDF50','0063F7C0','0063F7E0','00653F70','00658770','006922E0',
        '006AC5D0','006AC5E0','006D1800','004E19A0','00557800','006938C0']
for e in ents:
    r = pool.get(e)
    if not r: continue
    d = r['_det']
    print('='*80)
    print('%s %s sz=%d ins=%d direct=%d holds=%d' % (e, r['name'], d['size'], d['nins'], r['n_direct'], r['n_holds']))
    for l in r['_disasm']:
        print('  ', l)
