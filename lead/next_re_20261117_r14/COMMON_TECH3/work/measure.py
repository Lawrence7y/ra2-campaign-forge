# COMMON-TECH-3 reproduction measurements (read-only on the image)
# argv[1] = path to gamemd.exe
import sys, hashlib, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

IMG = sys.argv[1] if len(sys.argv) > 1 else r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(IMG, "rb").read()
print("IMAGE      =", IMG)
print("SIZE       =", len(data))
print("SHA256     =", hashlib.sha256(data).hexdigest().upper())

pe = pefile.PE(IMG, fast_load=True)
ib = pe.OPTIONAL_HEADER.ImageBase
soi = pe.OPTIONAL_HEADER.SizeOfImage
print("ImageBase  = 0x%08X" % ib)
print("SizeOfImage= 0x%08X" % soi)
secs = [(s.Name.rstrip(b"\x00").decode(), s.VirtualAddress + ib, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
for n, va, vs, raw, rs in secs:
    print("  SEC %-8s VA 0x%08X vsize 0x%-7X raw 0x%-7X rsize 0x%X" % (n, va, vs, raw, rs))

def va2off(va):
    for n, sva, vs, raw, rs in secs:
        if sva <= va < sva + max(vs, rs):
            off = raw + (va - sva)
            if 0 <= off < len(data):
                return off
    return None

def rd(va, n):
    o = va2off(va)
    return None if o is None else data[o:o + n]

def u32(va):
    b = rd(va, 4)
    return None if b is None or len(b) < 4 else struct.unpack("<I", b)[0]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

def dis(va, count=24, nbytes=160):
    b = rd(va, nbytes)
    out = []
    for i in md.disasm(b, va):
        out.append("  %08X  %-22s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
        if len(out) >= count:
            break
    return out

print("\n### A. RTTI: vt[-1] -> COL ; COL.pTD / COL.pCHD are absolute VA, not RVA")
def col_of_vt(vt_va):
    col = u32(vt_va - 4)
    b = rd(col, 20)
    sig, off, cd, ptd, pchd = struct.unpack("<IIIII", b)
    return col, sig, off, cd, ptd, pchd

CASE = [(0x007E88D0, "FactoryClass main vt (006C5210)"),
        (0x007F6B30, "WarheadTypeClass main vt (006C5390)"),
        (0x007F3D98, "TClassFactory ctor 006C5140 vt"),
        (0x007E1964, "MouseClass vt (004F45B0)")]
for vt, label in CASE:
    col, sig, off, cd, ptd, pchd = col_of_vt(vt)
    print("vt=0x%08X [%s]" % (vt, label))
    print("   vt[-1] -> COL = 0x%08X ; sig=%d off=0x%X cd=0x%X pTD=0x%08X pCHD=0x%08X"
          % (col, sig, off, cd, ptd, pchd))
    for name, p in (("pTD", ptd), ("pCHD", pchd)):
        inimg = ib <= p < ib + soi
        print("   %s=0x%08X  >=ImageBase? %s  in-image? %s  RVA-interpretation IB+0x%X = 0x%08X (%s)"
              % (name, p, p >= ib, inimg, p, ib + p,
                 "IN" if ib + p < ib + soi else "OUT>=SizeOfImage"))

col, sig, off, cd, ptd, pchd = col_of_vt(0x007F6B30)
try:
    pe.get_data(ptd, 16)
    print("   pefile.get_data(0x%08X as RVA): returned bytes (no exception)" % ptd)
except Exception as e:
    print("   pefile.get_data(0x%08X as RVA): %s: %s" % (ptd, type(e).__name__, str(e).strip()))

print("\n### B. RTTI: decorated name is INLINE at TD+8 (not a pointer)")
for td, label in ((ptd, "TD of WarheadTypeClass vt 007F6B30"), (0x00815E18, "TD 0x815E18 (draft 990)")):
    b = rd(td, 64)
    if b is None:
        print("TD 0x%08X: not mapped" % td); continue
    print("TD 0x%08X [%s]" % (td, label))
    print("   first 32 bytes = 0x%s" % b[:32].hex())
    print("   bytes[+8:+20]  = %s" % b[8:20].hex())
    ptr = u32(td + 8)
    print("   u32(TD+8) = 0x%08X ; mapped as pointer? %s" % (ptr, va2off(ptr) is not None))
    end = b.find(b"\x00", 8)
    end = len(b) if end < 0 else end
    print("   inline NUL-terminated string at TD+8 = %r" % (b[8:end].decode("latin1"),))

print("\n### C. AddRef / Release stubs and the real failure path")
for va, label in ((0x00410300, "slot1"), (0x00410310, "slot2"), (0x00410260, "QI helper")):
    b = rd(va, 12)
    print("0x%08X [%s] bytes = %s" % (va, label, b.hex()))
    for ln in dis(va, 3):
        print(ln)

print("\n-- TClassFactory<V>::CreateInstance 0x006C5210 (first 40 insns) --")
for ln in dis(0x006C5210, 40, 200):
    print(ln)

print("\n-- main vtable 0x007E88D0 slots 0..11 --")
for i in range(12):
    print("   vt[%2d] (vt+0x%02X) = 0x%08X" % (i, 4 * i, u32(0x007E88D0 + 4 * i)))

t8 = u32(0x007E88D0 + 0x20)
print("\n-- vt[8] = vt+0x20 target 0x%08X body --" % t8)
for ln in dis(t8, 34, 240):
    print(ln)

print("\n### D. count of 32-bit immediates equal to each vtable VA (whole file, incl. headers)")
def count_imm(v):
    pat = struct.pack("<I", v)
    hits, i = [], data.find(pat)
    while i >= 0:
        hits.append(i)
        i = data.find(pat, i + 1)
    return hits

for v in (0x007E88D0, 0x007F6B30, 0x007F3D98, 0x007E5358, 0x007F4348, 0x007E1964):
    hits = count_imm(v)
    t = [s for s in secs if s[0] == ".text"][0]
    vas = [(t[1] + (h - t[3])) if t[3] <= h < t[3] + t[4] else None for h in hits]
    print("   imm32 0x%08X : %d hit(s); .text VAs = %s"
          % (v, len(hits), [("0x%08X" % x if x else "non-.text") for x in vas]))

print("\n### E. 0x23 trap: enumerate every store site of a table immediate inside .text")
def store_sites(v):
    t = [s for s in secs if s[0] == ".text"][0]
    tva, tvs, traw, trs = t[1], t[2], t[3], t[4]
    out = []
    for h in count_imm(v):
        if not (traw <= h < traw + trs):
            continue
        fva = tva + (h - traw)
        for start in range(fva - 10, fva + 1):
            if start < tva:
                continue
            done = False
            for i in md.disasm(rd(start, 20), start):
                if i.address > fva:
                    break
                if i.address + i.size == fva + 4:
                    out.append((i.address, i.mnemonic + " " + i.op_str, i.bytes.hex()))
                    done = True
                    break
                if i.address + i.size > fva + 4:
                    break
            if done:
                break
    return sorted(set(out))

for v, label in ((0x007E5358, "row 00491210 ConvertClass main vt"),
                 (0x007F4348, "row 006DBD20 Tactical main vt"),
                 (0x007E1964, "row 004F45B0 MouseClass vt")):
    print("-- %s : table 0x%08X --" % (label, v))
    for a, txt, bx in store_sites(v):
        print("   site 0x%08X  %-34s %s" % (a, txt, bx))

print("\n-- disasm around the reported atexit/dtor sites --")
for va, n in ((0x0040D190, 16), (0x00490400, 12), (0x006DC470, 12), (0x0040D290, 12)):
    print("  @0x%08X:" % va)
    for ln in dis(va, n, 64):
        print(ln)
