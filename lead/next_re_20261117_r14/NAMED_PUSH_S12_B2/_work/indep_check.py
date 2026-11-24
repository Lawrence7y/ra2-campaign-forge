# -*- coding: utf-8 -*-
"""独立复核：不用 core.py 的任何辅助（自己算 VA->文件偏移），抽查 6 行的关键字节。"""
import struct, sys, pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = []
for s in pe.sections:
    nm = s.Name.rstrip(b"\x00").decode()
    secs.append((nm, IB + s.VirtualAddress, s.Misc_VirtualSize,
                 s.PointerToRawData, s.SizeOfRawData))
raw = open(EXE, "rb").read()


def off(va):
    for nm, v0, vs, pra, rs in secs:
        if v0 <= va < v0 + vs:
            d = va - v0
            if d < rs:
                return pra + d
            return None
    return None


def rd(va, n):
    o = off(va)
    return raw[o:o + n] if o is not None else b""


def u32(va):
    b = rd(va, 4)
    return struct.unpack("<I", b)[0] if len(b) == 4 else None


FAILS = []


def ck(c, m):
    if not c:
        FAILS.append(m)
        print("  [X]", m)


print("== 段表（独立解析）==")
for nm, v0, vs, pra, rs in secs:
    print("  %-8s va=%08X vsize=%X rawptr=%X rawsize=%X" % (nm, v0, vs, pra, rs))

print("\n== ① 槽值必 == entry（独立换算）==")
VT = {"BuildingClass": 0x7E3EBC, "BuildingTypeClass": 0x7E4570,
      "CaptureManagerClass": 0x7E4B40, "FactoryClass": 0x7E88D0}
CASES = [
    ("0044EFB0", "BuildingClass", 0x7E4390, "b0ef4400"),
    ("00453E20", "BuildingClass", 0x7E3ED0, "203e4500"),
    ("00454190", "BuildingClass", 0x7E3ED4, "90414500"),
    ("00456750", "BuildingClass", 0x7E3FEC, "50674500"),
    ("0045E800", "BuildingTypeClass", 0x7E45F0, "00e84500"),
    ("0045E880", "BuildingTypeClass", 0x7E45FC, "80e84500"),
    ("0045EBD0", "BuildingTypeClass", 0x7E45E8, "d0eb4500"),
    ("0045F040", "BuildingTypeClass", 0x7E460C, "40f04500"),
    ("0045FE50", "BuildingTypeClass", 0x7E45D4, "50fe4500"),
    ("00465300", "BuildingTypeClass", 0x7E4588, "00534600"),
    ("004728E0", "CaptureManagerClass", 0x7E4B58, "e0284700"),
    ("004729C0", "CaptureManagerClass", 0x7E4B60, "c0294700"),
    ("004CA3C0", "FactoryClass", 0x7E88E8, "c0a34c00"),
    ("004CA770", "FactoryClass", 0x7E88F0, "70a74c00"),
    ("00705CA0", "BuildingClass", 0x7E42E8, "a05c7000"),
]
for e, cls, slotva, hexs in CASES:
    got = rd(slotva, 4).hex()
    ck(got == hexs, "%s 槽 %08X 字节 %s != %s" % (e, slotva, got, hexs))
    ck(u32(slotva) == int(e, 16), "%s 槽值 != entry" % e)
    ck(u32(VT[cls]) == 0x410260, "%s 主表 slot0 != 410260" % cls)
    col = u32(VT[cls] - 4)
    ck(u32(col) == 0, "%s COL 签名非 0" % cls)

print("  done")

print("\n== ② RTTI 名串（独立读）==")
for cls, td, exp in (("BuildingClass", 0x818D60, ".?AVBuildingClass@@"),
                     ("BuildingTypeClass", 0x8193A8, ".?AVBuildingTypeClass@@"),
                     ("CaptureManagerClass", 0x81B6C8, ".?AVCaptureManagerClass@@"),
                     ("FactoryClass", 0x822290, ".?AVFactoryClass@@")):
    nm = rd(td + 8, 80).split(b"\x00")[0].decode("latin1")
    ck(nm == exp, "%s TD 名 %r != %r" % (cls, nm, exp))
print("  done")

