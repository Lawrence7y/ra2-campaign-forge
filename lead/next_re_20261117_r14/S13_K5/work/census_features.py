from re_core import *
import re
from capstone.x86 import X86_OP_IMM
c=cov_rows(); a=atlas_rows()
rows=[]
for va in s13_set():
    if c[va]['grade']=='[已证]': continue
    n=int(a[va]['size']); b=read(va,min(n,4096)); ins=list(dis(va,min(n,4096)))
    calls=[]
    for i in ins:
        if i.mnemonic=='call' and i.operands and i.operands[0].type==X86_OP_IMM: calls.append(i.operands[0].imm)
    # invoke patterns
    vcall=sum(1 for i in ins if i.mnemonic=='call' and i.operands and i.operands[0].type!=X86_OP_IMM)
    rets=[i.mnemonic for i in ins if i.mnemonic.startswith('ret')]
    # direct pushes of readable cstr in .rdata/.data
    strs=[]
    for i in ins:
        if i.mnemonic=='push' and i.operands and i.operands[0].type==X86_OP_IMM:
            x=i.operands[0].imm
            if 0x7e1000<=x<0xb79be4:
                try:
                    s=cstr(x,48)
                    if len(s)>=2 and all(32<=q<127 for q in s): strs.append((i.address,x,s))
                except: pass
    memimm=[]
    for i in ins:
        if i.mnemonic in ('cmp','mov','test') and len(i.operands)==2 and i.operands[1].type==X86_OP_IMM:
            memimm.append((i.address,i.mnemonic,i.operands[1].imm))
    rows.append((va,c[va]['name'],n,len(ins),len(calls),vcall,calls,rets,strs,memimm[:10],b[:8].hex()))
# emit succinct
for r in rows:
    va,name,n,ni,nc,nv,calls,rets,strs,memimm,head=r
    print(f"{va:08X}\t{name}\tsz={n}\tins={ni}\tdcall={nc}\tvcall={nv}\tret={','.join(rets)}\thead={head}\tstr={';'.join(f'{x:08X}:{s.decode(errors='replace')}' for _,x,s in strs[:4])}")
