#!/usr/bin/env python3
"""Dump full RTTI inheritance chain via COL+0x10 -> CHD -> BaseClassArray for holding tables.
Also emit function extents (atlas size + CFG extent from classification)."""
import sys, os, json, struct, csv
sys.path.insert(0, os.path.dirname(__file__))
import common as C

CLS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
HOLD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C7\EVIDENCE\rtti_all_holders.json"

ENTRIES = [0x004325C0, 0x00473C00, 0x00473CE0, 0x00473FC0, 0x0047AAB0,
           0x00631D30, 0x0065CCA0, 0x0065D1F0, 0x00432050]

def td_name(td):
    try:
        o = C.va2off(td + 8)
    except Exception:
        return None
    end = C.DATA.find(b'\x00', o, o+128)
    if end < 0: return None
    s = C.DATA[o:end].decode('latin-1')
    return s if (s.startswith('.?A') and s.endswith('@@')) else None

def base_chain(COL):
    """COL+0x10 -> CHD (ClassHierarchyDescriptor). CHD+4=numBases, CHD+8=pBaseClassArray.
       BaseClassArray[i] -> BCD; BCD+0 = pTD of base. Return list of base TD names (excluding self)."""
    chd = C.ru32(COL + 0x10)
    if not chd: return []
    nb = C.ru32(chd + 8)          # numBaseClasses at CHD+8
    if nb is None or nb > 32: return []
    bca = C.ru32(chd + 0xC)       # pBaseClassArray at CHD+0xC
    if not bca: return []
    names = []
    for i in range(nb):
        bcd = C.ru32(bca + 4*i)
        if not bcd: continue
        td = C.ru32(bcd)
        nm = td_name(td) if td else None
        if nm: names.append(nm)
    return names

# extents
ext = {}
for r in csv.DictReader(open(CLS, encoding='utf-8'), delimiter='\t'):
    try: ext[r['entry']] = (int(r['ext_lo'],16), int(r['ext_hi'],16))
    except Exception: pass
atlas = {}
for line in open(ATLAS, encoding='utf-8', errors='replace'):
    p = line.rstrip('\n').split('\t')
    try: atlas[int(p[0],16)] = int(p[1])
    except Exception: pass

hold = json.load(open(HOLD, encoding='utf-8'))
out = {'entries': {}}
for e in ENTRIES:
    key = f"{e:08X}"
    chains = []
    for h in hold['entries'][key]['holders']:
        col = int(h['COL'],16)
        bc = base_chain(col)
        chains.append({'vt': h['vt'], 'slot': h['slot'], 'name': h['name'],
                       'COL': h['COL'], 'TD': h['TD'], 'bases': bc})
    lo, hi = ext.get(key, (None,None))
    out['entries'][key] = {
        'chains': chains,
        'ext_lo': f"0x{lo:08X}" if lo else None,
        'ext_hi': f"0x{hi:08X}" if hi else None,
        'ext_size': (hi-lo) if lo and hi else None,
        'atlas_size': atlas.get(e),
    }
    print(f"\n{key}: ext=[{out['entries'][key]['ext_lo']},{out['entries'][key]['ext_hi']}) size={hi-lo if lo and hi else '?'} atlas={atlas.get(e)}")
    for c in chains:
        print(f"   vt={c['vt']} slot={c['slot']} {c['name']}")
        print(f"      bases: {' <- '.join(c['bases']) if c['bases'] else '(none)'}")

base = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C7"
json.dump(out, open(base + r"\EVIDENCE\rtti_inherit_extents.json", 'w', encoding='utf-8'), indent=2)
print("\nwrote EVIDENCE/rtti_inherit_extents.json")
