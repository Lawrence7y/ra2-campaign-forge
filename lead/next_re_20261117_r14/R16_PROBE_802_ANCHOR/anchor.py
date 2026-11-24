#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anchor.py — R16-PROBE-802-ANCHOR 度量器（只读输入 + 只写本目录）

问题：上一卡（R16-SCAN-EVID-802）测出 802 行 `R_TRACE_ONLY` 里有 127 行
「文件名命中」（A1），但它把内容级验证限死在 18 行，留下了「127 行全量内容
验证没有完成」的尾巴。本卡做掉这个尾巴：

  阶段 1  复现 A1 = 127 行集合（自己的独立实现，对账上一卡）
  阶段 2  对 127 行的每个候选文件 + 全树内容命中做**逐行形态判定**
  阶段 3  交叉核对上一卡的 18 行抽样分布（同口径应给出 STRONG3/WEAK15/NONE0）
  阶段 4  机器挑出 ≤18 行供人工目视（人工判读由人或本卡作者另行完成）

判定口径（四桶，写死在 classify()/file_struct() 里，可复核）：

  STRONG  内容里存在「明确以该 entry 为对象」的锚点：
            A1 行首锚 `#<entry>` / `# <entry> ...`
            A2 md ATX 标题 `## <entry> ...`（仅 .md/.markdown/.rst 的标题行）
            A3 文件头部（前 12 个非空行内）的字段位 meta：
               `entry=<e>` `entry : <e>` `start=<e>` `target=<e>` `function 0x<e>`
               `@0x<e>` 等；**代码文件（.py/.c/.cpp/.js/.ps1/...）不适用 A3**
            A4 该 entry 是**该段反汇编的起点**：命中行是反汇编记录行且其地址
               等于该文件反汇编记录行里的最小地址
            A5 函数体定义命名它：`FUN_<e>(` / `FUN_0x<e>(`
  MEDIUM  结构化表/结构体里**作为主体项（一行记录）**出现，但没有专门章节：
            M1 文件头有声明式表头，entry 位于**首列（key 列）**，且该 entry 在
               整文件里只出现这**一条记录**，且该行除地址外还带至少一个非地址
               属性字段
            M2 JSON 里 `<e>` 作为对象 key 且其 value 是有命名属性的对象
  WEAK    只在地址列表 / 顺带提及 / 工具参数位出现：
            W1 代码文件里的**工具参数位**：`(0x<e>` / `, 0x<e>` / `sys.argv` /
               `subprocess` 等调用参数形态 —— **上一卡的反例就是这个**
            W2 指令流 / 地址表 / 调用图 / 引用表里的一个值（含 key 列但一行里
               重复出现多次的流水表、JSON 里 value 纯为地址数组的 key）
            W3 散文顺带提及、日志 INFO 行
  NONE    命中文件里找不到该 entry 的可用内容（应有但未见）

行级 form = 该行全部外部命中的最大形态（STRONG > MEDIUM > WEAK > NONE）；
台账自指文件（coverage* 快照 / resolve / classification_trace / 本卡与上一卡的
产物）先剔除，否则「行是从台账抄的」会被误读成证据（上一卡 §2.5 的坑）。

纪律：不改任何输入；不判 grade；不写 ④；只写本目录。

用法：
  python anchor.py            # 全跑（需要 rg）
  python anchor.py --no-content   # 只复现 A1（不碰内容搜索）
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import re
import subprocess
import sys

HDR127 = ["entry", "subsystem", "name", "cand_files",
          "form(STRONG|MEDIUM|WEAK|NONE)", "hits_in_file",
          "is_entry_dedicated", "note"]
HDR18 = ["entry", "subsystem", "name", "form(mine)", "anchor_file",
         "hits_in_file", "ctx_20_40", "verdict(AGREE|DISAGREE)", "reason"]

HEX_TOKEN = re.compile(r"(?<![0-9a-f])[0-9a-f]{8}(?![0-9a-f])")
HEX_STR = re.compile(r"[0-9a-f]{8,}")

CODE_EXT = {".py", ".c", ".cpp", ".cc", ".h", ".js", ".ts", ".ps1", ".sh",
            ".bat", ".cmd", ".java", ".go", ".rs", ".pl", ".rb"}
MD_EXT = {".md", ".markdown", ".rst"}
TEXT_EXT = MD_EXT | {".txt", ""}

# 台账/追踪/本卡产物：出现该 entry 属"自身记录"，不是可引用证据
SELFREF_NAME = {"coverage.tsv", "row_class.tsv", "resolve.tsv", "summary.tsv",
                "coverage_pinned.tsv", "classification_trace.tsv",
                "traceonly802.tsv", "anchor127.tsv", "sample18.tsv",
                "stats.json"}
SELFREF_DIRPART = ("_hygiene", "r16_scan802", "r16_probe_802_anchor")

# 表头里可当作"entry 就是本行主体"的 key 列名
KEY_COLS = {"entry", "addr", "address", "va", "vaddr", "rva", "ea",
            "func", "function", "fname", "fn", "funcva", "entryva",
            "start", "entry_addr", "funcaddr", "func_addr"}
