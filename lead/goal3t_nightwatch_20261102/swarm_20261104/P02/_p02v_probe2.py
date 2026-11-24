# -*- coding: utf-8 -*-
"""P02 核验探针 2：补切 KF3/KF5 的对齐窗口 + BSS/ebp 细节。只读。"""
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("coverage", eng.coverage)
by = eng.by()

def show_stream(lo, hi, tag):
    """用已解码流按地址打印（保证对齐）。"""
    print("-- stream %s [0x%X,0x%X)" % (tag, lo, hi))
    for va in sorted(a for a in by if lo <= a < hi):
        i = by[va]
        print("  0x%06X  %-14s %s %s" % (va, i.bytes.hex(), i.mnemonic, i.op_str))

# 1. writer=2 (0x53E59D) 前置：找 push 0x82813C + call 0x7CA845
show_stream(0x53E560, 0x53E5B0, "writer2 ctx aligned")
# 2. mode2 路径：cmp [0xAA0444],2 @0x53E86C → WM_PAINT 0xF 分派 @0x53E89B/A1
show_stream(0x53E86C, 0x53E8D0, "mode2 path aligned")
# 3. mode0 路径：0x53EB16 PeekMessageA PM_NOREMOVE / 0x53EB25 cmp,1 / jne 0x53EBE8
show_stream(0x53EB00, 0x53EB40, "mode0 probe")
show_stream(0x53EBE0, 0x53EBF8, "mode0 jne target")
# 4. 包装 B 0x53E740-4F PM_REMOVE
show_stream(0x53E730, 0x53E770, "wrapper B")
# 5. 0x48CF94 处 ebx 是否 =0（向前找 ebx 定义）
show_stream(0x48CF60, 0x48CFA0, "gm0 ebx origin")
# 6. 0x53E958/0x53EAD8 处 ebp 是否 =0：向前搜当前函数头方向
show_stream(0x53E8F0, 0x53E958, "ebp origin A")
# 7. 0xABFD34 BSS 判定
def sec_of(va):
    for nm, sva, vsz, rp, rsz in eng.SEC:
        if sva <= va < sva + vsz:
            inraw = (rp + (va - sva)) < rp + rsz
            return nm, inraw, hex(vsz), hex(rsz)
print("sec 0xABFD34:", sec_of(0xABFD34), " sec 0xABCD58:", sec_of(0xABCD58), " sec 0xB73550:", sec_of(0xB73550))
# 8. 0xAA0430 同判（泵计数初值）
print("sec 0xAA0430:", sec_of(0xAA0430), " sec 0xA8ED80:", sec_of(0xA8ED80))
