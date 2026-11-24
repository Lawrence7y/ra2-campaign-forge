"""Does '00401000' occur verbatim as a bounds token? And a raw-byte count decoupled from JSON."""
import json, re
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
P0 = BASE + r'\D41_SUBST\_audit\EVIDENCE\a2_sites.json'
raw = open(P0, 'rb').read()
s = raw.decode('utf-8')
MARK = '}, "bounds": ["'
CUT = s.index(MARK)
LOG = []
def P(*a):
    line=' '.join(str(x) for x in a); LOG.append(line); print(line, flush=True)

d = json.loads(s); b = d['bounds']
P('json bounds[0:6]', b[:6])
P("raw file contains '00401000' ? ", '00401000' in s, 'count', s.count('00401000'))
P('first occurrence offset', s.find('00401000'))
P('context', repr(s[max(0, s.find('00401000')-30): s.find('00401000')+40]))
body = s[CUT+len(MARK):-2]
P('body.find("00401000")', body.find('00401000'))
P('body[:40]', repr(body[:40]))

# impl3: raw-byte, structure-blind token count (no JSON, no regex on parsed text)
P('')
P('--- impl3: raw 8-hex token count over whole file (structure-blind) ---')
toks_all = re.findall(rb'[0-9A-F]{8}', raw)
P('all 8-hex tokens in the file: %d' % len(toks_all))
head_b, body_b = raw[:CUT], raw[CUT:]
P('tokens in calls half: %d ; tokens in bounds half: %d ; sum %d' %
  (len(re.findall(rb'[0-9A-F]{8}', head_b)), len(re.findall(rb'[0-9A-F]{8}', body_b)),
   len(re.findall(rb'[0-9A-F]{8}', head_b)) + len(re.findall(rb'[0-9A-F]{8}', body_b))))
open(BASE + r'\R17_R95_T1_A2SITES\q5_deep.out','w',encoding='utf-8').write('\n'.join(LOG))
