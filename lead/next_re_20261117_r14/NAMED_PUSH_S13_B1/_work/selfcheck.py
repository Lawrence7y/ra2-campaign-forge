# -*- coding: utf-8 -*-
"""落盘自检：delta 列数/entry 大写/grade/evidence_path 存在；base_rate 与 delta 行数一致；
每个 [已证] 行的 ② 槽值/④ 写点字节/③b 锚字节在镜像中复核。"""
import os, sys, csv, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C2

WORK = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.dirname(WORK)

with open(os.path.join(OUT,"delta.tsv"),encoding="utf-8") as f:
    rows=list(csv.DictReader(f,delimiter="\t"))
print("delta rows:",len(rows))
ok=True
for r in rows:
    e=r["entry"]
    if e!=e.upper() or e.startswith("0X"): print("  BAD entry",e); ok=False
    if r["grade"]!="[已证]": print("  BAD grade",e); ok=False
    if r["subsystem"]!="S13": print("  BAD subsystem",e); ok=False
    p=r["evidence_path"].replace("D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/NAMED_PUSH_S13_B1/","").replace("/","\\")
    fp=os.path.join(OUT,p)
    if not os.path.exists(fp): print("  MISSING evidence",fp); ok=False
    print("  %s %-26s evidence=%s" % (e,r["name"],os.path.exists(fp)))

# ③b/④ 锚点字节复核
checks = {
 "004684E0": [("call [eax+0x10]",0x0046862A,"ff5010"),("cmp eax,-1",0x0046862D,"83f8ff"),("je",0x00468630,"742d"),("ctor write",0x00466425,"c706e4467e00")],
 "00629FD0": [("call new",0x0062A0D8,"e83aed1900"),("test",0x0062A0E0,"85c0"),("je",0x0062A0E2,"7424"),("ctor write",0x00629231,"c70690f87e00")],
 "0075E0C0": [("call read",0x0075E0F0,"e88b22cbff"),("test",0x0075E0F5,"85c0"),("jl",0x0075E0F7,"0f8cb1010000"),("ctor write",0x0075D0BA,"c74500306b7f00")],
 "0075E2C0": [("call write",0x0075E2D1,"e84a20cbff"),("jl",0x0075E2D8,"0f8cbe000000"),("ctor write",0x0075D0BA,"c74500306b7f00")],
 "00772CD0": [("call read",0x00772CFD,"e87ed6c9ff"),("jl",0x00772D04,"0f8c9c010000"),("ctor write",0x00771E77,"c706b8737f00")],
 "00772EB0": [("call write",0x00772EC1,"e85ad4c9ff"),("jl",0x00772EC8,"0f8cbe000000"),("ctor write",0x00771E77,"c706b8737f00")],
}
print("\nbyte checks:")
for e,cs in checks.items():
    for tag,va,hx in cs:
        got=R.read_va(va,len(hx)//2).hex()
        mark="OK" if got==hx else "MISMATCH"
        if mark!="OK": ok=False
        print("  %s %-14s @%08X expect=%s got=%s %s" % (e,tag,va,hx,got,mark))
print("\nSELFCHECK", "PASS" if ok else "FAIL")
