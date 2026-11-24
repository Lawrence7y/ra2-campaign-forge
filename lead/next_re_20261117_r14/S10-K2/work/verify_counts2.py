import json,sys
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2\work')
from pehelp import rd
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
E=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2\EVIDENCE'
with open(E+r'\t2_mission_slots.json') as f: s=json.load(f)
STUB=set(range(0x5B2E10,0x5B2FC0+1,0x10))
def classify(addr,depth=0):
    if addr in STUB: return 'stub',addr
    if depth>4: return 'impl',addr
    ins=list(md.disasm(rd(addr,16),addr))
    if ins and ins[0].mnemonic=='jmp' and ins[0].operands and ins[0].operands[0].type==X86_OP_IMM:
        return classify(ins[0].operands[0].imm,depth+1)
    return 'impl',addr
total=0; stub=0; nonstub=0; nonstub_addr=set(); jmp_redir=[]
for cls,rows in s.items():
    for r in rows:
        a=int(r['addr'],16); total+=1
        k,tgt=classify(a)
        if k=='stub': stub+=1
        else:
            nonstub+=1; nonstub_addr.add(a)
            if a!=tgt: jmp_redir.append((a,tgt,cls,r['slot']))
print('total slot entries:',total)
print('stub entries (incl jmp->stub):',stub)
print('non-stub entries:',nonstub)
print('distinct non-stub addresses:',len(nonstub_addr))
print('jmp-thunk redirects to impl (a->tgt):',len(jmp_redir))
for a,t,c,sl in jmp_redir: print('  %08X -> %08X  %s v%s'%(a,t,c,sl))
print('\ndistinct non-stub addrs:')
for a in sorted(nonstub_addr): print('  %08X'%a)
