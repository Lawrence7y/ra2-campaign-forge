#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立复算：不依赖 iat_resolve.py 的任何代码，手工写死 RVA 后直接读字节。"""
import struct
b = open(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe", "rb").read()

def hx(o, n):
    return " ".join("%02X" % x for x in b[o:o+n])

# 两个节各自的 RVA->文件偏移 线性映射（写死，不读节表）：
#   .rdata : RVA 0x3E1000 == RawPtr 0x3E1000  => delta 0x0
#   .detour: RVA 0x793000 , RawPtr 0x497000   => delta 0x2FC000
def r2o(rva):
    if 0x3E1000 <= rva < 0x411000:
        return rva
    if 0x793000 <= rva < 0x796000:
        return rva - 0x2FC000
    raise ValueError("unmapped rva 0x%X" % rva)

# KERNEL32 导入描述符位于 RVA 0x7955D4 -> 文件偏移 0x4995D4
print("KERNEL32 IMAGE_IMPORT_DESCRIPTOR @0x4995D4 :", hx(0x4995D4, 20))
d = b[0x4995D4:0x4995D4+20]
oft, tds, fc, namerva, ft = struct.unpack("<IIIII", d)
print("  OriginalFirstThunk=0x%08X TimeDateStamp=0x%08X ForwarderChain=0x%08X NameRVA=0x%08X FirstThunk=0x%08X"
      % (oft, tds, fc, namerva, ft))

for target in (0x3E11C8, 0x3E11CC):
    idx = (target - ft) // 4
    int_ent = oft + 4 * idx          # INT/ILT 条目 RVA（与 IAT 同序）
    o_int = r2o(int_ent)
    pin = struct.unpack_from("<I", b, o_int)[0]
    val = struct.unpack_from("<I", b, target)[0]
    o_nm = r2o(pin)
    hint = struct.unpack_from("<H", b, o_nm)[0]
    name = b[o_nm+2:b.index(b"\0", o_nm+2)].decode("latin1")
    print()
    print("--- IAT 槽 RVA=0x%08X ---" % target)
    print("  槽序号 idx = (0x%08X-0x%08X)/4 = %d" % (target, ft, idx))
    print("  IAT 槽原始字节 @off 0x%X : %s   (=0x%08X 已绑定)" % (target, hx(target, 4), val))
    print("  INT 条目 RVA=0x%08X off=0x%X  原始字节: %s" % (int_ent, o_int, hx(o_int, 4)))
    print("  IMAGE_IMPORT_BY_NAME RVA = 0x%08X  off=0x%X" % (pin, o_nm))
    print("  Hint/Name 原始字节 @off 0x%X: %s" % (o_nm, hx(o_nm, 2 + len(name) + 1)))
    print("  Hint = %d (0x%X)   名字(逐字) = \"%s\"" % (hint, hint, name))

# 正控旁证：逐字符串走一段 ILT，看连续性
print()
print("--- KERNEL32 ILT 连续切片 RVA 0x7931E0..0x793230 (off 0x4971E0) ---")
print(hx(0x4971E0, 80))
print("--- 对应名字区 off 0x4981E0..0x498230 ---")
print(b[0x4981E0:0x498230].decode("latin1").replace("\0", " | "))
