# COMMON-TECH-3 reproduction measurements, round 4
import sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

IMG = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(IMG, "rb").read()
pe = pefile.PE(IMG, fast_load=True)
ib = pe.OPTIONAL_HEADER.ImageBase
secs = [(s.Name.rstrip(b"\x00").decode(), s.VirtualAddress + ib, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]

def va2off(va):
    for n, sva, vs, raw, rs in secs:
        if sva <= va < sva + max(vs, rs):
            o = raw + (va - sva)
            if 0 <= o < len(data):
                return o
    return None

def rd(va, n):
    o = va2off(va)
    return None if o is None else data[o:o + n]

def u32(va):
    b = rd(va, 4)
    return None if b is None or len(b) < 4 else struct.unpack("<I", b)[0]

md = Cs(CS_ARCH_X86, CS_MODE_32)

def dis(va, count=20, nbytes=120):
    for i in md.disasm(rd(va, nbytes), va):
        print("  %08X  %-22s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
        count -= 1
        if i.mnemonic == "ret" or count <= 0:
            break

def count_imm(v):
    p = struct.pack("<I", v)
    c, i = 0, data.find(p)
    while i >= 0:
        c += 1
        i = data.find(p, i + 1)
    return c

print("### K2 (fixed). S22_B4 11 rows: factory ctor = entry-0xD0, vt at ctor+0xA, vt literal count")
rows = [0x006C5210, 0x006C5390, 0x006C5510, 0x006C5690, 0x006C5810, 0x006C5990,
        0x006C5B10, 0x006C5C90, 0x006C5E10, 0x006C5F90, 0x006C6110]
for e in rows:
    c = e - 0xD0
    b = rd(c, 16)
    vt = struct.unpack("<I", b[11:15])[0]
    print("   entry 0x%08X  ctor 0x%08X  bytes=%s  vt=0x%08X  vt-literal count=%d  ctor_slot3=vt[3]=0x%08X"
          % (e, c, b.hex(), vt, count_imm(vt), u32(vt + 0x0C)))

print("\n### L. the factory's OWN table 0x007F3D98 slot1 / slot2 bodies (not the stub)")
for va in (0x006C51C0, 0x006C51E0):
    print("  @0x%08X:" % va)
    dis(va, 14, 80)

print("\n### M. 0x00410300 / 0x00410310 bytes exactly (stub proof)")
for va in (0x00410300, 0x00410310):
    print("  0x%08X = %s" % (va, rd(va, 8).hex()))

print("\n### N. S07_B1 rows: entry fn and the 4/3 write sites with their function start guess")
for v, label in ((0x007E5358, "row 00491210 ConvertClass table"),
                 (0x007F4348, "row 006DBD20 Tactical table")):
    print("  -- %s 0x%08X --" % (label, v))
    p = struct.pack("<I", v)
    i = data.find(p)
    while i >= 0:
        n, va = None, None
        for nm, sva, vs, raw, rs in secs:
            if raw <= i < raw + rs:
                n, va = nm, sva + (i - raw)
        print("     raw off 0x%X -> %s 0x%08X" % (i, n, va if va else 0))
        i = data.find(p, i + 1)
