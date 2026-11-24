# S13-K9 analyze.py — entries, vtable slots, RTTI, body bytes, 14 entries
import sys, struct
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
from capstone import *

ENTRIES=[0x40B880,0x40B930,0x40F7C0,0x40FD90,0x40FE40,0x46B7E0,0x46B890,0x62B250,0x62B300,0x65C0D0,0x65C180,0x48AD60,0x54E8E0,0x48AD70]

# find all 4-byte little-endian occurrences of entry values in the whole file (mapped sections)
def find_u32_refs(val):
    pat=struct.pack('<I',val)
    out=[]
    for n,v,vs,pr,rs in SECS:
        start=pr; end=pr+min(vs,rs)
        i=DATA.find(pat,start,end)
        while i!=-1:
            out.append((IB+v+(i-pr),n))
            i=DATA.find(pat,i+1,end)
    return out

# RTTI chain: vt-4 = COL ; COL+0xC = TD ; TD+8 inline name
def rtti_chain(vt):
    col=u32(vt-4)
    if col is None: return (col,None,None)
    td=u32(col+0xC)
    if td is None: return (col,td,None)
    b=rd(td+8,80)
    if b is None: return (col,td,None)
    # inline string until NUL
    name=b.split(b'\x00')[0]
    try: s=name.decode('ascii')
    except: s=repr(name)
    return (col,td,s)

def disasm(va,n=96):
    b=rd(va,n)
    if b is None: return []
    md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=False
    return [(i.address,i.mnemonic,i.op_str,i.size,i.bytes.hex()) for i in md.disasm(b,va)]

print('=== .text range',[hex(x) for x in text_range()])
for e in ENTRIES:
    print('\n===== ENTRY',hex(e),'=====')
    b=rd(e,32)
    print('bytes@entry',b.hex() if b else None)
    print('refs',[(hex(a),n) for a,n in find_u32_refs(e)])
    for a,n in find_u32_refs(e):
        if n=='.rdata':
            col,td,name=rtti_chain(a)
            print('  vt',hex(a),'vt-4=COL',hex(col) if col else None,'COL+0xC=TD',hex(td) if td else None,'TD+8 name=',repr(name))
            # dump 8 slots from vt
            slots=[u32(a+4*i) for i in range(8)]
            print('  slots',[hex(x) if x else None for x in slots])
    print('disasm',disasm(e,64))
