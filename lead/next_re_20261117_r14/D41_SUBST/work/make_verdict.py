# -*- coding: utf-8 -*-
"""Final per-row verdict with all four rings + exact ④ sites for the 9 selected rows."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from common import find_dword

WORK=os.path.dirname(__file__)
sites=json.load(open(os.path.join(WORK,"final_sites.json"),encoding="utf-8"))
yrpp=json.load(open(os.path.join(WORK,"yrpp_bindings.json"),encoding="utf-8"))

sel=[
 ("007C9442","S02",2,"③b④","+0x00 cmp [esp+4],-0x20/ja; +0x07 alloc; +0x15 cmp[esp+8],eax; +0x1b realloc; +0x27 jne loop",2),
 ("00406130","S19",1,"③b②","+0x02 test [0x87E2A0]->ret0; +0x09 cmp [ecx+C],0x87E294->ret0; +0x12/+0x25 dual cmp; +0x30 clr f_0",1),
 ("00406170","S19",1,"③b②","+0x02 test [0x87E2A0]->ret0; +0x09 cmp [ecx+C],0x87E294->ret0; +0x12 ret Voice",1),
 ("0065CA80","S19",1,"③b③","+0x28 mov [eax],0x7F0904(vt); +0x07..+0x26 10 field writes; +0x2e ret 4 (1 stack arg)",1),
 ("00428B80","S19",2,"③b④","+0x33 count[0x8B4160]; +0x43 read [0x8B4154]+esi*4; +0x47 strcmp 0x7C8D20; +0x51 inc/cmp/jl",2),
 ("00405190","S19",2,"③b④","+0x36 walk [0x87E180] chain; +0x3E test [esi+18]/call 0x407450/write +0x138; +0x41 free 0x7C8B3D; +0x2B cmp/jne",2),
 ("004052F0","S19",2,"③b④","+0x43 count [esi+A8]; +0x4F loop read [edi]->call 0x401F90->write 0->inc ebx->cmp/jl; +0x60 finalize",2),
 ("00401F90","S19",2,"③b②","+0x02 mov eax,[ecx+C]; +0x03 dec; +0x06 test/mov; +0x09 jge; +0x0b clamp [ecx+C]=0 (never negative)",2),
 ("00405BE0","S19",2,"③b③","+0x02 mov [ecx+C],0x87E294 (AudioIndex=&Instance); +0x09/+0x0c/+0x0e zero f_0/f_4/Voice; 4-field shape",2),
]
byent={}
for b in yrpp:
    if b["kind"] in ("CALL","JMP_THIS","THISCALL"):
        byent.setdefault(b["va"],[]).append(b)

out=[]
for e,sub,ch,tier,offnote,_ in sel:
    ss=sites.get(e,[])
    r={"entry":e,"sub":sub,"vaocc":len(find_dword(int(e,16))),"channel":ch,"tier":tier,"offset_evidence":offnote}
    r["direct_sites"]=[s["site"] for s in ss]
    r["proven_callers"]=sorted(set(s["caller"] for s in ss if s["grade"]=="[已证]"))
    if ch==1:
        r["ch1_binding"]=[{"kind":b["kind"],"file":b["file"],"line":b["line"],"text":b["text"]} for b in byent.get(e,[])]
        r["byte_match"]={
          "00406130":["[ecx+0xC]==0x87E294 = AudioIndex==&AudioIDXData::Instance (Audio.h:53/116/123)",
                      "[ecx+0x8]=Voice (Audio.h:115)","[ecx+0x4]=f_4 (Audio.h:114)","[ecx+0x0]=f_0 (Audio.h:113)"],
          "00406170":["[ecx+0xC]==0x87E294 = AudioIndex==&Instance (Audio.h:53/116/123)","[ecx+0x8]=Voice (Audio.h:115)"],
          "0065CA80":["mov [this],0x7F0904 = RawFileClass vfptr (CCFileClass.h:75-100)",
                      "ret 4 = 1 stack arg pFileName (CCFileClass.h:98)","fields +4..+0x20 = FileClass/RawFileClass members (CCFileClass.h:110-114)"],
        }.get(e,[])
        r["ch2_proven_n"]=len(r["proven_callers"])
    else:
        r["ch2_contract"]=[{"caller":s["caller"],"name":s["name"],"site":s["site"],"prev":s["prev"]}
                           for s in ss if s["grade"]=="[已证]"][:3]
    r["four_rings"]={"1_entry":"atlas present","2_identity":"channel %d"%ch,"3_contract":tier,
                     "4_witness":"E8-boundary direct call, non-self, n=%d"%len(r["direct_sites"])}
    out.append(r)

json.dump(out,open(os.path.join(WORK,"final_verdict.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
with open(os.path.join(WORK,"..","EVIDENCE","per_row_verdict.tsv"),"w",encoding="utf-8") as f:
    f.write("entry\tsub\tvaocc\tchannel\ttier\tdirect_n\tproven_caller_n\tch1_binding\tfour_rings\n")
    for r in out:
        b1=";".join("%s:%s:%d"%(x["kind"],x["file"],x["line"]) for x in r.get("ch1_binding",[]))
        f.write("%s\t%s\t%d\t%d\t%s\t%d\t%d\t%s\tYES\n"%(r["entry"],r["sub"],r["vaocc"],r["channel"],r["tier"],
                len(r["direct_sites"]),len(r["proven_callers"]),b1))
for r in out:
    print("%s %s ch%d %s vaocc=%d direct=%d proven=%d"%(r["entry"],r["sub"],r["channel"],r["tier"],r["vaocc"],
        len(r["direct_sites"]),len(r["proven_callers"])))
print("wrote work/final_verdict.json + EVIDENCE/per_row_verdict.tsv")
