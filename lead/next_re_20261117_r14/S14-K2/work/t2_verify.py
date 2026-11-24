#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T2 收尾: (1) 全虚调用 call [reg+disp] 剔除计数; (2) 关键字段的具体读写指令逐字符。"""
import sys, os, csv, struct
sys.path.insert(0, os.path.dirname(__file__))
import wbase as W
from capstone.x86 import X86_OP_REG, X86_OP_MEM, X86_OP_IMM

def count_vcalls(methods):
    """扫所有方法内 call/jmp [reg+disp] (虚调用) 计数, 显式报剔除数"""
    total=0; bydisp={}
    for entry,size in methods:
        for a,m,o,insn in W.disasm(entry,size,stop_ret=False):
            if m not in ("call","jmp"): continue
            for op in insn.operands:
                if op.type==X86_OP_MEM and op.mem.base and op.mem.index==0:
                    total+=1
                    bydisp[op.mem.disp]=bydisp.get(op.mem.disp,0)+1
    return total,bydisp

def dump_site(va, n=24):
    out=[]
    for a,m,o,insn in W.disasm(va,n,stop_ret=False):
        out.append("0x%08X  %-18s %-6s %s"%(a,W.bytes_at(a,insn.size).hex(),m,o))
    return "\n".join(out)

def main():
    # TeamClass 方法集 (同 t2_team)
    import fields as F
    F.ATLAS=F.load_atlas()
    import t2_team as T
    vt=0x7F4730
    ms=T.vt_methods(vt,24)
    have={e for e,_ in ms}
    for e in [0x6E8A90,0x6E9050,0x6E9140]:
        if e not in have: ms.append((e,T.atlas_size(e))); have.add(e)
    ms.sort()
    total,bydisp=count_vcalls(ms)
    print("=== TeamClass 方法内 call/jmp [reg+disp] 虚调用剔除 ===")
    print("total:",total)
    print("by disp:",dict(sorted(bydisp.items())))

    print("\n\n=== 关键字段: 写点/读点逐字符 ===")
    SITES = {
      "+0x24 TeamType* (W ctor / R AI)": [0x6E8AA7,0x6EAEB4,0x6E8CF9],
      "+0x28 ScriptClass* (W ctor / R slot23)": [0x6E8AAA,0x6E8DBB,0x6E91ED],
      "+0x2C HouseClass* (W ctor / R slot23)": [0x6E8AAD,0x6EAE8C,0x6E9242],
      "+0x3C state/task (W / R AI-wrapper)": [0x6E8AB9,0x6E90E3,0x6E9059],
      "+0x54 FirstUnit (W ctor / R AI)": [0x6E8AD0,0x6EAE84,0x6E9060],
      "+0x80 StepCompleted (W ctor+slot23 / R)": [0x6E8B14,0x6E91F5,0x6E9364],
      "+0x83 IsSuspended (W / R slot23 head)": [0x6E8B26,0x6E9174,0x6E9149],
    }
    for title,sites in SITES.items():
        print("\n---",title,"---")
        for s in sites:
            print(dump_site(s,14)); print("   ...")
    # 形式3 检查: mov reg,[glob] -> [reg+idx*4] -> [eax+off]
    print("\n\n=== 形式3 (§S06-K3) 检查: 全局基址->索引->对象字段 ===")
    print("(TeamClass 成员列表为侵入式链表 FirstUnit(+0x54)->[unit+0x5D8], 无独立容器; 见 LAYOUT)")

if __name__=="__main__":
    main()
