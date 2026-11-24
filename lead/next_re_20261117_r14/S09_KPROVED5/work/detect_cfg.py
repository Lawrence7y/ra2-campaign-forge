"""Re-run ③b detection using self-written CFG extent (hi-lo) as the decode window,
instead of the possibly-truncated atlas_size. This is the correct discipline.
Also record cfg extent size vs atlas size to detect atlas truncation.
"""
import json, sys
from pathlib import Path
from capstone import CS_ARCH_X86, CS_MODE_32, Cs
from capstone import CS_AC_WRITE
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG
sys.path.insert(0, str(Path(__file__).parent))
from s09lib import cfg_extent, decode_range, u32, is_ro, is_text

OUT = Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED5')
WORK = OUT/'work'
eligible = json.load(open(WORK/'s09_A_eligible.json',encoding='utf-8'))

def detect_3b(entry, ins):
    if not ins: return (False,False,{})
    flags={}; n=len(ins)
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
    s2=False; s2d=[]
    for k,i in enumerate(ins):
        if i.mnemonic.startswith('j') and i.mnemonic!='jmp':
            ims=[o.imm for o in i.operands if o.type==X86_OP_IMM]
            if ims and entry<=ims[0]<=i.address:
                target=ims[0]; body=[x for x in ins if target<=x.address<i.address]
                memwr=0; bound=0; adv=0; wrd=[]
                for x in body:
                    for o in x.operands:
                        if o.type==X86_OP_MEM and (o.access & CS_AC_WRITE):
                            base=x.reg_name(o.mem.base) if o.mem.base else ''
                            if base not in ('esp','ebp'):
                                memwr+=1; wrd.append('+0x%04X:%s'%(x.address-entry,x.mnemonic))
                    if x.mnemonic in ('cmp','test'): bound+=1
                    if x.mnemonic in ('inc','dec','add','sub') and any(o.type==X86_OP_REG for o in x.operands): adv+=1
                if memwr>=1 and bound>=1 and adv>=1:
                    s2=True; s2d.append(dict(head='+0x%04X'%(target-entry),mw=memwr,b=bound,a=adv,wr=wrd[:4]))
    flags['S2']=s2; flags['S2d']=s2d
    s3=False; s3d=[]
    for i in ins:
        if i.mnemonic=='jmp':
            for o in i.operands:
                if o.type==X86_OP_MEM and o.mem.scale in (4,8) and o.mem.index!=0:
                    s3=True; s3d.append('+0x%04X'%(i.address-entry))
    flags['S3']=s3; flags['S3d']=s3d
    vtw=0; offs=set()
    for i in ins:
        if i.mnemonic=='mov' and i.operands and i.operands[0].type==X86_OP_MEM and (i.operands[0].access & CS_AC_WRITE):
            base=i.reg_name(i.operands[0].mem.base) if i.operands[0].mem.base else ''
            if base and base not in ('esp','ebp'):
                offs.add(i.operands[0].mem.disp)
                if len(i.operands)>1 and i.operands[1].type==X86_OP_IMM and is_ro(i.operands[1].imm): vtw+=1
    s4=(vtw>=2) or (len(offs)>=10)
    flags['S4']=s4; flags['vtw']=vtw; flags['noffs']=len(offs)
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
    s5=(jcc>=3 and len(dcall)>=1)
    flags['S5']=s5; flags['jcc']=jcc; flags['dcall']=len(dcall)
    strict=s1 or s2 or s3 or s4 or s6
    loose=strict or s5
    return strict,loose,flags

res={}
for r in eligible:
    eh=r['entry']; e=int(eh,16)
    lo,hi,ins,_=cfg_extent(e)
    st,lo2,fl=detect_3b(e,ins)
    res[eh]=dict(cfg_lo='%08X'%lo,cfg_hi='%08X'%hi,cfg_sz=hi-lo,atlas_sz=r['size'],
                 strict=st,loose=lo2,flags=fl)
json.dump(res,open(WORK/'features_cfg.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('%-8s %7s %7s %-4s %-4s %-4s %-4s %-4s %-4s %-4s %-5s %-5s %s'%(
    'entry','atlas','cfg','S1','S2','S3','S4','S5','S6','strict','jcc','dcall','S2d'))
for eh,f in sorted(res.items()):
    fl=f['flags']
    print('%-8s %7d %7d %-4d %-4d %-4d %-4d %-4d %-4d %-5d %-5d %-5d %s'%(
        eh,f['atlas_sz'],f['cfg_sz'],fl.get('S1',0),fl.get('S2',0),fl.get('S3',0),
        fl.get('S4',0),fl.get('S5',0),fl.get('S6',0),f['strict'],fl.get('jcc',0),
        fl.get('dcall',0), ';'.join(d['head'] for d in fl.get('S2d',[])[:3])))
