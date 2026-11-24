"""Final, self-checked Q5-1 reconciliation. Two implementations, same definition, must agree."""
import json, re
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
raw = open(BASE + r'\D41_SUBST\_audit\EVIDENCE\a2_sites.json', 'rb').read()
s = raw.decode('utf-8')
MARK = '}, "bounds": ["'
CUT = s.index(MARK)
LOG = []
def P(*a):
    line=' '.join(str(x) for x in a); LOG.append(line); print(line, flush=True)

d = json.loads(s)
c, b = d['calls'], d['bounds']
nk, ns, nb = len(c), sum(len(v) for v in c.values()), len(b)

P('--- impl1 (json module) ---')
P('keys=%d sites=%d bounds=%d total_records=%d file_bytes=%d' % (nk, ns, nb, nk+ns+nb, len(raw)))
P('avg_bytes(keys+sites+bounds) = %.6f' % (len(raw)/(nk+ns+nb)))
P('bounds_section_bytes=%d avg=%.6f' % (len(s)-CUT, (len(s)-CUT)/nb))
P('calls_section_bytes=%d avg_kv=%.6f' % (CUT, CUT/nk))

P('')
P('--- impl2 (regex, same definition) ---')
head = s[:CUT]
body = s[CUT+len(MARK):-2]
P('head chars=%d body chars=%d  (marker %d, trailing "]}": 2)' % (len(head), len(body), len(MARK)))
keys2 = re.findall(r'"([0-9A-F]{8})": \[', head)
# every 8-hex quoted token in head is either a key or one site
toks_head = re.findall(r'"([0-9A-F]{8})"', head)
P('head tokens=%d keys=%d -> sites=%d (sanity: all head tokens are 8-hex? %s)' %
  (len(toks_head), len(keys2), len(toks_head)-len(keys2),
   len(re.findall(r'"(?![0-9A-F]{8}")[\s\S]', head)) == 0))
btoks = re.findall(r'"([0-9A-F]{8})"', body)
P('body tokens(bounds)=%d' % len(btoks))
P('keys=%d sites=%d bounds=%d total_records=%d' % (len(keys2), len(toks_head)-len(keys2), len(btoks), len(keys2)+(len(toks_head)-len(keys2))+len(btoks)))
P('avg_bytes(keys+sites+bounds) = %.6f' % (len(raw)/(len(keys2)+(len(toks_head)-len(keys2))+len(btoks))))
P('bounds_section_bytes=%d avg=%.6f' % (len(s)-CUT, (len(s)-CUT)/len(btoks)))
P('calls_section_bytes=%d avg_kv=%.6f' % (len(head), len(head)/len(keys2)))

P('')
P('--- agreement ---')
P('keys  %d == %d -> %s' % (nk, len(keys2), nk == len(keys2)))
P('sites %d == %d -> %s' % (ns, len(toks_head)-len(keys2), ns == len(toks_head)-len(keys2)))
P('bounds %d == %d -> %s' % (nb, len(btoks), nb == len(btoks)))
tot1 = nk+ns+nb; tot2 = len(keys2)+(len(toks_head)-len(keys2))+len(btoks)
P('total %d == %d -> %s' % (tot1, tot2, tot1 == tot2))
P('avg %.6f == %.6f -> %s' % (len(raw)/tot1, len(raw)/tot2, abs(len(raw)/tot1-len(raw)/tot2) < 1e-9))
# element-level equality (stronger than counts)
P('bounds element lists identical: %s' % (b == btoks))
P('keys list identical: %s' % (list(c.keys()) == keys2))
open(BASE + r'\R17_R95_T1_A2SITES\q5_final.out','w',encoding='utf-8').write('\n'.join(LOG))
