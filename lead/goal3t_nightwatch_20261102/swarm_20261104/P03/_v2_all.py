# -*- coding: utf-8 -*-
"""V-P03 核验探针 2：全量复算（RMW 链 / 写 0 / 宿主定界 / push 路径 / measure 窗 / 空桩 / 死代码）
独立实现，不调 P03 原脚本。输出逐项对账。"""
import sys, struct
from collections import defaultdict, Counter
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
out = []
def P(*a):
    s = " ".join(str(x) for x in a)
    out.append(s); print(s)

S = eng.stream
BY = eng.by()
cov = eng.coverage
P("[coverage] %.2f%% / %d / %d" % cov)

# ---------- 通用工具 ----------
def text_call_sites(target):
    """全 .text E8 rel32 扫描，目标=target 的 call 站点"""
    tb = eng.raw[eng.TB: eng.TB + eng.TSZ]
    res = []
    i = tb.find(b"\xe8")
    while i >= 0:
        va = eng.TLO + i
        if i + 5 <= len(tb):
            rel = struct.unpack_from("<i", tb, i + 1)[0]
            if va + 5 + rel == target:
                res.append(va)
        i = tb.find(b"\xe8", i + 1)
    return res

def jmp_sites(target):
    """全 .text E9 rel32 + 0F 8x rel32 扫描，目标=target"""
    tb = eng.raw[eng.TB: eng.TB + eng.TSZ]
    res = []
    for i in range(len(tb) - 5):
        va = eng.TLO + i
        if tb[i] == 0xE9:
            rel = struct.unpack_from("<i", tb, i + 1)[0]
            if va + 5 + rel == target:
                res.append((va, "E9"))
        elif tb[i] == 0x0F and i + 6 <= len(tb) and 0x80 <= tb[i+1] <= 0x8F:
            rel = struct.unpack_from("<i", tb, i + 2)[0]
            if va + 6 + rel == target:
                res.append((va, "0F8%x" % (tb[i+1] & 0xF)))
    return res

def host_insns(lo, hi):
    return [i for i in S if lo <= i.address < hi]

def build_cfg(lo, hi):
    ins = host_insns(lo, hi)
    nxt = {ins[k].address: (ins[k+1].address if k+1 < len(ins) else None) for k in range(len(ins))}
    pred = defaultdict(list)
    indirect = []
    for I in ins:
        a, mn = I.address, I.mnemonic
        try: ops = I.operands
        except Exception: ops = []
        tgt = ops[0].imm if (ops and ops[0].type == 2) else None
        if mn == "ret":
            continue
        if mn == "jmp":
            if tgt is None:
                indirect.append(a)          # 间接 jmp（跳转表）
            elif lo <= tgt < hi:
                pred[tgt].append(a)
            else:
                P("  [cfg] jmp out-of-range at 0x%x -> 0x%x" % (a, tgt))
            continue
        if mn.startswith("j"):
            if tgt is None:
                indirect.append(a)
            elif lo <= tgt < hi:
                pred[tgt].append(a)
            if nxt[a] is not None:
                pred[nxt[a]].append(a)
            continue
        if nxt[a] is not None:
            pred[nxt[a]].append(a)
    return ins, nxt, pred, indirect

def backward_slice(lo, hi, wva, reg):
    """独立反向切片：能到达 wva 的指令集；返回 (指令数, reg 的 def 列表, 间接跳转)"""
    ins, nxt, pred, indirect = build_cfg(lo, hi)
    seen, work = set(), [wva]
    while work:
        a = work.pop()
        if a in seen: continue
        seen.add(a)
        for p in pred.get(a, ()):
            if p not in seen: work.append(p)
    defs = []
    for I in ins:
        if I.address not in seen: continue
        if I.mnemonic in ("call",):       # 调用不破坏 callee-saved；对 eax/ecx/edx 是 clobber 源
            pass
        try: ops = I.operands
        except Exception: continue
        for op in ops:
            if op.type == 1 and op.reg == reg and (op.access & 2):
                defs.append((I.address, I.mnemonic, I.op_str))
                break
    return seen, defs, indirect

# capstone reg id helper
import capstone as CS
X86 = {name: getattr(CS.x86_const, "X86_REG_" + name) for name in
       ["EAX","EBX","ECX","EDX","ESI","EDI","EBP","ESP"]}

