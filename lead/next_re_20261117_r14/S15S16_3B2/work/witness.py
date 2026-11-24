# -*- coding: utf-8 -*-
"""
Step 2 witness discovery for the 12 P1P2P3 hits.
For each hit entry, find:
  - dword slots in the whole image equal to entry (vtable slot candidates)
  - for each vtable slot, back-scan for RTTI COL (vtable[-4] points to COL) and parse TD name
  - direct callers (E8 rel32) to the entry
  - indirect dispatch sites: call [reg+off] where off matches slot offset, near a
    load of the vtable address; plus constructor writes of the vtable address
Emits work/witness.json and work/witness.txt.
"""
import json, os, struct, pefile, csv
from capstone import *
from capstone.x86 import *

BASE = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(BASE, r"ra2youli\gamemd.exe")
WORK = os.path.join(BASE, r"lead\next_re_20261117_r14\S15S16_3B2\work")

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
# Build flat image bytes mapped by VA
sections = []
for s in pe.sections:
    nm = s.Name.rstrip(b"\x00").decode("latin1")
    va = IB + s.VirtualAddress
    sz = max(s.Misc_VirtualSize, s.SizeOfRawData)
    data = s.get_data()[:sz]
    sections.append((nm, va, sz, s.PointerToRawData, data))

def va_read(va, n):
    for nm, v0, sz, raw, data in sections:
        if v0 <= va < v0 + sz:
            off = va - v0
            return data[off:off+n]
    return b""

def va_in(va):
    for nm, v0, sz, raw, data in sections:
        if v0 <= va < v0 + sz:
            return nm
    return None

