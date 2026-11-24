# -*- coding: utf-8 -*-
"""V-P03 快探针：只用原始字节/PE 头（不建 capstone 流）—— 死代码/空桩/IAT/串/u32"""
import sys, struct
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
P = print
P("[sha] %s.." % eng.sha[:16])
P("[sections]")
for nm, sva, vsz, rp, rsz in eng.SEC:
    P("   %-8s va=[0x%x,0x%x) raw=[0x%x,0x%x)" % (nm, sva, sva + vsz, rp, rp + rsz))

def cstr(va, n=72):
    b = eng.rd(va, n); z = b.find(b"\0")
    return b[:z if z >= 0 else n]

# ---- 空桩 ----
P("[0x4068E0 bytes] %s" % eng.rd(0x4068E0, 16).hex())
P("[0x4068F0 bytes] %s (expect 8b44240c)" % eng.rd(0x4068F0, 4).hex())
P("[0x6B8B10 bytes] %s" % eng.rd(0x6B8B10, 16).hex())

# ---- IAT ----
for va in (0x7E11F0, 0x7E1530, 0x7E14A4):
    P("[IAT 0x%x] = %s" % (va, eng.resolve_iat(va)))

# ---- u32 值 ----
P("[u32 0x7E4C30] = 0x%x" % eng.u32(0x7E4C30))
P("[u32 0xA8E2E4] = %d" % eng.u32(0xA8E2E4))
P("[bytes 0x841F30..] = %s (expect 1234..1237)" % eng.rd(0x841F30, 16).hex())

# ---- 格式串 ----
for va in (0x82CC04, 0x82CBF4, 0x82C9A4, 0x831A60, 0x83DA88, 0x82C1BC, 0x84C540, 0x820C54, 0x81D514, 0x81D53C, 0x81D55C):
    P("[str 0x%x] %r" % (va, cstr(va)))
b85 = eng.raw.find(b"Disconnect_Gracefully")
P("[Disconnect_Gracefully] file_off=%s" % (hex(b85) if b85 >= 0 else "NOT FOUND"))
if b85 >= 0:
    for nm, sva, vsz, rp, rsz in eng.SEC:
        if rp <= b85 < rp + rsz:
            P("   in section %s va=0x%x" % (nm, sva + (b85 - rp)))

# ---- W10 死代码：文件全域 dword 0x7970D0 ----
for val, tag in ((0x7970D0, "W10host"), (0xA8ED84, "CurrentFrame")):
    pat = struct.pack("<I", val)
    occ, i = [], eng.raw.find(pat)
    while i >= 0:
        occ.append(i); i = eng.raw.find(pat, i + 1)
    P("[file-wide dword 0x%x (%s)] total=%d" % (val, tag, len(occ)))
    tlo, thi, tbo = eng.TLO, eng.THI, eng.TB
    out_txt = []
    for off in occ:
        where = None
        if tbo <= off < tbo + eng.TSZ:
            where = ".text@0x%x" % (tlo + off - tbo)
        else:
            for nm, sva, vsz, rp, rsz in eng.SEC:
                if rp <= off < rp + rsz:
                    where = "%s@0x%x" % (nm, sva + off - rp)
        out_txt.append(where)
    from collections import Counter
    P("   by location: %s" % Counter(out_txt))

# W10 宿主范围入边：E8/E9/0F8x/EB 全扫（全 .text）
tb = eng.raw[eng.TB: eng.TB + eng.TSZ]
edges = []
for i in range(len(tb) - 6):
    va = eng.TLO + i
    c = tb[i]
    if c == 0xE8 and i + 5 <= len(tb):
        rel = struct.unpack_from("<i", tb, i + 1)[0]
        if 0x7970D0 <= va + 5 + rel < 0x7975AC: edges.append((hex(va), "E8"))
    elif c == 0xE9 and i + 5 <= len(tb):
        rel = struct.unpack_from("<i", tb, i + 1)[0]
        if 0x7970D0 <= va + 5 + rel < 0x7975AC: edges.append((hex(va), "E9"))
    elif c == 0xEB:
        rel = struct.unpack_from("<b", tb, i + 1)[0]
        if 0x7970D0 <= va + 2 + rel < 0x7975AC: edges.append((hex(va), "EB"))
    elif c == 0x0F and 0x80 <= tb[i+1] <= 0x8F:
        rel = struct.unpack_from("<i", tb, i + 2)[0]
        if 0x7970D0 <= va + 6 + rel < 0x7975AC: edges.append((hex(va), "0F8x"))
P("[static in-edges into [0x7970D0,0x7975AC)] from .text] = %d %s" % (len(edges), edges[:12]))

# ---- jump-table 内容 ----
P("[dwords @0x7975AC x8] %s" % [hex(x) for x in struct.unpack_from("<8I", eng.rd(0x7975AC, 32))])
P("[dwords @0x7975C4 x8] %s" % [hex(x) for x in struct.unpack_from("<8I", eng.rd(0x7975C4, 32))])
P("[W10 host head 0x7970D0] %s" % eng.rd(0x7970D0, 8).hex())
P("[W10 write ctx 0x797541..0x7975A0] %s" % eng.rd(0x797541, 0x60).hex())

# ---- push 0xA8ED84 ----
tb2 = eng.raw[eng.TB: eng.TB + eng.TSZ]
pat = bytes.fromhex("6884eda800")
pp, i = [], tb2.find(pat)
while i >= 0:
    pp.append(hex(eng.TLO + i)); i = tb2.find(pat, i + 1)
P("[push 0xA8ED84 in .text] %s" % pp)

# ---- .text 中 84eda800 计数 ----
pat3 = bytes.fromhex("84eda800")
cnt, i = 0, tb2.find(pat3)
while i >= 0:
    cnt += 1; i = tb2.find(pat3, i + 1)
P("[count 84eda800 in .text] = %d (claim 1009)" % cnt)
