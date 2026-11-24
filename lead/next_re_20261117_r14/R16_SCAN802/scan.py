#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan.py — R16-SCAN-EVID-802 度量器（只读 + 只写 R16_SCAN802/）

问题：802 行 `R_TRACE_ONLY` 的 `[已证]`，在 lead/ 全树里有没有"逐 entry 证据文件"可回指？

阶段 A（全量 802 行，文件系统级）
  A1 文件名命中：某文件的 basename 含该 entry 的 8 位十六进制（大小写不敏感）
  A2 路径命中  ：某文件的完整相对路径含该 entry 的 8 位十六进制
  并计算每个命中文件被多少行共享（M81 第二层弱化的度量）

阶段 B（严格 18 行抽样，内容级）
  抽样规则固定可复现：802 行按 entry 升序，取索引 0、801、以及 50,100,...,800（16 个）
  对每个抽样行：在 lead/ 全树内容里搜该 entry，把命中按行形态分类为
    anchor（标题/锚点）/ addresslist（地址列、表格行）/ passing（顺带提及）
  并显式区分"自身台账副本（coverage.tsv 历史快照等）"与"外部文件"——
  前者不是可引用证据（M81 教训：文件存在 != 逐 entry 证据成立）。

纪律：不改任何输入；不判定任何行的 grade；只写本目录。

用法：
  python scan.py                       # 全跑
  python scan.py --stage a             # 只跑阶段 A
  python scan.py --stage b             # 只跑阶段 B（仍会先建索引以填 cand 列）
