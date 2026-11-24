#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S05-K2: find S05 [静态推断] vslot functions whose bodies access a PROVEN field.
Proven fields: +0x10/20 (Abstract), +0x74/80/81/94 (Object), +0x21C (Techno), +0x674 (loco).
For each candidate function entry in S05 with grade [静态推断] and name containing slot/vslot,
disassemble its full atlas extent, collect data reads/writes (exclude vcall/lea/esp) at proven fields,
and if >=1 field access with this-like base, emit an upgrade candidate row.
"""
import pefile, os, json, csv, bisect, collections
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM
ROOT=r"D:\Project\ra2-campaign-forge"
P=os.path.join(ROOT,"ra2youli","gamemd.exe")
ATLAS=os.path.join(ROOT,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
COV=os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE","coverage.tsv")
OUTDIR=os.path.join(ROOT,"lead","next_re_20261117_r14","S05-K2"); EVID=os.path.join(OUTDIR,"EVIDENCE")
pe=pefile.PE(P); IB=pe.OPTIONAL_HEADER.ImageBase
SECS=[(s.Name.rstrip(b"\0").decode(),s.VirtualAddress+IB,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
SM={s[0]:s for s in SECS}; TEXT=SM[".text"]; DATA=open(P,"rb").read()
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.skipdata=True; MD.detail=True
funcs={}
with open(ATLAS,encoding="utf-8") as f:
    f.readline()
    for line in f:
        p=line.rstrip("\n").split("\t")
        try: funcs[int(p[0],16)]=int(p[1])
        except Exception: pass
# coverage S05 static vslot funcs
cands=[]
with open(COV,encoding="utf-8") as f:
    for row in csv.DictReader(f,delimiter="\t"):
        if row['subsystem']=='S05' and row['grade']=='[静态推断]':
            nm=row['name']
            if 'slot' in nm.lower() or 'vslot' in nm.lower():
                try: va=int(row['entry'],16)
                except Exception: continue
                if va in funcs: cands.append((va,nm,row['one_line_semantics']))
print('S05 static vslot candidates with atlas size:',len(cands))
PROVEN={0x10:'UniqueID',0x20:'Dirty',0x74:'on-map',0x80:'NeedsRedraw',0x81:'Limbo',0x94:'layer',0x21C:'Owner',0x674:'loco-ptr'}
WRITE_MN={'mov','movzx','movsx','add','sub','inc','dec','or','and','xor','adc','sbb',
          'neg','not','shl','shr','sar','imul','sete','setne','setz','setnz','seta','setb','setg','setl'}
def off(va):
    for n,vb,vs,pr,rs in SECS:
        if vb<=va<vb+max(vs,rs):
            d=va-vb
            if d<rs: return pr+d
    return None
rows=[]
for va,nm,sem in cands:
    sz=funcs[va]; o=off(va)
    if o is None: continue
    b=DATA[o:o+max(sz,1)]
    hits=collections.defaultdict(list)
    for ins in MD.disasm(b,va):
        mn=ins.mnemonic
        for oi,op in enumerate(ins.operands):
            if op.type!=X86_OP_MEM or op.mem.index!=0: continue
            d=int(op.mem.disp)
            if d not in PROVEN: continue
            base=ins.reg_name(op.mem.base) if op.mem.base else None
            if base=='esp': continue
            if mn in ('call','jmp') and oi==0: continue
            if mn=='lea': continue
            write=(oi==0 and mn in WRITE_MN)
            hits[d].append(('%08X'%ins.address, 'W' if write else 'R', ins.mnemonic, ins.op_str))
    if hits:
        rows.append({'entry':'%08X'%va,'name':nm,'old_sem':sem,'size':sz,
                     'fields':{('0x%X'%d):{'sem':PROVEN[d],'n':len(v),'sample':v[:4]} for d,v in sorted(hits.items())}})
rows.sort(key=lambda x:-sum(f['n'] for f in x['fields'].values()))
print('functions with >=1 proven-field access:',len(rows))
for r in rows[:40]:
    fs=', '.join('%s(%s x%d)'%(k,v['sem'],v['n']) for k,v in r['fields'].items())
    print('  %s %-28s %s'%(r['entry'],r['name'][:28],fs))
with open(os.path.join(EVID,'t5_fieldslot_upgrades.json'),'w',encoding='utf-8') as f:
    json.dump({'method':'S05 static vslot funcs; disassemble full atlas extent; count data accesses to proven fields; vcall/lea/esp excluded',
               'n_candidates':len(cands),'n_with_field_access':len(rows),'rows':rows},f,indent=1,ensure_ascii=False)
print('WROTE',os.path.join(EVID,'t5_fieldslot_upgrades.json'))
