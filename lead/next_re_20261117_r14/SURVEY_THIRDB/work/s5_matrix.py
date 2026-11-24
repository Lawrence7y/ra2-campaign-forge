"""s5: MATRIX3B.tsv (21 subsystems + TOTAL) + long-extent veto check + sensitivities."""
import sys, json, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core as C, b3

C.build_jt()
rows = json.loads((C.OUT/'work'/'rows3b.json').read_text(encoding='utf-8'))
SUBS = ['S%02d' % i for i in range(1, 22)]
CH = ['③b①', '③b②', '③b③', '③b④']

# --- long-extent veto check: does any ③b evidence site sit beyond [lo, lo+atlas_size)? ---
bad = []
for r in rows:
    if not r['cats'] or r['span'] <= r['atlas_size']: continue
    lim_hi = r['lo'] + r['atlas_size']
    sites = []
    for h in r['b1']: sites.append(h[1])
    for h in r['b2']: sites.append(int(h[1]))
    for k in ('head', 'back'):
        if isinstance(r['b4'].get(k), int): sites.append(r['b4'][k])
    if sites and all(s >= lim_hi for s in sites):
        bad.append((r['sub'], r['entry'], r['atlas_size'], r['span'], r['cats']))
print('③b rows with long extent:', sum(1 for r in rows if r['cats'] and r['span'] > r['atlas_size']))
print('  of which ALL evidence sites fall outside the atlas range (veto candidates):', len(bad))
for x in bad[:10]: print('    ', x)

# --- per-subsystem table ---
def g(r, field='cats'): return r.get(field) or []

tab = []
for s in SUBS:
    rr = [r for r in rows if r['sub'] == s]
    n = len(rr)
    c1 = sum(1 for r in rr if '③b①' in g(r))
    c2 = sum(1 for r in rr if '③b②' in g(r))
    c3 = sum(1 for r in rr if '③b③' in g(r))
    c4 = sum(1 for r in rr if '③b④' in g(r))
    tot = sum(1 for r in rr if g(r))
    a = n - tot
    pct = 100.0*tot/n if n else 0.0
    alts = sum(1 for r in rr if g(r, 'cats_alt'))
    sent = sum(1 for r in rr if g(r, 'cats_sent'))
    tab.append(dict(sub=s, n=n, c1=c1, c2=c2, c3=c3, c4=c4, tot=tot, a=a, pct=pct,
                    alts=alts, sent=sent,
                    overlap=sum(1 for r in rr if len(g(r)) > 1)))

tot = dict(sub='TOTAL', n=sum(t['n'] for t in tab), c1=sum(t['c1'] for t in tab),
           c2=sum(t['c2'] for t in tab), c3=sum(t['c3'] for t in tab),
           c4=sum(t['c4'] for t in tab), tot=sum(t['tot'] for t in tab),
           a=sum(t['a'] for t in tab), alts=sum(t['alts'] for t in tab),
           sent=sum(t['sent'] for t in tab), overlap=sum(t['overlap'] for t in tab))
tot['pct'] = 100.0*tot['tot']/tot['n'] if tot['n'] else 0.0
tab.append(tot)

hdr = ('subsystem\t池n\t③b①\t③b②\t③b③\t③b④\t③b合计\t③a\t占比%\t'
       'sens_A_②含cmp-1\t多通道行')
with open(C.OUT/'MATRIX3B.tsv', 'w', encoding='utf-8', newline='\n') as f:
    f.write(hdr+'\n')
    for t in tab:
        f.write('%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%.2f\t%d\t%d\n' % (
            t['sub'], t['n'], t['c1'], t['c2'], t['c3'], t['c4'], t['tot'], t['a'],
            t['pct'], t['sent'], t['overlap']))
print('\nwrote MATRIX3B.tsv')
print('%-6s %5s %5s %4s %4s %4s %6s %6s %7s' % ('sub', 'pool', '③b①', '②', '③', '④', '合计', '③a', '占比%'))
for t in tab:
    print('%-6s %5d %5d %4d %4d %4d %6d %6d %7.2f' % (
        t['sub'], t['n'], t['c1'], t['c2'], t['c3'], t['c4'], t['tot'], t['a'], t['pct']))
json.dump(tab, open(C.OUT/'work'/'matrix3b.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
