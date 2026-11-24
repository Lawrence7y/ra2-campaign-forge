#!/usr/bin/env python3
"""Dump raw byte-chain ② evidence for a given vt/slot/entry. Read-only on target."""
import struct, sys
import pefile
EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
D = pe.__data__
SEC = [(s.VirtualAddress, max(s.Misc_VirtualSize,s.SizeOfRawData), s.PointerToRawData) for s in pe.sections]
def va2off(va):
    rva=va-IB
    for v,sz,p in SEC:
        if v<=rva<v+sz:
            return p+(rva-v)
    return None
def u32(va):
    o=va2off(va)
    return None if o is None or o+4>len(D) else struct.unpack_from('<I',D,o)[0]
def cstr(va,n=100):
    o=va2off(va)
    if o is None: return '<UNMAPPED>'
    e=D.find(b'\x00',o,o+n)
    if e<0: return '<NO-NUL>'
    try: return D[o:e].decode('ascii')
    except: return '<NONASCII:'+repr(D[o:e])+'>'
def dump(vt_hex, slot, entry_hex):
    vt=int(vt_hex,16); slot=int(slot); entry=int(entry_hex,16)
    print(f'vt       = 0x{vt:08X}')
    print(f'vt-4     = 0x{vt-4:08X}  -> dword = 0x{(u32(vt-4) or 0):08X} (COL)')
    col=u32(vt-4)
    print(f'COL      = 0x{(col or 0):08X}')
    print(f'COL+0xC  = 0x{(col or 0)+0xC:08X} -> dword = 0x{(u32(col+0xC) if col else 0) or 0:08X} (TD)')
    td=u32(col+0xC) if col else None
    print(f'TD       = 0x{(td or 0):08X}')
    print(f'TD+8     = 0x{(td or 0)+8:08X} -> cstr = {cstr(td+8) if td else "<NA>"}')
    sv=u32(vt+slot*4)
    print(f'vt+slot*4= 0x{vt+slot*4:08X} (slot {slot}) -> dword = 0x{(sv or 0):08X}')
    print(f'entry    = 0x{entry:08X}   vt[slot]==entry ? {(sv==entry)}')
if __name__=='__main__':
    dump(sys.argv[1], sys.argv[2], sys.argv[3])
