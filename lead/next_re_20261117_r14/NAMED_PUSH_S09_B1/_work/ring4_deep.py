# -*- coding: utf-8 -*-
"""深度 ④ 见证：用 deep RTTI 解析所有槽，对每个 vtable_base 找 .text 写安装点，
判所在函数与 atexit；输出每行的 ④ 状态。"""
import os, sys, json, struct, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2

WORK=os.path.dirname(os.path.abspath(__file__))
ROWS=json.load(open(os.path.join(WORK,"b1_rows.json"),encoding="utf-8"))

import importlib
rd=importlib.import_module('ring2_deep')

def find_writes(vtable_addr):
    """同 core2.find_vtable_writes，但返回 regdisp + global。"""
    res=[]
    TEXT=R.TEXT_DATA; TVA=R.TEXT_VA
    for off in range(6,len(TEXT)-4):
        imm=struct.unpack_from("<I",TEXT,off)[0]
        if imm!=vtable_addr: continue
        if TEXT[off-6]==0xC7 and TEXT[off-5]==0x05:
            absv=struct.unpack_from("<I",TEXT,off-4)[0]
            res.append({"wa":(TVA+off-6)&0xFFFFFFFF,"global":absv})
        elif TEXT[off-2]==0xC7:
            res.append({"wa":(TVA+off-2)&0xFFFFFFFF,"global":None})
    # dedup by wa
    seen={}
    for x in res: seen[x["wa"]]=x
    return list(seen.values())

ATEXIT=0x7C978A
def is_atexit(func_va, window=0x80):
    needle=b"\x68"+struct.pack("<I",func_va)
    data=R.TEXT_DATA; v0=R.TEXT_VA; st=0
    while True:
        i=data.find(needle,st)
        if i<0: break
        for j in range(i+5,min(i+5+window,len(data)-5)):
            if data[j]==0xE8:
                rel=struct.unpack_from("<i",data,j+1)[0]
                if (v0+j+5+rel)&0xFFFFFFFF==ATEXIT: return True
        st=i+1
    return False

m=re.compile(r"::slot(\d+)$")
out={}
for r in ROWS:
    entry=r["entry"]; ea=int(entry,16)
    clue=None
    mm=m.search(r["name"])
    if mm: clue=int(mm.group(1))
    refs=C2.find_dword_refs(ea)
    slot_info=[]
    for refva,sec in refs:
        dh=rd.resolve_deep(refva)
        for d in dh:
            slotno=d["slot_off"]//4
            vb=d["vtable_base"]
            writes=find_writes(vb)
            wdet=[]
            for w in writes:
                f=C2.find_containing_atlas_func(w["wa"])
                ax=bool(is_atexit(f[0])) if f else False
                wdet.append({"wa":"%08X"%w["wa"],"global":w["global"],
                             "in_func":f[1] if f else None,"atexit":ax})
            slot_info.append({"ref":"%08X"%refva,"vbase":"%08X"%vb,
                              "slotno":slotno,"name":d["rtti_name"],
                              "match": (clue is None or slotno==clue),
                              "writes":wdet,
                              "non_atexit_writes":[w for w in wdet if not w["atexit"]]})
    # ④ OK if any matching slot has a non-atexit write in an in-line func
    r4ok=any(s["match"] and s["non_atexit_writes"] for s in slot_info)
    direct=R and C2.find_direct_calls(ea)
    out[entry]={"name":r["name"],"slots":slot_info,"ring4_ok":r4ok,
                "direct":["%08X"%x for x in direct]}
    print("%s %-40s 4ok=%s slots=%d direct=%d" % (entry,r["name"],r4ok,len(slot_info),len(direct)))
    for s in slot_info:
        if s["match"]:
            print("    matchslot ref=%s vbase=%s slot=%s name=%s writes=%d nonatexit=%d" % (
                s["ref"],s["vbase"],s["slotno"],s["name"],len(s["writes"]),len(s["non_atexit_writes"])))
            for w in s["non_atexit_writes"][:4]:
                print("       w=%s global=%s func=%s" % (w["wa"],w["global"],w["in_func"]))

json.dump(out,open(os.path.join(WORK,"ring4_deep.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("-> ring4_deep.json")
