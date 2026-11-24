# -*- coding: utf-8 -*-
"""§533 probe G -- 0x41D400 段（连续读 +0x620..+0x630）身份 + 0xA8B230 指针来源。

只读 gamemd.exe。零真机、零写入（除 stdout）。
"""
import hashlib
import struct

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


MD = Cs(CS_ARCH_X86, CS_MODE_32)

print("=" * 74)
print("T1 0x41D3C0..0x41D4E0 反汇编（含 +0x620..+0x630 连续读）")
print("=" * 74)
for ins in MD.disasm(rd(0x41D3C0, 0x120), 0x41D3C0):
    print("  %08X  %-20s %-7s %s" % (ins.address, ins.bytes.hex(),
                                     ins.mnemonic, ins.op_str))

print()
print("=" * 74)
print("T2 [0xA8B230] 的 raw abs32 命中（精确 4 字节模式，含非指令区）")
print("=" * 74)
pat = struct.pack("<I", 0xA8B230)
cnt, p = 0, 0
while True:
    j = raw.find(pat, p)
    if j < 0:
        break
    cnt += 1
    va = None
    sect = "?"
    for nm, sva, vsz, rp, rsz in SEC:
        if rp <= j < rp + rsz:
            va = sva + (j - rp)
            sect = nm
            break
    if cnt <= 12:
        print("   %s VA=%s off=%07X prefix=%s" % (
            sect, ("%08X" % va) if va else "?", j, raw[j - 3:j].hex()))
    p = j + 1
print("   raw abs32 总计 %d 处" % cnt)

print()
print("=" * 74)
print("T3 ★ 用 capstone 精确找 [0xA8B230] 访存（允许前缀/任意 mnemonic）")
print("=" * 74)
MD.detail = True
b = rd(TLO, THI - TLO)
hits = []
for ins in MD.disasm(b, TLO):
    try:
        ops = ins.operands
    except Exception:
        continue
    for op in ops:
        if op.type == 3 and op.mem.disp == 0xA8B230 and op.mem.base == 0 and op.mem.index == 0:
            hits.append((ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex(), op.access))
            break
print("   命中 %d 处（0x55D821/0x55D7D4/0x55D80F/0x55D815 应至少含 4 处）" % len(hits))
for h in hits[:40]:
    print("   %08X  %-18s %-8s %s  access=%s" % h)
