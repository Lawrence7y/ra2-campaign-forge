# -*- coding: utf-8 -*-
# _p11_supplement2.py — P11 第三轮补充（只读）：落盘内联探针
#  1) .rdata/.data 字符串读取（0x817F18/0x817EDC）
#  2) .text 全量 E8/E9/EB 直入边扫描（六个宿主/桩起点）
#  3) 0x4166C0 的 .rdata/.data dword 引用位（vtable 成员判定）+ AircraftClass vtable 基 0x7E22A4 复核
#  4) 0x4166C0 前置填充与序言、0x5098F0 前置填充/序言/五调用点区间
# 零真机/零采样/零进程 API/本脚本零写盘。
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

PATH = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(PATH, "rb").read()
print("R0 BYTES", len(data))
e = struct.unpack_from("<I", data, 0x3C)[0]
coff = e + 4
nsec = struct.unpack_from("<H", data, coff + 2)[0]
optsize = struct.unpack_from("<H", data, coff + 16)[0]
imagebase = struct.unpack_from("<I", data, coff + 20 + 28)[0]
sec0 = coff + 20 + optsize
secs = []
for i in range(nsec):
    o = sec0 + 40 * i
    nm = data[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
    vsize, va, rsz_, ptr = struct.unpack_from("<IIII", data, o + 8)
    secs.append((nm, imagebase + va, vsize, ptr, rsz_))

def va2off(va):
    for nm, sva, vsz, ptr, rsz in secs:
        if sva <= va < sva + rsz:
            return ptr + (va - sva)
    return None

def u32(va):
    o = va2off(va)
    return None if o is None else struct.unpack_from("<I", data, o)[0]

cs = Cs(CS_ARCH_X86, CS_MODE_32)

print("### 1) 字符串")
for va in (0x817F18, 0x817EDC):
    o = va2off(va)
    end = data.find(b"\0", o, o + 120)
    print("0x%08X %r" % (va, data[o:end].decode("ascii", "replace")))

print("### 2) .text E8/E9/EB 直入边")
svo, vsz, ptr, rsz = [s for s in secs if s[0] == ".text"][0][1:]
targets = {0x4166C0: "stub", 0x416D50: "MISSION_MOVE-sm", 0x4D4DC0: "Foot-v132",
           0x4DDF90: "v150-x4", 0x414A80: "Aircraft-v138", 0x51F330: "Infantry-v266",
           0x50D170: "PickTargetByType", 0x6ED090: "case0-handler", 0x6F0130: "case56-handler"}
hits = 0
for i in range(0, rsz - 5):
    b = data[ptr + i]
    if b in (0xE8, 0xE9):
        rel = struct.unpack_from("<i", data, ptr + i + 1)[0]
        tgt = svo + i + 5 + rel
        if tgt in targets:
            print("E8/E9 0x%08X -> 0x%08X %s" % (svo + i, tgt, targets[tgt]))
            hits += 1
    elif b == 0xEB:
        rel = struct.unpack_from("<b", data, ptr + i + 1)[0]
        tgt = svo + i + 2 + rel
        if tgt in targets:
            print("EB    0x%08X -> 0x%08X %s" % (svo + i, tgt, targets[tgt]))
            hits += 1
print("hits=%d" % hits)

print("### 3) 0x4166C0 的 .rdata/.data dword 引用位")
for tgt in (0x4166C0, 0x416D50, 0x414A80):
    pos = []
    for nm, sva, vsz2, ptr2, rsz2 in secs:
        if nm not in (".rdata", ".data"):
            continue
        for off in range(0, rsz2 - 3, 4):
            if struct.unpack_from("<I", data, ptr2 + off)[0] == tgt:
                pos.append((nm, sva + off))
    print("0x%08X positions=%s" % (tgt, [(nm, hex(p)) for nm, p in pos]))

print("### 3b) AircraftClass vtable 基 0x7E22A4 的 RTTI 复核 + 槽位算术")
col = u32(0x7E22A4 - 4)
print("COL=0x%08X sig=%d td=0x%08X" % (col, u32(col), u32(col + 12)))
o = va2off(u32(col + 12) + 8)
end = data.find(b"\0", o, o + 64)
print("TD name:", data[o:end].decode("ascii", "replace"))
print("entry[0x7E24CC]=0x%08X (slot %d)" % (u32(0x7E24CC), (0x7E24CC - 0x7E22A4) // 4))
print("entry[0x7E24D0]=0x%08X (slot %d)" % (u32(0x7E24D0), (0x7E24D0 - 0x7E22A4) // 4))

print("### 3c) 0x416D50 状态机跳表 0x4172E4（4 条目）")
print("table 0x4172E4:", [hex(u32(0x4172E4 + 4 * k)) for k in range(4)])
print("### 4) 0x4166C0 / 0x5098F0 序言")
for va, n in ((0x4166C0, 0x20), (0x5098F0, 0x18)):
    o = va2off(va)
    print("0x%08X pad_before[-8..-1]=%s" % (va, " ".join("%02x" % data[o - k] for k in range(8, 0, -1))))
    for ins in list(cs.disasm(data[o:o + n], va))[:9]:
        print("   %08x  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
print("5 callers of 0x50D170 within [0x5098F0,0x509F00):",
      all(0x5098F0 <= c < 0x509F00 for c in (0x5099C6, 0x509B7E, 0x509C6E, 0x509D34, 0x509E6B)))
print("DONE")
