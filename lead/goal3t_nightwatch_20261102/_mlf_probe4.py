# -*- coding: utf-8 -*-
"""§533 probe D -- 追 [0xA8B230]+0x62C / +0x620/+0x624/+0x628/+0x630 的身份与写点。

只读 gamemd.exe。零真机、零写入（除 stdout）。

背景（probe B 已钉）：MainLogicFrame 0x55D360 有两条**不经 0x55DE7E inc 就 ret** 的出口：
  (a) 0x55DEDB —— 头部 [0xA8E9A0]==0 早退（非局内）
  (b) 0x55D877 —— 0x55D7C2 分支：GameMode∈{0,5} 且 [[0xA8B230]+0x62C]!=0
                  ⇒ pump + 0x48D080 + 0x53B560 + vtable+0x5C + 0x4F4480 + LogicUpdate(0x55E160) → ret
                  **世界更新照跑，帧号不推进**

本探针要回答：(b) 的两个字段是谁、什么时候非零。
"""
import hashlib
import struct
from collections import defaultdict

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
raw = open(EXE, "rb").read()
assert hashlib.sha256(raw).hexdigest() == EXPECT_SHA, "image drift"

e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e + 6)[0]
optsz = struct.unpack_from("<H", raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", raw, opt + 28)[0]
tab = opt + optsz
SEC = []
for i in range(nsec):
    nm = raw[tab + i * 40: tab + i * 40 + 8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i * 40 + 8)
    SEC.append((nm, IB + va, vsz, rp, rsz))
TEXT = next(s for s in SEC if s[0] == ".text")
TLO, THI = TEXT[1], TEXT[1] + TEXT[4]


def fo(va):
    for nm, sva, vsz, rp, rsz in SEC:
        if sva <= va < sva + vsz:
            off = rp + (va - sva)
            return off if off < rp + rsz else None
    return None


def rd(va, n):
    o = fo(va)
    return raw[o:o + n] if o is not None else b"\0" * n


pat = struct.pack("<I", 0xA8B230)
print("=" * 74)
print("T1 [0xA8B230] 全镜像 raw abs32 引用站点")
print("=" * 74)
sites = []
p = 0
while True:
    j = raw.find(pat, p)
    if j < 0:
        break
    va = None
    for nm, sva, vsz, rp, rsz in SEC:
        if rp <= j < rp + rsz:
            va = sva + (j - rp)
            sect = nm
            break
    sites.append((va, j, sect))
    p = j + 1
print("  总计 %d 处" % len(sites))
for va, off, sect in sites:
    print("   %08X  %s  prefix=%s" % (va, sect, raw[off - 2:off].hex()))

# ---- 找出这些站点所属函数（用 0x55D360 同款线性解码 + 回扫） ----------------
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True

print()
print("=" * 74)
print("T2 每个引用点的反汇编上下文（前 3 条）")
print("=" * 74)
for va, off, sect in sites:
    if va is None:
        continue
    start = max(TLO, va - 12)
    print("\n--- %08X ---" % va)
    for ins in MD.disasm(rd(start, va - start + 10), start):
        m = " <<<" if ins.address <= va < ins.address + ins.size else ""
        print("   %08X  %-20s %-7s %s%s" % (
            ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, m))

# ---- 0x62C / 0x630 等字段的 disp 形态普查 ----------------------------------
print()
print("=" * 74)
print("T3 字段 disp 形态普查（[reg+0x62C] 族）")
print("=" * 74)
for disp in (0x620, 0x624, 0x628, 0x62C, 0x630):
    d = struct.pack("<I", disp)
    hits32 = []
    p = 0
    while True:
        j = raw.find(d, p)
        if j < 0:
            break
        for nm, sva, vsz, rp, rsz in SEC:
            if rp <= j < rp + rsz and nm == ".text":
                hits32.append((sva + (j - rp), nm))
                break
        p = j + 1
    print("  disp32 0x%03X : %d 处 %s" % (disp, len(hits32),
                                         [("%08X" % h[0]) for h in hits32[:8]]))

# ---- 0xA8B230 附近全局 -----------------------------------------------------
print()
print("=" * 74)
print("T4 0xA8B230 邻域全局（BSS 段？）")
print("=" * 74)
for va in range(0xA8B230, 0xA8B240, 4):
    print("   %08X = %08X" % (va, struct.unpack_from("<I", rd(va, 4), 0)[0]))
print("  (.data 虚尺寸 vs raw —— BSS 判定)")
for nm, sva, vsz, rp, rsz in SEC:
    print("   %-8s VA=[%08X,%08X) raw_off=%X raw_sz=%X %s" % (
        nm, sva, sva + vsz, rp, rsz,
        "BSS(虚>实)" if vsz > rsz else ""))
