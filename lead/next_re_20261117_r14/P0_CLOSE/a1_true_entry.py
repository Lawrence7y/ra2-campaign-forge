#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-CLOSE · 任务 A：用 R14-R1 唯一判据重算 10 片「疑似真入口」。

候选池 = 各片 `atlas_gaps.tsv` 的全部数据行（片内自己发现的洞目标）。
5 项判据全部现场由二进制判定（不依赖各片 note/first_insn 列）。

输出：P0_CLOSE\\TRUE_ENTRY_UNIFIED.tsv
"""
import io
import os
import sys
import json
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p0lib import (EXE, SHA256, RawPE, Sweep, Atlas, SLICES, JCC, disasm_at,
                   trailing_pad, predecessor, apply_c5)

HERE = os.path.dirname(os.path.abspath(__file__))
CARD = os.path.join(HERE, "..")          # next_re_20261117_r14


def sha256_of(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest().upper()


# ---------------- 候选解析 ----------------
def _is_hex(s):
    try:
        int(s, 16)
        return True
    except Exception:
        return False


def parse_gaps(sl):
    p = os.path.join(CARD, "%s_census" % sl, "atlas_gaps.tsv")
    txt = io.open(p, encoding="utf-8", errors="replace").read().splitlines()
    lines = [x for x in txt if x.strip()]
    rows = [x.split("\t") for x in lines]
    hdr = None
    if rows and not _is_hex(rows[0][0].strip()):
        hdr = [c.strip().lower() for c in rows[0]]
        rows = rows[1:]
    out = []
    for r in rows:
        rec = dict(slice=sl, raw=r)
        if hdr:
            d = dict(zip(hdr, r))
            rec["addr"] = int(d.get("target") or d.get("entry"), 16)
            rec["chan_raw"] = (d.get("chan") or d.get("kind") or "").strip()
            rec["first_raw"] = (d.get("first_insn") or "").strip()
            rec["sites_raw"] = (d.get("sites") or "").strip()
            rec["note_raw"] = " ".join(v for k, v in d.items()
                                       if k not in ("target", "entry", "chan", "kind",
                                                    "first_insn", "sites"))
            rec["verdict_raw"] = (d.get("verdict") or d.get("confidence") or "").strip()
            rec["prologue_raw"] = (d.get("prologue") or "").strip()
            rec["prev_term_raw"] = (d.get("prev_term") or "").strip()
        else:
            rec["addr"] = int(r[0], 16)
            rec["chan_raw"] = r[1].strip() if len(r) > 1 else ""
            rec["first_raw"] = r[2].strip() if len(r) > 2 else ""
            rec["sites_raw"] = r[3].strip() if len(r) > 3 else ""
            rec["note_raw"] = r[4].strip() if len(r) > 4 else ""
            rec["verdict_raw"] = ""
            rec["prologue_raw"] = ""
            rec["prev_term_raw"] = ""
        s = rec["sites_raw"]
        rec["sites"] = []
        for t in s.replace(" ", "").split(","):
            t = t.strip()
            if t and _is_hex(t) and len(t) >= 4:
                rec["sites"].append(int(t, 16))
        out.append(rec)
    return out


SW = None   # 供 site_chan 使用


def site_chan(pe, sites):
    """由引用站点的操作码字节判定真实通道（仅用于 C01–C03 未限定标签）。

    站点必须是线性扫出的指令起点，否则字节读音不可信 ⇒ 返回 unknown。
    """
    kinds = []
    for s in sites[:8]:
        if SW is not None and SW.index_of(s) < 0:
            continue
        d = pe.read(s, 2)
        if not d:
            continue
        b0 = d[0]
        if b0 == 0xE8:
            kinds.append("call32")
        elif b0 == 0xE9:
            kinds.append("jmp32")
        elif b0 == 0xEB:
            kinds.append("jmp8")
        elif 0x70 <= b0 <= 0x7F:
            kinds.append("jcc8")
        elif b0 == 0x0F and len(d) > 1 and 0x80 <= d[1] <= 0x8F:
            kinds.append("jcc32")
        elif b0 == 0xFF:
            kinds.append("indirect")
        else:
            kinds.append("other")
    if not kinds:
        return "unknown"
    for k in ("call32", "jmp32", "jmp8", "jcc8", "jcc32", "indirect", "other"):
        if k in kinds:
            return k
    return "other"


QUALIFIED = ("call32", "jmp32", "jmp8")


def norm_chan(chan_raw, pe, sites):
    c = chan_raw.lower()
    if c in QUALIFIED:
        return c, False
    if c in ("jcc32", "jcc8", "orphan", "indirect"):
        return c, False
    derived = site_chan(pe, sites)
    if derived in QUALIFIED:
        return derived, True
    return "unqualified", True


# ---------------- 判据 ----------------
def judge(pe, sw, at, T, lo, hi, same_slice_cands):
    first = disasm_at(pe, T, n=6, span=48)
    f0 = first[0] if first else (".byte", "?", T, 1)
    f1 = first[1] if len(first) > 1 else None
    fmn = f0[0]

    # (1) 16 字节对齐
    c1 = (T % 16 == 0)

    # (2) 前驱 nop 填充 / ret / jmp / int3
    pr = predecessor(pe, sw, T)
    pad_n, pad_byte = trailing_pad(pe, T)
    c2 = pr["kind"] in ("nop", "ret", "jmp", "int3")

    # (3) 首指令不是典型循环体起手
    if fmn == ".byte":
        c3 = None                      # 无法解码 ⇒ UNDECIDABLE
    elif fmn in JCC:
        c3 = False
    elif fmn in ("test", "cmp") and f1 is not None and f1[0] in JCC:
        c3 = False
    else:
        c3 = True
    # 严格变体（C07 实现口径：test/cmp 无条件视为分支起手）
    c3_strict = False if (fmn in JCC or fmn in ("test", "cmp")) else (None if fmn == ".byte" else True)

    # (4) T 处有序言：push ebp(0x55) 或 sub esp,imm(0x83 EC / 0x81 EC)
    raw4 = pe.read(T, 3)
    if len(raw4) >= 1 and raw4[0] == 0x55:
        c4, c4_why = True, "0x55 push ebp"
    elif len(raw4) >= 2 and raw4[0] == 0x83 and raw4[1] == 0xEC:
        c4, c4_why = True, "0x83 EC sub esp"
    elif len(raw4) >= 2 and raw4[0] == 0x81 and raw4[1] == 0xEC:
        c4, c4_why = True, "0x81 EC sub esp"
    else:
        c4, c4_why = False, ""
    # 宽松变体（前 6 条内出现 push ebp / sub esp,imm）—— 诊断用，非定稿判据
    joined = " ; ".join(("%s %s" % (x[0], x[1])) for x in first[:6]).lower()
    c4_loose = ("push ebp" in joined) or ("sub esp," in joined)

    # (5) 见 apply_c5 —— judge 先置 True，由调用方统一贪心判定
    c5 = True
    earlier = None
    hole = at.hole(T, lo, hi)
    five = [c1, c2, c3, c4, c5]
    verdict = "-pending-"

    # 变体（用于与各片历史口径对账，非交付口径）
    p123 = c1 and c2 and (c3 is True)
    p1234 = p123 and c4
    p1234_loose = p123 and c4_loose
    p123_strict = c1 and c2 and (c3_strict is True)
    p1235 = p123 and c5

    ev = "first=[%s %s]@%08X+%d" % (fmn, f0[1], T, f0[3])
    if pad_n:
        ev += "; pad=%d*%s" % (pad_n, pad_byte)
    ev += "; prev=%s(%s,via=%s%s)" % (pr["desc"], pr["kind"], pr["via"],
                                      "" if pr["boundary"] else ",resync")
    if hole:
        ev += "; hole=%08X-%08X" % hole
    else:
        ev += "; hole=none"
    if earlier is not None:
        ev += "; earlier=%08X(d=%d)" % (earlier, T - earlier)
    ev += "; c4=%s" % (c4_why if c4 else "no-prologue-first")
    if not c4 and c4_loose:
        ev += "(loose=Y)"
    ev += "; f6=[%s]" % " ; ".join("%s %s" % (x[0], x[1]) for x in first[:6])

    return dict(T=T, c1=c1, c2=c2, c3=c3, c4=c4, c5=c5, verdict=verdict,
                first=fmn, first_op=f0[1], first_raw=fmn,
                pred=pr["desc"], pred_kind=pr["kind"], pred_via=pr["via"],
                pred_boundary=pr["boundary"], pad_n=pad_n,
                hole=hole, earlier=earlier, c4_why=c4_why, c4_loose=c4_loose,
                c3_strict=c3_strict, evidence=ev,
                p123=p123, p1234=p1234, p1234_loose=p1234_loose,
                p123_strict=p123_strict, p1235=p1235)


def main():
    global SW
    sys.stdout.reconfigure(encoding="utf-8")
    got = sha256_of(EXE)
    print("SHA-256 = %s  %s" % (got, "OK" if got == SHA256 else "MISMATCH!"))
    assert got == SHA256
    pe = RawPE()
    t = pe.byname[".text"]
    IMGBASE = pe.imagebase
    lo = IMGBASE + t["va"]
    hi = lo + t["vsize"]
    print("ImageBase=%08X .text=[%08X,%08X) vsize=%d rawsize=%d delta=%d"
          % (IMGBASE, lo, hi, t["vsize"], t["rawsize"], t["rawsize"] - t["vsize"]))
    print("sections: " + ", ".join("%s@%08X vs=%d raw=%d" % (s["name"], IMGBASE + s["va"],
                                                             s["vsize"], s["rawsize"])
                                   for s in pe.secs if s["name"] in (".text", ".rdata", ".data")))
    sw = Sweep(pe, lo, hi)
    SW = sw
    print("linear sweep (skipdata=True): %d insn" % sw.n)
    at = Atlas()
    print("atlas: %d rows, merged intervals=%d, overlaps=%d"
          % (at.n, len(at.merged), at._overlaps))

    cands = []
    for sl in SLICES:
        g = parse_gaps(sl)
        slo, shi = at.slice_range(sl)
        for r in g:
            r["slice_lo"], r["slice_hi"] = slo, shi
            r["in_atlas"] = at.in_atlas(r["addr"])
            r["chan"], r["chan_derived"] = norm_chan(r["chan_raw"], pe, r["sites"])
        cands.extend(g)
        print("  %s: rows=%d  addr=[%08X,%08X]  chan=%s"
              % (sl, len(g), min(x["addr"] for x in g), max(x["addr"] for x in g),
                 _cnt(x["chan"] for x in g)))

    # 判据（c5 需同片候选集合）
    by_slice = {}
    for r in cands:
        by_slice.setdefault(r["slice"], set()).add(r["addr"])
    for r in cands:
        j = judge(pe, sw, at, r["addr"], r["slice_lo"], r["slice_hi"], by_slice[r["slice"]])
        r.update(j)

    # 判据 (5)：对「已通过 c1..c4」的入口候选做同洞近距贪心去重
    sup = apply_c5(cands)
    for r in cands:
        five = [r["c1"], r["c2"], r["c3"], r["c4"], r["c5"]]
        r["verdict"] = ("UNDECIDABLE" if any(x is None for x in five)
                        else ("TRUE" if all(five) else "FALSE"))
        if r["c5_sup"] is not None:
            r["evidence"] += "; c5-suppressed-by=%08X(d=%d)" % (
                r["c5_sup"], r["T"] - r["c5_sup"])
        # 字面读法（任一更早候选均压制）作为下界存证
        lit = None
        if r["hole"]:
            for t2 in sorted(by_slice[r["slice"]]):
                if t2 < r["addr"] and r["hole"][0] <= t2 < r["hole"][1] \
                        and (r["addr"] - t2) < 0x100:
                    lit = t2 if lit is None else max(lit, t2)
        r["c5_literal"] = (lit is None)
        r["c5_literal_sup"] = lit
    print("apply_c5: %d 个候选被同洞更早入口压制（贪心口径）" % len(sup))

    # 写交付 TSV
    outp = os.path.join(HERE, "TRUE_ENTRY_UNIFIED.tsv")
    def YN(x):
        return "Y" if x is True else ("N" if x is False else "?")

    with io.open(outp, "w", encoding="utf-8", newline="") as f:
        f.write("slice\taddress\tchan\tc1\tc2\tc3\tc4\tc5\tverdict\tevidence\n")
        for r in cands:
            f.write("%s\t%08X\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                r["slice"], r["addr"], r["chan"], YN(r["c1"]), YN(r["c2"]), YN(r["c3"]),
                YN(r["c4"]), YN(r["c5"]), r["verdict"],
                r["evidence"].replace("\t", " ")))
    print("\nwrote %s (%d rows)" % (outp, len(cands)))

    json.dump([{k: (v if not isinstance(v, tuple) else list(v))
                for k, v in r.items() if k not in ("raw",)} for r in cands],
              io.open(os.path.join(HERE, "true_entry_unified.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # ---------------- 汇总 ----------------
    CHANS = ("call32", "jmp32", "jmp8", "jcc8", "jcc32", "indirect", "orphan", "unqualified")
    print("\n=== 表 A · 各片 × 通道（交付口径 = c1..c5 全 Y） ===")
    print("%-5s %-12s %6s %5s %5s %5s %6s %6s %6s" %
          ("slice", "chan", "cands", "TRUE", "FALSE", "UNDEC", "p123", "p1234", "p12345"))
    tot = dict(n=0, TRUE=0, FALSE=0, UNDEC=0, p123=0, p1234=0, p1234loose=0,
               p1235=0, p123strict=0)
    per = {}
    for sl in SLICES:
        rs = [r for r in cands if r["slice"] == sl]
        per[sl] = dict(
            n=len(rs), by_chan={},
            TRUE=sum(1 for r in rs if r["verdict"] == "TRUE"),
            FALSE=sum(1 for r in rs if r["verdict"] == "FALSE"),
            UNDEC=sum(1 for r in rs if r["verdict"] == "UNDECIDABLE"),
            p123=sum(1 for r in rs if r["p123"]),
            p1234=sum(1 for r in rs if r["p1234"]),
            p1234loose=sum(1 for r in rs if r["p1234_loose"]),
            p1235=sum(1 for r in rs if r["p1235"]),
            p123strict=sum(1 for r in rs if r["p123_strict"]),
            true_list=["%08X" % r["addr"] for r in rs if r["verdict"] == "TRUE"],
        )
        for ch in CHANS:
            sub = [r for r in rs if r["chan"] == ch]
            if not sub:
                continue
            per[sl]["by_chan"][ch] = dict(
                n=len(sub),
                TRUE=sum(1 for r in sub if r["verdict"] == "TRUE"),
                FALSE=sum(1 for r in sub if r["verdict"] == "FALSE"),
                UNDEC=sum(1 for r in sub if r["verdict"] == "UNDECIDABLE"),
                p123=sum(1 for r in sub if r["p123"]),
                p1234=sum(1 for r in sub if r["p1234"]),
                TRUE_list=["%08X" % r["addr"] for r in sub if r["verdict"] == "TRUE"])
            d = per[sl]["by_chan"][ch]
            print("%-5s %-12s %6d %5d %5d %5d %6d %6d %6d" %
                  (sl, ch, d["n"], d["TRUE"], d["FALSE"], d["UNDEC"],
                   d["p123"], d["p1234"], d["TRUE"]))
        for k in ("n", "TRUE", "FALSE", "UNDEC", "p123", "p1234", "p1234loose",
                  "p1235", "p123strict"):
            tot[k] += per[sl][k]
    print("%-5s %-12s %6d %5d %5d %5d %6d %6d %6d" %
          ("TOTAL", "", tot["n"], tot["TRUE"], tot["FALSE"], tot["UNDEC"],
           tot["p123"], tot["p1234"], tot["TRUE"]))
    print("变体合计: p123=%d  p1235=%d  p1234(序言放宽到前6条)=%d  p123_strict(test/cmp无条件下=%d)"
          % (tot["p123"], tot["p1235"], tot["p1234loose"], tot["p123strict"]))

    # ---------------- 横向基准对账 ----------------
    BM = [
        ("C04", "jmp32", 2, 19), ("C05", "jmp32", 5, 23), ("C06", "jmp32", 2, 78),
        ("C07", "jmp32", 3, 18), ("C09", "jmp32", 0, 8), ("C10", "jmp32", 0, 71),
        ("C05", "call32", 32, 32), ("C06", "call32", 24, 24), ("C07", "call32", 14, 14),
        ("C09", "call32", 17, 17),
    ]
    print("\n=== 表 B · 横向基准对账（基准数 vs 本卡三种实现变体） ===")
    print("%-5s %-8s %-12s %6s %6s %6s %6s %6s" %
          ("slice", "chan", "bench", "bench", "p123", "p1234", "c1..5", "vs")
          )
    bm_out = []
    for sl, ch, bt, bn in BM:
        d = per[sl]["by_chan"].get(ch)
        if d is None:
            print("%-5s %-8s %-12s %6s %6s %6s %6s %6s" % (sl, ch, "-", bn, "n/a", "n/a", "n/a", "NO-ROW"))
            continue
        ok = "OK" if d["p123"] == bt else ("DIFF %+d" % (d["p123"] - bt))
        print("%-5s %-8s %-12s %6d %6d %6d %6d %6s" %
              (sl, ch, "%d/%d" % (bt, bn), bn, d["p123"], d["p1234"], d["TRUE"], ok))
        bm_out.append(dict(slice=sl, chan=ch, bench=bt, bench_n=bn, n=d["n"],
                           p123=d["p123"], p1234=d["p1234"], c5=d["TRUE"], match=(d["p123"] == bt)))

    json.dump(dict(total=tot, per_slice=per, bench=bm_out,
                   text=[hex(lo), hex(hi)], sweep_n=sw.n, atlas_rows=at.n,
                   atlas_overlaps=at._overlaps),
              io.open(os.path.join(HERE, "true_entry_summary.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\nwrote true_entry_summary.json")


def _cnt(it):
    from collections import Counter
    return dict(Counter(it))


if __name__ == "__main__":
    main()
