#!/usr/bin/env python3
"""Enumerate ALL RTTI vtables in .rdata, then find every (vtable,slot) holding each target entry.
② per R14_COMMON §8.6 clause2 / §8.2 tech7: [vt-4]=COL -> [COL+0xC]=TD -> TD+8 inline ".?AV..@@".
M1: enumerate ALL holding tables; M1/错源⑯: 2+ tables same slot => base-class level attribution.
Fail-closed: a slot hit with no valid RTTI chain is reported but NOT counted as ②."""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(__file__))
import common as C

ENTRIES = [0x004325C0, 0x00473C00, 0x00473CE0, 0x00473FC0, 0x0047AAB0,
           0x00631D30, 0x0065CCA0, 0x0065D1F0, 0x00432050]

def mappable(va):
    try:
        C.va2off(va)
        return True
    except Exception:
        return False

def name_at_td(td):
    # TypeDescriptors live in .data (e.g. 0x815E38) on this image; require only mappable.
    if not mappable(td):
        return None
    try:
        o = C.va2off(td + 8)
    except Exception:
        return None
    end = C.DATA.find(b'\x00', o, o + 128)
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
    """Return TD+name if col_va is a valid COL (mappable, TD with valid name), else None."""
    if not mappable(col_va):
        return None
    td = C.ru32(col_va + 0xC)
    if td is None or not mappable(td):
        return None
    name = name_at_td(td)
    if name is None:
        return None
    return (td, name)

# Enumerate all vtables: scan .rdata 4-byte aligned slots for a value pointing to a valid COL.
vts = {}   # vt_va -> {'COL','TD','name','slots':[list of slot values until non-text]}
rdata_bytes = C.DATA[C.RDATA_RP:C.RDATA_RE]
for off in range(0, len(rdata_bytes) - 4, 4):
    cand_col = struct.unpack_from('<I', rdata_bytes, off)[0]
    ci = col_info(cand_col)
    if ci is None:
        continue
    vt_va = C.RDATA_VA + off + 4   # COL sits at vt-4
    if vt_va in vts:
        continue
    td, name = ci
    # read slots from vt[0] while values point into .text
    slots = []
    s = 0
    while s < 512:
        v = C.ru32(vt_va + 4*s)
        if v is None:
            break
        if not C.in_text(v):
            break
        slots.append(v)
        s += 1
    vts[vt_va] = {'COL': cand_col, 'TD': td, 'name': name, 'nslots': len(slots), 'slots': slots}

print(f"enumerated {len(vts)} valid RTTI vtables in .rdata")

# For each entry, find all (vt, slot) pairs
out = {'sha': C.SHA, 'n_vtables': len(vts), 'entries': {}}
for e in ENTRIES:
    holders = []
    for vt_va, info in vts.items():
        for idx, val in enumerate(info['slots']):
            if val == e:
                holders.append({'vt': f"0x{vt_va:08X}", 'slot': idx,
                                'slot_off': f"+0x{idx*4:X}",
                                'name': info['name'], 'nslots': info['nslots'],
                                'COL': f"0x{info['COL']:08X}", 'TD': f"0x{info['TD']:08X}"})
    # distinct classes / slots
    classes = sorted({h['name'] for h in holders})
    slots = sorted({h['slot'] for h in holders})
    out['entries'][f"{e:08X}"] = {'holders': holders, 'distinct_classes': classes,
                                  'distinct_slots': slots, 'n_holders': len(holders)}
    print(f"\n{e:08X}: {len(holders)} holding tables, classes={classes}, slots={slots}")
    for h in holders:
        print(f"   vt={h['vt']} slot={h['slot']} ({h['slot_off']}) {h['name']}")

base = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C7"
json.dump(out, open(base + r"\EVIDENCE\rtti_all_holders.json", 'w', encoding='utf-8'), indent=2)
print("\nwrote EVIDENCE/rtti_all_holders.json")
