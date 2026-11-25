#!/usr/bin/env python3
# R129 auditor: single streaming sweep of .text (disasm_lite, skipdata) collecting
#  - all 'mov dword ptr [abs], imm32' sites (c7 05 form) and their target/imm
#  - imm32 mentions of a watch list
#  - imm32 mentions of 0xa8e8c8 / 0x7e9520 with form classification
# No backticks in output.
import struct, re, json, hashlib
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
IB=0x400000
WATCH=[0x7e9510,0x7e9520,0x7e9530,0x7e9540,0x7e9500,0x7e9720,0x7e99a0,0xa8e8c8,0x7ea564]

def main():
    print('sha256', hashlib.sha256(open(EXE,'rb').read()).hexdigest())
    pe=pefile.PE(EXE,fast_load=False)
    s=[x for x in pe.sections if x.Name.rstrip(b'\0')==b'.text'][0]
    data=pe.__data__[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData]
    base=IB+s.VirtualAddress
    md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
    movabs=[]       # (addr, target, imm, bytes)
    watch_hits={w:[] for w in WATCH}
    total=0; skipped=0
    pat_movabs=re.compile(r'^mov dword ptr \[(0x[0-9a-f]+)\], (0x[0-9a-f]+)$')
    pos=0; consumed_total=0
    CH=0x40000
    while pos < len(data):
        end=min(pos+CH,len(data))
        buf=data[pos:end]
        consumed=0
        for a,sz,m,op in md.disasm_lite(buf,base+pos):
            consumed=(a-(base+pos))+sz
            total+=1
            t=m+' '+op
            if m=='mov':
                mm=pat_movabs.match(t)
                if mm:
                    movabs.append((a,int(mm.group(1),16),int(mm.group(2),16),data[a-base:a-base+sz].hex()))
            low=t.lower()
            for w in WATCH:
                ns='0x%x'%w
                if re.search(r'(?<![0-9a-fA-F])'+re.escape(ns)+r'(?![0-9a-fA-F])',low):
                    watch_hits[w].append((a,m+' '+op,data[a-base:a-base+sz].hex()))
        pos = pos+consumed if consumed else end
    print('decoded instructions in .text:',total)
    print()
    print('=== A) mov dword ptr [abs], imm32  (c7 05 form) total:',len(movabs))
    from collections import Counter
    c=Counter()
    for a,tg,imm,b in movabs:
        in_data = 0x412000 <= (tg-IB) < 0x779be4
        c['target_in_.data' if in_data else 'target_other']+=1
    print('  breakdown:',dict(c))
    vt=[x for x in movabs if 0x7e1000 <= x[2] < 0x812000]
    print('  imm landing in .rdata (vtable-shaped):',len(vt))
    print('  sample of 12 raw movabs sites:')
    for a,tg,imm,b in movabs[:12]:
        print('    0x%08x  [0x%08x]=0x%08x  %s'%(a,tg,imm,b))
    print('  sites writing to 0xa8e8c8:',[('0x%08x'%a,'imm 0x%08x'%imm,'bytes '+b) for a,tg,imm,b in movabs if tg==0xa8e8c8])
    print()
    print('=== B) watch-list imm32 mentions')
    for w in WATCH:
        print('  0x%08x  hits=%d'%(w,len(watch_hits[w])))
        for a,t,b in watch_hits[w]:
            print('     0x%08x  %-16s %s'%(a,b,t))
    json.dump({'movabs':movabs,'watch':{('0x%x'%k):v for k,v in watch_hits.items()}},open('/tmp/r129_sweep.json','w'))

if __name__=='__main__': main()
