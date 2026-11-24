"""Analyze all 74 eligible candidates: ② all holding RTTI tables + ⑯ common-base,
③b feature detection (D-42 S1-S6), ④ direct sites. No atlas dependency for extent.
Outputs work/attrib_all.json, work/features_all.json, work/direct_all.json, EVIDENCE/DISASM_<e>.txt.
"""
import json, csv, os, sys
from pathlib import Path
from collections import Counter
from capstone import CS_ARCH_X86, CS_MODE_32, Cs
from capstone import CS_AC_WRITE
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_GRP_JUMP
sys.path.insert(0, str(Path(__file__).parent))
from s09lib import (rtti_tables, tables_holding, u32, cstr, is_ro, is_text,
                    cfg_extent, decode_range, decode_one, full_e8_sweep,
                    direct_sites_for, TEXT_LO, TEXT_HI)

OUT = Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED5')
WORK, EV = OUT/'work', OUT/'EVIDENCE'
EV.mkdir(exist_ok=True)
eligible = json.load(open(WORK/'s09_A_eligible.json',encoding='utf-8'))

tables = rtti_tables()
print('RTTI tables =', len(tables), ' slots =', sum(len(t['slots']) for t in tables))
# full table dump
with (EV/'VTABLES_ALL.tsv').open('w',encoding='utf-8') as f:
    f.write('vt\tcol\ttd\tname\tnslots\n')
    for t in tables:
        f.write('%08X\t%08X\t%08X\t%s\t%d\n' % (t['vt'],t['col'],t['td'],t['name'],len(t['slots'])))

# class parent map for ⑯ common base
cols=[]
for t in tables:
    cols.append(dict(vt=t['vt'],col=t['col'],td=t['td'],name=t['name']))
parent_map={}
for c in cols:
    if c['td'] in parent_map: continue
    col=c['col']; chd=u32(col+0x10)
    if not chd or not is_ro(chd): continue
    nb=u32(chd+8); pba=u32(chd+0xC)
    if not pba or not is_ro(pba) or nb is None or nb<1: continue
    bcd1=u32(pba+0)
    if not bcd1: continue
    btd=u32(bcd1); bn=cstr(btd+8) if btd else None
    parent_map[c['td']]=(c['name'],bn)
td_by_name={}
for c in cols: td_by_name.setdefault(c['name'],c['td'])
def base_chain(name):
    out=[name]; cur=name; seen={name}
    for _ in range(16):
        td=td_by_name.get(cur)
        if not td: break
        pr=parent_map.get(td)
        if not pr or not pr[1] or pr[1] in seen: break
        cur=pr[1]; out.append(cur); seen.add(cur)
    return out
def common_base(names):
    chains=[base_chain(n) for n in names]
    if not chains: return None
    common=set(chains[0])
    for ch in chains[1:]: common&=set(ch)
    best=None
    for n in chains[0]:
        if n in common: best=n
    return best

# full .text E8 sweep once
insns, calls = full_e8_sweep()
print('.text insns=',len(insns),' E8@boundary=',len(calls))

MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True

