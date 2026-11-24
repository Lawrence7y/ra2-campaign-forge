# a-S17-ENGFAM audit, script a1: sections + per-entry disassembly + independent byte-diff
# Own evidence only. capstone skipdata=True as card demands.
import pefile, capstone, hashlib, json, os
from capstone import *

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17_ENGFAM\EVIDENCE"
os.makedirs(OUT, exist_ok=True)

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
print("ImageBase = 0x%08X" % IB)
secs = {}
for s in pe.sections:
    name = s.Name.rstrip(b"\x00").decode(errors="replace")
    va = IB + s.VirtualAddress
    vsize = s.Misc_VirtualSize
    secs[name] = (va, va + vsize, s.VirtualAddress, s.SizeOfRawData)
    print("%-8s VA=[0x%08X,0x%08X) raw=0x%X vsize=0x%X" % (name, va, va + vsize, s.SizeOfRawData, vsize))

def rva2off(rva):
    return pe.get_offset_from_rva(rva)

def va2off(va):
    return rva2off(va - IB)

def read(va, n):
    off = va2off(va)
    d = pe.__data__
    return bytes(d[off:off+n])

text_lo, text_hi = secs['.text'][0], secs['.text'][1]
print(".text = [0x%08X, 0x%08X)  card says [0x401000,0x7E038D) -> %s" % (text_lo, text_hi, (text_lo==0x401000 and text_hi==0x7E038D)))

ENTRIES = []
for n in list(range(1,17))+list(range(18,36)):
    ENTRIES.append(("Save_VectorBlock_%02d" % n, 0x0067FDF0 + 0x80*(n-1)))
# sanity: _16 at 0x67FDF0+0x80*15=0x680570 ; _18 at 0x680670 -> gap slot 0x6805F0
assert ENTRIES[15][1] == 0x00680570 and ENTRIES[16][1] == 0x00680670
EXTRA = [("slot#17=0x6805F0 (coverage: absent)", 0x006805F0)]

md = capstone.Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
md.detail = True

lines = []
bodies = {}
def disasm_window(va, nbytes, tag):
    code = read(va, nbytes)
    lines.append("=" * 100)
    lines.append("[%s] entry 0x%08X window %d bytes" % (tag, va, nbytes))
    body = []
    for insn in md.disasm(code, va):
        raw = " ".join("%02X" % b for b in insn.bytes)
        lines.append("  0x%08X  %-24s %s %s" % (insn.address, raw, insn.mnemonic, insn.op_str))
        body.append((insn.address, insn.bytes, insn.mnemonic, insn.op_str))
        if insn.mnemonic == "ret" or insn.bytes[0] == 0xC3:
            lines.append("  --- ret reached ---")
            break
    lines.append("")
    return body

print("\n--- per-entry disassembly (until first C3, window 0x90) ---")
for name, va in ENTRIES + EXTRA:
    body = disasm_window(va, 0x90, name)
    bodies[name] = body

# independent 127B md5 + pairwise byte diff
print("\n--- own byte checks ---")
h127 = {}
for name, va in ENTRIES + EXTRA:
    code = read(va, 127)
    h = hashlib.md5(code).hexdigest()
    h127[name] = h
    print("%-24s 0x%08X md5(127B)=%s" % (name, va, h))
distinct = set(h127.values())
print("distinct 127B md5 count over 34+1 slots:", len(distinct))
# byte-level pairwise diff of first function vs all others
base = read(ENTRIES[0][1], 127)
for name, va in ENTRIES + EXTRA:
    code = read(va, 127)
    diffs = [i for i in range(127) if base[i] != code[i]]
    print("%-24s diff vs #1: %d bytes %s" % (name, len(diffs), diffs[:16]))

with open(os.path.join(OUT, "bodies.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\nwrote", os.path.join(OUT, "bodies.txt"))
