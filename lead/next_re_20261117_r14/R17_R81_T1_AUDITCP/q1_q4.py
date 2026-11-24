#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""q1_q4.py — R44-T1 审计补充：Q1 判据机械性扫描 / Q4 判据打架件取证 / Q3 全量阈值敏感度

只读：R17_R78_T1_RECLASS/*（清单 + decide_cprime.py）、lead/ 下文件前 8 KiB
只写：本目录 q1_q3_q4.json / q4_brawl.tsv
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

AUD = os.path.dirname(os.path.abspath(__file__))
LEAD = r"D:\Project\ra2-campaign-forge\lead"
REC = os.path.join(LEAD, "next_re_20261117_r14", "R17_R78_T1_RECLASS")

import audit_sample as AS  # 复用同一份独立重判实现（非 decide_cprime）


def load_tsv(p):
    rows = []
    with open(p, encoding="utf-8") as fh:
        hdr = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            f = line.rstrip("\n").split("\t")
            rows.append(dict(zip(hdr, f)))
    return rows


A = load_tsv(os.path.join(LEAD, "next_re_20261117_r14", "R17_R72_T1_CLEANSCALE", "files_tier_A_snap2.tsv"))
CP = load_tsv(os.path.join(REC, "files_tier_Cprime.tsv"))
EX = load_tsv(os.path.join(REC, "files_excluded_prime.tsv"))

RE_VA1 = re.compile(r"^\s*(0x)?[0-9A-Fa-f]{6,8}\s*[:\t ]")
RE_VA2 = re.compile(r"^\s*0x[0-9A-Fa-f]{6,8}\s{2,}")
RE_BANNER = re.compile(r"^\s*(={3,}|-{3,}|#{1,6}\s)")
RE_MDH1 = re.compile(r"^#\s+\S")
RE_RUNID = re.compile(r"^\s*(RUN_ID\b|run_id\s*[:=])", re.I)
META_DIR = re.compile(
    r"(^|/)(_cards|_drafts|_backlog|_hygiene|_smoke|_scratch_[^/]+|_lead_audit|_audit|_work|"
    r"_archive|_archive_probe|_raw|_verify|_r\d+)(/|$)", re.I)
META_SELF = re.compile(r"(^|/)(files_(tier|scale)_[^/]*|_hits_[^/]*|scale_[^/]*\.json|[^/]*\.tmp)$", re.I)
ROLLBACK = re.compile(r"(\.before[._][^/]*|\.before$|_before_[^/]*|_bak(\.[^/]*)?$|\.bak$)", re.I)
RE_REPORT_EQ = re.compile(r"^report\.md$", re.I)
RE_REPORT_SW = re.compile(r"_report\.(md|txt|json|log|tsv|csv)$", re.I)
RE_STDIO = re.compile(r"std(out|err)", re.I)
RE_OUTEXT = re.compile(r"[_\-.]out\.(txt|json|log|md|tsv|csv)$", re.I)


def base(rel):
    return rel.rsplit("/", 1)[-1]


def dirs_of(rel):
    return rel.split("/")[:-1]


def in_ev(rel):
    return any(s.upper() == "EVIDENCE" for s in dirs_of(rel))


def head(rel, n=8192):
    p = os.path.join(LEAD, rel.replace("/", os.sep))
    try:
        with open(p, "rb") as fh:
            return fh.read(n)
    except OSError:
        return None


def lines_of(h, cap=200):
    return [x for x in h.split(b"\n")[:cap] if x.strip()]


def va_cnt(ls):
    n = 0
    for x in ls:
        s = x.decode("utf-8", "replace")
        if RE_VA1.match(s) or RE_VA2.match(s):
            n += 1
    return n


def strip_rb(b):
    m = ROLLBACK.search(b)
    if not m:
        return None
    stem, tail = b[: m.start()], b[m.end():]
    ext = ""
    if "." in tail:
        ext = tail[tail.index("."):]
    if not ext:
        mm = re.search(r"(\.[A-Za-z0-9]{1,5})$", b)
        ext = mm.group(1) if mm else ""
    return stem + ext


PEER = {r["rel"].lower() for r in A}
PEER_BASE = {base(r["rel"]).lower() for r in A}


def hits(rel, hd):
    """返回该件命中的每一条判据（层序排列），用于 Q4「判据内部打架」结构统计。"""
    b = base(rel)
    d = dirs_of(rel)
    low = b.lower()
    ev = in_ev(rel)
    h = hd
    out = []
    ls = lines_of(h)
    nva, nln = va_cnt(ls), len(ls)
    first = h.split(b"\n", 3)[0].decode("utf-8", "replace")
    name_keep = []
    name_excl = []
    if nln and nva >= 3 and nva / nln >= 0.6:
        name_keep.append(f"P1a(行首VA {nva}/{nln}={nva/nln:.2f})")
    if low.endswith((".tsv", ".csv")) and nln >= 5:
        tabs = sum(1 for x in ls if x.count(b"\t") >= 2)
        if tabs / nln >= 0.7:
            name_keep.append(f"P1b(≥2TAB {tabs}/{nln}={tabs/nln:.2f})")
    if RE_STDIO.search(low) or RE_OUTEXT.search(low):
        name_excl.append("E1")
    if RE_BANNER.match(first) and not RE_MDH1.match(first) and not low.endswith(".md"):
        name_excl.append("E2")
    if RE_RUNID.match(first):
        name_excl.append("E2")
    if META_SELF.search(rel):
        name_excl.append("E5")
    if META_DIR.search("/" + "/".join(d) + "/"):
        name_excl.append("E3")
    cur = strip_rb(b)
    if cur and (cur.lower() in PEER_BASE or "/".join(d + [cur]).lower() in PEER):
        name_excl.append("E4")
    if RE_REPORT_EQ.match(low) or RE_REPORT_SW.search(low):
        name_excl.append("E6")
    if not low.endswith(".md") and RE_BANNER.match(first):
        name_excl.append("E2b")
    return dict(ev=ev, keep=name_keep, excl=sorted(set(name_excl)),
                n_lines=nln, n_va=nva, va_ratio=(nva / nln if nln else None),
                first=first[:100])


# ============================================================ Q3 全量阈值敏感度
def q3_full():
    res = {}
    for thr in (0.5, 0.6, 0.7):
        res[thr] = {r["rel"]: AS.rejudge(r["rel"], va_thr=thr)[0] for r in A}
    # 阈值只影响「静态」件：L0 命中 ⇒ C′（去往保留）；L0 未命中 ⇒ 继续按 L1..L4 判。
    # 但 L1..L4 的判定与阈值无关，故全量翻转只会发生在 L1..L4 会判 EXCL/UD 的件上。
    out = {}
    for pair in ((0.5, 0.6), (0.6, 0.7)):
        a, b = pair
        ch = [(k, res[b][k], res[a][k]) for k in res[a]
              if AS.norm_label(res[a][k]) != AS.norm_label(res[b][k])]
        out[f"{int(a*100)}->{int(b*100)}"] = ch
    return out


# ============================================================ Q4
def q4_scan():
    rows = []
    for r in A:
        hd = head(r["rel"])
        if hd is None:
            continue
        hh = hits(r["rel"], hd)
        # 「判据打架」结构定义：同一件同时有保留侧命中（keep）与排除侧命中（excl）
        if hh["keep"] and hh["excl"]:
            rows.append(dict(rel=r["rel"], bytes=int(r["bytes"]), keep=",".join(hh["keep"]),
                             excl=",".join(hh["excl"]), ev=hh["ev"],
                             va_ratio=hh["va_ratio"], first=hh["first"]))
    return rows


if __name__ == "__main__":
    print("[q3] 全量阈值敏感度（24,723 件）…")
    q3 = q3_full()
    summ = {}
    for k, v in q3.items():
        print(f"  {k}: 翻转 {len(v)} 件")
        m = {}
        for rel, old, new in v:
            key = f"{old}->{new}"
            m.setdefault(key, [0, 0])
            m[key][0] += 1
            m[key][1] += int({r['rel']: r['bytes'] for r in A}[rel])
        summ[k] = m
        print("    ", m)
        for rel, old, new in v[:6]:
            print(f"    {rel}  {old} -> {new}")

    print("[q4] 冲突件结构扫描…")
    brawl = q4_scan()
    print(f"  同时命中 keep+excl 的件 = {len(brawl)}")

    json.dump(dict(q3_full={k: [dict(rel=a, lab_at_hi=b, lab_at_lo=c) for a, b, c in v]
                           for k, v in q3.items()},
                   q4=dict(n_brawl=len(brawl), rows=brawl)),
              open(os.path.join(AUD, "q1_q3_q4.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    with open(os.path.join(AUD, "q4_brawl.tsv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("rel\tbytes\tkeep_hits\texcl_hits\tin_evidence\tva_ratio\tfirst_line\n")
        for x in brawl:
            fh.write(f"{x['rel']}\t{x['bytes']}\t{x['keep']}\t{x['excl']}\t{x['ev']}\t{x['va_ratio']}\t{x['first'].replace(chr(9),' ')}\n")
