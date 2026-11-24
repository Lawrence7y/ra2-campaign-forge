#!/usr/bin/env python3
"""④ witness: whole-.text direct call site scan, independent of function_atlas entry+size.
For every E8 instruction at a decode boundary in [TEXT_VA,TEXT_END): target=site+5+rel32.
Collect sites whose target equals one of the 7 entries. For containment:
  - function body = [entry, entry+size) using atlas size, independently confirmed by
    dis_full.txt showing the last insn is a ret exactly at entry+size.
  - reject self-loops (site inside its own target's body).
Also report scan scale (instructions decoded, E8 at boundary, raw 0xE8 bytes)."""
import json, struct
from common import DATA, IB, TEXT_VA, TEXT_END, disasm_range, va2off

ENTRIES = [0x0065CAC0, 0x004324B0, 0x00552490, 0x006C9890,
           0x00631CC0, 0x0065D150, 0x00431E80]
SIZE = {0x0065CAC0:111, 0x004324B0:234, 0x00552490:346, 0x006C9890:67,
        0x00631CC0:75, 0x0065D150:56, 0x00431E80:131}
NAME = {0x0065CAC0:'RawFileClass::slot2', 0x004324B0:'CDFileClass::vslot10',
        0x00552490:'LCWStraw::slot2', 0x006C9890:'FileStraw::slot1',
        0x00631CC0:'FilePipe::slot3', 0x0065D150:'CDFileClass::slot3',
        0x00431E80:'BufferIOFileClass::vslot2'}

# scan whole .text instruction by instruction with skipdata=True
n_insn = 0
n_skip = 0
e8_boundary = 0
sites = {e: [] for e in ENTRIES}
targets_all = {}

off = va2off(TEXT_VA)
nbytes = TEXT_END - TEXT_VA
from common import _MD
for ins in _MD.disasm(DATA[off:off+nbytes], TEXT_VA):
    n_insn += 1
    if ins.mnemonic == 'db' or ins.id == 0:
        n_skip += 1
    if ins.mnemonic in ('call',) and ins.size == 5 and ins.bytes[0] == 0xE8:
        e8_boundary += 1
        rel = struct.unpack('<i', ins.bytes[1:5])[0]
        site = ins.address
        target = site + 5 + rel
        targets_all.setdefault(target, []).append(site)
        if target in sites:
            sites[target].append({'site': site, 'bytes': ins.bytes.hex(),
                                  'rel32': rel, 'caller_insn': f"{ins.mnemonic} {ins.op_str}"})

# raw E8 count
raw_e8 = sum(1 for b in DATA[off:off+nbytes] if b == 0xE8)

# classify sites: containment & self-loop
result = {}
for e in ENTRIES:
    lo, hi = e, e + SIZE[e]
    valid = []
    for s in sites[e]:
        inside = lo <= s['site'] < hi
        valid.append({**s, 'inside_self_body': inside})
    nonloop = [s for s in valid if not s['inside_self_body']]
    result[f"{e:08X}"] = {
        'name': NAME[e], 'body': [hex(lo), hex(hi)],
        'n_sites_raw': len(valid), 'n_sites_nonloop': len(nonloop),
        'sites': valid,
    }
    print(f"{e:08X} {NAME[e]:28s} body=[{lo:#x},{hi:#x}) sites={len(valid)} nonloop={len(nonloop)}")
    for s in valid:
        print(f"    site={s['site']:08X} bytes={s['bytes']} rel32={s['rel32']} self={s['inside_self_body']}")

scan = {'text_va': hex(TEXT_VA), 'text_end': hex(TEXT_END),
        'instructions_decoded': n_insn, 'skipdata_pseudo': n_skip,
        'e8_at_boundary': e8_boundary, 'raw_e8_bytes': raw_e8}
print("\nscan scale:", scan)

base = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C4"
with open(base + r"\EVIDENCE\direct_sites.json", 'w', encoding='utf-8') as f:
    json.dump({'scan_scale': scan, 'rows': result}, f, indent=2)
with open(base + r"\EVIDENCE\scan_scale.json", 'w', encoding='utf-8') as f:
    json.dump(scan, f, indent=2)
print("wrote direct_sites.json / scan_scale.json")
