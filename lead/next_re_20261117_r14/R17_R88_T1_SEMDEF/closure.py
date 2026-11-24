#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""closure.py — 逐步加减算式的机器闭合校验（法 3：纯整数加减，不重新分类）。

每条式子的每一行 Δ 都是盘上清单的导出量，出处写在最后一列。
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

# ---- C′ 的 why 三档（R17_R78_T1_RECLASS\files_tier_Cprime.tsv 实算）
P1A = (3786, 714228639)
P1B = (378, 100948978)
P0 = (14548, 548531103)
C_TOT = (18712, 1363708720)
assert P1A[0] + P1B[0] + P0[0] == C_TOT[0]
assert P1A[1] + P1B[1] + P0[1] == C_TOT[1]

# ---- EVIDENCE 冲突件（R17_R81_T2_EVID\_verdicts.tsv 实算；三者互斥、全在 C′ 之外）
OBJ = (732, 10251220)
TIE = (266, 4965209)
PROC = (244, 31468350)
assert OBJ[0] + TIE[0] + PROC[0] == 1242
assert OBJ[1] + TIE[1] + PROC[1] == 46684779

FINAL = (4518, 724479859)


def run(title, steps, final):
    n = b = 0
    print(f"\n=== {title} ===")
    print("步号\t符号\tΔ件\tΔ字节\t累计件\t累计字节\t出处")
    for sid, sign, (dn, db), why in steps:
        if sign == "+":
            n += dn; b += db; sd, sb = f"+{dn:,}", f"+{db:,}"
        else:
            n -= dn; b -= db; sd, sb = f"-{dn:,}", f"-{db:,}"
        print(f"{sid}\t{sign}\t{sd}\t{sb}\t{n:,}\t{b:,}\t{why}")
    ok = (n, b) == final
    print(f"闭合 = {ok}   末行 = {n:,} / {b:,}   目标 = {final[0]:,} / {final[1]:,}")
    return ok


ok1 = run("算式 A（主式：从 C′ 出发，件级）", [
    ("A0", "+", C_TOT, "C′ 原值 = P1a + P1b + P0"),
    ("A1", "-", P1B, "减 P1b 档（表格形态，无对象内容证据）"),
    ("A2", "-", P0, "减 P0 档（兜底，无任何内容证据）"),
    ("A3", "+", OBJ, "加 EVIDENCE 内容判为对象抄本的 732 件（C′ 之外，单列判定表）"),
], FINAL)

ok2 = run("算式 B（对偶式：从档 A 出发，同样落到 4,518 / 724,479,859）", [
    ("B0", "+", (24723, 1589964358), "档 A 全量"),
    ("B1", "-", (20205, 865484499), "减「除 KEEP 以外」= A − KEEP（P1b+P0+TIE+PROC+冲突件外的 A 外件）"),
], FINAL)

print("\n=== 交叉恒等式（独立于上面两条算式的加法顺序） ===")
X = [
    ("X1 件数分解", FINAL[0], P1A[0] + OBJ[0], "3,786 (P1a) + 732 (逐件对象抄本)"),
    ("X2 字节分解", FINAL[1], P1A[1] + OBJ[1], "714,228,639 + 10,251,220"),
    ("X3 C′ 三档", C_TOT[0], P1A[0] + P1B[0] + P0[0], "P1a + P1b + P0"),
    ("X4 与旧C 件", FINAL[0], 4338 + 180, "C′∩旧C 4,338 + C′∖旧C 180"),
    ("X5 与旧C 字节", FINAL[1], 573217609 + 151262250, "573,217,609 + 151,262,250"),
    ("X6 档A 分桶", 1589964358, FINAL[1] + 654445290 + 31468350 + 179570859,
     "KEEP + SEMI(654,445,290) + PROC(31,468,350) + 其余 A 件(179,570,859)：四桶互斥、直接铺满档 A"),
    ("X7 档A 桶数", 24723, FINAL[0] + 15192 + 244 + 4769, "4,518 + 15,192 + 244 + 4,769"),
]
for name, a, bb, why in X:
    print(f"{name}: {a:,} == {bb:,} ? {a == bb}   # {why}")

print(f"\nGB(10^9) = {FINAL[1]/1e9:.6f}   GiB(2^30) = {FINAL[1]/2**30:.6f}")
print("ALL_CLOSED", ok1 and ok2 and all(a == b for _, a, b, _ in X))
