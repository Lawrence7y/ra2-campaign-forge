# -*- coding: utf-8 -*-
"""W86 候选2 前置侦察：ddraw.dll（cnc-ddraw）字符串与导入表侦察。只读磁盘，不启动进程。

产出：
  1. 关键字符串定位（maxfps / d3d9 / Direct3DCreate9 / QueryPerformanceCounter 等）及其 VA/文件偏移；
  2. 导入表（确认后端：d3d9.dll 静态导入 or LoadLibrary 动态串）；
  3. "maxfps" 字符串 VA 的全 .text 立即数引用（xref）位置。
基于 r02 REVIEW/_find_render_counter.py 复制改写（sha256 18017BFB...ACF6C3，已核）。
"""
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM

P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r03\W86_render_channel\bin\ddraw.dll"
pe = pefile.PE(P, fast_load=True)
pe.parse_data_directories()
IB = pe.OPTIONAL_HEADER.ImageBase
d = open(P, "rb").read()
secs = list(pe.sections)

def off2rva(off):
    for s in secs:
        if s.PointerToRawData <= off < s.PointerToRawData + s.SizeOfRawData:
            return s.VirtualAddress + (off - s.PointerToRawData)
    return None

def rva2sec(rva):
    for s in secs:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.Name.rstrip(b"\x00").decode("latin1")
    return "?"

print("=" * 78)
print("ddraw.dll ImageBase=0x%08X  Machine=0x%X" % (IB, pe.FILE_HEADER.Machine))
for s in secs:
    n = s.Name.rstrip(b"\x00").decode("latin1")
    print("  sec %-8s VA=0x%08X raw=0x%X size=%d" % (n, IB + s.VirtualAddress, s.PointerToRawData, s.SizeOfRawData))

print("\n== 导入表 ==")
for e in pe.DIRECTORY_ENTRY_IMPORT:
    dll = e.dll.decode()
    names = [i.name.decode() if i.name else str(i.ordinal) for i in e.imports]
    print("  %s (%d)" % (dll, len(names)))
    if dll.lower() in ("d3d9.dll", "dxgi.dll", "opengl32.dll", "gdi32.dll", "user32.dll", "kernel32.dll"):
        show = [n for n in names if any(k in n.lower() for k in
                ("present", "create", "swap", "queryperf", "loadlib", "getproc", "blt", "flip", "lock", "ddraw"))]
        for n in show[:20]:
            print("     -", n)

print("\n== 关键字符串定位 ==")
needles = [b"maxfps", b"minfps", b"d3d9.dll", b"Direct3DCreate9", b"d3d9", b"QueryPerformanceCounter",
           b"timeGetTime", b"renderer", b"gamemd", b"Direct3D", b"IDirect3D", b"opengl32", b"MaxFPS"]
found = {}
for nd in needles:
    pos = 0
    hits = []
    while True:
        i = d.find(nd, pos)
        if i < 0:
            break
        hits.append(i)
        pos = i + 1
        if len(hits) > 12:
            break
    found[nd] = hits
    for h in hits[:8]:
        rva = off2rva(h)
        va = (IB + rva) if rva is not None else 0
        ctx = d[max(0, h - 8): h + len(nd) + 16]
        print("  %-24s off=0x%06X rva=0x%06X va=0x%08X sec=%-6s ctx=%s"
              % (nd.decode("latin1"), h, rva or 0, va, rva2sec(rva) if rva else "?",
                 "".join(chr(c) if 32 <= c < 127 else "." for c in ctx)))

print("\n== 'maxfps' 字符串 VA 的 .text 立即数引用 ==")
t = next(s for s in secs if s.Name.rstrip(b"\x00") == b".text")
text = d[t.PointerToRawData: t.PointerToRawData + t.SizeOfRawData]
tva = IB + t.VirtualAddress
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
targets = set()
for nd in (b"maxfps", b"minfps", b"renderer", b"tshack"):
    for h in found.get(nd, []):
        rva = off2rva(h)
        if rva is not None:
            targets.add(IB + rva)
print("  目标 VA:", ", ".join("0x%X" % v for v in sorted(targets)))
xrefs = []
for ins in md.disasm(text, tva):
    for op in ins.operands:
        if op.type == X86_OP_IMM and op.imm in targets:
            xrefs.append((ins.address, ins.mnemonic, ins.op_str, ins.bytes.hex(" ")))
            break
print("  xref 数 =", len(xrefs))
for a, m, o, b in xrefs:
    print("  VA 0x%08X  %s  %s %s" % (a, b, m, o))
print("\n说明：只读磁盘；未启动游戏、未附加进程。")
