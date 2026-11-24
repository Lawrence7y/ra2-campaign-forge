# -*- coding: utf-8 -*-
"""S01-KPROVED ③b/④ candidate analyzer. Reads exe read-only."""
import sys, json, struct, hashlib
import pefile
from capstone import *
from capstone.x86 import *
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
PE=pefile.PE(EXE,fast_load=False); IB=PE.OPTIONAL_HEADER.ImageBase
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True
SECS=[]
for s in PE.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin1')
    SECS.append((nm, s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData))
DATA=PE.__data__
def rva2off(rva):
    for nm,va0,vsize,rsz,rp in SECS:
        if va0<=rva<va0+rsz: return rp+(rva-va0)
    return None
def va2off(va): return rva2off(va-IB)
def readva(va,n):
    o=va2off(va); return DATA[o:o+n] if o is not None else b''
def u32(va):
    b=readva(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
def dis(va,size):
    return list(MD.disasm(readva(va,size),va))

TEXT_VA=0x401000; TEXT_VSZ=0x3DF38D; TEXT_END=TEXT_VA+TEXT_VSZ

def analyze(va,size):
    ins=dis(va,size)
    cond=[]; calls=[]; jmptbl=[]; loops=[]; memwrites=[]; vtwrites=[]; gethandle=[]
    addrs=[i.address for i in ins]
    aset=set(addrs)
    for i in ins:
        m=i.mnemonic; ops=i.op_str
        if m.startswith('j') and m not in ('jmp','jecxz'):
            cond.append((i.address,m,ops))
        if m=='call':
            calls.append((i.address,ops))
        if m=='jmp' and ('*' in ops or ('[' in ops and ('eax' in ops or 'ecx' in ops or 'edx' in ops or 'ebx' in ops or 'esi' in ops or 'edi' in ops))):
            jmptbl.append((i.address,ops,i.bytes.hex()))
        # back edge: jcc/jmp target <= current within body
        if m.startswith('j'):
            try:
                t=int(ops,16)
                if t in aset and t<=i.address: loops.append((i.address,m,t))
            except: pass
        # memory writes (capstone groups)
        if i.operands and (i.operands[0].access==CS_AC_WRITE) and i.operands[0].type==X86_OP_MEM:
            op0=i.operands[0] if i.operands else None
            if op0 and op0.type==X86_OP_MEM:
                memwrites.append((i.address,m,ops))
        if m.startswith('mov') and ops.startswith('dword ptr [') and '0x7' in ops and ('e' in ops):
            # heuristic vt-like write to high rdata address immediate
            if i.operands and i.operands[1].type==X86_OP_IMM and 0x7E1000<=i.operands[1].imm<=0x7E4100:
                vtwrites.append((i.address,m,ops))
    sha=hashlib.sha256(readva(va,size)).hexdigest()[:12].upper()
    return dict(va=va,size=size,nins=len(ins),sha=sha,
                cond=cond,calls=calls,jmptbl=jmptbl,loops=loops,
                memwrite_n=len(memwrites),memwrites=memwrites[:20],
                vtwrites=vtwrites,
                first=ins[0].mnemonic+' '+ins[0].op_str if ins else '',
                last=ins[-1].mnemonic+' '+ins[-1].op_str if ins else '')

if __name__=='__main__':
    cmd=sys.argv[1] if len(sys.argv)>1 else 'one'
    if cmd=='one':
        va=int(sys.argv[2],16); size=int(sys.argv[3],0)
        r=analyze(va,size)
        print(json.dumps(r,ensure_ascii=False,indent=1))
        print('\n--- FULL DISASM ---')
        for i in dis(va,size): print(f'{i.address:08X}  {i.bytes.hex():<20} {i.mnemonic:<8} {i.op_str}')
    elif cmd=='summary':
        # list of candidates from argv: va:size ...
        for a in sys.argv[2:]:
            va,size=a.split(':'); r=analyze(int(va,16),int(size,0))
            print(f"{va} size={r['size']} nins={r['nins']} sha={r['sha']} cond={len(r['cond'])} calls={len(r['calls'])} jmptbl={len(r['jmptbl'])} loops={len(r['loops'])} memwr={r['memwrite_n']} vtwr={len(r['vtwrites'])} first={r['first']!r} last={r['last']!r}")
