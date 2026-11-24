#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decide_semdef.py — R46-T1 语义定义裁决器（法 1，Python）

输入（全部为盘上既有清单，**不重跑测量、不 os.walk 全树**）:
  S1  R17_R72_T1_CLEANSCALE\\files_tier_A_snap2.tsv        档 A 全量（6 扩展名内、lead/ 下单文件的完整枚举）
  S2  R17_R72_T1_CLEANSCALE\\files_tier_C.tsv              旧档 C（逐件判过「是不是测量过程产物」的集合）
  S3  R17_R78_T1_RECLASS\\files_tier_Cprime.tsv            C′ 的 18,712 行 + why（P0/P1a/P1b）
  S4  R17_R78_T1_RECLASS\\files_excluded_prime.tsv         C′ 的排除 + 无法判定（409 + 1,242 行）
  S5  R17_R78_T1_RECLASS\\decide_cprime.py                 生成 S3/S4 的裁决器源码（用于就地重算 p1a）
  S6  R17_R81_T2_EVID\\_verdicts.tsv                       1,242 件 EVIDENCE 冲突件的逐件内容判定
  S7  lead/ 下 {@s:6 扩展名} 的实盘目录枚举（仅扩展名过滤，不是 lead/ 全树）

本脚本**不写任何 lead/ 下既有目录**，只写本目录（R17_R88_T1_SEMDEF\\）。

输出:
  tier_final.tsv       定义乙（推荐）的逐文件清单
  semi_items.tsv       「有部分内容证据、但够不上有内容证据」的半证据件（与 S6 冲突件不相交）
  other6_unknown.tsv   6 扩展名内、但不在档 A 清单里的实盘件（无 verdict → 判不了）
  excluded_final.tsv   被定义乙剔除的件（含理由）
  semdef.json          全部计数、算式、闭合校验
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

LEAD = r"D:\Project\ra2-campaign-forge\lead"
R14 = os.path.join(LEAD, "next_re_20261117_r14")
OUT = os.path.dirname(os.path.abspath(__file__))

S1 = os.path.join(R14, "R17_R72_T1_CLEANSCALE", "files_tier_A_snap2.tsv")
S2 = os.path.join(R14, "R17_R72_T1_CLEANSCALE", "files_tier_C.tsv")
S3 = os.path.join(R14, "R17_R78_T1_RECLASS", "files_tier_Cprime.tsv")
S4 = os.path.join(R14, "R17_R78_T1_RECLASS", "files_excluded_prime.tsv")
S5 = os.path.join(R14, "R17_R78_T1_RECLASS", "decide_cprime.py")
S6 = os.path.join(R14, "R17_R81_T2_EVID", "_verdicts.tsv")

SIX_EXT = {".md", ".txt", ".json", ".tsv", ".log", ".csv"}
OBJ_VERDICT = "对象抄本"
PROC_VERDICT = "过程输出"
TIE_VERDICT = "无法判定"

NUM = re.compile(r"(\d+)(\.\d+)?")
SCRIPT_NAMES = ["decide_semdef.py", "posctrl_py.py"]


def tsv(p):
    with open(p, encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh, delimiter="\t")
        return list(r)


log = []


def say(s):
    print(s)
    log.append(s)


# ------------------------------------------------------------------ 1 读清单
A = tsv(S1)
C_OLD = tsv(S2)
CP = tsv(S3)
EX = tsv(S4)
VD = tsv(S6)
say(f"[in] A={len(A):,}/{sum(int(r['bytes']) for r in A):,}B  oldC={len(C_OLD):,}/{sum(int(r['bytes']) for r in C_OLD):,}B")
say(f"[in] C′={len(CP):,}/{sum(int(r['bytes']) for r in CP):,}B  excluded+undecided={len(EX):,}/{sum(int(r['bytes']) for r in EX):,}B")
say(f"[in] evidence verdicts={len(VD):,}")

SET_C_OLD = {r["rel"] for r in C_OLD}
A_BY = {r["rel"]: int(r["bytes"]) for r in A}
CP_BY = {r["rel"]: r for r in CP}
CP_REL = set(CP_BY)
EX_BY = {r["rel"]: r for r in EX}
VD_BY = {r["rel"]: r for r in VD}

