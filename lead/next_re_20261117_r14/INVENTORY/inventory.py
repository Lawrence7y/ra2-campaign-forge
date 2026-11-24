#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INVENTORY — 具名候选池余量与预期产出（收口判据）
卡片: lead\\next_re_20261117_r14\\_cards\\INVENTORY.md

只读输入（不改动其中任何字节）:
  SURVEY_3B2\\hits_detail.tsv                      (1,733 行 + 表头)
  COVERAGE\\coverage.tsv                           (18,498 行 + 表头)
  ..\\next_re_20261112_r10\\W130_atlas\\function_atlas.tsv  (12,916 行 + 表头)
  NAMED_PUSH_*\\REPORT.md / base_rate.tsv / delta.tsv / 各行清单 JSON

输出（仅写入 INVENTORY\\）:
  inventory.tsv   表 A（22 行，一行不跳）
  （表 B/C/D 由人工写入 REPORT.md，本脚本打印其全部数字）

口径要点（卡片 §输入）:
  * consumed 按各批 REPORT.md 里**核过的行数**算，不是只算 delta。
  * consumed 去重（同一 entry 跨批只记一次）。
  * fn_/sub_ 地址式伪名从 real_named 里剔除，也不计入 remaining 的消费。
  * expected_yield 是**预期**，不是保证。
