"""
S10-K2 T4-B: broader scan for the 3 one-sided fields across MissionClass code and
full .text with function-interval attribution. Distinguish byte/dword, skip virtual
call [reg+disp]. Track this-regs. Report ALL candidate hits with owning function.
"""
import os, json, csv
from pehelp import IMAGE_BASE, rd, u32, sections, disasm
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_REG_ECX, X86_REG_ESP, X86_REG_EBP

OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2'
EVID=os.path.join(OUT,'EVIDENCE')
L=[]
def P(s=''):
    s=str(s); L.append(s)
    try: print(s)
    except UnicodeEncodeError: print(s.encode('ascii','replace').decode('ascii'))
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True

# full function table for interval containment
ATL=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
funcs=[]
with open(ATL) as f:
    for r in csv.DictReader(f,delimiter='\t'):
        e=int(r['entry'],16); sz=int(r['size'])
        funcs.append((e,e+sz))
funcs.sort()
import bisect
starts=[a for a,b in funcs]
def owner(addr):
    i=bisect.bisect_right(starts,addr)-1
    if i>=0 and funcs[i][0]<=addr<funcs[i][1]: return funcs[i]
    return None

P('===== FULL MissionClass ctor 0x5B2DA0 disasm =====')
for ins in disasm(0x5B2DA0,0x70):
    P('  %s' % ('%08X  %-20s %-6s %s'%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str)))
    if ins.mnemonic=='ret': break

# target patterns: (disp,width) -> which side we need
# +0xB8 byte READ; +0xCC dword READ; +0x6C dword WRITE
TARGETS={'B8_READ':[], 'CC_READ':[], '6C_WRITE':[]}

tsec=[s for s in sections() if s[0]=='.text'][0]
nm,vaoff,vsize,rsize,praw=tsec
tlo=IMAGE_BASE+vaoff; thi=IMAGE_BASE+vaoff+min(vsize,rsize)

# single disasm pass; for each function window track this-regs
P('\n===== FULL .text SCAN for 3 fields (byte/dword, this-alias regs) =====')
count=0
for (flo,fhi) in funcs:
    if flo<tlo or flo>=thi: continue
    span=min(fhi,thi)-flo
    if span<=0 or span>0x2000: continue
    ins=list(md.disasm(rd(flo,span),flo))
    # this regs: mov r,ecx ; also ecx itself
    tregs={X86_REG_ECX}
    for x in ins:
        if x.id==0 or x.mnemonic.startswith('.'): continue
        if x.mnemonic=='mov' and len(x.operands)==2 and x.operands[0].type==X86_OP_REG and x.operands[1].type==X86_OP_REG:
            if x.operands[1].reg==X86_REG_ECX: tregs.add(x.operands[0].reg)
    for x in ins:
        if x.id==0 or x.mnemonic.startswith('.'): continue  # skipdata pseudo-instruction
        if x.mnemonic in ('call','jmp') and x.operands and x.operands[0].type==X86_OP_MEM: continue
        if not x.operands: continue
        for oi,op in enumerate(x.operands):
            if op.type!=X86_OP_MEM: continue
            m=op.mem
            if m.disp not in (0xB8,0xCC,0x6C): continue
            if m.base in (X86_REG_ESP,X86_REG_EBP): continue
            if m.base not in tregs: continue
            osz=op.size
            # write detection
            is_w = (oi==0 and x.mnemonic in ('mov','add','sub','inc','dec','and','or','xor','movzx','movsx','cmp'))
            # for cmp at op0, it's read really; treat cmp as read
            if x.mnemonic in ('cmp','test'): is_w=False
            key=None
            if m.disp==0xB8 and osz==1 and not is_w: key='B8_READ'
            if m.disp==0xCC and osz==4 and not is_w: key='CC_READ'
            if m.disp==0x6C and osz==4 and is_w: key='6C_WRITE'
            if key:
                TARGETS[key].append((x.address,x.bytes.hex(),x.mnemonic,x.op_str,flo,md.reg_name(m.base)))

for key,hits in TARGETS.items():
    P('\n--- %s : %d hits ---'%(key,len(hits)))
    for a,h,mn,ops,flo,br in hits[:40]:
        P('   %08X %-16s %-6s %-42s fn=%08X base=%s'%(a,h,mn,ops,flo,br))
    if len(hits)>40: P('   ... (%d more)'%(len(hits)-40))

# specifically: is there a MissionClass method that reads +B8 / reads +CC / writes +6C?
MISSION_REGION=(0x5B2D00,0x5B3B00)
P('\n===== hits inside MissionClass code region 0x5B2D00..0x5B3B00 =====')
for key,hits in TARGETS.items():
    inr=[h for h in hits if MISSION_REGION[0]<=h[0]<MISSION_REGION[1]]
    P('  %s: %d'%(key,len(inr)))
    for h in inr: P('     %08X %-6s %s'%(h[0],h[2],h[3]))

with open(os.path.join(EVID,'t4_fields_broad.json'),'w') as f:
    json.dump({k:[[('%08X'%a),h,mn,ops,('%08X'%fl),br] for a,h,mn,ops,fl,br in v] for k,v in TARGETS.items()},f,indent=2)
with open(os.path.join(EVID,'t4_fields_broad.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
print('\nWROTE t4_fields_broad.txt/.json')
