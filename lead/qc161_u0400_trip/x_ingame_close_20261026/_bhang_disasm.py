# -*- coding: utf-8 -*-
"""_bhang_disasm.py — B 线离线反汇编：0x6BEC72（第二写 1 点）与 0x6BE074 宿主上下文。
只读母本 gamemd.exe（sha256 前缀 73201cc021497c95 已验），零写入零发射。
"""
import capstone
import struct

PATH = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020\gamemd.exe"
BASE = 0x400000

with open(PATH, "rb") as f:
    data = f.read()

# PE 解析：节表 → RVA↔file offset
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
    print("sec %-8s va=0x%x vsize=0x%x raw=0x%x rsize=0x%x" % (name, va, vsize, rptr, rsize))

image_base = struct.unpack_from("<I", data, e_lfanew + 24 + 28)[0]
print("image_base=0x%x" % image_base)


def rva2off(rva):
    for name, va, vsize, rptr, rsize in sections:
        if va <= rva < va + max(vsize, rsize):
            return rptr + (rva - va)
    return None


def va2off(va):
    return rva2off(va - image_base)


md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False


def disasm(va_start, va_end, label):
    print("\n=== %s  0x%06X..0x%06X ===" % (label, va_start, va_end))
    off = va2off(va_start)
    if off is None:
        print("  <va 不在任何节内>")
        return
    code = data[off:off + (va_end - va_start)]
    for ins in md.disasm(code, va_start):
        print("  0x%06X: %-22s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))


# 宿主函数 0x6BE074（X_CONTROL_DESIGN §1b-B）+ 泵回边 + teardown 路径 A 起始
disasm(0x6BE074, 0x6BE100, "退出宿主 0x6BE074 起（写1@0x6BE0B6/泵环/出环0x6BE0E9/teardown A）")
# 第二写 1 点 0x6BEC72 前后 0xB0 字节
disasm(0x6BEC00, 0x6BECB0, "第二写 1 点 0x6BEC72 上下文")
# WM_DESTROY 块（§1b-C 参照复核）
disasm(0x7777F3, 0x777828, "WM_DESTROY 块 0x7777F3")

print("\n" + "=" * 70)
print("扩展：teardown A 链（0x6BE0E9 起 +0x90）与 teardown B 链（0x6BEC9D 起 +0x80）")
disasm(0x6BE0E9, 0x6BE180, "teardown A 链")
disasm(0x6BEC9D, 0x6BED20, "teardown B 链")

# 0x7E1144 / 0x7E14AC / 0x7E1384 的 import 名
print("\n=== import 表定位 0x7E1144/0x7E14AC/0x7E1384 ===")
opt_off = e_lfanew + 24
num_dd = struct.unpack_from("<I", data, opt_off + 92)[0]
imp_rva, imp_size = struct.unpack_from("<II", data, opt_off + 96 + 8)  # 数据目录第 2 项=import
print("import dir rva=0x%x size=0x%x" % (imp_rva, imp_size))
off = rva2off(imp_rva)
targets = {0x7E1144, 0x7E14AC, 0x7E1384, 0x7E15DC, 0x7E15D0}
for _ in range(imp_size // 20):
    oft, tds, fwc, name_rva, ft = struct.unpack_from("<IIIII", data, off)
    off += 20
    if name_rva == 0 or ft == 0:
        continue
    dll = data[rva2off(name_rva):rva2off(name_rva) + 64].split(b"\0")[0].decode(errors="replace")
    thunk_rva = ft
    idx = 0
    while True:
        val = struct.unpack_from("<I", data, rva2off(thunk_rva + 4 * idx))[0]
        if val == 0:
            break
        if not (val & 0x80000000):
            fname_off = rva2off(val)
            if fname_off:
                fname = data[fname_off + 2:fname_off + 2 + 96].split(b"\0")[0].decode(errors="replace")
                va_here = image_base + thunk_rva + 4 * idx
                if va_here in targets:
                    print("  [0x%X] = %s!%s" % (va_here, dll, fname))
        idx += 1
