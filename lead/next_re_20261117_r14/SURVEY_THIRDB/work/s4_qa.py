"""s4: QA — extent vs atlas size, per-channel samples for manual audit."""
import sys, json, collections, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core as C, b3

C.build_jt()
rows = json.loads((C.OUT/'work'/'rows3b.json').read_text(encoding='utf-8'))

print('=== extent vs atlas_size ===')
d = collections.Counter()
short = []
for r in rows:
    a, s = r['atlas_size'], r['span']
    if a <= 0: d['atlas_bad'] += 1; continue
    if s == a: d['exact'] += 1
    elif s < a: d['short'] += 1; short.append((r['sub'], r['entry'], a, s, r['verdict']))
    else: d['long'] += 1
print(d)
short.sort(key=lambda x: x[3]/max(x[2],1))
print('10 most-truncated (sub, entry, atlas, span, verdict):')
for x in short[:10]: print('   ', x)

print('\n=== channel counts (strict) ===')
print(collections.Counter(c for r in rows for c in r['cats']))
print('② detail:', collections.Counter(h[0] for r in rows for h in r['b2']))
print('\n=== ③b 合计 by row ===')
print('rows with >=1 channel:', sum(1 for r in rows if r['cats']))

print('\n=== ③b① samples (12) ===')
h1 = [r for r in rows if '③b①' in r['cats']]
random.seed(1)
for r in random.sample(h1, min(12, len(h1))):
    print('  %s %s n=%d  %s' % (r['sub'], r['entry'], r['n_ins'], r['b1'][:1]))

print('\n=== ③b② samples (10) ===')
h2 = [r for r in rows if '③b②' in r['cats']]
for r in random.sample(h2, min(10, len(h2))):
    print('  %s %s  %s' % (r['sub'], r['entry'], r['b2'][:1]))

print('\n=== ③b③ all ===')
for r in [x for x in rows if '③b③' in x['cats']]:
    print('  %s %s ctor=%d vt=%d maxdisp=%#x size=%s' % (
        r['sub'], r['entry'], r['b3']['n_ctor'], r['b3']['n_vt'], r['b3']['max_disp'], r['b3']['size'][:2]))

print('\n=== ③b④ samples (12) ===')
h4 = [r for r in rows if '③b④' in r['cats']]
for r in random.sample(h4, min(12, len(h4))):
    b = r['b4']
    print('  %s %s loop %08X..%08X n=%d' % (r['sub'], r['entry'], b['head'], b['back'], b['n']))
