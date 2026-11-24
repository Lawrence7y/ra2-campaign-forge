#!/usr/bin/env python3
"""Independent RTTI holder enumeration for the 5 candidate rows.
② per §8.6 clause2/§8.2 tech7: [vt-4]=COL -> [COL+0xC]=TD -> TD+8 ".?AV/.?AU...@@".
M1: enumerate ALL holding tables; 2+ tables same slot => base-class level (错源⑯).
Fail-closed: no valid RTTI chain => not counted."""
import os, struct, json
import common as C

ROWS = ["00473C00","00473CE0","00473FC0","0047AAB0","00631D30"]
base = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C8"

def name_at_td(td):
    if td is None:
        return None
    try:
        o = C.va2off(td + 8)
    except ValueError:
        return None
    end = C.DATA.find(b'\x00', o, o+160)
    if end < 0:
        return None
    raw = C.DATA[o:end]
    if not (5 <= len(raw) <= 96):
        return None
    s = raw.decode('latin-1')
    if (s.startswith('.?AV') or s.startswith('.?AU')) and s.endswith('@@'):
        return s
    return None

def col_info(col_va):
    td = C.ru32(col_va + 0xC)
    if td is None:
        return None
    name = name_at_td(td)
    if name is None:
        return None
    return td, name

# enumerate all RTTI vtables in .rdata
rb = C.DATA[C.RDATA_RO:C.RDATA_RO+C.RDATA_RS]
vts = {}
for off in range(0, len(rb)-4, 4):
    cand_col = struct.unpack_from('<I', rb, off)[0]
    ci = col_info(cand_col)
    if ci is None:
        continue
    vt_va = C.RDATA_VA + off + 4
    if vt_va in vts:
        continue
    td, name = ci
    slots = []
    s = 0
    while s < 512:
        v = C.ru32(vt_va + 4*s)
        if v is None or not C.in_text(v):
            break
        slots.append(v)
        s += 1
    vts[vt_va] = {'COL': cand_col, 'TD': td, 'name': name, 'nslots': len(slots), 'slots': slots}

print("enumerated %d valid RTTI vtables" % len(vts))
out = {'sha': C.SHA, 'n_vtables': len(vts), 'entries': {}}
for e in ROWS:
    target = int(e, 16)
    holders = []
    for vt_va, info in vts.items():
        for idx, val in enumerate(info['slots']):
            if val == target:
                holders.append({'vt': '0x%08X'%vt_va, 'slot': idx,
                                'slot_off': '+0x%X'%(idx*4), 'name': info['name'],
                                'nslots': info['nslots'], 'COL': '0x%08X'%info['COL'],
                                'TD': '0x%08X'%info['TD']})
    classes = sorted({h['name'] for h in holders})
    slots = sorted({h['slot'] for h in holders})
    out['entries'][e] = {'holders': holders, 'distinct_classes': classes,
                         'distinct_slots': slots, 'n_holders': len(holders)}
    print("\n%s: %d holders, classes=%s, slots=%s" % (e, len(holders), classes, slots))
    for h in holders:
        print("   vt=%s slot=%d(%s) %s" % (h['vt'], h['slot'], h['slot_off'], h['name']))

json.dump(out, open(os.path.join(base,'EVIDENCE','rtti_holders.json'),'w',encoding='utf-8'), indent=2)
print("\nwrote EVIDENCE/rtti_holders.json")
