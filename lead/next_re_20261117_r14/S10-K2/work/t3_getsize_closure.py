"""
S10-K2 T3-B: double-point closure. Find allocation points: push <size>/mov[esp],<size>
feeding operator new, with size == GetSize imm from v[12]. Cross-check ctor install.
capstone skipdata=True.
"""
import os, json
from pehelp import IMAGE_BASE, rd, u32, sections, section_of, is_code, disasm
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2'
EVID=os.path.join(OUT,'EVIDENCE')
L=[]
def P(s=''):
    s=str(s); L.append(s)
    try: print(s)
    except UnicodeEncodeError: print(s.encode('ascii','replace').decode('ascii'))

md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
tsec=[s for s in sections() if s[0]=='.text'][0]
nm,vaoff,vsize,rsize,praw=tsec
tlo=IMAGE_BASE+vaoff; thi=IMAGE_BASE+vaoff+min(vsize,rsize)

# GetSize candidates (from v[12]) and their classes
SIZES={0x6D8:'AircraftClass',0x720:'BuildingClass',0x6F0:'InfantryClass',
       0x8E8:'UnitClass',0x78:'FoggedObjectClass'}
# also 6A imm8 form values that equal size (size<=255): only 0x78 FoggedObject
# ctor install sites from T3
with open(os.path.join(EVID,'t3_getsize_raw.json')) as f: t3=json.load(f)
install={k:[int(a,16) for a in v] for k,v in t3['install'].items()}

# operator new candidates: common ones seen in RA2: 0x7C8E17, 0x7C8E12; find calls frequently right after push size
# We'll record next 'call imm' within 6 insns after each size-push.
P('===== T3-B ALLOCATION POINTS for GetSize immediates =====')
results={}
sizevals=sorted(SIZES)
for size in sizevals:
    needle_imm=size
    hits=[]
    # disassemble whole .text once is expensive but OK (~1.4M insns); do it once below instead
    results[size]=hits

# single pass over .text, capstone skipdata=True
all_ins=list(md.disasm(rd(tlo,thi-tlo),tlo))
P('total .text instructions (skipdata=True) = %d' % len(all_ins))
# index by address for window lookups
for idx,ins in enumerate(all_ins):
    pushed=None; pushaddr=None; enc=None
    if ins.mnemonic=='push' and ins.operands and ins.operands[0].type==X86_OP_IMM:
        v=ins.operands[0].imm & 0xffffffff
        if v in SIZES: pushed=v; pushaddr=ins.address; enc=ins.bytes.hex()
    elif ins.mnemonic=='mov' and len(ins.operands)==2 and ins.operands[0].type==X86_OP_MEM and ins.operands[1].type==X86_OP_IMM:
        if ins.operands[0].mem.base==4 and ins.operands[0].mem.disp==0 and ins.operands[0].mem.index is None:
            v=ins.operands[1].imm & 0xffffffff
            if v in SIZES: pushed=v; pushaddr=ins.address; enc=ins.bytes.hex()
    if pushed is None: continue
    # look ahead up to 8 insns for a call imm
    calls=[]
    for j in range(idx+1,min(idx+9,len(all_ins))):
        x=all_ins[j]
        if x.mnemonic=='call' and x.operands and x.operands[0].type==X86_OP_IMM:
            calls.append((x.address,x.operands[0].imm & 0xffffffff))
        if x.mnemonic in ('ret','jmp'): break
    results[pushed].append((pushaddr,enc,calls[:3]))

for size in sizevals:
    P('\n--- size 0x%X (%s) : %d allocation-form hits ---' % (size,SIZES[size],len(results[size])))
    for a,h,calls in results[size][:20]:
        # check if any call target is a ctor install site region
        cdesc=', '.join('%08X->%08X'%(ca,ct) for ca,ct in calls)
        P('   push@%08X %-14s calls: %s' % (a,h,cdesc))

# Now specifically: for each class, does a push(size)->call land right before its ctor?
P('\n===== T3-B CLOSURE: push(size)->new ... ->ctor(install) chain =====')
for cls in ['.?AVAircraftClass@@','.?AVBuildingClass@@','.?AVInfantryClass@@','.?AVUnitClass@@','.?AVFoggedObjectClass@@']:
    size={'AircraftClass':0x6D8,'BuildingClass':0x720,'InfantryClass':0x6F0,'UnitClass':0x8E8,'FoggedObjectClass':0x78}[cls.replace('.?AV','').replace('@@','')]
    ctors=install.get(cls,[])
    P('  %s size=0x%X ctor-install-sites=%s' % (cls,size,','.join('%08X'%c for c in ctors)))
    for a,h,calls in results[size]:
        for ca,ct in calls:
            # is ct called within +-0x40 of a ctor install site? (allocation block near ctor)
            near=[c for c in ctors if abs(ca-c)<0x200]
            if near:
                P('     ALLOC@%08X -> call %08X  (near ctor install %s) CLOSED' % (a,ct,','.join('%08X'%x for x in near)))

with open(os.path.join(EVID,'t3_getsize_closure.json'),'w') as f:
    json.dump({('%X'%k):[[('%08X'%a),h,[[('%08X'%x),('%08X'%y)] for x,y in c]] for a,h,c in v] for k,v in results.items()},f,indent=2)
with open(os.path.join(EVID,'t3_getsize_closure.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
print('\nWROTE t3_getsize_closure.txt/.json')
