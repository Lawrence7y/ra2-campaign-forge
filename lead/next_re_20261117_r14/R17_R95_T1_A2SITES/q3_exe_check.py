import json, glob, os, struct
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
print('EXE exists', os.path.exists(EXE), os.path.getsize(EXE) if os.path.exists(EXE) else None)
blob = open(EXE, 'rb').read()
u16 = lambda o: struct.unpack_from('<H', blob, o)[0]
u32 = lambda o: struct.unpack_from('<I', blob, o)[0]
e = u32(0x3C); coff = e + 4
nsec = u16(coff + 2); szopt = u16(coff + 16); opt = coff + 20
image_base = u32(opt + 28); sec_tab = opt + szopt
secs = []
for i in range(nsec):
    o = sec_tab + i * 40
    secs.append(dict(name=blob[o:o+8].rstrip(b'\0').decode('latin1'),
                     va=u32(o+12), vsz=u32(o+8), rawsz=u32(o+16), rawptr=u32(o+20)))
for s in secs:
    print('SEC', s['name'], 'va %08X' % (image_base+s['va']), 'vsz', s['vsz'], 'rawptr', s['rawptr'], 'rawsz', s['rawsz'])
T = next(s for s in secs if s['name'] == '.text')
TEXT_RAW = T['rawptr']; TEXT_VA = image_base + T['va']; TEXT_VSZ = T['vsz']
print('TEXT_VA %08X TEXT_VSZ %d TEXT_RAW %d' % (TEXT_VA, TEXT_VSZ, TEXT_RAW))
def foff(va):
    return TEXT_RAW + (va - TEXT_VA)

p = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\D41_SUBST\_audit\EVIDENCE\a2_sites.json'
d = json.loads(open(p, 'rb').read().decode('utf-8'))
calls = d['calls']
# records that lie inside .text by VA (call site VA), call target outside .text == 0x7Cxxxxx etc
out = []
out.append('== positive control 0: pick records whose TARGET is outside .text ==')
recs = []
for k, v in calls.items():
    for site in v:
        recs.append((k, site))
print('total (target,site) pairs', len(recs))
def va(t): return int(t, 16)
outside = [(k, s) for k, s in recs if not (TEXT_VA <= va(k) < TEXT_VA + TEXT_VSZ)]
inside_site = [(k, s) for k, s in outside if TEXT_VA <= va(s) < TEXT_VA + TEXT_VSZ]
print('targets outside .text:', len(outside), ' of which site inside .text:', len(inside_site))
print('sample', inside_site[:10])
PICK = inside_site[0]
print('PICK', PICK)

def verify(target_hex, site_hex):
    tva = int(target_hex, 16); sva = int(site_hex, 16)
    so = foff(sva)
    row = dict(target=target_hex, site=site_hex, site_off=so, b0=blob[so])
    ok = True
    if blob[so] != 0xE8:
        ok = False
    rel = struct.unpack_from('<i', blob, so+1)[0]
    row['rel32'] = rel
    row['computed_target'] = '%08X' % ((sva + 5 + rel) & 0xFFFFFFFF)
    row['target_match'] = (row['computed_target'].upper() == target_hex.upper())
    row['ok'] = ok and row['target_match']
    return row

for t, s in [PICK] + inside_site[1:4]:
    print(verify(t, s))
