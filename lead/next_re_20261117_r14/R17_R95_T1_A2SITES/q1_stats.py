import json, collections, statistics
p = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\D41_SUBST\_audit\EVIDENCE\a2_sites.json'
s = open(p, 'rb').read().decode('utf-8')
d = json.loads(s)
calls = d['calls']; bounds = d['bounds']
CALLS_BYTES = 913237
BOUNDS_BYTES = 17624355 - 913237

def f(t): return int(t, 16)

bk = [f(x) for x in bounds]
print('== bounds ==')
print('n', len(bk), 'uniq', len(set(bk)))
print('min %08X max %08X' % (min(bk), max(bk)))
asc = all(bk[i] < bk[i+1] for i in range(len(bk)-1))
print('strictly ascending', asc)
srt = sorted(set(bk))
gaps = [(srt[i+1]-srt[i], srt[i], srt[i+1]) for i in range(len(srt)-1)]
gaps.sort(reverse=True)
print('top10 gaps', [('%08X..%08X d=%d' % (g[1], g[2], g[0])) for g in gaps[:10]])
print('step counter', collections.Counter(gaps[i][0] for i in range(min(5000, len(gaps)))).most_common(6))
intext = sum(1 for x in bk if 0x00400000 <= x < 0x00B00000)
print('in .text window 0x400000-0xB00000:', intext, '(%.2f%%)' % (100*intext/len(bk)))
print('below 0x00400000:', sum(1 for x in bk if x < 0x00400000))
print('>= 0x00B00000:', sum(1 for x in bk if x >= 0x00B00000))

print('== calls keys ==')
ck = [(k, f(k), len(v)) for k, v in calls.items()]
print('n_keys', len(ck), 'total_targets', sum(c[2] for c in ck))
sizes = [c[2] for c in ck]
print('targets_per_key min %d med %d mean %.2f max %d' % (min(sizes), statistics.median(sizes), statistics.mean(sizes), max(sizes)))
print('size_hist', collections.Counter(sizes).most_common(8))
print('key_dup_in_targets', sum(1 for c in ck if any(t == c[0] for t in calls[c[0]])))
keyvals = [c[1] for c in ck]
print('keys_in_bounds', sum(1 for x in keyvals if x in set(bk)), '/', len(keyvals))
allt = [f(t) for v in calls.values() for t in v]
print('targets_in_bounds', sum(1 for x in allt if x in set(bk)), '/', len(allt))
print('targets_in_text', sum(1 for x in allt if 0x00400000 <= x < 0x00B00000), '/', len(allt))
# do targets exist literally in bounds section text
btxt = s[CALLS_BYTES:]
print('target literal present in bounds text:', sum(1 for t in calls['00407100'] if ('"%s"' % t) in btxt))

print('== determinism / dups ==')
print('bounds dup count', len(bounds) - len(set(bounds)))
print('sorted already (string order == numeric order)', bounds == sorted(set(bounds)))
