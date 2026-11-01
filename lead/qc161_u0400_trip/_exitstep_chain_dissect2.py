#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""退出步进链解剖 v2：钉真函数头、找 esi 装载点、读穿 0x6BE0B6、提取全部步骤名串。

v1 两个坑（如实登记）：
  1) find_func_start 取 max(cands) 拿到的是错位解码里的假 push ebp——
     函数头必须用「字节级证据」钉：prologue 字节序列 + 前一字节是 0xCC/0x90 填充。
  2) 0x900 解码窗没够到 0x6BE0B6（差 0x900 整），窗太小。

本版：
  - 用字节模式找头：90/CC 填充之后第一条指令，且解码对齐自洽
  - 从函数头一路解码到 WRITER+0x400，全部块抽取
  - push imm32 的名字串：VA→file offset 用 PE 段表（不猜 0x400000 线性）
  - call esi 之前最近的 esi 写入点回溯（可能在本函数头之前——宿主序言）
"""
import struct
import hashlib
import subprocess
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

GAME_SRC = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020")
GAMEMD = GAME_SRC / "gamemd.exe"
EXPECT_SHA16 = "73201cc021497c95"
WRITER = 0x6BE0B6
EXITSTATE = 0x00A8EDD8
STEP_CALL = 0x6C7400
MEMCALL = 0x7C9E17
OBJ = 0x00B0BC88

DATA = GAMEMD.read_bytes()
assert hashlib.sha256(DATA).hexdigest()[:16] == EXPECT_SHA16, "snapshot drifted"

# ---- PE 段表：VA <-> file offset 双向，不再猜 ----
pe_off = struct.unpack_from("<I", DATA, 0x3C)[0]
nsec = struct.unpack_from("<H", DATA, pe_off + 6)[0]
opt_size = struct.unpack_from("<H", DATA, pe_off + 20)[0]
IMAGE_BASE = struct.unpack_from("<I", DATA, pe_off + 24 + 28)[0]  # OptionalHeader.ImageBase
sec_off = pe_off + 24 + opt_size
SECS = []
for i in range(nsec):
    so = sec_off + i * 40
    name = DATA[so:so + 8].rstrip(b"\0").decode("ascii", "replace")
    vsize, va, rawsize, raw = struct.unpack_from("<IIII", DATA, so + 8)
    SECS.append((name, IMAGE_BASE + va, vsize, raw, rawsize))
assert IMAGE_BASE == 0x400000, "image base %08X" % IMAGE_BASE


def va_to_fo(va):
    for name, sva, svsize, sraw, srawsize in SECS:
        if sva <= va < sva + max(svsize, srawsize):
            return sraw + (va - sva)
    return None


def fo_to_va(fo):
    for name, sva, svsize, sraw, srawsize in SECS:
        if sraw <= fo < sraw + srawsize:
            return sva + (fo - sraw)
    return None


print("== 段表 ==")
for s in SECS:
    print("  %-8s VA=%08X sz=%06X raw=%06X rsz=%06X" % s)

md = Cs(CS_ARCH_X86, CS_MODE_32)


def read_cstr(va):
    fo = va_to_fo(va)
    if fo is None:
        return None
    end = fo
    while end < len(DATA) and end - fo < 128 and 0x20 <= DATA[end] < 0x7F:
        end += 1
    if end - fo < 2:
        return None
    return DATA[fo:end].decode("ascii", "replace")


# ---- 真函数头：从 WRITER 回看，找「填充块之后第一条指令」且自 0x6BE0xx 步长块可对齐 ----
# §430：0x6BE0B6 所在块是 ~72B 同构块。先取一个较大回看窗，逐一起点对齐解码，
# 选「能一条不落地解到 WRITER 且指令边界恰好踩中 WRITER」的起点。
cand_heads = []
back_lo = WRITER - 0x2000
for probe in range(back_lo, WRITER):
    fo = va_to_fo(probe)
    if fo is None:
        continue
    got_writer = False
    count = 0
    for ins in md.disasm(DATA[fo:fo + 0x2000], probe):
        count += 1
        if ins.address == WRITER:
            got_writer = True
            break
        if ins.address > WRITER:
            break
    if got_writer:
        cand_heads.append((probe, count))

print("\n== 能对齐解码并精确踩中 WRITER 的起点数：%d ==" % len(cand_heads))
# 取最小的起点（最早 head）与最大起点都看，但先看「其前一字节是 CC/90 填充」的
strict = []
for probe, count in cand_heads:
    fo = va_to_fo(probe)
    prev = DATA[fo - 1] if fo > 0 else None
    if prev in (0x90, 0xCC, 0xC3):
        strict.append((probe, count, prev))
print("== 其中前字节=填充/ret 的起点（真头强判据）：%d ==" % len(strict))
for probe, count, prev in strict[:10]:
    print("   head=%08X count=%d prevbyte=%02X" % (probe, count, prev))

# 选 strict 里地址最大的（= 最近真头；min 常是错位侥幸），若无 strict 用 cand_heads 最大
if strict:
    head = max(p for p, _, _ in strict)
else:
    head = max(p for p, _ in cand_heads)
print("\n== 采用函数头 = 0x%08X ==" % head)

fo = va_to_fo(head)
ins_all = []
for ins in md.disasm(DATA[fo:fo + 0x1200], head):
    ins_all.append(ins)
    if ins.address > WRITER + 0x300:
        break

# esi 装载点回溯（全函数 + 头前 0x60 字节）
print("\n== esi 写入点 ==")
for ins in ins_all:
    if ins.mnemonic == "mov" and ins.op_str.startswith("esi,"):
        print("  %08X  mov %s" % (ins.address, ins.op_str))
fo2 = va_to_fo(head - 0x60)
for ins in md.disasm(DATA[fo2:fo2 + 0x60], head - 0x60):
    if ins.mnemonic == "mov" and ins.op_str.startswith("esi,"):
        print("  %08X  mov %s   (头前)" % (ins.address, ins.op_str))

# 名字串提取（段表版）
print("\n== push imm32 名字串（去重按序） ==")
names = []
for ins in ins_all:
    if ins.mnemonic == "push" and ins.op_str.startswith("0x"):
        try:
            pv = int(ins.op_str, 16)
        except ValueError:
            continue
        if 0x400000 <= pv < 0xC00000:
            s = read_cstr(pv)
            if s and s.isprintable() and len(s) >= 3:
                names.append((ins.address, pv, s))
seen = set()
for a, pv, s in names:
    if pv not in seen:
        seen.add(pv)
        print("  %08X push %08X = %r" % (a, pv, s))

# 块结构：每个 call esi 站点前后文（前一条 call 0x7C9E17 之后的 test/je 消费链）
print("\n== call esi 站点与返回值消费者 ==")
n_esi = sum(1 for i in ins_all if i.mnemonic == "call" and i.op_str == "esi")
print("  call esi 总数（本次窗口）:", n_esi)
# 提取每个 step 块的 name 与后续条件分支
import re
pat = None
for idx, ins in enumerate(ins_all):
    if ins.mnemonic == "push" and ins.op_str.startswith("0x"):
        try:
            pv = int(ins.op_str, 16)
        except ValueError:
            pv = None
        if pv and 0x7E9000 <= pv <= 0x7EA000:
            s = read_cstr(pv)
            if s and len(s) >= 3:
                print("  step-name @%08X: %r" % (ins.address, s))

# call 0x6C7400 的 ecx 装载
print("\n== call 0x6C7400 之前的 ecx 装载（去重） ==")
ecx_sets = set()
for idx, ins in enumerate(ins_all):
    if ins.mnemonic == "call" and ins.op_str.startswith("0x6c7400"):
        for j in range(max(0, idx - 4), idx):
            p = ins_all[j]
            if p.mnemonic == "mov" and p.op_str.startswith("ecx,"):
                ecx_sets.add(p.op_str)
print("  ", sorted(ecx_sets))

# 0x6C7400 本体头 32 条
print("\n== 0x6C7400 本体（前 30 条） ==")
fo3 = va_to_fo(STEP_CALL)
for n, ins in enumerate(md.disasm(DATA[fo3:fo3 + 0x90], STEP_CALL)):
    print("  %08X  %s %s" % (ins.address, ins.mnemonic, ins.op_str))
    if n > 29:
        break

# 0x7C9E17 本体头 12 条
print("\n== 0x7C9E17 本体（前 12 条） ==")
fo4 = va_to_fo(MEMCALL)
for n, ins in enumerate(md.disasm(DATA[fo4:fo4 + 0x50], MEMCALL)):
    print("  %08X  %s %s" % (ins.address, ins.mnemonic, ins.op_str))
    if n > 11:
        break

# WRITER 之后：exitstate 是否被再递增、函数尾在哪
print("\n== WRITER 之后 0x300 字节内 [0xA8EDD8] 相关 ==")
for ins in ins_all:
    if ins.address >= WRITER and (("a8edd8" in ins.op_str.lower()) or (ins.mnemonic == "ret")):
        print("  %08X  %s %s" % (ins.address, ins.mnemonic, ins.op_str))
