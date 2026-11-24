#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""q2q3_types.py — R45-T1 Q2/Q3（法 1：Python 实现）

输入（只读）：
  R17_R78_T1_RECLASS/files_tier_Cprime.tsv                      —— why 列（R1）
  R17_R84_T1_NARRATIVE/narrative_candidates.tsv                 —— Q1 清单（4,493 件）
  lead/<候选件> 的前 8 KiB                                        —— 内容判据
  R17_R72_T1_CLEANSCALE/files_tier_A_snap2.tsv                  —— 「同目录当前版是否存在」（T2 的 E4 判据）
输出（只写本目录）：
  should_exclude.tsv / q2q3_types.json / unsure.tsv

分型只看**内容形态与结构**，文件名/目录名只在明确声明处使用（见每型一行 `name_used=Y`）。

T0（先跑，吸收"对象抄本被 P0 兜住"的那部分）
  T0a  body_va_ratio>=0.60                        —— 与 P0 自己的 P1a 同一条判据，只是改成"行首 VA 在**任意缩进**都算"
      （P1a 的正则 `^\\s*(0x)?[0-9A-Fa-f]{6,8}\\s*[:\\t ]` 要求 VA 后紧跟 `: \\t` 或空格；
        缩进两格的正文 VA 行只要后面不是这三种分隔符就漏判 —— 实测 `ROW_*.txt` 的正文就是这种形态）
  T0b  行级： 每行要么"行首 VA"，要么"含 >=2 TAB"。全行都满足 ⇒ 表格对象抄本
      （P1b 只在整件 ≥70% 行有 ≥2 TAB 时才命中；一行表头 + 全 TAB 正文的 .tsv 会被表头拉低到 97% 仍命中，
        但"叙述式表头 + TAB 正文"的 .txt 完全漏判）
  T0c  行级： 行首 VA 行占 >=30% 且 首行是 `# 标题`/`## 标题` 且 前 8 KiB 含 >=3 行 `0x\\w+` ——
       判"先写章节标题、正文是地址/指令流水"的流水体（如 WRITE_POINTS_DETAIL.md）

T1  判词/结论摘要（确应排除）
  判据：basename（小写）∈ 闭集 {disagree.md, unknowns.md, superseded.md, progress.md,
        pending_decisions.md, pending*.md,*_signoffs.md, verdict.md}
        或 basename 以 `pending` 开头
  为什么该排：这类文件的内容**整体是"某事是否成立"的结论/未决清单**（首行即标题声明），
        不含逐条对象事实；C′ 的定义是"未被排除的逆向证据集合"，结论摘要属于对证据的**二次加工**，
        其事实来源必已在 C′ 内的别的文件里逐条落过 —— 留它只会让同一结论被读两遍并把体积算进证据量。
        实测这些件 narr 行占比 ≥0.7、body_va=0，可复核。