# 反汇编记录行（地址在行首）
DISASM_PATS = [
    re.compile(r"^([0-9a-f]{8})[:!]?\s{2,}([0-9a-f]{2})\b"),       # 0045A560  53  push
    re.compile(r"^([0-9a-f]{8})\s*\(?\+?0x[0-9a-f]{1,4}\)?"),        # 0053AF40 +0x0000
    re.compile(r"^([0-9a-f]{8}):\s"),                                 # 0048A4F0: 53
    re.compile(r"^([0-9a-f]{8}) {2,}\S"),                             # 004C98B0  sub ...
]


# --------------------------------------------------------------------------- #
# 工具
# --------------------------------------------------------------------------- #
def posix_base(p):
    return p.replace("\\", "/").rsplit("/", 1)[-1]


def rel_join(root, rel):
    return os.path.join(root, rel.replace("/", os.sep))


def hex_windows(text):
    """长度>=8 的连续 hex 串里所有 8 长度子串（= '文件名含该 8 位 hex' 的等价倒排键）。"""
    out = set()
    for m in HEX_STR.finditer(text):
        r = m.group(0)
        for i in range(len(r) - 7):
            out.add(r[i:i + 8])
    return out


def file_kind(relpath):
    """selfref（台账自指 / 本卡产物） vs external。"""
    base = posix_base(relpath).lower()
    parts = relpath.lower().replace("\\", "/").split("/")
    if "coverage" in base:
        return "selfref"
    if base in SELFREF_NAME:
        return "selfref"
    if any(p in SELFREF_DIRPART for p in parts[:-1]):
        return "selfref"
    if any(p.endswith("_before") for p in parts):
        return "selfref"
    return "external"


def is_code(relpath):
    return os.path.splitext(relpath)[1].lower() in CODE_EXT


def is_texty(relpath):
    return os.path.splitext(relpath)[1].lower() in TEXT_EXT


def is_md(relpath):
    return os.path.splitext(relpath)[1].lower() in MD_EXT


# --------------------------------------------------------------------------- #
# 阶段 1：文件名索引（复现 A1）
# --------------------------------------------------------------------------- #
def build_name_index(lead_root, exclude_dirs):
    inv = collections.defaultdict(set)
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
                inv[w].add(idx)
    return inv, files


def load_rows(resolve_path, want="R_TRACE_ONLY"):
    with open(resolve_path, "r", encoding="utf-8", newline="") as fh:
        return [r for r in csv.DictReader(fh, delimiter="\t") if r.get("class") == want]


# --------------------------------------------------------------------------- #
# 阶段 2：单文件结构（供逐行放大积判定）
# --------------------------------------------------------------------------- #
HEAD_BYTES = 512 * 1024          # 结构分析只看文件头部（反汇编按地址升序，min 在头）
BIG_NOSTRUCT = 20 * 1024 * 1024  # 超过则不建结构，命中一律按 WEAK 处理


class FStruct:
    __slots__ = ("rel", "size", "lines", "head_n", "code", "has_header",
                 "key_col", "ncols", "disasm_min", "disasm_first_line",
                 "disasm_linenos", "head_meta", "meta_all", "hash_first",
                 "hash_all", "md_all", "funcdef", "funcdef_first_line",
                 "tokens", "truncated", "bigfile", "n802")

    def __init__(self, rel):
        self.rel = rel
        self.size = -1
        self.lines = []
        self.head_n = 12
        self.code = is_code(rel)
        self.has_header = False
        self.key_col = None
        self.ncols = 0
        self.disasm_min = None
        self.disasm_first_line = None
        self.disasm_linenos = {}
        self.head_meta = set()
        self.meta_all = set()
        self.hash_first = set()
        self.hash_all = set()
        self.md_all = set()
        self.funcdef = set()
        self.funcdef_first_line = None
        self.tokens = collections.Counter()
        self.truncated = False
        self.bigfile = False
        self.n802 = set()          # 该文件里出现的、属于 802 集合的所有 entry


META_FIELD = re.compile(
    r"(?<![0-9a-z_])(entry|start|target|addr|address|callee|fn|func|function|"
    r"entryva|funcva)\s*[=:]?\s*(?:0x)?([0-9a-f]{8})(?![0-9a-f])")
META_AT = re.compile(r"@(?:0x)?([0-9a-f]{8})(?![0-9a-f])")
FUNCDEF = re.compile(r"(?<![0-9a-z_])(?:fun_|sub_|fn_)(?:0x)?([0-9a-f]{8})(?![0-9a-f])")
# 函数体定义行（行内不能是 `;`/括号开头的表格或表达式；注意：作用对象是**小写行**）
FUNCDEF_LINE = re.compile(r"^[^;()]*\b(?:fun_|sub_|fn_)(?:0x)?")


