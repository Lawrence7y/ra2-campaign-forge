import json, collections, statistics, sys
p = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\D41_SUBST\_audit\EVIDENCE\a2_sites.json'
s = open(p, 'rb').read().decode('utf-8')
d = json.loads(s)
calls = d['calls']; bounds = d['bounds']
CALLS_BYTES = 913237
BOUNDS_BYTES = 17624355 - CALLS_BYTES
out = []
def P(*a):
    line = ' '.join(str(x) for x in a)
    out.append(line); print(line, flush=True)

def f(t): return int(t, 16)

bk = [f(x) for x in bounds]
bset = set(bk)
P('== bounds ==')
P('n', len(bk), 'uniq', len(bset))
P('min %08X max %08X' % (min(bk), max(bk)))
asc = all(bk[i] < bk[i+1] for i in range(len(bk)-1))
P('strictly ascending', asc)
gaps = [(bset_sorted[i+1]-bset_sorted[i], bset_sorted[i], bset_sorted[i+1]) for bset_sorted in [sorted(bset)] for i in range(len(bset_sorted)-1)]
gaps.sort(reverse=True)
P('top10 gaps', [('%08X..%08X d=%d' % (g[1], g[2], g[0])) for g in gaps[:10]])
P('gap_counter(60k smallest)', collections.Counter(g[0] for g in gaps[-60000:]).most_common(6))
intext = sum(1 for x in bk if 0x00400000 <= x < 0x00B00000)
P('in .text window 0x400000-0xB00000: %d (%.2f%%)' % (intext, 100*intext/len(bk)))
P('below 0x00400000:', sum(1 for x in bk if x < 0x00400000))
P('>= 0x00B00000:', sum(1 for x in bk if x >= 0x00B00000))

P('== calls ==')
ck = [(k, f(k), len(v)) for k, v in calls.items()]
P('n_keys', len(ck), 'total_targets', sum(c[2] for c in ck))
sizes = [c[2] for c in ck]
P('targets_per_key min %d med %s mean %.2f max %d' % (min(sizes), statistics.median(sizes), statistics.mean(sizes), max(sizes)))
P('size_hist', collections.Counter(sizes).most_common(8))
P('self_loop_keys', sum(1 for c in ck if c[0] in calls[c[0]]))
keyvals = [c[1] for c in ck]
P('keys_in_bounds %d / %d' % (sum(1 for x in keyvals if x in bset), len(keyvals)))
allt = [f(t) for v in calls.values() for t in v]
P('targets_in_bounds %d / %d' % (sum(1 for x in allt if x in bset), len(allt)))
P('targets_also_call_keys %d / %d' % (sum(1 for x in allt if x in set(keyvals)), len(allt)))
P('targets_in_text %d / %d' % (sum(1 for x in allt if 0x00400000 <= x < 0x00B00000), len(allt)))
t0 = calls['00407100']
btxt = s[CALLS_BYTES:]
P('target literal present in bounds text:', sum(1 for t in t0 if ('"%s"' % t) in btxt), '/', len(t0))

P('== raw ==')
P('bounds_key_offset', s.index('"bounds"'))
P('calls_bytes %d bounds_bytes %d sum %d' % (CALLS_BYTES, BOUNDS_BYTES, CALLS_BYTES+BOUNDS_BYTES))
P('avg_record_bytes whole(6728+1392592)', '%.2f' % (17624355/ (6728+1392592)))
P('avg_calls_kv', '%.2f' % (CALLS_BYTES/6728))
P('avg_bound_elem', '%.2f' % (BOUNDS_BYTES/1392592))
open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R95_T1_A2SITES\q1_stats.out','w',encoding='utf-8').write('\n'.join(out))
