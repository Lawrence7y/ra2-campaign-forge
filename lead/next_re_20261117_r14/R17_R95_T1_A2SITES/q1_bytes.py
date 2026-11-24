import json, hashlib, re
p = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\D41_SUBST\_audit\EVIDENCE\a2_sites.json'
b = open(p, 'rb').read()
s = b.decode('utf-8')
d = json.loads(s)
calls = d['calls']; bounds = d['bounds']
i = s.index('"bounds"')
print('bounds_key_offset', i)
print('HEAD_0_120:', s[:120])
print('BOUNDS_PRE:', s[i-60:i+120])
print('TAIL:', s[-40:])
# where does calls end
j = s.rindex('}, "bounds"') if '}, "bounds"' in s else -1
print('calls_end_marker', j)
# count literal occurrences
print('count {" in file', s.count('{"'))
print('count ": [" ', s.count('": ["'))
print('json byte len compact check', len(json.dumps(d, separators=(', ', ': '))))
