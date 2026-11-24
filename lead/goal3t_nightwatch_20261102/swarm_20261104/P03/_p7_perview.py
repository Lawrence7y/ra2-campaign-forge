# -*- coding: utf-8 -*-
# P07: 10 写点逐点深挖 —— 上下文 / 函数内读点 / RMW 形态 / 守卫 / 环 / 调用者
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine, G_FRAME
from collections import defaultdict

eng = Engine()
by = eng.by()

FUNCS = [
    (0x52DA08, 0x52D9A0, 0x52F3F0),
    (0x55DE81, 0x55D360, 0x55DEE0),
    (0x5B7329, 0x5B7090, 0x5B7360),
    (0x5BB20C, 0x5BAC60, 0x5BB290),
    (0x5E550F, 0x5E3D10, 0x5E5F10),
    (0x5E747C, 0x5E7460, 0x5E74E0),
    (0x68466B, 0x684620, 0x684C30),
    (0x686765, 0x686730, 0x686890),
    (0x795234, 0x794BA0, 0x795650),
    (0x79758C, 0x7970D0, 0x7975AC),
]

# E8 调用者图
call_sites = defaultdict(list)
for ins in eng.stream:
    if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == 2:
        t = ins.operands[0].imm
        call_sites[t].append(ins.address)

hits = []
with open("_hits_gframe.txt", encoding="utf-8") as f:
    for line in f:
        va, acc, mn, ops = line.split(None, 3)
        hits.append((int(va, 16), acc, mn, ops.strip()))

def dump(lo, hi):
    for a in sorted(k for k in by if lo <= k < hi):
        ins = by[a]
        mark = " <<<<" if a in {w for w, _, _ in FUNCS} else ""
        print("  %#08x  %-24s %s %s%s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))

for W, head, hi in FUNCS:
    print("=" * 90)
    print("W=%#x  func=[%#x,%#x)  rets=%s" % (W, head, hi,
          ",".join("%#x" % by[r].address for r in sorted(k for k in by
              if head <= k < hi and by[k].mnemonic.startswith("ret")))))
    callers = call_sites.get(head, [])
    print("  E8 callers(%d): %s" % (len(callers), " ".join("%#x" % c for c in callers[:16])))
    print("  -- 上下文 [W-0x48, W+0x20) --")
    dump(W - 0x48, W + 0x20)
    fr = [(va, mn, ops) for va, acc, mn, ops in hits if head <= va < W and acc == "R"]
    print("  -- 函数内 W 之前的读: %d 处" % len(fr))
    if fr:
        for va, mn, ops in fr[-6:]:
            print("     %#08x (%+#x) %s %s" % (va, va - W, mn, ops))
        nr = fr[-1][0]
        if 0 < W - nr <= 0x140:
            print("  -- RMW 检查片 [最近读 %#x, W) 距离=%#x --" % (nr, W - nr))
            dump(nr, W)
        else:
            print("  -- 最近读距 W %#x 字节（超窗，仅列尾 0x40）--" % (W - nr))
            dump(W - 0x40, W)
    # 守卫：W 前最近的 jcc
    jccs = [(a, by[a]) for a in sorted(k for k in by if max(head, W - 0x90) <= k < W)
            if by[a].mnemonic[0] == "j"]
    if jccs:
        print("  -- W 前的分支（守卫线索）--")
        for a, ins in jccs[-4:]:
            print("     %#08x %s %s" % (a, ins.mnemonic, ins.op_str))
    be = eng.loop_backedges(head, hi)
    inner = [(s, t, m) for s, t, m in be if s <= W <= t + 0x100] if be else []
    print("  -- 函数内回边数=%d；含 W 附近区间: %s" % (len(be), inner[:4]))
