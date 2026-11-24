"""
S06-K2: discover all CellClass/MapClass vtables via RTTI COL chain,
build the authoritative method set (from .rdata, NOT atlas).
Outputs EVIDENCE/method_sets.txt
"""
from pehelp import *
import struct

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S06-K2\EVIDENCE\method_sets.txt"
_lines=[]
def p(s=''):
    print(s); _lines.append(str(s))

def find_cols_for_td(td):
    """COL base addresses X where u32(X+0xC)==td. These are the COLs that name this class."""
    rdata = next(s for s in SECTIONS if s[4]=='.rdata')
    data = pe.get_data(rdata[2], rdata[3])
    cols=[]
    for i in range(0, len(data)-3, 4):
        if struct.unpack_from('<I', data, i)[0]==td:
            base = rdata[0]+i-0xC
            cols.append(base)
    return cols

def find_vtables_for_col(col):
    """Scan .rdata for dword==col at address A; vtable begins at A+4."""
    rdata = next(s for s in SECTIONS if s[4]=='.rdata')
    data = pe.get_data(rdata[2], rdata[3])
    vts=[]
    for i in range(0, len(data)-3, 4):
        if struct.unpack_from('<I', data, i)[0]==col:
            vts.append(rdata[0]+i+4)
    return vts

def vt_slots(vt, n=40):
    out=[]
    for i in range(n):
        f=u32(vt+i*4)
        sec=section_of(f) if f else None
        out.append((i, f, sec[4] if sec else '---'))
    return out

p("="*72)
p("S06-K2 METHOD SET DISCOVERY (from .rdata RTTI, not atlas)")
p("="*72)

for cname, td in [('CellClass',0x81cd70), ('MapClass',0x816bc0)]:
    p(f"\n[{cname}] TD={td:#x} name={read(td+8,20).split(b'\0')[0].decode('latin1')!r}")
    cols = find_cols_for_td(td)
    p(f"  COL bases (u32(COL+0xC)==TD): {[hex(x) for x in cols]}")
    for col in cols:
        vts = find_vtables_for_col(col)
        if not vts: continue
        off = u32(col+4) & 0xffffffff
        p(f"  COL {col:#x} (offset-to-top={off:#x}) -> vtables: {[hex(x) for x in vts]}")
        for vt in vts:
            slots = vt_slots(vt, 40)
            text_idx = [i for i,f,s in slots if s=='.text']
            max_txt = max(text_idx) if text_idx else -1
            p(f"    vtable {vt:#x}: .text slots 0..{max_txt} (count through first non-text)")
            # find terminator: first slot that is not .text starting from 0
            term=None
            for i,f,s in slots:
                if s!='.text':
                    term=(i,f,s); break
            p(f"      first non-text slot: idx={term[0]} val={term[1]:#x} sec={term[2]}")
            p(f"      slots: "+', '.join(f"{i}:{f:#x}" for i,f,s in slots[:36]))

with open(OUT,'w') as f:
    f.write('\n'.join(_lines)+'\n')
p(f"\n[saved] {OUT}")
