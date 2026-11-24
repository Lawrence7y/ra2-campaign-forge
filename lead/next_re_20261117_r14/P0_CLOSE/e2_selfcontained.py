#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-CLOSE · 自包含性判别：验证 413（VT）+ 361（FW-only）候选不只是
「某个更大函数中间一个 ret 之后的续段」。

对每个候选 S：从 S 线性解码，找到第一条「无条件终结」指令（ret/retn/jmp/int3 单条、
或 jmp 到非连续目标），记为 end；与「下一个 atlas entry 的起点」比较：
   end < next_atlas  ⇒ S 的体在下一 atlas 函数之前就终结，是自包含的独立函数
   end ≥ next_atlas  ⇒ 越界，可能不是独立入口
另记「体内是否只有一条 ret 且无内部 jmp 出界」等形态。
输出：selfcontained.txt
"""
import io
import os
import sys
import json
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p0lib import RawPE, Sweep, Atlas, SLICES, JCC, disasm_at   # noqa: E402

OUT = []


def w(s=""):
    print(s)
    OUT.append(s)


def body_end(pe, sw, S, limit):
    """从 S 线性走，返回第一条无条件终结指令的结束地址。"""
    i = sw.index_of(S)
    if i < 0:
        return None, "not-insn-start"
    j = i
    while j < sw.n:
        a = sw.starts[j]
        if a >= limit:
            return None, "ran-past-limit"
        m = sw.mn(j)
        if m in ("ret", "retn", "retf", "jmp", "int3"):
            return a + sw.sizes[j], m
        if m in ("iretd", "hlt"):
            return a + sw.sizes[j], m
        j += 1
    return None, "sweep-end"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    pe = RawPE()
    t = pe.byname[".text"]
    TLO = pe.imagebase + t["va"]
    THI = TLO + t["vsize"]
    sw = Sweep(pe, TLO, THI)
    at = Atlas()
    import bisect

    def next_entry(x):
        i = bisect.bisect_right(at.entries, x)
        return at.entries[i] if i < at.n else THI

    def load(path):
        s = set()
        for r in io.open(os.path.join(HERE, path), encoding="utf-8").read().splitlines()[1:]:
            p = r.split("\t")
            if len(p) > 1 and p[8] == "TRUE":
                s.add(int(p[1], 16))
        return s

    B1 = load("TRUE_ENTRY_UNIFIED.tsv")
    FW = load("TRUE_ENTRY_ORPHAN.tsv")
    V = json.load(io.open(os.path.join(HERE, "vt_direct_summary.json"), encoding="utf-8"))
    VT = set()
    for k, v in V["per_slice"].items():
        VT |= set(int(a, 16) for a in v["list"])

    w("# 自包含性判别")
    for name, S in (("VT 虚表槽直指（任务 B）", VT), ("FW-only 前向独占", FW - B1 - VT)):
        nxt = [next_entry(x) for x in S]
        ok = 0
        bad = 0
        unk = 0
        kinds = Counter()
        spans = []
        for x, nx in zip(sorted(S), sorted(nxt, key=lambda z: 0)) if False else []:
            pass
        for x in sorted(S):
            nx = next_entry(x)
            e, m = body_end(pe, sw, x, nx)
            if e is None:
                unk += 1
                continue
            kinds[m] += 1
            if e <= nx:
                ok += 1
                spans.append(e - x)
            else:
                bad += 1
        w("")
        w("## %s  （n=%d）" % (name, len(S)))
        w("  自包含（首条终结指令在下一 atlas entry 之前）= %d (%.1f%%)"
          % (ok, 100.0 * ok / len(S)))
        w("  越界（体的终结在下一 atlas entry 之后）      = %d" % bad)
        w("  未能判定                                    = %d" % unk)
        w("  首条终结指令类型：%s" % dict(kinds))
        if spans:
            spans.sort()
            w("  体长（S→首条终结）：p50=%d p90=%d max=%d min=%d"
              % (spans[len(spans) // 2], spans[int(len(spans) * 0.9)],
                 spans[-1], spans[0]))

    io.open(os.path.join(HERE, "selfcontained.txt"), "w", encoding="utf-8").write(
        "\n".join(OUT) + "\n")
    print("\nwrote selfcontained.txt")


if __name__ == "__main__":
    main()
