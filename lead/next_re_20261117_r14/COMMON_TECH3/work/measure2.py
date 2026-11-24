# COMMON-TECH-3 reproduction measurements, round 2
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
T = [s for s in secs if s[0] == ".text"][0]
tva, tvs, traw, trs = T[1], T[2], T[3], T[4]

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

def dis(va, count=40, nbytes=300):
    for i in md.disasm(rd(va, nbytes), va):
        print("  %08X  %-22s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
        count -= 1
        if count <= 0:
            break

print("### C2. failure path of 0x006C5210 (push 1 + call [reg+0x20])")
print("  @0x006C5270:")
dis(0x006C5270, 14, 60)

print("\n### C3. vt[8] of the two tables (slot8 = vt+0x20 = deleting destructor slot)")
for vt in (0x007E88D0, 0x007E5358, 0x007F4348, 0x007E1964):
    print("  vt 0x%08X : slot8 = 0x%08X   slot0 = 0x%08X" % (vt, u32(vt + 0x20), u32(vt)))

print("\n### E2. is each write site a deleting destructor?  (flag test + operator delete 0x7C8B3D)")
for va, label in ((0x004CA770, "vt[8] of FactoryClass table 007E88D0"),
                  (0x00490400, "write site 00490406 row 00491210"),
                  (0x006DC470, "write site 006DC475 row 006DBD20"),
                  (0x0040D1B0, "write site 0040D1B2 (atexit-registered global dtor)"),
                  (0x0040D290, "write site 0040D295")):
    print("  -- 0x%08X  [%s] --" % (va, label))
    dis(va, 40, 320)

print("\n### F. S22_B4 factory ctors: vt immediate + its occurrence count in whole file")
pat = bytes.fromhex("c74004000000 00".replace(" ", "")) + bytes.fromhex("c700")
def count_imm(v):
    p = struct.pack("<I", v)
    hits, i = [], data.find(p)
    while i >= 0:
        hits.append(i)
        i = data.find(p, i + 1)
    return hits

found = []
i = data.find(pat, traw)
while i >= 0:
    if i + len(pat) + 5 <= len(data):
        vt = struct.unpack("<I", data[i + len(pat):i + len(pat) + 4])[0]
        va = tva + (i - traw)
        found.append((va, vt))
    i = data.find(pat, i + 1)
for va, vt in found:
    hits = count_imm(vt)
    svas = [("0x%08X" % (tva + (h - traw))) if traw <= h < traw + trs else "non-.text" for h in hits]
    print("  ctor 0x%08X -> vt 0x%08X : %d occurrence(s) %s" % (va, vt, len(hits), svas))
