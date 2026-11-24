import json, sys, hashlib, collections, statistics
p = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\D41_SUBST\_audit\EVIDENCE\a2_sites.json'
b = open(p, 'rb').read()
s = b.decode('utf-8')
d = json.loads(s)
calls = d['calls']
bounds = d['bounds']
print('== calls ==')
ks = list(calls.keys())
print('n_keys', len(ks))
print('first3_keys', ks[:3])
for k in ks[:3]:
    print('  KEY', k, 'type', type(calls[k]).__name__, 'len', len(calls[k]), 'val', calls[k][:8])
tot_targets = sum(len(v) for v in calls.values())
print('total_targets', tot_targets)
print('== bounds ==')
print('n', len(bounds))
print('elem_types', collections.Counter(type(x).__name__ for x in bounds))
for x in bounds[:3]:
    print('  ', repr(x))
print('  ', repr(bounds[-1]))
if isinstance(bounds[0], list):
    print('elem_len_counter', collections.Counter(len(x) for x in bounds).most_common(10))
