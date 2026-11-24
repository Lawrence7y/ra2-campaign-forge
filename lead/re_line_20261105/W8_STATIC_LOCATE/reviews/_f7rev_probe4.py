# -*- coding: utf-8 -*-
"""F7 独立复核探针 #4（reviews/_f7rev_probe4.py）· 只读
  S  0x83D334/44/50/5C 字符串实字节 + 0x5283D0 头（是否 INI Get-Double）+
     0x6739BF 所在函数真实起点与调用者（裁决 Rules+0x1150 是否 INI 键）
  T  0x65A970（v+0x27C 共享实现）全函数 —— arg2=0xA8EC30 是否被写穿（0xA8EC34 间接写通道）
  U  0x736689 所在函数真实起点 + 调用者（v[265] 派发的实际可达性/条件）
  V  u32(0x7E2668)（0x7E22A4 虚表的 v[241] 槽 —— 0x7E2640 第六虚表归属）
用法: python -I -X utf8 _f7rev_probe4.py > _f7rev4_out.txt 2>&1
"""
import sys, time, struct, bisect
from collections import defaultdict

SWARM = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104"

def P(*a):
    try:
        print(" ".join(str(x) for x in a), flush=True)
    except Exception:
        pass

def D(eng, va, n, title):
    P("-- disasm %08x (%s) --" % (va, title))
    got = eng.disasm(va, n)
    if not got:
        P("  (empty decode)")
    for a, b, m, o in got:
        P("  %08x  %-20s %s %s" % (a, b, m, o))

t0 = time.time()
blob = open(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe", "rb").read()
sys.path.insert(0, SWARM)
from ra2tool import Engine
eng = Engine()
stream = eng.stream
addrs = [i.address for i in stream]
by = eng.by()
tb = blob[eng.TB:eng.TB + eng.TSZ]; TLO = eng.TLO

def raw_rel32(opc, target):
    hits = []; i = 0
    while True:
        i = tb.find(bytes([opc]), i)
        if i < 0:
            break
        rel = struct.unpack_from("<i", tb, i + 1)[0]
        if TLO + i + 5 + rel == target:
            hits.append(TLO + i)
        i += 1
    return hits

P("== S. INI key strings + reader fn ==")
for va in (0x83D334, 0x83D344, 0x83D350, 0x83D35C, 0x83D328):
    P("STR %08x = %r" % (va, eng.rd(va, 32).split(b"\0")[0]))
D(eng, 0x5283D0, 0x50, "0x5283D0 head (Get-Double?)")
P()
D(eng, 0x5276D0, 0x30, "0x5276D0 head (Get-Integer?)")
# find real fstart of the big fn containing 0x6739BF: collect all E8 targets in range
tg = defaultdict(int)
i = 0
while True:
    i = tb.find(b"\xe8", i)
    if i < 0:
        break
    rel = struct.unpack_from("<i", tb, i + 1)[0]
    t = TLO + i + 5 + rel
    if 0x672000 <= t < 0x674500:
        tg[t] += 1
    i += 1
pop = sorted(tg.items(), key=lambda kv: -kv[1])[:8]
P("most-targeted VAs in [0x672000,0x674500) by E8: %s" % [(hex(a), n) for a, n in pop])

P()
P("== T. v+0x27C shared impl 0x65A970 (arg2=0xA8EC30 write-through hunt) ==")
D(eng, 0x65A9C9, 0xD8, "0x65A970 second half (after arg2 load)")

P()
P("== U. enclosing function of 0x736689 ==")
k = bisect.bisect_left(addrs, 0x736689) - 1
fs = None
while k >= 0 and addrs[k] >= 0x736689 - 0x3000:
    mn = by[addrs[k]].mnemonic
    if mn == "int3" or mn.startswith("ret"):
        fs = addrs[k + 1]
        P("heuristic fstart: %08x (boundary %08x %s)" % (fs, addrs[k], mn))
        break
    k -= 1
if fs:
    P("RAW_E8 -> %s: %s" % (hex(fs), [hex(x) for x in raw_rel32(0xE8, fs)]))
    D(eng, fs, 0x40, "enclosing fn head")

P()
P("== V. sixth vtable attribution ==")
P("u32(0x7E2668) = %08x  ; candidate vtable@0x7E22A4 slot241" % eng.u32(0x7E2668))
P("u32(0x7E2640) = %08x  ; slot231 of same vtable" % eng.u32(0x7E2640))
# scan vtable area around 0x7E22A4 for RTTI-adjacent pointers: dump dwords before base
P("dwords [0x7E2294..0x7E22B4):")
for off in range(0x7E2294, 0x7E22B4, 4):
    P("   %08x: %08x" % (off, eng.u32(off)))

P()
P("### F7-REVIEW PROBE4 end %.1fs" % (time.time() - t0))
