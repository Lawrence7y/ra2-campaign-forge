#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T2 驱动: TeamClass 字段读写点扫描。"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(__file__))
import wbase as W, fields as F

def atlas_size(entry):
    F.ATLAS if F.ATLAS else F.load_atlas()
    import bisect
    ents=[x[0] for x in F.ATLAS]
    i=bisect.bisect_left(ents,entry)
    if i<len(F.ATLAS) and F.ATLAS[i][0]==entry:
        return F.ATLAS[i][1]
    return 0x200  # 未知函数给保守窗

def vt_methods(vt, n=24):
    ms=[]
    for i in range(n):
        v=W.rd32(vt+i*4)
        if v and W.in_text(v):
            ms.append((v,atlas_size(v)))
    return ms

def main():
    F.ATLAS=F.load_atlas()
    vt=0x7F4730  # TeamClass (RTTI 定类)
    ms=vt_methods(vt,24)
    # 额外: ctor + AI 包装, 去重
    extra=[0x6E8A90,0x6E9050,0x6E9140,0x6F09C0]  # ctor / AI-wrapper / slot23 / CreateTeam
    have={e for e,_ in ms}
    for e in extra:
        if e not in have:
            ms.append((e,atlas_size(e))); have.add(e)
    ms.sort()
    print("TeamClass methods scanned:",len(ms))
    for e,s in ms: print("  0x%X size 0x%X"%(e,s))
    r,w,v=F.main(ms,"TeamClass")
    # 导出 TSV
    out=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S14-K2\EVIDENCE\T2_team_field_access.tsv"
    with open(out,"w",encoding="utf-8") as f:
        f.write("disp\taccess\tentry\tsite\tinsn\tbase_reg\n")
        for disp in sorted(set(r)|set(w)):
            for rec in w.get(disp,[]):
                f.write("0x%X\tW\t0x%X\t0x%X\t%s\t%s\n"%(disp,rec[0],rec[1],rec[2],rec[3]))
            for rec in r.get(disp,[]):
                f.write("0x%X\tR\t0x%X\t0x%X\t%s\t%s\n"%(disp,rec[0],rec[1],rec[2],rec[3]))
    print("wrote",out)

if __name__=="__main__":
    main()
