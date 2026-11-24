#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""decide_cprime.py — R43-T1 档 C′ 语义裁决器（法 1：Python 实现）

只读  lead/next_re_20261117_r14/R17_R72_T1_CLEANSCALE/files_tier_A_snap2.tsv
      （以及该清单里列出的文件内容，只读打开）
只写  本目录：files_tier_Cprime.tsv / files_excluded_prime.tsv /
              q2q3_cprime.json / why_counts.json

纪律（卡 §四）：
  - 不运行 mev675.py；不重跑全树测量（不 os.walk，全部数据来自盘上既有清单）。
  - 「无法判定」单列（label=UNDECIDED），不硬塞两边。
  - 族归属（family）**只用于组织报告**，不参与裁决。裁决只看三层判据：

分层（优先级自高到低，第一个命中的层决定裁决）：
  L0  内容事实层（与文件名无关）
      P1a  对象抄本：前 8 KiB 里 ≥60% 非空行以 VA 开头（反汇编/地址表）
      P1b  表格对象抄本：≥70% 行有 ≥2 个 TAB（逐行对象事实表）
  L1  名字事实层（名字本身声明「这是某次执行的流出物」；内容已排除 L0）
      E1   stdio 重定向 / `*_out.<ext>`（任意扩展名，不止 .txt）
      E2   包壳脚本流出物：首行是 `===`/`---` 横幅、或 `RUN_ID=` 之类运行标头
            （覆盖 `*_probe.txt` / `*_check.txt` / 无后缀 `*_out` / 普通 .log 等）
      E5   自测量 meta：files_tier_* / files_scale_* / scale_*.json / *.tmp / _hits_*
  L2  路径事实层（路径本身声明「这是 lead 自己的管理产物」；内容已排除 L0）
      E3   元记录目录：_cards/_drafts/_backlog/_hygiene/_smoke/_scratch_*/_audit/_work/_rNN
      E4   旧版本别名：`.before*` / `_bak` / `.bak`，且**同目录当前版存在**（去掉标记后同名）
  L3  文体层
      E6   报告类文档：basename 匹配 `report.md`（不分大小写）或 `*_report.<任意扩展名>`

冲突规则（纪律 3）：
  P3  位于 `EVIDENCE/` 目录下的条目，若被 L1/L2/L3 命中 => UNDECIDED
      （目录名声明「这是证据」与内容/名字形态声明「这是流出物」互相冲突，不硬裁）。
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

LEAD = r"D:\Project\ra2-campaign-forge\lead"
SRC = os.path.join(LEAD, "next_re_20261117_r14", "R17_R72_T1_CLEANSCALE")
OUT = os.path.dirname(os.path.abspath(__file__))
A_TSV = os.path.join(SRC, "files_tier_A_snap2.tsv")
C_TSV = os.path.join(SRC, "files_tier_C.tsv")


def load(p):
    rows = []
    with open(p, encoding="utf-8") as fh:
        fh.readline()
        for line in fh:
            f = line.rstrip("\n").split("\t")
            rows.append({"rel": f[0], "ext": f[1], "bytes": int(f[2]),
                         "mtime_ns": int(f[3]), "selfkind": f[4]})
    return rows


RA = load(A_TSV)
RC = load(C_TSV)
SET_C = {r["rel"] for r in RC}
BY_REL = {r["rel"]: r for r in RA}
# 旧 C 表的 bytes 列自成一套（它由 final_writes.py 在 179 s 后另跑一次生成）。
# 对账必须用**旧 C 表自己的 bytes**，否则 1 行 3 B 的漂移会伪装成"不闭合"。
B_OLD = {r["rel"]: r["bytes"] for r in RC}
B_DRIFT = [(k, B_OLD[k], BY_REL[k]["bytes"]) for k in B_OLD if B_OLD[k] != BY_REL[k]["bytes"]]
print(f"[in] A={len(RA):,}/{sum(r['bytes'] for r in RA):,} B ; oldC={len(RC):,}/{sum(r['bytes'] for r in RC):,} B")
print(f"[in] A表与C表 bytes 不同的行 = {len(B_DRIFT)}: {B_DRIFT}")


# ---------------------------------------------------------------- 工具
def base(rel):
    return rel.rsplit("/", 1)[-1]


