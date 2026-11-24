import json, re
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
raw = open(BASE + r'\D41_SUBST\_audit\EVIDENCE\a2_sites.json', 'rb').read()
s = raw.decode('utf-8')
MARK = '}, "bounds": ["'
CUT = s.index(MARK)
LOG = []
def P(*a):
    line=' '.join(str(x) for x in a); LOG.append(line); print(line, flush=True)

head, body = s[:CUT], s[CUT+len(MARK):-2]
P('head chars', len(head), 'body chars', len(body))
P('--- how the calls half is laid out (first 220 chars) ---')
P(repr(head[:220]))
P('')
P('--- how the bounds half is laid out (first 160 chars) ---')
P(repr(body[:160]))
P('')
P('--- naive segmentation by the R92 method (no  }{  / newline inside -> falls back) ---')
seg = [p for p in re.split(r'"\s*,\s*"', s) if p.strip()]
P('segments produced by q2_rejudge.segments() on this file:', len(seg))
P('seg[0] (first 120):', repr(seg[0][:120]))
P('seg[1] (first 120):', repr(seg[1][:120]))
P('seg[-1] (last 120):', repr(seg[-1][-120:]))
# per-segment classification: how many segments are single address tokens?
pure_addr = sum(1 for x in seg if re.fullmatch(r'[0-9A-F]{8}', x.strip().strip('{}[]')))
P('segments that are exactly one 8-hex token:', pure_addr, '/', len(seg))
# how many contain a colon key (i.e. a target->[sites] record)?
withkey = sum(1 for x in seg if re.search(r'[0-9A-F]{8}":\s*\[', x))
P('segments containing a "target": [sites] key:', withkey)
open(BASE + r'\R17_R95_T1_A2SITES\q2_boundary.out','w',encoding='utf-8').write('\n'.join(LOG))
