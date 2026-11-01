#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""退出步进链解剖 v3：真函数头（prologue 字节判据）+ call esi 的 esi 来源 + 名字串真相。

v2 已知（写入 §431 候选）：
  - 链尾 0x6BE0B6 mov [0xA8EDD8],edi(=1)；0x6BE0E1 cmp [0xA8EDD8],edi；0x6BE173 ret 0x10
  - .rdata VA=0x7E1000 故名字 0x7e97xx 的 file off = VA-0x400000
  - 0x6C7400 是「存 eax 到 [ecx] 并推进」的列表追加器（ecx=0xB0BC88 全局游标）
本版聚焦：
  1) 用 push ebp/mov ebp,esp + sub esp(大帧) 钉真头，整函数解码
  2) 每个 call esi 之前最近的 mov esi,*（=循环用的函数指针来源）
  3) 名字串：直接 hexdump 该 VA 的原始字节（v1/v2 读出乱码⇒可能是 UTF-16 或短串）
  4) 每步的 call 0x6CXXXX（去重）⇒ 这批就是「带守卫的退出步骤处理函数族」候选
"""
import struct, hashlib
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

GAME_SRC = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020")
GAMEMD = GAME_SRC / "gamemd.exe"
assert hashlib.sha256(GAMEMD.read_bytes()).hexdigest()[:16] == "73201cc021497c95"
DATA = GAMEMD.read_bytes()
WRITER = 0x6BE0B6
md = Cs(CS_ARCH_X86, CS_MODE_32)

def fo(va):
    return va - 0x400000

# 1) 真头：回看 0x3000，找 prologue 字节
pat1 = b"\x55\x8b\xec\x81\xec"  # push ebp; mov ebp,esp; sub esp,imm32
pat2 = b"\x55\x8b\xec"          # push ebp; mov ebp,esp（小帧）
starts = []
lo = WRITER - 0x3000
for pat, tag in ((pat1, "sub-esp"), (pat2, "plain")):
    i = DATA.find(pat, lo, WRITER)
    while i != -1:
        va = i + 0x400000
        starts.append((va, tag))
        i = DATA.find(pat, i + 1, WRITER)
# 取「能一路解到 WRITER 且中间无 int3/ret 断开」的最大 va（=最近的头，最可能真头）
def clean_decode(start_va, span):
    o = fo(start_va)
    ins = list(md.disasm(DATA[o:o+span], start_va))
    if not ins:
        return False
    # 第一条须就是 prologue
    first = ins[0]
    if not (first.mnemonic=="push" and first.op_str=="ebp"):
        return False
    return True
best = None
for va, tag in starts:
    if clean_decode(va, WRITER - va + 0x10):
        best = (va, tag)
        break  # starts 已按出现序，但取最近头=va 最大
if best is None:
    # 退而求其次：va 最大的能解到 WRITER 的
    for va, tag in sorted(starts, reverse=True):
        o=fo(va); 
        if any(i.address==WRITER for i in md.disasm(DATA[o:o+(WRITER-va)+0x10], va)):
            best=(va,tag); break
print("== 真头候选 ==")
for va, tag in sorted(set(starts), reverse=True)[:12]:
    print("   %08X  %s%s" % (va, tag, "  <== 采用" if best==(va,tag) else ""))
print("采用真头 =", best)

head_va = best[0]
o = fo(head_va)
ins_all = []
for ins in md.disasm(DATA[o:o+0x1200], head_va):
    ins_all.append(ins)
    if ins.address > WRITER + 0x120:
        break
print("\n== 头前 18 条（看帧/esi 初始化） ==")
for ins in ins_all[:18]:
    print("  %08X  %s %s" % (ins.address, ins.mnemonic, ins.op_str))

# 2) call esi 的 esi 来源：函数内所有 mov esi,*
print("\n== 函数内全部 mov esi,* ==")
for ins in ins_all:
    if ins.mnemonic=="mov" and ins.op_str.startswith("esi,"):
        print("  %08X  mov %s" % (ins.address, ins.op_str))

# 3) 名字串真相：hexdump 0x7e97xx..0x7e99xx 用到的地址
print("\n== 名字 VA 原始字节 ==")
used = []
for ins in ins_all:
    if ins.mnemonic=="push" and ins.op_str.startswith("0x"):
        try: pv=int(ins.op_str,16)
        except: continue
        if 0x7e9000 <= pv <= 0x7ea000:
            used.append((ins.address, pv))
for a, pv in used[:30]:
    raw = DATA[fo(pv):fo(pv)+16]
    asc = "".join(chr(b) if 0x20<=b<0x7f else "." for b in raw)
    # UTF-16?
    u16 = raw.decode("utf-16-le", errors="replace")[:8]
    print("  @%08X push %08X bytes=%s ascii=%-16s u16=%r" % (a, pv, raw.hex(), asc, u16))

# 4) 每步的 call 0x6CXXXX（块处理函数族）
print("\n== 块处理 call 目标（去重排序） ==")
blk = []
for ins in ins_all:
    if ins.mnemonic=="call" and ins.op_str.startswith("0x"):
        try: t=int(ins.op_str,16)
        except: continue
        if 0x6c0000<=t<0x6c7000 and t!=0x6c7400:
            blk.append(t)
for t in sorted(set(blk)):
    print("   call 0x%08X" % t)
print("   块处理函数数量 =", len(set(blk)), " 步进间距=", [b-a for a,b in zip(sorted(set(blk)),sorted(set(blk))[1:])][:6])

# 取第一个块处理函数 0x6C14C0 头看它调谁
first = sorted(set(blk))[0] if blk else None
if first:
    print("\n== 第一个块处理 0x%08X 头 12 条 ==" % first)
    o2=fo(first)
    for n,ins in enumerate(md.disasm(DATA[o2:o2+0x40], first)):
        print("  %08X  %s %s" % (ins.address, ins.mnemonic, ins.op_str))
        if n>11: break

# 全局函数指针 [0xa8f794] 谁写
print("\n== esi 指向的全局 0xA8F794（若 esi 从其装载）==")
# 在 .text 找 mov [0xa8f794], * 写点
needle = struct.pack("<I", 0xA8F794)
idx = DATA.find(needle, 0x1000, 0x3E0000)
cnt=0
while idx!=-1 and cnt<12:
    va=idx-1+0x400000
    o3=idx-1
    for ins in md.disasm(DATA[o3:o3+12], va):
        if ins.mnemonic=="mov" and "0xa8f794" in ins.op_str and ins.op_str.startswith("["):
            print("  %08X  mov %s" % (ins.address, ins.op_str)); cnt+=1
        break
    idx = DATA.find(needle, idx+1, 0x3E0000)
