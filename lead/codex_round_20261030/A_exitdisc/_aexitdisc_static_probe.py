# -*- coding: utf-8 -*-
"""A 线·退出判别设计 静态探针（只读）。
对象：ra2youli/gamemd.exe（sha256 73201cc0…，本线 2026-10-30 亲算命中）。
用途：为「已闩未退 vs 不闩未退」判别设计的被动只读观测点清单提供字节级证据。
零写盘（除本文件自身）；零真机；零注入。
"""
import pefile
import capstone
import struct
import sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
print("ImageBase=0x%X  Machine=0x%X" % (base, pe.FILE_HEADER.Machine))

secs = []
for s in pe.sections:
    secs.append((s.Name.decode().rstrip("\x00"), s.VirtualAddress, s.Misc_VirtualSize,
                 s.PointerToRawData, s.SizeOfRawData, s.Characteristics))
for nm, va, vsz, rp, rsz, ch in secs:
    print("SEC %-8s VA=0x%08X VSize=0x%X raw=0x%X rawsz=0x%X chr=0x%08X%s" %
          (nm, base + va, vsz, rp, rsz, ch, "  [BSS-like: rawsz<VSize]" if rsz < vsz else ""))

SEC_BY_NAME = {nm: (va, vsz, rp, rsz) for nm, va, vsz, rp, rsz, ch in secs}

data = open(EXE, "rb").read()

def va2off(va):
    rva = va - base
    for nm, sva, vsz, rp, rsz, ch in secs:
        if sva <= rva < sva + max(vsz, rsz):
            off = rp + (rva - sva)
            if off < rp + rsz:
                return off, nm
            return None, nm + "(bss/virtual-only)"
    return None, None