T2  同一叙述的旧快照 / 非当前版副本（确应排除）——**两条并列判据，任一命中**
  判据一律"内容向"：先把前 8 KiB 的叙述行抽出来做**内容指纹**，
  两条判据问的都是"同一段叙述是不是已经在盘上别处还有一份（更新的或当前版）"：
  T2a 滚回标记（强）：basename 含 `.before` / `before_` / `_bak` / `.bak` 标记。滚回标记是**文件名断言**
       "我是某时刻对同名当前件的旧快照"。判据分两档，为的是把"名字断言 + 内容/清单任一佐证"的与"只有名字断言"的分开记账：
        T2a=1：去掉标记后的名字出现在 files_tier_A_snap2.tsv 的 basename 集合里（当前版在盘上可证）
        T2a=2：当前版名不在 A 表里 —— 但实测这类名字去掉标记后往往是**本身就叫 backup 的文件**
                （`GOAL_backup_before_858.md` → `GOAL_backup.md`、`control_20261106/backup/PHASE_BY_BOOT.before_erratum_*.md`），
                属于"备份的备份"。单靠名字，纪律 23 不允许直接判排，故 T2a=2 **只有在内容指纹也成群时才排**，
                否则进 U1（无法判定）。
  T2b 同首段内容簇：把「首行(标题) + 前 40 个叙述行」里的数字串替换成 `#`（去掉轮次/§/时间戳/字节数）
       得到指纹 F。簇 C(F) = 候选集里同一 F 的全部件。排除条件三条并列：
         (i)  |F 的叙述行数| >= 10（保证是"一段正文"，不是一两句抬头）
         (ii) |C(F)| >= 3
         (iii) 本件不是簇里唯一最大的那份（bytes < max(C(F)) 或同尺寸存在更短 rel 的并列者）
       另外先剔除"沙箱逐字节备份"目录（路径含 `_akv_own/`、`_akv_pre/`、`_akv_sbx/`）：
       这些目录是 andk 复核线把**整棵 lead 拷贝 N 份**做的隔离实验，同一文件在里面出现 N 次属于实验构造，
       不是文档被重复写；判它们该排的判据是"沙箱备份"，不是"叙述体"，留给别的排除判据，不在这里记账。
  **为什么这一型该排**：一是文件名自己声明"我是某一轮之前的版本"（T2a）；
  二是 T2b 是**同一段叙述被重复落盘 ≥3 次**（每轮一份快照，或同一份文档被复制到新目录）。
  C′ 是"未被排除集合"，它回答的是"该字节串该不该算进证据体"。
  同一段叙述的第 2..N 份副本**不增加任何对象事实**，只是把同一份判词按轮次复制 N 遍：
  实测 GOAL_THREE_TARGETS 家族 52 份 ≈ 141.5 MB，占 4,493 件 210.2 MB 的 67.3%，
  若只按文件名判（纪律 23 禁止），这 52 份里有 22 份名字带 before、另 30 份名字**完全正常**，
  只靠 before/bak 只能抓到 2/3 字节 → 所以 T2b 必须走内容指纹。
  留它们的唯一效果是让"证据量"被同一篇文档放大 N 倍（4.48 MB 的文档被计成 141 MB）。
  注意：判据不要求"当前版存在"（部分当前版已被移走），此时用内容簇回答"它是不是别的份的副本"。

T3  对象抄本的叙述式封装（确应排除）
  判据：T0a/T0b/T0c 任一命中（内容判据），且 basename 不在 T1 闭集里
  为什么该排：这些件**正文主体是对象事实**（行首 VA / 指令字节 / TAB 列），
        但因为前面多了一段中文前言/表格说明/TAB 表头，P1a 的 60% 门槛与 P1b 的 70% 门槛都没过，
        于是落进 P0 兜底。它们是"对象抄本"的另一种排布，不是叙述 —— 按 C′ 自己的口径（P1a/P1b ⇒ C′ 保留）
        本应归"对象抄本"，却被 why 列记成"未被排除判据命中"，与对象抄本同落 P0、口径未区分。
        **排它不是因为它是笔记，而是因为它本来就不是叙述体；它该进的是 P1a/P1b 的账。**

U1  无法判定（单列）
  判据：前缀只有工程编号/路径、首行是 `=== `/`--- ` 横幅或用全大写键=值，
        正文看不到任何中文句子；既像包壳脚本的流出物，又可能只是带说明的表格。

K1  其余（保留）
  判据：①中文叙述（判词/草稿/小结）为主体 ②或 结构化对象事实（JSON/CSV/TSV 键值或列式记录，
        中文只是在**字段值**里做注释）③或 小卡片/说明。它们提供的是对象事实或本轮判词，
        C′ 留它们符合"未被排除"的定义：没有别的排除判据能回答"为什么这一型该排"。
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
A_TSV = os.path.join(R14, "R17_R72_T1_CLEANSCALE", "files_tier_A_snap2.tsv")
OUT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(OUT, "narrative_candidates.tsv")

RE_CN = re.compile(r"[\u4e00-\u9fff]")
RE_VA_ANY = re.compile(r"^\s*(0x)?[0-9A-Fa-f]{6,8}\s*[:\t ]")
RE_VA_ANY2 = re.compile(r"^\s*0x[0-9A-Fa-f]{6,8}\s{2,}")
RE_VA_BODY = re.compile(r"(?m)^\s*(0x)?[0-9A-Fa-f]{6,8}\s{2,}\S")
RE_0X = re.compile(r"0x[0-9A-Fa-f]{4,8}")

