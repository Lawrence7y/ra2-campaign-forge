# -*- coding: utf-8 -*-
"""抽取每行四环所需精确字节，输出 facts.json 供 EVIDENCE 生成。"""
import os, sys, json, struct, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2

WORK=os.path.dirname(os.path.abspath(__file__))
ROWS=json.load(open(os.path.join(WORK,"b1_rows.json"),encoding="utf-8"))
ANA={a["entry"]:a for a in json.load(open(os.path.join(WORK,"analysis.json"),encoding="utf-8"))}
R4=json.load(open(os.path.join(WORK,"ring4_deep.json"),encoding="utf-8"))

def u32b(va):
    b=C2.va_read(va,4)
    return (b,struct.unpack("<I",b)[0] if len(b)==4 else None)

def resolve_deep(refva,kmax=400):
    for k in range(kmax):
        vb=refva-4*k
        c=C2.u32(vb-4)
        if not c: continue
        ci=C2.parse_col(c)
        if not ci or ci["sig"]!=0: continue
        tdi=C2.parse_td(ci["td"])
        if tdi and tdi["name"] and ".?AV" in tdi["name"]:
            return vb,4*k,ci["col"],tdi["td"],tdi["name"],tdi["name_va"]
    return None

m=re.compile(r"::slot(\d+)$")
facts={}
for r in ROWS:
    entry=r["entry"]; ea=int(entry,16)
    clue=None
    mm=m.search(r["name"])
    if mm: clue=int(mm.group(1))
    a=ANA[entry]
    r1=a["ring1"]
    # ring2: pick the ref whose class name matches clue (or first)
    refs=C2.find_dword_refs(ea)
    slots=[]
    for refva,sec in refs:
        rd=resolve_deep(refva)
        if not rd: continue
        vb,off,col,td,name,nva=rd
        slotval=struct.unpack("<I",C2.va_read(refva,4))[0]
        slots.append({"ref":"%08X"%refva,"sec":sec,"vbase":"%08X"%vb,"off":off,
                      "slotno":off//4,"col":"%08X"%col,"td":"%08X"%td,
                      "name":name,"name_va":"%08X"%nva,
                      "slot_bytes":C2.va_read(refva,4).hex(),"slotval":"%08X"%slotval,
                      "col_bytes":C2.va_read(col,16).hex(),
                      "td_bytes":C2.va_read(td,16).hex(),
                      "name_bytes":C2.va_read(nva,40).hex(),
                      "match": (clue is None or off//4==clue)})
    # ring4: from ring4_deep matching slot first non-atexit write with func
    r4slot=None
    for s in R4[entry]["slots"]:
        if s["match"] and s["non_atexit_writes"]:
            # prefer one with in_func
            wf=[w for w in s["non_atexit_writes"] if w["in_func"]]
            w=(wf[0] if wf else s["non_atexit_writes"][0])
            r4slot={"vbase":s["vbase"],"slotno":s["slotno"],"name":s["name"],
                    "wa":w["wa"],"func":w["in_func"],"global":w["global"],
                    "inst_bytes":C2.va_read(int(w["wa"],16),8).hex()}
            break
    facts[entry]={"name":r["name"],"clue":clue,"r1":r1,
                  "chA":a.get("chA",{}),"chB":a.get("chB",[]),
                  "slots":slots,"r4":r4slot,"direct":R4[entry]["direct"]}
json.dump(facts,open(os.path.join(WORK,"facts.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("facts.json written, rows=",len(facts))
# show ring2 match summary
for e,f in facts.items():
    ms=[s for s in f["slots"] if s["match"]]
    print(e,f["name"][:36],"r2match=%d"%len(ms),"r4=",f["r4"]["wa"] if f["r4"] else None)
