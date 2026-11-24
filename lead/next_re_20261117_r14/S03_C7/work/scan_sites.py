#!/usr/bin/env python3
"""④ site scanner: whole-.text E8 @ instruction boundary, site+5+rel32==entry,
site outside function body, non-self-loop. Independent of atlas.
Also emits the call_targets counter used by the random baseline."""
import sys, os, json, struct
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(__file__))
import common as C

ENTRIES = [0x004325C0, 0x00473C00, 0x00473CE0, 0x00473FC0, 0x0047AAB0,
           0x00631D30, 0x0065CCA0, 0x0065D1F0, 0x00432050]
ENTR = set(ENTRIES)

# extent map (lo,hi) from classification - used only to check "site outside body"
EXT = {}
J = json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C7\EVIDENCE\rtti_inherit_extents.json", encoding='utf-8'))
for k, v in J['entries'].items():
    EXT[int(k,16)] = (int(v['ext_lo'],16), int(v['ext_hi'],16))

# scan whole .text for E8 at instruction boundaries using capstone skipdata=True
off = C.va2off(C.TEXT_VA)
buf = C.DATA[off:off+(C.TEXT_END-C.TEXT_VA)]
call_sites = defaultdict(list)   # target -> [(site址, raw bytes, caller_context)]
call_targets = Counter()
n_insn = 0
for ins in C.md().disasm(buf, C.TEXT_VA):
    n_insn += 1
    if ins.mnemonic == 'call' and ins.size == 5 and ins.bytes[0] == 0xE8:
        rel = struct.unpack('<i', ins.bytes[1:5])[0]
        tgt = ins.address + 5 + rel
        call_targets[tgt] += 1
        if tgt in ENTR:
            call_sites[tgt].append({'site': f"0x{ins.address:08X}",
                                    'bytes': ins.bytes.hex(),
                                    'insn': C.insn_str(ins)})

print(f"scanned {n_insn} insns over whole .text [{C.TEXT_VA:#x},{C.TEXT_END:#x})")
out = {'sha': C.SHA, 'n_insn': n_insn, 'text': [f"0x{C.TEXT_VA:08X}", f"0x{C.TEXT_END:08X}"],
       'entries': {}}
for e in ENTRIES:
    sites = call_sites.get(e, [])
    lo, hi = EXT[e]
    valid = []
    for s in sites:
        sa = int(s['site'],16)
        outside = not (lo <= sa < hi)
        nonself = (sa != e)
        s['outside_body'] = outside
        s['nonself'] = nonself
        s['valid'] = outside and nonself
        if s['valid']: valid.append(s)
    out['entries'][f"{e:08X}"] = {'extent': [f"0x{lo:08X}",f"0x{hi:08X}"],
                                  'all_e8_sites': sites, 'n_valid': len(valid),
                                  'valid_sites': valid}
    print(f"{e:08X}: n_direct(site+5+rel32)={len(sites)}, valid(outside&nonself)={len(valid)}")
    for s in valid:
        print(f"   {s['site']} {s['bytes']}  {s['insn']}")

base = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C7"
json.dump(out, open(base + r"\EVIDENCE\direct_sites.json", 'w', encoding='utf-8'), indent=2)
# call_targets dump for baseline reuse
json.dump({f"{k:08X}":v for k,v in call_targets.items()},
          open(base + r"\work\call_targets.json", 'w', encoding='utf-8'))
print("wrote EVIDENCE/direct_sites.json + work/call_targets.json")
