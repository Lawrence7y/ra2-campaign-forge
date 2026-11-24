#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-CLOSE · 任务 B 校核：
  1. 与 4 个已独立报告过的片内数字对账（C06=31 / C07=24 / C09=17 / C10=6）与镜像级 413；
  2. 检验「atlas size 低估」假说：目标相对上一 entry 末尾的偏移分布；
  3. 目标是否为任何 call/jmp/jcc 的直接目标（→ 三通道结构性看不见）；
  4. 形态抽样（16B thunk / 带序言实体）。
输出：verify_vt_direct.txt
"""
import io
import os
import sys
import json
import bisect
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p0lib import RawPE, Sweep, Atlas, SLICES, disasm_at, JCC   # noqa: E402

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
    S = json.load(io.open(os.path.join(HERE, "vt_direct_summary.json"), encoding="utf-8"))

    w("# 任务 B 校核")
    w("")
    w("## 1 · 与既有独立报告对账")
    known = {"C06": 31, "C07": 24, "C09": 17, "C10": 6}
    w("  %-6s %10s %10s %8s" % ("slice", "既有报告", "本卡 distinct", "一致"))
    for k in ("C06", "C07", "C09", "C10"):
        mine = S["per_slice"][k]["distinct"]
        w("  %-6s %10d %10d %8s" % (k, known[k], mine, "YES" if mine == known[k] else "NO"))
    w("  镜像级：既有 C10 审计报 413，本卡 distinct = %d  ⇒ %s"
      % (S["n_distinct"], "YES" if S["n_distinct"] == 413 else "NO"))
    w("  虚表定界自校：%d 张 / %d 槽（Lead 基线 1214 / 14,044）⇒ %s"
      % (S["n_tables"], S["n_slots"],
         "YES" if (S["n_tables"], S["n_slots"]) == (1214, 14044) else "NO"))
    w("")
    w("## 2 · 「atlas size 低估」假说检验：目标相对上一 entry 末尾的偏移")
    rows = []
    for k in ("C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10"):
        for a in S["per_slice"][k]["list"]:
            rows.append(int(a, 16))
    w("  不同地址合计 %d" % len(rows))
    deltas = []
    inside_next = []
    for x in rows:
        i = bisect.bisect_right(at.entries, x) - 1
        pe_ = at.entries[i]
        pend = pe_ + dict(at.rows)[pe_]
        nxt = at.entries[i + 1] if i + 1 < at.n else THI
        deltas.append(x - pend)
        inside_next.append(nxt - x)
    w("  delta = S − (上一entry + size)：min=%d max=%d" % (min(deltas), max(deltas)))
    w("  分布（按 8 字节桶）：%s" % dict(sorted(Counter((d // 8) * 8 for d in deltas).items())))
    w("  delta ∈ [0,16) = %d/%d (%.1f%%)；delta < 0（=落在上一函数内部，说明 size 未低估而是真重叠）= %d"
      % (sum(1 for d in deltas if 0 <= d < 16), len(deltas),
         100.0 * sum(1 for d in deltas if 0 <= d < 16) / len(deltas),
         sum(1 for d in deltas if d < 0)))
    w("  到下一 entry 的距离：min=%d" % min(inside_next))
    w("")
    w("## 3 · 是否为任何直接分支目标（三通道结构性盲区验证）")
    tgt = set()
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.skipdata = True
    for ins in md.disasm(pe.read(TLO, THI - TLO), TLO):
        if ins.id == 0:
            continue
        m = ins.mnemonic
        if m in ("call", "jmp") or m in JCC:
            op = ins.op_str
            if op.startswith("0x"):
                try:
                    tgt.add(int(op, 16))
                except ValueError:
                    pass
    n_ref = sum(1 for x in rows if x in tgt)
    w("  直接目标全集 = %d；413 个中同时是 call/jmp/jcc 目标的 = %d（%.1f%%）"
      % (len(tgt), n_ref, 100.0 * n_ref / len(rows)))
    w("  ⇒ %d 个不被任何直接分支引用（虚表独有），三通道（call32/jmp32/jmp8）结构性不可见"
      % (len(rows) - n_ref))
    w("")
    w("## 4 · 形态抽样（前 24 个）")
    w("  %-9s %-6s %-28s %-10s %s" % ("target", "prev", "前 3 条指令", "到上entry末", "类名/槽"))
    import csv
    det = {}
    for r in csv.DictReader(io.open(os.path.join(HERE, "VT_DIRECT_ENTRIES.tsv"),
                                    encoding="utf-8"), delimiter="\t"):
        det.setdefault(int(r["target"], 16), r)
    for x in sorted(rows)[:24]:
        d = det.get(x)
        i = bisect.bisect_right(at.entries, x) - 1
        pe_ = at.entries[i]
        pend = pe_ + dict(at.rows)[pe_]
        il = disasm_at(pe, x, n=3, span=24)
        w("  %08X %-6s %-28s +%-9d %s" % (
            x, d["note"].split("prev=")[1].split("(")[0] if "prev=" in d["note"] else "?",
            " ; ".join("%s %s" % (y[0], y[1])[:26] for y in il), x - pend,
            d["note"].split("cls=")[1].split(";")[0]))
    w("")
    w("## 5 · 槽号分布（判断是否集中在末槽）")
    sl = [int(det[x]["slot_idx"]) for x in rows if x in det]
    w("  槽号 top12 = %s" % dict(Counter(sl).most_common(12)))
    w("  末槽（slot_idx == n_slots-1 - 上一表末尾误算）无法直接判；给出 slot_idx vs 表槽数：")
    pairs = Counter()
    for x in rows:
        d = det.get(x)
        if not d:
            continue
        ns = None
        for line in io.open(os.path.join(HERE, "vt_tables.tsv"), encoding="utf-8").read().splitlines()[1:]:
            p = line.split("\t")
            if int(p[0], 16) == int(d["vt_addr"], 16):
                ns = int(p[1])
                break
        if ns:
            pairs["slot%d/%d" % (int(d["slot_idx"]), ns)] += 1
    w("  %s" % dict(pairs.most_common(10)))

    io.open(os.path.join(HERE, "verify_vt_direct.txt"), "w", encoding="utf-8").write(
        "\n".join(OUT) + "\n")
    print("\nwrote verify_vt_direct.txt")


if __name__ == "__main__":
    main()
