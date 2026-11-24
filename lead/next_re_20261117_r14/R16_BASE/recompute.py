# -*- coding: utf-8 -*-
"""R16 Lead 接手基线复算（纯表内记账：数行、按列统计、快照比对）。

判据一律从权威实现抄：
  strict   = RULING_R15_20261119/work/strict_panel.py 第 78 行
             （atlas 内 ∧ grade=='[已证]' ∧ 第4列不含字面 "[未证]"）
  ④ 已成文 = MERGE_M79/verify.py 第 159 行
             （grade=='[已证]' ∧ 第4列含字符 "④"）
  atlas 比对 = strict_panel.py 第 34-41 行 ne() 归一（atlas entry 列小写，必须归一）
"""
import csv, hashlib, json, math, os, re, collections, sys

sys.stdout.reconfigure(encoding="utf-8")

PROJ  = r"D:\Project\ra2-campaign-forge"
ROOT  = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV   = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
EXE   = os.path.join(PROJ, "ra2youli", "gamemd.exe")
OUT   = os.path.join(ROOT, "R16_BASE")

RE_SLOT = re.compile(r"::v?slot\d+$")
RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")


def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main():
    rep = []

    # ---------- 文件指纹 ----------
    rep.append("## 1. 文件指纹")
    rep.append("coverage.tsv  bytes=%d  sha256=%s" % (os.path.getsize(COV), sha256_of(COV)))
    if os.path.exists(EXE):
        rep.append("gamemd.exe    bytes=%d  sha256=%s" % (os.path.getsize(EXE), sha256_of(EXE)))
    rep.append("atlas         bytes=%d" % os.path.getsize(ATLAS))

    # ---------- atlas ----------
    atlas = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip():
                atlas.add(ne(p[0]))

    # ---------- coverage ----------
    with open(COV, encoding="utf-8-sig", newline="") as f:
        rd = list(csv.reader(f, delimiter="\t"))
    hdr, cov = rd[0], rd[1:]
    rep.append("")
    rep.append("## 2. coverage.tsv 形状")
    rep.append("header(逗号分隔提示): %s" % ",".join(hdr))
    rep.append("数据行 = %d ; 列数分布 = %s" %
               (len(cov), dict(collections.Counter(len(r) for r in cov))))
    rep.append("atlas 条目 = %d" % len(atlas))

    # ---------- grade ----------
    rep.append("")
    rep.append("## 3. grade 分布（全表）")
    gc = collections.Counter(r[4].strip() for r in cov)
    tot = len(cov)
    for k, v in gc.most_common():
        rep.append("  %-12s %6d  %6.2f%%" % (k, v, 100.0 * v / tot))

    # ---------- atlas 内 / 外 ----------
    inside = [r for r in cov if ne(r[0]) in atlas]
    outside = [r for r in cov if ne(r[0]) not in atlas]
    rep.append("")
    rep.append("## 4. atlas 内/外")
    rep.append("atlas 内行 = %d ; atlas 外行 = %d" % (len(inside), len(outside)))
    rep.append("atlas 内 [已证] = %d ; atlas 外 [已证] = %d" % (
        sum(1 for r in inside if r[4].strip() == "[已证]"),
        sum(1 for r in outside if r[4].strip() == "[已证]")))
    rep.append("atlas 内【全部】[已证]口径（不限 grade 列位置）:")
    rep.append("  atlas 内 且 grade=[已证] = %d" % sum(1 for r in inside if r[4].strip() == "[已证]"))

    # ---------- strict ----------
    proved_strict = [r for r in inside if r[4].strip() == "[已证]" and "[未证]" not in r[3]]
    rep.append("")
    rep.append("## 5. TOTAL strict（atlas内 ∧ [已证] ∧ 第4列不含字面 \"[未证]\"）")
    rep.append("TOTAL strict = %d  (分母 atlas_n=%d, %.2f%%)" %
               (len(proved_strict), len(inside), 100.0 * len(proved_strict) / len(inside)))

    # 未归一对照（验证归一确有必要）
    naive = [r for r in cov if r[0].strip() in atlas or r[0].strip().upper() in atlas]
    rep.append("对照：不做 ne() 归一时 atlas 内行 = %d（差异即小写 entry 漏配数）" % len(naive))

    # ---------- ④ 已成文 ----------
    four = [r for r in cov if r[4].strip() == "[已证]" and "\u2463" in r[3]]
    rep.append("")
    rep.append("## 6. ④ 已成文（grade=[已证] ∧ 第4列含字符 ④）")
    rep.append("④ 已成文 = %d / %d = %.2f%%" %
               (len(four), gc["[已证]"], 100.0 * len(four) / gc["[已证]"]))

    # 语义栏含字面 [未证] 的 [已证] 行（F3a 同族，供交叉核对）
    f3 = [r for r in cov if r[4].strip() == "[已证]" and "[未证]" in r[3]]
    rep.append("[已证] 且第4列含 [未证] = %d" % len(f3))
    rep.append("（check: 1654 - %d = %d ）" % (len(f3), gc["[已证]"] - len(f3)))

    # ---------- 逐子系统 strict 与达标 ----------
    d = collections.defaultdict(collections.Counter)
    for r in cov:
        e = ne(r[0])
        s = r[1].strip()
        if e not in atlas:
            continue
        name, sem, grade = r[2].strip(), r[3], r[4].strip()
        d[s]["atlas_n"] += 1
        if name and not name.startswith("sub_"):
            d[s]["named_L"] += 1
            if not RE_CSUB.search(name):
                d[s]["named_S14"] += 1
                if not RE_SLOT.search(name):
                    d[s]["named_strict"] += 1
        if grade == "[已证]":
            d[s]["proved_n"] += 1
            if "[未证]" not in sem:
                d[s]["proved_strict_n"] += 1
            if "\u2463" in sem:
                d[s]["four_n"] += 1

    rep.append("")
    rep.append("## 7. 逐子系统（strict_panel.py 口径）")
    hdrline = ("S     atlas  namedS14 namedStr  proved provedSt   four  thrN thrP  "
               "n%(R14) n%(str)  p%  p%(str)  nominal strict")
    rep.append(hdrline)
    tots = collections.Counter()
    nom, strict = [], []
    for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
        c = d[s]
        a = c["atlas_n"]
        tn, tp = math.ceil(0.9 * a), math.ceil(0.5 * a)
        ok_n = c["named_S14"] >= tn
        ok_p = c["proved_n"] >= tp
        ok_ps = c["proved_strict_n"] >= tp
        rep.append("%-5s %6d %9d %8d %7d %9d %6d %5d %4d %8.2f %7.2f %5.2f %7.2f   %-5s %-5s" % (
            s, a, c["named_S14"], c["named_strict"], c["proved_n"], c["proved_strict_n"],
            c["four_n"], tn, tp,
            100.0 * c["named_S14"] / a if a else 0, 100.0 * c["named_strict"] / a if a else 0,
            100.0 * c["proved_n"] / a if a else 0, 100.0 * c["proved_strict_n"] / a if a else 0,
            ok_n and ok_p, ok_n and ok_ps))
        for k in ("atlas_n", "named_L", "named_S14", "named_strict", "proved_n", "proved_strict_n", "four_n"):
            tots[k] += c[k]
        if ok_n and ok_p:
            nom.append(s)
        if ok_n and ok_ps:
            strict.append(s)
    rep.append("")
    rep.append("TOTAL atlas_n=%d named_S14=%d named_strict=%d proved=%d proved_strict=%d four=%d" %
               (tots["atlas_n"], tots["named_S14"], tots["named_strict"],
                tots["proved_n"], tots["proved_strict_n"], tots["four_n"]))
    rep.append("名义达标 %d/22 : %s" % (len(nom), ",".join(nom)))
    rep.append("严格达标 %d/22 : %s" % (len(strict), ",".join(strict)))

    # ---------- evidence_path 粗分类（只看第6列字面，不做文件系统解析） ----------
    rep.append("")
    rep.append("## 8. evidence_path 字面形态（Lead 只数形态，不判可解析性）")
    ev = [r for r in cov if r[4].strip() == "[已证]"]
    c2 = collections.Counter()
    for r in ev:
        p = r[5].strip()
        if not p:
            c2["EMPTY"] += 1
        elif "classification_trace" in p and not re.search(r"(?<!classification_)trace", p.replace("classification_trace", "")) and ";" not in p and "/evidence/" not in p and "\\evidence\\" not in p:
            c2["TRACE_ONLY_literal"] += 1
        else:
            c2["OTHER"] += 1
    for k, v in c2.most_common():
        rep.append("  %-20s %5d" % (k, v))
    rep.append("  （权威口径见 EVID_RESOLVE/resolve.py —— 上述字面粗分不能替代它）")

    os.makedirs(OUT, exist_ok=True)
    txt = "\n".join(rep) + "\n"
    with open(os.path.join(OUT, "RECOMPUTE.md"), "w", encoding="utf-8") as f:
        f.write(txt)
    print(txt)


main()
