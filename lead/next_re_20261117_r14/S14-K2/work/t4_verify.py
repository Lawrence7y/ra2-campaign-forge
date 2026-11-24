#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T4 收尾: 找构造器写 vptr = 主 vtable 的地址点, 确认 address point;
   并验证目标分配点 push 确实是 operator new 的栈参数 (逐字符)."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import wbase as W

# 各类候选 vt address point (RTTI COL 的 vtable[-1] 指 COL)
VT_CAND = {
    "ScriptClass": [0x7F0F4C,0x7F0F54,0x7F0F5C,0x7F0F78],
    "TaskForceClass": [0x7F4654,0x7F465C,0x7F4664,0x7F4680],
    "AITriggerTypeClass": [0x7E2A24,0x7E2A2C,0x7E2A34,0x7E2A50],
    "TeamClass": [0x7F4730],
    "HouseClass": [0x7EA8A0],
    "TeamTypeClass": [0x7F47D0],
}

def find_c7_writes(vt):
    """扫 .text 找 C7 0x?? imm32 形态写 vt 到内存 (mov dword [reg/mem], vt)"""
    hits=[]; code=W.DATA[W.TEXT_RAW:W.TEXT_RAW+W.TEXT_RSZ]; base=W.TEXT_VA
    pat=struct.pack("<I",vt)
    for i in range(len(code)-10):
        if code[i]==0xC7 and code[i+2:i+6]==pat:
            # C7 /0 imm32 => modrm at i+1; 6 bytes总
            hits.append((base+i, code[i+1]))
    return hits

def verify_alloc(va, imm):
    """从 push 点反汇编到 new, 逐字符核对"""
    lines=[]
    for a,m,o,insn in W.disasm(va, 0x30, stop_ret=False):
        lines.append("0x%08X %-18s %-6s %s"%(a, W.bytes_at(a,insn.size).hex(), m, o))
        if a>va+0x20: break
    return "\n".join(lines)

def main():
    print("=== 构造器写 vptr = 候选 vt address point ===")
    for cname,cands in VT_CAND.items():
        print(f"\n{cname}:")
        for vt in cands:
            hits=find_c7_writes(vt)
            if hits:
                locs=", ".join("0x%X(modrm 0x%X)"%(a,md) for a,md in hits[:8])
                print(f"   vt=0x{vt:X}: {len(hits)} writes -> {locs}")
    print("\n\n=== 关键分配点逐字符 ===")
    for va,imm in [(0x6F0A4D,0xA0),(0x500A13,0x160B8),(0x6E82D2,0xD4),(0x41F378,0x110)]:
        print(f"\n--- push 0x{imm:X} @0x{va:X} ---")
        print(verify_alloc(va,imm))

if __name__=="__main__":
    main()
