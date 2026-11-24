# -*- coding: utf-8 -*-
"""F6 复核第二件证：RTTI 正确走法 / 0x5F4B13 字节 / Bink 字符串 / 矩阵浮点常量 /
   方向表推进块。只读，stdout 输出，由 shell 重定向落盘。
运行：python -I -X utf8 _f6rev_probe2.py > _f6rev_probe_out2.txt 2>&1
"""
import struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = "D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
raw = open(EXE, "rb").read()
e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e + 6)[0]
optsz = struct.unpack_from("<H", raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", raw, opt + 28)[0]
tab = opt + optsz
SEC = []
for i in range(nsec):
    nm = raw[tab + i*40: tab+i*40+8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i*40 + 8)
    SEC.append((nm, IB + va, vsz, rp, rsz))
def fo(va):
    for nm, sva, vsz, rp, rsz in SEC:
        if sva <= va < sva + vsz:
            o = rp + (va - sva)
            return o if o < rp + rsz else None
    return None
def rd(va, n):
    o = fo(va)
    return raw[o:o+n] if o is not None else b"\x00"*n
def u32(va):
    return struct.unpack_from("<I", rd(va, 4), 0)[0]

print("[R1] MSVC x86 RTTI：[vtable-4] = COL 指针；COL+0x0C = TypeDescriptor")
for vt in (0x7E85D4, 0x7F4348, 0x7F432C, 0x7F4324, 0x7F431C):
    col = u32(vt - 4)
    sig = u32(col)
    td = u32(col + 0x0C)
    name = rd(td + 8, 48).split(b"\x00")[0].decode("latin1", "replace")
    print("vtable 0x%08X  COL=0x%08X sig=%d  TD=0x%08X  name=%r" % (vt, col, sig, td, name))

print("[R2] 0x5F4B05..0x5F4B20 原始字节（验 D-20 所引 0x5F4B13 = mov al,[0xA8ED6B]）")
print(rd(0x5F4B05, 0x1B).hex(" "))

print("[R3] Bink 字符串")
print("str@0x818B2C:", rd(0x818B2C, 24).split(b"\x00")[0])
print("str@0x818B40:", rd(0x818B40, 20).split(b"\x00")[0])

print("[R4] ctor 写入的矩阵常量的浮点值")
for hx, tag in ((0x408888CE, "+0xDE4"), (0x410888CE, "+0xDE8"), (0xC08888CE, "+0xDF4"),
                (0x3F800000, "+0xE0C")):
    print("0x%08X (%s) = %.6f" % (hx, tag, struct.unpack("<f", struct.pack("<I", hx))[0]))
print("256/60=%.4f  256/30=%.4f" % (256/60, 256/30))

print("[R5] 方向表推进块 0x6D85C6..0x6D8630（线性解码）")
md = Cs(CS_ARCH_X86, CS_MODE_32)
for i in md.disasm(rd(0x6D85C6, 0x6A), 0x6D85C6):
    print("%08X  %-20s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
