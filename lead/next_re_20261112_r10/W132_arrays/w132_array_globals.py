#!/usr/bin/env python3
"""W132: identify gamemd.exe's per-type object-array globals, offline.

The question this settles
------------------------
The atlas ledger (GOAL_THREE_TARGETS §853-3) calls `DAT_00a8eb44` a "candidate
unit / object master table" and uses it to explain §707 ("cell chains do not
register units: 213 nodes vs 1500 designed").  Other project documents, from
RTTI, call `0xA8EB44 / 0xA8EB50` the **BuildingClass instance vector**
(`DynamicVectorClass<BuildingClass*>`).  Both cannot be right.

This script decides it from the image alone:
  1. every absolute (disp32 / imm32) reference to each candidate global inside
     .text, classified READ / WRITE / ADDR (lea = address taken), mapped to its
     containing function via function_atlas.tsv;
  2. the RTTI TypeDescriptor names of every `DynamicVectorClass<...>` in .rdata
     and what a given COL actually points at;
  3. the CRT static initialiser that zeroes the family, with the complete list
     of globals it touches.

Read-only over the file. No process, no writes.
"""
import bisect
import json
import os
import struct
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.dirname(HERE)
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ATLAS = os.path.join(R10, "W130_atlas", "function_atlas.tsv")

TEXT_LO, TEXT_HI = 0x00401000, 0x007E038D

# candidate globals: (label, va, note)
CANDIDATES = [
    ("bld_Items", 0x00A8EB44, "docs: BuildingClass::Array Items"),
    ("bld_Count", 0x00A8EB50, "docs: BuildingClass::Array Count"),
    ("unit_Items", 0x008B410C, "harness: units Items"),
    ("unit_Count", 0x008B4118, "harness: units Count"),
    ("inf_Items", 0x00A83DEC, "harness: infantry Items"),
    ("inf_Count", 0x00A83DF8, "harness: infantry Count"),
    ("air_Items", 0x00A8022C, "harness: aircraft Items"),
    ("air_Count", 0x00A80238, "harness: aircraft Count"),
    ("x_eaf8", 0x00A8EAF8, "§853-3 listed (capacity/count?)"),
    ("x_8b3dd0", 0x008B3DD0, "§853-3 listed"),
    ("x_ec7c", 0x00A8EC7C, "§853-3 'Techno' neighbourhood"),
    ("x_ec88", 0x00A8EC88, "harness: Techno count"),
    ("x_80218", 0x00A80218, "§853-3 listed"),
    ("x_a8b230", 0x00A8B230, "§853-3 listed (state)"),
    ("x_8871e0", 0x008871E0, "§853-3 listed (state)"),
]

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
SECS = []
for s in pe.sections:
    SECS.append({
        "name": s.Name.rstrip(b"\x00").decode("latin-1"),
        "va": IB + s.VirtualAddress,
        "vend": IB + s.VirtualAddress + s.Misc_VirtualSize,
        "raw_end": IB + s.VirtualAddress + s.SizeOfRawData,
    })


def blk(va):
    for s in SECS:
        if s["va"] <= va < s["vend"]:
            return s
    return None


def sec_of(va):
    s = blk(va)
    return s["name"] if s else None


def has_bytes(va, n=4):
    s = blk(va)
    return bool(s) and (va + n) <= s["raw_end"]


def u32(va):
    if not has_bytes(va):
        return None
    return struct.unpack("<I", img[va - IB: va - IB + 4])[0]


def cstr(va, cap=200):
    if not has_bytes(va, 1):
        return None
    i = va - IB
    out = bytearray()
    while i < len(img) and len(out) < cap:
        c = img[i]
        if c == 0:
            break
        if not (32 <= c < 127):
            return None
        out.append(c)
        i += 1
    return out.decode("latin-1")


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

# ---------------------------------------------------------------- function map
FN = []          # (entry, size)
if os.path.exists(ATLAS):
    with open(ATLAS, "r", encoding="utf-8") as f:
        next(f)
        for ln in f:
            p = ln.split("\t", 2)
            if len(p) < 2:
                continue
            try:
                FN.append((int(p[0], 16), int(p[1])))
            except ValueError:
                continue
    FN.sort()
FN_STARTS = [e for e, _ in FN]


def fn_of(va):
    i = bisect.bisect_right(FN_STARTS, va) - 1
    if i < 0:
        return None
    e, sz = FN[i]
    if sz and e <= va < e + sz:
        return e, sz
    return None


# ------------------------------------------------------------------ xref scan
text_off = TEXT_LO - IB
text = bytes(img[text_off: TEXT_HI - IB])


def hits_of(va):
    pat = struct.pack("<I", va)
    out, i = [], text.find(pat)
    while i >= 0:
        out.append(TEXT_LO + i)
        i = text.find(pat, i + 1)
    return out


