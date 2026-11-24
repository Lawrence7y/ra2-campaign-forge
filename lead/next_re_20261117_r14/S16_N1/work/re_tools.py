# -*- coding: utf-8 -*-
# system python: 3.12 + capstone 5.0.7 + pefile. No venv, no pip.
import sys, os, json, struct, re
import pefile
from capstone import *
from capstone.x86 import *

PE_PATH = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000
pe = pefile.PE(PE_PATH, fast_load=True)
pe.parse_data_directories()
SECTS = []
for s in pe.sections:
    SECTS.append((s.VirtualAddress+IB, s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData, s.Name.decode('utf8','replace').rstrip('\x00')))

def rva2off(rva):
    for va, vs, rs, ptr, nm in SECTS:
        if (va-IB) <= rva < (va-IB)+max(vs,rs): return ptr + (rva-(va-IB))
    raise ValueError('unmapped '+hex(rva))

def read(addr, n):
    o = rva2off(addr-IB)
    with open(PE_PATH,'rb') as f:
        f.seek(o); return f.read(n)

def u32(addr): return struct.unpack('<I', read(addr,4))[0]
def i32(addr): return struct.unpack('<i', read(addr,4))[0]

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
md.detail = True

def disasm(start, size=None, stop_ret=False, maxn=2000):
    if size is None: size=2048
    code = read(start, size)
    out=[]
    for ins in md.disasm(code, start):
        out.append(ins)
        if len(out)>=maxn: break
        if stop_ret and (ins.mnemonic.startswith('ret') or ins.mnemonic=='jmp') and len(out)>0: break
    return out

def fmt(ins):
    return f'{ins.address:08X}  {ins.bytes.hex():<20} {ins.mnemonic:<8} {ins.op_str}'

def scan_imm32(imm, sections=None):
    # find little-endian imm in mapped sections
    pat = struct.pack('<I', imm)
    hits=[]
    for va, vs, rs, ptr, nm in SECTS:
        if sections and nm not in sections: continue
        n=min(vs,rs)
        with open(PE_PATH,'rb') as f:
            f.seek(ptr); data=f.read(n)
        st=0
        while True:
            i=data.find(pat,st)
            if i<0: break
            hits.append((va+i, nm))
            st=i+1
    return hits

def find_calls(target, lo=None, hi=None):
    # find E8 rel32 call sites that resolve to target, scanning .text at every byte (raw) and via instruction boundaries
    ts=[]
    for va,vs,rs,ptr,nm in SECTS:
        if '.text' not in nm: continue
        with open(PE_PATH,'rb') as f: f.seek(ptr); data=f.read(min(vs,rs))
        for i in range(len(data)-4):
            if data[i]==0xE8:
                dest = va+i+5+struct.unpack('<i',data[i+1:i+5])[0]
                if dest==target and (lo is None or lo<=va+i<=hi if hi else lo is None or lo<=va+i):
                    ts.append(va+i)
    return ts

def strings_near(addr, radius=0x200):
    raw = read(max(0x400000,addr-radius), radius*2)
    out=[]
    for m in re.finditer(rb'[ -~]{4,}', raw):
        out.append((addr-radius+m.start(), m.group().decode('ascii','replace')))
    return out

if __name__=='__main__':
    cmd=sys.argv[1] if len(sys.argv)>1 else 'list'
    if cmd=='dis':
        for a in [int(x,16) for x in sys.argv[2:]]:
            print('=== %08X ==='%a)
            for ins in disasm(a, size=0x400, maxn=250):
                print(fmt(ins))
                if ins.mnemonic.startswith('ret'): break
    elif cmd=='sect':
        for s in SECTS: print(s)
    elif cmd=='str':
        a=int(sys.argv[2],16)
        for x in strings_near(a): print('%08X %s'%x)
    elif cmd=='imm':
        a=int(sys.argv[2],16); print('\n'.join('%08X %s'%x for x in scan_imm32(a)))
    elif cmd=='call':
        a=int(sys.argv[2],16); print('\n'.join('%08X'%x for x in find_calls(a)))
