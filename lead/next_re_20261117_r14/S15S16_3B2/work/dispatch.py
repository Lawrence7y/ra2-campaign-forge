# -*- coding: utf-8 -*-
"""
Find live vtable dispatch sites for slot5(+0x14)/slot6(+0x18) of the 12 hit classes.
Strategy: scan .text for `call dword ptr [reg + 0x14|0x18]` (FF 5x 14/18 with mod=00 or
disp8 forms), then for each site disassemble a window backwards to see if the same
register was loaded from [this] (vptr) and whether the enclosing function also writes
one of the known vtables (constructor) or is a known call path. Also capture sites
where a known vtable base is loaded as immediate near the call.
"""
import json, os, struct, pefile
from capstone import *
from capstone.x86 import *

BASE = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(BASE, r"ra2youli\gamemd.exe")
WORK = os.path.join(BASE, r"lead\next_re_20261117_r14\S15S16_3B2\work")

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
sections = []
for s in pe.sections:
    nm = s.Name.rstrip(b"\x00").decode("latin1")
    va = IB + s.VirtualAddress
    sz = max(s.Misc_VirtualSize, s.SizeOfRawData)
    sections.append((nm, va, sz, s.get_data()[:sz]))
text = next(s for s in sections if s[0] == ".text")
TVA, TDAT = text[1], text[3]

wit = json.load(open(os.path.join(WORK, "witness.json"), encoding="utf-8"))
vtables = {}
for w in wit:
    for sl in w["slots"]:
        if sl["vtable_base"]:
            vtables[sl["vtable_base"]] = {
                "class": sl["rtti_name"], "entry": w["entry"],
                "slot_off": sl["slot_off"], "slot_va": sl["slot_va"],
            }

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True

# Find all call [reg+disp8] with disp == 0x14 or 0x18.
# Encoding: FF /2 with mod=01 (disp8): FF 54 24 14 = call [esp+0x14]; FF 50 14 = call [eax+0x14]
dispatch_sites = []
for off in range(0, len(TDAT) - 4):
    b0 = TDAT[off]
    if b0 != 0xFF:
        continue
    b1 = TDAT[off + 1]
    # call near [reg+disp8] is FF /2 with mod=01: ModRM = 01 010 rm = 0x50..0x57
    if (b1 >> 6) != 1 or ((b1 >> 3) & 7) != 2:
        continue
    disp = struct.unpack_from("<b", TDAT, off + 2)[0] & 0xFF
    if disp not in (0x14, 0x18):
        continue
    site_va = TVA + off
    # decode a window [-32, +16] around the site
    start = max(0, off - 48)
    code = TDAT[start:off + 24]
    insns = list(md.disasm(code, TVA + start))
    ctx = []
    for ins in insns:
        if ins.id == 0:
            continue
        opstr = f" {ins.op_str}" if ins.op_str else ""
        ctx.append(f"{ins.address:08X}: {ins.mnemonic}{opstr}")
    dispatch_sites.append({
        "site_va": site_va, "slot_off": disp,
        "modrm": f"{b1:02X}", "context": ctx,
    })

# Group by slot_off
out = []
out.append(f"Known vtables: {len(vtables)}")
for vb, info in sorted(vtables.items()):
    out.append(f"  {vb} class={info['class']} entry={info['entry']} slot_off={info['slot_off']} slot_va={info['slot_va']}")
out.append(f"\nDispatch sites with slot off 0x14/0x18: {len(dispatch_sites)}")

# For each hit entry, list dispatch sites with matching slot_off (0x14->slot5, 0x18->slot6)
# and include full context so a human can see vptr load.
for w in wit:
    out.append(f"\n{'='*76}\n{w['entry']} {w['subsystem']} {w['name']}")
    for sl in w["slots"]:
        if not sl["vtable_base"]:
            continue
        so = sl["slot_off"]
        out.append(f"  vtable={sl['vtable_base']} class={sl['rtti_name']} slot_off=0x{so:X}")
        matches = [d for d in dispatch_sites if d["slot_off"] == so]
        out.append(f"    matching dispatch sites (any class, slot_off=0x{so:X}): {len(matches)}")
        for d in matches[:8]:
            out.append(f"      @{d['site_va']:08X}:")
            for c in d["context"]:
                out.append(f"        {c}")

json.dump(dispatch_sites, open(os.path.join(WORK, "dispatch_sites.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
open(os.path.join(WORK, "dispatch.txt"), "w", encoding="utf-8").write("\n".join(out))
print("dispatch sites:", len(dispatch_sites))
