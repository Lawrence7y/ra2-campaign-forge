#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S05-K2 T3 targeted: verify specific fields' byte evidence (write+read) in family.
Fields: 0x674 loco, 0x520, 0x6C4, 0x5A4, 0x2B4, 0x140, 0x218, 0x21C, 0x81.
For each: list family writes and reads with disasm bytes, and identify enclosing functions.
"""
import pefile, os, json, bisect, collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM

ROOT=r"D:\Project\ra2-campaign-forge"
P=os.path.join(ROOT,"ra2youli","gamemd.exe")
ATLAS=os.path.join(ROOT,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
SJ=os.path.join(ROOT,"re_atlas","evidence","rtti","symbols.json")
OUTDIR=os.path.join(ROOT,"lead","next_re_20261117_r14","S05-K2"); EVID=os.path.join(OUTDIR,"EVIDENCE")
pe=pefile.PE(P); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.rstrip(b"\0").decode(),s.VirtualAddress+IB,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
SM={s[0]:s for s in SECS}; TEXT=SM[".text"]; DATA=open(P,"rb").read()
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.skipdata=True; MD.detail=True
funcs=[]
with open(ATLAS,encoding="utf-8") as f:
    f.readline()
    for line in f:
        p=line.rstrip("\n").split("\t")
        try: funcs.append((int(p[0],16),int(p[1])))
        except Exception: pass
funcs.sort(); fstart=[e for e,_ in funcs]; fsz={e:sz for e,sz in funcs}
def enclosing(va):
    i=bisect.bisect_right(fstart,va)-1
    if i>=0:
        e=fstart[i]
        if e<=va<e+max(fsz[e],1): return e
    return None
sj=json.load(open(SJ,encoding="utf-8",errors="replace"))
func_class=collections.defaultdict(set)
for nm,c in sj.get("classes",{}).items():
    if nm.startswith("?"): continue
    for vf in c.get("vfuncs",[]):
        try: func_class[int(vf,16)].add(nm)
        except Exception: pass
CTOR={
 'AbstractClass':[0x410170,0x4101C0,0x4101F0,0x4105A0],
 'ObjectClass':[0x5F3900,0x5F3B50,0x5F3B80],
 'TechnoClass':[0x6F2B40,0x6F4300,0x6F4500],
 'FootClass':[0x4D31E0,0x4D3540,0x4D3590],
 'BuildingClass':[0x43B680,0x43B740,0x43BCF0],
 'UnitClass':[0x7353C0,0x735780,0x744470],
 'InfantryClass':[0x517A50,0x517D90,0x521960],
 'AircraftClass':[0x413D20,0x414080,0x41B430],
}
for cls,fl in CTOR.items():
    for f in fl: func_class[f].add(cls)
FAMILY=set(CTOR.keys())|{'MissionClass','RadioClass'}
CTOR_FNSET={x for fl in CTOR.values() for x in fl}
WRITE_MN={'mov','movzx','movsx','add','sub','inc','dec','or','and','xor','adc','sbb',
          'neg','not','shl','shr','sar','imul','sete','setne','setz','setnz','seta','setb','setg','setl'}
TARGET={0x674:'loco ptr',0x520:'?',0x6C4:'?',0x5A4:'?',0x2B4:'?',0x140:'?',0x218:'?',0x21C:'Owner',0x81:'Limbo',0x70C:'?',0x5D4:'?'}
recs={d:[] for d in TARGET}
baseb=DATA[TEXT[3]:TEXT[3]+TEXT[4]]
for ins in MD.disasm(baseb,TEXT[1]):
    try: ops=ins.operands
    except Exception: continue
    if not ops: continue
    mn=ins.mnemonic; f=enclosing(ins.address); cls=sorted(func_class.get(f,set())) if f else []
    for oi,op in enumerate(ops):
        if op.type!=X86_OP_MEM or op.mem.index!=0: continue
        disp=int(op.mem.disp)
        if disp not in recs: continue
        breg=ins.reg_name(op.mem.base) if op.mem.base else None
        write=(oi==0 and mn in WRITE_MN)
        kind=('write' if write else ('vcall' if (mn in('call','jmp') and oi==0) else ('lea' if mn=='lea' else 'read')))
        recs[disp].append({'va':ins.address,'mn':mn,'op':ins.op_str,'bytes':ins.bytes.hex(),'base':breg,
                           'func':f,'classes':cls,'kind':kind,'isfam':bool(FAMILY&set(cls)),'isctor':f in CTOR_FNSET})

out={}
for d,note in TARGET.items():
    R=recs[d]
    fw=[r for r in R if r['kind']=='write' and r['isfam']]
    fr=[r for r in R if r['kind']=='read' and r['base']!='esp' and r['isfam']]
    fc=[r for r in R if r['kind']=='write' and r['isctor']]
    out['0x%X'%d]={
      'note':note,'family_W':len(fw),'family_R':len(fr),'ctor_W':len(fc),
      'ctor_writes':[('%08X'%r['va'],'%08X'%r['func'] if r['func'] else None,r['bytes'],r['op'],r['classes']) for r in fc],
      'family_reads':[('%08X'%r['va'],'%08X'%r['func'] if r['func'] else None,r['bytes'],r['op'],r['classes']) for r in fr[:20]],
      'family_writes':[('%08X'%r['va'],'%08X'%r['func'] if r['func'] else None,r['bytes'],r['op'],r['classes']) for r in fw[:20]],
    }
    print('=== +0x%X %s famW=%d famR=%d ctorW=%d'%(d,note,len(fw),len(fr),len(fc)))
    print('  ctor W:',out['0x%X'%d]['ctor_writes'][:6])
    print('  fam R:',out['0x%X'%d]['family_reads'][:6])
with open(os.path.join(EVID,'t3_targeted_fields.json'),'w',encoding='utf-8') as f:
    json.dump(out,f,indent=1,ensure_ascii=False)
print('WROTE',os.path.join(EVID,'t3_targeted_fields.json'))
