# -*- coding: utf-8 -*-
"""W86 候选2 收尾：限帧全链闭环。
  A. IAT 槽位名（0x1003E244 / 0x1003E0F0 / 0x1003E0EC / 0x1003E3E8 / 0x1003E254）
  B. 全局 0x1005F120 / 0x1005F124 / 0x1005F128 / 0x1005F130 / 0x1005F138 / 0x1005EE48 的全文件引用
  C. 函数 0x10006AE0 / 0x10006880 / 0x10006DC0 的调用者（搜 call rel32 目标）
  D. DllCharacteristics（ASLR 判定）+ 浮点常量 0x1004F9A0
只读磁盘。
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

print("=" * 78)
print("D0. DllCharacteristics = 0x%04X  (DYNAMICBASE=0x40, NX_COMPAT=0x100)"
      % pe.OPTIONAL_HEADER.DllCharacteristics)

print("=" * 78)
print("A. IAT 槽位名")
slot_names = {}
for e in pe.DIRECTORY_ENTRY_IMPORT:
    for imp in e.imports:
        slot_names[imp.address] = "%s!%s" % (e.dll.decode(), imp.name.decode())
for slot in (0x1003E244, 0x1003E0F0, 0x1003E0EC, 0x1003E3E8, 0x1003E254):
    print("  0x%08X = %s" % (slot, slot_names.get(slot, "?")))

def raw_refs(va):
    pat = struct.pack("<I", va)
    out, pos = [], 0
    while True:
        i = d.find(pat, pos)
        if i < 0:
            break
        out.append(i)
        pos = i + 1
    return out

def code_ctx(va, before=0x40, after=0x40, mark=True):
    rva = va - IB
    sname, s = rva2sec(rva)
    if sname not in (".text", ".detourc"):
        return []
    sec_off = rva - s.VirtualAddress
    start = max(0, sec_off - before)
    chunk = d[s.PointerToRawData + start: s.PointerToRawData + sec_off + after]
    lines = []
    for ins in md.disasm(chunk, IB + s.VirtualAddress + start):
        m = "   <<<" if mark and ins.address == va else ""
        lines.append("  0x%08X  %-20s %s %s%s" % (ins.address, ins.bytes.hex(" "), ins.mnemonic, ins.op_str, m))
    return lines

print("=" * 78)
print("B. 关键全局的引用")
for gva, label in ((0x1005F120, "上一帧时刻 last_t"), (0x1005F124, "本帧时刻 cur_t"),
                   (0x1005F128, "帧间隔 interval"), (0x1005F130, "interval double"),
                   (0x1005F138, "aux"), (0x1005EE48, "clamp 上限"),
                   (0x100594EC, "maxfps 后邻键(默认1)"), (0x100594E4, "vsync 邻键")):
    refs = raw_refs(gva)
    code = []
    for h in refs:
        rva = off2rva(h)
        if rva is None:
            continue
        v = IB + rva
        sn, _ = rva2sec(v - IB)
        if sn in (".text", ".detourc"):
            code.append(v)
    print("--- 0x%08X %s : 引用 %d 处, 代码 %s ---" % (gva, label, len(refs),
          " ".join("0x%X" % c for c in code)))
    for c in code:
        for l in code_ctx(c, 0x30, 0x30):
            print(l)

print("=" * 78)
print("C. 函数调用者（call rel32 目标搜索）")
targets = {0x10006AE0: "frame_gate", 0x10006880: "limiter_init", 0x10006DC0: "inc[ecx+4]_fn",
           0x1001EF70: "ini_getint_maxfps"}
text = next(s for s in secs if s.Name.rstrip(b"\x00") == b".text")
tchunk = d[text.PointerToRawData: text.PointerToRawData + text.SizeOfRawData]
tva = IB + text.VirtualAddress
callers = {t: [] for t in targets}
for ins in md.disasm(tchunk, tva):
    if ins.mnemonic == "call" and ins.op_str.startswith("0x"):
        tgt = int(ins.op_str, 16)
        if tgt in callers:
            callers[tgt].append(ins.address)
for t, name in targets.items():
    print("--- 0x%08X %s : %d 个 call 点 ---" % (t, name, len(callers[t])))
    for c in callers[t][:12]:
        print("    from 0x%08X" % c)

print("=" * 78)
print("D. 浮点常量 0x1004F9A0")
rva = 0x1004F9A0 - IB
sn, s = rva2sec(rva)
o = s.PointerToRawData + (rva - s.VirtualAddress)
f = struct.unpack_from("<f", d, o)[0]
print("  [0x1004F9A0] float = %r" % f)
print("\n说明：只读磁盘；未启动游戏、未附加进程、未注入。")