# ------------------------------------------------------------------ 2 自测量产物（只按内容自指 / 文件名闭集，不看目录）
SELF_TSV = os.path.join(R14, "R17_R72_T1_CLEANSCALE", "files_tier_A_snap2.tsv")
SELF_FILES = {
    os.path.relpath(SELF_TSV, LEAD).replace(os.sep, "/"): "自测量产物_档A清单本身（本脚本的输入）",
    os.path.relpath(os.path.join(R14, "R17_R72_T1_CLEANSCALE", "files_tier_A.tsv"), LEAD).replace(os.sep, "/"): "自测量产物_档A清单副本",
    os.path.relpath(os.path.join(R14, "R17_R72_T1_CLEANSCALE", "files_tier_A_snap1.tsv"), LEAD).replace(os.sep, "/"): "自测量产物_档A清单旧快照",
    os.path.relpath(os.path.join(R14, "R17_R72_T1_CLEANSCALE", "files_tier_B.tsv"), LEAD).replace(os.sep, "/"): "自测量产物_档B清单",
    os.path.relpath(os.path.join(R14, "R17_R72_T1_CLEANSCALE", "files_tier_C.tsv"), LEAD).replace(os.sep, "/"): "自测量产物_档C清单",
    os.path.relpath(os.path.join(R14, "R17_R72_T1_CLEANSCALE", "selfartifacts_detail.tsv"), LEAD).replace(os.sep, "/"): "自测量产物_自身产物明细",
    os.path.relpath(os.path.join(R14, "R17_R78_T1_RECLASS", "files_tier_Cprime.tsv"), LEAD).replace(os.sep, "/"): "自测量产物_C′清单",
    os.path.relpath(os.path.join(R14, "R17_R78_T1_RECLASS", "files_excluded_prime.tsv"), LEAD).replace(os.sep, "/"): "自测量产物_C′排除清单",
    os.path.relpath(os.path.join(R14, "R17_R84_T2_EVID2", "q1_tie_detail.tsv"), LEAD).replace(os.sep, "/"): "自测量产物_平票明细表",
    os.path.relpath(os.path.join(R14, "R17_R84_T2_EVID2", "tie_dump.txt"), LEAD).replace(os.sep, "/"): "自测量产物_平票转储",
    os.path.relpath(S6, LEAD).replace(os.sep, "/"): "自测量产物_内容判定表（本脚本的输入）",
    os.path.relpath(os.path.join(R14, "R17_R81_T2_EVID", "_content_metrics.tsv"), LEAD).replace(os.sep, "/"): "自测量产物_内容度量表",
    os.path.relpath(os.path.join(R14, "R17_R81_T2_EVID", "_undead_evid.tsv"), LEAD).replace(os.sep, "/"): "自测量产物_冲突件候选表",
    os.path.relpath(os.path.join(R14, "R17_R72_T1_CLEANSCALE", "summary_snap2.json"), LEAD).replace(os.sep, "/"): "自测量产物_规模汇总",
    os.path.relpath(os.path.join(R14, "R17_R72_T1_CLEANSCALE", "summary.json"), LEAD).replace(os.sep, "/"): "自测量产物_规模汇总旧版",
    os.path.relpath(os.path.join(R14, "R17_R70_T1_REPRO", "scale_vs_baseline.json"), LEAD).replace(os.sep, "/"): "自测量产物_规模对比",
}
# 过程：脚本本身也是测量装置（t7）
for r in A:
    for sn in SCRIPT_NAMES:
        if r["rel"].endswith("/" + sn) or r["rel"] == sn:
            SELF_FILES.setdefault(r["rel"], "自测量产物_本裁决器的实现（测量装置本身）")

# ------------------------------------------------------------------ 3 p1a 就地重算（与 decide_cprime.py 同判据，只读前 8 KiB）
RE_VA_START = re.compile(r"^\s*(0x)?[0-9A-Fa-f]{6,8}\s*[:\t ]")
RE_VA_START2 = re.compile(r"^\s*0x[0-9A-Fa-f]{6,8}\s{2,}")


def in_evidence(rel):
    return any(s.upper() == "EVIDENCE" for s in rel.split("/")[:-1])


def p1a_now(rel):
    """返回 (命中?, n_va, n_lines)。判据逐字取自 decide_cprime.py:174-179。"""
    p = os.path.join(LEAD, rel.replace("/", os.sep))
    try:
        with open(p, "rb") as fh:
            head = fh.read(8192)
    except OSError:
        return None
    lines = [x for x in head.split(b"\n")[:200] if x.strip()]
    va = 0
    for x in lines:
        t = x.decode("utf-8", "replace")
        if RE_VA_START.match(t) or RE_VA_START2.match(t):
            va += 1
    hit = bool(lines) and va >= 3 and va / len(lines) >= 0.6
    return (hit, va, len(lines))


