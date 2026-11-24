#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INVENTORY R2 — 具名候选池余量与收口判据（第二次清点，S22 池清空之后）
卡片: lead\\next_re_20261117_r14\\_cards\\INVENTORY.md

只读输入（不改其中任何字节）:
  SURVEY_3B2\\hits_detail.tsv                             (1,733 行 + 表头)
  COVERAGE\\coverage.tsv                                  (18,498 行 + 表头)
  ..\\next_re_20261112_r10\\W130_atlas\\function_atlas.tsv  (12,916 行 + 表头)
  NAMED_PUSH_S*\\{REPORT.md, base_rate.tsv, delta.tsv, 行清单 JSON}

输出（仅写入 INVENTORY_R2\\）:
  inventory.tsv   表 A（22 行，S01..S22 一行不跳）
  （表 B/C/D 的每个数字都由本脚本打印，人工抄进 REPORT.md）

口径（卡片 §输入 + §纪律）:
  * consumed 按各批 REPORT.md / base_rate.tsv 里**核过的行**算，不只算 delta；
    consumed 取"核过 ∩ real_named"（批内核过的伪名行单列，不进 remaining）。
  * 跨批去重；批间若重复消费会显式报出。
  * fn_/sub_ 地址式伪名从 real_named 剔除。
  * expected_yield 是**预期**产出，不是保证、不是"可产出"。
  * 进行中的批次（无 delta.tsv / REPORT 标"进行中"）不计入 consumed。
