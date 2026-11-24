"""
S06-K2 foundation: verify RTTI TypeDescriptors, COL -> vtable chains, and
determine the true CellClass / MapClass method sets (from .rdata, NOT atlas).
All addresses VA (ImageBase 0x400000). Read-only on target.
Outputs to EVIDENCE/foundation.txt
"""
from pehelp import *
import struct, sys

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\foundation.txt"
_lines = []
def p(s=''):
    print(s); _lines.append(str(s))

def td_name(td):
    """TypeDescriptor: TD+8 = name (char[?], nul-terminated, leading '.?AV' / '.?AU')."""
    # TD layout: +0 vftable ptr, +4 reserved(0), +8 name string
    b = read(td + 8, 128)
    if not b: return None
    z = b.find(b'\0')
    if z < 0: z = len(b)
    return b[:z].decode('latin1')

def col_info(col):
    """COL (COLLECTOR) layout: +0 = signature? ; +4 = offset-to-top ; +8 = CD (CompleteObjectLocator ptr to TD?) ;
       Actually MSVC RTTI: COLLECTOR: +0 sig, +4 offset, +8 cdOffset, +0xC pTypeDescriptor, +0x10 pClassHierarchyDescriptor.
       The reliable chain per R14: COL + 0xC -> TD ; then TD + 8 -> name."""
    td = u32(col + 0xC)
    return td, td_name(td) if td else None

def dump_vtable(vt, n, label):
    p(f"\n-- vtable {label} @ {vt:#x} (first {n} slots) --")
    for i in range(n):
        f = u32(vt+i*4)
        sec = section_of(f) if f else None
        tag = sec[4] if sec else '---'
        p(f"  [{i:3d}] +{i*4:#05x}: {f:#010x} {tag}")

p("="*72)
p("S06-K2 FOUNDATION (RTTI / vtable / method set), target gamemd.exe 73201CC0..F67476")
p("="*72)

# CellClass
p("\n[CellClass]")
p(f"  TD 0x81cd70 name = {td_name(0x81cd70)!r}")
# find COL by searching .rdata for pointer to TD 0x81cd70
# COL + 0xC == TD. scan .rdata for dword == 0x81cd70
col_hits=[]
rdata = next(s for s in SECTIONS if s[4]=='.rdata')
lo, hi = rdata[0], rdata[0]+rdata[2]  # VA range raw
data = pe.get_data(rdata[2], rdata[3])
for i in range(0, len(data)-3, 4):
    if struct.unpack_from('<I', data, i)[0] == 0x81cd70:
        col_hits.append(rdata[0]+i)
p(f"  COL candidates (.rdata dword == TD): {[hex(x) for x in col_hits]}")
for col in col_hits:
    td, nm = col_info(col)
    p(f"    COL {col:#x}: +0xC->TD {td:#x} name={nm!r}; +4 off={u32(col+4):#x}; +8 cd={u32(col+8):#x}; +0x10 CHD={u32(col+0x10):#x}")

# known primary vtable 0x7e4eec ; vtable[-1] = COL
CELL_VT = 0x7e4eec
p(f"  primary vtable 0x7e4eec: [-1] (0x7e4ee8) = {u32(CELL_VT-4):#x} (should be COL)")
dump_vtable(CELL_VT, 40, 'CellClass primary')

# MapClass
p("\n[MapClass]")
p(f"  TD 0x816bc0 name = {td_name(0x816bc0)!r}")
col_hits2=[]
for i in range(0, len(data)-3, 4):
    if struct.unpack_from('<I', data, i)[0] == 0x816bc0:
        col_hits2.append(rdata[0]+i)
p(f"  COL candidates (.rdata dword == TD): {[hex(x) for x in col_hits2]}")
for col in col_hits2:
    td, nm = col_info(col)
    p(f"    COL {col:#x}: +0xC->TD {td:#x} name={nm!r}; +4 off={u32(col+4):#x}; +8 cd={u32(col+8):#x}; +0x10 CHD={u32(col+0x10):#x}")
MAP_VT = 0x7ed404
p(f"  primary vtable 0x7ed404: [-1] (0x7ed400) = {u32(MAP_VT-4):#x} (should be COL)")
dump_vtable(MAP_VT, 34, 'MapClass primary')

with open(OUT,'w') as f:
    f.write('\n'.join(_lines)+'\n')
p(f"\n[saved] {OUT}")