def build_struct(lead_root, rel, want_set):
    st = FStruct(rel)
    full = rel_join(lead_root, rel)
    try:
        st.size = os.path.getsize(full)
    except OSError:
        st.size = -1
        return st
    if st.size > BIG_NOSTRUCT:
        st.bigfile = True
        return st
    try:
        with open(full, "rb") as fh:
            raw = fh.read(HEAD_BYTES)
            st.truncated = st.size > HEAD_BYTES
    except OSError:
        return st
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    st.lines = lines
    st.tokens = collections.Counter(HEX_TOKEN.findall(text.lower()))
    st.n802 = {t for t in st.tokens if t in want_set}

    # 表头：前 3 个非空行里的第一个，用 tab / | / ; 分隔，字段是纯标识符
    nonempty = [(i + 1, l) for i, l in enumerate(lines[:30]) if l.strip()]
    if nonempty:
        for i, l in nonempty[:3]:
            fields = [f.strip().strip('"').lower()
                      for f in re.split(r"[\t|;]", l) if f.strip()]
            if len(fields) >= 2 and all(re.fullmatch(r"[a-z_][a-z0-9_ ]*", f) for f in fields):
                st.has_header = True
                st.ncols = len(fields)
                for k, f in enumerate(fields):
                    if f in KEY_COLS:
                        st.key_col = k
                        break
                if st.key_col is None:
                    st.key_col = 0
                break

    # 反汇编记录行 + 全文件的主体位置扫描（meta 字段 / 行首锚 / md 标题 / 函数定义名）
    #    head_meta 只取前 12 个非空行（供 A3 的"是否多目标列表"判断）；
    #    meta_all/hash_all/md_all 扫全文件（供"该文件是否被多 entry 共享"判断）。
    head_linenos = {ln for ln, _l in nonempty[:st.head_n]}
    for i, l in enumerate(lines):
        low = l.lower()
        for pat in DISASM_PATS:
            m = pat.match(low)
            if m:
                a = int(m.group(1), 16)
                st.disasm_linenos[i + 1] = a
                if st.disasm_min is None or a < st.disasm_min:
                    st.disasm_min = a
                    st.disasm_first_line = i + 1
                break
        for m in META_FIELD.finditer(low):
            st.meta_all.add(m.group(2))
            if (i + 1) in head_linenos:
                st.head_meta.add(m.group(2))
        for m in META_AT.finditer(low):
            st.meta_all.add(m.group(1))
            if (i + 1) in head_linenos:
                st.head_meta.add(m.group(1))
        m = re.match(r"^\s*#\s*(?:0x)?([0-9a-f]{8})(?![0-9a-f])", low)
        if m:
            st.hash_all.add(m.group(1))
            if (i + 1) in head_linenos:
                st.hash_first.add(m.group(1))
        if is_md(rel) and re.match(r"^\s{0,3}#{1,6}\s", low):
            for t in HEX_TOKEN.findall(low):
                st.md_all.add(t)
        m = FUNCDEF.search(low)
        if m and re.match(FUNCDEF_LINE.pattern + m.group(1) + r"\s*\(", low):
            st.funcdef.add(m.group(1))
            if st.funcdef_first_line is None:
                st.funcdef_first_line = i + 1     # 该文件第一个函数体定义所在行
    return st


# --------------------------------------------------------------------------- #
# 判定：单命中形态
# --------------------------------------------------------------------------- #
RANK = {"NONE": 0, "WEAK": 1, "MEDIUM": 2, "STRONG": 3}


TRUNC_MARK = "[... omitted end of long line]"


