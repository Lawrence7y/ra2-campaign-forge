# -*- coding: utf-8 -*-
"""深挖：工厂行的 QueryInterface 返回约定 + ctor 装表 + slot3 派发点；Vector 行的 ④。"""
import os, sys, json, struct, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "b1_rows.json"), encoding="utf-8") as f:
    B1 = json.load(f)["rows"]

def find_ctors_called_by(entry):
    """entry 体内所有直接 call 目标（imm）"""
    size = int(next(r["size"] for r in B1 if r["entry"] == entry))
    calls = []
    for ins in R.disasm_body(int(entry,16), size):
        if ins.id == X86_INS_CALL and ins.operands and ins.operands[0].type == X86_OP_IMM:
            calls.append(R.hx(ins.operands[0].imm & 0xFFFFFFFF))
    return calls

def vtable_writes_in_func(func_va, size=None):
    """函数内 C7 xx imm32 写 vt 立即数（obj vptr）"""
    if size is None:
        size = R.ATLAS.get(R.hx(func_va), {}).get("size") or 512
    writes = []
    for ins in R.disasm_body(func_va, size):
        if ins.id == X86_INS_MOV and len(ins.operands)==2 and ins.operands[1].type==X86_OP_IMM:
            v = ins.operands[1].imm & 0xFFFFFFFF
            if 0x7E0000 <= v <= 0x7F8000:  # .rdata vtable range
                writes.append((R.hx(ins.address), R.hx(v)))
    return writes

def callee_return_consts(func_va):
    prof = R.callee_return_profile(func_va)
    return prof

# 每工厂的 ctor 由其体内 call 找；QueryInterface = ctor 装的主 vt slot0
for r in B1:
    e = r["entry"]
    if "TClassFactory" not in r["name"]:
        continue
    calls = find_ctors_called_by(e)
    print("="*80)
    print(e, r["name"], "体内直接call=", calls)
    # 找 0x6d1c20 类 ctor（装表并检查它）: 取最后一个非CRT/非new的call候选
    for c in calls:
        cva = int(c,16)
        if cva in (0x7C8E17, 0x7C8B3D, 0x6D1C20):
            pass
        # 报每个 call 的装表
        w = vtable_writes_in_func(cva)
        if w:
            # 主 vt = [esi]/[eax]/[ecx] 的第一个写
            print("   ctor", c, "装表", w[:6])

# 专门看 Tactical 工厂的 ctor 0x6d1c20 主 vt slot0
print("\n### 0x6D1C20 主 vt 0x7F4348 slot0 (QueryInterface):")
for slot in range(0,4):
    t = R.u32(0x7F4348 + slot*4)
    print("   vt[+%d]=%s" % (slot, R.hx(t) if t else None))
    if t and R.in_text(t):
        print("      consts=", callee_return_consts(t))
