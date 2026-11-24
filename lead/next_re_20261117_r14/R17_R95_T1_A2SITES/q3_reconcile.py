import json, struct
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
blob = open(EXE, 'rb').read()
TEXT_RAW, TEXT_VA, TEXT_VSZ = 4096, 0x00401000, 4060045
foff = lambda va: TEXT_RAW + (va - TEXT_VA)

d = json.loads(open(BASE + r'\D41_SUBST\_audit\EVIDENCE\a2_sites.json', 'rb').read().decode('utf-8'))
calls = d['calls']; bounds = d['bounds']
bset = set(int(x, 16) for x in bounds)

def check_sites(target_hex, sites, label):
    ok = 0; det = []
    for sh in sites:
        sva = int(sh, 16)
        so = foff(sva)
        good = blob[so] == 0xE8 and ((sva + 5 + struct.unpack_from('<i', blob, so+1)[0]) & 0xFFFFFFFF) == int(target_hex, 16)
        ok += good
        det.append((sh, good))
    print('%-40s target=%s sites=%d: E8+rel32 match %d/%d' % (label, target_hex, len(sites), ok, len(sites)))
    return ok, det

# --- S16-K1: strip 0x, 7-digit (leading zero dropped) ---
o3 = json.load(open(BASE + r'\S16-K1\work\calls_map.json', encoding='utf-8'))['calls']
z = lambda x: ('%08X' % int(x, 16))
p3 = set((z(k), z(s)) for k, v in o3.items() for s in v)
mine = set((k.upper(), s.upper()) for k, v in calls.items() for s in v)
print('S16-K1 pairs', len(p3), 'identical to a2 after %08X normalisation:', p3 == mine)

# --- C01_census: their 1 missing pair ---
o4 = json.load(open(BASE + r'\C01_census\EVIDENCE\callgraph.json', encoding='utf-8'))
f4 = set(('%08X' % int(k), '%08X' % r['site']) for k, v in o4.items() for r in v)
print('C01 pairs', len(f4), 'mine-only', len(mine - f4), 'theirs-only', len(f4 - mine))
print('theirs-only', sorted(f4 - mine))
# their key/base semantics
k0 = list(o4.keys())[0]
print('C01 key', k0, 'dec', int(k0), '- base', int(k0) - 0x400000, '=', hex(int(k0) - 0x400000))
t, s0 = sorted(f4 - mine)[0]
print('checking theirs-only pair', t, s0)
check_sites(t, [s0], 'C01 theirs-only')

print()
print('=== Q3 3 records to verify (chosen by sampling rule) ===')
keys = list(calls.keys())
pick_keys = [keys[0], keys[1], keys[2], keys[len(keys)//3], keys[2*len(keys)//3], keys[-3]]
for k in pick_keys[:3]:
    sites = calls[k]
    ok, det = check_sites(k, sites, 'A2 rec')
    print('   in bounds:', all(int(x,16) in bset for x in sites), ' | sample sites', sites[:5], '| n=', len(sites))
