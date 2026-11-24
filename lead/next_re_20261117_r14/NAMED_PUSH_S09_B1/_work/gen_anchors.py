# -*- coding: utf-8 -*-
"""抽取所有行的精确字节锚点，输出 anchors.json。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2
WORK=os.path.dirname(os.path.abspath(__file__))
F=json.load(open(os.path.join(WORK,"facts.json"),encoding="utf-8"))
A={a["entry"]:a for a in json.load(open(os.path.join(WORK,"analysis.json"),encoding="utf-8"))}

def hxbytes(va,n): return C2.va_read(va,n).hex(' ')  # lowercase spaced

out={}
for e,f in F.items():
    rec={"name":f["name"],"r1":f["r1"]}
    # ring2 primary matching slot
    ms=[s for s in f["slots"] if s["match"]]
    if ms:
        s=ms[0]
        ref=int(s["ref"],16)
        slot_bytes=C2.va_read(ref,4).hex(' ')
        col=int(s["col"],16); td=int(s["td"],16); nva=int(s["name_va"],16)
        rec["r2"]={"ref":s["ref"],"slot_bytes":slot_bytes,"slotval":s["slotval"],
                   "vbase":s["vbase"],"off":s["off"],"slotno":s["slotno"],
                   "col":s["col"],"col_sig_bytes":C2.va_read(col,16).hex(' '),
                   "td":s["td"],"td_bytes":C2.va_read(td,16).hex(' '),
                   "name_va":s["name_va"],"name":s["name"],
                   "name_bytes":C2.va_read(nva,40).hex(' '),
                   "n_match":len(ms)}
    # ring4 primary install
    if f["r4"]:
        wa=int(f["r4"]["wa"],16)
        rec["r4"]={"wa":f["r4"]["wa"],
                   "inst_bytes":C2.va_read(wa,8).hex(' '),
                   "func":f["r4"]["func"]}
        if f["r4"]["func"]:
            fa=int(f["r4"]["func"],16)
            # find base ctor call in func window
            sz=R.ATLAS.get(R.hx(fa),{}).get('size') or 96
            calls=[]
            for i in R.disasm(fa,R.read_va(fa,sz)):
                if i.id==0xCD and False: pass
                if i.mnemonic=='call' and i.op_str.startswith('0x'):
                    calls.append("%08X"%i.address+":"+i.op_str)
            rec["r4"]["func_calls"]=calls[:5]
    # chA sites with byte anchors
    sites=[]
    for s in A[e].get("chA",{}).get("sites",[]):
        ca=s["call_addr"]; ta=s["test_addr"]; ja=s["jcc_addr"]
        sites.append({"call":"%08X"%ca,"call_bytes":C2.va_read(ca,5).hex(' '),
                      "callee":("%08X"%s["callee"]) if s["callee"] else None,
                      "test":"%08X"%ta,"test_bytes":C2.va_read(ta,4).hex(' '),
                      "jcc":"%08X"%ja,"jcc_mn":s["jcc_mnemonic"],
                      "jcc_bytes":C2.va_read(ja,6).hex(' '),
                      "jcc_tgt":("%08X"%s["jcc_target"]) if s.get("jcc_target") is not None else None,
                      "form":s["p3_form"],"falsy":s["call_site_falsy"],
                      "prof_consts":s["callee_profile"].get("all_consts")})
    rec["sites"]=sites
    rec["chA_p1p2p3"]=[A[e].get("chA",{}).get("p1"),A[e].get("chA",{}).get("p2"),A[e].get("chA",{}).get("p3")]
    out[e]=rec
json.dump(out,open(os.path.join(WORK,"anchors.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("anchors.json written")
print(json.dumps(out["004F45B0"],ensure_ascii=False,indent=1)[:2500])
