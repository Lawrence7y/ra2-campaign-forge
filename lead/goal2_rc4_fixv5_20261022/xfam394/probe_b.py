# -*- coding: utf-8 -*-
"""攻击 b：独立核实 0x4E1FA9 的 esi 中转，以及全部站点的线性反证。

对 0x4E1FA9：
  - 反汇编其所在函数（从最近的函数入口到 call）
  - 检查 esi 在 0x4E1F88 之后是否被覆盖
  - 检查 ecx 在 0x4E1FA7 之后是否被覆盖
  - 检查 call 站点的前驱集合是否唯一
另外做「线性反证」：对每个站点，找线性上最近的一条写 ecx 的指令，
与图分析命中的 writer 比较 —— 用来验证 S394 §二「16 个站点来自分支路径」。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import _verify_ecx_dataflow as G  # noqa: E402


def show(bn, lo, hi, marks=()):
    a = lo
    while a < hi:
        i = bn.code.get(a)
        if i is None:
            print("  0x%X  <not decoded>" % a)
            a += 1
            continue
        mk = "  <<<" if a in marks else ""
        print("  0x%08X  %-24s %-9s %s%s" % (a, i.bytes.hex(" "), i.mnemonic, i.op_str, mk))
        a += i.size


def main():
    bn = G.Bin(G.EXE)

    print("=" * 90)
    print("B1. 0x4E1FA9 站点完整上下文（前后 0x60 字节窗口）")
    print("=" * 90)
    show(bn, 0x4E1F60, 0x4E1FB8, marks=(0x4E1F88, 0x4E1FA7, 0x4E1FA9))

    print("\n  call 站点 0x4E1FA9 解码：%s %s" % (bn.code[0x4E1FA9].mnemonic,
                                              bn.code[0x4E1FA9].op_str))
    print("  前驱集合: %s" % sorted("0x%X" % x for x in bn.prev.get(0x4E1FA9, ())))

    # esi 从 0x4E1F88 到 0x4E1FA7 之间是否被写
    print("\n  --- esi 存活检查 [0x4E1F88, 0x4E1FA9) ---")
    a = 0x4E1F88 + bn.code[0x4E1F88].size
    hit = []
    while a < 0x4E1FA9:
        i = bn.code[a]
        d, s = G.operand_write(i)
        if d == "esi" or d == "__IMPLICIT__":
            hit.append((a, i.mnemonic, i.op_str, d, s))
        a += i.size
    print("    esi/隐式写点: %s" % (["0x%X %s %s" % (x[0], x[1], x[2]) for x in hit] or "无"))

    print("\n  --- ecx 存活检查 [0x4E1FA7, 0x4E1FA9) ---")
    a = 0x4E1FA7 + bn.code[0x4E1FA7].size
    hit2 = []
    while a < 0x4E1FA9:
        i = bn.code[a]
        d, s = G.operand_write(i)
        if d == "ecx" or d == "__IMPLICIT__":
            hit2.append((a, i.mnemonic, i.op_str))
        a += i.size
    print("    ecx/隐式写点: %s" % (["0x%X %s %s" % x for x in hit2] or "无"))

    # 更严格：用 capstone 独立枚举 [0x4E1F88, 0x4E1FA9) 内所有写 ecx/esi 的指令
    # （包括 operand_write 认不出的助记符）
    print("\n  --- 原始助记符清单 [0x4E1F88, 0x4E1FA9) ---")
    a = 0x4E1F88
    while a < 0x4E1FA9:
        i = bn.code[a]
        print("    0x%08X  %-9s %s" % (a, i.mnemonic, i.op_str))
        a += i.size

    print("\n" + "=" * 90)
    print("B2. 线性反证：图 writer vs 线性最近 writer（验证 S394 §二 的「16 个分支站点」）")
    print("=" * 90)

    def graph_writers(site, reg="ecx", limit=0x4000):
        seen, work, out = set(), [(site, reg)], []
        while work:
            node, r = work.pop()
            if (node, r) in seen:
                continue
            seen.add((node, r))
            for p in bn.prev.get(node, ()):
                if (p, r) in seen:
                    continue
                pi = bn.code.get(p)
                if pi is None:
                    continue
                d, s = G.operand_write(pi)
                if d == "__IMPLICIT__":
                    seen.add((p, r)); continue
                if d == r:
                    k, v = G.classify_source(pi, s)
                    out.append((p, k, v))
                    seen.add((p, r))
                    if k == "REG":
                        work.append((p, v))
                elif pi.mnemonic == "call":
                    seen.add((p, r))
                else:
                    work.append((p, r))
        return out

    def linear_writer(site, limit=0x400):
        a = site
        while a > site - limit:
            i = bn.code.get(a)
            if i is None:
                return None
            d, s = G.operand_write(i)
            if d == "ecx" or d == "__IMPLICIT__":
                return (a, i.mnemonic, i.op_str)
            # 上一条
            prev_addr = None
            for pa, pi in bn.code.items():
                if pa + pi.size == a:
                    prev_addr = pa
                    break
            if prev_addr is None:
                return None
            a = prev_addr
        return None

    sites = []
    for t in G.TARGETS:
        for s in bn.callers_of(t):
            sites.append((s, t))

    mismatch = 0
    for s, t in sorted(sites):
        gw = graph_writers(s)
        lw = linear_writer(s)
        gset = sorted(set(x[0] for x in gw))
        lin = lw[0] if lw else None
        flag = "" if (lin in gset) else "   <<< 线性最近写点不在图命中集合里"
        if flag:
            mismatch += 1
        print("  0x%08X  graph=%s  linear_nearest=%s%s"
              % (s, ["0x%X" % x for x in gset],
                 ("0x%X %s %s" % lw) if lw else "none", flag))
    print("\n  线性最近写点 != 图写点 的站点数: %d / %d" % (mismatch, len(sites)))


if __name__ == "__main__":
    main()