def classify(entry, st, lineno, line):
    """返回 (form, why)。form ∈ STRONG/MEDIUM/WEAK。

    所有锚点判据都是**行本地**的（只读这一行 + 该文件的 disasm_min），
    避免"文件头提过该 entry"就把它后面任何地址表行判成锚点。
    """
    e = entry.lower()
    low = line.lower()
    if st is not None and st.bigfile:
        return "WEAK", "W2 大文件（>20MB）未建结构，命中按地址表计"
    if low.rstrip().endswith(TRUNC_MARK):
        return "WEAK", "W2 超长行被 rg 截断（地址字典/单行 JSON 类），只可能读作地址表"

    # ---- STRONG ----
    # A1 行首锚
    if re.match(r"^\s*#\s*(?:0x)?" + e + r"(?![0-9a-f])", low):
        return "STRONG", "A1 行首锚 #<entry>"
    # A2 md ATX 标题行（只认 .md/.markdown/.rst；.txt 里的 `# …` 归 A1/A3）
    #    要求地址**就在标题开头**（前面最多一个 ASCII 短词），防止把
    #    `## ③ 站点被调 00489280 (size=4710)` 这种"被引用的站点"当成锚点。
    m2 = re.match(r"^\s{0,3}#{1,6}\s+(.*)$", low)
    if st is not None and is_md(st.rel) and m2:
        rest = m2.group(1)
        pos = rest.find(e)
        if pos >= 0 and pos <= 12:
            pre = rest[:pos]
            if not re.search(r"[\u4e00-\u9fff]", pre) and len(pre.split()) <= 1:
                return "STRONG", "A2 md 标题行以该 entry 为章节"
    # A3 文件头 meta 字段在本行（代码文件不适用 A3）
    #    若该文件头部同时以 meta 字段点名了 3 个以上地址，头部就是**多目标列表**
    #    （实测 W163_dirtyrect/q3_detail.stdout.txt:12 `TARGET 004F9B70` 就是这种
    #    BFS 搜索日志），此时只有显式 `=`/`:` 分隔才算命名主体。
    if st is not None and not st.code and lineno <= 14:
        multi = st.head_meta is not None and len(st.head_meta) > 2
        for m in META_FIELD.finditer(low):
            if m.group(2) != e:
                continue
            sep = re.search(r"([=:])", low[m.start():m.start(2)])
            kw = m.group(1)
            named = kw not in ("target", "callee") or bool(sep)
            if sep or not multi:
                if named:
                    return "STRONG", "A3 文件头 meta 行以 entry=/start=/@0x 命名该 entry"
        for m in META_AT.finditer(low):
            if m.group(1) == e:
                return "STRONG", "A3 文件头 meta 行以 @0x 标注该 entry"
    # A4 反汇编起点
    if st is not None and st.disasm_min is not None \
            and st.disasm_linenos.get(lineno) == int(e, 16) == st.disasm_min:
        return "STRONG", "A4 该 entry 是该文件反汇编记录的起点（最小地址）"
    # A5 函数体定义命名（`void FUN_<entry>(...)`，行内不能是表格行）
    # A5 函数体定义命名，且它是**该文件第一个函数体定义**（反汇编起点在 C 侧的对应物：
    #    单函数 decomp_XXXX.c 的第 1 个定义就是它；decomp_all.c 这种全量伪代码里
    #    第 300 个函数不算锚点）
    if st is not None and st.funcdef_first_line == lineno \
            and re.match(FUNCDEF_LINE.pattern + e + r"\s*\(", low):
        return "STRONG", "A5 函数体定义 FUN_<entry>( 是该文件第一个函数体定义"

    # ---- MEDIUM ----
    if st is not None and st.has_header and st.key_col is not None:
        fields = [f.strip().strip('"') for f in re.split(r"[\t|,]", line)]
        if len(fields) >= 2:
            key = fields[st.key_col].lower().replace("0x", "")
            if key == e:
                cnt = st.tokens.get(e, 0)
                attr = [f for f in fields
                        if f and not re.fullmatch(r"(?:0x)?[0-9a-f]{6,}", f.lower())]
                if cnt <= 1 and len(attr) >= 2:
                    return "MEDIUM", "M1 声明表首列（主体项）唯一一条记录带属性字段"
                return "WEAK", "W2 表的关键列出现但同一 entry 在表里有多条行/无属性（流水表）"
    if re.search(r'"' + e + r'"\s*:\s*\{', low):
        return "MEDIUM", "M2 JSON 以该 entry 为 key 且 value 是带命名属性的对象"
    if re.search(r'"' + e + r'"\s*:\s*\[', low):
        return "WEAK", "W2 JSON key 的 value 纯地址数组（地址列表）"

    # ---- WEAK ----
    # W1 代码里的工具参数位（上一卡反例）
    if st is not None and st.code:
        if re.search(r"[(,]\s*(?:0x)?" + e + r"\s*[,)]", low) or "sys.argv" in low \
                or "subprocess" in low:
            return "WEAK", "W1 代码文件里的函数/工具参数位（hex 只是传参）"
    # W2 反汇编记录行
    if st is not None and lineno in st.disasm_linenos:
        return "WEAK", "W2 反汇编记录行的地址（指令流里的一个值）"
    if len(set(HEX_TOKEN.findall(low))) >= 3:
        return "WEAK", "W2 一行 >=3 个地址 token（地址表/调用图/引用表）"
    if re.match(r"^\s*(?:0x)?" + e + r"(?![0-9a-f])", low):
        return "WEAK", "W2 行首是该地址但非记录主体（地址列表行）"
    return "WEAK", "W3 正文/日志顺带提及"


