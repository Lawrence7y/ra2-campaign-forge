# -*- coding: utf-8 -*-
"""攻击 a2/b：逐站点链路取证。
对 67 个站点各自打印：命中的 writer 地址、线性距离、路径上是否跨过 ret/函数序言，
以及 full 图 与 fallthrough-only 图 命中的 writer 集合是否相同。
"""
import collections
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import _verify_ecx_dataflow as G  # noqa: E402


def build_prev_ft(bin_):
    prev = collections.defaultdict(set)
    for a, i in bin_.code.items():
        ft = a + i.size
        m = i.mnemonic
        if m == "ret":
            continue
        if m == "jmp":
            continue
        if m.startswith("j") and m != "jmp":
            if ft in bin_.code:
                prev[ft].add(a)
            continue
        if ft in bin_.code:
            prev[ft].add(a)
    return prev


def trace(bin_, site, reg0="ecx"):
    """返回 (sources, writers[(addr, kind, src)], max_back_dist, crossed_prologue)"""
    seen = set()
    work = [(site, reg0)]
    sources = set()
    writers = []
    min_addr = site
    while work:
        node, reg = work.pop()
        if (node, reg) in seen:
            continue
        seen.add((node, reg))
        preds = bin_.prev.get(node)
        if not preds:
            sources.add(("UNKNOWN", "entry@0x%X" % node))
            continue
        for p in preds:
            if (p, reg) in seen:
                continue
            pi = bin_.code.get(p)
            if pi is None:
                sources.add(("UNKNOWN", "unmapped@0x%X" % p))
                continue
            min_addr = min(min_addr, p)
            dst, src = G.operand_write(pi)
            if dst == "__IMPLICIT__":
                sources.add(("UNKNOWN", "implicit@0x%X" % p))
                seen.add((p, reg))
                continue
            if dst == reg:
                kind, val = G.classify_source(pi, src)
                writers.append((p, kind, val, pi.mnemonic, pi.op_str))
                seen.add((p, reg))
                if kind == "REG":
                    work.append((p, val))
                else:
                    sources.add((kind, val))
                continue
            if pi.mnemonic == "call":
                sources.add(("UNKNOWN", "call@0x%X" % p))
                seen.add((p, reg))
                continue
            work.append((p, reg))
    return sources, writers, min_addr, len(seen)


def main():
    bn = G.Bin(G.EXE)
    full_prev = bn.prev
    ft_prev = build_prev_ft(bn)

    # 入口点统计：有多少地址在 full 图中无前驱
    n_entry = sum(1 for a in bn.code if a not in full_prev)
    print("[graph] insns=%d  nodes_without_pred(full)=%d  (%.4f%%)"
          % (len(bn.code), n_entry, 100.0 * n_entry / len(bn.code)))

    sites = []
    for t in G.TARGETS:
        for s in bn.callers_of(t):
            sites.append((s, t))
    print("[census] %d sites" % len(sites))

    print("\n%-12s %-12s %-9s %-6s %-8s %s" %
          ("call_site", "writer", "dist", "nodes", "mnem", "op"))
    diff_writer = []
    for s, t in sites:
        srcs, w, min_a, nseen = trace(bn, s)
        waddrs = sorted(x[0] for x in w)
        bn.prev = ft_prev
        srcs_ft, w_ft, _, _ = trace(bn, s)
        bn.prev = full_prev
        ft_addrs = sorted(x[0] for x in w_ft)
        if waddrs != ft_addrs:
            diff_writer.append((s, waddrs, ft_addrs))
        for (addr, kind, val, mn, op) in w:
            print("%-12s %-12s %-9d %-6d %-8s %s %s"
                  % ("0x%X" % s, "0x%X" % addr, s - addr, nseen, mn, op, kind))

    print("\n[full vs ft 命中 writer 集合不同的站点] %d 个" % len(diff_writer))
    for s, a, b in diff_writer:
        print("   0x%X  full=%s  ft=%s" % (s, ["0x%X" % x for x in a], ["0x%X" % x for x in b]))

    # 同一 writer 被多少个站点共享？
    cnt = collections.Counter()
    for s, t in sites:
        srcs, w, _, _ = trace(bn, s)
        for (addr, *_rest) in w:
            cnt[addr] += 1
    print("\n[writer 复用] 不同 writer 数=%d，被多站点共享的=%s"
          % (len(cnt), [(("0x%X" % k), v) for k, v in cnt.items() if v > 1]))


if __name__ == "__main__":
    main()
