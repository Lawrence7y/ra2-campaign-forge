#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""work.py — R17-R41-RECOMPUTE 独立复算（第二源）。

卡号：R17-R41-RECOMPUTE
写域：lead/next_re_20261117_r14/R17_R41_RECOMPUTE/   （只写本目录）
读（只读）：COVERAGE/coverage.tsv；../next_re_20261112_r10/W130_atlas/function_atlas.tsv
不写 coverage.tsv；不执行 resolve.py main()；不跑 strict_panel.py（另由其自身运行比对）。

★口径全部写在本脚本里，散文不算实现。逐项口径：

P0 文件形态
   - 表头行：逗号分隔（header = line0.split(","), 各字段 strip）
   - 数据行：TAB 分隔（fields = line.split("\t")）；字段数 != 8 的行计入 bad，不静默兜底
   - 行尾只去 "\r"（文件实为 LF，CR 计数须为 0）
   - entry 归一：strip + upper；若以 "0X" 开头则去前缀；再 %08X（16 位入口能解析则保留）
P1 grade 三档：第 5 列（index 4）strip 后字面等于 "[已证]" / "[静态推断]" / "[未证]"
P2 atlas 内/外：coverage entry（P0 归一）∈ atlas entry 集合（atlas entry 归一同 P0，atlas 首行为表头跳过）
P3 ④ 三口径 —— 一律只看第 4 列（index 3, one_line_semantics），且只统计 grade=="[已证]" 行：
   A   = 第 4 列含字符 "\u2463"
   B   = 第 4 列含全串 "\u2463 活表槽位见证"（④ + 一个半角空格 + 活表槽位见证）
   W   = B 或 第 4 列含全串 "\u2463 direct call"（报告两者交集，应 0）
   N   = 第 4 列不含字符 "\u2463"
   Loose = 第 4 列含正则 r"direct call"（不限全串、不限 ④ 前缀）—— 只作“会多计多少”的对照
P4 strict：atlas 内 ∧ grade=="[已证]" ∧ 第 4 列不含子串 "[未证]"
P5 §12.6：第 4 列含子串 "§12.6"；§12.4：第 4 列含子串 "§12.4"；
   CLSID None：任一行任一字段含子串 "CLSID None"
P6 第 6 列含 ④：第 6 列（index 5, evidence_path）含字符 "\u2463" 的行数（全表，不限 grade）
   另报：非第 4 列任一字段含 ④ 的行数，及 grade=="[已证]" 子集内的同项
P7 R_OK / R_MISSING / R_TRACE_ONLY：按 EVID_RESOLVE/resolve.py 文件头四类定义纯函数重实现：
   对 grade=="[已证]" 行，把第 6 列按 [;,|] 拆段、去空段；
   R_EMPTY = 无段；R_TRACE_ONLY = 所有段都含 "classification_trace"；
   否则逐段：去 "#anchor"（绝对路径的盘符冒号不当锚点），非绝对路径再去尾部 ":行号" 锚点，
   再在 bases=[r14, lead, repo] 下 os.path.join 试 os.path.isfile，任一命中 → R_OK；否则 R_MISSING。
   归类优先级：R_EMPTY > R_TRACE_ONLY > R_OK > R_MISSING。