def sensitivity_superset(lead_root, inv, files):
    """敏感性检查：coverage.tsv 里 evidence_path 含 classification_trace 的 [已证] 行有两类
    —— (a) 只有 trace（= R_TRACE_ONLY，802）；(b) trace 只是多源之一（90）。
    这里对 (b) 也算一次 A1，看把口径放宽后 127 会涨到多少。只读 coverage.tsv。"""
    r14 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for cand in (os.path.join(r14, "COVERAGE", "coverage.tsv"),):
        if os.path.exists(cand):
            cov = cand
            break
    else:
        return None
    only, anyh = set(), set()
    try:
        with open(cov, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()[1:]
    except OSError:
        return None
    for l in lines:
        f = l.split("\t")
        if len(f) < 8 or f[4].strip() != "[已证]":
            continue
        comps = [c for c in f[5].split(";") if c.strip()]
        if not any("classification_trace" in c for c in comps):
            continue
        anyh.add(f[0].lower())
        if all("classification_trace" in c for c in comps):
            only.add(f[0].lower())
    extra = anyh - only
    hit = {e for e in extra if inv.get(e)}
    print(f"[SENS] coverage.tsv: [已证] 含 trace 的 {len(anyh)} 行 = 仅 trace {len(only)} + "
          f"trace 为多源之一 {len(extra)}；后者 A1 文件名命中 {len(hit)} 行")
    return dict(any_trace=len(anyh), only_trace=len(only), extra=len(extra),
                extra_a1=len(hit), extra_a1_entries=sorted(hit))


# --------------------------------------------------------------------------- #
# 阶段 2b：全树内容命中（单趟 rg，-f 多字面量）
# --------------------------------------------------------------------------- #
def run_rg_batch(entries, lead_root, exclude_rel):
    pat = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pats.tmp")
    with open(pat, "w", encoding="utf-8", newline="\n") as fh:
        for e in entries:
            fh.write(e + "\n")
    cmd = ["rg", "-n", "-i", "-F", "-f", pat,
           "--no-messages", "--hidden", "--no-ignore", "--no-ignore-vcs",
           "--max-columns", "400", "--max-columns-preview",
           "--glob", "!.git/**", "--glob", "!*.exe", "--glob", "!*.dll",
           "--glob", "!*.zip", "--glob", "!*.7z"]
    for e in exclude_rel:
        cmd += ["--glob", "!" + e + "/**"]
    cmd += ["."]
    try:
        p = subprocess.run(cmd, cwd=lead_root, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=3600)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"[warn] rg 批量失败: {exc}", file=sys.stderr)
        return None
    if p.returncode not in (0, 1, 2):
        print(f"[warn] rg rc={p.returncode}", file=sys.stderr)
    if p.returncode == 2 and not p.stdout.strip():
        return None
    raw = collections.defaultdict(list)          # entry -> [(rel, lineno, text)]
    nline = 0
    for line in p.stdout.splitlines():
        m = re.match(r"^(.+?):(\d+):(.*)$", line)
        if not m:
            continue
        nline += 1
        rel = m.group(1)
        if rel.startswith(".\\") or rel.startswith("./"):
            rel = rel[2:]
        rel = rel.replace("\\", "/")
        text = m.group(3)
        low = text.lower()
        for e in set(HEX_TOKEN.findall(low)):
            if e in entries:
                raw[e].append((rel, int(m.group(2)), text))
    print(f"[in ] rg 批量: {nline} 条原始命中行 -> {len(raw)} 个 entry 有命中")
    return raw


def run_rg_one(entry, lead_root, exclude_rel):
    """兜底：批量趟里 0 命中的 entry 单独再搜一次（防 --max-columns 截断漏判）。"""
    cmd = ["rg", "-n", "-i", "-F", "--no-messages", "--hidden",
           "--no-ignore", "--no-ignore-vcs",
           "--glob", "!.git/**", "--glob", "!*.exe", "--glob", "!*.dll"]
    for e in exclude_rel:
        cmd += ["--glob", "!" + e + "/**"]
    cmd += [entry, "."]
    try:
        p = subprocess.run(cmd, cwd=lead_root, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900)
    except (OSError, subprocess.SubprocessError):
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


# --------------------------------------------------------------------------- #
# 阶段 2c：行级判定
# --------------------------------------------------------------------------- #
def hex_variants(entry):
    """entry 的 8 位形式 + 去前导零形式（`task2_PlayAt_7509E0.txt` 就是 6 位写法）。"""
    e = entry.lower()
    return {e, e.lstrip("0")}


def entry_named(rel, entry):
    b = posix_base(rel).lower()
    return any(v and v in b for v in hex_variants(entry))


def subject_entries(st, entry_set802):
    """该文件里以「主体形态」（meta 字段 / 行首锚 / md 标题 / 函数定义 / 反汇编起点）
    出现的 802 entry 集合。注意与"被提及"区分：反汇编体里被调用的地址不算主体。"""
    if st is None or st.bigfile:
        return set()
    cand = (st.meta_all | st.hash_all | st.md_all | st.funcdef) & entry_set802
    if st.disasm_min is not None:
        d = "%08x" % st.disasm_min
        if d in entry_set802:
            cand.add(d)
    return cand


