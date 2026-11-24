#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify.py — R17 交付摘要的复算脚本（只读输入，只写本目录）

卡号：R17-DELIVERY-SUMMARY
写域：lead/next_re_20261117_r14/R17_DELIVERY/

读（只读）：
  - COVERAGE/coverage.tsv                                   （现态）
  - R17_LEAD_BASELINE/coverage.before_hyg.tsv               （A1 卫生修复前快照，用于字面 ④ 双口径的「并表前」值）
  - ../next_re_20261112_r10/W130_atlas/function_atlas.tsv   （atlas 分母）
写：
  - numbers.tsv

不读 EVIDENCE/ 原始输出内容；不跑 capstone/Ghidra/pefile/反汇编；
不执行 EVID_RESOLVE/resolve.py 的 main()（它会写盘）——本脚本按该文件
文件头注释所载的四类定义（R_OK / R_MISSING / R_TRACE_ONLY / R_EMPTY）重新实现纯函数逻辑。

用法：
  python -X utf8 verify.py            # 在任意目录均可
"""

from __future__ import annotations

import collections
import hashlib
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)                      # lead/next_re_20261117_r14
LEAD = os.path.dirname(R14)                      # lead
REPO = os.path.dirname(LEAD)                     # repo root

COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
BEFORE = os.path.join(R14, "R17_LEAD_BASELINE", "coverage.before_hyg.tsv")
ATLAS = os.path.join(LEAD, "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
OUT = os.path.join(HERE, "numbers.tsv")

PROVED = "[已证]"
INFER = "[静态推断]"
UNPROVED = "[未证]"
RING4 = "\u2463"                 # ④
RING4_LIVESLOT = "\u2463 活表槽位见证"   # ④ 活表槽位见证
RING4_DIRECT = "\u2463 direct call"      # ④ direct call

SPLIT_RE = re.compile(r"[;,|]")
ABS_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\|/)")
LINESPEC_RE = re.compile(r":(?:\d+[0-9A-Za-z\-]*|0x[0-9A-Fa-f\-]+)$")


# --------------------------------------------------------------------------- #
# 读入
# --------------------------------------------------------------------------- #
def load_coverage(path):
    """读 coverage.tsv。表头逗号分隔、数据行 Tab 分隔（文件本身即如此）。"""
    raw = open(path, "rb").read()
    lines = raw.decode("utf-8").split("\n")
    header = [c.strip() for c in lines[0].rstrip("\r").split(",")]
    rows, bad = [], []
    for lineno, line in enumerate(lines[1:], start=2):
        line = line.rstrip("\r")
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != len(header):
            bad.append(lineno)
            continue
        rows.append(dict(zip(header, fields)))
    return raw, header, rows, bad


def load_atlas(path):
    entries = set()
    with open(path, encoding="utf-8") as fh:
        fh.readline()
        for line in fh:
            line = line.rstrip("\r\n")
            if line.strip():
                entries.add(line.split("\t")[0].strip().upper())
    return entries


# --------------------------------------------------------------------------- #
# EVID_RESOLVE 的四类口径（纯函数重实现，见 EVID_RESOLVE/resolve.py 文件头）
# --------------------------------------------------------------------------- #
def _strip_anchor(part):
    p = part.split("#", 1)[0].strip()
    if not ABS_RE.match(p):
        p = LINESPEC_RE.sub("", p).strip()
    return p


def classify_evidence(value, bases):
    parts = [p.strip() for p in SPLIT_RE.split(value.strip()) if p.strip()]
    if not parts:
        return "R_EMPTY"
    trace_flags = ["classification_trace" in p for p in parts]
    if all(trace_flags):
        return "R_TRACE_ONLY"
    for part in parts:
        rel = _strip_anchor(part)
        if not rel:
            continue
        rel = rel.replace("\\", os.sep).replace("/", os.sep)
        if ABS_RE.match(rel.strip()):
            if os.path.isfile(rel):
                return "R_OK"
            continue
        for _, base in bases:
            if os.path.isfile(os.path.join(base, rel)):
                return "R_OK"
    return "R_MISSING"


# --------------------------------------------------------------------------- #
# 各口径
# --------------------------------------------------------------------------- #
def ct_only(row):
    """第 6 列切段后全部含 classification_trace。"""
    parts = [p.strip() for p in SPLIT_RE.split(row["evidence_path"]) if p.strip()]
    return bool(parts) and all("classification_trace" in p for p in parts)


def named_S(row):
    """named_pct_S(R14) 口径：name 非空、非 sub_ 前缀、且不匹配 ::sub_<hex>$（任意长度）。"""
    name = row["name"].strip()
    if not name:
        return False
    if name.startswith("sub_"):
        return False
    if re.search(r"::sub_[0-9A-Fa-f]+$", name):
        return False
    return True


def ring4_counts(rows):
    """[已证] 行上的 ④ 三口径 + 完全无 ④。口径一律限第 4 列。"""
    proved = [r for r in rows if r["grade"] == PROVED]
    a = sum(1 for r in proved if RING4 in r["one_line_semantics"])
    b = sum(1 for r in proved if RING4_LIVESLOT in r["one_line_semantics"])
    wide = sum(1 for r in proved
               if RING4_LIVESLOT in r["one_line_semantics"]
               or RING4_DIRECT in r["one_line_semantics"])
    none4 = sum(1 for r in proved if RING4 not in r["one_line_semantics"])
    return a, b, wide, none4, len(proved)


def literal_ring4_ge2(rows, with_space):
    """字面「同格两条 ④」的两种字面口径（都只是字面数，不是真两链）。"""
    pat = RING4 + " " if with_space else RING4
    return sum(1 for r in rows
               if r["grade"] == PROVED and r["one_line_semantics"].count(pat) >= 2)


def dod(rows, atlas):
    """atlas 分母内按子系统算 named_S / proved / proved_strict 与达标。"""
    stat = collections.defaultdict(lambda: dict(n=0, named=0, proved=0, strict=0))
    for row in rows:
        if row["entry"].upper() not in atlas:
            continue
        d = stat[row["subsystem"]]
        d["n"] += 1
        if named_S(row):
            d["named"] += 1
        if row["grade"] == PROVED:
            d["proved"] += 1
            if UNPROVED not in row["one_line_semantics"]:
                d["strict"] += 1
    nominal, strict_ok = [], []
    for sub in sorted(stat):
        d = stat[sub]
        t90 = math.ceil(0.9 * d["n"])
        t50 = math.ceil(0.5 * d["n"])
        if d["named"] >= t90 and d["proved"] >= t50:
            nominal.append(sub)
        if d["named"] >= t90 and d["strict"] >= t50:
            strict_ok.append(sub)
    return stat, nominal, strict_ok


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def main():
    raw, header, rows, bad = load_coverage(COV)
    _, _, before_rows, _ = load_coverage(BEFORE)
    atlas = load_atlas(ATLAS)

    grades = collections.Counter(r["grade"] for r in rows)
    proved = [r for r in rows if r["grade"] == PROVED]
    proved_in = [r for r in proved if r["entry"].upper() in atlas]
    proved_out = [r for r in proved if r["entry"].upper() not in atlas]
    strict_total = sum(1 for r in proved_in if UNPROVED not in r["one_line_semantics"])

    a, b, wide, none4, nproved = ring4_counts(rows)

    s126 = sum(1 for r in rows if "§12.6" in r["one_line_semantics"])
    s124 = sum(1 for r in rows if "§12.4" in r["one_line_semantics"])
    clsid = sum(1 for r in rows if "CLSID None" in "\t".join(r.values()))

    # 卫生缺陷：A1（活表槽位无 §12.6）+ A2（direct call 误引 §12.6），均应为 0
    h1c = sum(1 for r in rows
              if RING4_LIVESLOT in r["one_line_semantics"]
              and "§12.6" not in r["one_line_semantics"])
    h1b = sum(1 for r in rows
              if RING4_DIRECT in r["one_line_semantics"]
              and "§12.6" in r["one_line_semantics"])

    # 第 6 列含 ④ 的行（M94 注记），用于「整行统计会多计」的披露
    col6_ring4 = sum(1 for r in rows if RING4 in r["evidence_path"])
    non_col4_ring4 = sum(1 for r in rows
                         if any(RING4 in v for k, v in r.items()
                                if k != "one_line_semantics"))

    bases = [(n, p) for n, p in (("r14", R14), ("lead", LEAD), ("repo", REPO))
             if os.path.isdir(p)]
    klass = collections.Counter(classify_evidence(r["evidence_path"], bases) for r in proved)

    ct_proved = sum(1 for r in proved if ct_only(r))

    ge2_disk = literal_ring4_ge2(rows, with_space=False)
    ge2_disk_sp = literal_ring4_ge2(rows, with_space=True)
    ge2_pre = literal_ring4_ge2(before_rows, with_space=False)
    ge2_pre_sp = literal_ring4_ge2(before_rows, with_space=True)

    stat, nominal, strict_ok = dod(rows, atlas)
    nsubs = len(stat)

    out = []
    def rec(item, value, source):
        out.append((item, str(value), source))

    rec("coverage.bytes", len(raw), "自算")
    rec("coverage.sha256", hashlib.sha256(raw).hexdigest(), "自算")
    rec("coverage.header_cols", len(header), "自算")
    rec("coverage.data_rows", len(rows), "自算")
    rec("coverage.rows_per_colcount", dict(collections.Counter(len(r) for r in rows)), "自算")
    rec("coverage.bad_rows", len(bad), "自算")
    rec("grade.[已证]", grades[PROVED], "自算")
    rec("grade.[静态推断]", grades[INFER], "自算")
    rec("grade.[未证]", grades[UNPROVED], "自算")
    rec("grade.sum", sum(grades.values()), "自算")
    rec("atlas.data_rows", len(atlas), "自算")
    rec("proved.in_atlas", len(proved_in), "自算")
    rec("proved.out_atlas", len(proved_out), "自算")
    rec("proved.out_atlas.entries", ",".join(sorted(r["entry"] for r in proved_out)), "自算")
    rec("TOTAL_strict", strict_total, "自算")
    rec("ring4.A.col4_contains_④", a, "自算")
    rec("ring4.A.pct_of_proved", "%.2f%%" % (100.0 * a / nproved), "自算")
    rec("ring4.B.col4_contains_④活表槽位见证", b, "自算")
    rec("ring4.B.pct_of_proved", "%.2f%%" % (100.0 * b / nproved), "自算")
    rec("ring4.wide.B+direct_call", wide, "自算")
    rec("ring4.wide.pct_of_proved", "%.2f%%" % (100.0 * wide / nproved), "自算")
    rec("ring4.none", none4, "自算")
    rec("§12.6.hit_rows", s126, "自算")
    rec("§12.4.residual_rows", s124, "自算")
    rec("CLSID_None.rows", clsid, "自算")
    rec("hygiene.A1_liveslot_no_§12.6", h1c, "自算")
    rec("hygiene.A2_direct_with_§12.6", h1b, "自算")
    rec("hygiene.defect_residual", h1c + h1b, "自算")
    rec("ring4.col6_contains_④", col6_ring4, "自算")
    rec("ring4.non_col4_contains_④", non_col4_ring4, "自算")
    rec("evid.R_OK", klass.get("R_OK", 0), "自算")
    rec("evid.R_MISSING", klass.get("R_MISSING", 0), "自算")
    rec("evid.R_TRACE_ONLY", klass.get("R_TRACE_ONLY", 0), "自算")
    rec("evid.R_EMPTY", klass.get("R_EMPTY", 0), "自算")
    rec("evid.R_OK.pct_of_proved", "%.2f%%" % (100.0 * klass.get("R_OK", 0) / nproved), "自算")
    rec("classification_trace_only.proved", ct_proved, "自算")
    rec("literal_ring4.ge2.raw.NOW", ge2_disk, "自算")
    rec("literal_ring4.ge2.with_space.NOW", ge2_disk_sp, "自算")
    rec("literal_ring4.ge2.raw.BEFORE_A1", ge2_pre, "自算")
    rec("literal_ring4.ge2.with_space.BEFORE_A1", ge2_pre_sp, "自算")
    rec("literal_ring4.R16_H3a_historical_304", "304", "照录 R16_HYGIENE_R16/REPORT.md L67（现盘复现不出，见 L3）")
    rec("two_chain.real", "65", "照录 R16_HYGIENE_R16/REPORT.md L§3/§7-B1")
    rec("dod.nominal_passed", "/".join(nominal) or "-", "自算")
    rec("dod.nominal_count", "%d/%d" % (len(nominal), nsubs), "自算")
    rec("dod.strict_passed", "/".join(strict_ok) or "-", "自算")
    rec("dod.strict_count", "%d/%d" % (len(strict_ok), nsubs), "自算")
    rec("dod.denominator_subsystems", nsubs, "自算")

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("item\tvalue\tsource\n")
        for item, value, source in out:
            fh.write("%s\t%s\t%s\n" % (item, value, source))

    print("== R17-DELIVERY verify ==")
    print("[in ] %s" % COV)
    print("[in ] %s" % BEFORE)
    print("[in ] %s" % ATLAS)
    print("[out] %s  (%d 项)" % (OUT, len(out)))
    print()
    print("coverage  : %d B / sha256 %s" % (len(raw), hashlib.sha256(raw).hexdigest()))
    print("data rows : %d  cols %d  bad %d" % (len(rows), len(header), len(bad)))
    print("grade     : [已证] %d  [静态推断] %d  [未证] %d"
          % (grades[PROVED], grades[INFER], grades[UNPROVED]))
    print("proved    : atlas 内 %d  atlas 外 %d   TOTAL strict %d"
          % (len(proved_in), len(proved_out), strict_total))
    print("ring4     : A %d (%.2f%%)  B %d (%.2f%%)  wide %d (%.2f%%)  无④ %d"
          % (a, 100.0 * a / nproved, b, 100.0 * b / nproved,
             wide, 100.0 * wide / nproved, none4))
    print("literal   : ④>=2 raw %d / ④空格>=2 %d （BEFORE_A1: %d / %d）"
          % (ge2_disk, ge2_disk_sp, ge2_pre, ge2_pre_sp))
    print("hygiene   : §12.6 %d  §12.4 %d  CLSID None %d  A1 %d  A2 %d"
          % (s126, s124, clsid, h1c, h1b))
    print("evidence  : R_OK %d  R_MISSING %d  R_TRACE_ONLY %d  R_EMPTY %d"
          % (klass.get("R_OK", 0), klass.get("R_MISSING", 0),
             klass.get("R_TRACE_ONLY", 0), klass.get("R_EMPTY", 0)))
    print("DoD       : 名义 %d/%d (%s)  严格 %d/%d (%s)"
          % (len(nominal), nsubs, "/".join(nominal),
             len(strict_ok), nsubs, "/".join(strict_ok)))


if __name__ == "__main__":
    main()
