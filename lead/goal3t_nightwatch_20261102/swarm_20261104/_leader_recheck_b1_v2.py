# -*- coding: utf-8 -*-
"""§534 Leader 亲算 v2 -- 按数据流重核 P03 的「9/10 写点写 0」。

上一版判据错了：我数的是「op_str 里字面含 0 的写点」= 3 处。
P03 的定义是「写入值在数据流上恒为 0」：字面常数 3 处 + 寄存器来自 xor reg,reg 的 6 处。

本件对 10 个写点逐个做「写入寄存器 → 最近前置定义」追踪，判定其是否恒 0。
只读 gamemd.exe。
"""
import sys

sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")

from collections import defaultdict  # noqa: E402

from ra2tool import Engine  # noqa: E402

e = Engine()
cov, n, rs = e.coverage
print("coverage=%.6f%% insns=%d resync=%d" % (cov, n, rs))
print()

SITES = [0x52DA08, 0x55DE81, 0x5B7329, 0x5BB20C, 0x5E550F,
         0x5E747C, 0x68466B, 0x686765, 0x795234, 0x79758C]

by = e.by()
seq = [i.address for i in e.stream]
pos = {a: k for k, a in enumerate(seq)}

# 前驱图（非 call 边，同函数内）
pred = defaultdict(list)
for k, ins in enumerate(e.stream):
    a, mn = ins.address, ins.mnemonic
    tgt = None
    try:
        if ins.operands and ins.operands[0].type == 2:
            tgt = ins.operands[0].imm
    except Exception:
        pass
    if mn.startswith("ret"):
        continue
    if mn == "jmp":
        if tgt is not None:
            pred[tgt].append(a)
        continue
    if mn.startswith("j"):
        if tgt is not None:
            pred[tgt].append(a)
        if k + 1 < len(seq):
            pred[seq[k + 1]].append(a)
        continue
    if k + 1 < len(seq):
        pred[seq[k + 1]].append(a)


def slice_back(site, limit=600):
    """从 site 反向爬，遇其它函数头（E8 目标）或无前驱则停。"""
    seen, work = set(), [site]
    while work and len(seen) < limit:
        a = work.pop()
        if a in seen:
            continue
        seen.add(a)
        for p in pred.get(a, ()):
            if p not in seen and p < site:
                work.append(p)
    return seen


def trace_reg(site, reg):
    """在 site 之前的切片内找 reg 的最后一个定义。"""
    sl = slice_back(site)
    best = None
    for a in sl:
        if a >= site:
            continue
        ins = by[a]
        op = ins.op_str
        # 只认「写 reg」形态
        if ins.mnemonic == "xor" and op.replace(" ", "") in (f"{reg},{reg}",):
            if best is None or a > best[0]:
                best = (a, "xor", op)
        elif ins.mnemonic == "mov" and op.split(",")[0].strip() == reg:
            if best is None or a > best[0]:
                best = (a, "mov", op)
        elif ins.mnemonic in ("pop",) and op.strip() == reg:
            if best is None or a > best[0]:
                best = (a, "pop", op)
    return best, len(sl)


print("=" * 82)
print("%-10s %-8s %-30s %s" % ("site", "reg", "last-def before site", "恒0?"))
print("=" * 82)
zero_literal = 0
zero_dataflow = 0
for s in SITES:
    ins = by[s]
    op = ins.op_str
    # 字面常数 0
    if ", 0" in op and "ptr" in op:
        zero_literal += 1
        zero_dataflow += 1
        print("%08X  %-8s %-30s %s" % (s, "-", "literal 0 (%s)" % op, "YES(字面)"))
        continue
    reg = op.split(",")[1].strip() if "," in op else "?"
    d, sz = trace_reg(s, reg)
    if d is None:
        verdict = "UNKNOWN(无前置定义)"
    elif d[1] == "xor":
        verdict = "YES(xor 清零 @%08X)" % d[0]
        zero_dataflow += 1
    else:
        verdict = "no (%s @%08X)" % (d[1], d[0])
    print("%08X  %-8s %-30s %s  [slice=%d]" % (
        s, reg, ("%s %s" % (d[1], d[2]) if d else "NONE"), verdict, sz))

print()
print("=" * 82)
print("字面常数 0 的写点 = %d" % zero_literal)
print("数据流恒 0 的写点 = %d / 10" % zero_dataflow)
print("P03 自报 = 9/10")
print("判定: %s" % ("与 P03 一致" if zero_dataflow == 9 else "与 P03 不一致，需查差异"))
print("=" * 82)
sys.exit(0 if zero_dataflow == 9 else 1)
