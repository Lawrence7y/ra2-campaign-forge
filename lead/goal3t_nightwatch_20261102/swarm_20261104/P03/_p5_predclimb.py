# -*- coding: utf-8 -*-
# P05: 全 .text 前驱图 + 写点向后爬（排除 call 边）→ 找无入边入口 = 宿主函数头
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine, G_FRAME
from collections import defaultdict

eng = Engine()
by = eng.by()
stream = eng.stream

# ---- 一次全图构建：非 call 边（fallthrough/jcc/jmp）----
nxt = {}
seq = stream
succ_nc = defaultdict(list)   # 非 call 后继
pred_nc = defaultdict(list)   # 非 call 前驱
call_sites = defaultdict(list)  # target -> [caller]
for k in range(len(seq) - 1):
    ins = seq[k]
    a = ins.address
    b = seq[k + 1].address
    is_call = ins.mnemonic == "call"
    tgt = None
    try:
        if ins.operands and ins.operands[0].type == 2:
            tgt = ins.operands[0].imm
    except Exception:
        pass
    if is_call:
        if tgt is not None:
            call_sites[tgt].append(a)
        if b == a + ins.size:                 # call 的落空边保留（目标边排除）
            succ_nc[a].append(b); pred_nc[b].append(a)
        continue
    if ins.mnemonic.startswith("ret"):
        continue                              # ret 无落空边
    if ins.mnemonic == "jmp":
        if tgt is not None:
            succ_nc[a].append(tgt); pred_nc[tgt].append(a)
        continue
    # jcc / 普通指令：落空 + 分支目标
    if b == a + ins.size:
        succ_nc[a].append(b); pred_nc[b].append(a)
    if ins.mnemonic[0] == "j" and tgt is not None and tgt != a:
        succ_nc[a].append(tgt); pred_nc[tgt].append(a)

HEADS = set(call_sites)  # E8 头集（call 目标）

WRITES = [0x52DA08, 0x55DE81, 0x5B7329, 0x5BB20C, 0x5E550F,
          0x5E747C, 0x68466B, 0x686765, 0x795234, 0x79758C]

def climb(W):
    """从 W 沿非 call 边向后爬，返回 (访问集, 入口集)。"""
    seen, work = set(), [W]
    while work:
        a = work.pop()
        if a in seen: continue
        seen.add(a)
        for p in pred_nc.get(a, ()):
            if p not in seen: work.append(p)
    entries = sorted(a for a in seen if not pred_nc.get(a))
    return seen, entries

print("== 10 写点向后爬（非 call 边）==")
for W in WRITES:
    seen, entries = climb(W)
    # 入口里挑最小且可作为函数头的（排除紧邻小块入口）
    print("W=%#x  |visit|=%d  entries=%s" % (
        W, len(seen), ["%#x%s" % (e, "*" if e in HEADS else "") for e in entries[:8]]))

# 0x79758C 的入口详情
seen, entries = climb(0x79758C)
print("\n-- 0x79758C 全部入口 --")
for e in entries:
    ins = by[e]
    print("entry %#x  %s %s   E8被调用=%s  callers=%d" % (
        e, ins.bytes.hex(), ins.mnemonic, e in HEADS, len(call_sites.get(e, []))))
    cs = call_sites.get(e, [])
    if cs:
        print("   callers:", " ".join("%#x" % c for c in cs[:12]))
