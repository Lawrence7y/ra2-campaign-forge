# -*- coding: utf-8 -*-
"""A07 probe1: 现场自证 + CurrentFrame 0xA8ED84 全镜像引用/写点复核 + 10 写点上下文窗口"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine, G_FRAME

eng = Engine()
cov = eng.coverage
print("== coverage ==")
print("pct=%.2f insns=%d resync=%d" % cov)
print("sha256 ok (engine assert passed)")

hits = eng.disp_hits(G_FRAME)
writes = [h for h in hits if h[1] == "W"]
reads = [h for h in hits if h[1] == "R"]
print("\n== disp_hits(0xA8ED84) ==")
print("total refs = %d, writes = %d, reads = %d" % (len(hits), len(writes), len(reads)))
print("\n-- all W hits --")
for va, k, m, o in writes:
    print("0x%08X %s %s %s" % (va, k, m, o))

# 10 写点任务单
TASK = [0x52DA08, 0x55DE81, 0x5B7329, 0x5BB20C, 0x5E550F,
        0x5E747C, 0x68466B, 0x686765, 0x795234, 0x79758C]
wset = set(h[0] for h in writes)
print("\n-- task W set vs computed W set --")
print("task not in computed:", [hex(x) for x in TASK if x not in wset])
print("computed not in task:", [hex(x) for x in sorted(wset) if x not in TASK])

# 每个写点前 40 字节后 16 字节的原始反汇编窗口（从写点对齐开始向前找最近可解码起点）
print("\n== context windows (write site +/-) ==")
for w in TASK:
    lo = w - 0x40
    print("\n---- write site 0x%08X ----" % w)
    try:
        rows = eng.disasm(lo, 0x60)
    except Exception as ex:
        print("disasm err", ex)
        continue
    for a, b, m, o in rows:
        mark = "  <<< W" if a == w else ""
        print("0x%08X  %-20s %s %s%s" % (a, b, m, o, mark))
