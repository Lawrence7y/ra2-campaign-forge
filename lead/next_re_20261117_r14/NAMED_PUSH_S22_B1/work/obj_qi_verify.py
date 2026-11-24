# -*- coding: utf-8 -*-
"""③b② 正确被调：工厂 Create 体内 call <对象ctor> 创建的对象，其主 vt slot0=QueryInterface。
验证该 QI 返回可伪证 HRESULT {0,80004002,80004003}。"""
import os,sys,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

# entry -> 对象 ctor（probe.py 得到，即工厂 Create 体内除 new 外的直接 call）
OBJ_CTOR = {
 "006BF810":"006D1C20","006BF990":"0047BBF0","006BFB10":"004C5370","006BFC90":"00554830",
 "006BFE10":"006A4550","006BFF90":"007216C0","006C0110":"00727FD0","006C0290":"0046CB60",
 "006C0410":"00435820","006C0590":"00763730","006C0710":"0071A450","006C0890":"0041D300",
 "006C0A10":"006B6EA0","006C0B90":"006AF360","006C0D10":"00471890","006C0E90":"004A7A30",
}
def obj_main_vt(ctor):
    """ctor 内 mov [reg+0], imm(.rdata vt)；取写到 offset0 的第一个，且非 atexit 死表。"""
    cva=int(ctor,16); sz=R.ATLAS.get(R.hx(cva),{}).get("size") or 1024
    cands=[]
    for ins in R.disasm_body(cva,sz):
        if ins.id==X86_INS_MOV and len(ins.operands)==2:
            a,b=ins.operands
            if a.type==X86_OP_MEM and b.type==X86_OP_IMM and a.mem.disp==0 and a.mem.scale==1:
                v=b.imm&0xFFFFFFFF
                if 0x7E0000<=v<=0x7F8000:
                    cands.append((R.hx(ins.address),R.hx(v)))
    return cands

res={}
for e,ctor in OBJ_CTOR.items():
    cands=obj_main_vt(ctor)
    # 取第一个（写到 this+0 的主表）
    wa,vt=cands[0] if cands else (None,None)
    qva=R.u32(int(vt,16)) if vt else None
    prof=R.callee_return_profile(qva) if qva else None
    consts=sorted(prof["consts"]) if prof else []
    ok=bool(prof and 0 in consts and any(0x80000000<=c<=0x8FFFFFFF for c in consts) and prof["n_rets"]>=2)
    res[e]={"obj_ctor":ctor,"mainvt":vt,"write":wa,"n_vt0_writes":len(cands),
            "QI":R.hx(qva) if qva else None,"QI_consts":[R.hx(c) for c in consts],
            "QI_nrets":prof["n_rets"] if prof else None,"QI_ok":ok}
    print("%s objctor=%s mainvt=%s@%s(n=%d) QI=%s consts=%s nret=%s ok=%s"%(
        e,ctor,vt,wa,len(cands),res[e]["QI"],res[e]["QI_consts"],res[e]["QI_nrets"],ok))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"obj_qi_verify.json"),"w",encoding="utf-8") as f:
    json.dump(res,f,ensure_ascii=False,indent=1)
print("\nOK:",sum(1 for x in res.values() if x["QI_ok"]),"/",len(res))
