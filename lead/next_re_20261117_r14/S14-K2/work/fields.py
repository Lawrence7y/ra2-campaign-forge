#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fields.py — 类字段读写点双通道扫描器
  对给定类的一组方法入口, thiscall this=ecx, 追踪 this 寄存器传播,
  找 [this + disp] 的 read / write 点, 分类三种访问形式:
    形式1: [reg + disp]       (reg 直接 = this)
    形式2: [reg + idx*4 + disp] 经指针数组
    形式3: mov reg,[全局] -> [reg+idx*4] -> [eax+off] (§S06-K3)
  排除 call [reg+disp] (虚调用, 非数据字段读点), 显式报剔除数。
  函数区间用 atlas entry+size 做包含判定 (不假定 entry_at_or_before)。
"""
import sys, os, csv, struct
sys.path.insert(0, os.path.dirname(__file__))
import wbase as W
from capstone.x86 import X86_OP_REG, X86_OP_MEM, X86_OP_IMM

ATL = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

def load_atlas():
    idx=[]
    with open(ATL,encoding="utf-8") as f:
        r=csv.DictReader(f,delimiter="\t")
        for row in r:
            idx.append((int(row["entry"],16), int(row["size"])))
    return sorted(idx)

ATLAS = None
def contains_fn(addr):
    """函数区间包含: 返回 (entry,size) 或 None。用二分。"""
    import bisect
    entries=[x[0] for x in ATLAS]
    i=bisect.bisect_right(entries,addr)-1
    if i>=0:
        e,s=ATLAS[i]
        if e<=addr<e+s:
            return (e,s)
    return None

def access_kind(insn, op):
    """返回 'W'/'R'/'RW'/None。capstone op.access"""
    try:
        a=op.access
    except Exception:
        a=None
    if a is None:
        # 退化: 看 mnemonic 与操作数位置
        return "?"
    if a==3: return "RW"
    if a==1: return "R"
    if a==2: return "W"
    return "?"

def scan_method(entry, size, this_disp_set=None):
    """反汇编一个方法, 追踪 this 寄存器, 返回 (reads, writes, vcalls_excluded)"""
    reads=[]; writes=[]; vcalls=[]
    this_regs={"ecx"}
    for a,m,o,insn in W.disasm(entry,size,stop_ret=False):
        # skipdata 伪指令 (.byte) 无 operands, 访问会抛 CS_ERR_SKIPDATA -> 跳过
        if insn.id==0 or m.startswith("."):
            continue
        try:
            ops=insn.operands
        except Exception:
            continue
        # --- 传播 this: mov dst,src (src 是 this) ---
        if m=="mov" and len(ops)==2:
            d,s=ops[0],ops[1]
            if d.type==X86_OP_REG and s.type==X86_OP_REG:
                dn=insn.reg_name(d.reg); sn=insn.reg_name(s.reg)
                if sn in this_regs: this_regs.add(dn)
                elif dn in this_regs and dn!=sn: this_regs.discard(dn)
        # --- 传播 this: xchg / lea reg,[this+disp] (取地址后可能当新基) 暂不追 lea ---
        # --- 内存操作数扫描 ---
        is_call = m in ("call","jmp")
        for op in ops:
            if op.type!=X86_OP_MEM: continue
            base = insn.reg_name(op.mem.base) if op.mem.base else None
            idxr = insn.reg_name(op.mem.index) if op.mem.index else None
            disp = op.mem.disp
            # 虚调用 call [reg+disp] (base 是 this, disp 为 vtable 槽) -> 排除
            if is_call and base in this_regs and idxr is None:
                vcalls.append((a,m,o,base,disp))
                continue
            if base in this_regs and idxr is None:
                k=access_kind(insn,op)
                rec=(a,m,o,base,disp,k)
                if k in ("W","RW"): writes.append(rec)
                elif k=="R": reads.append(rec)
                else: reads.append(rec)  # '?' 保守当读
            elif idxr in this_regs and base is None:
                k=access_kind(insn,op)
                rec=(a,m,o,"idx:"+idxr,disp,k)
                reads.append(rec)
        # call 会 clobber caller-save (eax/ecx/edx); 但若 this 在 ecx 且 call 前刚 mov ecx,this 需谨慎
        if m=="call":
            for r in ("eax","ecx","edx"):
                if a==entry or True:
                    this_regs.discard(r)
    return reads,writes,vcalls

def main(methods, label):
    global ATLAS
    ATLAS=load_atlas()
    all_r={}; all_w={}; all_v=[]
    print(f"=== {label}: {len(methods)} methods ===")
    for entry,size in methods:
        r,w,v=scan_method(entry,size)
        all_v.extend(v)
        for rec in r:
            all_r.setdefault(rec[4],[]).append((entry,)+rec)
        for rec in w:
            all_w.setdefault(rec[4],[]).append((entry,)+rec)
    print(f"call [this+disp] excluded (vcalls): {len(all_v)}")
    # 只显示字段偏移在合理范围(0..0x400)
    print(f"\n{'disp':>6} {'#W':>4} {'#R':>4}  sample W sites / R sites")
    for disp in sorted(set(all_r)|set(all_w)):
        if not (0<=disp<=0x600): continue
        w=all_w.get(disp,[]); r=all_r.get(disp,[])
        ws=" ".join("0x%X@fn0x%X"%((x[1],x[0])) for x in w[:3])
        rs=" ".join("0x%X@fn0x%X"%((x[1],x[0])) for x in r[:3])
        mark="  <<BOTH" if w and r else ("  <W-only" if w else "  <R-only")
        print(f"0x{disp:04X}  {len(w):4d} {len(r):4d}  W[{ws}] R[{rs}]{mark}")
    return all_r,all_w,all_v

if __name__=="__main__":
    # 由外部脚本 import 调用 main(methods,label)
    pass
