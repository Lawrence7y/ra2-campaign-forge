#!/usr/bin/env python3
"""W127h: verify the ds-verify subagent's contested claims against raw bytes.

Claims to check (do NOT trust the subagent; re-derive from the file):
  V1  0x006922E0 has a direct caller at 0x005BDF1F, and is ScrollClass vt 0x7F1094 slot 10.
  V2  0x004F8F82 lies inside a function starting at 0x004F8440.
  V3  0x004F8440 has no direct call/jmp caller anywhere in .text.
  V4  0x004F8440's only static data reference is .rdata:0x007EA8FC,
      vtable 0x007EA8A0 slot 23, class .?AVHouseClass@@ (RTTI read byte-wise).
  V5  0x004FC0B0 has two static code references: call@0x004F8F82 and jmp@0x004FC6A0.
  V6  the byte range of FUN_006d14f0's body is instruction-identical to a range
      inside FUN_006d1660 at +0x181.
  V7  .rdata:0x007EDFDC is vtable 0x007EDFB4 slot 10 (TabClass) and holds 0x006D0680.
"""
import pefile
import capstone
import struct

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
TEXT_VA, TEXT_END = 0x00401000, 0x007E038D
text = img[TEXT_VA - ib:TEXT_END - ib]

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True


def u32(va):
    return struct.unpack("<I", img[va - ib:va - ib + 4])[0]


def calls_to(target):
    out = []
    for ins in md.disasm(text, TEXT_VA):
        if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
            if int(ins.op_str, 16) == target:
                out.append((ins.address, ins.mnemonic))
    return out


def data_ptrs(val):
    hits = []
    for name, lo, hi in ((".rdata", 0x007E1000, 0x00811074),
                         (".data", 0x00812000, 0x0087E000)):   # .data raw only!
        for va in range(lo, hi - 3, 4):
            if u32(va) == val:
                hits.append((name, va))
    return hits


def rtti_of_vtable(vt):
    col = u32(vt - 4)
    ptd = u32(col + 0x0C)
    raw = img[ptd + 0x08 - ib:ptd + 0x08 - ib + 64]
    name = raw.split(b"\x00")[0].decode("latin-1", "replace")
    return col, ptd, name


print("=== V1: callers of 0x006922E0 / its vtable slot ===")
for a, m in calls_to(0x006922E0):
    print("   %s @0x%08X" % (m, a))
print("   vtable slot check: .rdata 0x7F10BC = 0x%08X" % u32(0x007F10BC))
col, ptd, nm = rtti_of_vtable(0x007F1094)
print("   vt 0x7F1094: COL=0x%08X TD=0x%08X name=%s slot=%d"
      % (col, ptd, nm, (0x007F10BC - 0x007F1094) // 4))

print("\n=== V5: code refs to 0x004FC0B0 ===")
for a, m in calls_to(0x004FC0B0):
    print("   %s @0x%08X" % (m, a))

print("\n=== V2/V3/V4: what contains 0x4F8F82, and who reaches it ===")
for a, m in calls_to(0x004F8440):
    print("   ref to 0x4F8440: %s @0x%08X" % (m, a))
ptr = data_ptrs(0x004F8440)
print("   data pointers to 0x4F8440: %s" % ptr)
for sec, va in ptr:
    # walk back to vtable start, then RTTI
    start = va
    while start - 4 >= (0x007E1000 if sec == ".rdata" else 0x00812000):
        prev = u32(start - 4)
        if 0x00401000 <= prev < 0x00800000:
            start -= 4
        else:
            break
    col, ptd, nm = rtti_of_vtable(start)
    print("      -> %s:0x%08X = vt 0x%08X slot %d  COL=0x%08X TD=0x%08X %s"
          % (sec, va, start, (va - start) // 4, col, ptd, nm))

print("\n=== V2: disassembly around 0x4F8420..0x4F8460 (is 0x4F8440 an entry?) ===")
for ins in md.disasm(img[0x004F8420 - ib:0x004F8460 - ib], 0x004F8420):
    print("   %08X  %-22s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
print("   instruction containing 0x4F8F82:")
for ins in md.disasm(img[0x004F8F78 - ib:0x004F8F8C - ib], 0x004F8F78):
    mark = "  <== contains 0x4F8F82" if ins.address <= 0x4F8F82 < ins.address + ins.size else ""
    print("   %08X  %-22s %s %s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))

print("\n=== V6: is FUN_006d14f0's body mirrored inside FUN_006d1660 at +0x181? ===")
for lo, hi, lbl in ((0x006D14F0, 0x006D1564, "orig 0x6D14F0"),
                    (0x006D1671, 0x006D16E5, "orig+0x181")):
    a = img[lo - ib:hi - ib]
    b = img[lo + 0x181 - ib:hi + 0x181 - ib]
    same = sum(1 for x, y in zip(a, b) if x == y)
    print("   %s: %d/%d bytes equal to +0x181 shifted copy" % (lbl, same, len(a)))
    # align on instruction boundary: start comparing at 0x6D14F9 and 0x6D167A
a = img[0x006D14F9 - ib:0x006D1564 - ib]
b = img[0x006D167A - ib:0x006D16E5 - ib]
print("   0x6D14F9..0x6D1563 vs 0x6D167A..: equal bytes %d/%d"
      % (sum(1 for x, y in zip(a, b) if x == y), len(a)))
ia = [i for i in md.disasm(img[0x006D14F9 - ib:0x006D1564 - ib], 0x006D14F9)]
ib_ = [i for i in md.disasm(img[0x006D167A - ib:0x006D16E4 - ib], 0x006D167A)]
print("   insns: %d vs %d" % (len(ia), len(ib_)))
n_same = 0
for x, y in zip(ia, ib_):
    if x.mnemonic == y.mnemonic and (x.op_str == y.op_str or
       (x.mnemonic.startswith("j") and y.mnemonic.startswith("j"))):
        n_same += 1
print("   same mnemonic(+jump class): %d" % n_same)

print("\n=== V7: TabClass slot 10 ===")
print("   .rdata 0x7EDFDC = 0x%08X" % u32(0x007EDFDC))
col, ptd, nm = rtti_of_vtable(0x007EDFB4)
print("   vt 0x7EDFB4: COL=0x%08X TD=0x%08X name=%s slot=%d"
      % (col, ptd, nm, (0x007EDFDC - 0x007EDFB4) // 4))