"""
from __future__ import annotations

import argparse
import collections
import csv
import os
import re
import subprocess
import sys

GLOB_HDR = ["entry", "subsystem", "name", "A1_filename_hit", "A2_path_hit",
            "cand_files(hit_count)", "shared_by_n_rows"]
SAMPLE_HDR = ["entry", "subsystem", "name", "cand_files",
              "content_anchor_form(anchor|addresslist|passing|absent)",
              "verdict(STRONG|WEAK|NONE)", "reason", "ext_hits_nonselfref"]

HEX_STR = re.compile(r"[0-9a-f]{8,}")
# 一行里出现的"独立 8 位十六进制 token"（前后不接 hex 字符）
HEX_TOKEN = re.compile(r"(?<![0-9a-f])[0-9a-f]{8}(?![0-9a-f])")

# 台账/追踪类文件：出现该 entry 属于"自身记录"，不是可引用证据
SELFREF_NAME = {"coverage.tsv", "row_class.tsv", "resolve.tsv", "summary.tsv",
                "coverage_pinned.tsv", "classification_trace.tsv"}


# --------------------------------------------------------------------------- #
# 工具
# --------------------------------------------------------------------------- #
def hex_windows(text):
    """text 里所有落在"长度>=8 的连续 hex 串"内的 8 长度子串集合。

    这给出与"子串包含 8 位 hex"完全等价、但可倒排索引的键集。
    """
    out = set()
    for m in HEX_STR.finditer(text):
        r = m.group(0)
        for i in range(len(r) - 7):
            out.add(r[i:i + 8])
    return out


def file_kind(relpath):
    """台账自指 / 其它。

    台账自指 = 该文件是 coverage / 分类追踪的副本或快照，行在里面出现是**构造使然**，
    不能当证据。实测坑：`coverage.tsv.bak`、`_before_coverage.tsv`、
    `coverage_snapshot_14495.tsv` 都不是 coverage.tsv 这个确切名字，按原名比对会漏。
    """
    base = posix_base(relpath).lower()
    parts = relpath.lower().replace("\\", "/").split("/")
    if "coverage" in base:                       # 覆盖所有 *_coverage.tsv / coverage*.bak
        return "selfref"
    if base in SELFREF_NAME:
        return "selfref"
    if "_hygiene" in parts or any(p.endswith("_before") for p in parts):
        return "selfref"          # M*_before / _hygiene 里的 coverage.tsv 历史快照
    return "external"


def posix_base(p):
    return p.replace("\\", "/").rsplit("/", 1)[-1]


def card_dir(relpath):
    """一级「卡目录」名：next_re_*/<d> 取 d，否则取第一段。"""
    parts = [c for c in relpath.replace("\\", "/").split("/") if c]
    if not parts:
        return "<none>"
    if parts[0].startswith("next_re_") and len(parts) > 1:
        return parts[1]
    return parts[0]


# --------------------------------------------------------------------------- #
# 阶段 A：文件系统索引
# --------------------------------------------------------------------------- #
def build_index(lead_root, exclude_dirs):
    """返回 (base_inv, path_inv, n_files)。倒排：8hex -> [file_idx]"""
    base_inv = collections.defaultdict(list)
    path_inv = collections.defaultdict(list)
    files = []
    excl = {os.path.normcase(os.path.abspath(d)) for d in exclude_dirs}

    for root, dirs, fnames in os.walk(lead_root):
        dirs[:] = [d for d in dirs if d.lower() != ".git"
                   and os.path.normcase(os.path.abspath(os.path.join(root, d))) not in excl]
        for fn in fnames:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, lead_root).replace("\\", "/")
            idx = len(files)
            files.append(rel)
            for w in hex_windows(fn.lower()):
                base_inv[w].append(idx)
            for w in hex_windows(rel.lower()):
                path_inv[w].append(idx)
    return base_inv, path_inv, files


def load_trace_only(resolve_path, want="R_TRACE_ONLY"):
    with open(resolve_path, "r", encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh, delimiter="\t") if r.get("class") == want]
    return rows


# --------------------------------------------------------------------------- #
# 阶段 B：内容级
# --------------------------------------------------------------------------- #
def rg_match(entry, lead_root, exclude_rel):
    """在 lead 全树内容里搜 entry（不区分大小写、字面量）。返回 [(relpath, lineno, text)]"""
    cmd = ["rg", "-n", "-i", "-F", "--no-messages",
           "--hidden", "--no-ignore", "--no-ignore-vcs",
           "--max-count", "8",
           "--glob", "!.git/**", "--glob", "!*.exe", "--glob", "!*.dll"]
    for e in exclude_rel:
        cmd += ["--glob", "!" + e + "/**"]
    cmd += [entry, "."]
    try:
        p = subprocess.run(cmd, cwd=lead_root, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=600)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"[warn] rg 失败 {entry}: {exc}", file=sys.stderr)
        return None
    if p.returncode == 2:
        # 实测：rc=2 只来自 next_re_*_r14/S16_N1/work/venv/bin/python* 三个断链
        # （os error 1920，Windows 无法访问 Linux 符号链接），stdout 完整可用。
        # 若 stdout 也为空则视为真失败。
        if not p.stdout.strip():
            print(f"[warn] rg rc=2 且无输出，{entry} 未测定", file=sys.stderr)
            return None
    out = []
    for line in p.stdout.splitlines():
        m = re.match(r"^(.+?):(\d+):(.*)$", line)
        if not m:
            continue
        rel = m.group(1)
        if rel.startswith(".\\") or rel.startswith("./"):
            rel = rel[2:]
        rel = rel.replace("\\", "/")
        out.append((rel, int(m.group(2)), m.group(3)))
    return out


def classify_line(entry, relpath, lineno, line):
    """单行形态：anchor / addresslist / passing

    anchor = 该行把 entry 当**主体命名**（标题 / 锚点 / 文件头部 meta 行 / 专属反汇编起点），
             而不是把它当成地址表里的一个值或正文里的顺带一提。
    """
    low = line.lower()
    s = line.lstrip()
    ext = os.path.splitext(relpath)[1].lower()
    dedicated = entry in posix_base(relpath).lower()

    # 1) markdown ATX 标题行（只在 md/markdown 里认；代码文件的 `# 注释` 不算标题）
    if ext in (".md", ".markdown") and re.match(r"^#{1,6}\s", s) and entry in low:
        return "anchor"
    # 2) 锚点片段在行首：`#004DF320`
    if s.startswith("#" + entry):
        return "anchor"
    # 3) 文件头部 meta 行把 entry 命名为主体：`# entry 007DCFC4 …` / `; start=00752480 …`
    #    注意只认 entry/start/addr：`fn=<hex>` 是"被调者"标注（调用点记录），
    #    出现在地址表行里，不是以它为主体 —— 实测 EVIDENCE_slot8_sites.txt:323 就是这形态。
    pos = low.find(entry)
    if 0 <= lineno <= 10 and pos > 0:
        if re.search(r"(entry|start|addr)\s*[=:]?\s*$", low[:pos]):
            return "anchor"
    # 4) 行首字段就是该地址
    first = re.split(r"[\s,;|]+", line.strip())[0].lower() if line.strip() else ""
    if first == entry or first.endswith(entry):
        # 专属文件（文件名含该 entry）前 10 行里的首地址 = 以它为起点的反汇编 ⇒ 主体
        return "anchor" if (dedicated and lineno <= 10) else "addresslist"
    # 5) 一行里 >=3 个不同地址 token ⇒ 地址表/调用图/引用表的一行
    if len(set(HEX_TOKEN.findall(low))) >= 3:
        return "addresslist"
    # 6) 其余：正文顺带提及
    return "passing"


FORM_RANK = {"absent": 0, "passing": 1, "addresslist": 2, "anchor": 3}


def rg_anchor(entry, lead_root, exclude_rel):
    """专找"以该 entry 为标题行"的行（不受 --max-count 截断影响）。

    主搜索用 --max-count 8 限制每文件行数；如果某个大 .md 的前 8 次命中都在
    地址表里，靠后的 `## 00XXXXXX` 章节标题会被截断 —— 那正是 STRONG 的信号。
    这里用标题正则单独扫一遍补上这个洞。
    """
    pat = r"^[ \t]{0,3}#{1,6}[ \t].*" + entry
    cmd = ["rg", "-n", "-i", "--no-messages", "--hidden",
           "--no-ignore", "--no-ignore-vcs",
           "--glob", "!.git/**", "--glob", "!*.exe", "--glob", "!*.dll"]
    for e in exclude_rel:
        cmd += ["--glob", "!" + e + "/**"]
    cmd += [pat, "."]
    try:
        p = subprocess.run(cmd, cwd=lead_root, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=600)
    except (OSError, subprocess.SubprocessError):
        return []
    TEXT_EXT = (".md", ".markdown", ".txt", ".rst")
    out = []
    for line in p.stdout.splitlines():
        m = re.match(r"^(.+?):(\d+):(.*)$", line)
        if not m:
            continue
        rel = m.group(1)
        if rel.startswith(".\\") or rel.startswith("./"):
            rel = rel[2:]
        rel = rel.replace("\\", "/")
        if os.path.splitext(rel)[1].lower() not in TEXT_EXT:
            continue                      # 代码文件里的 `# 注释` 不算标题
        out.append((rel, int(m.group(2)), m.group(3)))
    return out


def analyse_sample(row, lead_root, exclude_rel, cand_files):
    entry = row["entry"].lower()
    hits = rg_match(entry, lead_root, exclude_rel)
    if hits is None:
        return dict(form="absent", verdict="NONE", ext=0,
                    reason="rg 执行失败，本行未测定（不可当作 NONE）", pairs=[], files=0)

    # 合并标题专用搜索的结果（去重）
    seen = {(h[0], h[1]) for h in hits}
    for h in rg_anchor(entry, lead_root, exclude_rel):
        if (h[0], h[1]) not in seen:
            hits.append(h)
            seen.add((h[0], h[1]))

    ext = [h for h in hits if file_kind(h[0]) == "external"]
    sel = [h for h in hits if file_kind(h[0]) == "selfref"]
    pairs = [(h[0], classify_line(entry, h[0], h[1], h[2])) for h in ext]
    best = "absent"
    for _, f in pairs:
        if FORM_RANK[f] > FORM_RANK[best]:
            best = f
    if best == "anchor":
        verdict = "STRONG"
    elif best in ("addresslist", "passing"):
        verdict = "WEAK"
    else:
        verdict = "NONE"
    return dict(form=best, verdict=verdict, ext=len(ext), pairs=pairs,
                files=len({h[0] for h in ext}), self_n=len(sel),
                self_files=sorted({h[0] for h in sel}))


# --------------------------------------------------------------------------- #
# 统计小工具
# --------------------------------------------------------------------------- #
def wilson(k, n, z=1.96):
    """比例的 Wilson 95% 区间。"""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, (c - h) * n), p * n, min(float(n), (c + h) * n))


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    r14 = os.path.dirname(here)
    lead = os.path.dirname(r14)
    ap = argparse.ArgumentParser(description="802 行 trace-only 逐 entry 证据可回收性度量")
    ap.add_argument("--repo", default=os.path.dirname(lead))
    ap.add_argument("--lead", default=lead, help="索引与内容搜索的根（默认 lead/）")
    ap.add_argument("--resolve", default=os.path.join(
        r14, "R16_BASE", "evid", "resolve.tsv"))
    ap.add_argument("--out", default=here)
    ap.add_argument("--stage", default="all", choices=["all", "a", "b"])
    ap.add_argument("--sample-n", type=int, default=16,
                    help="中间等距抽样点数（卡面固定 16 ⇒ 共 18 行）")
    args = ap.parse_args(argv)

    rows = load_trace_only(args.resolve)
    rows.sort(key=lambda r: r["entry"])
    n = len(rows)
    print(f"[in ] resolve : {args.resolve}")
    print(f"[in ] lead    : {args.lead}")
    print(f"[data] R_TRACE_ONLY 行数 = {n}  (卡面期望 802)")
    if n != 802:
        print(f"[WARN] 与卡面 802 不一致，差 {n - 802:+d}")
    dup = [e for e, c in collections.Counter(r["entry"] for r in rows).items() if c > 1]
    print(f"[data] entry 唯一性: {n - len(dup)} 唯一 / 重复 {len(dup)}")

    base_inv, path_inv, files = build_index(
        args.lead, exclude_dirs=[args.out])
    print(f"[data] 索引文件数 = {len(files)}")

    # ---------------- 阶段 A ---------------- #
    file_rows = collections.Counter()          # 命中文件 -> 覆盖多少行
    recs = []
    for r in rows:
        e = r["entry"].lower()
        a1 = sorted({files[i] for i in base_inv.get(e, [])})
        a2 = sorted({files[i] for i in path_inv.get(e, [])})
        a1s, a2s = set(a1), set(a2)
        cands = a1 + ["dir:" + p for p in a2 if p not in a1s]
        for c in cands:
            file_rows[c] += 1
        recs.append(dict(row=r, a1=a1, a2=a2, cands=cands))

    for d in recs:
        d["shared"] = max((file_rows[c] for c in d["cands"]), default=0)

    a1_rows = [d for d in recs if d["a1"]]
    a2_rows = [d for d in recs if d["a2"]]
    a1_files = {p for d in recs for p in d["a1"]}
    a2_files = {p for d in recs for p in d["a2"]}

    out_a = os.path.join(args.out, "traceonly802.tsv")
    with open(out_a, "w", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(GLOB_HDR) + "\n")
        for d in recs:
            fh.write("\t".join([
                d["row"]["entry"], d["row"]["subsystem"], d["row"]["name"],
                "Y" if d["a1"] else "N",
                "Y" if d["a2"] else "N",
                ";".join(d["cands"]),
                str(d["shared"]),
            ]) + "\n")
    print(f"[out] {out_a} : {len(recs)} 行")

    by_card_a1 = collections.Counter()
    by_card_a2 = collections.Counter()
    for d in recs:
        if d["a1"]:
            by_card_a1[card_dir(d["a1"][0])] += 1
        if d["a2"]:
            by_card_a2[card_dir(d["a2"][0])] += 1

    print(f"[A] A1 文件名命中行 = {len(a1_rows)} ({100.0*len(a1_rows)/n:.2f}%)"
          f"  涉及文件 {len(a1_files)}")
    print(f"[A] A2 路径命中行   = {len(a2_rows)} ({100.0*len(a2_rows)/n:.2f}%)"
          f"  涉及文件 {len(a2_files)}")
    top = [(c, file_rows[c], k) for c, k in
           file_rows.most_common(10)]
    print("[A] Top10 共享文件:")
    for c, cnt, _k in top:
        print(f"      {cnt:4d} 行  {c}")

    # ---------------- 阶段 B ---------------- #
    idx = [0, n - 1] + list(range(n // 16, n - 1, n // 16))
    # 卡面固定：50,100,...,800（n=802 时恰为该序列）
    idx = [0, n - 1] + [50 * k for k in range(1, args.sample_n + 1)]
    idx = [i for i in dict.fromkeys(idx) if 0 <= i < n]
    sample = [recs[i] for i in idx]
    print(f"[B] 抽样行数 = {len(sample)} (索引 {','.join(str(i) for i in idx)})")
    if len(sample) > 18:
        sys.exit("[FATAL] 抽样超过 18 行，违反卡面硬边界")

    exclude_rel = [os.path.relpath(args.out, args.lead).replace("\\", "/")]
    srows = []
    sample_file_share = collections.Counter()   # 仅 18 行样本内：文件 -> 命中它的抽样行数
    for d in sample:
        r = d["row"]
        a = analyse_sample(r, args.lead, exclude_rel, d["cands"])
        for p in {p for p, _ in a["pairs"]}:
            sample_file_share[p] += 1
        a1set = set(d["a1"])
        cand_show = ";".join(d["cands"][:6]) + (";…" if len(d["cands"]) > 6 else "")
        shown_files = "; ".join(sorted({p for p, _ in a["pairs"]})[:3]) or "无"
        if a["verdict"] == "STRONG":
            anchors = [p for p, f in a["pairs"] if f == "anchor"]
            in_a1 = [p for p in anchors if p in a1set]
            reason = (f"锚点文件 {in_a1[0] if in_a1 else anchors[0]} "
                      f"{'(A1 文件名命中，属专属文件)' if in_a1 else '(A1 未命中，靠内容标题锚定)'} "
                      f"以其为主体锚定；内容命中 {a['ext']} 处/在外 {a['files']} 文件，"
                      f"其中锚点形态 {len(anchors)} 处")
        elif a["verdict"] == "WEAK":
            forms = "/".join(sorted({f for _, f in a["pairs"]}))
            lead_phrase = ("阶段 A 无文件名命中" if not d["a1"] else "有文件名命中但内容不作为主体锚定")
            reason = (f"{lead_phrase}；内容命中 {a['ext']} 处/在外 {a['files']} 文件，"
                      f"最强形态 {forms}（例：{shown_files}），无任何文件专讲该 entry")
        else:
            if a["self_n"]:
                reason = (f"lead 全树无外部命中；{a['self_n']} 处全在自身台账/追踪副本"
                          f"（{'; '.join(a['self_files'][:3])}）⇒ 自指，不可引用")
            else:
                reason = ("lead 全树内容搜索 0 命中，且阶段 A 无候选文件"
                          if a["ext"] == 0 else
                          f"内容命中 {a['ext']} 处但不构成任何可引用形态")
        srows.append([r["entry"], r["subsystem"], r["name"],
                      cand_show or "<none>", a["form"], a["verdict"],
                      reason, str(a["ext"])])

    out_b = os.path.join(args.out, "sample18.tsv")
    with open(out_b, "w", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(SAMPLE_HDR) + "\n")
        for s in srows:
            fh.write("\t".join(s) + "\n")
    print(f"[out] {out_b} : {len(srows)} 行")

    vc = collections.Counter(s[5] for s in srows)
    print(f"[B] STRONG={vc.get('STRONG',0)} WEAK={vc.get('WEAK',0)} NONE={vc.get('NONE',0)}")

    # 交叉表：verdict × 阶段 A 是否有文件名命中（STRONG 是否只在 A1 命中行里出现）
    cross = collections.Counter()
    for d, s in zip(sample, srows):
        cross[("A1" if d["a1"] else "noA1", s[5])] += 1
    print("[B] verdict × A1: " + ", ".join(f"{k[0]}/{k[1]}={v}" for k, v in sorted(cross.items())))
    print("[B] 内容级共享 Top10（仅 18 行样本内）:")
    for p, c in sample_file_share.most_common(10):
        print(f"      {c:3d}/18 行  {p}")

    # 外推（Wilson 95%）
    lo_s, _, hi_s = wilson(vc.get("STRONG", 0), len(srows))
    lo_w, _, hi_w = wilson(vc.get("STRONG", 0) + vc.get("WEAK", 0), len(srows))
    scale = n / len(srows)
    print(f"[B] STRONG 外推 802: {lo_s*scale:.1f} – {hi_s*scale:.1f} 行")
    print(f"[B] STRONG+WEAK 外推 802: {lo_w*scale:.1f} – {hi_w*scale:.1f} 行")

    # 机器可读的统计块，供 REPORT 引用
    stats = {
        "n_rows": n, "n_files_indexed": len(files),
        "a1_rows": len(a1_rows), "a2_rows": len(a2_rows),
        "a1_files": len(a1_files), "a2_files": len(a2_files),
        "by_card_a1": dict(by_card_a1.most_common()),
        "by_card_a2": dict(by_card_a2.most_common()),
        "top_files": [{"file": c, "rows": cnt, "kind": file_kind(c)} for c, cnt, _ in top],
        "sample_idx": idx,
        "verdicts": dict(vc),
        "verdict_x_a1": {f"{k[0]}/{k[1]}": v for k, v in cross.items()},
        "sample_file_share_top": [{"file": p, "rows": c}
                                  for p, c in sample_file_share.most_common(15)],
        "extrap_strong": [lo_s * scale, hi_s * scale],
        "extrap_strong_weak": [lo_w * scale, hi_w * scale],
        "no_a1_rows": n - len(a1_rows),
    }
    with open(os.path.join(args.out, "stats.json"), "w", encoding="utf-8") as fh:
        import json
        json.dump(stats, fh, ensure_ascii=False, indent=1)
    return stats


if __name__ == "__main__":
    main()
