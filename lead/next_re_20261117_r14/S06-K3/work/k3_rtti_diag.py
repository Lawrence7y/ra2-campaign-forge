"""Diagnose RTTI chain layout using known CellClass vtable 0x7E4EEC."""
from lib import *
import struct, re

def cstr(va,maxn=100):
    b=read(va,maxn)
    if not b: return None
    z=b.find(b'\0'); return b[:z if z>=0 else len(b)]

# Method 1: vtable[-1] -> COL ; COL+0xC -> TD ; TD+8 -> name
print("=== method: vtable[-1]=COL, COL+0xC=TD, TD+8=name ===")
for vt in [0x7E4EEC,0x7E4EC0,0x7ED404,0x7F56BC]:
    col=u32(vt-4)
    td=u32(col+0xC) if col and section_of(col) else None
    np=u32(td+8) if td and section_of(td) else None
    nm=cstr(np) if np and section_of(np) else None
    print(f"  vt={vt:#x} col(vt-4)={col and hex(col)} td(col+0xC)={td and hex(td)} np={np and hex(np)} name={nm}")

# Method 2: search all '.?AV' strings in raw file, then find TD pointing to them, then COL pointing to TD
print("\n=== method: scan .?AV strings ===")
allsecs=SECTIONS
hits=[]
for v,vs,raw,rs,name in allsecs:
    data=pe.get_data(raw,rs)
    pos=0
    while True:
        i=data.find(b'.?AV',pos)
        if i<0: break
        hits.append((v+i, data[i:i+80].split(b'\0')[0].decode('latin1','replace')))
        pos=i+1
print(f"total .?AV strings = {len(hits)}")
tib=[(hex(a),s) for a,s in hits if 'Tiber' in s or 'Ore' in s or 'Gem' in s or 'Light' in s or 'Dynamic' in s or 'Vector' in s]
for a,s in sorted(tib,key=lambda x:x[1])[:60]: print(f"  {a}  {s}")