def dump(va, n, label):
    off, sec = va2off(va)
    if off is None:
        print("\n[%s] VA=0x%08X sec=%s — 无文件镜像字节（BSS/虚拟）" % (label, va, sec))
        return b""
    b = data[off:off + n]
    print("\n[%s] VA=0x%08X sec=%s off=0x%X" % (label, va, sec, off))
    print("  bytes:", b.hex(" "))
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    for ins in md.disasm(b, va):
        print("  0x%08X: %-24s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    return b

# ---- 1. 焦点旗标 [0xA8ED80] 唯一写式 + 去重门 + WM_SYSCOMMAND 位写者（R-063a 钉点复验）----
dump(0x777860, 0x80, "WndProc 焦点块 0x777860..0x7778E0（含 0x777874/0x777880/0x7778BF/0x7778CE）")
# ---- 2. exitstate 写 2 站点 0x777818 ----
dump(0x777800, 0x40, "WndProc C 块 0x777800..0x777840（含 0x777818 写 2）")
# ---- 3. 宿主 A 门+自旋环（0x6BDCFE 门 / 0x6BDD03、0x6BDD2E 环 / 0x6BDD08、0x6BDD33 旗标读）----
dump(0x6BDCF0, 0x60, "A 门+自旋环1 0x6BDCF0..0x6BDD50")
# ---- 4. 闩写点 0x6BE0B6 + hook6 站点 0x6BE0E1 ----
dump(0x6BE0A8, 0x50, "A 退出序列 0x6BE0A8..0x6BE0F8（闩写 0x6BE0B6 / BAIL_SITE 0x6BE0E1）")
# ---- 5. 宿主 B 头/环/闩写 0x6BEC60..0x6BEC9B ----
dump(0x6BEC60, 0x48, "宿主 B 0x6BEC60..0x6BECA8（B 头 hwnd 读 / 0x6BEC72 闩写 / B 环）")
# ---- 6. 0x759200 泵（[0xAA0430] 无条件 +1 候选写者）----
dump(0x7591F0, 0x30, "0x7591F0..0x759220（0x759200 泵计数写者）")
# ---- 7. 主泵 0x5D4D50 头（hwnd==0 短路）----
dump(0x5D4D50, 0x28, "主泵 0x5D4D50..0x5D4D78")

# ---- 8. 全 .text 扫描六地址引用，按前导操作码分类 ----
TARGETS = {
    "0xA8EDD8(exitstate闩)": bytes.fromhex("d8eda800"),
    "0xA8ED80(focus旗标)":    bytes.fromhex("80eda800"),
    "0xA8ED81(SYSCOMMAND位)": bytes.fromhex("81eda800"),
    "0xA8ED84(frame)":        bytes.fromhex("84eda800"),
    "0xAA0430(泵计数)":       bytes.fromhex("3004aa00"),
    "0xB73550(主窗hwnd)":     bytes.fromhex("5035b700"),
}
CLASSES = [
    (b"\xc6\x05", "c6 05 = mov BYTE ptr [m],imm8  (写字节)"),
    (b"\xc7\x05", "c7 05 = mov DWORD ptr [m],imm32 (写双字)"),
    (b"\xff\x05", "ff 05 = inc DWORD ptr [m]  (无条件+1)"),
    (b"\xff\x0d", "ff 0d = dec DWORD ptr [m]"),
    (b"\x88",     "88 = mov [m],r8  (写字节)"),
    (b"\x89",     "89 = mov [m],r32 (写双字)"),
    (b"\x8a",     "8a = mov r8,[m]  (读字节)"),
    (b"\x8b",     "8b = mov r32,[m] (读双字)"),
    (b"\xa2",     "a2 = mov BYTE ptr [m],al"),
    (b"\xa3",     "a3 = mov DWORD ptr [m],eax"),
    (b"\xa0",     "a0 = mov al,[m]  (读字节)"),
    (b"\xa1",     "a1 = mov eax,[m] (读双字)"),
    (b"\x3b",     "3b = cmp r,[m]"),
    (b"\x3d",     "3d = cmp eax,imm"),
    (b"\x39",     "39 = cmp [m],r"),
    (b"\x3a",     "3a = cmp r8,[m]"),
    (b"\x83",     "83 = cmp/sub [m],imm8"),
    (b"\x80",     "80 = cmp/test byte [m],imm8"),
    (b"\xf7",     "f7 = test/neg [m],imm32"),
    (b"\x85",     "85 = test [m],r"),
    (b"\x8d",     "8d = lea"),
]

def classify(ctx):
    for pat, desc in CLASSES:
        if ctx.startswith(pat):
            return desc
    return "??未分类"

tsec = SEC_BY_NAME.get(".text")
if tsec:
    sva, vsz, rp, rsz = tsec
    text = data[rp:rp + rsz]
    print("\n.text 文件镜像长度=0x%X（VA 0x%X..0x%X）" % (rsz, base + sva, base + sva + rsz))
    for label, pat in TARGETS.items():
        hits = []
        i = text.find(pat)
        while i != -1:
            va = base + sva + i
            ctx = text[max(0, i - 6):i]
            hits.append((va, ctx))
            i = text.find(pat, i + 1)
        print("\n== %s ：.text 命中 %d 处" % (label, len(hits)))
        for va, ctx in hits:
            print("  VA=0x%08X  前 6 字节=%s  → %s" % (va, ctx.hex(" "), classify(ctx)))

# ---- 9. 0xAA0430 所在段（BSS 判定）----
off, sec = va2off(0xAA0430)
print("\n0xAA0430 → 段=%s off=%s（off=None ⇒ 无文件镜像=BSS，初值 0）" % (sec, hex(off) if off is not None else None))
for nm in (".data", ".bss"):
    if nm in SEC_BY_NAME:
        sva, vsz, rp, rsz = SEC_BY_NAME[nm]
        inb = sva <= (0xAA0430 - base) < sva + vsz
        print("  %s: VA 0x%X..0x%X rawsz=0x%X %s" % (nm, base + sva, base + sva + vsz, rsz,
              "← 0xAA0430 落此段" if inb else ""))
