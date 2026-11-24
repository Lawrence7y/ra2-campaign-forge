#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T4: GetSize 双向核对 (§981 槽契约)
  判据不特异(B8 imm32 C3 全镜像 666) -> 叠加槽位锚定 + 构造器 push<size> 双点闭合
  (1) 全 .text 扫 B8 imm32 C3 桩, 记 imm
  (2) 对每个目标类 vtable 全槽扫, 找槽值指向这些桩
  (3) 构造器分配点扫 6A imm8 / 68 imm32 / mov[esp],imm / sub esp,imm -> push<size>
  (4) 0x4C9150 抽象基类共用桩 (33 C0 C3) 排除
  槽号不假定, 逐槽记录。
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
import wbase as W

STUB_4C9150 = 0x4C9150

def scan_b8_imm32_c3():
    """全 .text 逐字节扫 B8 imm32 C3, 且该地址须为指令边界(先验)"""
    hits = {}
    code = W.DATA[W.TEXT_RAW:W.TEXT_RAW+W.TEXT_RSZ]
    base = W.TEXT_VA
    for i in range(len(code)-6):
        if code[i] == 0xB8 and code[i+5] == 0xC3:
            imm = struct.unpack_from("<I", code, i+1)[0]
            va = base + i
            hits[va] = imm
    return hits

def scan_68_imm32():
    """扫 68 imm32 (push imm32) 分配点, 返回 {va:imm}"""
    hits = {}
    code = W.DATA[W.TEXT_RAW:W.TEXT_RAW+W.TEXT_RSZ]
    base = W.TEXT_VA
    for i in range(len(code)-5):
        if code[i] == 0x68:
            imm = struct.unpack_from("<I", code, i+1)[0]
            hits[base+i] = imm
    return hits

def verify_boundary(va):
    """用 capstone 从 va 起反汇编 1 条, 看是否正好 B8 imm32 C3"""
    ins = W.disasm(va, 6, stop_ret=False)
    if not ins:
        return False
    a,m,o,insn = ins[0]
    return a==va and m=="mov" and insn.size==5 and W.rd8(va+5)==0xC3

def class_vtable(name):
    # 已知主 vtable (RTTI 定类)
    return {
        "TeamClass": 0x7F4730,
        "TeamTypeClass": 0x7F47D0,
        "HouseClass": 0x7EA8A0,
        "AITriggerTypeClass": 0x7E2A50,
        "ScriptClass": 0x7F0F78,
        "TaskForceClass": 0x7F4680,
    }.get(name)

def main():
    b8 = scan_b8_imm32_c3()
    print("B8 imm32 C3 raw count:", len(b8))
    # 边界校验后
    b8v = {va:imm for va,imm in b8.items() if verify_boundary(va)}
    print("B8 imm32 C3 instruction-boundary verified:", len(b8v))
    print("0x4C9150 in set:", 0x4C9150 in b8, "(should be 33C0C3, not B8)")

    classes = ["HouseClass","TeamClass","ScriptClass","TaskForceClass","AITriggerTypeClass","TeamTypeClass"]
    print("\n=== 每类 vtable 全槽 x B8桩 锚定 ===")
    for cname in classes:
        vt = class_vtable(cname)
        if not vt: 
            print(cname, "NO VTABLE"); continue
        # RTTI 定类
        from vt import rtti_name_from_col, find_col_for_vtable
        col = find_col_for_vtable(vt)
        td, nm = rtti_name_from_col(col)
        print(f"\n{cname}: vt=0x{vt:X} COL=0x{col:X} TD=0x{td:X} RTTI={nm}")
        for i in range(64):
            sv = W.rd32(vt+i*4)
            if sv is None or sv==0: break
            if sv in b8v:
                print(f"  slot[{i}] +0x{i*4:X} = 0x{sv:X} -> GetSize imm=0x{b8v[sv]:X} ({b8v[sv]})")
            elif not W.in_text(sv):
                break
    return b8v

if __name__ == "__main__":
    main()
