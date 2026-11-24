"""Q5-1 second implementation, fixed: operate on the calls half only, and count structurally."""
import re
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
raw = open(BASE + r'\D41_SUBST\_audit\EVIDENCE\a2_sites.json', 'rb').read()
s = raw.decode('utf-8')
CUT = s.index('}, "bounds": ["')          # 913237-ish boundary
head = s[:CUT]
tail = s[CUT + len('}, "bounds": ["'):-2]   # drop trailing ']}'
LOG = []
def P(*a):
    line=' '.join(str(x) for x in a); LOG.append(line); print(line, flush=True)

P('calls_half_chars', len(head), 'bounds_half_chars', len(tail), 'sum+overhead', len(head)+len(tail))
keys = re.findall(r'"([0-9A-F]{8})": \[', head)
# every 8-hex token in the calls half = keys + sites
toks = re.findall(r'"([0-9A-F]{8})"', head)
sites_n = len(toks) - len(keys)
P('[impl2 regex] keys=%d sites=%d total_records(keys+sites)=%d' % (len(keys), sites_n, len(keys)+sites_n))
bounds_toks = re.findall(r'"([0-9A-F]{8})"', tail)
P('[impl2 regex] bounds=%d total_records(keys+sites+bounds)=%d' % (len(bounds_toks), len(keys)+sites_n+len(bounds_toks)))
P('[impl2 regex] avg_bytes over (keys+sites+bounds) = %.6f' % (len(raw)/(len(keys)+sites_n+len(bounds_toks))))
P('[impl2 regex] avg_bytes over bounds only = %.6f' % (len(tail+'"')/len(bounds_toks)))
P('[impl2 regex] avg_bytes over calls keys only = %.6f' % (len(head)/len(keys)))
open(BASE + r'\R17_R95_T1_A2SITES\q5_impl2.out','w',encoding='utf-8').write('\n'.join(LOG))