def dirs_of(rel):
    return rel.split("/")[:-1]


def in_evidence(rel):
    return any(s.upper() == "EVIDENCE" for s in dirs_of(rel))


# ---------------------------------------------------------------- 族（仅报告用）
S_REPORT_EQ = re.compile(r"^report\.md$", re.I)
S_REPORT_SW = re.compile(r"_report\.(md|txt|json|log|tsv|csv)$", re.I)
S_OUT_TXT = re.compile(r"_out\.txt$", re.I)
S_OUT_JSON = re.compile(r"_out\.json$", re.I)
S_STDIO = re.compile(r"std(out|err)", re.I)
S_PROBE_CHECK = re.compile(r"_(probe|check)\.(json|txt|log|tsv)$", re.I)
S_ROLLBACK = re.compile(r"(_before_|\.before|before_|_bak\b|\bbak\b|_backup|backup/|\.SUPERSEDED\.)", re.I)


def family(rel):
    b = base(rel)
    d = dirs_of(rel)
    if in_evidence(rel):
        return "F09_EVIDENCE"
    if "R17_LEAD_BASELINE" in d:
        return "F10_R17_LEAD_BASELINE"
    if S_REPORT_EQ.match(b):
        return "F01_bare_REPORT.md"
    if S_REPORT_SW.search(b):
        return "F02_star_report.md"
    if "_cards" in d:
        return "F03_cards_md"
    if b.lower() in ("changes.md", "readme.md"):
        return "F04_CHANGES_README"
    if S_OUT_TXT.search(b):
        return "F05_star_out.txt"
    if S_OUT_JSON.search(b):
        return "F06_star_out.json"
    if S_STDIO.search(b):
        return "F07_stdout_stderr"
    if S_PROBE_CHECK.search(b):
        return "F08_probe_check"
    if S_ROLLBACK.search(rel):
        return "F11_rollback_copy"
    if b.lower().endswith(".tmp"):
        return "F12_tmp"
    return "F99_other"


# ---------------------------------------------------------------- 内容读取
def read_head(rel, n=8192):
    p = os.path.join(LEAD, rel.replace("/", os.sep))
    try:
        with open(p, "rb") as fh:
            return fh.read(n)
    except OSError:
        return None


RE_VA_START = re.compile(r"^\s*(0x)?[0-9A-Fa-f]{6,8}\s*[:\t ]")
RE_VA_START2 = re.compile(r"^\s*0x[0-9A-Fa-f]{6,8}\s{2,}")
RE_SHELL = re.compile(r"^\s*(={3,}|-{3,}|#{1,6}\s)")
RE_MD_HEAD = re.compile(r"^#\s+\S")
RE_RUNID = re.compile(r"^\s*(RUN_ID\b|run_id\s*[:=])", re.I)

META_DIR = re.compile(
    r"(^|/)(_cards|_drafts|_backlog|_hygiene|_smoke|_scratch_[^/]+|_lead_audit|_audit|_work|"
    r"_archive|_archive_probe|_raw|_verify|_r\d+)(/|$)", re.I)
META_SELF = re.compile(r"(^|/)(files_(tier|scale)_[^/]*|_hits_[^/]*|scale_[^/]*\.json|[^/]*\.tmp)$", re.I)
ROLLBACK_MARK = re.compile(r"(\.before[._][^/]*|\.before$|_before_[^/]*|_bak(\.[^/]*)?$|\.bak$)", re.I)


def strip_rollback(b):
    m = ROLLBACK_MARK.search(b)
    if not m:
        return None
    stem = b[:m.start()]
    tail = b[m.end():]
    ext = ""
    if "." in tail:
        ext = tail[tail.index("."):]
    if not ext:
        mm = re.search(r"(\.[A-Za-z0-9]{1,5})$", b)
        ext = mm.group(1) if mm else ""
    return stem + ext


