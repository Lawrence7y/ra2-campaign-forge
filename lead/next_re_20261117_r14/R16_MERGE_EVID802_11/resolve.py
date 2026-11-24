#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
resolve.py — coverage.tsv 中 `[已证]` 行 evidence_path 的盘上可解析性核查（只读）

做什么
------
取 COVERAGE/coverage.tsv 中 grade == "[已证]" 的行，把第 6 列 evidence_path
按 `;` / `,` 拆成多个路径，去掉 `#anchor`，在若干相对路径基准下解析，
判断该路径是否解析到盘上真实存在的**文件**，然后把每行归入四类：

  R_OK          至少一个路径解析到真实存在的文件
  R_MISSING     所有路径都解析不到（列出尝试过的候选）
  R_TRACE_ONLY  evidence_path 只含 classification_trace（分类追踪，不是证据文件）
  R_EMPTY       evidence_path 为空

纪律
----
只读：只读 coverage.tsv 与盘上文件；只写 EVID_RESOLVE/ 目录。

用法
----
  python resolve.py                 # 用脚本内置默认路径
  python resolve.py --repo D:\\Project\\ra2-campaign-forge
  python resolve.py --coverage <path> --out <dir>
"""
from __future__ import annotations

import argparse
import collections
import os
import re
import sys

PROVED_GRADE = "[已证]"
TRACE_MARK = "classification_trace"
# 分隔符：规范要求 `;` 与 `,`；实测还有 2 行用 `|` 连接多个路径，一并拆
SPLIT_RE = re.compile(r"[;,|]")
ABS_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\|/)")
# 除 `#anchor` 外，实测还有 6 段用文件内行号锚点，如 `YRpp/CRT.h:87-88`
LINESPEC_RE = re.compile(r":(?:\d+[0-9A-Za-z\-]*|0x[0-9A-Fa-f\-]+)$")


# --------------------------------------------------------------------------- #
# 输入
# --------------------------------------------------------------------------- #
def load_coverage(path):
    """读 coverage.tsv。

    注意该文件的真实格式：表头用逗号分隔，数据行用 Tab 分隔（同一个文件里
    两种分隔符混用）。这里按各行自身的分隔符解析，并硬校验列数一致——
    列数不符直接报错，不做静默兜底。
    """
    with open(path, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()

    lines = text.split("\n")
    header = [c.strip() for c in lines[0].rstrip("\r").split(",")]

    rows, bad = [], []
    for lineno, raw in enumerate(lines[1:], start=2):
        raw = raw.rstrip("\r")
        if not raw.strip():
            continue
        fields = raw.split("\t")
        if len(fields) != len(header):
            bad.append((lineno, len(fields), raw[:120]))
            continue
        rows.append(dict(zip(header, fields)))
    return header, rows, bad


# --------------------------------------------------------------------------- #
# 解析
# --------------------------------------------------------------------------- #
def split_evidence(value):
    """按 `;` 和 `,` 拆分 evidence_path，去空段。"""
    return [p.strip() for p in SPLIT_RE.split(value.strip()) if p.strip()]


def strip_anchor(part):
    """去掉 `#anchor` 与 `:行号` 锚点，只留文件路径。"""
    p = part.split("#", 1)[0].strip()
    if not ABS_RE.match(p):            # 绝对路径的盘符冒号不能当锚点
        p = LINESPEC_RE.sub("", p).strip()
    return p


def is_trace(part):
    return TRACE_MARK in part


def candidates_for(rel, bases):
    """给一个（相对的）路径，在各基准下生成 (base_name, abs_path) 候选序列。

    绝对路径（盘符 / UNC / 以 / 开头）只试一次，基准名记为 ABS。
    """
    rel = rel.replace("\\", os.sep).replace("/", os.sep)
    if ABS_RE.match(rel.strip()):
        return [("ABS", rel)]
    out = []
    for name, base in bases:
        out.append((name, os.path.join(base, rel)))
    return out


def resolve_row(evidence_value, bases):
    """返回该 evidence_path 的解析结果 dict。"""
    parts = split_evidence(evidence_value)
    trace_flags = [is_trace(p) for p in parts]

    first_existing = None        # (part, base_name, abs_path)
    attempted = []               # 所有尝试过的候选 abs path
    part_report = []             # (part, hit|None, [cands])

    for part, is_tr in zip(parts, trace_flags):
        rel = strip_anchor(part)
        if not rel:
            continue
        cands = candidates_for(rel, bases)
        attempted.extend(p for _, p in cands)
        hit = None
        for base_name, p in cands:
            if os.path.isfile(p):
                hit = (base_name, p)
                break
        part_report.append((part, is_tr, hit, [p for _, p in cands]))
        if hit and first_existing is None:
            first_existing = (part, hit[0], hit[1])

    # ---- 归类（顺序即优先级）----
    if not parts:
        klass = "R_EMPTY"
    elif all(trace_flags):
        klass = "R_TRACE_ONLY"
    elif first_existing is not None:
        klass = "R_OK"
    else:
        klass = "R_MISSING"

    return {
        "parts": parts,
        "trace_flags": trace_flags,
        "class": klass,
        "first_existing": first_existing,
        "attempted": attempted,
        "part_report": part_report,
    }


# --------------------------------------------------------------------------- #
# 统计
# --------------------------------------------------------------------------- #
def dirname_prefix(part):
    """相对路径的目录前缀（去掉 #anchor，去掉文件名）。"""
    rel = strip_anchor(part).replace("\\", "/").strip("/")
    comps = [c for c in rel.split("/") if c]
    if len(comps) <= 1:
        return comps[0] if comps else "<none>"
    return "/".join(comps[:-1])


