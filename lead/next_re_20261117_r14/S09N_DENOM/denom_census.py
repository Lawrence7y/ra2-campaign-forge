#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
S09N-DENOM — PANEL.md 的 n 列 vs coverage.tsv 实际行数 一致性普查（唯一主脚本）

只读：COVERAGE\coverage.tsv、COVERAGE\PANEL.md、W130_atlas\function_atlas.tsv、_hygiene\*.bak
只写：S09N_DENOM\ 下的 n_table.tsv / amed_check.tsv / named_check.tsv / _calc.json / _s09_atlas_out.tsv

用法：python S09N_DENOM\denom_census.py
"""
import csv, re, json, math, collections, io, sys, os, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

R14  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV   = os.path.join(R14, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(R14, "COVERAGE", "PANEL.md")
OUTSIDE = os.path.join(R14, "COVERAGE", "coverage_outside_atlas.tsv")
ATL   = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
OUT   = os.path.join(R14, "S09N_DENOM")

# ---------------- 输入 ----------------
atlas_raw = []
with open(ATL, encoding="utf-8", newline="") as f:
    rd = csv.reader(f, delimiter="\t"); next(rd)
    for row in rd:
        if row: atlas_raw.append(row[0])
ATLAS      = set(e.upper() for e in atlas_raw)   # 口径：entry 统一大写（PANEL §M47 明文）
ATLAS_EXACT = set(atlas_raw)                     # 反例口径：大小写敏感（atlas 全小写）

def load_cov(path):
    out = []
    with open(path, encoding="utf-8", newline="") as f:
        rd = csv.reader(f, delimiter="\t"); next(rd)
        for row in rd:
            if row: out.append(row)
    return out

COVROWS = load_cov(COV)

# initterm 目标集（PANEL §9.1 的 B 口径：coverage ∖ initterm）
INITTERM_TABLE = os.path.join(R14, "P0_INITTERM", "INITTERM_TABLE.tsv")
INITTERM = set()
if os.path.exists(INITTERM_TABLE):
    with open(INITTERM_TABLE, encoding="utf-8", newline="") as f:
        rd = csv.reader(f, delimiter="\t"); h = next(rd)
        ti = h.index("target")
        for row in rd:
            if row: INITTERM.add(row[ti].upper())
print(f"[initterm 目标 {len(INITTERM)} 项（PANEL §9.1 记 3,944）]")

panel, panel_line = {}, {}
pat = re.compile(r"^\|\s*(S\d\d)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|")
with open(PANEL, encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        m = pat.match(line)
        if m:
            s = m.group(1)
            panel[s] = dict(n=int(m.group(2)), nL=int(m.group(3)), pctL=float(m.group(4)),
                            nS=int(m.group(5)), pctS=float(m.group(6)),
                            nT=int(m.group(7)), pctT=float(m.group(8)),
                            proved=int(m.group(9)), pctP=float(m.group(10)))
            panel_line[s] = i
SUBS = sorted(panel)

# ---------------- named 谓词 ----------------
re_sub = re.compile(r"::sub_[0-9A-Fa-f]+$")
re_sub_anchored_only = re.compile(r"::sub_[0-9A-Fa-f]{8}$")     # 反例：字面 8 位
re_slot_any  = re.compile(r"::(v)?slot\d+")                     # 本卡口径：含
re_slot_tail = re.compile(r"::(v)?slot\d+$")                    # 反例：锚定结尾（PANEL 实测口径）
is_L = lambda n: bool(n.strip()) and not n.startswith("sub_")
is_S = lambda n: is_L(n) and not re_sub.search(n)
is_T = lambda n: is_S(n) and not re_slot_any.search(n)

# ---------------- 逐子系统普查 ----------------
rec = {}
for s in SUBS:
    rows  = [x for x in COVROWS if x[1] == s]
    inatl = [x for x in rows if x[0].upper() in ATLAS]
    rec[s] = dict(
        cov_rows=len(rows), panel_n=panel[s]["n"], panel_line=panel_line[s],
        diff=len(rows) - panel[s]["n"],
        atlas_in=len(inatl), atlas_out=len(rows) - len(inatl),
        proved=sum(1 for x in inatl if x[4] == "[已证]"),
        namedL=sum(1 for x in inatl if is_L(x[2])),
        namedS=sum(1 for x in inatl if is_S(x[2])),
        namedT=sum(1 for x in inatl if is_T(x[2])),
        namedT_tail=sum(1 for x in inatl if is_S(x[2]) and not re_slot_tail.search(x[2])),
        panel_namedL=panel[s]["nL"], panel_namedS=panel[s]["nS"], panel_namedT=panel[s]["nT"],
        panel_proved=panel[s]["proved"],
        cand_noempty=sum(1 for x in rows if x[2].strip()),
        cand_noinitterm=sum(1 for x in rows if not x[2].startswith("initterm_thunk_")),
        cand_casesens=sum(1 for x in rows if x[0] in ATLAS_EXACT),
    cand_B=sum(1 for x in rows if x[0].upper() not in INITTERM),
        ceil90=math.ceil(0.9*panel[s]["n"]), ceil50=math.ceil(0.5*panel[s]["n"]),
    )

def zero_test(key, label):
    diffs = [(s, rec[s][key] - rec[s]["panel_n"]) for s in SUBS]
    nz = [d for d in diffs if d[1] != 0]
    print(f"  [{label}] sum={sum(rec[s][key] for s in SUBS)}  diff!=0：{len(nz)}/22"
          + ("" if not nz else "  " + str(nz)))
    return dict(label=label, total=sum(rec[s][key] for s in SUBS), nonzero=len(nz), details=nz)

print("=== 口径检验：若 n 的真是该口径，则 22 个子系统 diff 应全为 0 ===")
tests = [
    zero_test("atlas_in",        "T1 coverage∩atlas 行数（大小写归一）"),
    zero_test("cov_rows",        "T2 coverage 全部行数"),
    zero_test("cand_noempty",    "T3 去掉 name 空行"),
    zero_test("cand_noinitterm", "T4 去掉 initterm_thunk_* 行"),
    zero_test("cand_B",          "T4b 去掉 INITTERM_TABLE 全部 target（PANEL §9.1 B 口径）"),
    zero_test("cand_casesens",   "T5 大小写敏感匹配的 coverage∩atlas 行数"),
]

# ---------------- 旧快照检验 ----------------
print("\n=== T6 旧快照遗留 / 面板未随合并更新 检验 ===")
hist_panel_n, snap_atlasin = {}, {}
for p in sorted(glob.glob(os.path.join(R14, "_hygiene", "PANEL.*.bak"))):
    m = re.search(r"^\|\s*S09\s*\|\s*(\d+)\s*\|", open(p, encoding="utf-8").read(), re.M)
    if m: hist_panel_n[os.path.basename(p)] = int(m.group(1))
print("  PANEL 备份中 S09 的 n：", collections.Counter(hist_panel_n.values()),
      f"({len(hist_panel_n)} 个备份)")
for b in ("coverage.M23.bak", "coverage.M43.bak", "coverage.M55.bak", "coverage.M56.bak"):
    p = os.path.join(R14, "_hygiene", b)
    if not os.path.exists(p): continue
    rows = load_cov(p)
    cnt = collections.Counter(x[1] for x in rows if x[0].upper() in ATLAS)
    snap_atlasin[b] = {s: cnt.get(s, 0) for s in SUBS}
    mism = [(s, cnt.get(s, 0), rec[s]["panel_n"]) for s in SUBS if cnt.get(s, 0) != rec[s]["panel_n"]]
    print(f"  {b}: 数据行 {len(rows)}，与现 panel_n 不一致的子系统 {len(mism)}/22 {mism}")

# ---------------- 明细输出 ----------------
print("\n=== 逐子系统普查 ===")
print(f"{'sub':4}{'cov_rows':>9}{'panel_n':>9}{'diff':>6}{'atlas_in':>9}{'atlas_out':>10}{'PANEL行':>8}")
for s in SUBS:
    r = rec[s]
    print(f"{s:4}{r['cov_rows']:9d}{r['panel_n']:9d}{r['diff']:6d}{r['atlas_in']:9d}{r['atlas_out']:10d}{r['panel_line']:8d}")

print("\n=== named 复算 vs PANEL（面板列 L / S(R14) / strict / proved）===")
print(f"{'sub':4}{'pL':>6}{'rL':>6}{'pS':>6}{'rS':>6}{'pT':>6}{'rT':>7}{'pProv':>7}{'rProv':>7}")
for s in SUBS:
    r = rec[s]
    print(f"{s:4}{r['panel_namedL']:6d}{r['namedL']:6d}{r['panel_namedS']:6d}{r['namedS']:6d}"
          f"{r['panel_namedT']:6d}{r['namedT']:7d}{r['panel_proved']:7d}{r['proved']:7d}")

print("\n=== S09 atlas 外 51 行 ===")
s09out = [x for x in COVROWS if x[1] == "S09" and x[0].upper() not in ATLAS]
fe = set()
with open(OUTSIDE, encoding="utf-8", newline="") as f:
    rd = csv.reader(f, delimiter="\t"); next(rd)
    for row in rd:
        if row: fe.add(row[0].upper())
print(f"  条数 {len(s09out)}；grade {dict(collections.Counter(x[4] for x in s09out))}；"
      f"含 slotN 命名 {sum(1 for x in s09out if re.search(r'slot[0-9]+', x[2]))}；"
      f"登记于 coverage_outside_atlas.tsv {sum(1 for x in s09out if x[0].upper() in fe)}")
for b in ("coverage.M23.bak", "coverage.M43.bak", "coverage.M55.bak", "coverage.M56.bak"):
    p = os.path.join(R14, "_hygiene", b)
    if not os.path.exists(p): continue
    m = {x[0].upper(): x[1] for x in load_cov(p)}
    print(f"  {b} 中这 51 行的 subsystem 分布: {dict(collections.Counter(m.get(x[0].upper(), '<缺>') for x in s09out))}")

# ---------------- 附带：两处辅助表的 proved 列 vs 盘上 ----------------
print("\n=== 附带发现：PANEL 辅助表 proved 列 vs 盘上重算 ===")
lines = open(PANEL, encoding="utf-8").read().splitlines()
def parse_tbl(a, b):
    out = {}
    for i in range(a - 1, b):
        p = [x.strip() for x in lines[i].split("|")]
        if len(p) > 3 and re.fullmatch(r"S\d\d", p[1]): out[p[1]] = (i + 1, p[2:])
    return out
for label, a, b, idx in (("严格双列表(103-127)", 103, 127, 1), ("M47三表(166-188)", 166, 188, 4)):
    tbl = parse_tbl(a, b); bad = []
    for s in sorted(tbl):
        pv = int(tbl[s][1][idx])
        if pv != rec[s]["proved"]: bad.append((s, pv, rec[s]["proved"]))
    print(f"  {label}: proved 列不一致 {len(bad)} 行 {bad}")

# ---------------- 写盘 ----------------
with open(os.path.join(OUT, "n_table.tsv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["subsystem", "cov_rows", "panel_n", "diff", "atlas_in_rows", "verdict"])
    for s in SUBS:
        r = rec[s]
        extra = "该子系统无 atlas 外行" if r["atlas_out"] == 0 else f"diff {r['diff']} 全为 atlas 外行"
        w.writerow([s, r["cov_rows"], r["panel_n"], r["diff"], r["atlas_in"],
                    f"n 正确 = atlas 内行数；{extra}"])

for name in ("amed_check.tsv", "named_check.tsv"):   # 卡片字面文件名 + 拼写更正别名
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["subsystem", "panel_named_L", "recalc_L", "panel_S", "recalc_S",
                    "panel_strict", "recalc_strict"])
        for s in SUBS:
            r = rec[s]
            w.writerow([s, r["panel_namedL"], r["namedL"], r["panel_namedS"], r["namedS"],
                        r["panel_namedT"], r["namedT"]])

with open(os.path.join(OUT, "_s09_atlas_out.tsv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["entry", "name", "grade", "evidence_path"])
    for x in s09out:
        w.writerow([x[0], x[2], x[4], x[5]])

with open(os.path.join(OUT, "_calc.json"), "w", encoding="utf-8") as f:
    json.dump(dict(rec=rec, tests=tests, hist_panel_n=hist_panel_n, snap_atlasin=snap_atlasin),
              f, ensure_ascii=False, indent=1)

print("\nwrote: n_table.tsv / amed_check.tsv / named_check.tsv / _s09_atlas_out.tsv / _calc.json")
