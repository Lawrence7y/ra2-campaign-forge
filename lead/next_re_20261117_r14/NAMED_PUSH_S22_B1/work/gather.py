# -*- coding: utf-8 -*-
"""最终取证汇总：为 18 行每行生成 verdict JSON（①②③④ 锚点地址+字节），供产物生成。只读目标。"""
import os,sys,json,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

HERE=os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE,"b1_rows.json"),encoding="utf-8") as f: B1=json.load(f)["rows"]
with open(os.path.join(HERE,"analysis.json"),encoding="utf-8") as f: A=json.load(f)
AMAP={x["entry"]:x for x in A}
with open(os.path.join(HERE,"obj_qi_verify.json"),encoding="utf-8") as f: OQV=json.load(f)

FACT_CTOR = {
 "006BF810":"006BF740","006BF990":"006BF8C0","006BFB10":"006BFA40","006BFC90":"006BFBC0",
 "006BFE10":"006BFD40","006BFF90":"006BFEC0","006C0110":"006C0040","006C0290":"006C01C0",
 "006C0410":"006C0340","006C0590":"006C04C0","006C0710":"006C0640","006C0890":"006C07C0",
 "006C0A10":"006C0940","006C0B90":"006C0AC0","006C0D10":"006C0C40","006C0E90":"006C0DC0",
}
# 工厂注册点（call <ctor> 的地址）来自 probe5，和 CLSID 字符串
FACT_REG = {  # entry -> (ctor_call_addr, alloc_push_addr, clsid_str_va, reg_call_addr)
 "006BF810":("006BC5D6","006BC5C6","7E9580","006BC5F0"),
 "006BF990":("006BC613","006BC603","7E9930","006BC62D"),
 "006BFB10":("006BC650","006BC640","7E9940","006BC66A"),
 "006BFC90":("006BC68D","006BC67D","7E98F0","006BC6A7"),
 "006BFE10":("006BC6CA","006BC6BA","7E9910","006BC6E4"),
 "006BFF90":("006BC707","006BC6F7",None,None),
 "006C0110":("006BC744","006BC734",None,None),
 "006C0290":("006BC781","006BC771",None,None),
 "006C0410":("006BC7BE","006BC7AE",None,None),
 "006C0590":("006BC7FB","006BC7EB",None,None),
 "006C0710":("006BC838","006BC828",None,None),
 "006C0890":("006BC875","006BC865",None,None),
 "006C0A10":("006BC8B2","006BC8A2",None,None),
 "006C0B90":("006BC8EF","006BC8DF",None,None),
 "006C0D10":("006BC92C","006BC91C",None,None),
 "006C0E90":("006BC969","006BC959",None,None),
}

def bytes_at(va,n):
    b=R.read_va(va,n)
    return b.hex(" ") if b else ""

def insn_at(va,n=1):
    b=R.read_va(va,16)
    for i in R.disasm(va,b):
        return (i.bytes.hex(" "),i.mnemonic+" "+i.op_str)
    return ("","")

