#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T5: AITrigger 评估链每跳的调用点地址 + 判据。
   扫全 .text 的 E8 rel32 直接调用目标 = 链上函数。"""
import sys, os, struct, csv, bisect
sys.path.insert(0, os.path.dirname(__file__))
import wbase as W

CHAIN = {
  0x6F0AB0: "AITrigger eval (EvaluateTriggers?)",
  0x41E720: "ConditionMet",
  0x6F09C0: "TeamTypeClass::CreateTeam",
  0x41F230: "comparator dispatch (ret8)",
  0x578540: "map/team-type check called from AI-wrapper",
}
ATL=[(int(r['entry'],16),int(r['size'])) for r in csv.DictReader(
    open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv',encoding='utf-8'),delimiter='\t')]
ATL.sort(); E=[x[0] for x in ATL]
def host(a):
    i=bisect.bisect_right(E,a)-1
    if i>=0 and ATL[i][0]<=a<ATL[i][0]+ATL[i][1]: return ATL[i][0]
    return None

def scan_e8():
    calls={k:[] for k in CHAIN}
    code=W.DATA[W.TEXT_RAW:W.TEXT_RAW+W.TEXT_RSZ]; base=W.TEXT_VA
    for i in range(len(code)-5):
        if code[i]==0xE8:
            rel=struct.unpack_from("<i",code,i+1)[0]; dst=base+i+5+rel
            if dst in calls:
                calls[dst].append((base+i,host(base+i)))
    return calls

def main():
    c=scan_e8()
    print("=== AITrigger 链调用点 (E8 rel32) ===")
    for va,name in CHAIN.items():
        sites=c[va]
        print(f"\n0x{va:X} {name}: {len(sites)} call sites")
        for s,h in sites:
            print(f"   call @0x{s:X}  host=0x{h:X}" if h else f"   call @0x{s:X}  host=?")
    # 每条跳转的判据: 从调用点上下文取前几条
    print("\n\n=== 关键调用点上下文 ===")
    for va in (0x4F8A6A,):
        print("--- around call site 0x%X ---"%va)
        for a,m,o,ins in W.disasm(va-0x20,0x40,stop_ret=False):
            if ins.id==0 or m.startswith('.'): continue
            print("0x%X %-8s %s"%(a,m,o))

if __name__=="__main__": main()
