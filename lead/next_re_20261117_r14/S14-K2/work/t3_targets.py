#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3 收尾: 对候选 HouseClass 字段在全 .text 找读/写点 (字节级, 先验指令边界),
   并给每个点标注宿主函数 (atlas 区间包含)。目标偏移来自 YRpp/既有实证, 本卡独立复核。"""
import sys, os, csv, bisect
sys.path.insert(0, os.path.dirname(__file__))
import wbase as W
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

# 目标字段: off -> 说明 (来自 YRpp / 既有实证, 待本卡字节复核)
TARGETS = {
  0x30C: "Credits(actual)",
  0x1DC: "StartingCredits(INI)",
  0x1D4: "TechLevel",
  0x1ED: "PlayerControl/IsHuman",
  0x1EC: "MP slot flag / IsPlayerControl",
  0x258: "Supers.Items",
  0x264: "Supers.Count",
  0x56F9: "Color.R",
  0x56FA: "Color.G",
  0x56FB: "Color.B",
  0x577A: "SpySatActive",
  0x5788: "Alliance bitmap",
  0x57A4: "CDTimer.Start",
}

def load_atlas():
    A=[(int(r['entry'],16),int(r['size'])) for r in csv.DictReader(
        open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv',encoding='utf-8'),delimiter='\t')]
    A.sort(); return A
ATL=load_atlas(); ENTRIES=[x[0] for x in ATL]
def host(addr):
    i=bisect.bisect_right(ENTRIES,addr)-1
    if i>=0:
        e,s=ATL[i]
        if e<=addr<e+s: return e
    return None

def scan_all_text():
    """全 .text 逐指令扫, 找 disp 在 TARGETS 的内存操作数, 记 host 函数"""
    found={k:{'R':[], 'W':[]} for k in TARGETS}
    for a,m,o,insn in W.disasm(W.TEXT_VA, W.TEXT_VS, stop_ret=False):
        if insn.id==0 or m.startswith('.'): continue
        for op in insn.operands:
            if op.type!=X86_OP_MEM: continue
            d=op.mem.disp
            if d not in TARGETS: continue
            # 访问类型
            acc=op.access
            kind='R' if acc in (1,3) else ('W' if acc==2 else '?')
            h=host(a)
            found[d][kind if kind in ('R','W') else 'R'].append((a,m,o,h))
    return found

def main():
    f=scan_all_text()
    print("=== 全 .text 逐指令字段点 (host=atlas 函数区间包含) ===")
    for off,name in sorted(TARGETS.items()):
        R=f[off]['R']; Wr=f[off]['W']
        # 只看 host 存在 (在已知 HouseClass 方法) 的点, 但也列总数
        print(f"\n0x{off:X} {name}: total R={len(R)} W={len(Wr)}")
        # 采样写点、读点 (host)
        ws=[x for x in Wr if x[3] is not None][:5]
        rs=[x for x in R if x[3] is not None][:5]
        for x in ws: print("   W 0x%X %-6s %-30s host=0x%X"%(x[0],x[1],x[2],x[3]))
        for x in rs: print("   R 0x%X %-6s %-30s host=0x%X"%(x[0],x[1],x[2],x[3]))
    import json
    out=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S14-K2\EVIDENCE\T3_field_sites.json'
    json.dump({hex(k):{kk:[[hex(z[0]),z[1],z[2],hex(z[3]) if z[3] else None] for z in vv] for kk,vv in v.items()} for k,v in f.items()},open(out,'w'),indent=1)
    print("\nwrote",out)

if __name__=="__main__": main()
