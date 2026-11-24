# -*- coding: utf-8 -*-
# P02: E8 头集 + 写点宿主函数定界（ret 扫描 + CFG 可达验证，禁线性窗）
import sys, bisect
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine, G_FRAME

eng = Engine()
by = eng.by()
stream = eng.stream

# ---- E8 头集：全部 call rel32 目标 ----
heads = set()
callers = {}   # head -> [caller va]
for ins in stream:
    if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == 2:
        t = ins.operands[0].imm
        if eng.TLO <= t < eng.THI:
            heads.add(t)
            callers.setdefault(t, []).append(ins.address)
HEADS = sorted(heads)
print("E8 头集: %d 个唯一目标" % len(HEADS))

WRITES = [0x52DA08, 0x55DE81, 0x5B7329, 0x5BB20C, 0x5E550F,
          0x5E747C, 0x68466B, 0x686765, 0x795234, 0x79758C]

def reach_no_cross(h, W, hi):
    """从 h 出发 CFG 可达 W 且路径不穿过 (h, W) 内任何其它头。返回 (bool, crossed)"""
    succ, seq = eng._edges(h, hi)
    seen, work, cross = set(), [h], None
    while work:
        a = work.pop()
        if a in seen:
            continue
        seen.add(a)
        for s in succ.get(a, ()):
            if s == W:
                return True, None
            if h < s < W and s in heads:
                if cross is None:
                    cross = s
                continue
            if s not in seen:
                work.append(s)
    return False, cross

def enclosing(W):
    i = bisect.bisect_right(HEADS, W)
    lo_cands = HEADS[max(0, i - 6): i]          # W 之前最近的至多 6 个头
    hi = HEADS[i] if i < len(HEADS) else W + 0x2000   # W 之后下一个头
    ok = None
    for h in reversed(lo_cands):
        got, cross = reach_no_cross(h, W, hi)
        if got:
            ok = (h, hi)
            break
        # 若被中间头挡住，改试那个中间头（由外层 reversed 循环自然覆盖）
    return ok, hi, lo_cands

print()
for W in WRITES:
    res, hi2, cands = enclosing(W)
    if res:
        h, hi = res
        rets, _ = eng.func_rets(h, hi)
        ncalls = len(callers.get(h, []))
        print("W=%#x  head=%#x  range=[%#x,%#x)  rets=%d @ %s  callers=%d" % (
            W, h, h, hi, len(rets), ",".join("%#x" % r.address for r in rets), ncalls))
    else:
        print("W=%#x  head=?? 未定界  cands=%s" % (W, ["%#x" % c for c in cands]))

# 顺带：把 1007 引用全量落盘（复算 + RMW 攻击用）
hits = eng.disp_hits(G_FRAME)
with open("_hits_gframe.txt", "w", encoding="utf-8") as f:
    for va, acc, mn, ops in hits:
        f.write("%08x %s %s %s\n" % (va, acc, mn, ops))
print("\n1007 引用已落盘 _hits_gframe.txt")
