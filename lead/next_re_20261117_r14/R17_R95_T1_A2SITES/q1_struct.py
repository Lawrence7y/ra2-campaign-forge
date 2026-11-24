import json, sys, hashlib
p = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\D41_SUBST\_audit\EVIDENCE\a2_sites.json'
b = open(p, 'rb').read()
print('file_bytes', len(b))
print('sha256', hashlib.sha256(b).hexdigest().upper())
s = b.decode('utf-8')
print('chars', len(s))
i = s.rfind('"}')
print('rfind_close_brace_quote', i)
d = json.loads(s)
print('top_type', type(d).__name__)
print('top_keys', list(d.keys()))
for k, v in d.items():
    print('KEY', repr(k), type(v).__name__, 'len', len(v) if hasattr(v, '__len__') else 'n/a')