"""

import csv
import json
import os
import re
import sys
import collections

BASE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(BASE)
R_ROOT = os.path.dirname(R14)

HITS = os.path.join(R14, "SURVEY_3B2", "hits_detail.tsv")
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(R_ROOT, "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUT_TSV = os.path.join(BASE, "inventory.tsv")

# ---------------------------------------------------------------- 批次登记表
# (批次目录, 子系统, 核过行清单 JSON 的相对路径)
# 清单来源优先级：该批自己落盘的 filter_*.py 输出（条目即为"本批核过行"）。
BATCHES = [
    ("NAMED_PUSH_S05_B1", "S05", r"work\b1_rows.json"),
    ("NAMED_PUSH_S05_B2", "S05", r"work\b2_rows.json"),
    ("NAMED_PUSH_S05_B3", "S05", r"work\b3_rows.json"),
    ("NAMED_PUSH_S06_B1", "S06", r"_work\b1_rows.json"),
    ("NAMED_PUSH_S06_B2", "S06", r"_work\b2_rows.json"),
    ("NAMED_PUSH_S06_B3", "S06", r"_work\b3_rows.json"),
    ("NAMED_PUSH_S10_B1", "S10", r"work\results.json"),
    ("NAMED_PUSH_S10_B2", "S10", r"work\results.json"),
    ("NAMED_PUSH_S12_B1", "S12", r"_work\rows_b1.json"),
    ("NAMED_PUSH_S12_B2", "S12", r"_work\rows_b2.json"),
    ("NAMED_PUSH_S14_B1", "S14", r"_work\b1_rows.json"),
    ("NAMED_PUSH_S14_B2", "S14", r"_work\b2_rows.json"),
    ("NAMED_PUSH_S18_B1", "S18", r"work\b1_rows.json"),
    ("NAMED_PUSH_S18_B2", "S18", r"work\b2_rows.json"),
    ("NAMED_PUSH_S18_B3", "S18", r"work\b3_rows.json"),
    ("NAMED_PUSH_S20_B1", "S20", r"_work\b1_rows.json"),
    ("NAMED_PUSH_S20_B2", "S20", r"_work\b2_rows.json"),
    ("NAMED_PUSH_S20_B3", "S20", r"_work\b3_rows.json"),
    ("NAMED_PUSH_S22_B1", "S22", r"work\b1_rows.json"),
    ("NAMED_PUSH_S22_B2", "S22", r"work\b2_rows.json"),
]

# 地址式伪名：fn_XXXXXXXX / sub_XXXXXXXX（可选 Class:: 前缀）
PSEUDO = re.compile(r"^(?:[A-Za-z0-9_<>@$?]*::)?(?:fn|sub)_[0-9A-Fa-f]{8}$")

ALL_SS = ["S%02d" % i for i in range(1, 23)]


def read_tsv_dicts(path):
    with open(path, newline="", encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        out = []
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            out.append(dict(zip(hdr, line.split("\t"))))
        return hdr, out


def read_coverage_grades(path):
    """coverage.tsv: 表头是逗号分隔的老格式，正文是 8 列 TAB。按字节切，避免歧义。"""
    grades = collections.Counter()
    by_entry = {}
    n = 0
    with open(path, "rb") as f:
        raw = f.read()
    for line in raw.split(b"\n")[1:]:
        if not line.strip():
            continue
        f8 = line.split(b"\t")
        assert len(f8) == 8, "coverage.tsv 列数异常: %r" % (line[:80],)
        grades[f8[4].decode("utf-8")] += 1
        by_entry[f8[0].decode("utf-8").upper()] = f8[4].decode("utf-8")
        n += 1
    return n, grades, by_entry


def load_json_entries(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    if isinstance(d, dict):
        for k in ("rows", "entries", "results"):
            if k in d:
                d = d[k]
                break
    assert isinstance(d, list), path
    ents = []
    for it in d:
        if isinstance(it, str):
            ents.append(it.upper())
        else:
            ents.append(str(it["entry"]).upper())
    return ents


def read_base_rate(path):
    """base_rate.tsv: batch rows_checked ring2_ok ring3b_ok ring4_ok all_four rate"""
    with open(path, newline="", encoding="utf-8") as f:
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


def read_delta_entries(path):
    with open(path, newline="", encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        out = []
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            out.append(line.split("\t")[0].upper())
    return out


RE_ROWS_CHECKED = re.compile(r"rows_checked[^0-9]{0,12}(\d+)")
RE_BENCH = re.compile(r"本批行数[^\d]{0,12}(\d+)")


def read_report_rows_checked(path):
    """从 REPORT.md 里取'核过的行数'：优先 rows_checked，退化取'本批行数'表行。"""
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    m = RE_ROWS_CHECKED.search(txt)
    if m:
        return int(m.group(1)), "rows_checked"
    m = RE_BENCH.search(txt)
    if m:
        return int(m.group(1)), "本批行数"
    return None, "MISSING"


def main():
    # ---------------------------------------------------------------- 读输入
    hits_hdr, hits = read_tsv_dicts(HITS)
    atlas_hdr, atlas = read_tsv_dicts(ATLAS)
    cov_rows, cov_grades, cov_grade_by_entry = read_coverage_grades(COV)

    atlas_entries = set(r[atlas_hdr[0]].strip().upper() for r in atlas)

    # named 池
    named = [h for h in hits if h["p3b2_named"] == "True"]
    named_by_ss = collections.defaultdict(list)
    for h in named:
        named_by_ss[h["subsystem"]].append(h)

    real_named_by_ss = {}
    pool_total_by_ss = {}
    fnlike_by_ss = {}
    for ss in ALL_SS:
        rows = named_by_ss.get(ss, [])
        pool_total_by_ss[ss] = len(rows)
        fnl = [h for h in rows if PSEUDO.match(h["name"])]
        fnlike_by_ss[ss] = len(fnl)
        real_named_by_ss[ss] = len(rows) - len(fnl)

    real_entry_set = {}  # ss -> set(entry) 属于 real_named
    for ss in ALL_SS:
        real_entry_set[ss] = set(
            h["entry"].upper() for h in named_by_ss.get(ss, []) if not PSEUDO.match(h["name"])
        )

    # ---------------------------------------------------------------- 读批次
    batches = []
    problems = []
    checked_union = collections.defaultdict(set)   # ss -> set(entry) 已核过（全部）
    checked_order = collections.defaultdict(list)
    rows_checked_by_ss = collections.Counter()
    all_four_by_ss = collections.Counter()

    for name, ss, rel in BATCHES:
        d = os.path.join(R14, name)
        rep = os.path.join(d, "REPORT.md")
        br = os.path.join(d, "base_rate.tsv")
        dl = os.path.join(d, "delta.tsv")
        js = os.path.join(d, rel)
        for p in (rep, br, dl, js):
            if not os.path.exists(p):
                problems.append("缺文件: " + p)
                continue

        ents = load_json_entries(js)
        brr = read_base_rate(br)
        rep_n, rep_src = read_report_rows_checked(rep)
        delta = read_delta_entries(dl)

        if len(ents) != brr["rows_checked"]:
            problems.append("%s: 清单 %d 行 ≠ base_rate rows_checked %d"
                            % (name, len(ents), brr["rows_checked"]))
        if rep_n is None:
            problems.append("%s: REPORT.md 里取不到核过行数" % name)
        elif rep_n != brr["rows_checked"]:
            problems.append("%s: REPORT(%s)=%d ≠ base_rate %d"
                            % (name, rep_src, rep_n, brr["rows_checked"]))
        if not set(delta) <= set(ents):
            extra = sorted(set(delta) - set(ents))
            problems.append("%s: delta 有 %d 个 entry 不在核过清单里: %s"
                            % (name, len(extra), extra[:5]))
        if len(set(ents)) != len(ents):
            problems.append("%s: 本批清单内自身有重复 entry" % name)
        for e in ents:
            if e not in atlas_entries:
                problems.append("%s: entry %s 不在 W130 function_atlas 里" % (name, e))
            if e not in real_entry_set.get(ss, set()) and e not in set(
                    h["entry"].upper() for h in named_by_ss.get(ss, [])):
                problems.append("%s: entry %s 不属于 %s 的 named 池" % (name, e, ss))

        for e in ents:
            checked_union[ss].add(e)
            checked_order[ss].append((name, e))

        rows_checked_by_ss[ss] += brr["rows_checked"]
        all_four_by_ss[ss] += brr["all_four"]

        batches.append(dict(
            name=name, ss=ss, n_checked=brr["rows_checked"], rep_n=rep_n, rep_src=rep_src,
            all_four=brr["all_four"], ring2=brr["ring2_ok"], ring3b=brr["ring3b_ok"],
            ring4=brr["ring4_ok"], rate=brr["rate"], n_delta=len(delta),
            n_unique=len(set(ents)),
            pseudo_in_batch=sum(1 for e in set(ents)
                                if PSEUDO.match(next(h["name"] for h in named_by_ss[ss]
                                                     if h["entry"].upper() == e))),
        ))

    # ---------------------------------------------------------------- 表 A
    table_a = []
    for ss in ALL_SS:
        pool = pool_total_by_ss[ss]
        fnl = fnlike_by_ss[ss]
        real = real_named_by_ss[ss]
        checked_all = checked_union.get(ss, set())
        consumed_real_entries = set(e for e in checked_all if e in real_entry_set[ss])
        consumed = len(consumed_real_entries)
        offpool = len(checked_all) - consumed     # 核过但是伪名（不计入 remaining 消费）
        remaining = real - consumed
        rc = rows_checked_by_ss[ss]
        af = all_four_by_ss[ss]
        if rc > 0:
            rate = af / rc
            rate_s = "%.4f" % rate
            exp_s = "%.1f（预期）" % (remaining * rate)
            exp_v = remaining * rate
        else:
            rate = None
            rate_s = "n/a"
            exp_s = "n/a（本子系统未跑过批次）"
            exp_v = None
        table_a.append(dict(
            subsystem=ss, named_pool_total=pool, fn_like_excluded=fnl, real_named=real,
            consumed=consumed, remaining=remaining, measured_rate=rate_s,
            expected_yield=exp_s, _rate=rate, _exp=exp_v, _rc=rc, _af=af,
            _offpool=offpool, _checked_all=len(checked_all),
        ))

    # ---------------------------------------------------------------- 汇总
    tot_pool = sum(r["named_pool_total"] for r in table_a)
    tot_fn = sum(r["fn_like_excluded"] for r in table_a)
    tot_real = sum(r["real_named"] for r in table_a)
    tot_cons = sum(r["consumed"] for r in table_a)
    tot_rem = sum(r["remaining"] for r in table_a)
    tot_rc = sum(r["_rc"] for r in table_a)
    tot_af = sum(r["_af"] for r in table_a)
    global_rate = tot_af / tot_rc if tot_rc else 0.0

    exp_measured = sum(r["_exp"] for r in table_a if r["_exp"] is not None)
    rem_unmeasured = sum(r["remaining"] for r in table_a if r["_exp"] is None)
    exp_blend = exp_measured + rem_unmeasured * global_rate

    proven = cov_grades.get("[已证]", 0)

    # ---------------------------------------------------------------- 写 tsv
    cols = ["subsystem", "named_pool_total", "fn_like_excluded", "real_named", "consumed",
            "remaining", "measured_rate", "expected_yield"]
    with open(OUT_TSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(cols)
        for r in table_a:
            w.writerow([r[c] for c in cols])

    # ---------------------------------------------------------------- 审计打印
    p = print
    p("=" * 78)
    p("输入")
    p("  hits_detail  %d 行 ; named(p3b2_named=True) %d 行" % (len(hits), len(named)))
    p("  coverage     %d 行 ; grades %s" % (cov_rows, dict(cov_grades)))
    p("  function_atlas %d 行 ; atlas 唯一 entry %d" % (len(atlas), len(atlas_entries)))
    p("  subsystems(hits) %d 个 ; 表 A 按 S01..S22 共 %d 行"
      % (len(set(h['subsystem'] for h in hits)), len(ALL_SS)))
    p("")
    p("批次（读了 %d 个 REPORT.md / base_rate.tsv / delta.tsv / 行清单）" % len(batches))
    p("%-19s %4s %6s %4s %8s %6s %6s %5s %4s" %
      ("batch", "ss", "核过", "rep", "all_four", "delta", "去重", "伪名", "rate"))
    for b in batches:
        p("%-19s %4s %6d %4d %8d %6d %6d %5d %6.4f" %
          (b["name"], b["ss"], b["n_checked"], b["rep_n"], b["all_four"],
           b["n_delta"], b["n_unique"], b["pseudo_in_batch"], b["rate"]))
    p("合计核过 %d 行（去重后 %d 行）；合计四环齐全 %d 行；批次级加权率 %.4f"
      % (tot_rc, sum(len(v) for v in checked_union.values()), tot_af, global_rate))
    p("")
    p("表 A")
    p("%-4s %6s %5s %5s %8s %9s %-7s %s" %
      ("ss", "pool", "fn_", "real", "consumed", "remaining", "rate", "expected"))
    for r in table_a:
        p("%-4s %6d %5d %5d %8d %9d %-7s %s" %
          (r["subsystem"], r["named_pool_total"], r["fn_like_excluded"], r["real_named"],
           r["consumed"], r["remaining"], r["measured_rate"], r["expected_yield"]))
    p("%-4s %6d %5d %5d %8d %9d %-7s" %
      ("TOT", tot_pool, tot_fn, tot_real, tot_cons, tot_rem, "%.4f" % global_rate))
    p("")
    p("表 B")
    p("  全表 real_named 合计        %d" % tot_real)
    p("  已消费合计                  %d" % tot_cons)
    p("  剩余合计                    %d" % tot_rem)
    p("  加权平均四环齐全率          %.4f  (%d/%d)" % (global_rate, tot_af, tot_rc))
    p("  预期可再产出(仅实测子系统)  %.1f 行" % exp_measured)
    p("  预期可再产出(未跑子系统按全表率折算) %.1f 行" % exp_blend)
    p("  其中未跑过批次的子系统剩余  %d 行" % rem_unmeasured)
    p("  coverage [已证] 现有        %d 行 / %d 行" % (proven, cov_rows))
    p("  折成 [已证] 增幅            严格 %.3f 个百分点 / 折算 %.3f 个百分点"
      % (100.0 * exp_measured / cov_rows, 100.0 * exp_blend / cov_rows))
    p("")
    p("有未消费具名候选的子系统")
    for r in table_a:
        if r["remaining"] > 0:
            p("  %s  remaining=%d  已核过=%d  实测率=%s  预期=%s"
              % (r["subsystem"], r["remaining"], r["_rc"], r["measured_rate"],
                 r["expected_yield"]))
    # ---------------------------------------------------------------- 表 D 素材
    # 未消费但"名字本身给不出类身份/槽位"的行：裸名（无 Class:: 前缀）
    BARE = lambda nm: "::" not in nm
    p("")
    p("表 D —— 未消费但不该派的行")
    p("%-4s %8s %10s %8s   %s" % ("ss", "伪名未核", "裸名未核", "合计", "明细"))
    d_tot = collections.Counter()
    for ss in ALL_SS:
        rows = named_by_ss.get(ss, [])
        unc_pseudo = [h for h in rows
                      if PSEUDO.match(h["name"]) and h["entry"].upper() not in checked_union.get(ss, set())]
        unc_bare = [h for h in rows
                    if (not PSEUDO.match(h["name"])) and BARE(h["name"])
                    and h["entry"].upper() not in checked_union.get(ss, set())]
        if not (unc_pseudo or unc_bare):
            continue
        det = "; ".join("%s=%s" % (h["entry"], h["name"]) for h in (unc_pseudo + unc_bare))
        p("%-4s %8d %10d %8d   %s" % (ss, len(unc_pseudo), len(unc_bare),
                                      len(unc_pseudo) + len(unc_bare), det))
        d_tot["pseudo"] += len(unc_pseudo)
        d_tot["bare"] += len(unc_bare)
    p("合计：伪名未核 %d + 裸名未核 %d = %d 行（这些行即使派批，② 也拿不到类身份/槽号）"
      % (d_tot["pseudo"], d_tot["bare"], d_tot["pseudo"] + d_tot["bare"]))
    p("  ↳ 两类的位置不同：伪名 %d 行在 real_named 之外（从不计入 remaining）；"
      "裸名 %d 行在 remaining 之内。" % (d_tot["pseudo"], d_tot["bare"]))
    p("  ↳ 所以：remaining %d 行 − 裸名 %d 行 = **可派余量 %d 行**"
      % (tot_rem, d_tot["bare"], tot_rem - d_tot["bare"]))
    # 全表（含已核）伪名/裸名总量，供对照
    all_pseudo = sum(fnlike_by_ss.values())
    all_bare = sum(1 for h in named if not PSEUDO.match(h["name"]) and BARE(h["name"]))
    p("全表口径：伪名 %d 行 + 裸名 %d 行 = %d / 552 named" % (all_pseudo, all_bare, all_pseudo + all_bare))
    n_pseudo_chk = sum(b["pseudo_in_batch"] for b in batches)
    n_bare_chk = sum(1 for ss in ALL_SS for h in named_by_ss.get(ss, [])
                     if (not PSEUDO.match(h["name"])) and BARE(h["name"])
                     and h["entry"].upper() in checked_union.get(ss, set()))
    p("已核过的：伪名 %d 行 / 裸名 %d 行 —— 产出 delta 0 行、落 [已证] 0 行（见下'按名字形态'表）"
      % (n_pseudo_chk, n_bare_chk))

    # ---------------------------------------------------------------- 敏感度
    p("")
    p("敏感度 —— measured_rate 的分母若只算 real_named（剔除批内伪名行）")
    for ss in ALL_SS:
        r = next(x for x in table_a if x["subsystem"] == ss)
        if r["_rc"] == 0:
            continue
        # 批内核过的伪名行数
        n_pseudo_checked = sum(b["pseudo_in_batch"] for b in batches if b["ss"] == ss)
        denom = r["_rc"] - n_pseudo_checked
        alt = (r["_af"] / denom) if denom else None
        p("  %-4s 实测率 %-7s (分母 %2d) → 仅实数分母 %-7s (分母 %2d, 剔伪名 %d) 预期 %s → %s"
          % (ss, r["measured_rate"], r["_rc"],
             ("%.4f" % alt) if alt is not None else "n/a", denom, n_pseudo_checked,
             r["expected_yield"],
             ("%.1f" % (r["remaining"] * alt)) if alt is not None else "n/a"))

    # ---------------------------------------------------------------- delta 是否已并表
    merged = collections.Counter()
    for name, ss, rel in BATCHES:
        dl = os.path.join(R14, name, "delta.tsv")
        for e in read_delta_entries(dl):
            merged[cov_grade_by_entry.get(e, "NOT-IN-COVERAGE")] += 1
    p("")
    p("delta 行在 coverage.tsv 里的当前 grade（判断是否已并表）: %s" % dict(merged))
    p("逐批 delta 的当前 grade:")
    for name, ss, rel in BATCHES:
        c = collections.Counter()
        for e in read_delta_entries(os.path.join(R14, name, "delta.tsv")):
            c[cov_grade_by_entry.get(e, "NOT-IN-COVERAGE")] += 1
        p("  %-19s %s" % (name, dict(c)))
    p("")
    p("逐批 rows_checked 出处（REPORT.md 用哪一行取数）:")
    for b in batches:
        p("  %-19s 核过=%2d  REPORT取数=%s '%s'  base_rate=%d  all_four=%d"
          % (b["name"], b["n_checked"], b["rep_src"], b["rep_n"], b["n_checked"], b["all_four"]))

    # ------------------------------------------- "真正落成 [已证]" 的实收率
    # 四环齐全是各批自报；落到 coverage.tsv 才是事实。两者差值即"报审≠落地"。
    p("")
    p("实收率 —— delta 行里当前 grade==[已证] 的比例（比 four-ring 自报更严）")
    realized_by_ss = collections.Counter()
    for name, ss, rel in BATCHES:
        for e in read_delta_entries(os.path.join(R14, name, "delta.tsv")):
            if cov_grade_by_entry.get(e) == "[已证]":
                realized_by_ss[ss] += 1
    tot_realized = sum(realized_by_ss.values())
    p("%-4s %8s %8s %8s %10s %10s" %
      ("ss", "核过", "four_ring", "已证", "four_ring率", "实收率"))
    for ss in ALL_SS:
        r = next(x for x in table_a if x["subsystem"] == ss)
        if r["_rc"] == 0:
            continue
        rz = realized_by_ss[ss]
        p("%-4s %8d %8d %8d %10.4f %10.4f" %
          (ss, r["_rc"], r["_af"], rz, r["_af"] / r["_rc"], rz / r["_rc"]))
    p("%-4s %8d %8d %8d %10.4f %10.4f" %
      ("TOT", tot_rc, tot_af, tot_realized,
       tot_af / tot_rc, tot_realized / tot_rc))
    p("  92 行四环里 %d 行已落 [已证]，%d 行仍是 [静态推断]/[未证] ⇒ 自报率 %.4f 高于实收率 %.4f"
      % (tot_realized, tot_af - tot_realized, tot_af / tot_rc, tot_realized / tot_rc))
    p("")
    p("若 expected_yield 改用实收率（含未跑子系统按全表实收率折算）:")
    exp_measured_rz = 0.0
    for ss in ALL_SS:
        r = next(x for x in table_a if x["subsystem"] == ss)
        if r["_rc"] == 0:
            continue
        exp_measured_rz += r["remaining"] * (realized_by_ss[ss] / r["_rc"])
    glob_rz = tot_realized / tot_rc
    rem_unm = sum(r["remaining"] for r in table_a if r["_rc"] == 0)
    p("  仅实测子系统   %.1f 行" % exp_measured_rz)
    p("  含未跑折算     %.1f 行（未跑 %d 行 × 全表实收率 %.4f = %.1f）"
      % (exp_measured_rz + rem_unm * glob_rz, rem_unm, glob_rz, rem_unm * glob_rz))
    p("  折成全表 [已证] 增幅 严格 %.3f 个百分点 / 折算 %.3f 个百分点"
      % (100.0 * exp_measured_rz / cov_rows,
         100.0 * (exp_measured_rz + rem_unm * glob_rz) / cov_rows))
    p("  相对现有 [已证] %d 行：严格 +%.2f%% / 折算 +%.2f%%"
      % (proven, 100.0 * exp_measured_rz / proven,
         100.0 * (exp_measured_rz + rem_unm * glob_rz) / proven))

    # ------------------------------------------- 按名字形态分组的实测产出
    # 支撑表 D：哪一类"名字"实际能换出行，哪一类换不出
    SLOT = re.compile(r"^[A-Za-z0-9_<>@$?]+::v?slot\d+$", re.I)
    def shape_of(nm):
        if PSEUDO.match(nm):
            return "pseudo(fn_/sub_)"
        if SLOT.match(nm):
            return "Class::slotN"
        if "::" in nm:
            return "Class::named_member"
        return "bare(裸名)"
    delta_all = set()
    for name, ss, rel in BATCHES:
        delta_all |= set(read_delta_entries(os.path.join(R14, name, "delta.tsv")))
    shp = collections.defaultdict(lambda: dict(checked=0, delta=0, prov=0, pool=0))
    for ss in ALL_SS:
        for h in named_by_ss.get(ss, []):
            s = shape_of(h["name"])
            shp[s]["pool"] += 1
            e = h["entry"].upper()
            if e in checked_union.get(ss, set()):
                shp[s]["checked"] += 1
                if e in delta_all:
                    shp[s]["delta"] += 1
                if cov_grade_by_entry.get(e) == "[已证]":
                    shp[s]["prov"] += 1
    p("")
    p("按名字形态看实测产出（全表，named 552 行）")
    p("%-22s %6s %8s %8s %8s %9s %9s" %
      ("形态", "池", "已核", "delta", "已证", "delta率", "已证率"))
    for s in ["Class::slotN", "Class::named_member", "bare(裸名)", "pseudo(fn_/sub_)"]:
        v = shp[s]
        if v["pool"] == 0:
            continue
        dr = (v["delta"] / v["checked"]) if v["checked"] else float("nan")
        pr = (v["prov"] / v["checked"]) if v["checked"] else float("nan")
        p("%-22s %6d %8d %8d %8d %9.4f %9.4f" %
          (s, v["pool"], v["checked"], v["delta"], v["prov"], dr, pr))

    # S22 内部结构（解释 0.9444 是不是可迁移的）
    p("")
    p("S22 具名池结构（71 行）")
    pref = collections.Counter()
    for h in named_by_ss.get("S22", []):
        nm = h["name"]
        pref[nm.split("::")[0]] += 1
    for k, v in pref.most_common():
        p("  %-44s %d" % (k, v))
    tcf = sum(v for k, v in pref.items() if k.startswith("T_TClassFactory_"))
    vec = sum(v for k, v in pref.items() if "Vector" in k)
    p("  ⇒ TClassFactory<T>::slot3 %d 行 + Vector 系 %d 行 = %d/%d（其余 %d）"
      % (tcf, vec, tcf + vec, len(named_by_ss.get("S22", [])),
         len(named_by_ss.get("S22", [])) - tcf - vec))

    # ---------------------------------------------------------------- 剩余明细
    p("")
    p("未消费具名候选明细（按子系统，entry 升序）")
    for ss in ALL_SS:
        r = next(x for x in table_a if x["subsystem"] == ss)
        if r["remaining"] <= 0:
            continue
        rem_entries = sorted(
            (h for h in named_by_ss.get(ss, [])
             if not PSEUDO.match(h["name"]) and h["entry"].upper() not in checked_union.get(ss, set())),
            key=lambda h: int(h["entry"], 16))
        n_bare = sum(1 for h in rem_entries if BARE(h["name"]))
        tag = "（含 %d 裸名，见上表 D）" % n_bare if n_bare else ""
        p("  %s (%d 行)%s:" % (ss, len(rem_entries), tag))
        p("    " + " ".join(h["entry"] for h in rem_entries))

    # 剩余行按名字形态归类（回答"剩下的都是什么货色"）
    p("")
    p("剩余候选按名字形态（可派 vs 不可派一眼分开）")
    p("%-4s %6s %10s %10s %8s" % ("ss", "剩余", "slotN", "named_mem", "裸名"))
    for ss in ALL_SS:
        r = next(x for x in table_a if x["subsystem"] == ss)
        if r["remaining"] <= 0:
            continue
        rem = [h for h in named_by_ss.get(ss, [])
               if not PSEUDO.match(h["name"]) and h["entry"].upper() not in checked_union.get(ss, set())]
        c = collections.Counter(shape_of(h["name"]) for h in rem)
        p("%-4s %6d %10d %10d %8d" %
          (ss, len(rem), c.get("Class::slotN", 0), c.get("Class::named_member", 0),
           c.get("bare(裸名)", 0)))

    p("")
    p("S22 剩余 35 行的类前缀（判断是否仍是模板族）")
    rem22 = [h for h in named_by_ss.get("S22", [])
             if not PSEUDO.match(h["name"]) and h["entry"].upper() not in checked_union.get("S22", set())]
    p22 = collections.Counter(h["name"].split("::")[0] for h in rem22)
    p("  T_TClassFactory_* 前缀 %d 个 ; 非工厂前缀 %d 个"
      % (sum(1 for k in p22 if k.startswith("T_TClassFactory_")),
         sum(1 for k in p22 if not k.startswith("T_TClassFactory_"))))
    for k in sorted(p22):
        if not k.startswith("T_TClassFactory_"):
            p("    非工厂: %s" % k)

    # S22 两个子种群分开算率：工厂族 vs Vector 族（B1 已证 Vector slot2 两行全败）
    p("")
    p("S22 子种群拆分（0.9444 是两个不同族的混合，不能整体外推）")
    def is_factory(nm):
        return nm.split("::")[0].startswith("T_TClassFactory_")
    for label, pred in (("TClassFactory<T>::slot3", is_factory),
                        ("Vector/DynamicVector 族", lambda nm: not is_factory(nm))):
        chk = [h for h in named_by_ss.get("S22", [])
               if pred(h["name"]) and h["entry"].upper() in checked_union.get("S22", set())]
        d_ = sum(1 for h in chk if h["entry"].upper() in delta_all)
        pr_ = sum(1 for h in chk if cov_grade_by_entry.get(h["entry"].upper()) == "[已证]")
        rem_ = [h for h in rem22 if pred(h["name"])]
        rate_ = (pr_ / len(chk)) if chk else float("nan")
        p("  %-24s 池 %2d  已核 %2d  delta %2d  已证 %2d  实收率 %.4f  剩 %2d  ⇒ 预期 %.1f 行"
          % (label, sum(1 for h in named_by_ss.get("S22", []) if pred(h["name"])),
             len(chk), d_, pr_, rate_, len(rem_), len(rem_) * rate_))

    p("")
    if problems:
        p("!! 校验问题 %d 条" % len(problems))
        for x in problems:
            p("   - " + x)
    else:
        p("校验：20 批全通过（清单行数 == base_rate rows_checked == REPORT 核过行数；"
          "delta ⊆ 核过清单；核过 entry 均属该子系统 named 池且在 atlas 内）")
    p("=" * 78)
    return 0 if not problems else 2


if __name__ == "__main__":
    sys.exit(main())
