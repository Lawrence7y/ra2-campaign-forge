# -*- coding: utf-8 -*-
"""W86 候选2 第二步：maxfps 全局(0x100594E8) 的 xref + getter 0x1001EF70 内部 + 限帧循环。

产出：
  A. 0x1001EF70 / 0x1001EEA0 反汇编全文（段名解析：exe 名 -> ini 段）；
  B. 全文件原始字节搜索 0x100594E8 的 4 字节小端（代码立即数 + 指针），代码命中处反汇编上下文；
  C. timeGetTime 4 个调用点上下文反汇编（找限帧循环与帧计数/上一帧时刻）；
  D. .data 全局 0x100594E4..0x100594F0 邻域布局。
只读磁盘，不启动进程。
"""
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r03\W86_render_channel\bin\ddraw.dll"
pe = pefile.PE(P, fast_load=True)
pe.parse_data_directories()
IB = pe.OPTIONAL_HEADER.ImageBase
d = open(P, "rb").read()
secs = list(pe.sections)
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False

def rva2sec(rva):
    for s in secs:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.Name.rstrip(b"\x00").decode("latin1"), s
    return "?", None

def off2rva(off):
    for s in secs:
        if s.PointerToRawData <= off < s.PointerToRawData + s.SizeOfRawData:
            return s.VirtualAddress + (off - s.PointerToRawData)
    return None

def disasm_range(va, before, after, mark_va=None):
    """反汇编 [va-before, va+after]，返回行列表；mark_va 加标记。"""
    rva = va - IB
    sname, s = rva2sec(rva)
    sec_off = rva - s.VirtualAddress
    start = max(0, sec_off - before)
    chunk = d[s.PointerToRawData + start: s.PointerToRawData + sec_off + after]
    out = []
    for ins in md.disasm(chunk, IB + s.VirtualAddress + start):
        mark = "   <<<" if (mark_va and ins.address == mark_va) else ""
        out.append("  0x%08X  %-20s %s %s%s" % (ins.address, ins.bytes.hex(" "), ins.mnemonic, ins.op_str, mark))
    return out

def str_at(va, maxlen=32):
    for s in secs:
        if s.VirtualAddress <= va - IB < s.VirtualAddress + s.SizeOfRawData:
            o = s.PointerToRawData + ((va - IB) - s.VirtualAddress)
            end = d.find(b"\x00", o)
            if end > o:
                return d[o:end].decode("latin1", "replace")[:maxlen]
    return None

print("=" * 78)
print("A. getter 0x1001EF70（maxfps 的 ini 取值函数）反汇编")
print("-" * 78)
for l in disasm_range(0x1001EF70, 0, 0x140):
    print(l)

print("=" * 78)
print("B. 全局 0x100594E8（maxfps 存储位）全文件 4 字节引用")
print("-" * 78)
pat = struct.pack("<I", 0x100594E8)
hits = []
pos = 0
while True:
    i = d.find(pat, pos)
    if i < 0:
        break
    hits.append(i)
    pos = i + 1
print("命中数 =", len(hits))
for h in hits:
    rva = off2rva(h)
    if rva is None:
        print("  off=0x%06X (raw 区外)" % h)
        continue
    va = IB + rva
    sname, _ = rva2sec(rva)
    print("  off=0x%06X rva=0x%06X va=0x%08X sec=%s" % (h, rva, va, sname))
    if sname in (".text", ".detourc"):
        for l in disasm_range(va, 0x50, 0x50, mark_va=va):
            print(l)

print("=" * 78)
print("C. timeGetTime 4 个调用点上下文（限帧循环候选）")
print("-" * 78)
for site in (0x10006D66, 0x100076B8, 0x10007E6F, 0x10007E89):
    print("--- call [timeGetTime] 返回点 va=0x%08X ---" % site)
    for l in disasm_range(site, 0x60, 0x70, mark_va=site):
        print(l)

print("=" * 78)
print("D. .data 邻域布局 0x100594D4..0x100594F4（当前文件值）")
print("-" * 78)
for va in range(0x100594D4, 0x100594F5, 4):
    rva = va - IB
    sname, s = rva2sec(rva)
    o = s.PointerToRawData + (rva - s.VirtualAddress)
    v = struct.unpack_from("<I", d, o)[0]
    print("  0x%08X  = 0x%08X (%d)" % (va, v, v))
print("\n说明：只读磁盘；未启动游戏、未附加进程、未注入。")
