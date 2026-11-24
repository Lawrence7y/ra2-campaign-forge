# -*- coding: utf-8 -*-
"""strict_panel.py 的本地副本：口径逐条照权威实现
RULING_R15_20261119/work/strict_panel.py（第 78 行 "[未证]" 带方括号字面过滤）。
输出写到本目录（R16_MERGE_D1_WIDE_B2/），不碰卡目录。
用法: python strict_panel_local.py <coverage路径> <输出前缀>
"""
import csv, json, os, re, collections, sys, math
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
OUT  = os.path.join(ROOT, "R16_MERGE_D1_WIDE_B2")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")

COV = sys.argv[1]
PREFIX = sys.argv[2]

RE_SLOT = re.compile(r"::v?slot\d+$")
RE_CSUB = re.compile(r"::sub_[0-9A-Fa-f]+$")

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"): e = e[2:]
    try: return "%08X" % int(e, 16)
    except ValueError: return e

def main():
    atlas = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0: continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip(): atlas.add(ne(p[0]))

    with open(COV, encoding="utf-8-sig", newline="") as f:
        cov = list(csv.reader(f, delimiter="\t"))[1:]

    d = collections.defaultdict(collections.Counter)
    for r in cov:
        if len(r) < 8: continue
        e = ne(r[0]); s = r[1].strip()
        if e not in atlas:
            d[s]["cov_nonatlas"] += 1
            continue
        name = r[2].strip(); sem = r[3]; grade = r[4].strip()
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

    rows, tot = [], collections.Counter()
    for s in sorted(k for k in d if re.match(r"^S\d\d$", k)):
        c = d[s]; a = c["atlas_n"]
        tn, tp = math.ceil(0.9*a), math.ceil(0.5*a)
        ok_n = c["named_S14"] >= tn
        ok_s = c["named_strict"] >= tn
        ok_p = c["proved_n"] >= tp
        ok_ps = c["proved_strict_n"] >= tp
        rows.append(dict(S=s, atlas_n=a,
            named_L=c["named_L"], named_S14=c["named_S14"], named_strict=c["named_strict"],
            proved_n=c["proved_n"], proved_strict_n=c["proved_strict_n"],
            thu_named=tn, thu_proved=tp,
            dod_nominal=bool(ok_n and ok_p), dod_strict=bool(ok_n and ok_ps)))
        for k in ("atlas_n","named_L","named_S14","named_strict","proved_n","proved_strict_n"):
            tot[k] += c[k]
        tot["dod_nominal"] += int(ok_n and ok_p)
        tot["dod_strict"] += int(ok_n and ok_ps)

    summary = dict(rows=rows, total=dict(tot), cov_source=COV)
    with open(os.path.join(OUT, PREFIX+"_strict_panel.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    nom = [r["S"] for r in rows if r["dod_nominal"]]
    strict = [r["S"] for r in rows if r["dod_strict"]]
    print("%s: nominal=%s strict=%s total_proved=%d total_proved_strict=%d cov_rows=%d atlas_in=%d atlas_out=%d" % (
        PREFIX, ",".join(nom), ",".join(strict), tot["proved_n"], tot["proved_strict_n"],
        len([r for r in cov if len(r)>=8]), tot["atlas_n"],
        len([r for r in cov if len(r)>=8])-tot["atlas_n"]))

main()
