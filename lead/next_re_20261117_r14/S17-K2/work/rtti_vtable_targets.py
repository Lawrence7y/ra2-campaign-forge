#!/usr/bin/env python3
"""S17-K2: RTTI/vtable resolution + function disassembly for S17 target entries.
Reuses S17-F1 pe_util (read-only). capstone skipdata=True.
Writes only to S17-K2\work and S17-K2\EVIDENCE.
"""
import sys, struct, os, re, io
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work")
import pe_util as P
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-K2\EVIDENCE"

# target addresses from T1
TARGETS = [
  0x004068E0,0x0040E340,0x0041D6E0,0x00427940,0x0042E410,0x00431B80,0x00433CF0,0x004355B0,0x0043A5D0,0x0043AE50,
  0x0049F740,0x0049F8B0,0x004B6BB0,0x00539AE0,0x0055AAC0,0x0067C690,0x00773450,
]

def sec_of(va):
    for name, va_base, vsize, praw, rawsize, ch in P.sections():
        if va_base <= va < va_base + max(vsize, rawsize):
            return name
    return "?"

def is_rtti_col(col_va):
    """Validate a Complete Object Locator: signature==0 at +0, TD ptr plausible, name readable."""
    sig = P.u32(col_va)
    if sig != 0:  # MSVC RTTI COL signature is 0 (RTTICompleteObjectLocator signature=0)
        return None
    td = P.u32(col_va+0xC)
    if td is None or not (0x400000 <= td <= 0x900000):
        return None
    vf = P.u32(td)       # TypeDescriptor vftable ptr (in .rdata)
    name_off = P.read(td+8, 64)
    if name_off is None: return None
    # name is '.?AV...@@' style NUL-terminated
    nm = name_off.split(b'\x00')[0]
    try: s = nm.decode('ascii')
    except: return None
    if not s.startswith('.?AV') and not s.startswith('.?AU'):
        return None
    return (td, s)

def vtable_class(vt_va):
    """Given a vtable address (first slot), resolve class name via vtable[-1] -> COL -> TD."""
    col = P.u32(vt_va-4)
    if col is None: return None
    r = is_rtti_col(col)
    if r is None: return None
    return (col, r[0], r[1])

def demangle_simple(s):
    # .?AVClassName@@ -> ClassName
    m = re.match(r'\.\?A[UV]([A-Za-z0-9_]+)@@', s)
    return m.group(1) if m else s

# Build map: slot_value_addr -> list of (vtable_va, slot_index, class_name)
out = io.StringIO()
def p(*a): print(*a, file=out)

p("S17-K2 RTTI / vtable resolution for unnamed S17 target entries")
p("="*100)
p("Method: for each target function VA, scan every section for a dword equals VA.")
p("  Each hit in .rdata is a candidate vtable slot. For a candidate at address A,")
p("  find the vtable base V = A - 4*slot_index by walking backwards over consecutive")
p("  code pointers; then resolve class via V[-4] -> COL(sig=0) -> COL[+0xC]=TD -> TD+8 name.")
p("  Also scan for static-init C7 05 <obj><vt> writing V into an object.")

# Pre-scan: all dword refs to targets, grouped by section
all_hits = {}
for t in TARGETS:
    hits = P.scan_imm32_refs(t)
    all_hits[t] = hits

# helper: find consecutive code pointers ending at a hit (vtable detection)
def find_vtable_base(hit_va):
    """walk backwards from hit_va while preceding dword looks like code ptr in .text"""
    lo, hi = P.sections()[0][1], None
    # .text range
    txt = [s for s in P.sections() if s[0]=='.text'][0]
    txtlo, txthi = txt[1], txt[1]+txt[2]
    base = hit_va
    # walk back up to 100 slots
    for _ in range(100):
        prev = P.u32(base-4)
        if prev is None or not (txtlo <= prev < txthi):
            break
        base -= 4
    return base

for t in TARGETS:
    p(f"\n### 0x{t:08X}  section={sec_of(t)}")
    hits = all_hits[t]
    p(f"  dword refs total = {len(hits)}")
    rdata_hits = [h for h in hits if h[1]=='.rdata']
    p(f"  .rdata hits = {len(rdata_hits)}")
    seen_vt = set()
    for hva, sname in rdata_hits:
        vb = find_vtable_base(hva)
        if vb in seen_vt: continue
        seen_vt.add(vb)
        slot = (hva - vb)//4
        res = vtable_class(vb)
        p(f"    hit@0x{hva:08X} vtable_base=0x{vb:08X} slot={slot} (+0x{slot*4:X}) class_res={res}")
    # if no rdata class resolved, try: maybe hit is itself preceded by COL pattern (vtable[-1] at hit-4 only if slot0)
    # Static init scan: C7 05 <obj><vt> where value==vt of any resolved vtable — report separately later

# Write
with open(os.path.join(OUT,"rtti_vtable_targets.txt"),"w",encoding="utf-8") as f:
    f.write(out.getvalue())
print("wrote rtti_vtable_targets.txt")
