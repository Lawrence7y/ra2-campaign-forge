# -*- coding: utf-8 -*-
"""攻击 d + 边界检查 + 间接调用面检查。

D1. merged 分支：给 backward_sources 做等价复刻并加不变量检查，
    找出「merged 时该节点的前驱链是否真的都已被记录」。
D2. 0x724530 / 0x724540 上下文反汇编 + 前驱检查。
D3. 8 个目标地址是否出现在数据段（vtable/函数指针表）⇒ 间接调用面。
"""
import collections
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import _verify_ecx_dataflow as G  # noqa: E402


def backward_instrumented(bin_, call_va, reg0="ecx"):
    """复刻 backward_sources，但记录 merged 的细节。"""
    seen = set()
    recorded = set()   # (addr, reg) 已记录来源（writer/call/implicit/unmapped/entry）
    expanded = set()   # (addr, reg) 已展开前驱
    work = [(call_va, reg0)]
    sources = set()
    ends = collections.Counter()
    merged_detail = []
    while work:
        node, reg = work.pop()
        if (node, reg) in seen:
            continue
        seen.add((node, reg))
        expanded.add((node, reg))
        preds = bin_.prev.get(node)
        if not preds:
            ends["entry"] += 1
            sources.add(("UNKNOWN", "function-entry@0x%X" % node))
            recorded.add((node, reg))
            continue
        progressed = False
        for p in preds:
            if (p, reg) in seen:
                continue
            pi = bin_.code.get(p)
            if pi is None:
                ends["unmapped"] += 1
                sources.add(("UNKNOWN", "unmapped-pred"))
                continue
            progressed = True
            dst, src = G.operand_write(pi)
            if dst == "__IMPLICIT__":
                ends["strop"] += 1
                sources.add(("UNKNOWN", "implicit@0x%X" % p))
                seen.add((p, reg)); recorded.add((p, reg))
                continue
            if dst == reg:
                kind, val = G.classify_source(pi, src)
                ends["writer"] += 1
                seen.add((p, reg)); recorded.add((p, reg))
                if kind == "REG":
                    work.append((p, val))
                else:
                    sources.add((kind, val))
                continue
            if pi.mnemonic == "call":
                ends["call"] += 1
                sources.add(("UNKNOWN", "call@0x%X" % p))
                seen.add((p, reg)); recorded.add((p, reg))
                continue
            work.append((p, reg))
        if not progressed:
            ends["merged"] += 1
            # 不变量：每个前驱 (p,reg) 必须已在 recorded 或 expanded 里
            unrec = [p for p in preds if (p, reg) not in recorded and (p, reg) not in expanded]
            merged_detail.append((node, reg, sorted(preds), unrec))
    return sources, dict(ends=dict(ends)), merged_detail


def main():
    bn = G.Bin(G.EXE)

    print("=" * 90)
    print("D1. merged 不变量检查（全部 67 站点）")
    print("=" * 90)
    sites = []
    for t in G.TARGETS:
        for s in bn.callers_of(t):
            sites.append((s, t))
    total_merged = 0
    violations = 0
    for s, t in sorted(sites):
        srcs, meta, md = backward_instrumented(bn, s)
        if md:
            total_merged += len(md)
            for node, reg, preds, unrec in md:
                print("  0x%08X merged@0x%X reg=%s preds=%s 未记录前驱=%s"
                      % (s, node, reg, ["0x%X" % p for p in preds],
                         ["0x%X" % p for p in unrec]))
                if unrec:
                    violations += 1
    print("  merged 事件总数=%d，不变量违反=%d" % (total_merged, violations))

    print("\n" + "=" * 90)
    print("D2. 0x724530 / 0x724540 上下文")
    print("=" * 90)
    a = 0x724500
    while a < 0x7245A0:
        i = bn.code.get(a)
        if i is None:
            print("  0x%08X  <not decoded>" % a); a += 1; continue
        mk = ""
        if a in (0x724520, 0x724530, 0x724540, 0x724580):
            mk = "   <<< TARGET"
        print("  0x%08X  %-24s %-8s %s%s" % (a, i.bytes.hex(" "), i.mnemonic, i.op_str, mk))
        a += i.size

    print("\n  0x724530 前驱: %s" % sorted("0x%X" % x for x in bn.prev.get(0x724530, ())))
    print("  0x724540 前驱: %s" % sorted("0x%X" % x for x in bn.prev.get(0x724540, ())))
    print("  0x724520 前驱: %s" % sorted("0x%X" % x for x in bn.prev.get(0x724520, ())))
    print("  0x724580 前驱: %s" % sorted("0x%X" % x for x in bn.prev.get(0x724580, ())))

    print("\n  --- 目标前 8 字节（看是否紧跟 ret / 对齐填充）---")
    for t in G.TARGETS:
        off = bn.va2off(t)
        print("    0x%08X 前 8 字节: %s | 该处 %s %s"
              % (t, bn.b[off - 8:off].hex(" "),
                 bn.code[t].mnemonic, bn.code[t].op_str))

    print("\n  --- 以 0x724530 为 call 目标的调用者，其上下文 ---")
    for s in bn.callers_of(0x724530) + bn.callers_of(0x724540):
        print("    站点 0x%08X:" % s)
        a = s - 24
        while a < s + 8:
            i = bn.code.get(a)
            if i is None:
                a += 1; continue
            print("      0x%08X  %-8s %s%s" % (a, i.mnemonic, i.op_str, "   <<<" if a == s else ""))
            a += i.size

    print("\n" + "=" * 90)
    print("D3. 8 个目标地址是否作为函数指针出现在镜像里（间接调用面）")
    print("=" * 90)
    for t in G.TARGETS:
        pat = struct.pack("<I", t)
        hits = []
        idx = bn.b.find(pat)
        while idx != -1:
            hits.append(idx)
            idx = bn.b.find(pat, idx + 1)
        print("  0x%08X  裸字节命中 %d 处: %s"
              % (t, len(hits), ["0x%X" % h for h in hits[:8]]))
        for h in hits[:4]:
            # 映射回 VA
            for nm, v, vs, ra, rs in bn.secs:
                if ra <= h < ra + max(vs, rs):
                    print("        偏移 0x%X → 段 %s VA 0x%X"
                          % (h, nm, bn.ib + v + (h - ra)))
                    break
            else:
                print("        偏移 0x%X → 不属于任何段（PE 头）" % h)


if __name__ == "__main__":
    main()
