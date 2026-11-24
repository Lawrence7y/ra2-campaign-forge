# -*- coding: utf-8 -*-
# _eqv_measure.py — 复核员独立量测 R=8 与 R_local=2 是否「本语料实测」成立（只读）
import json, pathlib, re, statistics, sys

ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
DIRS = ["lead/tautology_audit_20261109", "lead/layer_identity_20261109",
        "lead/metric_audit_20261109", "lead/keff_calc_20261109",
        "lead/evidence_indep_20261109", "lead/gate_pipeline_20261109",
        "lead/score_decomp_20261109", "lead/comparability_20261109"]
HARD = re.compile(r"^\s*$|^#{1,6}\s|^-{3,}\s*$|^\s*```")
TAUT_MARK = re.compile(r"重言式|重言半|恒真兜底|零信息量|恒真")
SUBST_MARK = re.compile(r"B\s*⊆\s*A|非平凡|forbidden|禁止格|不存在格|反例|额外排除|什么输入会破")
INTENS_MARK = re.compile(r"决定性|定理|已证|恒等式|必相等|恒成立")
SCOPE_MARK = re.compile(r"本 74 行|本批语料|74 行上|观测值|观测等式|样本巧合|巧合|不是定理|不是恒等式|未验|反事实|train=test|95%|契约")

blocks = []
for d in DIRS:
    for p in sorted((ROOT / d).glob("*.md")):
        lines = p.read_bytes().decode("utf-8", errors="replace").split("\n")
        start = None
        for i, l in enumerate(lines, 1):
            if HARD.match(l):
                if start is not None:
                    blocks.append((p, start, i - 1, lines))
                    start = None
            else:
                if start is None:
                    start = i
        if start is not None:
            blocks.append((p, start, len(lines), lines))

blens = [b - a + 1 for _, a, b, _ in blocks]
print("n_blocks =", len(blocks), " max_block_len =", max(blens),
      " median =", statistics.median(blens))

dist = []
for p, a, b, lines in blocks:
    t = [n for n in range(a, b + 1) if TAUT_MARK.search(lines[n - 1])]
    s = [n for n in range(a, b + 1) if SUBST_MARK.search(lines[n - 1])]
    if t and s:
        dmin = min(abs(x - y) for x in t for y in s)
        dist.append(dmin)
from collections import Counter
print("两半同块 =", len(dist), " 距离分布 =", sorted(Counter(dist).items()), " max =", max(dist))

d2 = Counter()
none_ct = 0
for d in DIRS:
    for p in sorted((ROOT / d).glob("*.md")):
        lines = p.read_bytes().decode("utf-8", errors="replace").split("\n")
        for i, l in enumerate(lines, 1):
            if INTENS_MARK.search(l):
                dd = None
                for off in range(0, 8):
                    for n2 in ({i - off, i + off} if off else {i}):
                        if 1 <= n2 <= len(lines) and SCOPE_MARK.search(lines[n2 - 1]):
                            dd = off
                            break
                    if dd is not None:
                        break
                if dd is None:
                    none_ct += 1
                else:
                    d2[dd] += 1
print("强度标签行→最近范围词距离 =", sorted(d2.items()), " none =", none_ct,
      " ±2 内占比 =", round(sum(v for k, v in d2.items() if k <= 2) / max(1, sum(d2.values())), 4))
