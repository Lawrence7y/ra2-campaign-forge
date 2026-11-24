#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-CLOSE · 任务 A 校核：
  1. 逐条列出 V4（交付口径）42 个 TRUE 的字节取证，供人工复核；
  2. UNDECIDABLE 逐条列出；
  3. c5 语义敏感性（「已有入口」= 全部候选 vs 仅 V3 已判真者）；
  4. 与各片自己记录的 align16 / 前驱 标签对账（独立交叉核验我的 c1/c2）。
输出：verify_true_entries.txt
"""
import io
import os
import re
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p0lib import RawPE, Sweep, Atlas, SLICES, disasm_at, trailing_pad   # noqa: E402

OUT = []


def w(s=""):
    print(s)
    OUT.append(s)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    R = json.load(io.open(os.path.join(HERE, "true_entry_unified.json"), encoding="utf-8"))
    pe = RawPE()
    t = pe.byname[".text"]
    lo = pe.imagebase + t["va"]
    hi = lo + t["vsize"]
    sw = Sweep(pe, lo, hi)
    at = Atlas()

    tru = [r for r in R if r["verdict"] == "TRUE"]
    w("# 任务 A 校核")
    w("")
    w("## 1 · 交付口径（c1..c5 全 Y）共 %d 条，逐条字节取证" % len(tru))
    for r in tru:
        T = r["T"]
        il = disasm_at(pe, T, n=8, span=64)
        back = pe.read(T - 16, 16)
        pad, pb = trailing_pad(pe, T)
        w("")
        w("%s %08X [%s] align16=Y  hole=%s" %
          (r["slice"], T, r["chan"],
           ("%08X-%08X" % tuple(r["hole"])) if r["hole"] else "none"))
        w("  T-16..T bytes: %s" % back.hex())
        w("  紧邻填充: %s×%s 前一个非填充字节=%s" %
          (pad, pb, back[-pad - 1:len(back) - pad + 0].hex() if pad and pad <= 16 else "-"))
        w("  前驱: %s (kind=%s, via=%s, 线性扫边界=%s)" %
          (r["pred"], r["pred_kind"], r["pred_via"], r["pred_boundary"]))
        w("  前 8 条: %s" % " ; ".join("%s %s" % (x[0], x[1]) for x in il))
        w("  c4 依据: %s" % (r["c4_why"] or "?"))
        w("  atlas owner(@T)=%s  最近前入口=%s" %
          (("%08X" % at.owner(T)) if at.owner(T) else "None",
           ("%08X" % r["earlier"]) if r["earlier"] else "-"))

    w("")
    w("## 2 · UNDECIDABLE 逐条")
    und = [r for r in R if r["verdict"] == "UNDECIDABLE"]
    w("  合计 %d 条" % len(und))
    for r in und:
        w("  %s %08X [%s] c3=%s 首指令原始字节=%s  evidence=%s" %
          (r["slice"], r["T"], r["chan"], r["c3"],
           pe.read(r["T"], 8).hex(), r["evidence"]))

    w("")
    w("## 3 · c5 语义敏感性")
    v3 = set(r["T"] for r in R if r["c1"] and r["c2"] and r["c3"] is True and r["c4"])
    # (a) 字面实现：同洞任一更靠前候选（含未判真者）都压制 T
    a = [r for r in R if r["c1"] and r["c2"] and r["c3"] is True and r["c4"] and r["c5"]]
    # (b) 收窄实现：只有「同洞更靠前且自身已是 V3 真入口」才压制 T
    by_slice = {}
    for r in R:
        by_slice.setdefault(r["slice"], []).append(r)
    b = []
    for r in R:
        if not (r["c1"] and r["c2"] and r["c3"] is True and r["c4"]):
            continue
        T = r["T"]
        hole = r["hole"]
        sup = None
        if hole:
            for r2 in by_slice[r["slice"]]:
                if r2["T"] < T and hole[0] <= r2["T"] < hole[1] and (T - r2["T"]) < 0x100 \
                        and r2["T"] in v3:
                    if sup is None or r2["T"] > sup:
                        sup = r2["T"]
        if sup is None:
            b.append(r)
    w("  V3（c1..c4）= %d 条" % len(v3))
    w("  (a) 字面 c5（任一更靠前候选均压制）= %d 条 ← 交付口径" % len(a))
    w("  (b) 收窄 c5（仅 V3 已判真者压制）    = %d 条" % len(b))
    w("  差额地址: %s" % " ".join("%08X" % r["T"] for r in b if r not in a))

    w("")
    w("## 4 · 与各片自记录标签的对账（独立交叉核验）")
    PAT_PREV = re.compile(r"(?:prev|前驱)=(nop|ret|jmp|int3|other|plain|jcc|call|none)")
    PAT_A = re.compile(r"align16\s*=\s*([YN10])")
    agg_prev = {}
    agg_align = {}
    for r in R:
        note = r.get("note_raw") or ""
        hay = note + "\t" + "\t".join(r.get("raw", []))
        m = PAT_PREV.search(hay)
        if m:
            v = m.group(1)
            norm = {"plain": "other", "jcc": "other", "call": "other"}.get(v, v)
            k = (r["slice"], norm, r["pred_kind"])
            agg_prev[k] = agg_prev.get(k, 0) + 1
        m2 = PAT_A.search(hay)
        if m2:
            theirs = m2.group(1) in ("Y", "1")
            k = (r["slice"], theirs, bool(r["c1"]))
            agg_align[k] = agg_align.get(k, 0) + 1

    w("  (A) 片内「align16」标签 vs 本卡 c1")
    na = nb = 0
    for k in sorted(agg_align, key=lambda x: (x[0], str(x[1]))):
        same = (k[1] == k[2])
        if same:
            na += agg_align[k]
        else:
            nb += agg_align[k]
        w("    %-4s 片内=%-5s 本卡=%-5s n=%3d %s" % (k[0], k[1], k[2], agg_align[k],
                                                    "一致" if same else "★不一致"))
    w("    小计：一致 %d，不一致 %d" % (na, nb))
    w("")
    w("  (B) 片内「prev / 前驱」标签 vs 本卡 c2 的 pred_kind")
    ma = mb = 0
    for k in sorted(agg_prev, key=lambda x: (x[0], str(x[1]))):
        same = (k[1] == k[2])
        if same:
            ma += agg_prev[k]
        else:
            mb += agg_prev[k]
        w("    %-4s 片内=%-6s 本卡=%-6s n=%3d %s" % (k[0], k[1], k[2], agg_prev[k],
                                                  "一致" if same else "★不一致"))
    w("    小计：一致 %d，不一致 %d" % (ma, mb))

    io.open(os.path.join(HERE, "verify_true_entries.txt"), "w", encoding="utf-8").write(
        "\n".join(OUT) + "\n")
    print("\nwrote verify_true_entries.txt")


if __name__ == "__main__":
    main()
