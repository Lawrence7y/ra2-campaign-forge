#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S05-K2 T2: family-level attribution + targeted function check for +0x94/+0x10/+0x20.
Family = 10 core classes from S05-K1 (Abstract..Aircraft).
"""
import pefile, os, json, bisect, collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM

ROOT = r"D:\Project\ra2-campaign-forge"
P = os.path.join(ROOT, "ra2youli", "gamemd.exe")
ATLAS = os.path.join(ROOT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
SJ = os.path.join(ROOT, "re_atlas", "evidence", "rtti", "symbols.json")
OUTDIR = os.path.join(ROOT, "lead", "next_re_20261117_r14", "S05-K2")
EVID = os.path.join(OUTDIR, "EVIDENCE")

pe = pefile.PE(P); IB = pe.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in pe.sections:
    SECS.append((s.Name.rstrip(b"\0").decode(), s.VirtualAddress+IB, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
SM={s[0]:s for s in SECS}; TEXT=SM[".text"]
DATA=open(P,"rb").read()
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.skipdata=True; MD.detail=True

funcs=[]
with open(ATLAS,encoding="utf-8") as f:
    f.readline()
    for line in f:
        p=line.rstrip("\n").split("\t")
        try: funcs.append((int(p[0],16),int(p[1])))
        except Exception: pass
funcs.sort(); starts=[e for e,_ in funcs]
def enclosing(va):
    i=bisect.bisect_right(starts,va)-1
    if i>=0:
        e,sz=funcs[i]
        if e<=va<e+max(sz,1): return e
    return None

sj=json.load(open(SJ,encoding="utf-8",errors="replace"))
func_class=collections.defaultdict(set)
for nm,c in sj.get("classes",{}).items():
    short=nm
    if short.startswith("?"): continue
    for vf in c.get("vfuncs",[]):
        try: func_class[int(vf,16)].add(short)
        except Exception: pass
ctor_map={
 0x410170:{'AbstractClass'},0x4101C0:{'AbstractClass'},0x4101F0:{'AbstractClass'},0x4105A0:{'AbstractClass'},
 0x5F3900:{'ObjectClass'},0x5F3B50:{'ObjectClass'},0x5F3B80:{'ObjectClass'},
 0x6F2B40:{'TechnoClass'},0x6F4300:{'TechnoClass'},0x6F4500:{'TechnoClass'},
 0x4D31E0:{'FootClass'},0x4D3540:{'FootClass'},0x4D3590:{'FootClass'},
 0x43B680:{'BuildingClass'},0x43B740:{'BuildingClass'},0x43BCF0:{'BuildingClass'},
 0x7353C0:{'UnitClass'},0x735780:{'UnitClass'},0x744470:{'UnitClass'},
 0x517A50:{'InfantryClass'},0x517D90:{'InfantryClass'},0x521960:{'InfantryClass'},
 0x413D20:{'AircraftClass'},0x414080:{'AircraftClass'},0x41B430:{'AircraftClass'},
}
for f,cs in ctor_map.items(): func_class[f]|=cs

FAMILY={'AbstractClass','ObjectClass','MissionClass','RadioClass','TechnoClass',
        'FootClass','BuildingClass','UnitClass','InfantryClass','AircraftClass'}
WRITE_MN={'mov','movzx','movsx','add','sub','inc','dec','or','and','xor','adc','sbb',
          'neg','not','shl','shr','sar','imul','sete','setne','setz','setnz','seta','setb','setg','setl'}
TARGET=[0x10,0x20,0x74,0x80,0x94,0x21C]
recs={d:[] for d in TARGET}
baseb=DATA[TEXT[3]:TEXT[3]+TEXT[4]]
for ins in MD.disasm(baseb,TEXT[1]):
    try: ops=ins.operands
    except Exception: continue
    if not ops: continue
    mn=ins.mnemonic
    for oi,op in enumerate(ops):
        if op.type!=X86_OP_MEM: continue
        disp=int(op.mem.disp)
        if disp not in recs: continue
        if op.mem.index!=0: continue
        breg=ins.reg_name(op.mem.base) if op.mem.base else None
        f=enclosing(ins.address)
        cls=sorted(func_class.get(f,set())) if f else []
        kind='other'
        if mn in ('call','jmp') and oi==0: kind='vcall'
        elif mn=='lea': kind='lea'
        elif oi==0 and mn in WRITE_MN: kind='write'
        elif breg=='esp': kind='stack_read'
        else: kind='read'
        recs[disp].append({'va':ins.address,'mn':mn,'op':ins.op_str,'bytes':ins.bytes.hex(),
                           'base':breg,'func':f,'classes':cls,'kind':kind,'oi':oi})

out={'family':sorted(FAMILY),'method':'family = 10 core classes; vcall excluded; esp-base excluded from reads','fields':{}}
for d in TARGET:
    R=recs[d]
    def fam(r): return bool(FAMILY & set(r['classes']))
    writes=[r for r in R if r['kind']=='write']
    reads=[r for r in R if r['kind']=='read']
    vcalls=[r for r in R if r['kind']=='vcall']
    fw=[r for r in writes if fam(r)]
    fr=[r for r in reads if fam(r)]
    fv=[r for r in vcalls if fam(r)]
    out['fields']['0x%X'%d]={
        'global_W':len(writes),'global_R_data':len(reads),'global_vcall':len(vcalls),
        'family_W':len(fw),'family_R_data':len(fr),'family_vcall':len(fv),
        'family_W_addrs':[('%08X'%r['va'],'%08X'%r['func'] if r['func'] else None,r['op'],r['classes']) for r in fw],
        'family_R_addrs':[('%08X'%r['va'],'%08X'%r['func'] if r['func'] else None,r['op'],r['classes']) for r in fr[:40]],
        'func_read_hist':collections.Counter(('%08X'%r['func']) if r['func'] else 'None' for r in reads).most_common(15),
    }
    print('+0x%-4X global W=%d R=%d vcall=%d | FAMILY W=%d R=%d vcall=%d'%(
        d,len(writes),len(reads),len(vcalls),len(fw),len(fr),len(fv)))
with open(os.path.join(EVID,'t2_family_attrib.json'),'w',encoding='utf-8') as f:
    json.dump(out,f,indent=1,ensure_ascii=False)
print('WROTE',os.path.join(EVID,'t2_family_attrib.json'))

# targeted: explicit functions
print('\n--- targeted function check +0x94 / +0x10 / +0x20 ---')
for target_fn in [0x4A9720,0x4A9770,0x4A9710,0x4A9720,0x410410,0x4101F0]:
    hits=[r for d in [0x10,0x20,0x94] for r in recs[d] if r['func']==target_fn]
    if hits:
        print('%08X:'%target_fn, [(('0x%X'%h['va']),h['mn'],h['op'],h['kind']) for h in hits])
