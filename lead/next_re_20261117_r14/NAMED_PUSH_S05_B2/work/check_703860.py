# -*- coding: utf-8 -*-
"""列出 00703860 的 P1/P2 站点（含被 P3 剔除原因）：确认无 falsifiable 返回约定。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
WORK=os.path.dirname(os.path.abspath(__file__))
ea=0x00703860
size=R.ATLAS.get(R.hx(ea),{}).get("size",686)
insns=R.disasm(ea, R.read_va(ea,size))
idx={i.address:j for j,i in enumerate(insns)}
for i,ins in enumerate(insns):
    if ins.id!=R.X86_INS_CALL: continue
    callee=ins.operands[0].imm & 0xFFFFFFFF if (ins.operands and ins.operands[0].type==R.X86_OP_IMM) else None
    for k in range(i+1,min(i+5,len(insns))):
        tk=R.test_kind(insns[k])
        if not tk: continue
        for m in range(k+1,min(k+3,len(insns))):
            if insns[m].id not in R.JCC_IDS: continue
            tgt=insns[m].operands[0].imm if (insns[m].operands and insns[m].operands[0].type==R.X86_OP_IMM) else None
            ti=idx.get(tgt)
            st=R.path_sig(insns,ti) if ti is not None else {"calls":[],"rets":[],"has_ret":False,"end_eax":"OUT_OF_BODY"}
            sf=R.path_sig(insns,m+1)
            keys=("calls","rets","has_ret","end_eax")
            same=tuple(st[x] for x in keys)==tuple(sf[x] for x in keys)
            fals=(tk[0]=="CMP_IMM" and R.is_falsifiable(tk[1])) or (tk[0] in ("TEST_EAX","OR_EAX") and insns[m].id==R.X86_INS_JE)
            prof=R.callee_return_profile(callee)
            prof_ok=bool(prof and any(R.is_falsifiable(v) for v in prof["consts"]) and len(prof["origins"])>=2)
            print("call=%08X callee=%s test=%s imm=%s jcc=%s->%s same_paths=%s falsy=%s prof_ok=%s prof_consts=%s" % (
                ins.address, R.hx(callee) if callee else "None", tk[0], tk[1], insns[m].mnemonic,
                R.hx(tgt) if tgt else "N/A", same, fals, prof_ok,
                [hex(v) for v in prof["consts"]] if prof else None))
            break
        break