def decide(rel, peer_index, peer_basenames):
    b = base(rel)
    d = dirs_of(rel)
    low = b.lower()
    ev = in_evidence(rel)
    head = read_head(rel)
    if head is None:
        return "UNDECIDED", "U0_不可读(取不到内容)", "U0"

    lines = [x for x in head.split(b"\n")[:200] if x.strip()]
    # ---- L0
    va = sum(1 for x in lines if RE_VA_START.match(x.decode("utf-8", "replace"))
             or RE_VA_START2.match(x.decode("utf-8", "replace")))
    if lines and va >= 3 and va / len(lines) >= 0.6:
        return "C′", f"P1a_对象抄本(行首VA {va}/{len(lines)})", "L0"
    if low.endswith((".tsv", ".csv")) and len(lines) >= 5:
        tabs = sum(1 for x in lines if x.count(b"\t") >= 2)
        if tabs / len(lines) >= 0.7:
            return "C′", "P1b_表格对象抄本", "L0"

    first = head.split(b"\n", 3)[0].decode("utf-8", "replace")
    # ---- L1
    why = None
    if S_STDIO.search(low) or re.search(r"[_\-.]out\.(txt|json|log|md|tsv|csv)$", low, re.I):
        why = "E1_工具流出物(名含stdout/out.)"
    elif RE_SHELL.match(first) and not RE_MD_HEAD.match(first) and not low.endswith(".md"):
        # md 文件以 `###` / `---` 开头是 markdown 语法本身，不能当包壳横幅（反例见 Q1/E2）；
        # md 的排除由 L2（元记录目录）与 L3（报告类）负责。
        why = "E2_包壳脚本流出物(首行横幅)"
    elif RE_RUNID.match(first):
        why = "E2_包壳脚本流出物(首行RUN_ID)"
    elif META_SELF.search(rel):
        why = "E5_自测量meta"
    layer = "L1"
    # ---- L2
    if why is None:
        layer = "L2"
        if META_DIR.search("/" + "/".join(d) + "/"):
            why = "E3_元记录目录"
    # ---- L2b 旧版别名：判据是「存在更新的同名兄弟」，与是否还有原版无关
    #      （13 个 GOAL_*.md 的当前版已被删/移走，只剩 before 副本，但它们仍是旧版别名）
    if why is None:
        layer = "L2"
        cur = strip_rollback(b)
        if cur and (cur.lower() in peer_basenames or ("/".join(d + [cur])).lower() in peer_index):
            why = f"E4_旧版别名(当前版名={cur})"
    # ---- L3
    if why is None:
        layer = "L3"
        if S_REPORT_EQ.match(low) or S_REPORT_SW.search(low):
            why = "E6_报告类文档"
    # ---- L4 元记录文体（只对非 md）：`===`/`###` 包壳标题开头的 .txt/.log 记录
    #      按「B 卷·记录层面」口径由 E2 下移到这里，写明它排的是"本线自己的过程记录"。
    if why is None and not low.endswith(".md"):
        if RE_SHELL.match(first):
            why = "E2b_元记录文体(包壳标题)"
            layer = "L4"
    if why is None:
        return "C′", "P0_未被排除判据命中", "L4"
    if ev:
        return "UNDECIDED", f"U1_EVIDENCE声明 vs {why}", "CONFLICT"
    return "EXCL", why, layer


peer = {r["rel"].lower(): r["rel"] for r in RA}
PEER_BASE = {base(r["rel"]).lower() for r in RA}
dec = {r["rel"]: decide(r["rel"], peer, PEER_BASE) for r in RA}


def norm(w):
    return re.sub(r"\(.*\)$", "", w)


def tot(lab):
    s = [r for r in RA if dec[r["rel"]][0] == lab]
    return len(s), sum(r["bytes"] for r in s)


n_cp, b_cp = tot("C′")
n_ex, b_ex = tot("EXCL")
n_ud, b_ud = tot("UNDECIDED")
n_a, b_a = len(RA), sum(r["bytes"] for r in RA)
assert n_cp + n_ex + n_ud == n_a and b_cp + b_ex + b_ud == b_a
print(f"[out] C'={n_cp:,}/{b_cp:,} B  EXCL={n_ex:,}/{b_ex:,} B  UD={n_ud:,}/{b_ud:,} B")

