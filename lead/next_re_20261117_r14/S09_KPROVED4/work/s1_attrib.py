"""Step 1: enumerate all RTTI vtables; compute ② holding tables for all 83 S09 A-remaining
candidates. Output EVIDENCE/VTABLES_ALL.tsv and work/attrib_raw.json.
"""
import json
from pathlib import Path
from s09lib import rtti_tables, tables_holding, u32, cstr, is_ro

OUT = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED4")
WORK = OUT/'work'
EV = OUT/'EVIDENCE'

rem = json.load(open(WORK/'s09_A_remaining.json'))
tables = rtti_tables()
print('RTTI tables =', len(tables), ' total slots =', sum(len(t['slots']) for t in tables))

# full table dump
with (EV/'VTABLES_ALL.tsv').open('w', encoding='utf-8') as f:
    f.write('vt\tcol\ttd\tname\tnslots\n')
    for t in tables:
        f.write('%08X\t%08X\t%08X\t%s\t%d\n' % (t['vt'], t['col'], t['td'], t['name'], len(t['slots'])))

# entry -> 4-byte VA occurrence count in whole file (independent channel, like audit)
DATA = (Path(r'D:\Project\ra2-campaign-forge')/'ra2youli'/'gamemd.exe').read_bytes()
def va_occurrences(entry):
    pat = entry.to_bytes(4, 'little')
    c = 0; i = 0
    while True:
        j = DATA.find(pat, i)
        if j < 0: break
        c += 1; i = j + 1
    return c

out = {}
for r in rem:
    e = int(r['entry'], 16)
    hits = tables_holding(tables, e)
    ht = []
    for t, slot in hits:
        ht.append(dict(vt='%08X'%t['vt'], slot=slot, col='%08X'%t['col'],
                       td='%08X'%t['td'], name=t['name']))
    out[r['entry']] = dict(hits=ht, n_hits=len(ht), va_occ=va_occurrences(e),
                           survey_slot=r['slot'], survey_vt=r['vt'], survey_cls=r['rtti'])

json.dump(out, open(WORK/'attrib_raw.json','w'), ensure_ascii=False, indent=1)

# summary
for r in rem:
    a = out[r['entry']]
    names = sorted(set(h['name'] for h in a['hits']))
    slots = sorted(set(h['slot'] for h in a['hits']))
    print('%s nhits=%d occ=%d slots=%s names=%s' % (
        r['entry'], a['n_hits'], a['va_occ'], slots,
        ','.join(n.replace('.?AV','').replace('@@','') for n in names)))
