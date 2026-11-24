#!/usr/bin/env python3
# W155 byte-channel caller search independent of atlas: raw E8 rel32 scan + pointer scan.
import os, struct, pickle, re
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT=r'D:\Project\ra2-campaign-forge'; CARD=os.path.join(ROOT,r'lead\next_re_20261116_r12\W155_dispatch')
EVID=os.path.join(CARD,'EVIDENCE'); EXE=os.path.join(ROOT,'ra2youli','gamemd.exe')
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
sec=next(s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text')
TV=IB+sec.VirtualAddress; RAW=open(EXE,'rb').read()
TSTART,TEND=0x55B8F0,0x55BAA0
with open(os.path.join(CARD,'work','maps.pkl'),'rb') as f: M=pickle.load(f)
insn_start=set(a for lst in M['func_insns'].values() for a,*_ in lst)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True

out=open(os.path.join(EVID,'caller_bytes_raw.txt'),'w',encoding='utf-8')
out.write('=== raw E8 rel32 scan of .text; targets in [0x55B8F0,0x55BAA0) ===\n')
hits=[]
for i in range(sec.SizeOfRawData-5):
    b=RAW[sec.PointerToRawData+i]
    if b!=0xE8: continue
    rel=struct.unpack_from('<i',RAW,sec.PointerToRawData+i+1)[0]
    va=TV+i; tgt=va+5+rel
    if TSTART<=tgt<TEND:
        boundary = va in insn_start
        hits.append((va,tgt,boundary,i))
for va,tgt,bd,off in hits:
    out.write('site=0x%08X target=0x%08X atlas_boundary=%d fileoff=0x%X\n'%(va,tgt,bd,off))
out.write('raw_candidates=%d atlas_confirmed=%d\n'%(len(hits),sum(1 for h in hits if h[2])))
out.write('\n=== exact-entry pointer scan (whole file, LE dword 0x0055B8F0) ===\n')
pat=struct.pack('<I',0x55B8F0); st=0; ptrs=[]
while True:
    i=RAW.find(pat,st)
    if i<0: break
    ptrs.append(i); st=i+1
for i in ptrs[:80]:
    # which section / VA
    va=None
    for s in pe.sections:
        if s.PointerToRawData<=i<s.PointerToRawData+s.SizeOfRawData:
            va=IB+s.VirtualAddress+(i-s.PointerToRawData); break
    out.write('fileoff=0x%X va=%s\n'%(i,('0x%08X'%va) if va else '-'))
out.write('pointer_hits=%d\n'%len(ptrs))
out.write('\n=== pointer scan for 0x0055B960 ===\n')
pat2=struct.pack('<I',0x55B960); st=0; n=0
while True:
    i=RAW.find(pat2,st)
    if i<0: break
    n+=1; st=i+1
out.write('pointer_hits_55B960=%d\n'%n)
out.close()
print('raw E8 candidates',len(hits),'atlas confirmed',sum(1 for h in hits if h[2]),'ptr55B8F0',len(ptrs))
