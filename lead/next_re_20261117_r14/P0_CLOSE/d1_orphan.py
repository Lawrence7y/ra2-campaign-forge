#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-CLOSE · 任务 A 第三条通道：孤儿入口补扫（前向扫描）。

原理：前两条通道都要求「有引用」（分支目标 / 虚表槽）。无任何引用但确实是函数入口的
「孤儿」在原理上被两者结构性漏掉（C01 审计已实证 5 个）。本脚本做前向扫描：
  遍历 .text 内全部 16 字节对齐地址 A，A ∉ atlas，且
    (2) 前驱 ∈ {nop, ret, jmp, int3}
    (3) 首指令非循环体起手
    (4) 首字节 = 0x55 / 83 EC / 81 EC
  ⇒ 与任务 A 的 5 项判据逐条一致（c1 由构造满足）。再加 (5) 贪心去重。

输出：TRUE_ENTRY_ORPHAN.tsv
"""
import io
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p0lib import (RawPE, Sweep, Atlas, SLICES, JCC, disasm_at, trailing_pad,
                   predecessor, apply_c5)   # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    pe = RawPE()
    t = pe.byname[".text"]
    TLO = pe.imagebase + t["va"]
    THI = TLO + t["vsize"]
    sw = Sweep(pe, TLO, THI)
    at = Atlas()

    ranges = sorted(((sl,) + at.slice_range(sl) for sl in SLICES), key=lambda x: x[1])

    def slice_of(x):
        for sl, a, b in ranges:
            if a <= x < b:
                return sl
        for sl, a, b in ranges:
            if x < a:
                return sl + "*"
        return "C10*"

    # 候选：16 对齐 ∧ 不在 atlas ∧ 前驱合格 ∧ 非分支起手 ∧ 有序言
    rows = []
    n_scan = 0
    for A in range((TLO + 15) & ~15, THI, 16):
        if at.in_atlas(A):
            continue
        n_scan += 1
        pr = predecessor(pe, sw, A)
        if pr["kind"] not in ("nop", "ret", "jmp", "int3"):
            continue
        raw4 = pe.read(A, 3)
        if not (raw4 and (raw4[0] == 0x55 or
                          (len(raw4) > 1 and raw4[0] in (0x83, 0x81) and raw4[1] == 0xEC))):
            continue
        first = disasm_at(pe, A, n=3, span=24)
        fmn = first[0][0]
        if fmn == ".byte":
            continue
        if fmn in JCC:
            continue
        if fmn in ("test", "cmp") and len(first) > 1 and first[1][0] in JCC:
            continue
        rows.append(dict(slice=slice_of(A), T=A, c1=True, c2=True, c3=True, c4=True,
                         c5=True, p1234=True, first="%s %s" % (fmn, first[0][1]),
                         pred=pr["desc"], pred_kind=pr["kind"],
                         hole=at.hole(A, TLO, THI)))

    print("前向扫描：16 对齐且未被 atlas 覆盖的地址 %d 个；其中通过 (2)(3)(4) = %d"
          % (n_scan, len(rows)))
    apply_c5(rows)
    for r in rows:
        r["verdict"] = "TRUE" if r["c5"] else "FALSE"

    outp = os.path.join(HERE, "TRUE_ENTRY_ORPHAN.tsv")
    with io.open(outp, "w", encoding="utf-8", newline="") as f:
        f.write("slice\taddress\tchan\tc1\tc2\tc3\tc4\tc5\tverdict\tevidence\n")
        for r in rows:
            f.write("%s\t%08X\t%s\tY\tY\tY\tY\t%s\t%s\tfirst=[%s]; prev=%s(%s); hole=%s\n" % (
                r["slice"], r["T"], "orphan-cand",
                "Y" if r["c5"] else "N", r["verdict"], r["first"], r["pred"],
                r["pred_kind"], ("%08X-%08X" % r["hole"]) if r["hole"] else "none"))
    print("wrote %s (%d rows, %d TRUE)"
          % (outp, len(rows), sum(1 for r in rows if r["verdict"] == "TRUE")))

    # 与既有两通道结果对比
    P = json.load(io.open(os.path.join(HERE, "true_entry_summary.json"), encoding="utf-8"))
    pset = set()
    for sl in SLICES:
        pset |= set(int(a, 16) for a in P["per_slice"][sl]["true_list"])
    M = json.load(io.open(os.path.join(HERE, "mirrorwide_summary.json"), encoding="utf-8"))
    mset = set()
    for sl in SLICES:
        mset |= set(int(a, 16) for a in M["per_slice"][sl]["TRUE_list"])
    oset = set(r["T"] for r in rows if r["verdict"] == "TRUE")

    print("\n=== 三通道汇总 ===")
    print("  池口径（分支目标，各片 atlas_gaps.tsv）      = %d" % len(pset))
    print("  镜像级分支目标重算                          = %d" % len(mset))
    print("  前向孤儿扫描                                = %d" % len(oset))
    print("  并集（新增 1·2 之外的孤儿）                  = %d" % len(pset | mset | oset))
    print("  仅前向通道发现（两条引用通道都看不到）        = %d  %s"
          % (len(oset - pset - mset),
             " ".join("%08X" % x for x in sorted(oset - pset - mset))))
    print("  池有而前向无: %s" % " ".join("%08X" % x for x in sorted(pset - oset)))
    print("  镜像有而前向无: %s" % " ".join("%08X" % x for x in sorted(mset - oset)))

    per = {}
    for sl in SLICES:
        s = set(r["T"] for r in rows if r["slice"].startswith(sl) and r["verdict"] == "TRUE")
        per[sl] = dict(n=len(s), list=["%08X" % x for x in sorted(s)],
                       only_orphan=["%08X" % x for x in sorted(s - pset - mset)])
        print("  %s 前向 TRUE=%3d  其中两条引用通道都漏=%3d" % (sl, len(s), len(per[sl]["only_orphan"])))

    json.dump(dict(total=len(oset), per_slice=per,
                   union=len(pset | mset | oset),
                   only_orphan_total=len(oset - pset - mset)),
              io.open(os.path.join(HERE, "orphan_summary.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