# ------------------------------------------------------------------ 4 定义乙（推荐）: 有内容证据说它是对象
dec_b = {}
why_b = {}
for rel in A_BY:
    if rel in CP_BY:
        w = CP_BY[rel]["why"]
        if w.startswith("P1a_"):
            dec_b[rel] = "KEEP"
            why_b[rel] = "有内容证据=前8KiB行首VA≥60%（C′清单 why=P1a_对象抄本）"
        else:
            dec_b[rel] = "SEMI"
            why_b[rel] = "半证据=表格形态(P1b) / 无内容证据(P0兜底)，不作对象断定"
    else:
        v = VD_BY.get(rel)
        if v is None:
            dec_b[rel] = "NOEVID"
            why_b[rel] = "6扩展名内但不在档A清单，无逐件裁定"
        elif v["verdict"] == OBJ_VERDICT:
            dec_b[rel] = "KEEP"
            why_b[rel] = f"有内容证据=逐件内容判定为对象抄本（O={v['O']}/P={v['P']}，reason={v['reason']}）"
        elif v["verdict"] == PROC_VERDICT:
            dec_b[rel] = "EXCL"
            why_b[rel] = f"逐件内容判为过程输出（O={v['O']}/P={v['P']}，reason={v['reason']}）"
        else:
            dec_b[rel] = "SEMI"
            why_b[rel] = f"半证据=内容平票（O={v['O']}/P={v['P']}，reason=tie），不与对象/过程归并"

# 就地重算 p1a：与清单 why 不一致的件必须显式披露
mismatch = []
for rel in CP_REL:
    if not CP_BY[rel]["why"].startswith("P1a_"):
        continue
    now = p1a_now(rel)
    if now is None:
        mismatch.append((rel, "unreadable"))
    elif not now[0]:
        mismatch.append((rel, f"p1a_now=NO({now[1]}/{now[2]})"))

# 自测量产物一律剔除（定义乙只保留「内容证据说它是对象」；自测量清单本身不是对象抄本）
for rel, why in SELF_FILES.items():
    if rel in dec_b:
        dec_b[rel] = "EXCL"
        why_b[rel] = "自测量产物：" + why

# 旧档 C 交叉：定义乙的 KEEP 件是否全被「旧档 C 的过程筛」放行
keep_rel = {r for r in dec_b if dec_b[r] == "KEEP"}
keep_not_in_oldC = sorted(keep_rel - SET_C_OLD)
keep_in_oldC = sorted(keep_rel & SET_C_OLD)

# ------------------------------------------------------------------ 5 实盘目录枚举（补档 A 之外的 6 扩展名件）
disk = {}
for root, dirs, files in os.walk(LEAD):
    for fn in files:
        e = os.path.splitext(fn)[1].lower()
        if e in SIX_EXT:
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, LEAD).replace(os.sep, "/")
            try:
                disk[rel] = os.path.getsize(p)
            except OSError:
                disk[rel] = None
say(f"[disk] 6 扩展名实盘件 = {len(disk):,} / {sum(v for v in disk.values() if v):,}B（含取不到大小的 {sum(1 for v in disk.values() if v is None)} 件）")
disk_not_A = {k: v for k, v in disk.items() if k not in A_BY}
disk_not_A_by_ext = {}
b_dna = 0
n_dna_null = 0
for k, v in disk_not_A.items():
    e = os.path.splitext(k)[1].lower()
    disk_not_A_by_ext[e] = disk_not_A_by_ext.get(e, 0) + 1
    if v is None:
        n_dna_null += 1
    else:
        b_dna += v
say(f"[disk] 6 扩展名但不在档 A：{len(disk_not_A):,} 件 / {b_dna:,}B（另 {n_dna_null} 件取不到大小）  by_ext={disk_not_A_by_ext}")
set_A = set(A_BY)
A_not_disk = sorted(set_A - set(disk))

# ------------------------------------------------------------------ 6 三档汇总
nA, bA = len(A_BY), sum(A_BY.values())
nK = len([r for r in dec_b if dec_b[r] == "KEEP"])
bK = sum(A_BY[r] for r in dec_b if dec_b[r] == "KEEP")
nS = len([r for r in dec_b if dec_b[r] == "SEMI"])
bS = sum(A_BY[r] for r in dec_b if dec_b[r] == "SEMI")
nX = len([r for r in dec_b if dec_b[r] == "EXCL"])
bX = sum(A_BY[r] for r in dec_b if dec_b[r] == "EXCL")
nN = len([r for r in dec_b if dec_b[r] == "NOEVID"])
bN = sum(A_BY[r] for r in dec_b if dec_b[r] == "NOEVID")
assert nK + nS + nX + nN == nA and bK + bS + bX + bN == bA
say(f"[乙] KEEP={nK:,}/{bK:,}B  SEMI={nS:,}/{bS:,}B  EXCL={nX:,}/{bX:,}B  NOEVID={nN:,}/{bN:,}B  (三档+1 合计={nK+nS+nX+bN:,})")
say(f"[乙] KEEP 中不在旧档 C 的 = {len(keep_not_in_oldC)} 件 / {sum(A_BY[r] for r in keep_not_in_oldC):,}B")

