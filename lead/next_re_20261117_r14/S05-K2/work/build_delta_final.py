#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S05-K2 FINAL delta builder: only rows with >=3 thiscall-this-register field accesses.
For each S05 [静态推断] vslot func of the 10 core object classes:
 - prologue mov reg,ecx -> thisreg
 - count proven-field data accesses (vcall/lea/esp excluded) where base==thisreg
 - emit [已证] row if >=3, with byte-proven semantic.
"""
import pefile, os, json, csv, collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM
ROOT=r"D:\Project\ra2-campaign-forge"
P=os.path.join(ROOT,"ra2youli","gamemd.exe")
CA=os.path.join(ROOT,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
COV=os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE","coverage.tsv")
OUTDIR=os.path.join(ROOT,"lead","next_re_20261117_r14","S05-K2"); EVID=os.path.join(OUTDIR,"EVIDENCE")
pe=pefile.PE(P); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.rstrip(b"\0").decode(),s.VirtualAddress+IB,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
SM={s[0]:s for s in SECS}; T=SM[".text"]; D=open(P,"rb").read()
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.skipdata=True; MD.detail=True
funcs={}
with open(CA,encoding="utf-8") as f:
    f.readline()
    for line in f:
        p=line.rstrip("\n").split("\t")
        try: funcs[int(p[0],16)]=int(p[1])
        except Exception: pass
CORE=('AbstractClass','ObjectClass','MissionClass','RadioClass','TechnoClass','FootClass',
      'BuildingClass','UnitClass','InfantryClass','AircraftClass')
PROVEN={0x10:'UniqueID',0x20:'Dirty',0x74:'on-map',0x80:'NeedsRedraw',0x81:'Limbo',0x94:'layer',0x21C:'Owner',0x674:'loco-ptr'}
WRITE_MN={'mov','movzx','movsx','add','sub','inc','dec','or','and','xor','adc','sbb',
          'neg','not','shl','shr','sar','imul','sete','setne','setz','setnz','seta','setb','setg','setl'}
def insns(va,n=260):
    o=T[3]+(va-T[1]); out=[]
    for i in MD.disasm(D[o:o+10000],va):
        out.append(i)
        if len(out)>=n: break
    return out
cands=[]
with open(COV,encoding="utf-8") as f:
    for row in csv.DictReader(f,delimiter="\t"):
        if row['subsystem']=='S05' and row['grade']=='[静态推断]':
            nm=row['name']
            if any(nm.startswith(c+'::') for c in CORE) and ('slot' in nm.lower()):
                try: va=int(row['entry'],16)
                except Exception: continue
                if va in funcs: cands.append((va,nm))
print('candidates:',len(cands))
rows=[]
detail={}
for va,nm in cands:
    ins=insns(va)
    thisreg='ecx'
    for i in ins[:24]:
        try: pop=i.operands
        except Exception: continue
        if i.mnemonic=='mov' and len(pop)==2:
            dst,src=pop[0],pop[1]
            if src.type==1 and i.reg_name(src.reg)=='ecx' and dst.type==1:
                thisreg=i.reg_name(dst.reg); break
    hits=collections.defaultdict(list)
    for i in ins:
        mn=i.mnemonic
        try: ops=i.operands
        except Exception: continue
        for oi,op in enumerate(ops):
            if op.type!=X86_OP_MEM or op.mem.index!=0: continue
            d=int(op.mem.disp)
            if d not in PROVEN: continue
            b=i.reg_name(op.mem.base) if op.mem.base else None
            if b!=thisreg: continue
            if mn in ('call','jmp') and oi==0: continue
            if mn=='lea': continue
            w = (oi==0 and mn in WRITE_MN)
            hits[d].append(('%08X'%i.address, 'W' if w else 'R', mn, i.op_str))
    tot=sum(len(v) for v in hits.values())
    if tot>=3:
        parts=[]
        for d,v in sorted(hits.items(),key=lambda x:-len(x[1])):
            parts.append("0x%X %s x%d"%(d,PROVEN[d],len(v)))
        sem="vtable slot fn (this=%s via mov reg,ecx); byte-proven this-field access: %s; vcall/lea excluded"%(thisreg,', '.join(parts))
        e='%08X'%va
        rows.append([e,'S05',nm,sem,'[已证]',"EVIDENCE/t5_fieldslot_final.json#"+e])
        detail[e]={'name':nm,'thisreg':thisreg,'fields':{('0x%X'%d):{'sem':PROVEN[d],'n':len(v),'accesses':v} for d,v in hits.items()}}
rows.sort()
print('final rows:',len(rows))
for r in rows: print(' ',r[0],r[2],'|',r[3][:100])
with open(os.path.join(EVID,'t5_fieldslot_final.json'),'w',encoding="utf-8") as f:
    json.dump({'method':'S05 static vslot; prologue mov reg,ecx -> thisreg; proven-field accesses base==thisreg; vcall/lea excluded; >=3',
               'detail':detail},f,indent=1,ensure_ascii=False)
with open(os.path.join(OUTDIR,'coverage_delta.tsv'),'w',encoding="utf-8",newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n')
    w.writerow(['entry','subsystem','name','one_line_semantics','grade','evidence_path'])
    w.writerows(rows)
print('WROTE coverage_delta.tsv and EVIDENCE/t5_fieldslot_final.json')
