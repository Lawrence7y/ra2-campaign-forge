# -*- coding: utf-8 -*-
# P09: 调用者归属 + dispatcher 0x48CDxx 结构 + W6 尾 + W4 ebp 反向切片 + W3 环境域
import sys, bisect
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine, G_FRAME
from collections import defaultdict

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

def owner(va):
    i = bisect.bisect_right(HEADS, va) - 1
    return HEADS[i] if i >= 0 else None

SITES = [0x48CDD3, 0x48CFAA, 0x48CE8A, 0x5B65BF, 0x5B7903, 0x5E0D12,
         0x7A6DEE, 0x7A7F07, 0x683D21, 0x7800EC, 0x5C4BB3, 0x5DD2C8, 0x5DD488]
print("== A. 调用点归属 ==")
for s in SITES:
    h = owner(s)
    print("call site %#x -> 宿主函数头 %#x" % (s, h))

print("\n== B. 各调用点上下文 ±0x30 ==")
def dump(lo, hi, tag):
    print("  [%s]" % tag)
    for a in sorted(k for k in by if lo <= k < hi):
        ins = by[a]
        print("  %#08x  %-22s %s %s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str))
for s in SITES:
    dump(s - 0x28, s + 0x10, "site %#x" % s)

print("\n== C. dispatcher 头 + 回边 ==")
dh = owner(0x48CE8A)
print("dispatcher head = %#x" % dh)
i = bisect.bisect_right(HEADS, dh)
nxt = HEADS[i] if i < len(HEADS) else dh + 0x1000
print("范围=[%#x,%#x)" % (dh, nxt))
for s, t, m in eng.loop_backedges(dh, nxt):
    print("  backedge %#x -> %#x  %s" % (s, t, m))

print("\n== D. W6 尾部 [0x5E7490, 0x5E74E0) ==")
dump(0x5E7490, 0x5E74E0, "W6 tail")

print("\n== E. W4 反向切片：能到 W=0x5BB20C 的指令集内的 ebp 写点 ==")
# 非call边反向爬取，限制在本函数内
succ_nc = defaultdict(list)
pred_nc = defaultdict(list)
seq = [x for x in stream if 0x5BAC60 <= x.address < 0x5BB290]
for k in range(len(seq)):
    ins = seq[k]
    a = ins.address
    if ins.mnemonic.startswith("ret"):
        continue
    b = seq[k + 1].address if k + 1 < len(seq) else None
    tgt = None
    try:
        if ins.operands and ins.operands[0].type == 2:
            tgt = ins.operands[0].imm
    except Exception:
        pass
    if ins.mnemonic == "call":
        if b == a + ins.size:
            succ_nc[a].append(b); pred_nc[b].append(a)
        continue
    if ins.mnemonic == "jmp":
        if tgt is not None and 0x5BAC60 <= tgt < 0x5BB290:
            succ_nc[a].append(tgt); pred_nc[tgt].append(a)
        continue
    if b is not None:
        succ_nc[a].append(b); pred_nc[b].append(a)
    if ins.mnemonic[0] == "j" and tgt is not None and 0x5BAC60 <= tgt < 0x5BB290:
        succ_nc[a].append(tgt); pred_nc[tgt].append(a)

W = 0x5BB20C
seen, work = set(), [W]
while work:
    a = work.pop()
    if a in seen: continue
    seen.add(a)
    for p in pred_nc.get(a, ()):
        if p not in seen: work.append(p)
print("  能到 W 的指令数 = %d" % len(seen))
for a in sorted(seen):
    ins = by[a]
    if (ins.mnemonic in ("mov", "xor", "pop", "leave") and
            (ins.op_str.startswith("ebp") or ", ebp" in ins.op_str or ins.op_str == "ebp")):
        print("  切片内 ebp 写: %#x  %s %s" % (a, ins.mnemonic, ins.op_str))

print("\n== F. W3 环境域 [0x5B7240, 0x5B7330) ==")
dump(0x5B7240, 0x5B7330, "W3 guard loop")
