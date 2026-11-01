#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""退出步进链解剖 v4：修 v3 的「VA 当 file 索引」bug；用帧尺寸 0xA34 直接钉真头。

v1/v2 事实（沿用）：
  - 块体从 0x6BD7C7 起，每 ~0x3D 字节一块；WRITER=0x6BE0B6 是第 N 块的收口
  - 每块：push(buf,1,1,prev_eax,name); call esi; 结果交 0x6C7400 存进 [0xB0BC88] 数组;
    push 8; call 0x7C9E17; eax==0 ⇒ 跳过本块 handler；否则 mov ecx,eax; call 0x6C1XXX
  - 函数尾 ret 0x10 @0x6BE173；0x6BE0E1 cmp [0xA8EDD8],edi
本版目标：
  1) 真头：搜 sub esp,0xA34 字节（[ebp-0xa34] 的帧）+ 其前为 0xCC/0x90 填充
  2) esi 装载点（call esi 的 callee 指针来源）
  3) 名字串原始字节（v1 乱码 ⇒ 判 UTF-16/编码）
"""
import struct, hashlib
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

GAME_SRC = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020")
GAMEMD = GAME_SRC / "gamemd.exe"
assert hashlib.sha256(GAMEMD.read_bytes()).hexdigest()[:16] == "73201cc021497c95"
DATA = GAMEMD.read_bytes()
BASE = 0x400000
WRITER = 0x6BE0B6
md = Cs(CS_ARCH_X86, CS_MODE_32)

def f(v):
    return v - BASE

# 1) 真头：sub esp,0xA34 = 81 EC 34 0A 00 00，且前面 push ebp(0x55);mov ebp,esp(8B EC)
needle = bytes.fromhex("558bec81ec340a00")  # 部分匹配即可（末字节 imm32 第一字节 34）
i = DATA.find(bytes.fromhex("81ec340a0000"), 0, WRITER - BASE + 0x200)
heads = []
while i != -1:
    va = i + BASE
    prev = va - 2
    ok = DATA[f(prev):f(prev) + 2] == bytes.fromhex("558bec") or DATA[f(prev) - 1] in (0x90, 0xCC)
    heads.append((va, DATA[f(prev):f(prev)+2].hex(), ok))
    i = DATA.find(bytes.fromhex("81ec340a0000"), i + 1, WRITER - BASE + 0x200)
print("== sub esp,0xA34 命中（VA, 前两字节, 紧邻push ebp?） ==")
for h in heads:
    print("   %08X prev=%s prologue=%s" % h)
real_head = None
for va, prevhex, ok in heads:
    if ok and va < WRITER:
        real_head = va
print("采用真头 =", hex(real_head) if real_head else None)

if real_head:
    o = f(real_head)
    ins_all = []
    for ins in md.disasm(DATA[o:o + 0x1400], real_head):
        ins_all.append(ins)
        if ins.address > WRITER + 0x120:
            break
    print("\n== 序言 24 条 ==")
    for ins in ins_all[:24]:
        print("  %08X  %s %s" % (ins.address, ins.mnemonic, ins.op_str))
    print("\n== 全部 mov esi,* ==")
    for ins in ins_all:
        if ins.mnemonic == "mov" and ins.op_str.startswith("esi,"):
            print("  %08X  mov %s" % (ins.address, ins.op_str))
    print("\n== call esi 前最近一条 esi 装载（每站点回溯≤8条） ==")
    for n, ins in enumerate(ins_all):
        if ins.mnemonic == "call" and ins.op_str == "esi":
            src = None
            for j in range(max(0, n - 8), n):
                p = ins_all[j]
                if p.mnemonic == "mov" and p.op_str.startswith("esi,"):
                    src = "%08X mov %s" % (p.address, p.op_str)
            print("  %08X call esi  <-  %s" % (ins.address, src if src else "(回溯窗内无)")
                  )

# 2) 名字串原始字节：取 0x6BD7C7..WRITER 的 push 0x7e9xxx / 0x7e8xxx 等
print("\n== push 立即数→.rdata 名字原始字节 ==")
o2 = f(0x6BD7C7)
seen = {}
for ins in md.disasm(DATA[o2:o2 + (WRITER - 0x6BD7C7 + 0x10)], 0x6BD7C7):
    if ins.mnemonic == "push" and ins.op_str.startswith("0x"):
        try:
            pv = int(ins.op_str, 16)
        except ValueError:
            continue
        if BASE < pv < BASE + 0x400000 and pv not in seen:
            raw = DATA[f(pv):f(pv) + 20]
            # ascii 单字节串
            a = b""
            k = 0
            while k < len(raw) and 0x20 <= raw[k] < 0x7F:
                a += bytes([raw[k]]); k += 1
            u = raw.decode("utf-16-le", errors="replace")
            u = u.split("\x00")[0]
            seen[pv] = (a.decode("ascii", "replace"), u[:12])
for pv, (a, u) in sorted(seen.items()):
    print("  %08X ascii=%-14r utf16=%r" % (pv, a, u))
