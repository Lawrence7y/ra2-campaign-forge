#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-CLOSE · 任务 A 补齐性校核（镜像级重算，不依赖各片 gap 列表）。

各片 `atlas_gaps.tsv` 的候选池不保证完备（例：C04 只写了 26 个 rel32 行，
71 个 jmp8 目标从未入表；孤儿入口在原理上没有分支指向，任何目标扫都看不到）。
本脚本做镜像级重算：全 .text 的直接分支目标（E8/E9/EB/7x/0F8x）→ 去掉 atlas 覆盖 →
同一套 5 项判据 → 逐片计数。用于回答「任务 A 的 42 是否完备」。

输出：TRUE_ENTRY_MIRRORWIDE.tsv
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

    # 直接分支目标
    tgt = {}
    for i in range(sw.n):
        m = sw.mn(i)
        if m == "call" or m == "jmp" or m in JCC:
            a = sw.starts[i]
            d = pe.read(a, 8)
            if not d:
                continue
            b0 = d[0]
            if b0 == 0xE8:
                ch = "call32"
            elif b0 == 0xE9:
                ch = "jmp32"
            elif b0 == 0xEB:
                ch = "jmp8"
            elif 0x70 <= b0 <= 0x7F:
                ch = "jcc8"
            elif b0 == 0x0F and len(d) > 1 and 0x80 <= d[1] <= 0x8F:
                ch = "jcc32"
            else:
                ch = "other"
            # 目标地址从 capstone 已解出的操作数取
            # （Sweep 未存 op_str，这里对单条指令重解）
            one = None
            for ins in __import__("capstone").Cs(
                    __import__("capstone").CS_ARCH_X86,
                    __import__("capstone").CS_MODE_32).disasm(d, a):
                one = ins
                break
            if one is None:
                continue
            op = one.op_str
            if not op.startswith("0x"):
                continue
            try:
                T = int(op, 16)
            except ValueError:
                continue
            if not (TLO <= T < THI):
                continue
            tgt.setdefault(T, set()).add(ch)

    cand = sorted(T for T in tgt if not at.in_atlas(T))
    print("直接分支目标（落 .text）= %d；其中 atlas 未覆盖 = %d" % (len(tgt), len(cand)))

    ranges = sorted(((sl,) + at.slice_range(sl) for sl in SLICES), key=lambda x: x[1])

    def slice_of(x):
        for sl, a, b in ranges:
            if a <= x < b:
                return sl
        for sl, a, b in ranges:
            if x < a:
                return sl + "*"
        return "C10*"

    rows = []
    per_slice_set = {}
    for T in cand:
        sl = slice_of(T)
        per_slice_set.setdefault(sl, set()).add(T)
    for T in cand:
        sl = slice_of(T)
        first = disasm_at(pe, T, n=6, span=48)
        f0 = first[0]
        f1 = first[1] if len(first) > 1 else None
        fmn = f0[0]
        c1 = (T % 16 == 0)
        pr = predecessor(pe, sw, T)
        c2 = pr["kind"] in ("nop", "ret", "jmp", "int3")
        c3 = None if fmn == ".byte" else (
            False if (fmn in JCC or (fmn in ("test", "cmp") and f1 and f1[0] in JCC)) else True)
        raw4 = pe.read(T, 3)
        c4 = bool(raw4) and (raw4[0] == 0x55 or
                             (len(raw4) > 1 and raw4[0] in (0x83, 0x81) and raw4[1] == 0xEC))
        hole = at.hole(T, TLO, THI)
        five = [c1, c2, c3, c4, True]
        verdict = "UNDECIDABLE" if any(x is None for x in five) else (
            "TRUE" if all(five) else "FALSE")
        chans = "+".join(sorted(tgt[T]))
        rows.append(dict(slice=sl, T=T, chan=chans, c1=c1, c2=c2, c3=c3, c4=c4, c5=True,
                         verdict=verdict, first="%s %s" % (fmn, f0[1]), pred=pr["desc"],
                         pred_kind=pr["kind"], hole=hole, earlier=None,
                         p1234=(c1 and c2 and (c3 is True) and c4)))

    # 判据 (5)：对通过 c1..c4 的候选做同洞近距贪心去重（与池口径完全同一实现）
    sup = apply_c5(rows)
    for r in rows:
        five = [r["c1"], r["c2"], r["c3"], r["c4"], r["c5"]]
        r["verdict"] = ("UNDECIDABLE" if any(x is None for x in five)
                        else ("TRUE" if all(five) else "FALSE"))

    outp = os.path.join(HERE, "TRUE_ENTRY_MIRRORWIDE.tsv")
    def YN(x):
        return "Y" if x is True else ("N" if x is False else "?")
    with io.open(outp, "w", encoding="utf-8", newline="") as f:
        f.write("slice\taddress\tchan\tc1\tc2\tc3\tc4\tc5\tverdict\tevidence\n")
        for r in rows:
            ev = "first=[%s]; prev=%s(%s); hole=%s%s" % (
                r["first"], r["pred"], r["pred_kind"],
                ("%08X-%08X" % r["hole"]) if r["hole"] else "none",
                ("; earlier=%08X" % r["earlier"]) if r["earlier"] else "")
            f.write("%s\t%08X\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                r["slice"], r["T"], r["chan"], YN(r["c1"]), YN(r["c2"]), YN(r["c3"]),
                YN(r["c4"]), YN(r["c5"]), r["verdict"], ev))
    print("wrote %s (%d rows)" % (outp, len(rows)))

    print("\n=== 镜像级重算（补齐性校核）逐片 ===")
    print("%-6s %8s %8s %10s" % ("slice", "cands", "TRUE", "UNDEC"))
    per = {}
    for sl, a, b in ranges:
        rs = [r for r in rows if r["slice"].startswith(sl)]
        per[sl] = dict(cands=len(rs), TRUE=sum(1 for r in rs if r["verdict"] == "TRUE"),
                       TRUE_list=["%08X" % r["T"] for r in rs if r["verdict"] == "TRUE"])
        print("%-6s %8d %8d %10d" % (sl, len(rs), per[sl]["TRUE"],
                                     sum(1 for r in rs if r["verdict"] == "UNDECIDABLE")))
    tt = sum(v["TRUE"] for v in per.values())
    print("%-6s %8d %8d %10d" % ("TOTAL", len(rows), tt,
                                 sum(1 for r in rows if r["verdict"] == "UNDECIDABLE")))

    # 与池口径对比
    P = json.load(io.open(os.path.join(HERE, "true_entry_summary.json"), encoding="utf-8"))
    print("\n=== 池口径（各片 atlas_gaps.tsv）vs 镜像级重算 ===")
    print("%-6s %10s %10s %8s" % ("slice", "pool TRUE", "mirror TRUE", "delta"))
    for sl in SLICES:
        p = P["per_slice"][sl]["TRUE"]
        m = per[sl]["TRUE"]
        print("%-6s %10d %10d %+8d" % (sl, p, m, m - p))
    print("%-6s %10d %10d %+8d" % ("TOTAL", P["total"]["TRUE"], tt,
                                   tt - P["total"]["TRUE"]))
    pset = set("%08X" % r["T"] for r in json.load(io.open(
        os.path.join(HERE, "true_entry_unified.json"), encoding="utf-8"))
        if r["verdict"] == "TRUE")
    mset = set("%08X" % r["T"] for r in rows if r["verdict"] == "TRUE")
    print("  仅池口径: %s" % sorted(pset - mset))
    print("  仅镜像级: %s" % sorted(mset - pset))

    json.dump(dict(total=tt, per_slice=per, cands=len(rows)),
              io.open(os.path.join(HERE, "mirrorwide_summary.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
