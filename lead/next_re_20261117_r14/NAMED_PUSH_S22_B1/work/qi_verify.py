# -*- coding: utf-8 -*-
"""逐工厂验证 ③b②：ctor 装的主 vt 的 slot0=QueryInterface，返回可伪证 HRESULT {0,80004002,80004003}。"""
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

# entry -> (ctor, 主vt写地址, 主vt)  主vt = ctor 内写 [esi]/[eax]/[ecx]+0 的立即数
# 从 probe 结果手工汇总（主 vt 是每 ctor 的第一个 .rdata vt 写，写到 [reg] offset 0）
# 用脚本自动：ctor 内找 mov [reg+0], imm(.rdata vt)
import json
FACT_CTOR = {
 "006BF810":"006BF740","006BF990":"006BF8C0","006BFB10":"006BFA40","006BFC90":"006BFBC0",
 "006BFE10":"006BFD40","006BFF90":"006BFEC0","006C0110":"006C0040","006C0290":"006C01C0",
 "006C0410":"006C0340","006C0590":"006C04C0","006C0710":"006C0640","006C0890":"006C07C0",
 "006C0A10":"006C0940","006C0B90":"006C0AC0","006C0D10":"006C0C40","006C0E90":"006C0DC0",
}
def main_vt(ctor):
    cva=int(ctor,16); sz=R.ATLAS.get(R.hx(cva),{}).get("size") or 64
    for ins in R.disasm_body(cva,sz):
        if ins.id==X86_INS_MOV and len(ins.operands)==2:
            a,b=ins.operands
            if a.type==X86_OP_MEM and b.type==X86_OP_IMM and a.mem.disp==0 and a.mem.scale==1:
                v=b.imm&0xFFFFFFFF
                if 0x7E0000<=v<=0x7F8000:
                    return R.hx(ins.address), R.hx(v), ins.mnemonic+' '+ins.op_str
    return None,None,None

res={}
for e,ctor in FACT_CTOR.items():
    wa,vt,insn=main_vt(ctor)
    qva=R.u32(int(vt,16)) if vt else None
    prof=R.callee_return_profile(qva) if qva else None
    consts=sorted(prof["consts"]) if prof else []
    res[e]={"ctor":ctor,"mainvt_write":wa,"mainvt":vt,"insn":insn,
            "qi":R.hx(qva) if qva else None,
            "qi_consts":[R.hx(c) for c in consts],"qi_nrets":prof["n_rets"] if prof else None,
            "qi_ok": bool(prof and 0 in consts and any(0x80000000<=c<=0x8FFFFFFF for c in consts) and prof["n_rets"]>=2)}
    r=res[e]
    print("%s ctor=%s vt=%s@%s QI=%s consts=%s nrets=%s ok=%s" % (
        e,ctor,vt,wa,r["qi"],r["qi_consts"],r["qi_nrets"],r["qi_ok"]))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"qi_verify.json"),"w",encoding="utf-8") as f:
    json.dump(res,f,ensure_ascii=False,indent=1)
print("\nQI ok count:",sum(1 for x in res.values() if x["qi_ok"]),"/",len(res))
