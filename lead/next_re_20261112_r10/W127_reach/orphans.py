#!/usr/bin/env python3
"""W127c: resolve the three open reachability questions about the 20 call sites.

  (a) sites #7-#9 live in FUN_006d0680 whose only caller is FUN_006922e0[fnptr]
      -> is 0x006922E0 a vtable slot? which class?
  (b) sites #15-#16 live in FUN_006d14f0 with zero code callers -> dead code?
  (c) site #17 at 0x006D15FA is inside no Ghidra function -> orphan fragment?

Method: raw byte/immediate scan + RTTI map (project artifact) + capstone windows.
No heuristics about "what the code looks like".
"""
import json
import re
import struct
import pefile
import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
RTTI = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json"

pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()

TEXT_VA = 0x00401000
TEXT_END = 0x007E038D
DATA_VA = 0x00812000
DATA_END = 0x00B79BE4
RDATA_VA = 0x007E1000
RDATA_END = 0x00811074

text = img[TEXT_VA - ib:TEXT_END - ib]
rdata = img[RDATA_VA - ib:RDATA_END - ib]
data = img[DATA_VA - ib:DATA_END - ib]

rtti = json.load(open(RTTI, encoding="utf-8"))
vt2name = {int(k, 16) if isinstance(k, str) and k.lower().startswith("0x") else int(k): v
           for k, v in rtti["vt2name"].items()}

print("RTTI vtables known: %d" % len(vt2name))

TARGETS = {
    "FUN_00654320 (site1)": 0x00654320,
    "FUN_006abd30 (site2,3)": 0x006ABD30,
    "FUN_006d04f0 (site4,5,6)": 0x006D04F0,
    "FUN_006d0680 (site7,8,9)": 0x006D0680,
    "FUN_006d09c0 (site10)": 0x006D09C0,
    "FUN_006d1200 (site11-14)": 0x006D1200,
    "FUN_006d14f0 (site15,16)": 0x006D14F0,
    "FUN_006d1610 (site18)": 0x006D1610,
    "FUN_006d1660 (site19,20)": 0x006D1660,
    "FUN_006922e0 (only caller of 6d0680)": 0x006922E0,
    "ORPHAN 0x6D15FA (site17)": 0x006D15FA,
    "FUN_004fc0b0 (crash entry)": 0x004FC0B0,
}


def find_dword(blob, base, val):
    pat = struct.pack("<I", val)
    out = []
    i = blob.find(pat)
    while i != -1:
        if i % 4 == 0:
            out.append(base + i)
        i = blob.find(pat, i + 1)
    return out


print("\n=== [A] immediate/pointer references to each target ===")
for label, va in TARGETS.items():
    pat = struct.pack("<I", va)
    in_text = [TEXT_VA + m.start() for m in re.finditer(re.escape(pat), text)]
    in_rdata = find_dword(rdata, RDATA_VA, va)
    in_data = find_dword(data, DATA_VA, va)
    # which vtable contains it?
    vt_hits = []
    for base, hits in (("rdata", in_rdata), ("data", in_data)):
        for h in hits:
            # walk back to a plausible vtable start: find contiguous run of
            # pointers into .text/.rdata-code-space
            start = h
            while start - 4 >= (RDATA_VA if base == "rdata" else DATA_VA):
                prevv = struct.unpack("<I", img[(start - 4) - ib:(start - 4) - ib + 4])[0]
                if 0x00401000 <= prevv < 0x00800000:
                    start -= 4
                else:
                    break
            nm = vt2name.get(start)
            vt_hits.append((base, h, start, nm))
    print("\n  %-38s 0x%08X   text_imm=%d rdata_ptr=%d data_ptr=%d"
          % (label, va, len(in_text), len(in_rdata), len(in_data)))
    for loc in in_text[:6]:
        pre = img[loc - 6 - ib:loc - ib + 6]
        print("      immediate in .text @0x%08X  ctx=%s" % (loc, pre.hex(" ")))
    for base, h, start, nm in vt_hits[:6]:
        print("      %s ptr @0x%08X  container_start=0x%08X  class=%s"
              % (base, h, start, nm))

print("\n=== [B] RTTI: is 0x6922E0 a vtable slot? class? ===")
for cls_vt, name in sorted(vt2name.items()):
    pass
for base, blobbase, blobend in (("rdata", RDATA_VA, RDATA_END), ("data", DATA_VA, DATA_END)):
    hits = find_dword(rdata if base == "rdata" else data, blobbase, 0x006922E0)
    for h in hits:
        start = h
        while start - 4 >= blobbase:
            prevv = struct.unpack("<I", img[(start - 4) - ib:(start - 4) - ib + 4])[0]
            if 0x00401000 <= prevv < 0x00800000:
                start -= 4
            else:
                break
        nm = vt2name.get(start)
        print("  0x6922E0 stored at 0x%08X inside vtable-ish start=0x%08X class=%s slot=%d"
              % (h, start, nm, (h - start) // 4))

print("\n=== [C] raw region 0x6D14E0 .. 0x6D1625 ===")
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
start, end = 0x006D14E0, 0x006D1625
for ins in md.disasm(img[start - ib:end - ib], start):
    print("   %08X  %-20s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
