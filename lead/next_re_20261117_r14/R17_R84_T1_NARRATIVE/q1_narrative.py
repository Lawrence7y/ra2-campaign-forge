#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""q1_narrative.py — R45-T1 Q1（法 1：Python 实现）

只读：
  lead/next_re_20261117_r14/R17_R78_T1_RECLASS/files_tier_Cprime.tsv
  lead/<清单中列出的文件> 的前 8 KiB
只写：本目录 q1_py.json / narrative_candidates.tsv

Q1 判据（与 R44 上一轮 prose.py 逐字同一判据，只是把作用域收紧到 why == P0）：
  R1  why 列 == "P0_未被排除判据命中"                      （源：files_tier_Cprime.tsv 的 why 列）
  R2  取该件前 8192 B                                      （read = open(...).read(8192)）
  R3  非空行 = 前 8 KiB 按 b"\\n" 切、先截 200 行、再丢 strip() 为空的行
      （两步顺序照抄 R17_R81_T1_AUDITCP/audit_sample.py:119-120，与 decide_cprime.py:174 一致）
  R4  P1a / P1b 均未命中（即不是"行首 VA 对象抄本"，也不是"TAB 对象事实表"）
  R5  cn_ratio = 含 CJK 统一表意文字(\\u4e00-\\u9fff)的非空行数 / 非空行总数 >= 0.25
  P0 ∧ R2..R5 ⇒ 叙述体候选
  自检：同一脚本对**全 C′**（不加 R1）复算一次，必须复现 4,471 / 210,142,479
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

LEAD = r"D:\Project\ra2-campaign-forge\lead"
R14 = os.path.join(LEAD, "next_re_20261117_r14")
CP_TSV = os.path.join(R14, "R17_R78_T1_RECLASS", "files_tier_Cprime.tsv")
OUT = os.path.dirname(os.path.abspath(__file__))

RE_VA = re.compile(r"^\s*(0x)?[0-9A-Fa-f]{6,8}\s*[:\t ]")
RE_VA2 = re.compile(r"^\s*0x[0-9A-Fa-f]{6,8}\s{2,}")
RE_CN = re.compile(r"[\u4e00-\u9fff]")


def read_head(rel, n=8192):
    p = os.path.join(LEAD, rel.replace("/", os.sep))
    try:
        with open(p, "rb") as fh:
            return fh.read(n)
    except OSError:
        return None


def lines_of(h, cap=200):
    return [x for x in h.split(b"\n")[:cap] if x.strip()]


def features(rel, ext):
    """返回 dict(head_ok, n_lines, cn_ratio, p1a, p1b)"""
    h = read_head(rel)
    if h is None:
        return dict(head_ok=False)
    ls = lines_of(h)
    if not ls:
        return dict(head_ok=True, n_lines=0, cn_ratio=0.0, p1a=False, p1b=False)
    va = sum(1 for x in ls if RE_VA.match(x.decode("utf-8", "replace"))
             or RE_VA2.match(x.decode("utf-8", "replace")))
    p1a = bool(va >= 3 and va / len(ls) >= 0.6)
    low = rel.rsplit("/", 1)[-1].lower()
    p1b = False
    if low.endswith((".tsv", ".csv")) and len(ls) >= 5:
        p1b = (sum(1 for x in ls if x.count(b"\t") >= 2) / len(ls)) >= 0.7
    cn = sum(1 for x in ls if RE_CN.search(x.decode("utf-8", "replace")))
    return dict(head_ok=True, n_lines=len(ls), cn_ratio=cn / len(ls),
                p1a=p1a, p1b=p1b, cn_lines=cn)


def first_line(rel):
    h = read_head(rel)
    if h is None:
        return "未取得"
    raw = h.split(b"\n", 1)[0].rstrip(b"\r")
    s = raw.decode("utf-8", "replace")
    return s[:200]


def load_cp():
    rows = []
    with open(CP_TSV, encoding="utf-8") as fh:
        fh.readline()
        for line in fh:
            f = line.rstrip("\n").split("\t")
            rows.append(dict(rel=f[0], ext=f[1], bytes=int(f[2]), mtime_ns=int(f[3]),
                             family=f[4], why=f[5]))
    return rows


def main():
    rows = load_cp()
    n_cp = len(rows)
    b_cp = sum(r["bytes"] for r in rows)

    # ---- 自检：全 C′ 上复算上一轮的 4,471 / 210,142,479
    all_hit, all_b, all_unread = 0, 0, 0
    for r in rows:
        f = features(r["rel"], r["ext"])
        if not f.get("head_ok"):
            all_unread += 1
            continue
        if f["n_lines"] == 0:
            continue
        if f["p1a"] or f["p1b"]:
            continue
        if f["cn_ratio"] >= 0.25:
            all_hit += 1
            all_b += r["bytes"]

    # ---- Q1：只作用于 P0 行
    p0 = [r for r in rows if r["why"] == "P0_未被排除判据命中"]
    b_p0 = sum(r["bytes"] for r in p0)
    hits = []
    unread = []
    for r in p0:
        f = features(r["rel"], r["ext"])
        if not f.get("head_ok"):
            unread.append(r["rel"])
            continue
        if f["n_lines"] == 0:
            continue
        if f["p1a"] or f["p1b"]:
            continue
        if f["cn_ratio"] >= 0.25:
            hits.append((r, f))

    n_q1 = len(hits)
    b_q1 = sum(r["bytes"] for r, _ in hits)

    with open(os.path.join(OUT, "narrative_candidates.tsv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("rel\tbytes\twhy\tcn_ratio\tfirst_line\n")
        for r, f in sorted(hits, key=lambda x: x[0]["rel"]):
            fl = first_line(r["rel"]).replace("\t", " ").replace("\x00", "")
            fh.write(f'{r["rel"]}\t{r["bytes"]}\t{r["why"]}\t{f["cn_ratio"]:.4f}\t{fl}\n')

    out = dict(
        法="法1 python (q1_narrative.py)",
        源_清单=os.path.relpath(CP_TSV, LEAD).replace("\\", "/"),
        源_列="rel, bytes, why",
        判据="why==P0_未被排除判据命中 ∧ 前8KiB(先截200行再丢空行)非空行中 含中文行占比>=0.25 ∧ P1a/P1b 均未命中",
        Cprime_n=n_cp, Cprime_b=b_cp,
        full_Cprime_recount_n=all_hit, full_Cprime_recount_b=all_b, full_Cprime_unread=all_unread,
        P0_n=len(p0), P0_b=b_p0,
        Q1_n=n_q1, Q1_b=b_q1,
        Q1_unread=unread,
        上一轮_claimed_n=4471, 上一轮_claimed_b=210142479,
        一致=dict(n=(all_hit == 4471), b=(all_b == 210142479)),
    )
    json.dump(out, open(os.path.join(OUT, "q1_py.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
