import sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2\work')
from pehelp import rd, sections, IMAGE_BASE
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
tsec=[s for s in sections() if s[0]=='.text'][0]
nm,vaoff,vsize,rsize,praw=tsec
tlo=IMAGE_BASE+vaoff; thi=IMAGE_BASE+vaoff+min(vsize,rsize)
blob=rd(tlo,thi-tlo)
ins=list(md.disasm(blob,tlo))
L=[]
def P(s=''):
    L.append(str(s)); print(s)
# instruction-level B8 imm32 (mov eax,imm32) regardless of next insn; and with next=ret
b8=0; b8c3=0; retc=0
for i,x in enumerate(ins):
    if x.id==0 or x.mnemonic.startswith('.'): continue
    if x.mnemonic=='mov' and x.op_str.startswith('eax,') and x.bytes and x.bytes[0]==0xB8:
        b8+=1
        if i+1<len(ins) and ins[i+1].mnemonic=='ret' and ins[i+1].address==x.address+5:
            b8c3+=1
    if x.mnemonic=='ret' and x.op_str.strip()=='0xc':
        retc+=1
P('instruction-level mov eax,imm32 (B8): %d  [STATUS_BOARD loose ~837]'%b8)
P('instruction-level B8 imm32 immediately followed by ret: %d  [STATUS_BOARD strict 666]'%b8c3)
P('instruction-level ret 0xC: %d  [§969: 672]'%retc)
with open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2\EVIDENCE\baselines_insn.txt','w',encoding='utf-8') as f:
    f.write('\n'.join(L)+'\n')