# ---------- 1. 唯一 RMW 链 ----------
P("")
P("===== [1] 唯一读-加-写链 =====")
P("anchor 0x55DE73 = %s (expect 8b1584eda800)" % eng.rd(0x55DE73,6).hex())
P("anchor 0x55DE7E = %s (expect 42)" % eng.rd(0x55DE7E,3).hex())
P("anchor 0x55DE81 = %s (expect 891584eda800)" % eng.rd(0x55DE81,6).hex())

hits = eng.disp_hits(0xA8ED84)
W = sorted([h for h in hits if h[1]=="W"])
R = sorted([h for h in hits if h[1]=="R"])
P("disp_hits total=%d W=%d R=%d" % (len(hits), len(W), len(R)))
P("W mnemonic census:", dict(Counter(mn for _,_,mn,_ in W)))

# MLF 内 disp 命中
mlf = [h for h in hits if 0x55D360 <= h[0] < 0x55DEE0]
P("MLF [0x55D360,0x55DEE0) hits: %s" % [(hex(a), d, m) for a,d,m,_ in mlf])

# inc/write-back 对的入边检查：任何跳转落进 [0x55DE73,0x55DE82)？
P("[in-edge check] jump targets landing inside [0x55DE73,0x55DE82):")
for I in S:
    if I.mnemonic.startswith("j"):
        try: ops = I.operands
        except Exception: continue
        if ops and ops[0].type == 2 and 0x55DE73 <= ops[0].imm < 0x55DE82:
            P("   !! 0x%x %s -> 0x%x" % (I.address, I.mnemonic, ops[0].imm))
P("   (done)")

# MLF 尾部守卫反汇编
P("[MLF tail 0x55DE60..0x55DEE0]")
for a, b, m, o in eng.disasm(0x55DE60, 0x80):
    P("   0x%08x  %-20s %s %s" % (a, b, m, o))

# reach_without 独立复算
lo, hi, clo, chi = 0x55D360, 0x55DEE0, 0x55DE73, 0x55DE84
ins, nxt, pred, indirect = build_cfg(lo, hi)
succ = defaultdict(list)
for t, ps in pred.items():
    for p in ps: succ[p].append(t)
for I in ins:
    a, mn = I.address, I.mnemonic
    if nxt.get(a) is not None and not mn.startswith("ret"):
        pass
seen, work = set(), [lo]
while work:
    a = work.pop()
    if a in seen: continue
    seen.add(a)
    for s2 in succ.get(a, ()):
        if clo <= s2 <= chi: continue
        if s2 not in seen: work.append(s2)
# 注意 succ 只含块内跳转；补 fallthrough/jcc 双边
succ2, _ = eng._edges(lo, hi)
seen2, work2 = set(), [lo]
while work2:
    a = work2.pop()
    if a in seen2: continue
    seen2.add(a)
    for s2 in succ2.get(a, ()):
        if clo <= s2 <= chi: continue
        if s2 not in seen2: work2.append(s2)
rets = [i.address for i in ins if i.mnemonic.startswith("ret")]
rets_reach_wo = sorted([r for r in rets if r in seen2])
rets_reach = sorted([r for r in rets if r in seen])
P("[MLF rets] all=%s" % [hex(r) for r in rets])
P("[reach_without(eng)] rets reachable bypassing inc block = %s" % [hex(r) for r in sorted([r for r in rets if r in eng.reach_without(lo,hi,clo,chi)])])
P("[reach_without(mine succ2)] = %s" % [hex(r) for r in rets_reach_wo])
P("[reach_without(mine succ)]  = %s" % [hex(r) for r in rets_reach])

# MLF 3 读点上下文
P("[0x55D3BB context]")
for a, b, m, o in eng.disasm(0x55D3BB, 0x40):
    P("   0x%08x  %-16s %s %s" % (a, b, m, o))
P("[0x55D8C9 context]")
for a, b, m, o in eng.disasm(0x55D8C9, 0x30):
    P("   0x%08x  %-16s %s %s" % (a, b, m, o))

with open(r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/P03/_v2_out_part1.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("PART1 SAVED")
