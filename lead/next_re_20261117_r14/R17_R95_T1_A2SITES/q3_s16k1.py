import json
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
calls = json.load(open(BASE + r'\D41_SUBST\_audit\EVIDENCE\a2_sites.json', 'rb'))['calls'] if False else json.loads(open(BASE + r'\D41_SUBST\_audit\EVIDENCE\a2_sites.json','rb').read().decode('utf-8'))['calls']
mine = set((k.upper(), s.upper()) for k, v in calls.items() for s in v)

p3 = BASE + r'\S16-K1\work\calls_map.json'
o3 = json.load(open(p3, encoding='utf-8'))['calls']
k0 = list(o3.keys())[0]
print('S16-K1 key sample', repr(k0), 'value sample', o3[k0][:4])
# check: are values SITES or TARGETS?  use a2 mapping to see whether k0's values equal mine's sites for k0
kk = k0[2:].upper() if k0.lower().startswith('0x') else k0.upper()
print('as target ->', kk, 'a2 sites', calls.get(kk, [])[:4])
# maybe roles swapped: key = site, values = targets
vals = o3[k0]
print('as-site lookup in a2 (invert):')
inv = {}
for t, v in calls.items():
    for s in v:
        inv.setdefault(s.upper(), []).append(t.upper())
print('  inv[k0no0x]=', inv.get(kk))
print('  inv[first value]=', inv.get(vals[0][2:].upper() if vals[0].lower().startswith('0x') else vals[0].upper()))
