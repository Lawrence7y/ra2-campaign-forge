# -*- coding: utf-8 -*-
"""F7 独立复核探针 #5（reviews/_f7rev_probe5.py）· 只读 · 纯字节段，不建流
  W  u32(0x7F0CD4) -> 节名串（PatrolScan 读取的 section 实参）
  X  0x40DD70 —— 是否写穿 arg3(=0xA8EC30) 指针（0xA8EC34 间接写通道裁决）
  Y  0x736689 外层函数起点搜索（0x736540..0x736640 找 prologue）+ E8 调用者
  Z  0x666E09（ctor 双写）外层函数起点 + 头部
用法: python -I -X utf8 _f7rev_probe5.py > _f7rev5_out.txt 2>&1
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

P("== W. section-name arg of PatrolScan reader ==")
secptr = eng.u32(0x7F0CD4)
P("u32(0x7F0CD4) = %08x -> string %r" % (secptr, eng.rd(secptr, 32).split(b"\0")[0]))

P()
P("== X. 0x40DD70 (receives 0xA8EC30 as arg3) ==")
D(eng, 0x40DD70, 0xE0, "0x40DD70 body")

P()
P("== Y. enclosing fn of 0x736689 ==")
D(eng, 0x736580, 0x90, "0x736580..0x736610 (prologue hunt)")

P()
P("== Z. ctor fn of 0x666E09 ==")
D(eng, 0x666DC0, 0x60, "0x666DC0..0x666E20 (ctor context)")

P()
P("### F7-REVIEW PROBE5 end %.1fs" % (time.time() - t0))
