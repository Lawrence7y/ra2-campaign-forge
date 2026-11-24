# -*- coding: utf-8 -*-
"""V-P03 核验探针 5（收尾）：MLF 尾对齐/四旗标守卫链 + 0x683AB0 调用者 + push 形态 + 写窗入边 + decoded-call 计数"""
import sys, struct
from collections import defaultdict
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
P = print
S = eng.stream
P("[coverage] %.2f%% / %d / %d" % eng.coverage)

# ---------- H1. MLF 尾部对齐 ----------
P("")
P("===== [H1] MLF 尾 0x55DE40..0x55DE78 字节与两种对齐 =====")
P("[raw] %s" % eng.rd(0x55DE40, 0x38).hex())
P("[engine stream 0x55DE40..0x55DE75]")
for i in S:
    if 0x55DE40 <= i.address < 0x55DE75:
        P("    0x%08x  %-18s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
P("[alt alignment from 0x55DE5F]")
for a, b, m, o in eng.disasm(0x55DE5F, 0x14):
    P("    0x%08x  %-18s %s %s" % (a, b, m, o))

# 四旗标在 MLF 内的 R 命中
hits = eng.disp_hits(0xA8ED84)
for f in (0xA83D49, 0xA8ECD0, 0x8B41C0, 0xA83D48, 0xA83D4C):
    hs = [(hex(a), m, o) for a, d, m, o in eng.disp_hits(f) if 0x55D360 <= a < 0x55DEE0]
    P("[flag 0x%x in MLF] %s" % (f, hs))

# 全 .text 跳到 0x55DEC8 的站点
tb = eng.raw[eng.TB: eng.TB + eng.TSZ]
P("[jumps to 0x55DEC8]")
for i in range(len(tb) - 6):
    va = eng.TLO + i
    c = tb[i]
    if 0x70 <= c <= 0x7F or c == 0xEB:
        rel = struct.unpack_from("<b", tb, i + 1)[0]
        if va + 2 + rel == 0x55DEC8: P("    short 0x%08x op=%02x" % (va, c))
    if c == 0x0F and 0x80 <= tb[i+1] <= 0x8F:
        rel = struct.unpack_from("<i", tb, i + 2)[0]
        if va + 6 + rel == 0x55DEC8: P("    near  0x%08x 0f8%x" % (va, tb[i+1] & 0xF))

# ---------- H2. 0x48CE70..0x48CEC0 dispatcher 循环体 ----------
P("")
P("===== [H2] dispatcher 循环体 0x48CE60..0x48CEC0 =====")
for a, b, m, o in eng.disasm(0x48CE60, 0x60):
    P("    0x%08x  %-18s %s %s" % (a, b, m, o))

# ---------- H3. 0x683AB0 全图调用者 ----------
P("")
P("===== [H3] call 0x683AB0 全图站点 =====")
for i in range(len(tb) - 5):
    va = eng.TLO + i
    if tb[i] == 0xE8:
        rel = struct.unpack_from("<i", tb, i + 1)[0]
        if va + 5 + rel == 0x683AB0:
            P("    call site 0x%08x" % va)

# 0x686570 是否引用 'Disconnect_Gracefully'(0x82A044)
pat = struct.pack("<I", 0x82A044)
seg = eng.rd(0x686570, 0x500)
idx, found = seg.find(pat), []
while idx >= 0:
    found.append(hex(0x686570 + idx)); idx = seg.find(pat, idx + 1)
P("[0x82A044 refs in [0x686570,0x686A70)] = %s" % found)
P("[0x686570 head] %s" % eng.rd(0x686570, 12).hex())

# ---------- H4. push <全局> 形态扫描（hostA/hostB 序列化清单） ----------
P("")
P("===== [H4] push-imm 全局形态（hostA/hostB） =====")
SER = [0xA8ED78, 0xA83D4C, 0xA8ED84, 0x89EA40, 0x89EC28, 0x89ECC0, 0xA8E3A8, 0xB07784]
for lo, hi, tag in ((0x67F7E0, 0x67F9C0, "hostA"), (0x67F9C0, 0x67FD80, "hostB")):
    seg = eng.raw[eng.fo(lo): eng.fo(lo) + (hi - lo)]
    row = {}
    for g in SER:
        pat = b"\x68" + struct.pack("<I", g)
        cnt, j = 0, seg.find(pat)
        while j >= 0:
            cnt += 1; j = seg.find(pat, j + 1)
        row[hex(g)] = cnt
    P("[%s push-imm census] %s" % (tag, row))

# ---------- H5. 写窗入边原始扫描 ----------
P("")
P("===== [H5] 各写点「清零定义→写点」窗口的跳入边（任何一条=绕过清零） =====")
WINDOWS = {
    "W1": (0x52D9C4, 0x52DA08), "W2": (0x55DE73, 0x55DE82), "W4": (0x5BACBE, 0x5BB20C),
    "W5": (0x5E54E5, 0x5E550F), "W7": (0x684669, 0x68466B), "W8": (0x68675F, 0x686765),
    "W10": (0x797541, 0x79758C),
}
for tag, (lo, hi) in WINDOWS.items():
    bad = []
    for i in range(len(tb) - 6):
        va = eng.TLO + i
        c = tb[i]
        t = None
        if c == 0xE8 or c == 0xE9:
            if i + 5 <= len(tb): t = (va + 5 + struct.unpack_from("<i", tb, i + 1)[0], "E8/E9")
        elif c == 0xEB:
            t = (va + 2 + struct.unpack_from("<b", tb, i + 1)[0], "EB")
        elif 0x70 <= c <= 0x7F:
            t = (va + 2 + struct.unpack_from("<b", tb, i + 1)[0], "jcc%02x" % c)
        elif c == 0x0F and 0x80 <= tb[i+1] <= 0x8F:
            if i + 6 <= len(tb): t = (va + 6 + struct.unpack_from("<i", tb, i + 2)[0], "0F8x")
        if t and lo < t[0] <= hi:
            bad.append((hex(va), t[1], hex(t[0])))
    P("[%s] window (0x%x,0x%x] foreign in-edges = %d %s" % (tag, lo, hi, len(bad), bad[:6]))

# ---------- H6. decoded-call 唯一目标数（消解 6719 vs 7279） ----------
P("")
P("===== [H6] E8 头集两种口径 =====")
heads_raw = set()
for i in range(len(tb) - 5):
    if tb[i] == 0xE8:
        va = eng.TLO + i
        t = va + 5 + struct.unpack_from("<i", tb, i + 1)[0]
        if eng.TLO <= t < eng.THI: heads_raw.add(t)
heads_dec = set()
ncalls = 0
for ins in S:
    if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == 2:
        t = ins.operands[0].imm
        if eng.TLO <= t < eng.THI:
            heads_dec.add(t); ncalls += 1
P("[raw E8 byte-scan] unique targets = %d" % len(heads_raw))
P("[decoded call insns] = %d ; unique targets = %d (report claims 6719)" % (ncalls, len(heads_dec)))

# ---------- H7. MLF 读点汇总 ----------
P("")
P("===== [H7] MLF 内 [0xA8ED84] 命中汇总（3R+1W 预期） =====")
P("[MLF 0xA8ED84 hits] %s" % [(hex(a), d, m) for a, d, m, _ in hits if 0x55D360 <= a < 0x55DEE0])
print("DONE5")
