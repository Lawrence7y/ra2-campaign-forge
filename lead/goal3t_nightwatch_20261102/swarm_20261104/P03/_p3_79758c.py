# -*- coding: utf-8 -*-
# P03a: 0x79758C 宿主函数定位（E8 头不可达 → 查 jmp thunk / 非调用入口）
import sys, bisect
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine, G_FRAME

eng = Engine()
by = eng.by()
stream = eng.stream

heads = set()
for ins in stream:
    if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == 2:
        t = ins.operands[0].imm
        if eng.TLO <= t < eng.THI:
            heads.add(t)
HEADS = sorted(heads)
W = 0x79758C
i = bisect.bisect_right(HEADS, W)
print("W=%#x 下方最近 6 头: %s" % (W, ["%#x" % h for h in HEADS[i-6:i]]))
print("W 上方下一头: %#x" % (HEADS[i] if i < len(HEADS) else 0))

# W 前后指令上下文（指令对齐）
lo, hi_ = W - 0x70, W + 0x30
print("--- 上下文 [%#x, %#x) ---" % (lo, hi_))
for a in sorted(k for k in by if lo <= k < hi_):
    ins = by[a]
    print("%#08x  %-22s %s %s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str))

# 从每个候选头出发的普通可达性（允许穿头），看最近的能到哪
def reach(h, hi):
    succ, seq = eng._edges(h, hi)
    seen, work = set(), [h]
    while work:
        a = work.pop()
        if a in seen: continue
        seen.add(a)
        for s in succ.get(a, ()):
            if s not in seen: work.append(s)
    return seen

hi_next = HEADS[i] if i < len(HEADS) else W + 0x2000
for h in HEADS[i-6:i]:
    r = reach(h, hi_next)
    print("from %#x: |reach|=%d  W可达=%s  最大到达=%#x" % (
        h, len(r), W in r, max(r) if r else 0))
