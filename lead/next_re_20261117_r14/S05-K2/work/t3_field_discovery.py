#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S05-K2 T3: discover fields with double support.
ctor writes [reg+disp] -> field candidate; count family-wide data reads
(vcall excluded, esp-base excluded) at that disp; report fields with ctor-write + family reads >=3.
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
funcs.sort(); fstart=[e for e,_ in funcs]; fsize={e:sz for e,sz in funcs}
def enclosing(va):
    i=bisect.bisect_right(fstart,va)-1
    if i>=0:
        e=fstart[i]
        if e<=va<e+max(fsize[e],1): return e
    return None

sj=json.load(open(SJ,encoding="utf-8",errors="replace"))
func_class=collections.defaultdict(set)
for nm,c in sj.get("classes",{}).items():
    short=nm
    if short.startswith("?"): continue
    for vf in c.get("vfuncs",[]):
        try: func_class[int(vf,16)].add(short)
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
WRITE_MN={'mov','movzx','movsx','add','sub','inc','dec','or','and','xor','adc','sbb',
          'neg','not','shl','shr','sar','imul','sete','setne','setz','setnz','seta','setb','setg','setl'}
PRIORITY={0x674:'loco pointer',0x21C:'Owner HouseClass*',0x81:'Limbo flag',0x10:'UniqueID',
          0x20:'Dirty',0x74:'on-map',0x80:'needsRedraw',0x94:'layer index'}
CTOR_FNSET={x for fl in CTOR.values() for x in fl}

ctor_writes=collections.defaultdict(list)
allacc=collections.defaultdict(list)
baseb=DATA[TEXT[3]:TEXT[3]+TEXT[4]]
n=0
for ins in MD.disasm(baseb,TEXT[1]):
    n+=1
    try: ops=ins.operands
    except Exception: continue
    if not ops: continue
    mn=ins.mnemonic
    f=enclosing(ins.address)
    cls=sorted(func_class.get(f,set())) if f else []
    for oi,op in enumerate(ops):
        if op.type!=X86_OP_MEM: continue
        if op.mem.index!=0: continue
        disp=int(op.mem.disp)
        if disp<0 or disp>0x1000: continue
        breg=ins.reg_name(op.mem.base) if op.mem.base else None
        write=(oi==0 and mn in WRITE_MN)
        rec={'va':ins.address,'mn':mn,'op':ins.op_str,'bytes':ins.bytes.hex(),'base':breg,
             'func':f,'classes':cls,'kind':('write' if write else ('vcall' if (mn in('call','jmp') and oi==0) else ('lea' if mn=='lea' else 'read')))}
        allacc[disp].append(rec)
        if write and f in CTOR_FNSET:
            ctor_writes[disp].append(rec)

print('scanned',n,'disps',len(allacc),'ctor-write disps',len(ctor_writes))

results=[]
for disp,wr in ctor_writes.items():
    wcls=set()
    for r in wr:
        for c in r['classes']: wcls.add(c)
    acc=allacc[disp]
    fam_reads=[r for r in acc if r['kind']=='read' and r['base']!='esp' and (FAMILY & set(r['classes']))]
    fam_vcall=[r for r in acc if r['kind']=='vcall' and (FAMILY & set(r['classes']))]
    all_reads=[r for r in acc if r['kind']=='read' and r['base']!='esp']
    if len(fam_reads)>=3:
        results.append({
            'disp':'0x%X'%disp,'ctor_classes':sorted(wcls),
            'ctor_writes':len(wr),'family_reads':len(fam_reads),'family_vcall_excluded':len(fam_vcall),
            'all_data_reads':len(all_reads),
            'priority_note':PRIORITY.get(disp,''),
            'ctor_write_addrs':[('%08X'%r['va'],'%08X'%r['func'] if r['func'] else None,r['op']) for r in wr[:8]],
            'family_read_sample':[('%08X'%r['va'],'%08X'%r['func'] if r['func'] else None,r['op']) for r in fam_reads[:6]],
        })
results.sort(key=lambda x:(-x['family_reads']))
print('fields with ctor-write + family_reads>=3:',len(results))
for r in results[:45]:
    print('  +%-6s cls=%-24s ctorW=%d famR=%d vcall=%d allR=%d %s'%(
        r['disp'],','.join(r['ctor_classes'])[:24],r['ctor_writes'],r['family_reads'],
        r['family_vcall_excluded'],r['all_data_reads'],r['priority_note']))

with open(os.path.join(EVID,'t3_field_candidates.json'),'w',encoding='utf-8') as f:
    json.dump({'method':'ctor-write + family data-reads(vcall/esp excluded); family=10 core+Mission+Radio',
               'scanned_insns':n,'n_candidates':len(results),'candidates':results},f,indent=1,ensure_ascii=False)
print('WROTE',os.path.join(EVID,'t3_field_candidates.json'))