def u32(va):
    b = va_read(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None

def find_dword_refs(target):
    """Find all VAs whose dword == target, across all sections with raw data."""
    refs = []
    needle = struct.pack("<I", target)
    for nm, v0, sz, raw, data in sections:
        if nm in (".text",):  # skip code for data-ref scan; handle code separately
            continue
        start = 0
        while True:
            i = data.find(needle, start)
            if i < 0:
                break
            refs.append((v0 + i, nm))
            start = i + 1
    return refs

# RTTI parsing helpers
def read_cstr(va, maxn=200):
    out = bytearray()
    for i in range(maxn):
        b = va_read(va + i, 1)
        if not b or b[0] == 0:
            break
        out += b
    return out.decode("latin1", "replace")

def parse_col(col_va):
    """MSVC x86 RTTICompleteObjectLocator:
       +0 signature, +4 offset, +8 cdOffset, +C pTypeDescriptor, +10 pClassHierarchyDescriptor.
       The class vtable base is at col_va+4 (COL sits at vtable[-4])."""
    if not va_in(col_va):
        return None
    sig = u32(col_va)
    td = u32(col_va + 0xC)
    chd = u32(col_va + 0x10)
    return {"col": col_va, "sig": sig, "td": td, "chd": chd}

def parse_td(td_va):
    """TypeDescriptor: +0 vftable, +4 sparse, +8 name (null-terminated '.*AV...@@')"""
    if not td_va or not va_in(td_va):
        return None
    name_va = td_va + 8
    name = read_cstr(name_va, 200)
    return {"td": td_va, "name_va": name_va, "name": name}

# capstone for .text scanning
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True
text_sec = next(s for s in sections if s[0] == ".text")
text_va, text_data = text_sec[1], text_sec[4]

def find_direct_calls(target):
    """E8 rel32 call to target anywhere in .text."""
    calls = []
    for off in range(0, len(text_data) - 5):
        if text_data[off] != 0xE8:
            continue
        rel = struct.unpack_from("<i", text_data, off + 1)[0]
        dest = (text_va + off + 5 + rel) & 0xFFFFFFFF
        if dest == target:
            calls.append(text_va + off)
    return calls

def find_vtable_refs_in_text(vtable_addr, slot_off):
    """Find code sites that reference the vtable address (mov reg, imm) or load [reg+slot_off]
    near such a reference; plus constructor writes mov [reg+disp], imm of vtable_addr."""
    sites = {"vtable_imm_loads": [], "constructor_writes": [], "slot_dispatch_near": []}
    needle = struct.pack("<I", vtable_addr)
    # find immediate loads of vtable_addr in .text (c7 c0 imm32 / b8 imm32 / 8b .. with imm)
    for off in range(0, len(text_data) - 5):
        # mov reg32, imm32 (B8+r) 
        if 0xB8 <= text_data[off] <= 0xBF:
            imm = struct.unpack_from("<I", text_data, off + 1)[0]
            if imm == vtable_addr:
                sites["vtable_imm_loads"].append(text_va + off)
        # mov r/m32, imm32 group (C7 /0 imm32)
        if text_data[off] == 0xC7:
            imm = struct.unpack_from("<I", text_data, off + 2)[0] if off + 6 <= len(text_data) else None
            if imm == vtable_addr:
                sites["constructor_writes"].append(text_va + off)
    return sites

res = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
hits = [r for r in res if r["p3_count"] > 0]

witness = []
out = []
def w(s=""):
    out.append(s)

for r in hits:
    ea = int(r["entry"], 16)
    refs = find_dword_refs(ea)
    slot_info = []
    for refva, sec in refs:
        # treat refva as a vtable slot: vtable[-4] (refva-4) may be COL pointer
        col = u32(refva - 4)
        col_info = parse_col(col) if col else None
        td_info = parse_td(col_info["td"]) if col_info else None
        # back-scan: for each candidate slot index k, vtable_base = refva-4*k,
        # COL pointer sits at vtable_base-4 (col[0]==0, col+0xC -> TD with '.?AV' name)
        col2 = None
        td2 = None
        vtable_base = None
        slot_off = None
        for k in range(0, 41):
            vb = refva - 4 * k
            c = u32(vb - 4)
            if not c:
                continue
            ci = parse_col(c)
            if not ci or ci["sig"] != 0:
                continue
            tdi = parse_td(ci["td"])
            if tdi and tdi["name"] and ".?AV" in tdi["name"]:
                col2, td2 = ci, tdi
                vtable_base = vb
                slot_off = 4 * k
                break
        chosen_col = col2 or col_info
        chosen_td = td2 or td_info
        disp = {}
        if vtable_base is not None:
            disp = find_vtable_refs_in_text(vtable_base, slot_off)
        slot_info.append({
            "slot_va": refva, "section": sec,
            "vtable_base": "%08X" % vtable_base if vtable_base is not None else None,
            "slot_off": slot_off,
            "col": "%08X" % chosen_col["col"] if chosen_col else None,
            "td": "%08X" % chosen_td["td"] if chosen_td else None,
            "rtti_name": chosen_td["name"] if chosen_td else None,
            "name_va": "%08X" % chosen_td["name_va"] if chosen_td else None,
            "text_vtable_loads": ["%08X" % x for x in disp.get("vtable_imm_loads", [])],
            "text_ctor_writes": ["%08X" % x for x in disp.get("constructor_writes", [])],
        })
    direct = find_direct_calls(ea)
    w(f"\n{'='*76}\n{r['entry']} {r['subsystem']} {r['name']}\n  direct_callers={['%08X'%x for x in direct]}")
    for si in slot_info:
        w(f"  slot@{si['slot_va']:08X} [{si['section']}] vbase={si['vtable_base']} off={si['slot_off']} "
          f"rtti={si['rtti_name']!r} td={si['td']} name_va={si['name_va']}")
        if si["text_vtable_loads"]:
            w(f"    vtable imm loads in .text: {si['text_vtable_loads'][:12]}")
        if si["text_ctor_writes"]:
            w(f"    ctor writes of vtable in .text: {si['text_ctor_writes'][:12]}")
    witness.append({
        "entry": r["entry"], "subsystem": r["subsystem"], "name": r["name"],
        "direct_callers": ["%08X" % x for x in direct],
        "slots": slot_info,
    })

json.dump(witness, open(os.path.join(WORK, "witness.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
open(os.path.join(WORK, "witness.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote witness.json / witness.txt; hits:", len(hits))
