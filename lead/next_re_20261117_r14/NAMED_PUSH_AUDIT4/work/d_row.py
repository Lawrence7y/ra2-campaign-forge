"""Per-row independent verification dump.
usage: python d_row.py 006BF810
"""
import sys, struct, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt, IMAGEBASE

img = Img()
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D
IAT_CRC = 0x7E15D8      # ole32!CoRegisterClassObject
IAT_CCI = 0x7E15FC      # ole32!CoCreateInstance

entry = int(sys.argv[1], 16)

print("### SECTION LAYOUT")
for name, base, vsz, praw, rsz in img.sections:
    print("  %-8s %08X .. %08X  raw=%08X" % (name, base, base + max(vsz, rsz), praw))

# ---------- ② vtable & RTTI ----------
print("\n### ② vtable/RTTI")
raw = img.data
hits = []
for i in range(0, len(raw) - 4):
    pass  # too slow in python; use section-limited scan instead
def scan_dword(val, lo, hi):
    out = []
    b = img.read(lo, hi - lo)
    if not b:
        return out
    for i in range(0, len(b) - 3, 4):
        if struct.unpack_from('<I', b, i)[0] == val:
            out.append(lo + i)
    return out

# candidate locations (read-only data sections)
for name, base, vsz, praw, rsz in img.sections:
    if name in ('.text', '.data'):
        continue
    for va in scan_dword(entry, base, base + max(vsz, rsz)):
        col = img.u32(va - 4)
        sig = img.u32(col) if col else None
        print("  dword==entry at %08X (sec %s); [va-4]=%08X sig=%s" % (va, name, col or 0, sig))
        hits.append(va)

# ---------- RTTI resolution helper ----------
def rtti_of(vt):
    col = img.u32(vt - 4)
    if not col:
        return None
    sig = img.u32(col)
    off = img.u32(col + 4)
    cd = img.u32(col + 8)
    td = img.u32(col + 0xC)
    cd2 = img.u32(col + 0x10)
    name = img.cstr(td + 8) if td else None
    return dict(col=col, sig=sig, offset=off, cd=cd, td=td, cd2=cd2, name=name)

# ---------- ③b body ----------
print("\n### ③b BODY")
body = img.body(entry)
for ins in body:
    print("  " + fmt(ins))
imm_codes = []
for ins in body:
    if ins.mnemonic == 'mov' and ins.op_str.startswith('eax, 0x8'):
        imm_codes.append((ins.address, ins.op_str.split(', ')[1]))
print("  imm error codes:", imm_codes)
rets = [hex(i.address) for i in body if i.mnemonic.startswith('ret')]
print("  rets:", rets)

# find QI call site: 'call dword ptr [eax]' after 'mov eax, dword ptr [reg]'
print("\n### ③b QI site")
qi = [i for i in body if i.mnemonic == 'call' and i.op_str == 'dword ptr [eax]']
for q in qi:
    print("  QI call @%08X bytes=%s" % (q.address, q.bytes.hex(' ')))
qi_addr = qi[0].address if qi else None

# disasm callee of QI: need the vt installed on the fresh object -> follow ctor call
ctor_calls = [i for i in body if i.mnemonic == 'call' and i.op_str.startswith('0x')]
for c in ctor_calls:
    print("  direct call @%08X -> %s" % (c.address, c.op_str))

print("\n### ④ vt-imm references in .text")
refs = scan_dword(entry, TEXT_LO, TEXT_HI)  # self-reference sanity
# factory vt: candidate vt = the table whose slot3 == entry (found above, top of list)
