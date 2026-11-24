# -*- coding: utf-8 -*-
"""W86 候选2 主脚本：定位 cnc-ddraw 的 maxfps 解析表与限帧判断代码。

方法（修正 r02 失败的方法论：线性 sweep 会因数据嵌入失步漏指令，改用原始字节搜索）：
  1. 全文件原始字节搜索 "maxfps" 字符串 VA(0x10048298) 的 4 字节小端立即数 ——
     同时覆盖 代码立即数 与 指针表条目（settings 表）；
  2. 对每个命中给出 节/文件偏移/RVA/VA 与上下文（指针表 vs 代码）；
  3. 若命中指针表：解析表结构（name 指针 -> 后随字段），找到 maxfps 对应的
     struct 偏移（这是 ReadProcessMemory 读目标的候选）；
  4. 对代码命中处反汇编上下文（±0x60），定位解析值存储与限帧判断；
  5. 搜索 QueryPerformanceCounter / timeGetTime 的 IAT 槽与 call [IAT] 点，
     与 maxfps 代码命中做邻近性分析（限帧循环必含取时刻）。
只读磁盘，不启动进程。
"""
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_INVALID

P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r03\W86_render_channel\bin\ddraw.dll"
pe = pefile.PE(P, fast_load=True)
pe.parse_data_directories()
IB = pe.OPTIONAL_HEADER.ImageBase
d = open(P, "rb").read()
secs = list(pe.sections)

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

MAXFPS_VA = 0x10048298          # "maxfps" 键名字符串（侦察脚本实测）
MINFPS_VA = 0x10048414
pat = struct.pack("<I", MAXFPS_VA)
print("=" * 78)
print("搜索立即数/指针 0x%08X（%d 字节模式 %s）" % (MAXFPS_VA, len(pat), pat.hex()))
hits = []
pos = 0
while True:
    i = d.find(pat, pos)
    if i < 0:
        break
    hits.append(i)
    pos = i + 1
print("命中数 =", len(hits))
code_hits = []
data_hits = []
for h in hits:
    rva = off2rva(h)
    if rva is None:
        print("  off=0x%06X  (不在任何节的 raw 区)" % h)
        continue
    va = IB + rva
    sname, _ = rva2sec(rva)
    va_off = rva - (IB + 0)  # rva
    ctx = d[max(0, h - 24): h + 28]
    print("  off=0x%06X rva=0x%06X va=0x%08X sec=%-8s ctx=%s"
          % (h, rva, va, sname, ctx.hex(" ")))
    (code_hits if sname in (".text", ".detourc") else data_hits).append((h, rva, va, sname))

print("\n== .data/.rdata 指针表命中上下文解码（找 settings 表结构）==")
# settings 表通常形如 {ptr name; ptr value/offset; int type}。解码命中前后各 3 个 dword。
for (h, rva, va, sname) in data_hits:
    print("--- 命中 va=0x%08X (%s) ---" % (va, sname))
    base = h - (h % 4)
    for k in range(-3, 4):
        o = base + k * 4
        if o < 0 or o + 4 > len(d):
            continue
        v = struct.unpack_from("<I", d, o)[0]
        tag = ""
        if 0x10040000 <= v < 0x10053000:  # rdata 字符串区
            s2 = d[d.find(b"\x00", 0):0]  # placeholder
            end = d.find(b"\x00", o + 0)  # not meaningful; decode target string
            toff = None
            for s in secs:
                if s.VirtualAddress <= (v - IB) < s.VirtualAddress + s.SizeOfRawData:
                    toff = s.PointerToRawData + ((v - IB) - s.VirtualAddress)
                    break
            if toff is not None:
                end = d.find(b"\x00", toff)
                tag = '-> "%s"' % d[toff:end].decode("latin1", "replace")
        mark = "  <== maxfps" if o == h else ""
        print("    va=0x%08X  dword=0x%08X%s %s" % (IB + off2rva(o), v, tag, mark))

print("\n== 代码命中处反汇编上下文 ==")
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
for (h, rva, va, sname) in code_hits:
    s = rva2sec(rva)[1]
    sec_off = rva - s.VirtualAddress
    start = max(0, sec_off - 0x60)
    chunk = d[s.PointerToRawData + start: s.PointerToRawData + sec_off + 0x60]
    print("--- 代码命中 va=0x%08X (%s) ---" % (va, sname))
    for ins in md.disasm(chunk, IB + s.VirtualAddress + start):
        mark = "   <==== 命中" if ins.address == va else ""
        print("  0x%08X  %-22s %s %s%s" % (ins.address, ins.bytes.hex(" "), ins.mnemonic, ins.op_str, mark))

print("\n== IAT: QueryPerformanceCounter / timeGetTime 槽与调用点 ==")
qpc_slot = tgt_slot = None
for e in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in e.imports:
        if imp.name == b"QueryPerformanceCounter":
            qpc_slot = imp.address
        if imp.name == b"timeGetTime":
            tgt_slot = imp.address
print("  QPC IAT slot = 0x%08X   timeGetTime IAT slot = 0x%08X" % (qpc_slot or 0, tgt_slot or 0))
qpc_calls, tgt_calls = [], []
for sname in (".text", ".detourc"):
    s = next(x for x in secs if x.Name.rstrip(b"\x00").decode() == sname)
    chunk = d[s.PointerToRawData: s.PointerToRawData + s.SizeOfRawData]
    for ins in md.disasm(chunk, IB + s.VirtualAddress):
        if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_MEM:
            m = ins.operands[0].mem
            if m.base == X86_REG_INVALID and m.index == X86_REG_INVALID:
                if qpc_slot and m.disp == qpc_slot:
                    qpc_calls.append(ins.address)
                if tgt_slot and m.disp == tgt_slot:
                    tgt_calls.append(ins.address)
print("  call [QPC]  点数=%d : %s" % (len(qpc_calls), " ".join("0x%X" % a for a in qpc_calls[:20])))
print("  call [timeGetTime] 点数=%d : %s" % (len(tgt_calls), " ".join("0x%X" % a for a in tgt_calls[:20])))
if code_hits:
    for (h, rva, va, sn) in code_hits:
        near_q = min((abs(c - va), c) for c in qpc_calls) if qpc_calls else None
        near_t = min((abs(c - va), c) for c in tgt_calls) if tgt_calls else None
        print("  maxfps 代码命中 va=0x%08X 最近 call[QPC]=%s 最近 call[timeGetTime]=%s"
              % (va,
                 ("0x%X d=%d" % (near_q[1], near_q[0])) if near_q else "-",
                 ("0x%X d=%d" % (near_t[1], near_t[0])) if near_t else "-"))
print("\n说明：只读磁盘；未启动游戏、未附加进程、未注入。")
