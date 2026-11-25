#!/usr/bin/env python3
# R129 auditor: streaming imm32 cross-reference scan over .text, plus raw byte scan.
# No backticks. disasm_lite only, skipdata=True, chunked to bound memory.
import sys, re, struct, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
IB=0x400000

def load():
    pe=pefile.PE(EXE,fast_load=False)
    return pe

def sections(pe):
    return {s.Name.rstrip(b'\0').decode():s for s in pe.sections}

def raw(pe,name):
    s=sections(pe)[name]
    return s, pe.__data__[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData]

def va2off(pe,va):
    rva=va-IB
    for s in pe.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            if rva-s.VirtualAddress < s.SizeOfRawData:
                return s.PointerToRawData+(rva-s.VirtualAddress)
    return None

def raw_hits(pe,name,val):
    s,data=raw(pe,name)
    pat=struct.pack('<I',val)
    out=[];i=0
    while True:
        i=data.find(pat,i)
        if i<0:break
        out.append(IB+s.VirtualAddress+i); i+=1
    return out

def imm_hits(pe,name,val,chunk=0x40000):
    """Linear-sweep disasm_lite in chunks, keep only instructions whose text mentions val."""
    s,data=raw(pe,name)
    base=IB+s.VirtualAddress
    md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
    needle=('0x%x'%val)
    hits=[]
    pos=0
    total=len(data)
    carry=b''
    # Simple approach: sweep whole section in overlapping windows would break alignment;
    # instead sweep once in slices that end on a decoded boundary.
    while pos<total:
        end=min(pos+chunk,total)
        buf=data[pos:end]
        consumed=0
        for a,sz,m,op in md.disasm_lite(buf,base+pos):
            consumed=(a-(base+pos))+sz
            t=(m+' '+op)
            if re.search(r'(?<![0-9a-fA-F])'+re.escape(needle)+r'(?![0-9a-fA-F])',t):
                hits.append((a,data[(a-base):(a-base)+sz].hex(),t))
        if consumed==0:
            pos=end
        else:
            pos=pos+consumed
    return hits

if __name__=='__main__':
    pe=load()
    print('sha256',hashlib.sha256(open(EXE,'rb').read()).hexdigest())
    for val in [int(x,16) for x in sys.argv[1:]] or [0xa8e8c8,0x7e9520]:
        print('=== value 0x%08x'%val)
        rh=raw_hits(pe,'.text',val)
        print(' raw .text occurrences: %d'%len(rh), ['0x%08x'%x for x in rh])
        ih=imm_hits(pe,'.text',val)
        print(' decoded imm operands: %d'%len(ih))
        for a,b,t in ih:
            print('  0x%08x  %-16s %s'%(a,b,t))
