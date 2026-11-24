# -*- coding: utf-8 -*-
"""F7 独立复核探针 #2（reviews/_f7rev_probe2.py）· 只读
补漏:
  I   disp_hits_field(0x1150) —— F7 声称「全镜像 [reg+0x1150] 写点恰 1 处（构造器）」
  J   0x740BED and ecx,7 上下文（F7 补跑声称：属另一函数、表索引 add/jmp [ecx*4+0x89F688]）
  K   push 0xa8ec30 三站点（0x65aaab/0x65acc3/0x65ad05）——被调者是否经寄存器写 [arg+4]=0xA8EC34
      （F7/卡片未覆盖的间接写通道反例狩猎）
  L   inc [0xa8e7ac] @0x52e0be 上下文分类
  M   E8 -> 0x736664（v[265] 派发宿主自身的调用者）+ 0x736664 全文件 dword 引用
用法: python -I -X utf8 _f7rev_probe2.py > _f7rev2_out.txt 2>&1
"""
import sys, time, struct
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

P("== I. disp_hits_field(0x1150) ==")
try:
    hits = eng.disp_hits_field(0x1150)
    P("count=%d" % len(hits))
    for h in hits:
        P("   %s" % (h,))
except Exception as e:
    P("disp_hits_field failed: %r" % e)

P()
P("== J. 0x740BED region ==")
for anchor in (0x740BC0, 0x740BE0, 0x740BE8):
    got = eng.disasm(anchor, 0x40)
    if got:
        D(eng, anchor, 0x40, "anchor %08x" % anchor)
        break
    else:
        P("anchor %08x: empty" % anchor)

P()
P("== K. push 0xa8ec30 sites ==")
D(eng, 0x65AA80, 0xA0, "0x65aaab context")
P()
D(eng, 0x65AC90, 0x90, "0x65acc3/0x65ad05 context")

P()
P("== L. inc [0xa8e7ac] @0x52e0be context ==")
D(eng, 0x52E0A0, 0x50, "0x52e0be context")

P()
P("== M. who calls v265-dispatch host 0x736664 ==")
tb = blob[eng.TB:eng.TB + eng.TSZ]; TLO = eng.TLO
def raw_rel(opc, target):
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
P("RAW_E8 -> 0x736664: %s" % [hex(x) for x in raw_rel(0xE8, 0x736664)])
P("RAW_E9 -> 0x736664: %s" % [hex(x) for x in raw_rel(0xE9, 0x736664)])
pat = struct.pack("<I", 0x736664)
i = blob.find(pat); hits = []
while i >= 0:
    hits.append(i); i = blob.find(pat, i + 1)
P("whole-file dword 0x00736664 hits: %d at %s" % (len(hits), [hex(x) for x in hits]))

P()
P("### F7-REVIEW PROBE2 end %.1fs" % (time.time() - t0))
