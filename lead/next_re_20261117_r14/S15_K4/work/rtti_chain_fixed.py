#!/usr/bin/env python3
"""S15-K4: corrected static vtable init-chain/RTTI recovery.

Chain per R14_COMMON 8.1 (8): vtable[-1] -> COL; COL+0xC -> TD; TD+8 is INLINE name
(bytes '.?AVClass@@'), NOT a pointer. Fail-closed if any link unreadable.
capstone skipdata=True; no atlas boundary used for RTTI decisions.
"""
from __future__ import annotations
import bisect, collections, csv, pathlib, re, struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM

ROOT=pathlib.Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli/gamemd.exe'
ATLAS=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
OUT=pathlib.Path(__file__).resolve().parents[1]/'EVIDENCE'
TARGETS=['006D0F00','006D6070','006E1830','006E2A10','006E2AA0','006E4790','006E47C0','006E6310','006EA3E0','006F1920','0070F120','0071FA30','00721270','00726910','00727AA0','0072DDB0','0072DEF0','00751590','00752460','00763610','00763690']

pe=pefile.PE(str(EXE)); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append((s.Name.rstrip(b'\0').decode('latin1'),IB+s.VirtualAddress,max(s.Misc_VirtualSize,s.SizeOfRawData)))
def sec(va):
    for n,a,z in secs:
        if a<=va<a+z:return n
    return '?'
def rd(va,n):
    try:return pe.get_data(va-IB,n)
    except Exception:return b''
def u32(va):
    b=rd(va,4);return struct.unpack('<I',b)[0] if len(b)==4 else None

def rtti(vt):
    col=u32(vt-4)
    if col is None or sec(col) not in ('.rdata','.data'):return None
    td=u32(col+0xC)
    if td is None or sec(td) not in ('.rdata','.data'):return None
    b=rd(td+8,160)
    m=re.match(rb'^\.\?AV([A-Za-z0-9_]+)@@',b)
    if not m:return None
    return m.group(1).decode('latin1'),col,td

md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
tsec=[s for s in secs if s[0]=='.text'][0]
code=pe.get_data(tsec[1]-IB,tsec[2])
ins=list(md.disasm(code,tsec[1]))
byaddr={i.address:i for i in ins}
addrs=[i.address for i in ins]

writes=[]
byclass=collections.defaultdict(list)
for i in ins:
    if i.mnemonic!='mov' or len(i.operands)!=2:continue
    op0,op1=i.operands
    if op1.type!=CS_OP_IMM:continue
    vt=op1.imm&0xffffffff
    r=rtti(vt)
    if not r:continue
    cls,col,td=r
    if op0.type==CS_OP_MEM and op0.mem.base==0 and op0.mem.index==0:
        form='ABS'; obj='%08X'%(op0.mem.disp&0xffffffff)
    elif op0.type==CS_OP_MEM:
        form='REG'; obj=i.op_str.split(',')[0]
    else:continue
    rec=(i.address,form,obj,vt,cls,col,td,i.mnemonic+' '+i.op_str,i.bytes.hex())
    writes.append(rec);byclass[cls].append(rec)

def tsv(p):
    with p.open('r',encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
atlas=tsv(ATLAS)
ints=sorted((int(r['entry'],16),int(r['size'],0),r) for r in atlas)
starts=[x[0] for x in ints]
def owner(va):
    k=bisect.bisect_right(starts,va)-1
    if k>=0 and va<ints[k][0]+ints[k][1]:return ints[k]
    return None
cov={r['entry'].upper():r for r in tsv(COV)}
def nm(va):
    r=cov.get('%08X'%(va&0xffffffff))
    return (r['name']+'|'+r['grade']) if r else ''

# callees from a function body (atlas interval only for dump scope; byte evidence independent)
def callees(va,size):
    out=[]
    for i in md.disasm(rd(va,size),va):
        if i.mnemonic in ('call','jmp') and len(i.operands) and i.operands[0].type==CS_OP_IMM:
            out.append((i.address,i.mnemonic,i.operands[0].imm&0xffffffff))
    return out
writes_by_site=collections.defaultdict(list)
for w in writes:writes_by_site[w[0]].append(w)

lines=[]
A=lines.append
A('S15-K4 corrected vtable initialization chain + RTTI recovery')
A('chain: vtable[-1] -> COL; COL+0xC -> TD; TD+8 INLINE name; fail-closed')
A('PE sections: '+'; '.join('%s[%08X,+%X]'%(n,a,z) for n,a,z in secs))
A('.text linear sweep skipdata=True: %d instructions'%len(ins))
A('valid vptr-write sites=%d; distinct classes=%d'%(len(writes),len(byclass)))
A('\n[class histogram: writes]')
for cls,ws in sorted(byclass.items(),key=lambda kv:(-len(kv[1]),kv[0])):
    A('  %-40s %d'%(cls,len(ws)))
A('\n[ALL vptr-write sites with valid RTTI]')
for w in sorted(writes):
    a,form,obj,vt,cls,col,td,txt,byt=w
    ow=owner(a)
    A('  %08X %-3s obj=%-24s vt=%08X COL=%08X TD=%08X cls=%-32s fn=%s bytes=%s txt=%s'%(a,form,obj,vt,col,td,cls,('%08X'%ow[0]) if ow else '<hole>',byt,txt))
A('\n[targets: direct vtable slot hits; callee-installed vptrs; caller-site host classes]')
for t in TARGETS:
    va=int(t,16)
    # scan all loaded data for exact dword slot
    hits=[]
    for sname,sa,sz in secs:
        if sname not in ('.rdata','.data'):continue
        data=rd(sa,sz)
        for off in range(0,len(data)-3,4):
            if struct.unpack_from('<I',data,off)[0]==va:hits.append(sa+off)
    A('\nTARGET %s  coverage=%s  direct vtable-slot dword hits=%d %s'%(t,nm(va),len(hits),' '.join('%08X'%h for h in hits)))
    ow=owner(va)
    size=ow[1] if ow else 0
    for a,m,d in callees(va,size) if size else []:
        ci=[w for w in writes if w[0]==d or (d<=w[0]<d+0x200)]
        A('  callee %08X %s at %08X  name=%s  nearby_vptr_writes=%s'%(d,m,a,nm(d),sorted(set((w[0],w[4]) for w in ci))[:8] or 'NONE'))
    # callers
    idxs=[k for k,i in enumerate(ins) if i.mnemonic in ('call','jmp') and len(i.operands) and i.operands[0].type==CS_OP_IMM and (i.operands[0].imm&0xffffffff)==va]
    A('  direct call/jmp xrefs=%d'%len(idxs))
    for k in idxs:
        i=ins[k];owc=owner(i.address)
        cls=set()
        if owc:
            cs,sz,_=owc
            for w in writes:
                if cs<=w[0]<cs+sz:cls.add(w[4])
        A('    site %08X owner=%s owner_name=%s owner_vptr_classes=%s'%(i.address,('%08X'%owc[0]) if owc else '<hole>',nm(owc[0]) if owc else '',sorted(cls) or 'NONE'))
        for j in ins[max(0,k-8):min(len(ins),k+5)]:
            A('      '+('> ' if j.address==i.address else '  ')+'%08X %-8s %s'%(j.address,j.mnemonic,j.op_str))
(OUT/'vtable_rtti_fixed.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('wrote',OUT/'vtable_rtti_fixed.txt','sites',len(writes),'classes',len(byclass),'lines',len(lines))
print('\n'.join(lines[:12]))
