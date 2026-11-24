#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-CLOSE · 任务 B 判别：413 个未覆盖虚表目标究竟是
   (A) atlas `size` 低估（目标其实落在上一函数末尾的对齐填充里 / 上一函数未终结）
   还是 (B) 真漏收函数（上一函数已 ret/jmp 终结，中间是填充，S 是新函数体）

判别法：对每个 S，取上一 atlas entry E，size=sz，pend=E+sz。
   b1 = pend 前一条「以 pend 结尾」的指令助记符 ⇒ 是否终结符
   b2 = S 之前紧邻字节 ⇒ 填充形态
   ⇒ 若 b1 ∈ {ret,jmp,int3} ⇒ 上一函数在 pend 处已结束，S 是**新函数**（真漏收）
     若 b1 为其他 ⇒ 上一函数的线性流越过了 pend（=size 低估，S 可能是同一函数的内部）
输出：discriminate_vt.txt
"""
import io
import os
import sys
import json
import bisect
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p0lib import RawPE, Sweep, Atlas, disasm_at, trailing_pad   # noqa: E402

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
    size = dict(at.rows)
    S = json.load(io.open(os.path.join(HERE, "vt_direct_summary.json"), encoding="utf-8"))

    rows = []
    for k in S["per_slice"]:
        rows += [(k, int(a, 16)) for a in S["per_slice"][k]["list"]]
    rows.sort(key=lambda x: x[1])
    w("# 任务 B 判别：413 个未覆盖虚表目标是「size 低估」还是「真漏收函数」")
    w("")

    md_kind = Counter()
    prev_term = Counter()
    detail = []
    for sl, x in rows:
        i = bisect.bisect_right(at.entries, x) - 1
        E = at.entries[i]
        pend = E + size[E]
        # pend 处「以 pend 结尾」的指令
        j = sw.index_of(pend)
        if j >= 0 and j > 0:
            last = sw.mn(j - 1)
        else:
            # 重同步
            last = "?"
            import capstone
            md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
            md.skipdata = True
            for s in range(pend - 15, pend):
                d = pe.read(s, 16)
                for ins in md.disasm(d, s):
                    if ins.id == 0:
                        break
                    if ins.address + ins.size == pend:
                        last = ins.mnemonic
                    break
                if last != "?":
                    break
        term = last in ("ret", "retn", "retf", "jmp", "int3")
        prev_term[last] += 1
        pad, padb = trailing_pad(pe, x)
        # 分类
        if term:
            kind = "B: 上一函数已终结 ⇒ 真漏收"
        else:
            kind = "A: 上一函数流越过 pend ⇒ size 低估"
        md_kind[kind] += 1
        detail.append((sl, x, E, pend, last, term, pad, x - pend, kind))

    w("## 1 · 判别结果（%d 个不同地址）" % len(rows))
    for k, v in md_kind.most_common():
        w("  %-42s %3d  (%.1f%%)" % (k, v, 100.0 * v / len(rows)))
    w("")
    w("## 2 · 上一 entry 在 pend 处的终结指令分布")
    for k, v in prev_term.most_common(12):
        w("  %-10s %3d" % (k, v))
    w("")
    w("## 3 · 目标前填充长度分布")
    w("  %s" % dict(sorted(Counter(d[6] for d in detail).items())))
    w("")
    w("## 4 · 判为「真漏收」的样例（前 20）")
    w("  %-6s %-9s %-9s %-9s %-8s %-5s %-4s %s" %
      ("slice", "target", "prevEntry", "prevEnd", "末端指令", "pad", "d", "形态"))
    n = 0
    for sl, x, E, pend, last, term, pad, d, kind in detail:
        if not term or n >= 20:
            continue
        il = disasm_at(pe, x, n=4, span=32)
        w("  %-6s %08X %08X %08X %-8s %-5d %-4d %s" % (
            sl, x, E, pend, last, pad, d,
            " ; ".join("%s %s" % (y[0], y[1])[:22] for y in il)))
        n += 1
    w("")
    w("## 5 · 判为「size 低估」的全部清单")
    for sl, x, E, pend, last, term, pad, d, kind in detail:
        if term:
            continue
        w("  %-6s %08X prevEntry=%08X prevEnd=%08X 末端指令=%-8s d=%d" % (sl, x, E, pend, last, d))

    io.open(os.path.join(HERE, "discriminate_vt.txt"), "w", encoding="utf-8").write(
        "\n".join(OUT) + "\n")
    print("\nwrote discriminate_vt.txt")


if __name__ == "__main__":
    main()
