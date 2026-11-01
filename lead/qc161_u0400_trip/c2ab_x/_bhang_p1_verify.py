# -*- coding: utf-8 -*-
"""_bhang_p1_verify.py — B 线定稿轮只读复核：P1 自旋环与 E3 判读锚地址字节回验。
零真机、零写入、只读母本 gamemd.exe。唯一目的=独立复算 E4 报告钉住的字节锚，
供 LATCHED_HANG_MECHANISM §8 吸收使用。不 import E4 脚本、不改任何现有文件。"""
import struct
import capstone

PATH = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020\gamemd.exe"
BASE = 0x400000

with open(PATH, "rb") as f:
    data = f.read()

e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
nsec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
opt_size = struct.unpack_from("<H", data, e_lfanew + 20)[0]
sec0 = e_lfanew + 24 + opt_size
sections = []
for i in range(nsec):
    off = sec0 + 40 * i
    name = data[off:off + 8].rstrip(b"\0").decode()
    vsize, va, rsize, rptr = struct.unpack_from("<IIII", data, off + 8)
    sections.append((name, va, vsize, rptr, rsize))
image_base = struct.unpack_from("<I", data, e_lfanew + 24 + 28)[0]


def rva2off(rva):
    for name, va, vsize, rptr, rsize in sections:
        if va <= rva < va + max(vsize, rsize):
            return rptr + (rva - va)
    return None


def va2off(va):
    return rva2off(va - image_base)


md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)


def disasm(va_start, va_end, label):
    print("\n=== %s  0x%06X..0x%06X ===" % (label, va_start, va_end))
    off = va2off(va_start)
    if off is None:
        print("  <va 不在任何节内>")
        return
    code = data[off:off + (va_end - va_start)]
    for ins in md.disasm(code, va_start):
        print("  0x%06X: %-22s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))


# A 内部门 0x6BDCFE + 自旋环1 0x6BDD03 + 环间 0x49F620 + 自旋环2 0x6BDD2E
disasm(0x6BDCAC, 0x6BDD3C, "A 内部门→B→自旋环（P1 全段）")

print("\n=== 锚字节回验 ===")
anchors = {
    0x6BDCFE: "call 0x6BEC60 (A→B 唯一门)",
    0x6BDD03: "自旋环1 环头 call 泵",
    0x6BDD08: "自旋环1 泵返回点(读 [0xA8ED80])",
    0x6BDD11: "call 0x49F620",
    0x6BDD16: "环间 0x49F620 返回点",
    0x6BDD2E: "自旋环2 环头 call 泵",
    0x6BDD33: "自旋环2 泵返回点",
    0x6BE0B6: "宿主 A 写闩点",
    0x6BE0DF: "宿主 A bail 环泵返回点",
    0x6BE0E1: "bail 站点 cmp",
    0x6BEC72: "宿主 B 写闩点",
    0x6BEC87: "宿主 B 环头",
    0x6BEC9B: "宿主 B 回边",
    0x6BEC60: "宿主 B 函数头",
}
for va, note in sorted(anchors.items()):
    off = va2off(va)
    b = data[off:off + 10].hex()
    ins = next(md.disasm(data[off:off + 15], va), None)
    s = ("%s %s" % (ins.mnemonic, ins.op_str)) if ins else "?"
    print("  0x%06X  bytes=%s  |  %s  |  %s" % (va, b, s, note))