def classify(va):
    """disassemble small windows around each raw byte hit; keep real operands."""
    res = []
    for h in hits_of(va):
        lo = max(TEXT_LO, h - 16)
        win = bytes(img[lo - IB: min(TEXT_HI, h + 17) - IB])
        done = False
        for insn in md.disasm(win, lo):
            if insn.address + insn.size <= h:
                continue
            if insn.address > h:
                break
            if not insn.operands:
                continue
            for oi, op in enumerate(insn.operands):
                if op.type != X86_OP_MEM:
                    continue
                if op.mem.base != 0 or op.mem.index != 0:
                    continue
                ea = op.mem.disp & 0xFFFFFFFF
                if ea != va:
                    continue
                m = insn.mnemonic
                if m == "lea":
                    kind = "ADDR"
                elif oi == 0 and m not in ("cmp", "test", "push"):
                    kind = "WRITE" if ("mov" == m or m in (
                        "add", "or", "and", "sub", "xor", "inc", "dec",
                        "shl", "shr", "sar", "not", "neg", "xchg")) else "WRITE?"
                else:
                    kind = "READ"
                res.append((insn.address, kind, "%s %s" % (m, insn.op_str)))
                done = True
                break
            if done:
                break
    return res


print("=" * 100)
print("W132-1  absolute references to the candidate globals (.text)")
print("=" * 100)
summary = {}
for label, va, note in CANDIDATES:
    rows = classify(va)
    summary[label] = rows
    print("\n-- %-10s 0x%08X  (%-38s) refs=%d" % (label, va, note, len(rows)))
    if not rows:
        print("     (no absolute reference)")
        continue
    for at, kind, txt in sorted(rows):
        f = fn_of(at)
        where = ("fn 0x%08X+%-5d" % (f[0], at - f[0])) if f else "no-function"
        print("     %-6s 0x%08X  %-22s %-28s %s"
              % (kind, at, where, txt[:28], sec_of(at) or ""))

print()
print("=" * 100)
print("W132-2  RTTI TypeDescriptor names of VectorClass / DynamicVectorClass")
print("=" * 100)
# TypeDescriptor { void* pVFTable; void* spare; char name[]; }
tds = []
i = IB
needles = (b".?AV", b".?AU")
rdata = [s for s in SECS if s["name"] == ".rdata"]
if rdata:
    s0 = rdata[0]
    lo, hi = s0["va"], min(s0["vend"], s0["raw_end"])
    j = lo - IB
    while j < hi - IB - 4:
        if img[j] == 0x2E and img[j + 1] in (0x3F,):   # "."
            nm = cstr(lo + ((j + 1) - (lo - IB)) - 1, 220)
            if nm and (nm.startswith(".?AV") or nm.startswith(".?AU")):
                strva = lo + (j - (lo - IB))
                td = strva - 8
                pv = u32(td)
                if pv is not None and sec_of(pv) == ".rdata":
                    tds.append((td, nm))
            j += 1
        else:
            j += 1

vecs = [(td, nm) for td, nm in tds if "VectorClass" in nm]
print("total TypeDescriptors scanned: %d ; Vector/DynamicVector ones: %d"
      % (len(tds), len(vecs)))
for td, nm in sorted(vecs, key=lambda t: t[1]):
    print("   TD 0x%08X  %s" % (td, nm))


def col_info(col, tag=""):
    off = u32(col + 0x04)
    ptd = u32(col + 0x0C)
    nm = cstr(ptd + 8) if ptd else None
    print("   %-10s COL 0x%08X  offset=%-3s pTD=0x%08X  name=%s"
          % (tag, col, off, ptd or 0, nm))
    return nm


print()
print("=" * 100)
print("W132-3  what the documented COL actually says")
print("=" * 100)
for col in (0x007E9E20,):
    col_info(col, "doc:")
# which COLs point at a VectorClass TD?
by_td = {}
for col_va in range(rdata[0]["va"] if rdata else 0, 0):
    pass
print("\n   (reverse: COLs in .rdata whose pTD names a VectorClass)")
vec_tds = {td for td, _ in vecs}
found = 0
if rdata:
    lo, hi = rdata[0]["va"], min(rdata[0]["vend"], rdata[0]["raw_end"])
    for col in range(lo, hi - 0x14, 4):
        ptd = u32(col + 0x0C)
        if ptd in vec_tds:
            found += 1
            if found <= 40:
                print("   COL 0x%08X offset=%-3s -> %s"
                      % (col, u32(col + 4), cstr(ptd + 8)))
print("   total COLs typing a VectorClass: %d" % found)

print()
print("=" * 100)
print("W132-4  a function's module-global references (--fn)")
print("=" * 100)


def dump_fn(entry, length=None):
    f = fn_of(entry)
    size = length or (f[1] if f else 0x100)
    win = bytes(img[entry - IB: entry - IB + size])
    refs = {}
    for insn in md.disasm(win, entry):
        for op in insn.operands:
            if op.type != X86_OP_MEM or op.mem.base or op.mem.index:
                continue
            ea = op.mem.disp & 0xFFFFFFFF
            if sec_of(ea) in (".data", ".bss") or 0x00A00000 <= ea < 0x00C00000:
                refs.setdefault(ea, []).append(insn.address)
    print("fn 0x%08X size=%d  distinct data globals touched: %d"
          % (entry, size, len(refs)))
    for ea in sorted(refs):
        print("   global 0x%08X  %-3d refs  first 0x%08X"
              % (ea, len(refs[ea]), min(refs[ea])))
    return refs


if "--fn" in sys.argv:
    for a in sys.argv[sys.argv.index("--fn") + 1:]:
        dump_fn(int(a, 0))

if "--json" in sys.argv:
    out = os.path.join(HERE, "w132_refs.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({k: [[a, kd, t] for a, kd, t in v] for k, v in summary.items()},
                  f, ensure_ascii=False, indent=1)
    print("\nwrote %s" % out)