T1_NAMES = {"disagree.md", "unknowns.md", "superseded.md", "progress.md",
            "pending_decisions.md", "verdict.md", "pending_and_signoffs.md"}
RE_T1_EXTRA = re.compile(r"^(pending[^/]*\.(md|txt)|[^/]*_signoffs\.md)$", re.I)
RE_ROLLBACK = re.compile(r"(\.before[._][^/]*|\.before$|_before_[^/]*|_bak(\.[^/]*)?$|\.bak$)", re.I)


def base(rel):
    return rel.rsplit("/", 1)[-1]


def read_head(rel, n=8192):
    try:
        with open(os.path.join(LEAD, rel.replace("/", os.sep)), "rb") as fh:
            return fh.read(n)
    except OSError:
        return None


def feats(text):
    ls = [x for x in text.split("\n")[:200] if x.strip()] or [""]
    n = len(ls)
    va = 0
    tabline = 0
    narr = 0
    for x in ls:
        if RE_VA_ANY.match(x) or RE_VA_ANY2.match(x):
            va += 1
            continue
        if x.count("\t") >= 2:
            tabline += 1
            continue
        if RE_CN.search(x) and len(x.strip()) >= 8:
            narr += 1
    return dict(n=n, va=va, tabline=tabline, narr=narr,
                body_va_ratio=va / n, tab_frac=tabline / n, narr_frac=narr / n,
                n0x=len(RE_0X.findall(text)), first=ls[0][:160],
                head_is_hdr=bool(re.match(r"^\s#{1,3}\s", ls[0])))


def strip_rollback(b):
    m = RE_ROLLBACK.search(b)
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


def narr_lines(text):
    """叙述行：非空、非行首VA、非 TAB 表行、含中文、长度>=8"""
    out = []
    for x in text.split("\n")[:200]:
        if not x.strip():
            continue
        if RE_VA_ANY.match(x) or RE_VA_ANY2.match(x):
            continue
        if x.count("\t") >= 2:
            continue
        if RE_CN.search(x) and len(x.strip()) >= 8:
            out.append(x.strip())
    return out


RE_NUMS = re.compile(r"[0-9]+")


def fingerprint(text):
    ls = narr_lines(text)[:40]
    if not ls:
        return None, 0
    body = "".join(RE_NUMS.sub("#", x) for x in ls)
    return body, len(ls)


