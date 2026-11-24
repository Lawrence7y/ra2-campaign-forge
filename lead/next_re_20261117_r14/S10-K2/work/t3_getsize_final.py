"""
S10-K2 T3-final: rigorous GetSize double-point closure.
Point A: v[12] B8 imm32 C3 (slot delimited from .rdata, verified not WhatAmI v[11]).
Point B: factory push <size> -> call operator new (0x7C8E17) -> call <ctor>;
         ctor body contains C7 <install> of that class's off=0 vtable.
Also: confirm 0x7C8E17 is operator new; verify base stub 0x4C9150 excluded.
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

# Confirm operator new 0x7C8E17
P('===== operator new 0x7C8E17 body =====')
for ins in disasm(0x7C8E17,48):
    P('  %s' % ('%08X  %-18s %-6s %s'%(ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str)))
    if ins.mnemonic=='ret': break

with open(os.path.join(EVID,'t3_getsize_raw.json')) as f: t3=json.load(f)
with open(os.path.join(EVID,'t3_getsize_closure.json')) as f: cl=json.load(f)
with open(os.path.join(EVID,'t2_rtti_vtables.json')) as f: rj=json.load(f)
cls_vt={}
for x in rj['kvts']:
    if x['off']==0 and x['name'] not in cls_vt: cls_vt[x['name']]=int(x['vt'],16)

# classes with real GetSize (v[12] B8 imm32 C3, non-stub)
CASES={
 '.?AVAircraftClass@@':0x6D8,
 '.?AVBuildingClass@@':0x720,
 '.?AVInfantryClass@@':0x6F0,
 '.?AVUnitClass@@':0x8E8,
 '.?AVFoggedObjectClass@@':0x78,
}
# from closure json: get push->calls for each size, pick ones whose call target is a ctor
def body_contains_vt_install(ctor, vt, span=0x300):
    b=rd(ctor,span)
    needle=vt.to_bytes(4,'little')
    k=b.find(needle)
    if k<0: return None
    return ctor+k  # address of imm; install insn starts ~2 bytes earlier

P('\n===== RIGOROUS DOUBLE-POINT CLOSURE =====')
P('class | A: v[12] imm | B: push size -> new -> ctor | ctor installs VT? | CLOSED')
closed={}
for cls,size in CASES.items():
    vt=cls_vt[cls]
    installs=[int(a,16) for a in t3['install'][cls]]
    hits=cl.get('%X'%size,[])
    found=[]
    for a,h,calls in hits:
        a=int(a,16)
        for ca_s,ct_s in calls:
            ca=int(ca_s,16); ct=int(ct_s,16)
            if ct!=0x7C8E17: continue
            # operator new call; find next call (ctor) after ca within few insns
            # use closure's second call if present
            idx=calls.index([ca_s,ct_s])
            for c2_s,c3_s in calls[idx+1:]:
                c2=int(c2_s,16); ctor=int(c3_s,16)
                # ctor candidate: body contains vtable install
                loc=body_contains_vt_install(ctor,vt)
                if loc is not None:
                    enc='6A %02X'%size if size<=255 else '68 %02X %02X 00 00'%(size&0xff,(size>>8)&0xff)
                    found.append((a,enc,ca,ctor,loc))
    if found:
        P('  %-32s A=0x%X B=%s | %s | CLOSED=%d' % (cls.replace('.?AV','').replace('@@',''),size,
          ';'.join('push@%08X[%s]->new@%08X->ctor@%08X'%(a,e,ca,ct) for a,e,ca,ct,loc in found[:2]),
          ';'.join('install@%08X'%loc for a,e,ca,ct,loc in found[:2]), len(found)))
        closed[cls]=found
    else:
        P('  %-32s A=0x%X : NO factory closure found' % (cls.replace('.?AV','').replace('@@',''),size))

P('\n===== EXCLUDED (abstract bases, shared stub 0x4C9150) =====')
for cls in ['.?AVMissionClass@@','.?AVObjectClass@@','.?AVTechnoClass@@','.?AVFootClass@@','.?AVAbstractClass@@']:
    vt=cls_vt[cls]
    a12=u32(vt+12*4); a11=u32(vt+11*4)
    P('  %-28s v[11]=%08X v[12]=%08X bytes=%s => NOT real GetSize (shared stub)' %
      (cls.replace('.?AV','').replace('@@',''),a11,a12,rd(a12,3).hex()))

with open(os.path.join(EVID,'t3_getsize_final.json'),'w') as f:
    json.dump({k:[[('%08X'%a),e,('%08X'%ca),('%08X'%ct),('%08X'%loc)] for a,e,ca,ct,loc in v] for k,v in closed.items()}, f, indent=2)
with open(os.path.join(EVID,'t3_getsize_final.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
print('\nWROTE t3_getsize_final.txt/.json')