# ---------------------------------------------------------------- 落盘
with open(os.path.join(OUT, "files_tier_Cprime.tsv"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("rel\text\tbytes\tmtime_ns\tfamily\twhy\n")
    for r in sorted(RA, key=lambda x: x["rel"]):
        lab, why, _ = dec[r["rel"]]
        if lab == "C′":
            fh.write(f'{r["rel"]}\t{r["ext"]}\t{r["bytes"]}\t{r["mtime_ns"]}\t{family(r["rel"])}\t{why}\n')

with open(os.path.join(OUT, "files_excluded_prime.tsv"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("rel\text\tbytes\tmtime_ns\tfamily\tlabel\twhy\tlayer\tin_tier_C_old\n")
    for r in sorted(RA, key=lambda x: x["rel"]):
        lab, why, layer = dec[r["rel"]]
        if lab == "C′":
            continue
        fh.write(f'{r["rel"]}\t{r["ext"]}\t{r["bytes"]}\t{r["mtime_ns"]}\t{family(r["rel"])}\t{lab}\t{why}\t{layer}\t'
                 f'{"Y" if r["rel"] in SET_C else "N"}\n')

# ---------------------------------------------------------------- Q3
q3 = {}
for f in sorted({family(r["rel"]) for r in RA}):
    rows = [r for r in RA if family(r["rel"]) == f]
    add = [r for r in rows if dec[r["rel"]][0] == "C′" and r["rel"] not in SET_C]
    rem = [r for r in rows if dec[r["rel"]][0] == "EXCL" and r["rel"] in SET_C]
    q3[f] = dict(
        n_total=len(rows), b_total=sum(r["bytes"] for r in rows),
        old_kept_n=sum(1 for r in rows if r["rel"] in SET_C),
        old_kept_b=sum(r["bytes"] for r in rows if r["rel"] in SET_C),
        new_kept_n=sum(1 for r in rows if dec[r["rel"]][0] == "C′"),
        new_kept_b=sum(r["bytes"] for r in rows if dec[r["rel"]][0] == "C′"),
        new_out_n=sum(1 for r in rows if dec[r["rel"]][0] == "EXCL"),
        new_out_b=sum(r["bytes"] for r in rows if dec[r["rel"]][0] == "EXCL"),
        new_ud_n=sum(1 for r in rows if dec[r["rel"]][0] == "UNDECIDED"),
        new_ud_b=sum(r["bytes"] for r in rows if dec[r["rel"]][0] == "UNDECIDED"),
        added_n=len(add), added_b=sum(r["bytes"] for r in add),
        removed_n=len(rem), removed_b=sum(r["bytes"] for r in rem),
        added_reasons=dict(collections.Counter(norm(dec[r["rel"]][1]) for r in add).most_common()),
        removed_reasons=dict(collections.Counter(norm(dec[r["rel"]][1]) for r in rem).most_common()),
    )

add_n = sum(v["added_n"] for v in q3.values())
add_b = sum(v["added_b"] for v in q3.values())
rem_n = sum(v["removed_n"] for v in q3.values())
rem_b = sum(v["removed_b"] for v in q3.values())
b_c_old = sum(r["bytes"] for r in RC)
cp_set = {r["rel"] for r in RA if dec[r["rel"]][0] == "C′"}
ex_set = {r["rel"] for r in RA if dec[r["rel"]][0] == "EXCL"}
ud_set = {r["rel"] for r in RA if dec[r["rel"]][0] == "UNDECIDED"}
assert cp_set | ex_set | ud_set == set(BY_REL) and not (cp_set & ex_set or cp_set & ud_set or ex_set & ud_set)

# 三分类上的位移表（这套按集合算术，必闭合）：
#   旧C留 & 新C′留      = 不动
#   旧C留 & 新EXCL      = removed（旧留→新排）
#   旧C留 & 新UNDECIDED = moved（旧留→新"无法判定"）
#   旧C排 & 新C′留      = added（旧排→新留）
#   旧C排 & 新EXCL      = 不动（排→排，只是理由换了）
#   旧C排 & 新UNDECIDED = into_undecided_unmatched（旧排→新"无法判定"）
shift = dict(
    K_user_K_new=len(SET_C & cp_set), K_user_E_new=len(SET_C & ex_set), K_user_U_new=len(SET_C & ud_set),
    O_user_K_new=len(cp_set - SET_C), O_user_E_new=len(ex_set - SET_C), O_user_U_new=len(ud_set - SET_C),
)
shift["sum_n"] = sum(shift[k] for k in list(shift))
assert shift["sum_n"] == len(BY_REL)

add_n = sum(v["added_n"] for v in q3.values())
add_b = sum(v["added_b"] for v in q3.values())
rem_n = sum(v["removed_n"] for v in q3.values())
rem_b = sum(v["removed_b"] for v in q3.values())
b_c_old = sum(r["bytes"] for r in RC)
ud_from_oldC = sorted(SET_C & ud_set)
ud_b = sum(B_OLD[x] for x in ud_from_oldC)
# 逐字节闭合的正确写法：
#   ΣC′ = Σ(旧C 中仍留的) + Σ(旧C排而新留的)
# 旧C 的 bytes 必须用"交集用 A 表列、非交集用 C 表列"，因为 C 表有 1 行 3 B 漂移。
oldC_in_cp_b = sum(BY_REL[k]["bytes"] for k in SET_C & cp_set)
closure = dict(
    old_C_n=len(RC), old_C_b=b_c_old, new_Cp_n=n_cp, new_Cp_b=b_cp,
    added_n=add_n, added_b=add_b, removed_n=rem_n, removed_b=rem_b,
    moved_to_undecided_n=len(ud_from_oldC), moved_to_undecided_b=ud_b,
    shift=shift,
    old_C_in_cp_b=oldC_in_cp_b,
    arith_n=shift["K_user_K_new"] + shift["O_user_K_new"],
    arith_b=oldC_in_cp_b + add_b,
    closed_n=(shift["K_user_K_new"] + shift["O_user_K_new"] == n_cp),
    closed_b=(oldC_in_cp_b + add_b == b_cp),
    closed_b_delta=b_cp - (oldC_in_cp_b + add_b),
    total_cp_minus_added_b=b_cp - add_b,
    cp_minus_oldC_n=len(cp_set - SET_C), cp_minus_oldC_b=add_b,
    oldC_minus_cp_n=len(SET_C - cp_set), oldC_minus_cp_b=sum(B_OLD[x] for x in (SET_C - cp_set)),
    A_minus_Cp_n=n_a - n_cp, A_minus_Cp_b=b_a - b_cp,
    A_table_vs_C_table_byte_drift_b=sum(abs(B_OLD[k] - BY_REL[k]["bytes"]) for k, _, _ in B_DRIFT),
    A_table_vs_C_table_byte_drift_rows=B_DRIFT,
)
assert closure["closed_n"] and closure["closed_b"], closure

wc = collections.Counter()
wb = collections.Counter()
kc = collections.Counter()
kb = collections.Counter()
for r in RA:
    lab, why, layer = dec[r["rel"]]
    if lab == "C′":
        kc[norm(why)] += 1
        kb[norm(why)] += r["bytes"]
    else:
        wc[f"{lab}|{norm(why)}"] += 1
        wb[f"{lab}|{norm(why)}"] += r["bytes"]

q2 = dict(source=os.path.basename(A_TSV), A_n=n_a, A_b=b_a,
          Cp_n=n_cp, Cp_b=b_cp, Cp_GB=round(b_cp / 1e9, 6), Cp_GiB=round(b_cp / 2 ** 30, 6),
          EXCL_n=n_ex, EXCL_b=b_ex, UNDECIDED_n=n_ud, UNDECIDED_b=b_ud,
          A_minus_Cp_n=n_a - n_cp, A_minus_Cp_b=b_a - b_cp,
          A_minus_Cp_GB=round((b_a - b_cp) / 1e9, 6), A_minus_Cp_GiB=round((b_a - b_cp) / 2 ** 30, 6))
json.dump(dict(q2=q2, q3=q3, closure=closure,
               why_counts_excl={k: dict(n=wc[k], b=wb[k]) for k in sorted(wb, key=lambda x: -wb[x])},
               why_counts_keep={k: dict(n=kc[k], b=kb[k]) for k in sorted(kb, key=lambda x: -kb[x])}),
          open(os.path.join(OUT, "q2q3_cprime.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("[done] files_tier_Cprime.tsv / files_excluded_prime.tsv / q2q3_cprime.json")
print(json.dumps(closure, ensure_ascii=False, indent=1))
print(json.dumps({k: dict(n=wc[k], b=wb[k]) for k in sorted(wb, key=lambda x: -wb[x])}, ensure_ascii=False, indent=1))
print(json.dumps({k: dict(n=kc[k], b=kb[k]) for k in sorted(kb, key=lambda x: -kb[x])}, ensure_ascii=False, indent=1))
