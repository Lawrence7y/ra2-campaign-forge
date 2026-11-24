# -*- coding: utf-8 -*-
"""Lead 离线核对：三个候选代理字段的绝对引用位置。

地址口径（这次先声明，避免再踩）：
  0xA8ED50 / 0xB0CE88 / 0x87E8E0 都是**绝对 VA**（不是 RVA），指令里编码的就是这个值。
  ra2bench/gamemd.exe 的 .text：RVA 0x1000 == RawPtr 0x1000 ⇒ .text 内 file_off == RVA。
只读磁盘，不启动任何进程。
"""
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe"
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
d = open(EXE, "rb").read()
secs = {s.Name.rstrip(b"\x00").decode("latin1"): s for s in pe.sections}
t = secs[".text"]
md = Cs(CS_ARCH_X86, CS_MODE_32)

TARGETS = {"0xA8ED50": 0xA8ED50, "0xB0CE88": 0xB0CE88, "0x87E8E0": 0x87E8E0}


def which_section(va):
    rva = va - IB
    for n, s in secs.items():
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            in_raw = (rva - s.VirtualAddress) < s.SizeOfRawData
            return n, in_raw
    return None, False


def decode_refs(target_va, want=10):
    """找指令里编码了 target_va 的位置，并给出覆盖该操作数的指令。"""
    pat = struct.pack("<I", target_va)
    out = []
    i = 0
    while len(out) < want:
        j = d.find(pat, i)
        if j < 0:
            break
        i = j + 1
        if not (t.PointerToRawData <= j < t.PointerToRawData + t.SizeOfRawData):
            continue
        best = None
        for back in range(0, 15):
            s = j - back
            if s < 0:
                continue
            base = IB + s  # .text: VA = ImageBase + file_off
            for ins in md.disasm(d[s:s + 18], base):
                if ins.address <= target_va < ins.address + ins.size:
                    if best is None or back < best[1]:
                        best = (ins, back)
                    break
        if best:
            ins, _ = best
            out.append(ins)
    return out


print("=" * 80)
print("镜像:", EXE.split("\\")[-1], " ImageBase=0x%08X" % IB)
for name, va in TARGETS.items():
    sec, in_raw = which_section(va)
    print("=" * 80)
    print("%s  → 所在节=%s  磁盘有字节=%s" % (name, sec, in_raw))
    refs = decode_refs(va)
    print("  可解码的引用指令数（上限 10）: %d" % len(refs))
    for ins in refs:
        print("    0x%08X  %-22s %s %s" % (ins.address, ins.bytes.hex(" "), ins.mnemonic, ins.op_str))
print("=" * 80)
print("说明：只读磁盘字节；未启动游戏、未 attach。")