verdicts=[]
for row in B1:
    e=row["entry"]; ea=int(e,16); an=AMAP[e]
    isfac = "TClassFactory" in row["name"]
    v={"entry":e,"name":row["name"],"subsystem":"S22","size":int(row["size"]),"is_factory":isfac}

    # ---- ring1 ----
    r1=an["ring1"]
    v["r1"]={"in_text":r1["in_text"],"atlas_size":r1["atlas_size"],"n_insn":r1["n_insn"],
             "n_skipdata":r1["n_skipdata"],"last":r1["last"],"first_bytes":bytes_at(ea,8)}

    # ---- ring2 ----
    c=an["ring2"]["cands"][0]
    slotva=int(c["slot_va"],16); vt=int(c["vtable_base"],16); off=int(c["slot_off"])
    col=int(c["col"],16); td=int(c["td"],16); nva=int(c["name_va"],16)
    v["r2"]={"slot_va":c["slot_va"],"slot_bytes":bytes_at(slotva,4),
             "vtable":c["vtable_base"],"slot_off":off,"slotno":off//4,
             "clue_slotno":an["ring2"]["slotnum_clue"],"rtti_name":c["rtti_name"],
             "col":c["col"],"col_bytes":bytes_at(col,16),"td":c["td"],"td_bytes":bytes_at(td,16),
             "name_va":c["name_va"],"name_bytes":bytes_at(nva,40)}

    if isfac:
        # ---- ring3b② QI HRESULT branch ----
        # 找工厂体内 call [eax] (slot0 QI) 站点
        ins=list(R.disasm_body(ea,int(row["size"])))
        qi_site=None
        for k,i in enumerate(ins):
            if i.id==X86_INS_CALL and i.operands and i.operands[0].type==X86_OP_MEM \
               and i.operands[0].mem.base==X86_REG_EAX and i.operands[0].mem.disp==0:
                seq=[(R.hx(j.address),j.bytes.hex(" "),j.mnemonic+" "+j.op_str) for j in ins[k:k+8]]
                qi_site={"addr":R.hx(i.address),"bytes":i.bytes.hex(" "),"seq":seq}
                break
        # 释放分支 call [edx+0x20]
        rel=None
        for i in ins:
            if i.id==X86_INS_CALL and i.operands and i.operands[0].type==X86_OP_MEM \
               and i.operands[0].mem.disp==0x20:
                rel={"addr":R.hx(i.address),"bytes":i.bytes.hex(" "),"op":i.op_str}; break
        oq=OQV[e]
        v["r3b"]={"form":"3b2","ok":True,
            "qi_site":qi_site,"release":rel,
            "callee":oq["QI"],"callee_consts":oq["QI_consts"],"callee_nrets":oq["QI_nrets"],
            "created_obj_ctor":oq["obj_ctor"],"obj_mainvt":oq["mainvt"],"obj_vt_write":oq["write"],
            "early_guards":{"E_INVALIDARG":"0x80070057 @+0xA","CLASS_E_NOAGGREGATION":"0x80040110 @+0x23",
                            "E_OUTOFMEMORY":"0x8007000e (new空+ctor空)"}}
        # ---- ring4 factory: 分配+ctor装表+注册 活COM类对象 ----
        ctor=FACT_CTOR[e]; reg=FACT_REG[e]
        cva=int(ctor,16)
        ctor_ins=[(R.hx(i.address),i.bytes.hex(" "),i.mnemonic+" "+i.op_str) for i in R.disasm_body(cva,16)]
        callers=C.find_direct_calls(cva)
        atexit=C.is_atexit_registered(cva)
        v["r4"]={"ok":True,"kind":"live_com_class_object",
            "factory_ctor":ctor,"ctor_ins":ctor_ins,
            "ctor_callers":[R.hx(x) for x in callers],"ctor_atexit":atexit,
            "reg_ctor_call":reg[0],"reg_alloc":reg[1],"clsid":reg[2],"reg_call":reg[3],
            "host_func":"006BB9A0","host_atexit":C.is_atexit_registered(0x6BB9A0),
            "reg_api":"ole32.dll!CoRegisterClassObject (IAT 0x7E15D8, mov esi,[0x7e15d8]@006BC43F; call esi)",
            "reg_args":"push 1; push 1; push <factory_obj>; push <CLSID guid>; call esi",
            "direct_callers_entry":[R.hx(x) for x in C.find_direct_calls(ea)],
            "different_source":True}
    else:
        # Vector slot2: ③ FAIL（malloc空判断/bool返回 模板假句）；④ 不依赖
        ins=list(R.disasm_body(ea,int(row["size"])))
        new_site=None
        for k,i in enumerate(ins):
            if i.id==X86_INS_CALL and i.operands and i.operands[0].type==X86_OP_IMM \
               and (i.operands[0].imm&0xFFFFFFFF)==0x7C8E17:
                new_site={"addr":R.hx(i.address),"bytes":i.bytes.hex(" "),
                          "seq":[(R.hx(j.address),j.bytes.hex(" "),j.mnemonic+" "+j.op_str) for j in ins[k:k+5]]}
                break
        v["r3b"]={"form":"n/a","ok":False,"reason":"operator-new(0x7C8E17) 空判断模板假句 + bool返回(al=0/1)，D-46(A)/模板假句禁","new_site":new_site}
        v["r4"]={"ok":None,"kind":"not_relied","reason":"③不成立，④不作为升级依据；安装点多在含free的清理函数，未取析构锚"}

    v["all_four"]= bool(isfac and v["r3b"]["ok"] and v["r4"]["ok"] and v["r1"]["in_text"])
    verdicts.append(v)

with open(os.path.join(HERE,"verdicts.json"),"w",encoding="utf-8") as f:
    json.dump(verdicts,f,ensure_ascii=False,indent=1)

# 汇总
r2ok=sum(1 for v in verdicts if v["r2"]["rtti_name"])
r3ok=sum(1 for v in verdicts if v["r3b"]["ok"])
r4ok=sum(1 for v in verdicts if v["r4"]["ok"])
allfour=sum(1 for v in verdicts if v["all_four"])
print("rows=%d ring2=%d ring3b=%d ring4=%d allfour=%d"%(len(verdicts),r2ok,r3ok,r4ok,allfour))
for v in verdicts:
    print("  %s %-50s R2=%s R3=%s R4=%s ALL=%s"%(v["entry"],v["name"][:50],
        bool(v["r2"]["rtti_name"]),v["r3b"]["ok"],v["r4"]["ok"],v["all_four"]))
