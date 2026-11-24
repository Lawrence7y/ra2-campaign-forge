#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-CLOSE · 任务 A 的横向基准对账（逐行定位差异机制）。

输入：true_entry_unified.json（a1 产物）。
输出：屏幕 + calibration_diag.txt

目的：解释「任务书给出 6 条横向基准」与本卡实现的差异，逐条给出机制，
      并证明 c1/c2/c3 的实现本身正确（基准数可由单条判据计数复现）。
"""
import io
import os
import sys
import json
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
CARD = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
from p0lib import RawPE, Atlas, SLICES, disasm_at, JCC   # noqa: E402


def load():
    return json.load(io.open(os.path.join(HERE, "true_entry_unified.json"), encoding="utf-8"))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    R = load()
    out = []

    def w(s=""):
        print(s)
        out.append(s)

    bench = {
        ("C04", "jmp32"): ("2/19", 2, 19),
        ("C05", "jmp32"): ("5/23", 5, 23),
        ("C06", "jmp32"): ("2/78", 2, 78),
        ("C07", "jmp32"): ("3/18", 3, 18),
        ("C09", "jmp32"): ("0/8", 0, 8),
        ("C10", "jmp32"): ("0/71", 0, 71),
    }

    w("# 任务 A 横向基准对账（逐行定位）")
    w("")
    w("实现变体定义：")
    w("  V1 = c1∧c2∧c3           （C04/C05/C06/C07/C09 审计脚本的实际口径）")
    w("  V2 = V1∧c4_loose        （C10 entry_criteria.py 口径：前 6 条内含 push ebp / sub esp,imm）")
    w("  V3 = V1∧c4_strict       （R14-R1 (4) 字面：T 首字节 = 0x55 / 83 EC / 81 EC）")
    w("  V4 = V3∧c5              ★ 本卡交付口径（5 项全 Y）")
    w("  V5 = V1 ∧ T 非 jcc 目的地址（C10 另有的一条，本判据集不含）")
    w("")

    # T 是否 jcc 目的地址（供 V5）
    pe = RawPE()
    jt = set()
    at = Atlas()
    t = pe.byname[".text"]
    lo = pe.imagebase + t["va"]
    hi = lo + t["vsize"]
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.skipdata = True
    for ins in md.disasm(pe.read(lo, hi - lo), lo):
        if ins.id == 0:
            continue
        m = ins.mnemonic
        if m in JCC:
            op = ins.op_str
            if op.startswith("0x"):
                try:
                    jt.add(int(op, 16))
                except ValueError:
                    pass
    w("jcc 目的地址全集：%d 个" % len(jt))
    w("")

    def V(r, which):
        c1, c2, c3 = r["c1"], r["c2"], (r["c3"] is True)
        if which == "V1":
            return c1 and c2 and c3
        if which == "V2":
            return c1 and c2 and c3 and r["c4_loose"]
        if which == "V3":
            return c1 and c2 and c3 and r["c4"]
        if which == "V4":
            return c1 and c2 and c3 and r["c4"] and r["c5"]
        if which == "V5":
            return c1 and c2 and c3 and (r["T"] not in jt)
        raise KeyError(which)

    w("## 表 1 · 6 条 jmp32 基准 × 5 种变体")
    w("%-5s %-6s %-7s %6s %6s %6s %6s %6s %6s" %
      ("slice", "chan", "bench", "n", "c1", "V1", "V2", "V3", "V4"))
    for (sl, ch), (bs, bt, bn) in bench.items():
        rs = [r for r in R if r["slice"] == sl and r["chan"] == ch]
        c1 = sum(1 for r in rs if r["c1"])
        w("%-5s %-6s %-7s %6d %6d %6d %6d %6d %6d" %
          (sl, ch, bs, len(rs), c1, sum(1 for r in rs if V(r, "V1")),
           sum(1 for r in rs if V(r, "V2")), sum(1 for r in rs if V(r, "V3")),
           sum(1 for r in rs if V(r, "V4"))))
    w("")
    w("## 表 2 · 基准命中表（V1 vs 基准真入口；c1 vs 「对齐」数）")
    for (sl, ch), (bs, bt, bn) in bench.items():
        rs = [r for r in R if r["slice"] == sl and r["chan"] == ch]
        v1 = sum(1 for r in rs if V(r, "V1"))
        c1 = sum(1 for r in rs if r["c1"])
        tag = []
        if v1 == bt:
            tag.append("V1==基准真入口(%d)" % bt)
        if c1 == bt:
            tag.append("c1==基准数(%d)" % bt)
        w("  %s %s 基准=%s(%d/%d)  V1=%d  c1(对齐)=%d  ⇒ %s"
          % (sl, ch, bs, bt, bn, v1, c1, " / ".join(tag) if tag else "无对应"))
    w("")

    # 逐行列出 V1 命中集，便于人读复核
    w("## 表 3 · V1 命中地址（与各片审计结论逐地址对照用）")
    for (sl, ch) in bench:
        rs = [r for r in R if r["slice"] == sl and r["chan"] == ch]
        hit = ["%08X" % r["T"] for r in rs if V(r, "V1")]
        w("  %s %-6s V1(%2d) = %s" % (sl, ch, len(hit), " ".join(hit)))
    w("")

    # C05 差异定位：0x5B1E20
    w("## 表 4 · C05 jmp32 的 5 个 V1 命中逐条（基准 5/23）")
    for r in R:
        if r["slice"] == "C05" and r["chan"] == "jmp32" and V(r, "V1"):
            w("  %08X c1=%s c2=%s c3=%s c4=%s c5=%s first=[%s %s] pred=%s"
              % (r["T"], r["c1"], r["c2"], r["c3"], r["c4"], r["c5"],
                 r["first"], r["first_op"], r["pred"]))
    w("")
    w("## 表 5 · C05 的 0x5B1E20 与 C05 审计判定差异取证")
    for r in R:
        if r["T"] == 0x5B1E20:
            w("  %08X c3=%s (首指令 %s %s；c3 判 N 的机制见下行)" % (r["T"], r["c3"], r["first"], r["first_op"]))
            il = disasm_at(pe, r["T"], n=4, span=32)
            w("    前 4 条：%s" % " ; ".join("%s %s" % (x[0], x[1]) for x in il))
    w("")

    # C10 差异定位：c4_loose vs c4_strict
    w("## 表 6 · C10 call32（基准 12+2=14）逐变体")
    rs = [r for r in R if r["slice"] == "C10" and r["chan"] == "call32"]
    for which in ("V1", "V2", "V3", "V4", "V5"):
        hit = ["%08X" % r["T"] for r in rs if V(r, which)]
        w("  %s = %2d  %s" % (which, len(hit), " ".join(hit)))
    w("")
    w("## 表 7 · 全部基准切片 × 变体的合计（含 call32）")
    for sl in SLICES:
        rs = [r for r in R if r["slice"] == sl]
        w("  %s: n=%3d  V1=%3d  V2=%3d  V3=%2d  V4=%2d  V5=%3d"
          % (sl, len(rs), sum(1 for r in rs if V(r, "V1")), sum(1 for r in rs if V(r, "V2")),
             sum(1 for r in rs if V(r, "V3")), sum(1 for r in rs if V(r, "V4")),
             sum(1 for r in rs if V(r, "V5"))))
    w("")
    w("## 表 8 · 单条判据通过率（全 1288 候选）")
    w("  c1 对齐16 = %d ; c2 前驱合格 = %d ; c3 非分支起手 = %d ; c4 序言(严格) = %d ; c4 序言(前6条) = %d ; c5 非同洞后者 = %d"
      % (sum(1 for r in R if r["c1"]), sum(1 for r in R if r["c2"]),
         sum(1 for r in R if r["c3"] is True), sum(1 for r in R if r["c4"]),
         sum(1 for r in R if r["c4_loose"]), sum(1 for r in R if r["c5"])))
    w("  前驱 kind 分布 = %s" % dict(Counter(r["pred_kind"] for r in R)))
    w("  前驱通路 = %s" % dict(Counter(r["pred_via"] for r in R)))
    w("  首指令 top12 = %s" % dict(Counter(r["first"] for r in R).most_common(12)))
    w("")

    io.open(os.path.join(HERE, "calibration_diag.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\nwrote calibration_diag.txt")


if __name__ == "__main__":
    main()