def detect_3b(entry, sz):
    if sz<=0 or not is_text(entry): return (False,False,{})
    ins=decode_range(entry, entry+min(sz,4000))
    if not ins: return (False,False,{})
    flags={}; n=len(ins)
    # S1 error-code
    s1=False
    for k,i in enumerate(ins):
        if i.mnemonic=='call':
            for j in range(k+1,min(k+7,n)):
                if ins[j].mnemonic in ('cmp','test'):
                    ims=[o.imm for o in ins[j].operands if o.type==X86_OP_IMM]
                    if -1 in ims or 0xFFFFFFFF in ims:
                        for l in range(j+1,min(j+4,n)):
                            if ins[l].mnemonic.startswith(('set','j')) and ins[l].mnemonic!='jmp':
                                s1=True; break
                    if s1: break
            if s1: break
    flags['S1']=s1
    # S2 loop-IO with explicit non-stack write + boundary + advance
    s2=False; s2_detail=[]
    for k,i in enumerate(ins):
        if i.mnemonic.startswith('j') and i.mnemonic!='jmp':
            ims=[o.imm for o in i.operands if o.type==X86_OP_IMM]
            if ims and entry<=ims[0]<=i.address:
                target=ims[0]
                body=[x for x in ins if target<=x.address<i.address]
                memwr=0; bound=0; adv=0; wr_detail=[]
                for x in body:
                    for o in x.operands:
                        if o.type==X86_OP_MEM and (o.access & CS_AC_WRITE):
                            base=x.reg_name(o.mem.base) if o.mem.base else ''
                            if base not in ('esp','ebp'):
                                memwr+=1; wr_detail.append('%08X:+0x%04X'%(x.address,x.address-entry))
                    if x.mnemonic in ('cmp','test'): bound+=1
                    if x.mnemonic in ('inc','dec','add','sub') and any(o.type==X86_OP_REG for o in x.operands): adv+=1
                if memwr>=1 and bound>=1 and adv>=1:
                    s2=True; s2_detail.append(dict(head='%08X'%target,memwr=memwr,bound=bound,adv=adv,wr=wr_detail[:3]))
    flags['S2']=s2; flags['S2d']=s2_detail
    # S3 jump-table
    s3=False; s3_detail=[]
    for i in ins:
        if i.mnemonic=='jmp':
            for o in i.operands:
                if o.type==X86_OP_MEM and o.mem.scale in (4,8) and o.mem.index!=0:
                    s3=True
                    s3_detail.append('%08X:+0x%04X'%(i.address,i.address-entry))
    flags['S3']=s3; flags['S3d']=s3_detail
    # S4 memory-shape
    vtw=0; offs=set()
    for i in ins:
        if i.mnemonic=='mov':
            ops=i.operands
            if ops and ops[0].type==X86_OP_MEM and (ops[0].access & CS_AC_WRITE):
                base=i.reg_name(ops[0].mem.base) if ops[0].mem.base else ''
                if base and base not in ('esp','ebp'):
                    offs.add(ops[0].mem.disp)
                    if len(ops)>1 and ops[1].type==X86_OP_IMM and is_ro(ops[1].imm): vtw+=1
    s4=(vtw>=2) or (len(offs)>=10)
    flags['S4']=s4; flags['vtw']=vtw; flags['noffs']=len(offs)
    # S6 multi-guard strict (细则#1): >=3 distinct jcc targets + >=2 distinct call targets OR >=2 write offsets
    jcc_targets=set(); wo=set(); dcall=set(); jcc=0
    for i in ins:
        if i.mnemonic.startswith('j') and i.mnemonic!='jmp':
            jcc+=1
            ims=[o.imm for o in i.operands if o.type==X86_OP_IMM]
            if ims: jcc_targets.add(ims[0])
        if i.mnemonic=='call':
            ims=[o.imm for o in i.operands if o.type==X86_OP_IMM]
            if ims: dcall.add(ims[0])
        if i.mnemonic=='mov' and i.operands and i.operands[0].type==X86_OP_MEM and (i.operands[0].access & CS_AC_WRITE):
            base=i.reg_name(i.operands[0].mem.base) if i.operands[0].mem.base else ''
            if base and base not in ('esp','ebp'): wo.add(i.operands[0].mem.disp)
    s6=(len(jcc_targets)>=3 and (len(dcall)>=2 or len(wo)>=2))
    flags['S6']=s6; flags['jtgt']=len(jcc_targets); flags['woff']=len(wo)
    s5=(jcc>=3 and len(dcall)>=1)  # loose
    flags['S5']=s5; flags['jcc']=jcc; flags['dcall']=len(dcall)
    strict = s1 or s2 or s3 or s4 or s6
    loose = strict or s5
    return (strict,loose,flags)

attrib={}; features={}; direct={}
for r in eligible:
    eh=r['entry']; e=int(eh,16)
    hits=tables_holding(tables,e)
    ht=[dict(vt='%08X'%t['vt'],slot=slot,col='%08X'%t['col'],td='%08X'%t['td'],name=t['name']) for t,slot in hits]
    attrib[eh]=dict(hits=ht,n_hits=len(ht))
    st,lo,fl=detect_3b(e,r['size'])
    cb=common_base([h['name'] for h in ht])
    features[eh]=dict(strict=st,loose=lo,flags=fl,common_base=cb,
                      slots=sorted(set(h['slot'] for h in ht)),
                      names=sorted(set(h['name'] for h in ht)),
                      chains={n:base_chain(n) for n in sorted(set(h['name'] for h in ht))})
    lo2,hi2,sites=direct_sites_for(e,calls)
    direct[eh]=dict(lo='%08X'%lo2,hi='%08X'%hi2,sites=sites,
                    n_ok=sum(1 for s in sites if s['ok']),n=len(sites))
    # disassembly with entry-relative offsets (CFG extent)
    _,_,ordered,_=cfg_extent(e)
    dl=[]
    for ins in ordered:
        dl.append('%08X  +0x%04X  %-8s %s'%(ins.address,ins.address-e,ins.mnemonic,ins.op_str))
    (EV/('DISASM_%s.txt'%eh)).write_text('\n'.join(dl),encoding='utf-8')

json.dump(attrib,open(WORK/'attrib_all.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
json.dump(features,open(WORK/'features_all.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
json.dump(direct,open(WORK/'direct_all.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)

# ranking: strong ③b (S2/S3/S1) with all holding tables single-slot consistent + direct ok
print('\n%-8s %-4s %-4s %-5s %-5s %-4s %-6s %-10s %s'%(
    'entry','S1','S2','S3','S4','S6','dirok','common_base','hits'))
for r in eligible:
    eh=r['entry']; f=features[eh]; fl=f['flags']; d=direct[eh]
    strong = 'S2' if fl.get('S2') else ('S3' if fl.get('S3') else ('S1' if fl.get('S1') else ('S6' if fl.get('S6') else ('S4' if fl.get('S4') else '-'))))
    print('%-8s %-4d %-4d %-5d %-5d %-4d %-6s %-10s %s'%(
        eh,fl.get('S1',0),fl.get('S2',0),fl.get('S3',0),fl.get('S4',0),fl.get('S6',0),
        '%d/%d'%(d['n_ok'],d['n']),str(f['common_base'])[:10],strong))