def main():
    # --- A 表 basename 集合（E4 的"当前版存在"判据）
    peer = set()
    with open(A_TSV, encoding="utf-8") as fh:
        fh.readline()
        for line in fh:
            peer.add(base(line.split("\t", 1)[0]).lower())

    # --- C′ 的 why
    why = {}
    with open(CP_TSV, encoding="utf-8") as fh:
        fh.readline()
        for line in fh:
            f = line.rstrip("\n").split("\t")
            why[f[0]] = f[5]

    rows = []
    for line in open(CAND, encoding="utf-8").read().splitlines()[1:]:
        f = line.split("\t")
        rows.append(dict(rel=f[0], bytes=int(f[1]), cn_ratio=float(f[3])))

    # --- 第一遍：取内容 + 算指纹（T2b 需要全候选集的簇统计，故先收集）
    pre = []
    for r in rows:
        rel = r["rel"]
        h = read_head(rel)
        if h is None:
            pre.append(dict(r, text=None))
            continue
        text = h.decode("utf-8", "replace")
        fp, fp_n = fingerprint(text)
        pre.append(dict(r, text=text, fp=fp, fp_n=fp_n))

    # T2b 簇：|F| >= 10 且同一 F 出现 >=3 次
    fp_groups = {}
    for x in pre:
        if x["text"] is not None and x["fp"] and x["fp_n"] >= 10:
            fp_groups.setdefault(x["fp"], []).append(x)
    fp_max = {k: max(y["bytes"] for y in v) for k, v in fp_groups.items() if len(v) >= 3}

    SBX = re.compile(r"(^|/)(_akv_own|_akv_pre|_akv_sbx)(/|$)")

    def cluster_is_dup(x):
        """T2b 判据；返回 (是否该排, 说明)"""
        grp = fp_groups.get(x["fp"])
        if not grp or len(grp) < 3 or x["fp_n"] < 10:
            return False, ""
        mx = fp_max.get(x["fp"])
        if mx is None:
            return False, ""
        if x["bytes"] < mx:
            return True, f'T2b(内容簇 {len(grp)} 份, 本件 {x["bytes"]}B < 簇最大 {mx}B)'
        # 并列最大：按 rel 字典序保留第一份
        same = sorted([y for y in grp if y["bytes"] == mx], key=lambda y: y["rel"])
        if same and same[0]["rel"] != x["rel"]:
            return True, f'T2b(内容簇 {len(grp)} 份, 本件与最大份同尺寸, 按 rel 序保留 {same[0]["rel"]})'
        return False, ""

    typed = []
    for x in pre:
        rel, b = x["rel"], base(x["rel"])
        low = b.lower()
        if x["text"] is None:
            typed.append(dict(x, type="未取得", reason="U0_不可读(取不到内容)", keys=""))
            continue
        text = x["text"]
        ft = feats(text)
        t0 = []
        if ft["body_va_ratio"] >= 0.60:
            t0.append(f'T0a(行首VA任意缩进 {ft["va"]}/{ft["n"]})')
        if ft["n"] + 0 and (ft["va"] + ft["tabline"]) / ft["n"] >= 0.95:
            t0.append(f'T0b(每行VA或TAB {ft["va"] + ft["tabline"]}/{ft["n"]})')
        if ft["body_va_ratio"] >= 0.30 and ft["head_is_hdr"] and ft["n0x"] >= 3:
            t0.append(f'T0c(标题+地址流水 {ft["va"]}/{ft["n"]}, 0x行={ft["n0x"]})')

        if t0:
            t = "T3_对象抄本的叙述式封装"
            reason = "内容主体是对象事实（" + "; ".join(t0) + "），中文只是前言/表头"
            keys = "content:body_va/tabline/head"
        elif low in T1_NAMES or RE_T1_EXTRA.match(low):
            t = "T1_判词结论摘要"
            reason = f'basename 声明"结论/未决清单"；narr={ft["narr"]}/{ft["n"]}, bodyva={ft["va"]}, 0x行={ft["n0x"]}'
            keys = "name:T1_closure+content:bodyva=0"
        else:
            cur = strip_rollback(b)
            mark = bool(cur)
            peer_hit = bool(cur and cur.lower() in peer)
            is_dup, dup_note = cluster_is_dup(x)
            eff_dup = bool(is_dup and not SBX.search(rel))
            if peer_hit or eff_dup:
                t = "T2_旧版副本"
                bits = []
                if peer_hit:
                    bits.append(f"T2a=1(滚回标记→当前版名 {cur} 在 A 表)")
                if is_dup:
                    bits.append(("T2b" + dup_note[3:]) if eff_dup else (dup_note + " [沙箱备份目录，不计入本型]"))
                reason = "; ".join(bits) + f'；narr={ft["narr"]}/{ft["n"]}'
                keys = "name:rollback_mark+list:A_peer_exists" if peer_hit else "content:first40_narr_lines_fingerprint"
                if peer_hit and eff_dup:
                    keys = "both"
            else:
                # U1：首行横幅/键值，且正文看不到中文句子
                hdr = re.match(r"^(={3,}\s|-{3,}\s)", ft["first"]) or re.match(r"^[A-Z][A-Z0-9_]{3,}\s*=", ft["first"])
                pref = re.match(r"^[A-Za-z_][\w./\\-]*\s+[\[{]?\w*[:=]", ft["first"]) or re.match(r"^[^\s:]{2,40}:\s", ft["first"])
                if ft["narr"] == 0 and (hdr or pref):
                    t = "U1_无法判定"
                    reason = "首行是包壳横幅/键值或编号前缀，正文无一句中文；像流出物也可能只是带说明的表格"
                    keys = "content:firstline_form"
                elif mark and not is_dup:
                    t = "U1_无法判定"
                    reason = (f'名字有滚回标记（→ {cur}），但当前版名不在 A 表、内容指纹也不成群'
                              f'（簇 {len(fp_groups.get(x["fp"], []))} 份）；仅凭名字不许判排')
                    keys = "name_only(rollback_mark)"
                else:
                    t = "K1_保留"
                    if ft["narr_frac"] >= 0.5:
                        reason = f'中文叙述为主体 narr={ft["narr"]}/{ft["n"]}; 无排除判据可命中'
                    elif ft["n0x"] >= 3 or ft["va"] >= 1:
                        reason = f'结构化事实/说明混合 narr={ft["narr"]}/{ft["n"]}, bodyva={ft["va"]}, 0x={ft["n0x"]}'
                    else:
                        reason = f'结构化记录 narr={ft["narr"]}/{ft["n"]}，中文在字段值里'
                    keys = "none"
        typed.append(dict(x, type=t, reason=reason, keys=keys, ft=ft))

    # ---- 落盘
    EX_LABELS = ("T1_判词结论摘要", "T2_旧版副本", "T3_对象抄本的叙述式封装")
    with open(os.path.join(OUT, "should_exclude.tsv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("rel\tbytes\ttype\twhy\n")
        for r in sorted([x for x in typed if x["type"] in EX_LABELS], key=lambda x: (x["type"], x["rel"])):
            fh.write(f'{r["rel"]}\t{r["bytes"]}\t{r["type"]}\t{r["reason"]}\n')

    with open(os.path.join(OUT, "unsure.tsv"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("rel\tbytes\ttype\twhy\n")
        for r in sorted([x for x in typed if x["type"] == "U1_无法判定"], key=lambda x: x["rel"]):
            fh.write(f'{r["rel"]}\t{r["bytes"]}\t{r["type"]}\t{r["reason"]}\n')

    agg = {}
    for t in ("T1_判词结论摘要", "T2_旧版副本", "T3_对象抄本的叙述式封装", "K1_保留", "U1_无法判定", "未取得"):
        g = [x for x in typed if x["type"] == t]
        agg[t] = dict(n=len(g), bytes=sum(x["bytes"] for x in g))

    ex = [x for x in typed if x["type"] in EX_LABELS]
    n_ex, b_ex = len(ex), sum(x["bytes"] for x in ex)

    # C′ 基线
    n_cp, b_cp = 18712, 1363708720
    n_after, b_after = n_cp - n_ex, b_cp - b_ex

    # K1 里再细分：真叙述(中文叙述为主体，含草稿/备忘/小结/判词) vs 结构化
    k1 = [x for x in typed if x["type"] == "K1_保留"]
    k1_prose = [x for x in k1 if x["ft"]["narr_frac"] >= 0.5]
    k1_struct = [x for x in k1 if x["ft"]["narr_frac"] < 0.5]

    out = dict(
        源_清单="next_re_20261117_r14/R17_R78_T1_RECLASS/files_tier_Cprime.tsv (why 列) + narrative_candidates.tsv",
        判据="见 q2q3_types.py 文档串 T0/T1/T2/T3/U1/K1",
        n_candidates=len(typed), b_candidates=sum(x["bytes"] for x in typed),
        types=agg,
        K1_sub=dict(prose_n=len(k1_prose), prose_b=sum(x["bytes"] for x in k1_prose),
                    struct_n=len(k1_struct), struct_b=sum(x["bytes"] for x in k1_struct)),
        exclude_n=n_ex, exclude_b=b_ex,
        after=dict(n=n_after, b=b_after, GB=round(b_after / 1e9, 6), GiB=round(b_after / 2 ** 30, 6)),
        before=dict(n=n_cp, b=b_cp, GB=round(b_cp / 1e9, 6), GiB=round(b_cp / 2 ** 30, 6)),
    )
    json.dump(out, open(os.path.join(OUT, "q2q3_types.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
