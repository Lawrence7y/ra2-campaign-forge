# -*- coding: utf-8 -*-
"""F7 独立复核探针 #6（reviews/_f7rev_probe6.py）· 只读 · 纯字节段
  AA  0x40DD70 的 15 项跳转表逐项反汇编 —— 是否存在写穿 arg3(0xA8EC30) 的 case
  AB  0x736689 外层函数起点（0x7364A0..0x7365A0 对齐解码找 prologue）+ E8 扫描
用法: python -I -X utf8 _f7rev_probe6.py > _f7rev6_out.txt 2>&1
"""
import sys, time, struct

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
tb = blob[eng.TB:eng.TB + eng.TSZ]; TLO = eng.TBO if hasattr(eng, "TBO") else eng.TLO

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

P("== AA. 0x40DD70 jump table ==")
tbl = 0x40DD9C
targets = set()
for k in range(15):
    t = eng.u32(tbl + k * 4)
    targets.add(t)
    P("case %d -> %08x" % (k, t))
for t in sorted(targets):
    D(eng, t, 0x40, "case handler %08x" % t)

P()
P("== AB. enclosing fn start of 0x736689 ==")
D(eng, 0x7364E0, 0xB0, "0x7364E0..0x736590 aligned hunt")
for cand in (0x7364E0, 0x736510, 0x736540, 0x736560):
    hits = raw_rel32(0xE8, cand)
    if hits:
        P("E8 callers of %08x: %s" % (cand, [hex(x) for x in hits]))

P()
P("### F7-REVIEW PROBE6 end %.1fs" % (time.time() - t0))
