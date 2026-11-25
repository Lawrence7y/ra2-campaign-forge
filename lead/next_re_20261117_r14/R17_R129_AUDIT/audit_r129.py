#!/usr/bin/env python3
# Independent audit for R129 CLSID chain. No backtick characters in output.
import os, re, struct, hashlib, sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SKIPDATA

EXE = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ra2bench', 'gamemd.exe')
EXE = os.path.abspath(EXE)
IMAGE_BASE = 0x400000
EXPECT_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def i32(b,o): return struct.unpack_from('<i',b,o)[0]
def hex8(x): return '0x%08x' % (x & 0xffffffff)

def section_by_rva(pe,rva):
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s
    return None

def rva_to_off(pe,rva):
    s=section_by_rva(pe,rva)
    if not s: return None
    delta=rva-s.VirtualAddress
    if delta >= s.SizeOfRawData: return None
    return s.PointerToRawData+delta

def va_to_off(pe,va): return rva_to_off(pe,va-IMAGE_BASE)

def read_va(pe,va,n):
    o=va_to_off(pe,va)
    if o is None: return None
    return pe.__data__[o:o+n]

def cstring_at_va(pe,va,maxlen=256):
    d=read_va(pe,va,maxlen)
    if d is None: return None
    z=d.find(b'\0')
    if z<0: z=len(d)
    return d[:z]

def import_by_iat(pe,iat_va):
    for desc in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in desc.imports:
            if imp.address == iat_va:
                return desc.dll.decode(errors='replace'), (imp.name.decode(errors='replace') if imp.name else 'ordinal:%s'%imp.ordinal)
    return None,None

def disasm_range(pe,start_va,end_va):
    # streaming disasm_lite only, skipdata=True
    off=va_to_off(pe,start_va)
    size=end_va-start_va
    data=pe.__data__[off:off+size]
    md=Cs(CS_ARCH_X86,CS_MODE_32)
    md.skipdata=True
    for a,s,m,o in md.disasm_lite(data,start_va):
        yield a,s,m,o

def find_imm_sites(pe,target,section_name='.text'):
    # scan whole named section with disasm_lite streaming; no detail objects
    sec=next(s for s in pe.sections if s.Name.rstrip(b'\0').decode()==section_name)
    data=pe.__data__[sec.PointerToRawData:sec.PointerToRawData+sec.SizeOfRawData]
    md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
    pat='0x%x' % target
    out=[]
    for a,s,m,o in md.disasm_lite(data, IMAGE_BASE+sec.VirtualAddress):
        if re.search(r'(?<![0-9a-fA-F])'+re.escape(pat)+r'(?![0-9a-fA-F])',o):
            out.append((a,m,o))
    return out

def find_raw_pattern(pe,section_name,needle):
    sec=next(s for s in pe.sections if s.Name.rstrip(b'\0').decode()==section_name)
    data=pe.__data__[sec.PointerToRawData:sec.PointerToRawData+sec.SizeOfRawData]
    out=[]; start=0
    while True:
        i=data.find(needle,start)
        if i<0: break
        out.append(IMAGE_BASE+sec.VirtualAddress+i); start=i+1
    return out

# Minimal MSVC RTTI parser: vtable -> COL -> TypeDescriptor -> base classes.
def parse_rtti(pe,vtable_va):
    col_ptr=u32(read_va(pe,vtable_va+4,4),0)  # vtable[-1] at +4? MSVC: vfptr[0]=RTTI COL ptr at vtable-4; vtable layout: [0]=COL ptr, [4]=first method. But many dumps start at vtable base.
    return col_ptr

def describe_col(pe,vtable_va):
    # CDOCOLLECTORCOMPLETEOBJECT layout (x86): pVFTable, spare, name(int), numBases, bases[4]. pTypeDescriptor is at name? Need inspect empirically.
    pass

def main():
    h=hashlib.sha256(open(EXE,'rb').read()).hexdigest()
    print('SHA256',h,'MATCH',h==EXPECT_SHA)
    pe=pefile.PE(EXE,fast_load=False)

    print('\nIMPORTS of interest:')
    for iat in (0x7e15d8,0x7e15d4,0x7e15dc,0x7e15e0):
        dll,name=import_by_iat(pe,iat)
        print(hex8(iat),dll,name)

    print('\nSEG1 disasm 0x6bc410..0x6bc460:')
    for a,s,m,o in disasm_range(pe,0x6bc410,0x6bc460):
        print(hex8(a),('%02x'%0)*0, m, o)

    print('\nSEG4 disasm 0x6bd900..0x6bd960:')
    for a,s,m,o in disasm_range(pe,0x6bd900,0x6bd960):
        print(hex8(a), m, o)

if __name__=='__main__': main()
