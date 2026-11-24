#!/usr/bin/env python3
"""③b analyzer for the 8 entries. Reads EVIDENCE/dis_*.txt, dumps jump tables from raw bytes.
Read-only on target; writes EVIDENCE/analy3b_<entry>.txt
"""
import os, struct, re
import pefile
EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED'
EV = os.path.join(BASE,'EVIDENCE')
ENTRIES=['004AAE90','005BDF70','006A5310','004AB9B0','0063FEA0','006A7780','004ACE70','006ABD30']
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase; D=pe.__data__
SEC=[(s.VirtualAddress,max(s.Misc_VirtualSize,s.SizeOfRawData),s.PointerToRawData) for s in pe.sections]
def va2off(va):
    r=va-IB
    for v,sz,p in SEC:
        if v<=r<v+sz: return p+(r-v)
    return None
def u32(va):
    o=va2off(va)
    return None if o is None or o+4>len(D) else struct.unpack_from('<I',D,o)[0]

# parse disasm lines: addr  bytes  mnemonic  opstr
line_re=re.compile(r'^([0-9A-F]{8})\s+([0-9a-f]+)\s+(\S+)\s*(.*)$')
for e in ENTRIES:
    path=os.path.join(EV,'dis_%s.txt'%e)
    ins=[]
    for ln in open(path,encoding='utf-8'):
        m=line_re.match(ln.rstrip('\n'))
        if m: ins.append((int(m.group(1),16),m.group(2),m.group(3),m.group(4)))
    addrs=[x[0] for x in ins]
    aset=set(addrs)
    bodylo=ins[0][0]; bodyhi=ins[-1][0]
    out=[]
    out.append('=== ③b analysis %s body 0x%08X..0x%08X (%d insns) ==='%(e,bodylo,bodyhi,len(ins)))
    # jump tables
    jt=[x for x in ins if x[2]=='jmp' and 'ptr [' in x[3] and '*4' in x[3]]
    n_jt_all=0; jt_detail=[]
    for a,byt,mn,op in jt:
        mm=re.search(r'\[(?:e[a-z]+)\*4 \+ (0x[0-9a-f]+)\]',op)
        if not mm: 
            out.append('  JT @0x%08X %s (unparsed)'%(a,op)); continue
        tbl=int(mm.group(1),16)
        # determine number of entries by scanning contiguous dwords that land in body
        targets=[]
        for k in range(64):
            v=u32(tbl+k*4)
            if v is None or not (bodylo<=v<=bodyhi): break
            targets.append(v)
        n_jt_all+=1
        out.append('  JT @0x%08X: %s -> table 0x%08X, %d in-body targets: %s'%(
            a,op,tbl,len(targets),','.join('0x%X'%t for t in targets)))
        jt_detail.append((a,tbl,targets))
    out.append('  total jump tables: %d'%n_jt_all)
    # backward branches (loops)
    loops=[]
    for a,byt,mn,op in ins:
        if mn.startswith('j'):
            mm=re.search(r'(0x[0-9a-f]+)',op)
            if mm:
                t=int(mm.group(1),16)
                if t<=a and t in aset:
                    loops.append((a,mn,t))
    out.append('  backward branch edges: %d'%len(loops))
    for a,mn,t in loops[:12]:
        out.append('    @0x%08X %s -> 0x%08X'%(a,mn,t))
    # error-code patterns: mov eax,-1 / or eax,-1 / mov reg,-1 followed by ret/leave
    errs=[]
    for i,(a,byt,mn,op) in enumerate(ins):
        if mn in ('mov','or') and re.match(r'(e?ax|e?bx|e?cx|e?dx), ?-?1$',op):
            errs.append((a,mn,op))
    out.append('  eax/reg=-1 patterns: %d'%len(errs))
    for a,mn,op in errs[:10]:
        out.append('    @0x%08X %s %s'%(a,mn,op))
    # ret count
    rets=[x[0] for x in ins if x[2].startswith('ret')]
    out.append('  ret sites: %d (%s)'%(len(rets),','.join('0x%X'%r for r in rets[:10])))
    open(os.path.join(EV,'analy3b_%s.txt'%e),'w',encoding='utf-8').write('\n'.join(out)+'\n')
    print('\n'.join(out[:6]))