"""

import os
import re
import csv
import sys
import json
import collections

BASE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(BASE)
R_ROOT = os.path.dirname(R14)

HITS = os.path.join(R14, "SURVEY_3B2", "hits_detail.tsv")
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(R_ROOT, "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUT_TSV = os.path.join(BASE, "inventory.tsv")

# ------------------------------------------------------------------ 批次登记
# (批次目录, 子系统, 行清单 JSON 相对路径, 该 JSON 的形态)
#   "auto"     : list / dict{rows|selected|entries|results|candidates}
#   "dictkeys" : 字典的 key 就是 entry（S15 的 _work/analyze.json 没有行清单）
BATCHES = [
    ("NAMED_PUSH_S05_B1",  "S05", r"work\b1_rows.json",     "auto"),
    ("NAMED_PUSH_S05_B2",  "S05", r"work\b2_rows.json",     "auto"),
    ("NAMED_PUSH_S05_B3",  "S05", r"work\b3_rows.json",     "auto"),
    ("NAMED_PUSH_S06_B1",  "S06", r"_work\b1_rows.json",    "auto"),
    ("NAMED_PUSH_S06_B2",  "S06", r"_work\b2_rows.json",    "auto"),
    ("NAMED_PUSH_S06_B3",  "S06", r"_work\b3_rows.json",    "auto"),
    ("NAMED_PUSH_S07_B1",  "S07", r"work\b1_rows.json",     "auto"),
    ("NAMED_PUSH_S09_B1",  "S09", r"_work\b1_rows.json",    "auto"),
    ("NAMED_PUSH_S10_B1",  "S10", r"work\results.json",     "auto"),
    ("NAMED_PUSH_S10_B2",  "S10", r"work\results.json",     "auto"),
    ("NAMED_PUSH_S11_B1",  "S11", r"work\b1_rows.json",     "auto"),
    ("NAMED_PUSH_S12_B1",  "S12", r"_work\rows_b1.json",    "auto"),
    ("NAMED_PUSH_S12_B2",  "S12", r"_work\rows_b2.json",    "auto"),
    ("NAMED_PUSH_S13_B1",  "S13", r"_work\b1_rows.json",    "auto"),
    ("NAMED_PUSH_S14_B1",  "S14", r"_work\b1_rows.json",    "auto"),
    ("NAMED_PUSH_S14_B2",  "S14", r"_work\b2_rows.json",    "auto"),
    ("NAMED_PUSH_S15_B1",  "S15", r"_work\analyze.json",    "dictkeys"),
    ("NAMED_PUSH_S17_B1",  "S17", r"work\pass1.json",       "auto"),
    ("NAMED_PUSH_S18_B1",  "S18", r"work\b1_rows.json",     "auto"),
    ("NAMED_PUSH_S18_B2",  "S18", r"work\b2_rows.json",     "auto"),
    ("NAMED_PUSH_S18_B3",  "S18", r"work\b3_rows.json",     "auto"),
    ("NAMED_PUSH_S18_B4",  "S18", r"work\b4_rows.json",     "auto"),
    ("NAMED_PUSH_S18_B5",  "S18", r"work\b5_rows.json",     "auto"),
    ("NAMED_PUSH_S20_B1",  "S20", r"_work\b1_rows.json",    "auto"),
    ("NAMED_PUSH_S20_B2",  "S20", r"_work\b2_rows.json",    "auto"),
    ("NAMED_PUSH_S20_B3",  "S20", r"_work\b3_rows.json",    "auto"),
    ("NAMED_PUSH_S22_B1",  "S22", r"work\b1_rows.json",     "auto"),
    ("NAMED_PUSH_S22_B2",  "S22", r"work\b2_rows.json",     "auto"),
    ("NAMED_PUSH_S22_B3",  "S22", r"work\b3_rows.json",     "auto"),
    ("NAMED_PUSH_S22_B4",  "S22", r"work\b4_rows.json",     "auto"),
    ("NAMED_PUSH_S22_B5",  "S22", r"work\b5_rows.json",     "auto"),
]

# 进行中、明确不计入的批次（卡片外，用户说明"可不计"）
INFLIGHT = ["NAMED_PUSH_S16S21_B1", "NAMED_PUSH_S01S03_B1"]

PSEUDO = re.compile(r"^(?:[A-Za-z0-9_<>@$?]*::)?(?:fn|sub)_[0-9A-Fa-f]{8}$")
SLOT = re.compile(r"^[A-Za-z0-9_<>@$?,:*& ]+::v?slot\d+$", re.I)

ALL_SS = ["S%02d" % i for i in range(1, 23)]


def shape_of(nm):
    if PSEUDO.match(nm):
        return "pseudo"
    if SLOT.match(nm):
        return "slotN"
    if "::" in nm:
        return "named_member"
    return "bare"


def read_hits(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_atlas_entries(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rd = csv.DictReader(f, delimiter="\t")
        col = rd.fieldnames[0]
        return set((r[col] or "").strip().upper() for r in rd)


def read_coverage(path):
    """coverage.tsv: 表头是逗号分隔老格式，正文 8 列 TAB ⇒ 按字节切。"""
    grades = collections.Counter()
    by_entry = {}
    with open(path, "rb") as f:
        raw = f.read()
    n = 0
    for line in raw.split(b"\n")[1:]:
        if not line.strip():
            continue
        f8 = line.split(b"\t")
        assert len(f8) == 8, "coverage.tsv 列数异常: %r" % (line[:80],)
        g = f8[4].decode("utf-8")
        grades[g] += 1
        by_entry[f8[0].decode("utf-8").upper()] = g
        n += 1
    return n, grades, by_entry


def read_base_rate(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    assert len(rows) == 1, (path, len(rows))
    r = rows[0]
    return dict(
        rows_checked=int(r["rows_checked"]),
        ring2_ok=int(r["ring2_ok"]),
        ring3b_ok=int(r["ring3b_ok"]),
        ring4_ok=int(r["ring4_ok"]),
        all_four=int(r["all_four"]),
        rate=float(r["rate"]),
    )


def load_row_list(path, kind):
    with open(path, encoding="utf-8") as f:
        obj = json.load(f)
    if kind == "dictkeys":
        return [k.upper() for k in obj.keys()]
    if isinstance(obj, dict):
        for k in ("rows", "selected", "entries", "results", "candidates"):
            if k in obj and isinstance(obj[k], list):
                obj = obj[k]
                break
        else:
            raise AssertionError("无法定位行清单: %s" % path)
    ents = []
    for it in obj:
        ents.append(it.strip().upper() if isinstance(it, str) else str(it["entry"]).upper())
    return ents


def read_delta(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        lines = [l for l in f.read().splitlines() if l.strip()]
    return [l.split("\t")[0].strip().upper() for l in lines[1:]]


# ------------------------------------------------------------- REPORT 取"核过行数"
RE_T1 = re.compile(r"rows_checked\s*[：:=]\s*\*{0,2}\s*(\d+)")
RE_T2 = re.compile(r"\|\s*本批行数\s*\|\s*\*{0,2}\s*(\d+)")
RE_T3 = re.compile(r"候选(?:全|全部)\s*\*{0,2}\s*(\d+)\s*行")
RE_T3B = re.compile(r"[（(]\s*(\d+)\s*行逐行核完\s*[）)]")
RE_T4 = re.compile(r"^\|?\s*(?:NAMED_PUSH_)?(S\d\d(?:_B\d)?|B\d)\s*\|\s*(\d+)\s*\|", re.M)
RE_T5 = re.compile(r"`base_rate\.tsv`\s*[：:]\s*`[^`]*?(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)`")


def report_rows_checked(path):
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    for tier, rx in (("rows_checked", RE_T1), ("本批行数", RE_T2),
                     ("候选全N行", RE_T3), ("N行逐行核完", RE_T3B)):
        m = rx.search(txt)
        if m:
            return int(m.group(1)), tier
    m = RE_T5.search(txt)
    if m:
        return int(m.group(1)), "base_rate回显"
    m = RE_T4.search(txt)
    if m:
        return int(m.group(2)), "计数表行"
    return None, "MISSING"


def main():
    hits = read_hits(HITS)
    atlas = read_atlas_entries(ATLAS)
    cov_n, cov_grades, cov_by_entry = read_coverage(COV)

    named = [h for h in hits if h["p3b2_named"] == "True"]
    named_by_ss = collections.defaultdict(list)
    for h in named:
        named_by_ss[h["subsystem"]].append(h)

    pool_total = {}
    fn_like = {}
    real_named = {}
    real_entries = {}
    for ss in ALL_SS:
        rows = named_by_ss.get(ss, [])
        pool_total[ss] = len(rows)
        fn_like[ss] = sum(1 for h in rows if PSEUDO.match(h["name"]))
        real_named[ss] = pool_total[ss] - fn_like[ss]
        real_entries[ss] = set(h["entry"].upper() for h in rows if not PSEUDO.match(h["name"]))

    # ------------------------------------------------------------- 读批次
    problems = []
    batches = []
    checked = collections.defaultdict(set)        # ss -> set(entry) 已核过
    owner = {}                                    # entry -> 首次出现的批次
    rows_checked = collections.Counter()
    all_four = collections.Counter()
    realized = collections.Counter()              # delta ∩ [已证]
    delta_by_ss = collections.defaultdict(set)

    for name, ss, rel, kind in BATCHES:
        d = os.path.join(R14, name)
        rep = os.path.join(d, "REPORT.md")
        br = os.path.join(d, "base_rate.tsv")
        dl = os.path.join(d, "delta.tsv")
        js = os.path.join(d, rel)
        missing = [p for p in (rep, br, dl, js) if not os.path.exists(p)]
        if missing:
            problems.append("%s 缺文件: %s" % (name, missing))
            continue

        ents = load_row_list(js, kind)
        brr = read_base_rate(br)
        rep_n, rep_src = report_rows_checked(rep)
        dl_e = read_delta(dl)

        if len(ents) != brr["rows_checked"]:
            problems.append("%s: 行清单 %d ≠ base_rate rows_checked %d"
                            % (name, len(ents), brr["rows_checked"]))
        if rep_n is None:
            problems.append("%s: REPORT.md 取不到核过行数" % name)
        elif rep_n != brr["rows_checked"]:
            problems.append("%s: REPORT(%s)=%d ≠ base_rate %d"
                            % (name, rep_src, rep_n, brr["rows_checked"]))
        if not set(dl_e) <= set(ents):
            problems.append("%s: delta 有 %d 个 entry 不在核过清单: %s"
                            % (name, len(set(dl_e) - set(ents)), sorted(set(dl_e) - set(ents))[:5]))
        if len(set(ents)) != len(ents):
            problems.append("%s: 本批清单内自身重复 entry" % name)
        for e in ents:
            if e not in atlas:
                problems.append("%s: entry %s 不在 W130 function_atlas" % (name, e))
            if e not in set(h["entry"].upper() for h in named_by_ss.get(ss, [])):
                problems.append("%s: entry %s 不属于 %s 的 named 池" % (name, e, ss))
            if e in owner and owner[e] != name:
                problems.append("%s: entry %s 已被 %s 核过（跨批重复消费）" % (name, e, owner[e]))
            owner.setdefault(e, name)
            checked[ss].add(e)

        rows_checked[ss] += brr["rows_checked"]
        all_four[ss] += brr["all_four"]
        for e in dl_e:
            delta_by_ss[ss].add(e)
            if cov_by_entry.get(e) == "[已证]":
                realized[ss] += 1

        batches.append(dict(name=name, ss=ss, n=brr["rows_checked"], rep_n=rep_n,
                            rep_src=rep_src, ring2=brr["ring2_ok"], ring3b=brr["ring3b_ok"],
                            ring4=brr["ring4_ok"], af=brr["all_four"], rate=brr["rate"],
                            n_delta=len(dl_e),
                            n_realized=sum(1 for e in dl_e if cov_by_entry.get(e) == "[已证]"),
                            n_pseudo=sum(1 for e in ents if PSEUDO.match(
                                next(h["name"] for h in named_by_ss[ss]
                                     if h["entry"].upper() == e)))))

    # ------------------------------------------------------------- 表 A
    table = []
    for ss in ALL_SS:
        consumed = len(checked[ss] & real_entries[ss])
        remaining = real_named[ss] - consumed
        rc, af = rows_checked[ss], all_four[ss]
        if rc:
            rate = af / rc
            table.append(dict(ss=ss, pool=pool_total[ss], fn=fn_like[ss], real=real_named[ss],
                              consumed=consumed, remaining=remaining,
                              rate=rate, exp=remaining * rate, rc=rc, af=af,
                              rz=(realized[ss] / rc)))
        else:
            table.append(dict(ss=ss, pool=pool_total[ss], fn=fn_like[ss], real=real_named[ss],
                              consumed=consumed, remaining=remaining,
                              rate=None, exp=None, rc=0, af=0, rz=None))

    tot = dict(pool=sum(r["pool"] for r in table), fn=sum(r["fn"] for r in table),
               real=sum(r["real"] for r in table), consumed=sum(r["consumed"] for r in table),
               remaining=sum(r["remaining"] for r in table),
               rc=sum(r["rc"] for r in table), af=sum(r["af"] for r in table),
               realized=sum(realized.values()))
    g_rate = tot["af"] / tot["rc"] if tot["rc"] else 0.0
    g_rz = tot["realized"] / tot["rc"] if tot["rc"] else 0.0
    proven = cov_grades.get("[已证]", 0)

    exp_fr = sum(r["exp"] for r in table if r["exp"] is not None)
    exp_rz = sum(r["remaining"] * r["rz"] for r in table if r["rz"] is not None)
    rem_unmeasured = sum(r["remaining"] for r in table if r["rc"] == 0)

    # ------------------------------------------------------------- 写 TSV
    cols = ["subsystem", "named_pool_total", "fn_like_excluded", "real_named", "consumed",
            "remaining", "measured_rate", "expected_yield"]
    with open(OUT_TSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(cols)
        for r in table:
            w.writerow([r["ss"], r["pool"], r["fn"], r["real"], r["consumed"], r["remaining"],
                        ("%.4f" % r["rate"]) if r["rate"] is not None else "n/a",
                        ("%.1f（预期）" % r["exp"]) if r["exp"] is not None else "n/a（本子系统未跑过批次）"])

    p = print
    p("=" * 90)
    p("输入")
    p("  hits_detail        %d 行 ; named(p3b2_named=True) %d 行 ; 覆盖 %d 个子系统（无 S02/S04/S08/S19）"
      % (len(hits), len(named), len(named_by_ss)))
    p("  coverage           %d 行 ; %s" % (cov_n, dict(cov_grades)))
    p("  function_atlas     唯一 entry %d 个" % len(atlas))
    p("")
    p("读过的批次（REPORT.md / base_rate.tsv / delta.tsv / 行清单，共 %d 个）" % len(batches))
    p("%-21s %4s %4s %-12s %6s %4s %4s %4s %5s %6s %4s" %
      ("batch", "ss", "核过", "REPORT取数", "rep_n", "②", "③b", "④", "四环", "delta", "伪名"))
    for b in batches:
        p("%-21s %4s %4d %-12s %6d %4d %4d %4d %5d %6d %4d" %
          (b["name"], b["ss"], b["n"], b["rep_src"], b["rep_n"], b["ring2"], b["ring3b"],
           b["ring4"], b["af"], b["n_delta"], b["n_pseudo"]))
    p("%-21s %4s %4d %-12s %6s %4s %4s %4s %5d %6d %4d" %
      ("合计", "%d池" % len(set(b["ss"] for b in batches)), tot["rc"], "", "",
       "", "", "", tot["af"], sum(b["n_delta"] for b in batches),
       sum(b["n_pseudo"] for b in batches)))
    p("  去重后核过 entry %d 个（跨批重复消费 %d 条校验问题见末尾）"
      % (sum(len(v) for v in checked.values()), len([x for x in problems if "重复消费" in x])))
    p("  四环齐全 %d 行 → delta %d 行 → 落 [已证] %d 行"
      % (tot["af"], sum(b["n_delta"] for b in batches), tot["realized"]))
    p("")
    p("REPORT 表格行（可直接抄；最后一列 = delta 里当前 grade==[已证] 的行数）")
    for b in batches:
        p("| `%s` | %s | %d（`%s`） | %d | %d | %d | %d |"
          % (b["name"], b["ss"], b["n"], b["rep_src"], b["n_pseudo"], b["af"],
             b["n_delta"], b["n_realized"]))
    p("")
    p("表 A")
    p("%-4s %5s %4s %5s %8s %9s %-8s %-10s %6s %6s" %
      ("ss", "pool", "fn_", "real", "consumed", "remaining", "rate", "expected", "实收率", "实收预期"))
    for r in table:
        p("%-4s %5d %4d %5d %8d %9d %-8s %-10s %6s %6s" %
          (r["ss"], r["pool"], r["fn"], r["real"], r["consumed"], r["remaining"],
           ("%.4f" % r["rate"]) if r["rate"] is not None else "n/a",
           ("%.1f" % r["exp"]) if r["exp"] is not None else "n/a",
           ("%.4f" % r["rz"]) if r["rz"] is not None else "n/a",
           ("%.1f" % (r["remaining"] * r["rz"])) if r["rz"] is not None else "n/a"))
    p("%-4s %5d %4d %5d %8d %9d %-8.4f %-10.1f %6.4f %6.1f" %
      ("TOT", tot["pool"], tot["fn"], tot["real"], tot["consumed"], tot["remaining"],
       g_rate, exp_fr, g_rz, exp_rz))
    p("")
    p("表 B")
    p("  全表 real_named 合计                        %d" % tot["real"])
    p("  已消费合计                                  %d" % tot["consumed"])
    p("  剩余合计                                    %d" % tot["remaining"])
    p("  其中 已实测子系统剩余 / 未实测子系统剩余     %d / %d"
      % (tot["remaining"] - rem_unmeasured, rem_unmeasured))
    p("  加权平均四环齐全率（自报）                  %.4f (%d/%d)"
      % (g_rate, tot["af"], tot["rc"]))
    p("  加权平均实收率（落 [已证]）                  %.4f (%d/%d)"
      % (g_rz, tot["realized"], tot["rc"]))
    p("  预期可再产出（四环口径，仅已实测池）        %.1f 行" % exp_fr)
    p("  预期可再产出（实收口径，仅已实测池）        %.1f 行" % exp_rz)
    p("  现有 [已证]                                 %d / %d 行" % (proven, cov_n))
    p("  折成全表 [已证] 增幅  四环 %.3f pp / 实收 %.3f pp"
      % (100.0 * exp_fr / cov_n, 100.0 * exp_rz / cov_n))
    p("  相对现有 [已证] 增量  四环 +%.2f%% / 实收 +%.2f%%"
      % (100.0 * exp_fr / proven, 100.0 * exp_rz / proven))
    p("  剩余预期若把未实测 %d 行按全表实收率 %.4f 折算: +%.1f 行 ⇒ 合计 %.1f 行"
      % (rem_unmeasured, g_rz, rem_unmeasured * g_rz, exp_rz + rem_unmeasured * g_rz))
    p("")
    p("有剩余的子系统（remaining > 0）")
    for r in table:
        if r["remaining"] > 0:
            now = sorted((h for h in named_by_ss.get(r["ss"], [])
                          if not PSEUDO.match(h["name"])
                          and h["entry"].upper() not in checked[r["ss"]]),
                         key=lambda h: int(h["entry"], 16))
            g = collections.Counter(cov_by_entry.get(h["entry"].upper(), "NOT-IN-COV") for h in now)
            c = collections.Counter(shape_of(h["name"]) for h in now)
            p("  %-4s remaining=%2d  已实测=%s  四环率=%s  实收率=%s  预期(实收)=%s  形态=%s  grade=%s"
              % (r["ss"], r["remaining"], "是" if r["rc"] else "否",
                 ("%.4f" % r["rate"]) if r["rate"] is not None else "n/a",
                 ("%.4f" % r["rz"]) if r["rz"] is not None else "n/a",
                 ("%.2f" % (r["remaining"] * r["rz"])) if r["rz"] is not None else "n/a",
                 dict(c), dict(g)))
    p("")
    p("剩余明细（entry / name / grade / 形态）")
    for r in table:
        if r["remaining"] <= 0:
            continue
        now = sorted((h for h in named_by_ss.get(r["ss"], [])
                      if not PSEUDO.match(h["name"])
                      and h["entry"].upper() not in checked[r["ss"]]),
                     key=lambda h: int(h["entry"], 16))
        p("  %s（%d 行）:" % (r["ss"], len(now)))
        for h in now:
            p("     %s  %-46s %-10s %s" % (h["entry"], h["name"],
                                           cov_by_entry.get(h["entry"].upper(), "NOT-IN-COV"),
                                           shape_of(h["name"])))
    p("")
    p("表 D — 未消费但名字给不出类身份的行")
    d_pseudo = d_bare = d_nm = 0
    for ss in ALL_SS:
        rows = named_by_ss.get(ss, [])
        up = [h for h in rows if PSEUDO.match(h["name"]) and h["entry"].upper() not in checked[ss]]
        ub = [h for h in rows if (not PSEUDO.match(h["name"])) and shape_of(h["name"]) == "bare"
              and h["entry"].upper() not in checked[ss]]
        if not (up or ub):
            continue
        d_pseudo += len(up)
        d_bare += len(ub)
        p("  %-4s 伪名未核 %d, 裸名未核 %d :: %s"
          % (ss, len(up), len(ub), "; ".join("%s=%s" % (h["entry"], h["name"]) for h in up + ub)))
    p("  合计 伪名未核 %d + 裸名未核 %d = %d（伪名在 real_named 之外，裸名在 remaining 之内）"
      % (d_pseudo, d_bare, d_pseudo + d_bare))
    p("  ⇒ 可派余量 = remaining %d − 裸名 %d = %d 行" % (tot["remaining"], d_bare, tot["remaining"] - d_bare))
    p("")
    p("按名字形态看实测产出（全表 named %d 行）" % len(named))
    delta_all = set().union(*delta_by_ss.values()) if delta_by_ss else set()
    shp = collections.defaultdict(lambda: dict(pool=0, chk=0, dl=0, pv=0))
    for ss in ALL_SS:
        for h in named_by_ss.get(ss, []):
            s = shape_of(h["name"])
            e = h["entry"].upper()
            shp[s]["pool"] += 1
            if e in checked[ss]:
                shp[s]["chk"] += 1
                if e in delta_all:
                    shp[s]["dl"] += 1
                if cov_by_entry.get(e) == "[已证]":
                    shp[s]["pv"] += 1
    p("%-16s %6s %6s %6s %6s %9s %9s" % ("形态", "池", "已核", "delta", "已证", "delta率", "已证率"))
    for s in ("slotN", "named_member", "bare", "pseudo"):
        v = shp[s]
        if v["pool"] == 0:
            continue
        p("%-16s %6d %6d %6d %6d %9.4f %9.4f" %
          (s, v["pool"], v["chk"], v["dl"], v["pv"],
           (v["dl"] / v["chk"]) if v["chk"] else float("nan"),
           (v["pv"] / v["chk"]) if v["chk"] else float("nan")))
    p("")
    p("进行中批次（未计入 consumed）")
    for n in INFLIGHT:
        d = os.path.join(R14, n)
        if os.path.isdir(d):
            files = sorted(os.listdir(d))
            brp = os.path.join(d, "base_rate.tsv")
            note = ""
            if os.path.exists(brp):
                with open(brp, encoding="utf-8-sig") as f:
                    note = " base_rate=" + " | ".join(f.read().splitlines()[1:])
            p("  %-22s 存在; 文件 %s%s" % (n, files, note))
        else:
            p("  %-22s 不存在（可能在其他 worktree）" % n)
    p("")
    p("四环齐全但尚未落 [已证] 的行（这批是'存量回收'，不花新候选）")
    stuck = []
    for b in batches:
        for e in read_delta(os.path.join(R14, b["name"], "delta.tsv")):
            g = cov_by_entry.get(e, "NOT-IN-COV")
            if g != "[已证]":
                stuck.append((b["name"], b["ss"], e, g))
    for name, ss, e, g in stuck:
        nm = next((h["name"] for h in named_by_ss.get(ss, []) if h["entry"].upper() == e), "?")
        p("  %-21s %-4s %s  %-44s %s" % (name, ss, e, nm, g))
    p("  合计 %d 行（四环 %d − 已证 %d）；结掉它们 = +%.3f%% 的 [已证]，零新候选"
      % (len(stuck), tot["af"], tot["realized"], 100.0 * len(stuck) / proven))
    p("")
    p("收口判据计算")
    per_pool = [(r["ss"], r["remaining"], r["rz"], r["remaining"] * r["rz"])
                for r in table if r["rz"] is not None and r["remaining"] > 0]
    for ss, rem, rz, ex in per_pool:
        p("  %-4s 剩 %2d × 实收率 %.4f = %5.2f 行  ⇒ 该池 %s"
          % (ss, rem, rz, ex, "已低于 3 行（永久关闭）" if ex < 3 else "**高于 3 行（仍可开）**"))
    p("  已实测池合计 Σ = %.2f 行；未实测池剩 %d 行（无实测率，不得按全表率充数）"
      % (exp_rz, rem_unmeasured))
    p("  ⇒ 总口径（Σ < 3 行？）：%s" % ("**已收口**" if exp_rz < 3 else "**未收口**（%.2f ≥ 3）" % exp_rz))
    p("  ⇒ 逐池口径（每池 < 3 行？）：%s"
      % ("**全部池已关闭**" if all(ex < 3 for _, _, _, ex in per_pool) else "仍有池 ≥ 3"))
    # 只留 S07+S11（当前唯二每池 ≥1 行的池）再派一批的效果
    big = [(ss, rem, rz, ex) for ss, rem, rz, ex in per_pool if ex >= 1.5]
    if big:
        rows_big = sum(r for _, r, _, _ in big)
        ex_big = sum(e for _, _, _, e in big)
        p("  若再派 1 批吃掉 %s 共 %d 行（≤18）⇒ 预期 +%.2f 行，Σ 降到 %.2f 行"
          % ("+".join(ss for ss, _, _, _ in big), rows_big, ex_big, exp_rz - ex_big))
    p("")
    if problems:
        p("!! 校验问题 %d 条" % len(problems))
        for x in problems:
            p("   - " + x)
    else:
        p("校验：%d 批全部通过（行清单 == base_rate == REPORT 取数；delta ⊆ 清单；"
          "清单 ⊆ 该子系统 named 池 且 ⊆ function_atlas；无跨批重复消费）" % len(batches))
    p("=" * 90)
    return 0 if not problems else 2


if __name__ == "__main__":
    sys.exit(main())