print("\n== ③ 6 行关键字节（独立读）==")
# 00453E20
ck(rd(0x453EB8, 2).hex() == "3bc3", "453EB8 应 3b c3")
ck(rd(0x453EBE, 2).hex() == "0f8c", "453EBE 应 0f 8c")
ck(struct.unpack("<i", rd(0x453EC0, 4))[0] + 0x453EC4 == 0x45417E, "453EBE jl 目标 != 45417E")
ck(rd(0x453E46, 2).hex() == "33db", "453E46 应 33 db")
ck(rd(0x45417E, 1).hex() == "5f", "45417E 应 pop edi(5f)")
ck(rd(0x70C246, 2).hex() == "8bc3", "70C246 应 8b c3")
ck(rd(0x70C24B, 3).hex() == "c20800", "70C24B 应 c2 08 00")
# 00465300
ck(rd(0x465318, 2).hex() == "85c0", "465318 应 85 c0")
ck(rd(0x46531A, 2).hex() == "7c4e", "46531A 应 7c 4e")
ck(struct.unpack("<b", rd(0x46531B, 1))[0] + 0x46531C == 0x46536A, "46531A jl 目标 != 46536A")
ck(rd(0x465368, 2).hex() == "33c0", "465368 应 33 c0")
ck(rd(0x717091, 2).hex() == "33c0", "717091 应 33 c0")
ck(rd(0x717094, 1).hex() == "5f", "717094 应 pop edi")
# 004728E0
ck(rd(0x4728F3, 5).hex() == "e828daf9ff", "4728F3 字节")
ck(0x4728F3 + 5 + struct.unpack("<i", rd(0x4728F4, 4))[0] == 0x410320, "4728F3 call 目标 != 410320")
ck(rd(0x4728F8, 2).hex() == "8bf8", "4728F8 应 8b f8")
ck(rd(0x472900, 1).hex() == "7c", "472900 应 7c")
ck(rd(0x472956, 2).hex() == "8bc7", "472956 应 8b c7")
ck(rd(0x41032B, 5).hex() == "b803400080", "41032B 应 b8 03 40 00 80")
ck(rd(0x410331, 3).hex() == "c20c00", "410331 应 c2 0c 00")
# 004CA3C0
ck(rd(0x4CA3D7, 2).hex() == "85c0", "4CA3D7 应 85 c0")
ck(rd(0x4CA3D9, 2).hex() == "7c44", "4CA3D9 应 7c 44")
ck(rd(0x4CA41D, 2).hex() == "33c0", "4CA41D 应 33 c0")
ck(rd(0x4CA41F, 1).hex() == "5f", "4CA41F 应 pop edi")
# 004729C0
ck(rd(0x4729F3, 3).hex() == "ff5210", "4729F3 应 ff 52 10")
ck(rd(0x4729F6, 2).hex() == "83f8", "4729F6 应 83 f8")
ck(rd(0x4729F9, 2).hex() == "742d", "4729F9 应 74 2d")
ck(struct.unpack("<b", rd(0x4729FA, 1))[0] + 0x4729FB == 0x472A28, "4729F9 je 目标 != 472A28")
ck(rd(0x472FEF, 3).hex() == "83c8ff", "472FEF 应 83 c8 ff")
ck(rd(0x472FF3, 3).hex() == "c20400", "472FF3 应 c2 04 00")
# 004CA770
ck(rd(0x4CA7AA, 3).hex() == "ff5210", "4CA7AA 应 ff 52 10")
ck(rd(0x4CA7AD, 2).hex() == "83f8", "4CA7AD 应 83 f8")
ck(rd(0x4CA7B0, 2).hex() == "742d", "4CA7B0 应 74 2d")
ck(rd(0x4CA803, 3).hex() == "ff5210", "4CA803 应 ff 52 10")
ck(rd(0x4CA806, 2).hex() == "83f8", "4CA806 应 83 f8")
ck(rd(0x4EC2EF, 3).hex() == "83c8ff", "4EC2EF 应 83 c8 ff")
ck(rd(0x4E056F, 3).hex() == "83c8ff", "4E056F 应 83 c8 ff")
print("  done")

print("\n== ④ 8 个构造安装点字节（独立读）==")
for w, vt in ((0x43B71F, 0x7E3EBC), (0x43B9FA, 0x7E3EBC),
              (0x45E2CD, 0x7E4570), (0x45E558, 0x7E4570),
              (0x471807, 0x7E4B40), (0x4718BC, 0x7E4B40),
              (0x4C991A, 0x7E88D0), (0x4CA2C7, 0x7E88D0)):
    b = rd(w, 6)
    ck(b[0] == 0xC7, "安装点 %08X 首字节非 C7" % w)
    ck(struct.unpack("<I", b[2:6])[0] == vt, "安装点 %08X 立即数 != %08X" % (w, vt))
print("  done")

print("\n== 静态初始化器（全局容器）==")
# .text 中 c7 05 <addr> <imm>
rawtext = raw[off(0x401000):off(0x401000) + 0x3E0000]
for g, exp in ((0x89E0F0, 0x7E4AD4), (0xA83E30, 0x7E9FA4), (0xB0F720, 0x7E91EC)):
    needle = b"\xc7\x05" + struct.pack("<I", g)
    i = rawtext.find(needle)
    ck(i >= 0, "%08X 无静态初始化器" % g)
    if i >= 0:
        imm = struct.unpack_from("<I", rawtext, i + 6)[0]
        ck(imm == exp, "%08X 初始化值 %s != %s" % (g, hex(imm), hex(exp)))
        print("    0x%08X @ %08X -> %08X" % (g, 0x401000 + i, imm))
print("  done")

print("\n==== 独立复核：%s（%d 项失败）====" % ("全绿" if not FAILS else "有失败", len(FAILS)))
for f in FAILS:
    print("  -", f)
