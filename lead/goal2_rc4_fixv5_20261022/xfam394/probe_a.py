# -*- coding: utf-8 -*-
"""攻击 a：前驱图里的分支边是否真的在起作用？
用被审脚本自己的 Bin/backward_sources，只在内存里替换 prev 图。
"""
import collections
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import _verify_ecx_dataflow as G  # noqa: E402

TARGETS = G.TARGETS


def census(bin_):
    n = 0
    fails = []
    for t in TARGETS:
        for s in bin_.callers_of(t):
            srcs, meta = G.backward_sources(bin_, s)
            if set(k for k, _ in srcs) == {"GLOBAL"} and not meta["trunc"]:
                n += 1
            else:
                fails.append((s, t, sorted(set(k for k, _ in srcs))))
    return n, fails


def build_prev(bin_, mode):
    """mode: full / fallthrough_only / branch_only"""
    prev = collections.defaultdict(set)
    for a, i in bin_.code.items():
        ft = a + i.size
        m = i.mnemonic
        if m == "ret":
            continue
        if m == "jmp":
            t = bin_._target(i)
            if mode != "fallthrough_only" and t is not None:
                prev[t].add(a)
            continue
        if m.startswith("j") and m != "jmp":
            t = bin_._target(i)
            if mode != "fallthrough_only" and t is not None:
                prev[t].add(a)
            if mode != "branch_only" and ft in bin_.code:
                prev[ft].add(a)
            continue
        if mode != "branch_only" and ft in bin_.code:
            prev[ft].add(a)
    return prev


def main():
    bn = G.Bin(G.EXE)
    full_prev = bn.prev
    print("[build] insns=%d edges=%d" % (len(bn.code), sum(len(v) for v in full_prev.values())))

    n_full, f_full = census(bn)
    print("[full graph]        %d/67  fails=%s" % (n_full, ["0x%X" % x[0] for x in f_full]))

    ft_prev = build_prev(bn, "fallthrough_only")
    bn.prev = ft_prev
    n_ft, f_ft = census(bn)
    print("[fallthrough only]  %d/67  fails=%d" % (n_ft, len(f_ft)))
    for s, t, k in f_ft:
        print("      FAIL 0x%08X -> 0x%08X  %s" % (s, t, k))
    print("[fallthrough only] edges=%d" % sum(len(v) for v in ft_prev.values()))

    br_prev = build_prev(bn, "branch_only")
    bn.prev = br_prev
    n_br, f_br = census(bn)
    print("[branch only]       %d/67  fails=%d  edges=%d"
          % (n_br, len(f_br), sum(len(v) for v in br_prev.values())))

    # 分支边对每个站点的增量影响：full 通过但 ft 不通过的站点 = 依赖分支边
    ft_fail = {x[0] for x in f_ft}
    dep = sorted(set(ft_fail))
    print("\n[依赖分支边的站点] %d 个: %s" % (len(dep), ["0x%X" % x for x in dep]))

    # 进一步：把分支边指向的目标地址统计一下，看 0x48CE62 那条断言的价值
    print("\n[0x48CE62 前驱 full] %s" % sorted("0x%X" % x for x in full_prev.get(0x48CE62, ())))
    print("[0x48CE62 前驱 ft  ] %s" % sorted("0x%X" % x for x in ft_prev.get(0x48CE62, ())))


if __name__ == "__main__":
    main()
