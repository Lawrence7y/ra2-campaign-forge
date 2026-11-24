# COMMON-TECH-3 reproduction measurements, round 3
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

def sec_of(off):
    for n, sva, vs, raw, rs in secs:
        if raw <= off < raw + rs:
            return n, sva + (off - raw)
    return None, None

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

def dis(va, count=120, nbytes=900, stop_ret=True):
    for i in md.disasm(rd(va, nbytes), va):
        print("  %08X  %-22s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
        count -= 1
        if stop_ret and i.mnemonic == "ret":
            break
        if count <= 0:
            break

print("### G. slot8 deleting destructor body 0x004CA770 (FactoryClass) -- where is the delete flag consumed?")
dis(0x004CA770, 120, 900)

print("\n### H. counter-example: the S22 TClassFactory subfamily AddRef (M70 / AUDIT11) at 0x006C2AC0")
print("  bytes:", rd(0x006C2AC0, 16).hex())
dis(0x006C2AC0, 20, 160)

print("\n### I. factory vtable 0x007F3D98 (ctor 006C5140) slots 0..9")
for i in range(10):
    print("   slot%2d (vt+0x%02X) = 0x%08X" % (i, 4 * i, u32(0x007F3D98 + 4 * i)))

print("\n### J. how many places reference the AddRef/Release stubs (section split)")
for v, label in ((0x00410300, "AddRef stub mov eax,1;ret 4"), (0x00410310, "Release stub mov eax,1;ret 4")):
    p = struct.pack("<I", v)
    hits, i = [], data.find(p)
    while i >= 0:
        hits.append(i)
        i = data.find(p, i + 1)
    split = {}
    for h in hits:
        n, va = sec_of(h)
        split.setdefault(n, []).append(va)
    print("   0x%08X [%s] total %d hits: %s" % (v, label, len(hits),
          {k: len(vv) for k, vv in split.items()}))
    for k, vv in split.items():
        print("      %s VAs: %s" % (k, ["0x%08X" % x for x in vv[:12]]))

print("\n### K. S22_B4 11 rows: factory ctor = entry-0xD0, its vt, and the vt literal count")
rows = [0x006C5210, 0x006C5390, 0x006C5510, 0x006C5690, 0x006C5810, 0x006C5990,
        0x006C5B10, 0x006C5C90, 0x006C5E10, 0x006C5F90, 0x006C6110]
def count_imm(v):
    p = struct.pack("<I", v)
    c, i = 0, data.find(p)
    while i >= 0:
        c += 1
        i = data.find(p, i + 1)
    return c
for e in rows:
    c = e - 0xD0
    b = rd(c, 12)
    vt = struct.unpack("<I", b[8:12])[0] if b else None
    print("   entry 0x%08X  factory ctor 0x%08X bytes=%s  vt=0x%08X  vt-literal count=%d"
          % (e, c, b.hex() if b else "-", vt, count_imm(vt)))
