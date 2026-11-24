#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-CLOSE · 四通道并集与形态判别。

通道：
  B1 池口径分支目标（各片 atlas_gaps.tsv，5 判据）        tid = 60
  B2 镜像级分支目标重算                                   tid = 59
  VT 虚表槽直指（任务 B）                                 tid = 413
  FW 前向扫描（16 对齐 + 前驱终结/填充 + 序言 + 非分支起手） tid = 438
计算四通道并集，并抽样 FW-only 的形态，判断它们是不是「函数内 ret 之后的续段」
（若是，则 FW 通道的 (2) 判据不足，不应并入函数基数）。
输出：union_channels.txt
"""
import io
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p0lib import RawPE, Sweep, Atlas, SLICES, disasm_at, trailing_pad, predecessor  # noqa: E402

OUT = []


def w(s=""):
    print(s)
    OUT.append(s)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    pe = RawPE()
    t = pe.byname[".text"]
    TLO = pe.imagebase + t["va"]
    THI = TLO + t["vsize"]
    sw = Sweep(pe, TLO, THI)
    at = Atlas()

    def load_set(path, key="address"):
        s = set()
        for r in io.open(os.path.join(HERE, path), encoding="utf-8").read().splitlines()[1:]:
            p = r.split("\t")
            if len(p) > 1 and p[8] == "TRUE":
                s.add(int(p[1], 16))
        return s

    B1 = load_set("TRUE_ENTRY_UNIFIED.tsv")
    B2 = load_set("TRUE_ENTRY_MIRRORWIDE.tsv")
    FW = load_set("TRUE_ENTRY_ORPHAN.tsv")
    VT = set()
    V = json.load(io.open(os.path.join(HERE, "vt_direct_summary.json"), encoding="utf-8"))
    for k, v in V["per_slice"].items():
        VT |= set(int(a, 16) for a in v["list"])

    w("# 四通道并集")
    w("  B1 池口径分支目标（交付口径 5 判据）= %d" % len(B1))
    w("  B2 镜像级分支目标重算               = %d" % len(B2))
    w("  VT 虚表槽直指（任务 B）             = %d" % len(VT))
    w("  FW 前向扫描                         = %d" % len(FW))
    U = B1 | B2 | VT | FW
    w("  并集 U                              = %d" % len(U))
    w("")
    w("  两两交集：B1∩VT=%d  B1∩FW=%d  VT∩FW=%d  B2∩FW=%d"
      % (len(B1 & VT), len(B1 & FW), len(VT & FW), len(B2 & FW)))
    w("  FW-only（不是任何分支目标、也不是虚表槽）= %d" % len(FW - B1 - B2 - VT))
    w("  VT-only（不是分支目标、也不是 FW）      = %d" % len(VT - B1 - B2 - FW))
    w("  B1-only                                = %d" % len(B1 - VT - FW))
    w("")
    w("## FW-only 抽样形态（判断是否函数内 ret 之后的续段）")
    fw_only = sorted(FW - B1 - B2 - VT)
    w("  合计 %d，前 30 条：" % len(fw_only))
    for x in fw_only[:30]:
        il = disasm_at(pe, x, n=5, span=32)
        pad, pb = trailing_pad(pe, x)
        i = at.entries and None
        # 上一 atlas entry
        import bisect
        j = bisect.bisect_right(at.entries, x) - 1
        E = at.entries[j]
        pend = E + dict(at.rows)[E]
        # 后向：FW 之前最近的 atlas entry 的 size 是否终止在 pend
        w("  %08X pad=%-2d prev=%-22s | %s" % (
            x, pad, " ; ".join("%s %s" % (y[0], y[1])[:20] for y in il[:4]),
            "prevEntry=%08X end=%08X d=%d" % (E, pend, x - pend)))

    w("")
    w("## 判别：FW-only 中「上一 atlas entry 已 ret/jmp 终结」的比例")
    term_ok = 0
    tot = 0
    for x in fw_only:
        import bisect
        j = bisect.bisect_right(at.entries, x) - 1
        E = at.entries[j]
        pend = E + dict(at.rows)[E]
        k = sw.index_of(pend)
        last = sw.mn(k - 1) if (k > 0 and k >= 0) else "?"
        tot += 1
        if last in ("ret", "retn", "retf", "jmp", "int3"):
            term_ok += 1
    w("  %d/%d 的上一 entry 在自身末尾已终结（⇒ 边界干净，不是同函数续段）" % (term_ok, tot))

    io.open(os.path.join(HERE, "union_channels.txt"), "w", encoding="utf-8").write(
        "\n".join(OUT) + "\n")
    print("\nwrote union_channels.txt")


if __name__ == "__main__":
    main()
