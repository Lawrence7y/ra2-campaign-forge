# -*- coding: utf-8 -*-
"""F7 独立复核探针 #7（reviews/_f7rev_probe7.py）· 只读 · 纯字节段
  AB2 0x736689 外层函数起点（0x7364A0..0x7365A0）+ E8 扫描
  AC  0x0065A970 全文件 dword 引用（v159 共享实现被多少虚表引用）
用法: python -I -X utf8 _f7rev_probe7.py > _f7rev7_out.txt 2>&1
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

P("== AB2. enclosing fn start of 0x736689 ==")
D(eng, 0x7364A0, 0xE8, "0x7364A0..0x736588")
for cand in (0x7364A0, 0x7364C0, 0x7364D0, 0x7364F0, 0x736500, 0x736510,
             0x736520, 0x736530, 0x736540, 0x736550, 0x736560, 0x736570):
    hits = raw_rel32(0xE8, cand)
    if hits:
        P("E8 callers of %08x: %s" % (cand, [hex(x) for x in hits]))

P()
P("== AC. whole-file dword refs to 0x0065A970 ==")
pat = struct.pack("<I", 0x65A970)
i = blob.find(pat)
while i >= 0:
    va = None
    for nm, sv, vsz, rp, rsz in eng.SEC:
        if rp <= i < rp + rsz:
            va = sv + (i - rp); break
    P("   file_off=%08x VA=%s" % (i, hex(va) if va else "<none>"))
    i = blob.find(pat, i + 1)

P()
P("### F7-REVIEW PROBE7 end %.1fs" % (time.time() - t0))
