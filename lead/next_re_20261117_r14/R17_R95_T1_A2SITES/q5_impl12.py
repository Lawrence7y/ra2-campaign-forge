import json, re
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
raw = open(BASE + r'\D41_SUBST\_audit\EVIDENCE\a2_sites.json', 'rb').read()
s = raw.decode('utf-8')
LOG = []
def P(*a):
    line=' '.join(str(x) for x in a); LOG.append(line); print(line, flush=True)

# impl1: json module
d = json.loads(s)
c = d['calls']; b = d['bounds']
nk, ns, nb = len(c), sum(len(v) for v in c.values()), len(b)
n = nk + ns + nb
P('[impl1 json]  keys=%d sites=%d bounds=%d total=%d avg=%.6f' % (nk, ns, nb, n, len(raw)/n))
P('[impl1 json]  bounds_avg=%.6f calls_kv_avg=%.6f' % (len(raw)/nb, 913237/nk))

# impl2: regex, and the -1 anomaly explained
CUT = s.index('}, "bounds": ["')
head, tail = s[:CUT], s[CUT + len('}, "bounds": ["'):-2]
keys = re.findall(r'"([0-9A-F]{8})": \[', head)
toks = re.findall(r'"([0-9A-F]{8})"', head)
sites_n = len(toks) - len(keys)
btoks = re.findall(r'"([0-9A-F]{8})"', tail)
P('[impl2 regex] keys=%d sites=%d bounds=%d total=%d avg=%.6f' % (len(keys), sites_n, len(btoks), len(keys)+sites_n+len(btoks), len(raw)/(len(keys)+sites_n+len(btoks))))
P('[impl2 regex] bounds_avg=%.6f' % ((len(tail)+1)/len(btoks)))
P('agree: keys %s sites %s total %s avg %s' % (nk == len(keys), ns == sites_n, nb == len(btoks),
                                               abs(len(raw)/n - len(raw)/(len(keys)+sites_n+len(btoks))) < 1e-9))
P('')
P('bounds count discrepancy (json=%d regex=%d) explanation:' % (nb, len(btoks)))
last_elem = b[-1]
pos_last = tail.rindex('"' + last_elem + '"')
P('  last bound = %s ; its quoted occurrence inside the tail slice at %d ; tail len %d' % (last_elem, pos_last, len(tail)))
P('  re.findall on tail: need closing quote after token -> last token is cut by the -2 slice for the closing "]}", so regex needs [:-2] -> count %d' % len(re.findall(r'"([0-9A-F]{8})"', tail + '"')))
P('  recomputed with re-closed tail: %d (== json %d ? %s)' % (len(re.findall(r'"([0-9A-F]{8})"', tail + '"')), nb, len(re.findall(r'"([0-9A-F]{8})"', tail + '"')) == nb))
open(BASE + r'\R17_R95_T1_A2SITES\q5_impl1_2.out','w',encoding='utf-8').write('\n'.join(LOG))
