"""Pin down the 1-element discrepancy between json parse and regex scan of "bounds"."""
import json, re
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
raw = open(BASE + r'\D41_SUBST\_audit\EVIDENCE\a2_sites.json', 'rb').read()
s = raw.decode('utf-8')
CUT = s.index('}, "bounds": ["')
MARK = '}, "bounds": ["'
LOG = []
def P(*a):
    line=' '.join(str(x) for x in a); LOG.append(line); print(line, flush=True)

d = json.loads(s); b = d['bounds']
P('json bounds len', len(b))
P('marker len', len(MARK), 'cut', CUT)
# Correct slicing: after the marker the array elements run until the final ']}'
start = CUT + len(MARK)
body = s[start:-2]
P('body chars', len(body), 'body[-20:]', repr(body[-20:]))
toks = re.findall(r'"([0-9A-F]{8})"', body)
P('regex tokens', len(toks))
P('json[0], toks[0]:', b[0], toks[0], b[0] == toks[0])
P('json[-1], toks[-1]:', b[-1], toks[-1], b[-1] == toks[-1])
# find the first index where they diverge
div = next((i for i in range(min(len(b), len(toks))) if b[i] != toks[i]), None)
P('first divergence at', div)
if div is not None:
    P('  json[div-1:div+3]', b[max(0,div-1):div+3])
    P('  toks[div-1:div+3]', toks[max(0,div-1):div+3])
    P('  json around', b[div-2:div+2])
    # Show raw text around the corresponding position
    idx = body.find('"%s"' % toks[div])
    P('  raw slice around divergence:', repr(body[max(0, idx-60):idx+80]))
else:
    P('  no divergence in overlap; lengths differ only at the tail')
    P('  last few json', b[-3:])
    P('  last few toks', toks[-3:])
    P('  raw body tail', repr(body[-120:]))
open(BASE + r'\R17_R95_T1_A2SITES\q5_div.out','w',encoding='utf-8').write('\n'.join(LOG))
