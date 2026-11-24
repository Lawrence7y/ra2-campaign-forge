# -*- coding: utf-8 -*-
"""V-P03 探针 7（raw）：W4 窗入边全列表 + 0x82A044 引用 + 0x686570/0x52D9A0 head 对齐反汇编"""
import sys, struct
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

eng = Engine()
tb = eng.raw[eng.TB: eng.TB + eng.TSZ]
P = print

# ---- 1. W4 窗口 (0x5BACC0,0x5BB20C] 入边源全列表 ----
P("===== [1] W4 window in-edge sources =====")
srcs = []
for i in range(len(tb) - 6):
    va = eng.TLO + i
    c = tb[i]
    t = None
    if c in (0xE8, 0xE9):
        t = va + 5 + struct.unpack_from("<i", tb, i + 1)[0]
    elif c == 0xEB:
        t = va + 2 + struct.unpack_from("<b", tb, i + 1)[0]
    elif 0x70 <= c <= 0x7F:
        t = va + 2 + struct.unpack_from("<b", tb, i + 1)[0]
    elif c == 0x0F and 0x80 <= tb[i+1] <= 0x8F:
        t = va + 6 + struct.unpack_from("<i", tb, i + 2)[0]
    if t and 0x5BACC0 < t <= 0x5BB20C:
        srcs.append(va)
inside = [v for v in srcs if 0x5BAC60 <= v < 0x5BB290]
outside = [v for v in srcs if v not in inside]
P("total=%d inside_host=%d OUTSIDE_host=%s" % (len(srcs), len(inside), [hex(v) for v in outside]))

# ---- 2. 0x82A044 ('Disconnect_Gracefully') 在 .text 的引用 ----
P("")
P("===== [2] refs of string 0x82A044 in .text =====")
pat = struct.pack("<I", 0x82A044)
refs, i = [], tb.find(pat)
while i >= 0:
    refs.append(eng.TLO + i); i = tb.find(pat, i + 1)
P("dword refs: %s" % [hex(v) for v in refs])
# rel32 引用（mov/push imm32 已覆盖；lea/mov disp32 形态同为 dword）——再补 rip 相对? x86-32 无 rip 相对
for va in refs:
    print("   ctx @0x%x: %s" % (va - 1, eng.rd(va - 1, 8).hex()))

# ---- 3. 0x686570 head 对齐反汇编（head 处 fresh 解码安全） ----
P("")
P("===== [3] 0x686570 disasm (fresh from head) =====")
for a, b, m, o in [(i.address, i.bytes.hex(), i.mnemonic, i.op_str)
                   for i in md.disasm(eng.rd(0x686570, 0x60), 0x686570)]:
    P("    0x%08x  %-18s %s %s" % (a, b, m, o))

# ---- 4. 0x52D9A0 head 反汇编 + 0x52D9C4..0x52DA10 ----
P("")
P("===== [4] 0x52D9A0 head + pre-write block =====")
for i in md.disasm(eng.rd(0x52D9A0, 0x30), 0x52D9A0):
    P("    0x%08x  %-18s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
P("   --- 0x52D9C4..0x52DA10 ---")
for i in md.disasm(eng.rd(0x52D9C4, 0x4C), 0x52D9C4):
    P("    0x%08x  %-18s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))

# ---- 5. 0x52E72 附近上下文（候选 call 0x52D9C9 现场） ----
P("")
P("===== [5] context around 0x52E732 / 0x52E75F =====")
for base in (0x52E720, 0x52E750):
    P("   --- from 0x%x ---" % base)
    for i in md.disasm(eng.rd(base, 0x30), base):
        P("    0x%08x  %-18s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
