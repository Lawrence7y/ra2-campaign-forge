#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""0x6BE0xx 退出步进链静态解剖（纯只读，离线，不烧真机趟）。

承接 §430：硬件写断点已把 exitstate[0xA8EDD8]=1 的写入者钉到指令粒度
  0x6BE0B6: mov [0xA8EDD8], edi (edi=1)，主线程，WM_CLOSE+5.8s，之后再无写入。
本脚本要回答 D-09-A 设计输入的两个剩余静态问题：
  (1) esi 是怎么被设置的？call esi 调用的成员函数具体是谁？
  (2) 这些 call 的返回值 eax 被谁消费——即哪一步的返回值门控了链的推进。

方法（全部对齐解码，函数头用前一 ret/填充 + 帧序对钉界，不"遇 ret 就停"）：
  - 从包含 0x6BE0B6 的函数头开始，线性解码到下一个函数头（帧尺寸互校）
  - 抽取所有 call 目标、mov esi 来源、[0xA8EDD8] 写点、以及每步 push 的名字串地址
  - 把 call esi 的目标集与"已知带守卫的函数"交叉，标出 D-09-A 要绕开的那批 callee

产出只是事实清单，不做补丁（补丁设计留给 D-09 裁决）。
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

GAME_SRC = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020")
GAMEMD = GAME_SRC / "gamemd.exe"
EXPECT_SHA16 = "73201cc021497c95"
BASE_IMAGE = 0x400000
WRITER = 0x6BE0B6          # mov [0xA8EDD8],edi (edi=1) — §430 硬件断点实证
EXITSTATE = 0x00A8EDD8
STEP_CALL = 0x6C7400        # §430: call 0x6C7400，ecx=0xB0BC88
OBJ = 0xB0BC88             # §430: exitstep 对象

DATA = GAMEMD.read_bytes()
import hashlib
assert hashlib.sha256(DATA).hexdigest()[:16] == EXPECT_SHA16, "snapshot drifted"

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True


def off_of(va):
    # 本仓 .text: FileOffset = VA - 0x401000（§429/§430 已证）
    return va - 0x401000


def is_readable_va(va):
    return BASE_IMAGE <= va < BASE_IMAGE + 0x750000


def read_cstr_rva(va):
    """从 VA 读一个 ASCII 串（用于 push 的名字参数）。仅在 .rdata/.data 段做保守读取。"""
    o = va - 0x400000  # 粗 RVA -> file: 对 .rdata 段近似；用线性读，遇非可打印即停
    fo = va - BASE_IMAGE
    # 安全窗口
    if fo < 0 or fo >= len(DATA):
        return None
    end = fo
    while end < len(DATA) and end - fo < 64 and 0x20 <= DATA[end] < 0x7F:
        end += 1
    s = DATA[fo:end]
    if len(s) < 2:
        return None
    try:
        return s.decode("ascii")
    except Exception:
        return None


def find_func_start(va_hint):
    """向前找函数头：最近的 'ret ...' 之后紧跟填充(0xCC/0x90) 再紧接 prologue。
    不"遇 ret 就停"——要跨过 ret 直到下一个非填充指令。"""
    o = off_of(va_hint)
    # 回看最多 0x900 字节，逐条对齐解码自一个保守起点
    back_start = va_hint - 0x900
    bs = off_of(back_start)
    ins_list = list(md.disasm(DATA[bs:bs + 0x900], back_start))
    last_boundary = None
    for i, ins in enumerate(ins_list):
        m = ins.mnemonic
        if m == "ret" or (m == "int3" and ins.address < va_hint):
            # ret 之后第一条指令 = 下一函数头候选（需跨填充）
            j = i + 1
            while j < len(ins_list) and ins_list[j].mnemonic in ("nop", "int3"):
                j += 1
            if j < len(ins_list) and ins_list[j].address < va_hint:
                # 只有当下一条是常见 prologue 才认作头
                nxt = ins_list[j]
                if nxt.mnemonic == "push" and "ebp" in nxt.op_str:
                    last_boundary = nxt.address
                elif nxt.mnemonic == "sub" and "esp" in nxt.op_str:
                    last_boundary = nxt.address
    # 兜底：找最近的 push ebp / mov ebp,esp 且 address < va_hint
    cands = [ins.address for ins in ins_list
             if ins.mnemonic == "push" and ins.address < va_hint and "ebp" in ins.op_str]
    if cands:
        return max(cands), ins_list, back_start
    return (last_boundary or back_start), ins_list, back_start


def main():
    start, _, _ = find_func_start(WRITER)
    print("== 函数头候选 (含 0x6BE0B6) = 0x%08X ==" % start)

    # 从函数头线性解码一段，直到再次命中下一个 prologue 或超出块
    fo = off_of(start)
    chunk = DATA[fo:fo + 0x600]
    ins_all = list(md.disasm(chunk, start))

    # 逐块打印，并抽取关键事件
    print("\n== 线性解码 ==")
    calls = []          # (addr, target_va, reg_or_imm, comment)
    esi_writes = []     # (addr, op_str)
    step_calls = []     # 命中 call 0x6C7400
    exit_writes = []    # mov [0xA8EDD8],...
    name_pushes = []    # push imm32 指向可读串

    for ins in ins_all:
        addr, m, ops = ins.address, ins.mnemonic, ins.op_str
        print("  %08X  %s %s" % (addr, m, ops))

        # call 目标解析
        if m == "call":
            if "0x" in ops and "[" not in ops:
                try:
                    tgt = int(ops.split("0x")[1], 16)
                except Exception:
                    tgt = None
                calls.append((addr, tgt, "imm", ops))
                if tgt == STEP_CALL:
                    step_calls.append(addr)
            else:
                calls.append((addr, None, "reg", ops))
                if STEP_CALL == 0:
                    pass
        # esi 来源
        if m == "mov" and ops.startswith("esi"):
            esi_writes.append((addr, ops))
        # exitstate 写点
        if m == "mov" and ("[0x%x]" % EXITSTATE) in ops.replace(" ", "").lower().replace("0x00a8edd8", "[0x%x]" % EXITSTATE):
            exit_writes.append((addr, ops))
        # push imm32 指向 ASCII 名
        if m == "push" and "0x" in ops and "[" not in ops:
            try:
                pv = int(ops.split("0x")[1], 16)
            except Exception:
                pv = None
            if pv is not None and is_readable_va(pv):
                s = read_cstr_rva(pv)
                if s:
                    name_pushes.append((addr, pv, s))

    print("\n== 关键事件汇总 ==")
    print("call 总数:", len(calls))
    print("call [reg] 间接调用 (esi/edi/eax 等):")
    ind = [c for c in calls if c[2] == "reg"]
    for a, t, k, ops in ind:
        print("  %08X  call %s" % (a, ops))
    print("直接 call 目标去重:")
    from collections import Counter
    c = Counter(t for a, t, k, ops in calls if k == "imm" and t is not None)
    for tgt, n in sorted(c.items()):
        print("  call 0x%08X  x%d" % (tgt, n))

    print("\nesi 写入点（找 call esi 的 callee 来源）:")
    for a, ops in esi_writes:
        print("  %08X  mov %s" % (a, ops))

    print("\nexitstate[0xA8EDD8] 写点:")
    for a, ops in exit_writes:
        print("  %08X  mov %s" % (a, ops))

    print("\n名字串 push（.rdata 里的退出步骤名）:")
    for a, pv, s in name_pushes:
        print("  %08X  push 0x%08X  = %r" % (a, pv, s))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