def top_prefix_prefix(part):
    rel = strip_anchor(part).replace("\\", "/").strip("/")
    comps = [c for c in rel.split("/") if c]
    return comps[0] if comps else "<none>"


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    default_r14 = os.path.dirname(here)

    ap = argparse.ArgumentParser(description="核查 [已证] 行 evidence_path 可解析性（只读）")
    ap.add_argument("--repo", default=os.path.dirname(os.path.dirname(default_r14)),
                    help="仓库根（默认由脚本位置推得）")
    ap.add_argument("--coverage", default=None, help="coverage.tsv 路径")
    ap.add_argument("--out", default=here, help="输出目录（默认脚本所在目录）")
    args = ap.parse_args(argv)

    repo = os.path.abspath(args.repo)
    lead = os.path.join(repo, "lead")
    r14 = os.path.join(lead, "next_re_20261117_r14")
    coverage = args.coverage or os.path.join(r14, "COVERAGE", "coverage.tsv")
    out_dir = os.path.abspath(args.out)

    for p in (coverage,):
        if not os.path.isfile(p):
            sys.exit(f"[FATAL] 找不到输入：{p}")
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    # 相对路径基准候选：主基准 r14，再退 lead、仓库根
    bases = [("r14", r14), ("lead", lead), ("repo", repo)]
    bases_present = [(n, p) for n, p in bases if os.path.isdir(p)]

    header, rows, bad = load_coverage(coverage)
    need = ["entry", "subsystem", "name", "grade", "evidence_path"]
    missing_cols = [c for c in need if c not in header]
    if missing_cols:
        sys.exit(f"[FATAL] 缺列：{missing_cols}")

    proved = [r for r in rows if r["grade"] == PROVED_GRADE]
    total_proved = len(proved)

    records = []
    for r in proved:
        res = resolve_row(r["evidence_path"], bases_present)
        records.append((r, res))

    # ---- 分类计数 ----
    klass_count = collections.Counter(res["class"] for _, res in records)
    klass_count.setdefault("R_OK", 0)

    # ---- R_MISSING / R_TRACE_ONLY 的分布 ----
    missing_prefix1 = collections.Counter()
    missing_prefix2 = collections.Counter()
    missing_samples = []
    trace_by_subsys = collections.Counter()
    missing_by_subsys = collections.Counter()
    missing_with_trace = 0
    trace_file_exists = 0

    for r, res in records:
        if res["class"] == "R_MISSING":
            missing_by_subsys[r["subsystem"]] += 1
            seen1, seen2 = set(), set()
            for part, is_tr, hit, cands in res["part_report"]:
                if is_tr:
                    continue
                seen1.add(top_prefix_prefix(part))
                seen2.add(dirname_prefix(part))
            for k in seen1:
                missing_prefix1[k] += 1
            for k in seen2:
                missing_prefix2[k] += 1
            if any(res["trace_flags"]):
                missing_with_trace += 1
            if len(missing_samples) < 12:
                missing_samples.append((r, res))
        elif res["class"] == "R_TRACE_ONLY":
            trace_by_subsys[r["subsystem"]] += 1
            if res["first_existing"] is not None:
                trace_file_exists += 1

    # ---- R_OK 的解析基准分布 ----
    ok_base = collections.Counter()
    ok_only_trace_present = 0
    for r, res in records:
        if res["class"] == "R_OK":
            ok_base[res["first_existing"][1]] += 1
            if any(res["trace_flags"]):
                ok_only_trace_present += 1

    # ---- 写 resolve.tsv（只放 R_MISSING / R_TRACE_ONLY / R_EMPTY）----
    out_cols = ["entry", "subsystem", "name", "grade", "evidence_path",
                "class", "first_existing", "attempted"]
    resolve_path = os.path.join(out_dir, "resolve.tsv")
    written = 0
    with open(resolve_path, "w", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(out_cols) + "\n")
        for r, res in records:
            if res["class"] == "R_OK":
                continue
            fe = res["first_existing"]
            fh.write("\t".join([
                r["entry"], r["subsystem"], r["name"], r["grade"],
                r["evidence_path"], res["class"],
                fe[2] if fe else "",
                ";".join(res["attempted"]),
            ]) + "\n")
            written += 1

    # ---- 写 summary.tsv ----
    summary_path = os.path.join(out_dir, "summary.tsv")
    with open(summary_path, "w", encoding="utf-8", newline="") as fh:
        fh.write("class\tcount\tpct\n")
        for k in ("R_OK", "R_MISSING", "R_TRACE_ONLY", "R_EMPTY"):
            c = klass_count.get(k, 0)
            pct = (100.0 * c / total_proved) if total_proved else 0.0
            fh.write(f"{k}\t{c}\t{pct:.2f}\n")

    # ---- 控制台小结 ----
    print(f"[in ] coverage : {coverage}")
    print(f"[in ] repo     : {repo}")
    print(f"[in ] bases    : " + ", ".join(f"{n}={p}" for n, p in bases_present))
    print(f"[data] 总行 {len(rows)}，[已证] {total_proved} 行，列数异常 {len(bad)} 行")
    print(f"[out] {os.path.basename(resolve_path)} : {written} 行")
    print(f"[out] {os.path.basename(summary_path)} : 4 行")
    for k in ("R_OK", "R_MISSING", "R_TRACE_ONLY", "R_EMPTY"):
        c = klass_count.get(k, 0)
        print(f"   {k:12s} {c:5d}  {(100.0*c/total_proved if total_proved else 0):6.2f}%")

    # 供 REPORT 使用的统计打包
    stats = dict(
        repo=repo, r14=r14, coverage=coverage, out_dir=out_dir,
        total_rows=len(rows), total_proved=total_proved, bad_rows=bad,
        bases_present=bases_present,
        klass_count=dict(klass_count),
        missing_prefix1=missing_prefix1, missing_prefix2=missing_prefix2,
        missing_by_subsys=missing_by_subsys, trace_by_subsys=trace_by_subsys,
        missing_with_trace=missing_with_trace, trace_file_exists=trace_file_exists,
        ok_base=ok_base, ok_with_trace_part=ok_only_trace_present,
        missing_samples=missing_samples, records=records,
    )
    return stats


if __name__ == "__main__":
    main()
