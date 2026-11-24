# -*- coding: utf-8 -*-
"""Build a consolidated facts JSON for all 18 rows: RTTI chain, ③ site choice, ④ ctor anchor, verdict.
Each row carries its OWN addresses/bytes (no shared reason)."""
import os, sys, io, json, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import recore as R
import core2 as C2

AN = json.load(open(os.path.join(WORK,"analysis.json"),encoding="utf-8"))
ROWS = json.load(open(os.path.join(WORK,"b1_rows.json"),encoding="utf-8"))

def resolve_slot_ext(refva, maxk=130):
    for k in range(0,maxk):
        vb=refva-4*k; c=C2.u32(vb-4)
        if not c: continue
        ci=C2.parse_col(c)
        if not ci or ci["sig"]!=0: continue
        tdi=C2.parse_td(ci["td"])
        if tdi and tdi["name"] and ".?AV" in tdi["name"]:
            return vb,4*k,ci["col"],tdi["td"],tdi["name_va"],tdi["name"]
    return None

out=[]
for rec,row in zip(AN,ROWS):
    e=rec["entry"]; ea=int(e,16); sn=int(row["name"].rsplit("slot",1)[1])
    refs=C2.find_dword_refs(ea)
    best=None
    for refva,sec in refs:
        r=resolve_slot_ext(refva)
        if r and r[1]//4==sn:
            best=(refva,sec,r); break
    refva,sec,r = best
    vb,off,col,td,Nameva,nm=r
    d={
      "entry":e,"name":row["name"],"subsystem":"S06",
      "r1":{"in_text":rec["ring1"]["in_text"],"atlas_size":rec["ring1"].get("atlas_size"),
            "n":rec["ring1"].get("n_disasm"),"skip":rec["ring1"].get("n_skipdata"),
            "first":rec["ring1"].get("first"),"last":rec["ring1"].get("last")},
      "r2":{"slot_va":"%08X"%refva,"vtable":"%08X"%vb,"slot_off":off,"slot_no":off//4,
            "col":"%08X"%col,"td":"%08X"%td,"name_va":"%08X"%Nameva,"rtti":nm,
            "slot_bytes":R.read_va(refva,4).hex(" "),"slot_val":"%08X"%R.u32(refva)},
      "chA":{"p1":rec["chA"]["p1"],"p2":rec["chA"]["p2"],"p3":rec["chA"]["p3"],
             "sites":[{"call":"%08X"%s["call_addr"],
                       "callee":("%08X"%s["callee"]) if s.get("callee") else None,
                       "test":s["test_kind"],"imm":s.get("test_imm"),
                       "jcc":s["jcc_mnemonic"],
                       "tgt":("%08X"%s["jcc_target"]) if s.get("jcc_target") else None,
                       "form":s.get("p3_form"),"falsy":s.get("call_site_falsy")}
                      for s in rec["chA"]["sites"]]}
    }
    out.append(d)

json.dump(out,open(os.path.join(WORK,"facts.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
for d in out:
    print("%s %-42s slot=%s vt=%s col=%s td=%s name=%s chA=%s/%s/%s"%(
        d["entry"],d["name"],d["r2"]["slot_va"],d["r2"]["vtable"],d["r2"]["col"],d["r2"]["td"],
        d["r2"]["rtti"],d["chA"]["p1"],d["chA"]["p2"],d["chA"]["p3"]))
