#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_sample.py — R44-T1 独立审计：抽样重判（Q2）/ 阈值敏感度（Q3）/ 判据打架（Q4）

只读：
  R17_R78_T1_RECLASS/files_tier_Cprime.tsv
  R17_R78_T1_RECLASS/files_excluded_prime.tsv
  lead/ 下列出文件的前 8 KiB
只写：本目录 audit_q2q3.json / audit_sample_detail.tsv

独立性约束：本脚本不 import decide_cprime，不读它的 why/label 列参与判决；
为什么列只在最后一步与本地重判结果比对时才读。
本脚本自带一份「我读 REPORT.md 后认为它写的判据」的独立实现 —— 若两者实现有差，
差在实现细节而非规则本意，会在输出里单列。
"""
from __future__ import annotations

import json
import os
import re

AUD = os.path.dirname(os.path.abspath(__file__))
LEAD = r"D:\Project\ra2-campaign-forge\lead"
REC = os.path.join(LEAD, "next_re_20261117_r14", "R17_R78_T1_RECLASS")
A_TSV = os.path.join(LEAD, "next_re_20261117_r14", "R17_R72_T1_CLEANSCALE", "files_tier_A_snap2.tsv")


def load_tsv(p):
    rows = []
    with open(p, encoding="utf-8") as fh:
        hdr = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            f = line.rstrip("\n").split("\t")
            rows.append(dict(zip(hdr, f)))
    return rows


CP = load_tsv(os.path.join(REC, "files_tier_Cprime.tsv"))
EX = load_tsv(os.path.join(REC, "files_excluded_prime.tsv"))
A = load_tsv(A_TSV)
A_BY_REL = {r["rel"]: r for r in A}


# ------------------------------------------------------------------ 抽样规则
def stride_sample(rows, n=40, key="rel"):
    """固定规则：按 key 升序排序，等距抽取 n 件，索引 = floor((k+0.5)*N/n)，k=0..n-1。
    等距抽样而非随机：无随机种子，任何人按同一清单重跑得到同一批样本。"""
    s = sorted(rows, key=lambda r: r[key])
    N = len(s)
    idx = [int((k + 0.5) * N / n) for k in range(n)]
    return [s[i] for i in idx], idx, N


CP_S, CP_IDX, CP_N = stride_sample(CP)
EX_S, EX_IDX, EX_N = stride_sample(EX)
# EX 需要可复现地取 40 件：包含 1,242 UD 与 4,769 EXCL 两侧，故按 label 分层等距抽
#   rule: 对 label 升序分组（EXCL 在前、UNDECIDED 在后），在每组内等距抽 round(40*share) 件。
def stratified(rows, n=40):
    groups = {}
    for r in rows:
        groups.setdefault(r["label"], []).append(r)
    out = []
    plan = {}
    tot = len(rows)
    for lab in sorted(groups):
        share = len(groups[lab]) / tot
        k = max(1, round(n * share))
        plan[lab] = (k, len(groups[lab]))
        g = sorted(groups[lab], key=lambda r: r["rel"])
        N = len(g)
        out += [g[int((j + 0.5) * N / k)] for j in range(k)]
    return out, plan


EX_S2, EX_PLAN = stratified(EX, 40)
# EXCL 组计划会抽 33 件、UD 组 9 件 → 补齐到 40 取前 40（按 rel 排序后等距再裁）
EX_S2 = sorted(EX_S2, key=lambda r: r["rel"])[:40]
EX_S = EX_S2


# ------------------------------------------------------------------ 独立重判实现
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


def va_ratio(ls):
    if not ls:
        return (0, 0)
    n = 0
    for x in ls:
        s = x.decode("utf-8", "replace")
        if RE_VA1.match(s) or RE_VA2.match(s):
            n += 1
    return (n, len(ls))


def tab_ratio(ls):
    if not ls:
        return (0, 0)
    return (sum(1 for x in ls if x.count(b"\t") >= 2), len(ls))


PEER = {r["rel"].lower() for r in A}
PEER_BASE = {base(r["rel"]).lower() for r in A}


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


def rejudge(rel, va_thr=0.6, tab_thr=0.7):
    """独立重判。返回 (label, why, layer, diag)"""
    b = base(rel)
    d = dirs_of(rel)
    low = b.lower()
    ev = in_ev(rel)
    h = head(rel)
    if h is None:
        return "UNDECIDED", "U0_不可读", "U0", {}
    ls = lines_of(h)
    nva, nln = va_ratio(ls)
    ntab, _ = tab_ratio(ls)
    diag = dict(n_lines=nln, n_va=nva, va_ratio=round(nva / nln, 4) if nln else None,
                tab_ratio=round(ntab / nln, 4) if nln else None,
                first_line=h.split(b"\n", 3)[0].decode("utf-8", "replace")[:90])
    # L0 内容事实层
    if nln and nva >= 3 and nva / nln >= va_thr:
        return "C′", f"P1a_对象抄本(行首VA {nva}/{nln})", "L0", diag
    if low.endswith((".tsv", ".csv")) and nln >= 5 and ntab / nln >= tab_thr:
        return "C′", "P1b_表格对象抄本", "L0", diag
    first = diag["first_line"]
    why = None
    layer = None
    if RE_STDIO.search(low) or RE_OUTEXT.search(low):
        why, layer = "E1_工具流出物", "L1"
    elif RE_BANNER.match(first) and not RE_MDH1.match(first) and not low.endswith(".md"):
        why, layer = "E2_包壳脚本流出物(首行横幅)", "L1"
    elif RE_RUNID.match(first):
        why, layer = "E2_包壳脚本流出物(首行RUN_ID)", "L1"
    elif META_SELF.search(rel):
        why, layer = "E5_自测量meta", "L1"
    if why is None and META_DIR.search("/" + "/".join(d) + "/"):
        why, layer = "E3_元记录目录", "L2"
    if why is None:
        cur = strip_rb(b)
        if cur and (cur.lower() in PEER_BASE or "/".join(d + [cur]).lower() in PEER):
            why, layer = f"E4_旧版别名(当前版名={cur})", "L2"
    if why is None and (RE_REPORT_EQ.match(low) or RE_REPORT_SW.search(low)):
        why, layer = "E6_报告类文档", "L3"
    if why is None and not low.endswith(".md") and RE_BANNER.match(first):
        why, layer = "E2b_元记录文体(包壳标题)", "L4"
    if why is None:
        return "C′", "P0_未被排除判据命中", "L4", diag
    if ev:
        return "UNDECIDED", f"U1_EVIDENCE声明 vs {why}", "CONFLICT", diag
    return "EXCL", why, layer, diag


def norm_why(w):
    return re.sub(r"\(.*\)$", "", w).strip()


def norm_label(x):
    return "C′" if x in ("C′", "C'") else x


# ------------------------------------------------------------------ Q2
def run_q2():
    det = []
    agree = 0
    for grp, s, given_kind in (("Cprime", CP_S, "keep"), ("excluded", EX_S, "mixed")):
        for r in s:
            mine, mwhy, mlayer, dg = rejudge(r["rel"])
            theirs = None
            if grp == "Cprime":
                theirs = "C′"
                twhy = r["why"]
            else:
                theirs = r["label"]
                twhy = r["why"]
            same = norm_label(mine) == norm_label(theirs)
            agree += 1 if same else 0
            det.append(dict(group=grp, rel=r["rel"], theirs=theirs, theirs_why=twhy,
                            mine=mine, mine_why=mwhy, layer=mlayer,
                            agree=same, **dg))
    return det, agree


DET, AGREE = run_q2()
TOT = len(DET)

# ------------------------------------------------------------------ Q3 阈值敏感度
# 只看「行首 VA 比例」这一条判据：把阈值 0.6 → 0.5 / 0.7，重判全部 80 个样本（不只 VA 候选），
# 统计最终 label 翻转件数。同时给出「只看 VA 门槛判定」的翻转件数（不含层优先级影响）。
def run_q3():
    out = {}
    for thr, tag in ((0.5, "50%"), (0.6, "60%"), (0.7, "70%")):
        labels = {}
        for r in CP_S + EX_S:
            labels[r["rel"]] = rejudge(r["rel"], va_thr=thr)[0]
        out[tag] = labels
    flip = {}
    for pair in (("60%", "50%"), ("60%", "70%")):
        a, b = pair
        ch = [k for k in out[a] if norm_label(out[a][k]) != norm_label(out[b][k])]
        flip[f"{a}->{b}"] = ch
    # VA 门槛本身对样本中「P1a 候选」的翻转（用实测 va_ratio）
    cand = [d for d in DET if d.get("va_ratio") is not None]
    va_flip50 = [d["rel"] for d in cand
                 if d["n_va"] >= 3 and (d["n_va"] / d["n_lines"]) >= 0.5 and (d["n_va"] / d["n_lines"]) < 0.6]
    va_flip70 = [d["rel"] for d in cand
                 if d["n_va"] >= 3 and (d["n_va"] / d["n_lines"]) >= 0.6 and (d["n_va"] / d["n_lines"]) < 0.7]
    return out, flip, va_flip50, va_flip70, cand


Q3_OUT, Q3_FLIP, VA50, VA70, CANDS = run_q3()

# ------------------------------------------------------------------ 落盘
with open(os.path.join(AUD, "audit_sample_detail.tsv"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("group\trel\ttheirs\ttheirs_why\tmine\tmine_why\tlayer\tagree\tn_lines\tn_va\tva_ratio\ttab_ratio\tfirst_line\n")
    for d in DET:
        fh.write("\t".join(str(d.get(k, "")) for k in
                           ("group", "rel", "theirs", "theirs_why", "mine", "mine_why", "layer",
                            "agree", "n_lines", "n_va", "va_ratio", "tab_ratio", "first_line")) + "\n")

json.dump(dict(
    sample_rule=dict(
        Cprime=f"files_tier_Cprime.tsv 按 rel 升序，N={CP_N}，索引=int((k+0.5)*N/40) k=0..39",
        excluded=f"files_excluded_prime.tsv 先按 label 升序分 2 组（EXCL/UNDECIDED），组内按 rel 升序、按 group_size/total 比例分配 40 个名额并等距抽取，合并后按 rel 升序取前 40；plan={EX_PLAN}",
        Cprime_idx=CP_IDX),
    q2=dict(total=TOT, agree=AGREE, disagree=TOT - AGREE, detail=DET),
    q3=dict(flip=Q3_FLIP, va_only_flip_50=VA50, va_only_flip_70=VA70,
            n_samples_with_content=TOT),
), open(os.path.join(AUD, "audit_q2q3.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
    default=str)

# ------------------------------------------------------------------ 控制台
print(f"[sample] Cprime N={CP_N} 抽 {len(CP_S)}; excluded N={EX_N} 抽 {len(EX_S)} plan={EX_PLAN}")
print(f"[Q2] 一致={AGREE}/{TOT} 不一致={TOT-AGREE}/{TOT}")
for d in DET:
    if not d["agree"]:
        print(f"  X {d['rel']} | 它={d['theirs']}({d['theirs_why']}) | 我={d['mine']}({d['mine_why']})")
print("[Q3] 60->50 翻转:", Q3_FLIP.get("60%->50%"))
print("[Q3] 60->70 翻转:", Q3_FLIP.get("60%->70%"))
print("[Q3] 纯VA门槛 落 (0.5,0.6):", VA50)
print("[Q3] 纯VA门槛 落 [0.6,0.7):", VA70)
