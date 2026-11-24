# -*- coding: utf-8 -*-
"""§533 probe A -- MainLogicFrame 0x55D360 全解构：枚举所有「帧不推进」的出口。

只读 ra2youli/gamemd.exe（sha256 钉死）。零真机、零进程、零写入（除 stdout）。

问题：实测「帧号冻结」(0xA8ED84 数千次采样全同) 在二进制上的充要条件是
      「MainLogicFrame 走到 0x55DE7E 之前的某条 ret」。本探针把这条充要条件
      展开成可判定的有限集合：列出函数体内每一条 ret / 尾部 jmp 及其守卫条件。
"""
import hashlib
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

raw = open(EXE, "rb").read()
assert hashlib.sha256(raw).hexdigest() == EXPECT_SHA, "image drift"

# ---- own PE parse ----------------------------------------------------------
e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e + 6)[0]
optsz = struct.unpack_from("<H", raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", raw, opt + 28)[0]
tab = opt + optsz
SEC = []
for i in range(nsec):
    name = raw[tab + i * 40: tab + i * 40 + 8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i * 40 + 8)
    SEC.append((name, IB + va, vsz, rp, rsz))
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


print("E0 sha256 OK; ImageBase=%08X .text=[%08X,%08X)" % (IB, TLO, THI))

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = False

FUNC = 0x55D360
INC_READ = 0x55DE73   # mov edx,[0xA8ED84]
INC_PT = 0x55DE7E     # inc edx
INC_WRITE = 0x55DE81  # mov [0xA8ED84],edx

# 先线性解码一个足够大的窗口，再二分找函数尾
WIN = 0x600
text = rd(FUNC, WIN)
insns = []
for ins in MD.disasm(text, FUNC):
    insns.append((ins.address, ins.size, ins.mnemonic, ins.op_str, ins.bytes.hex()))
print("E1 linear window 0x%X..0x%X decoded %d insns" % (FUNC, FUNC + WIN, len(insns)))
print("E1b last insn @%08X %s %s" % (insns[-1][0], insns[-1][2], insns[-1][3]))

# 确认 inc 三点在位
for va, want in ((INC_READ, "8b15 84eda800".replace(" ", "")),
                 (INC_PT, "42"),
                 (INC_WRITE, "8915 84eda800".replace(" ", ""))):
    got = rd(va, len(want) // 2).hex()
    print("E2 %08X expect=%s got=%s %s" % (va, want, got, "OK" if got == want else "MISMATCH"))

print()
print("=" * 78)
print("FULL DISASSEMBLY 0x%08X ... (window %d bytes)" % (FUNC, WIN))
print("=" * 78)
for a, sz, mn, op, bs in insns:
    mark = ""
    if a == INC_READ:
        mark = "  <<< CurrentFrame READ"
    elif a == INC_PT:
        mark = "  <<< *** CurrentFrame++ ***"
    elif a == INC_WRITE:
        mark = "  <<< CurrentFrame WRITE"
    if mn.startswith("ret"):
        mark += "  <<<<<< EXIT"
    print("%08X  %-24s %-6s %s%s" % (a, bs, mn, op, mark))

print()
print("=" * 78)
print("RET ENUMERATION (function window)")
print("=" * 78)
rets = [x for x in insns if x[2].startswith("ret")]
for a, sz, mn, op, bs in rets:
    print("%08X  %-18s %-6s %s   %s" % (
        a, bs, mn, op,
        "BEFORE INC -> frame will NOT advance" if a < INC_PT else "AFTER INC -> frame advances"))
print("total ret in window: %d ; before INC: %d" % (
    len(rets), sum(1 for r in rets if r[0] < INC_PT)))
