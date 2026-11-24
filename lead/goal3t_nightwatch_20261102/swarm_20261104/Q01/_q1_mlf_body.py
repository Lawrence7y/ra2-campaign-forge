# -*- coding: utf-8 -*-
"""Q01 步4：MLF 体内是否调旗标置位者/泵消息；0x48C8B0 完整 CFG；每轮慢爬假说的字节链。"""
import sys, bisect
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("coverage %.6f%% / %d insns / %d resync" % eng.coverage)
stream = eng.stream

MLF_LO, MLF_HI = 0x55D360, 0x55DEE0
SETTERS = (0x4F7870, 0x4C6CB0, 0x48C8B0)

# ---------- A. MLF 体内对置位者/清零者/状态机/泵的调用 ----------
print("===== MLF 体内直接调用普查 =====")
targets = {}
for i in stream:
    if MLF_LO <= i.address < MLF_HI and i.mnemonic == "call":
        if i.operands and i.operands[0].type == 2:
            t = i.operands[0].imm
            targets.setdefault(t, []).append(i.address)
        elif i.operands and i.operands[0].type == 3:
            targets.setdefault("indirect", []).append(i.address)
for t in sorted(targets, key=lambda x: str(x)):
    sites = targets[t]
    tag = ""
    if t in SETTERS:
        tag = "  <<<< 旗标置位者!"
    if t in (0x55CFD0,):
        tag = "  <<<< 状态机"
    if t in (0x48D080, 0x5D4D50, 0x5F1C60):
        tag = "  <<<< 消息泵族"
    print("  -> 0x%08X x%d  @ %s%s" % (t, len(sites), " ".join(hex(a) for a in sites[:8]), tag))

# ---------- B. 0x48C8B0 全函数反汇编落盘 + ret/jcc 结构 ----------
heads = sorted({i.operands[0].imm for i in stream
                if i.mnemonic == "call" and i.operands and i.operands[0].type == 2})
k = bisect.bisect_left(heads, 0x48C8B0)
lo, hi = 0x48C8B0, heads[k + 1]
print("\n===== 0x48C8B0 = [0x%08X, 0x%08X) size=0x%X =====" % (lo, hi, hi - lo))
succ, seq = eng._edges(lo, hi)
rets = [i.address for i in seq if i.mnemonic.startswith("ret")]
print("rets:", [hex(x) for x in rets])
with open(r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/Q01/_q1_48C8B0_full.asm", "w", encoding="utf-8") as f:
    for i in seq:
        f.write("%08X  %-20s %s %s\n" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
print("full -> _q1_48C8B0_full.asm (%d insns)" % len(seq))
# F3 写点 0x48CB2E 的前向支配条件：打印从函数头到写点的全部条件跳转
print("\n-- 头部到 0x48CB2E 之间的全部 jcc/cmp/test --")
for i in seq:
    if i.address >= 0x48CB2E:
        break
    if i.mnemonic.startswith("j") or i.mnemonic in ("cmp", "test"):
        print("  %08X  %s %s" % (i.address, i.mnemonic, i.op_str))

# ---------- C. 0x48C8B0 是否也读四旗标（判断互斥） ----------
print("\n===== 0x48C8B0 内四旗标访存 =====")
for i in stream:
    if not (lo <= i.address < hi):
        continue
    try:
        ops = i.operands
    except Exception:
        continue
    for op in ops:
        if op.type == 3 and op.mem.base == 0 and op.mem.index == 0 \
           and op.mem.disp in (0xA83D49, 0xA8ECD0, 0x8B41C0, 0xA83D48):
            print("  %08X %s %s %s" % (i.address, "W" if (op.access & 2) else "R", i.mnemonic, i.op_str))
            break

# ---------- D. 0x4F7870/0x4C6CB0 的调用者（含间接段归属） ----------
for fva in (0x4F7870, 0x4C6CB0):
    print("\n===== callers of 0x%08X =====" % fva)
    for i in stream:
        if i.mnemonic == "call" and i.operands and i.operands[0].type == 2 \
           and i.operands[0].imm == fva:
            print("   call @ 0x%08X host=0x%08X" % (i.address, host(i.address) or 0))