def judge_row(entry, hits, structs, entry_set802):
    """hits: [(rel, lineno, text)] 全树外部命中。返回 dict。"""
    ext = [h for h in hits if file_kind(h[0]) == "external"]
    sel = [h for h in hits if file_kind(h[0]) == "selfref"]

    per_file = collections.defaultdict(list)
    text_of = {}
    for rel, lineno, text in ext:
        per_file[rel].append(lineno)
        text_of[(rel, lineno)] = text

    # 逐文件取最大形态（透明度：反例文件要能被点名）
    file_forms = {}
    for rel, linenos in per_file.items():
        st = structs.get(rel)
        fmax, fwhy, fline = "NONE", "", 0
        for lineno in linenos:
            f, w = classify(entry, st, lineno, text_of[(rel, lineno)])
            if RANK[f] > RANK[fmax]:
                fmax, fwhy, fline = f, w, lineno
        file_forms[rel] = (fmax, fwhy, len(linenos), fline)

    row_form = "NONE"
    for f, _w, _n, _l in file_forms.values():
        if RANK[f] > RANK[row_form]:
            row_form = f

    dedicated, ded_note, chosen, subj = False, "", None, None
    if row_form != "NONE":
        cands = [rel for rel, v in file_forms.items() if v[0] == row_form]
        info = {rel: (entry_named(rel, entry),
                      subject_entries(structs.get(rel), entry_set802))
                for rel in cands}

        def key(rel):
            named, sj = info[rel]
            shared = 1 if (sj - {entry}) else 0
            return (0 if named else 1, shared, rel)

        chosen = sorted(cands, key=key)[0]
        st = structs.get(chosen)
        named, sj = info[chosen]
        subj = sj - {entry}
        dedicated = bool(named and not subj)
        ded_note = (f"锚点文件 {chosen}（{st.size if st else -1}B，该 entry 出现 "
                    f"{st.tokens.get(entry, 0) if st else 0} 次"
                    f"{'，头 512KB 截断' if st is not None and st.truncated else ''}；"
                    f"文件名带 entry={named}；文件内以主体形态出现的 802 entry 数="
                    f"{len(sj) if st else 0}"
                    f"{'（另有 ' + ','.join(sorted(subj)[:4]) + '）' if subj else '（仅此一个）'}；"
                    f"文件内提及的 802 entry 数={len(st.n802) if st else 0}）")

    return dict(form=row_form,
                why=file_forms[chosen][1] if chosen else "无外部内容命中",
                file=chosen, lineno=file_forms[chosen][3] if chosen else 0,
                hits_in_file=file_forms[chosen][2] if chosen else 0,
                dedicated=dedicated, ded_note=ded_note,
                n_ext=len(ext), n_self=len(sel),
                file_forms={k: v[:3] for k, v in file_forms.items()})


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    r14 = os.path.dirname(here)
    lead = os.path.dirname(r14)
    ap = argparse.ArgumentParser(description="127 行 trace-only 的内容级锚点全量验证")
    ap.add_argument("--lead", default=lead)
    ap.add_argument("--resolve", default=os.path.join(r14, "R16_BASE", "evid", "resolve.tsv"))
    ap.add_argument("--prev", default=os.path.join(r14, "R16_SCAN802"))
    ap.add_argument("--out", default=here)
    ap.add_argument("--sample-n", type=int, default=16)
    ap.add_argument("--no-content", action="store_true")
    ap.add_argument("--reuse-cache", action="store_true",
                    help="复用上次 rg 批量命中（仅调试用；最终产物应跑全量）")
    args = ap.parse_args(argv)

    exclude_rel = [os.path.relpath(args.out, args.lead).replace("\\", "/")]

    # ---------------- 阶段 1 ----------------
    rows = load_rows(args.resolve)
    rows.sort(key=lambda r: r["entry"])
    n = len(rows)
    print(f"[data] R_TRACE_ONLY = {n} (卡面 802)")
    entries802 = [r["entry"].lower() for r in rows]
    inv, files = build_name_index(args.lead, exclude_dirs=[args.out])
    print(f"[data] 索引文件数 = {len(files)}")

    a1 = {}
    for r in rows:
        e = r["entry"].lower()
        a1[e] = sorted({files[i] for i in inv.get(e, [])})
    a1_rows = [r for r in rows if a1[r["entry"].lower()]]
    print(f"[A1] 文件名命中行 = {len(a1_rows)} / {n} ({100.0*len(a1_rows)/n:.2f}%)，"
          f"涉及文件 {len({f for r in a1_rows for f in a1[r['entry'].lower()]})}")

    # 上一卡的 18 行抽样（索引口径照录：0, n-1, 50,100,...,800）
    prev_idx = [0, n - 1] + [50 * k for k in range(1, 17)]
    prev_idx = [i for i in dict.fromkeys(prev_idx) if 0 <= i < n]
    prev_rows = [rows[i] for i in prev_idx]
    cross_entries = [r["entry"].lower() for r in prev_rows]

    if args.no_content:
        return

    # ---------------- 阶段 2：全树内容命中（一趟） ----------------
    batch_entries = sorted({r["entry"].lower() for r in a1_rows} | set(cross_entries))
    print(f"[in ] 批量搜索 entry 数 = {len(batch_entries)} (127 行 ∪ 18 行抽样)")
    cache = os.path.join(args.out, "_hits_cache.json")
    raw = None
    if args.reuse_cache and os.path.exists(cache):
        with open(cache, encoding="utf-8") as fh:
            raw = {k: [tuple(x) for x in v] for k, v in json.load(fh).items()}
        print(f"[in ] 复用命中缓存 {cache}（{len(raw)} 个 entry）")
    if raw is None:
        raw = run_rg_batch(batch_entries, args.lead, exclude_rel)
        if raw is None:
            sys.exit("[FATAL] 批量 rg 失败，内容级判定不可做")
        with open(cache, "w", encoding="utf-8") as fh:
            json.dump({k: [list(x) for x in v] for k, v in raw.items()}, fh)

    # 兜底：0 命中的单独复核（防 --max-columns 截断 / rg 处理导致漏）
    zero = [e for e in batch_entries if e not in raw]
    if zero:
        print(f"[in ] 批量 0 命中的 entry = {len(zero)}，逐个兜底复核")
        for e in zero:
            hits = run_rg_one(e, args.lead, exclude_rel)
            if hits:
                raw[e] = hits
                print(f"      [兜底命中] {e}: {len(hits)} 处")

    # 结构缓存
    entries802_set = set(entries802)
    structs = {}
    need = {h[0] for e in raw for h in raw[e]}
    print(f"[in ] 需建结构的命中文件 = {len(need)}")
    for rel in sorted(need):
        structs[rel] = build_struct(args.lead, rel, entries802_set)

    # ---------------- 阶段 3：127 行全量判定 ----------------
    recs = []
    for r in a1_rows:
        e = r["entry"].lower()
        hits = raw.get(e, [])
        j = judge_row(e, hits, structs, entries802_set)
        recs.append((r, j))
    vc = collections.Counter(j["form"] for _, j in recs)
    whyc = collections.Counter(j["why"].split()[0] for _, j in recs)
    print(f"[127] 四桶 STRONG={vc.get('STRONG',0)} MEDIUM={vc.get('MEDIUM',0)} "
          f"WEAK={vc.get('WEAK',0)} NONE={vc.get('NONE',0)}")
    print(f"[127] 判定依据分布: " + ", ".join(f"{k}={v}" for k, v in whyc.most_common()))
    ded = sum(1 for _, j in recs if j["form"] == "STRONG" and j["dedicated"])
    print(f"[127] STRONG 且逐 entry 专属 = {ded}")
    nd = [(r["entry"], j["file"]) for r, j in recs if j["form"] == "STRONG" and not j["dedicated"]]
    print(f"[127] STRONG 但非专属 = {len(nd)}")
    for e2, f2 in nd:
        print(f"      {e2}  {f2}")

    out127 = os.path.join(args.out, "anchor127.tsv")
    with open(out127, "w", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(HDR127) + "\n")
        for r, j in recs:
            e = r["entry"]
            note = (f"{j['why']}；锚点/最强文件 {j['file'] or '无'}:{j['lineno']}；"
                    f"外部命中 {j['n_ext']} 处、台账自指 {j['n_self']} 处")
            if j["ded_note"]:
                note += "；" + j["ded_note"]
            # 只看该行的 A1 候选文件（文件名带 entry 的那些）：它们里面有谁没锚定住
            weakcand = [f"{p}({j['file_forms'][p][0]})" for p in a1[e.lower()]
                        if p in j["file_forms"] and j["file_forms"][p][0] in ("WEAK", "NONE")]
            if weakcand:
                note += "；A1 候选文件里非锚点形态：" + "; ".join(sorted(weakcand)[:6])
                if len(weakcand) > 6:
                    note += f"；…共 {len(weakcand)} 个"
            fh.write("\t".join([e, r["subsystem"], r["name"],
                                ";".join(a1[e.lower()]), j["form"],
                                str(j["hits_in_file"]),
                                "Y" if j["dedicated"] else "N",
                                note]) + "\n")
    print(f"[out] {out127}")

    # ---------------- 阶段 3b：与上一卡 18 行交叉核对 ----------------
    prev18 = []
    p = os.path.join(args.prev, "sample18.tsv")
    if os.path.exists(p):
        with open(p, encoding="utf-8", newline="") as fh:
            prev18 = list(csv.DictReader(fh, delimiter="\t"))
    prev_map = {r["entry"].lower(): r for r in prev18}
    cross = []
    for r in prev_rows:
        e = r["entry"].lower()
        j = judge_row(e, raw.get(e, []), structs, entries802_set)
        pv = prev_map.get(e, {})
        pv_verdict = pv.get("verdict(STRONG|WEAK|NONE)", "?")
        mine = j["form"]
        exact = mine == pv_verdict
        # 折叠口径：上一卡没有 MEDIUM 桶，MEDIUM 与 WEAK 都落在它的"WEAK"里
        collapsed = ("WEAK" if mine in ("WEAK", "MEDIUM") else mine) == pv_verdict
        cross.append(dict(entry=e, mine=mine, prev=pv_verdict, exact=exact,
                          collapsed=collapsed, file=j["file"] or "无",
                          why=j["why"], n_ext=j["n_ext"], a1=bool(a1[e])))
    cc = collections.Counter(x["mine"] for x in cross)
    print(f"[18 ] 我这套口径: STRONG={cc.get('STRONG',0)} MEDIUM={cc.get('MEDIUM',0)} "
          f"WEAK={cc.get('WEAK',0)} NONE={cc.get('NONE',0)}")
    print(f"[18 ] 上一卡: STRONG=3 WEAK=15 NONE=0")
    print(f"[18 ] 逐行逐桶一致 = {sum(1 for x in cross if x['exact'])}/{len(cross)}；"
          f"折叠口径（MEDIUM∪WEAK ≡ 上一卡 WEAK）一致 = "
          f"{sum(1 for x in cross if x['collapsed'])}/{len(cross)}")
    with open(os.path.join(args.out, "cross18.tsv"), "w", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(["entry", "prev_verdict", "my_form", "agree_exact",
                            "agree_collapsed", "my_anchor_file", "n_ext_hits",
                            "A1_hit", "why"]) + "\n")
        for x in cross:
            fh.write("\t".join([x["entry"], x["prev"], x["mine"],
                                "Y" if x["exact"] else "N",
                                "Y" if x["collapsed"] else "N", x["file"],
                                str(x["n_ext"]), "Y" if x["a1"] else "N",
                                x["why"]]) + "\n")

    # ---------------- 阶段 4：机器抽样（≤18 行，供人工目视） ----------------
    strong = [(r, j) for r, j in recs if j["form"] == "STRONG"]
    medium = [(r, j) for r, j in recs if j["form"] == "MEDIUM"]
    sample = pick_sample(strong, medium, args.sample_n)
    print(f"[S18] 抽样行数 = {len(sample)} (STRONG 桶 {len(strong)} / MEDIUM 桶 {len(medium)})")
    if len(sample) > 18:
        sys.exit("[FATAL] 抽样超 18 行，违反卡面硬边界")
    with open(os.path.join(args.out, "sample18.tsv"), "w", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(HDR18) + "\n")
        for r, j in sample:
            e = r["entry"].lower()
            ctx = ""
            if j["file"] and j["file"] in structs:
                st = structs[j["file"]]
                if 0 < j["lineno"] <= len(st.lines):
                    ctx = st.lines[j["lineno"] - 1].strip()
            fh.write("\t".join([r["entry"], r["subsystem"], r["name"],
                                j["form"], j["file"] or "无", str(j["hits_in_file"]),
                                ctx[:120], "", ""]) + "\n")

    # 机器可读统计
    cand_form = collections.Counter()
    rows_mention_only = 0
    anchor_why = collections.Counter()
    for r, j in recs:
        e = r["entry"].lower()
        anchor_why[j["why"].split()[0]] += 1
        m = re.search(r"文件内提及的 802 entry 数=(\d+)", j["ded_note"] or "")
        if m and m.group(1) == "1":
            rows_mention_only += 1
        for p in a1[e]:
            cand_form[j["file_forms"].get(p, ("NOHIT", "", 0))[0]] += 1
    print(f"[127] 锚点形态分布: " + ", ".join(f"{k}={v}" for k, v in anchor_why.most_common()))
    print(f"[127] 锚点文件只提及这一个 802 entry 的行 = {rows_mention_only}")
    print("[267] A1 候选文件逐文件形态: " +
          ", ".join(f"{k}={v}" for k, v in cand_form.most_common()))

    # 候选文件里是否含 ①②③④ 四环分组（这才是真 ④ 素材；纯 dump 不是）
    RING = ("①", "②", "③", "④")
    four = []
    for r, j in recs:
        for p in a1[r["entry"].lower()]:
            st = structs.get(p)
            if st is None or st.bigfile:
                continue
            txt = "\n".join(st.lines)
            if all(mk in txt for mk in RING):
                four.append(r["entry"])
                break
    print(f"[127] 候选文件里有 ①②③④ 四环分组的行 = {len(four)}"
          + (("  [" + ", ".join(sorted(four)[:20]) + (" …]") ) if four else ""))

    # 敏感性：把「classification_trace 只是多源之一」的 [已证] 行并入后，A1 会涨多少
    sens = sensitivity_superset(args.lead, inv, files)
    stats = dict(n_rows=n, a1_rows=len(a1_rows),
                 a1_files=len({f for r in a1_rows for f in a1[r["entry"].lower()]}),
                 forms={k: vc.get(k, 0) for k in ("STRONG", "MEDIUM", "WEAK", "NONE")},
                 strong_dedicated=ded,
                 anchor_forms=dict(anchor_why),
                 rows_anchor_mentions_only_entry=rows_mention_only,
                 candidate_file_forms=dict(cand_form),
                 rows_with_four_rings=four,
                 sens_superset=sens,
                 cross18={k: cc.get(k, 0) for k in ("STRONG", "MEDIUM", "WEAK", "NONE")},
                 cross18_agree_exact=sum(1 for x in cross if x["exact"]),
                 cross18_agree_collapsed=sum(1 for x in cross if x["collapsed"]),
                 sample=[r["entry"] for r, _ in sample])
    with open(os.path.join(args.out, "stats.json"), "w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=1)
    for f in ("_pats.tmp",):
        try:
            os.remove(os.path.join(here, f))
        except OSError:
            pass
    return stats


def pick_sample(strong, medium, sample_n):
    """确定规则：STRONG/MEDIUM 各桶 entry 升序取首/末/等距；
    优先纳入上一卡点名的反例 entry（0053AF40），总数 <= 18。"""
    BUDGET = 18
    FORCE = "0053af40"
    out = []
    seen = set()
    buckets = [("S", strong), ("M", medium)]
    for tag, b in buckets:
        if not b:
            continue
        b = sorted(b, key=lambda x: x[0]["entry"])
        if tag == "S":
            quota = min(sample_n, BUDGET) if not medium else max(1, BUDGET - 9)
        else:
            quota = BUDGET - len(out)
        idx = {0, len(b) - 1}
        if quota > 2:
            step = (len(b) - 1) / (quota - 1)
            idx |= {int(round(k * step)) for k in range(quota)}
        idx = sorted(i for i in idx if 0 <= i < len(b))
        for i in idx:
            r, j = b[i]
            if r["entry"].lower() in seen:
                continue
            if len(out) >= BUDGET:
                break
            seen.add(r["entry"].lower())
            out.append((r, j))
    # 强制纳入反例（若在 STRONG/MEDIUM 桶里且还没被抽到）
    if FORCE not in seen:
        for r, j in strong + medium:
            if r["entry"].lower() == FORCE:
                if len(out) >= BUDGET:
                    out.pop(len(out) // 2)   # 挤掉一个中间点，保证 <=18
                out.append((r, j))
                seen.add(FORCE)
                break
    return out


if __name__ == "__main__":
    main()