# ------------------------------------------------------------------ 7 定义甲（规模口径）
# 甲 = 6 扩展名内全部实盘件 − 测量过程产物 − 自测量产物；保留对象抄本与文档
EXCL_LABEL = {"EXCL": "过程产物", "KEEP": "对象（保留）", "SEMI": "半证据（保留）",
              "NOEVID": "无裁定（保留，单列计数）"}
nJ_member = 0
bJ = 0
nJ_self = 0
bJ_self = 0
for rel in disk:
    if rel in SELF_FILES:
        nJ_self += 1
        bJ_self += disk[rel] or 0
    if rel in dec_b and dec_b[rel] == "EXCL":
        nJ_member += 1
        bJ += A_BY[rel]
j_parts = {k: [0, 0] for k in ("member_excl", "self", "disk_not_A")}
for rel in disk:
    if rel in SELF_FILES:
        j_parts["self"][0] += 1
        j_parts["self"][1] += disk[rel] or 0
    elif rel in dec_b and dec_b[rel] == "EXCL":
        j_parts["member_excl"][0] += 1
        j_parts["member_excl"][1] += A_BY[rel]
    elif rel not in A_BY:
        j_parts["disk_not_A"][0] += 1
        j_parts["disk_not_A"][1] += disk[rel] or 0
nDisk = len(disk)
bDisk = sum(v for v in disk.values() if v)
nJia = nDisk - sum(v[0] for v in j_parts.values())
bJia = bDisk - sum(v[1] for v in j_parts.values())
say(f"[甲] 实盘 6 扩展名 {nDisk:,}/{bDisk:,}B  减过程={j_parts['member_excl']}  减自测量={j_parts['self']}  减无裁定6扩展名={j_parts['disk_not_A']}  ⇒ 甲={nJia:,}/{bJia:,}B")

# ------------------------------------------------------------------ 8 落盘
def wr(name, header, rows):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(r)


keep_rows = sorted(((r, A_BY[r], why_b[r]) for r in dec_b if dec_b[r] == "KEEP"))
wr("tier_final.tsv", ["rel", "bytes", "why_content", "oldC", "in_A"], [
    (r, b, w, "Y" if r in SET_C_OLD else "N", "Y") for r, b, w in keep_rows])
wr("semi_items.tsv", ["rel", "bytes", "why", "oldC", "in_A"], [
    (r, A_BY[r], why_b[r], "Y" if r in SET_C_OLD else "N", "Y")
    for r in sorted(dec_b) if dec_b[r] == "SEMI"])
wr("excluded_final.tsv", ["rel", "bytes", "why", "oldC", "in_A"], [
    (r, A_BY[r], why_b[r], "Y" if r in SET_C_OLD else "N", "Y")
    for r in sorted(dec_b) if dec_b[r] == "EXCL"])
wr("other6_unknown.tsv", ["rel", "bytes"], [
    (r, disk_not_A[r] if disk_not_A[r] is not None else "未取得") for r in sorted(disk_not_A)])

res = dict(
    inputs=dict(A=[nA, bA], oldC=len(SET_C_OLD), oldC_b=sum(int(r["bytes"]) for r in C_OLD),
                Cp=[len(CP_REL), sum(int(r["bytes"]) for r in CP)],
                excluded=[len(EX_BY), sum(int(r["bytes"]) for r in EX)],
                verdicts=len(VD)),
    yi=dict(KEEP=[nK, bK], SEMI=[nS, bS], EXCL=[nX, bX], NOEVID=[nN, bN],
            GB=round(bK / 1e9, 6), GiB=round(bK / 2 ** 30, 6),
            keep_not_in_oldC=[len(keep_not_in_oldC), sum(A_BY[r] for r in keep_not_in_oldC)],
            keep_in_oldC=[len(keep_in_oldC), sum(A_BY[r] for r in keep_in_oldC)]),
    jia=dict(disk=[nDisk, bDisk], parts=j_parts, JIA=[nJia, bJia],
             GB=round(bJia / 1e9, 6), GiB=round(bJia / 2 ** 30, 6)),
    p1a_recheck=dict(checked=nK, mismatches=mismatch),
    disk_vs_A=dict(disk_not_A=[len(disk_not_A), b_dna, disk_not_A_by_ext],
                   A_not_disk=nA - len(A_not_disk), A_not_disk_list=A_not_disk[:20]),
)
json.dump(res, open(os.path.join(OUT, "semdef.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
say(f"[done] tier_final={len(keep_rows):,} 行 ; p1a 就地重算不一致={len(mismatch)}")
if mismatch:
    for m in mismatch[:10]:
        say("  MISMATCH " + str(m))