"""
from __future__ import annotations
import collections, hashlib, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
LEAD = os.path.dirname(R14)
REPO = os.path.dirname(LEAD)

COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
ATLAS = os.path.join(LEAD, "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")

PROVED, INFER, UNPROVED = "[已证]", "[静态推断]", "[未证]"
R4 = "\u2463"
B_S = R4 + " 活表槽位见证"
D_S = R4 + " direct call"
LOOSE_RE = re.compile(r"direct call")
ABS_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\|/)")
LINESPEC_RE = re.compile(r":(?:\d+[0-9A-Za-z\-]*|0x[0-9A-Fa-f\-]+)$")
SPLIT_RE = re.compile(r"[;,|]")


def norm_entry(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e


def load_coverage(path):
    raw = open(path, "rb").read()
    cr = raw.count(b"\r")
    text = raw.decode("utf-8")
    lines = text.split("\n")
    header = [c.strip() for c in lines[0].split(",")]
    rows, bad = [], []
    for lineno, line in enumerate(lines[1:], start=2):
        line = line.rstrip("\r")
        if not line.strip():
            continue
        f = line.split("\t")
        if len(f) != len(header):
            bad.append((lineno, len(f)))
            continue
        rows.append(f)
    return raw, cr, header, rows, bad


def load_atlas(path):
    s = set()
    with open(path, encoding="utf-8-sig") as fh:
        fh.readline()
        for line in fh:
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            s.add(norm_entry(line.split("\t")[0]))
    return s


def strip_anchor(p):
    p = p.split("#", 1)[0].strip()
    if not ABS_RE.match(p):
        p = LINESPEC_RE.sub("", p).strip()
    return p


def classify(ev, bases):
    parts = [x.strip() for x in SPLIT_RE.split(ev.strip()) if x.strip()]
    if not parts:
        return "R_EMPTY"
    if all("classification_trace" in x for x in parts):
        return "R_TRACE_ONLY"
    for x in parts:
        rel = strip_anchor(x)
        if not rel:
            continue
        rel = rel.replace("\\", os.sep).replace("/", os.sep)
        if ABS_RE.match(rel.strip()):
            if os.path.isfile(rel):
                return "R_OK"
            continue
        for _, b in bases:
            if os.path.isfile(os.path.join(b, rel)):
                return "R_OK"
    return "R_MISSING"


def main():
    raw, cr, header, rows, bad = load_coverage(COV)
    atlas = load_atlas(ATLAS)
    R = dict()

    R["cov.bytes"] = len(raw)
    R["cov.sha256"] = hashlib.sha256(raw).hexdigest()
    R["cov.cr_count"] = cr
    R["cov.header_cols"] = len(header)
    R["cov.header"] = ",".join(header)
    R["cov.data_rows"] = len(rows)
    R["cov.col_dist"] = dict(collections.Counter(len(r) for r in rows))
    R["cov.bad_rows"] = len(bad)
    R["atlas.data_rows"] = len(atlas)

    grades = collections.Counter(r[4].strip() for r in rows)
    R["grade.proved"] = grades[PROVED]
    R["grade.infer"] = grades[INFER]
    R["grade.unproved"] = grades[UNPROVED]
    R["grade.sum"] = sum(grades.values())
    R["grade.other"] = {k: v for k, v in grades.items() if k not in (PROVED, INFER, UNPROVED)}

    # 归一：整数与"去 0x 再 upper"两条路都算一遍，看是否同值
    def in_atlas_raw(e):
        return e.strip().upper() in atlas
    proved = [r for r in rows if r[4].strip() == PROVED]
    pin_n = [r for r in proved if norm_entry(r[0]) in atlas]
    pin_raw = [r for r in proved if r[0].strip().upper() in atlas]
    R["atlas.proved_in_norm"] = len(pin_n)
    R["atlas.proved_out_norm"] = len(proved) - len(pin_n)
    R["atlas.proved_in_rawupper"] = len(pin_raw)
    R["atlas.proved_out_entries"] = sorted(r[0] for r in proved if norm_entry(r[0]) not in atlas)
    R["atlas.rows_in_norm"] = sum(1 for r in rows if norm_entry(r[0]) in atlas)
    R["atlas.rows_in_rawupper"] = sum(1 for r in rows if r[0].strip().upper() in atlas)

    # ④ 三口径（限第 4 列，限 [已证]）
    A = [r for r in proved if R4 in r[3]]
    B = [r for r in proved if B_S in r[3]]
    Dc = [r for r in proved if D_S in r[3]]
    W = [r for r in proved if (B_S in r[3]) or (D_S in r[3])]
    N4 = [r for r in proved if R4 not in r[3]]
    Loose = [r for r in proved if LOOSE_RE.search(r[3])]
    Loose_noB = [r for r in proved if LOOSE_RE.search(r[3]) and B_S not in r[3]]
    R["ring4.A"] = len(A)
    R["ring4.B"] = len(B)
    R["ring4.D_only"] = len(Dc)
    R["ring4.W"] = len(W)
    R["ring4.none"] = len(N4)
    R["ring4.B_and_D"] = len([r for r in proved if B_S in r[3] and D_S in r[3]])
    R["ring4.A_not_B"] = len([r for r in proved if R4 in r[3] and B_S not in r[3]])
    R["ring4.A_minus_B"] = len(A) - len(B)
    R["ring4.loose_direct_call"] = len(Loose)
    R["ring4.loose_extra_vs_W"] = len(Loose_noB)   # 相对宽口径 W 多计入的行数
    R["ring4.loose_extra_vs_B"] = len([r for r in proved if LOOSE_RE.search(r[3]) and B_S not in r[3]])
    R["ring4.proved_denom"] = len(proved)

    # strict
    strict = [r for r in pin_n if UNPROVED not in r[3]]
    R["strict.total"] = len(strict)
    R["strict.pct_of_proved"] = "%.2f%%" % (100.0 * len(strict) / len(proved))

    # §12.6 / §12.4 / CLSID None
    R["s126.col4"] = sum(1 for r in rows if "§12.6" in r[3])
    R["s126.col4_proved"] = sum(1 for r in proved if "§12.6" in r[3])
    R["s124.col4"] = sum(1 for r in rows if "§12.4" in r[3])
    R["clsid_none.anyfield"] = sum(1 for r in rows if any("CLSID None" in x for x in r))

    # 第 6 列含 ④
    R["ring4.col6_allrows"] = sum(1 for r in rows if R4 in r[5])
    R["ring4.col6_proved"] = sum(1 for r in proved if R4 in r[5])
    R["ring4.non_col4_allrows"] = sum(1 for r in rows if any(R4 in x for i, x in enumerate(r) if i != 3))
    R["ring4.non_col4_proved"] = sum(1 for r in proved if any(R4 in x for i, x in enumerate(r) if i != 3))
    R["ring4.whole_row_loose_proved"] = sum(1 for r in proved if any(R4 in x for x in r))

    # R_OK / R_TRACE_ONLY 等
    bases = [(n, p) for n, p in (("r14", R14), ("lead", LEAD), ("repo", REPO)) if os.path.isdir(p)]
    R["evid.bases"] = [n for n, _ in bases]
    klass = collections.Counter(classify(r[5], bases) for r in proved)
    R["evid.R_OK"] = klass.get("R_OK", 0)
    R["evid.R_MISSING"] = klass.get("R_MISSING", 0)
    R["evid.R_TRACE_ONLY"] = klass.get("R_TRACE_ONLY", 0)
    R["evid.R_EMPTY"] = klass.get("R_EMPTY", 0)
    R["evid.R_OK_pct"] = "%.2f%%" % (100.0 * klass.get("R_OK", 0) / len(proved))

    # 交叉：R_TRACE_ONLY 与「第 6 列全段含 classification_trace」同源核验
    R["evid.trace_only_eq_ct_only"] = (klass.get("R_TRACE_ONLY", 0) ==
        sum(1 for r in proved if [x.strip() for x in SPLIT_RE.split(r[5].strip()) if x.strip()]
            and all("classification_trace" in x for x in SPLIT_RE.split(r[5]))))

    # 行尾/编码卫生
    R["hyg.utf8_bom"] = raw.startswith(b"\xef\xbb\xbf")
    R["hyg.trailing_newline"] = raw.endswith(b"\n")


    # ---- 宽松正则对照的三种定义（口径写死在此，报告逐条引用）----
    def loose_loose(pat):
        return sum(1 for r in proved if re.search(pat, r[3]))
    R["ring4.loose.a_bare_word"] = loose_loose(r"\bdirect call\b")
    R["ring4.loose.b_substring"] = loose_loose(r"direct call")
    R["ring4.loose.c_no_ring4_prefix"] = sum(1 for r in proved
        if "direct call" in r[3] and D_S not in r[3])
    R["ring4.loose.d_nonsemantic_hits"] = sorted(
        r[0] for r in proved if "direct call" in r[3]
        and D_S not in r[3] and B_S not in r[3]
        and any(t in r[3] for t in ("direct callers", "无 direct caller", "No direct caller")))
    R["ring4.loose.e_substantive_extra"] = sum(1 for r in proved
        if "direct call" in r[3] and D_S not in r[3] and B_S not in r[3]
        and not any(t in r[3] for t in ("direct callers", "无 direct caller", "No direct caller")))
    # 注：numbers.tsv 是本卡人工定稿的交付表（含 before/after 证据行），本脚本只写 crosscheck.json，
    # 避免复跑覆盖交付物。
    with open(os.path.join(HERE, "crosscheck.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1, sort_keys=True)

    print(json.dumps(R, ensure_ascii=False, indent=1))


main()
