#!/usr/bin/env python3
"""② channel: RTTI chain verification from raw bytes, fail-closed.
Algorithm (per R14_COMMON §8.2 tech7 + §8.6 clause2):
  scan whole image for 4-byte slot dword == entry -> candidate slot addresses.
  For each slot address, scan back k=0..31 for a vtable base vt=slot_addr-4*k such that
    COL = [vt-4], TD = [COL+0xC], name = inline string at TD+8 matching .?AV...@ .
  Accept only with valid name; then vt[k]==entry holds by construction.
Liveness (ctor vs atexit dtor) checked in check_liveness.py separately."""
import json, struct
from common import DATA, IB, va2off, _pe

ENTRIES = [0x0065CAC0, 0x004324B0, 0x00552490, 0x006C9890,
           0x00631CC0, 0x0065D150, 0x00431E80]

sections = []
for s in _pe.sections:
    name = s.Name.rstrip(b'\x00').decode('latin-1')
    va0 = IB + s.VirtualAddress
    sections.append((name, va0, va0 + s.Misc_VirtualSize,
                     s.PointerToRawData, s.SizeOfRawData))

def ru32(va):
    try:
        o = va2off(va)
        return struct.unpack_from('<I', DATA, o)[0]
    except Exception:
        return None

def name_at_td(td):
    try: o = va2off(td + 8)
    except Exception: return None
    end = DATA.find(b'\x00', o, o+120)
    if end < 0: return None
    raw = DATA[o:end]
    if not (5 <= len(raw) <= 96): return None
    s = raw.decode('latin-1')
    if s.startswith('.?AV') and s.endswith('@@'):
        return s
    return None

def chain_from_slot(slot_va):
    """Return (vt, slot_index, COL, TD, name) or None."""
    for k in range(0, 40):
        vt = slot_va - 4*k
        col = ru32(vt - 4)
        if col is None: continue
        td = ru32(col + 0xC)
        if td is None: continue
        name = name_at_td(td)
        if name is not None:
            # verify vt[k] == the dword at slot_va (== entry by scan construction)
            return {'vt': vt, 'slot': k, 'COL': col, 'TD': td, 'name': name}
    return None

def scan(entry):
    pat = struct.pack('<I', entry)
    hits = []
    for name, va0, va1, praw, sraw in sections:
        pos = praw
        end = praw + sraw
        idx = DATA.find(pat, pos, end)
        while idx >= 0:
            if idx % 4 == 0:
                hits.append((va0 + (idx - praw), name))
            idx = DATA.find(pat, idx+1, end)
    chains = []
    for slot_va, sec in hits:
        c = chain_from_slot(slot_va)
        if c:
            c['slot_addr'] = slot_va; c['section'] = sec
            chains.append(c)
    return hits, chains

out = {}
for e in ENTRIES:
    hits, chains = scan(e)
    out[f"{e:08X}"] = {'raw_slot_hits': len(hits), 'slot_addrs': [hex(h[0]) for h in hits],
                       'chains': chains}
    print(f"\n{e:08X}: raw hits={len(hits)}, valid chains={len(chains)}")
    for c in chains:
        print(f"   vt={c['vt']:08X} slot={c['slot']} COL={c['COL']:08X} TD={c['TD']:08X} "
              f"name={c['name']} slot_addr={c['slot_addr']:08X}")

base = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C4"
with open(base + r"\EVIDENCE\rtti_chains.json", 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2)
print("\nwrote rtti_chains.json")
