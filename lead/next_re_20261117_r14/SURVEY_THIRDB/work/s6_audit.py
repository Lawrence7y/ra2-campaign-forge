"""s6: manual-audit dump — a handful of accepted rows, decoded, so a human can eyeball them."""
import sys, json, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core as C, b3

C.build_jt()
rows = json.loads((C.OUT/'work'/'rows3b.json').read_text(encoding='utf-8'))
random.seed(20261119)

def dump(fn, lo, hi):
    for i in fn.ins:
        if lo <= i.address <= hi:
            print('      %08X %-16s %s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))

print('########## ③b① audits ##########')
h1 = [r for r in rows if '③b①' in r['cats']]
for r in random.sample(h1, 3):
    fn = b3.Fn(int(r['entry'], 16))
    print('\n--- %s %s  %s' % (r['sub'], r['entry'], r['b1'][:1]))
    site = r['b1'][0][1]
    dump(fn, site-24, site+8)

print('\n########## ③b② audits (all 30) ##########')
for r in [x for x in rows if '③b②' in x['cats']]:
    print('  %s %s  %s' % (r['sub'], r['entry'], r['b2'][:1]))

print('\n########## ③b④ audit sample ##########')
h4 = [r for r in rows if '③b④' in r['cats']]
for r in random.sample(h4, 2):
    fn = b3.Fn(int(r['entry'], 16))
    b = r['b4']
    print('\n--- %s %s loop %08X..%08X n=%d ind=%s bound=%s' % (
        r['sub'], r['entry'], b['head'], b['back'], b['n'], b['ind'], b['bound']))
    dump(fn, b['head'], min(b['back'] + 1, b['head'] + 60))

print('\n########## rows where extent != atlas size (23) ##########')
for r in [x for x in rows if x['span'] != x['atlas_size']]:
    print('  %s %s atlas=%d span=%d %s' % (r['sub'], r['entry'], r['atlas_size'], r['span'], r['cats']))
