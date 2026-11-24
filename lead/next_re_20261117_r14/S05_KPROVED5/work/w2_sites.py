# -*- coding: utf-8 -*-
"""w2: ④ direct call 站点验证 —— 全 .text 指令边界 E8 扫（skipdata=True），
site+5+rel32==entry，站点在体外，非自环。双通道：字节命中先验 + 指令边界解码。"""
import os,sys,json,csv,struct
sys.path.insert(0,os.path.dirname(__file__))
import ax_lib
from capstone import *
from capstone.x86 import *

CLS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
ROWS=["005F9720","00709A40","006F3F40","006F6CA0","006F4A70","00711F00","0070E2B0","0040BA50"]
meta={}
for r in csv.DictReader(open(CLS,encoding='utf-8'),delimiter='\t'):
    if r['entry'].upper() in ROWS:
        meta[r['entry'].upper()]=dict(name=r['name'],sites=r['ring4_direct_sites'],
            ext=(int(r['ext_lo'],16),int(r['ext_hi'],16)),ndir=r['n_direct_out'])

pe=ax_lib.load()
tlo,thi=pe.text
off=pe.off(tlo); size=thi-tlo
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True
# 全 .text 线性解码 + 追踪指令边界（skipdata 会把不可解字节当 .byte，仍是边界）
insns=list(MD.disasm(pe.buf[off:off+size],tlo))
call_sites={}   # target -> [site...]
n_e8_bnd=0
for i in insns:
    if i.mnemonic=='call' and i.op_str.startswith('0x'):
        n_e8_bnd+=1
        try: tgt=int(i.op_str,16)
        except: continue
        call_sites.setdefault(tgt,[]).append(i.address)

out={'text_range':['%08X'%tlo,'%08X'%thi],'n_insns':len(insns),'n_call_boundary':n_e8_bnd,'rows':[]}
for e in ROWS:
    ent=int(e,16); lo,hi=meta[e]['ext']
    sites=call_sites.get(ent,[])
    outside=[s for s in sites if not (lo<=s<hi)]
    claimed=meta[e]['sites']
    row=dict(entry=e,name=meta[e]['name'],ext=['%08X'%lo,'%08X'%hi],
             n_sites_all=len(sites),sites=['%08X'%s for s in sites],
             sites_outside=['%08X'%s for s in outside],claimed=claimed)
    out['rows'].append(row)
    print("%s n_call=%d outside=%d sites=%s claimed=%s"%(e,len(sites),len(outside),
        [hex(s) for s in outside][:6],claimed))
json.dump(out,open(os.path.join(os.path.dirname(__file__),'sites.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print("total insns=%d, boundary calls=%d"%(len(insns),n_e8_bnd))
