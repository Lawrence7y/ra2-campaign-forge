#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mev675.py — R16-MEASURE-EVID675 度量器（只读 + 只写 R16_MEASURE_EVID675/）

任务：对 791 行 `R_TRACE_ONLY` 中「文件名零命中」的 675 行，做**有界**的内容级搜索，
      判入 CTX_STRONG / CTX_MEDIUM / CTX_WEAK / CTX_NONE 四桶；并用**同一套判据**
      重跑 116 行 dump-only（127 文件名命中行 − 11 带四环行）。

阶段（--stage 可单跑，命中缓存落盘以便反复改判定而不重扫）：
  repro   复现 675：resolve.tsv 筛 R_TRACE_ONLY(791) → 文件名索引 → 文件名命中行(116) → 零候选(675)
  scale   报规模：允许扩展名集合的文件数 / 总体积；超 5 万文件或 2GB 则要求分片
  search  一趟 rg 批量内容搜索（-F -f 多字面量），落 _hits_<scope>.tsv
  judge   逐命中行判定（行本地判据）→ 四桶；落 buckets675.tsv / recheck116.tsv
  sample  确定性抽样 ≤18 行，落 sample18_draft.tsv（上下文供人工核）

两个 scope：
  primary  卡面指定：扩展名限 .tsv/.txt/.json/.md/.csv/.log；只搜 8 位 hex（大小写不敏感）
  wide     敏感性：primary ∪ 代码扩展名(.py/.asm/...)，且加搜去前导零的短形式
           —— 只为两件事：(a) 处理上一卡点名的反例 p1_dump_0053AF40.py；(b) 检查
           「真找不到」是否只是 8 位写法漏搜。**不作为权威口径。**

边界：不改任何输入；不判 grade；不写 ④；不读 gamemd.exe；只写本目录。
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
import time

# --------------------------------------------------------------------------- #
# 常量
# --------------------------------------------------------------------------- #
HDR_BUCKETS = ["entry", "subsystem", "name", "bucket", "hit_files", "hit_files_top3", "note"]
HDR_RECHECK = ["entry", "subsystem", "name", "filehit_127", "bucket", "hit_files",
               "hit_files_top3", "note"]
HDR_SAMPLE = ["entry", "subsystem", "name", "bucket", "file", "lineno",
              "ctx_20_40", "auto_form", "auto_why", "manual_verdict", "manual_reason"]

HEX_TOKEN = re.compile(r"(?<![0-9a-f])[0-9a-f]{8}(?![0-9a-f])")
HEX_STR = re.compile(r"[0-9a-f]{8,}")

PRIMARY_EXT = {".tsv", ".txt", ".json", ".md", ".csv", ".log"}
CODE_EXT = {".py", ".asm", ".s", ".c", ".cpp", ".h", ".inc", ".ps1", ".sh",
            ".js", ".ts", ".java", ".go", ".rs", ".bat", ".cmd"}
MD_EXT = {".md", ".markdown", ".rst"}

# 台账/追踪/度量产物：出现该 entry 属"自身记录/派生记录"，不是可引用证据
SELFREF_NAME = {
    "coverage.tsv", "row_class.tsv", "resolve.tsv", "summary.tsv",
    "coverage_pinned.tsv", "classification_trace.tsv",
    # 本线与上一线度量卡的逐行表：派生自同一台账，不是证据
    "traceonly802.tsv", "anchor127.tsv", "sample18.tsv", "stats.json",
    "buckets675.tsv", "recheck116.tsv", "sample18_draft.tsv",
}
SELFREF_DIRPART = ("_hygiene", "r16_scan802", "r16_probe_802_anchor",
                   "r16_measure_evid675")

KEY_COLS = {"entry", "addr", "address", "va", "vaddr", "rva", "ea",
            "func", "function", "fname", "fn", "funcva", "entryva",
            "start", "entry_addr", "funcaddr", "func_addr"}

DISASM_PATS = [
    re.compile(r"^([0-9a-f]{8})[:!]?\s{2,}([0-9a-f]{2})\b"),       # 0045A560  53  push
    re.compile(r"^([0-9a-f]{8})\s*\(?\+?0x[0-9a-f]{1,4}\)?"),       # 0053AF40 +0x0000
    re.compile(r"^([0-9a-f]{8}):\s"),                                # 0048A4F0: 53
]
# `addr  <token>` 这种 4 号形态太宽松：会把「地址 + 符号名」表（如
# `005D3BA0  MessageListClass::MessageListClass`）当成反汇编记录。
# 实测它让 005D3BA0 白拿了 A4（该行恰是文件最小地址）——本卡收紧为
# 「第二列必须是 hex 字节串 或 真助记符」。
MNEMONICS = {
    "push", "pop", "mov", "movzx", "movsx", "lea", "add", "sub", "and", "or",
    "xor", "cmp", "test", "call", "jmp", "je", "jne", "jz", "jnz", "jg",
    "jge", "jl", "jle", "ja", "jae", "jb", "jbe", "js", "jns", "jo", "jno",
    "ret", "retn", "nop", "inc", "dec", "imul", "mul", "idiv", "div", "shl",
    "shr", "sar", "sal", "rol", "ror", "neg", "not", "adc", "sbb", "xchg",
    "int", "int3", "leave", "enter", "fld", "fst", "fstp", "fadd", "fsub",
    "fmul", "fdiv", "rep", "repe", "repne", "movsd", "movss", "cmove",
    "sete", "setne", "bt", "bts", "btr", "bsf", "bsr", "loop", "cdq", "cwd",
}
DISASM_TWOCOL = re.compile(r"^([0-9a-f]{8}) {2,}(\S+)")


def disasm_addr(low):
    """该行是不是一条反汇编记录行？是则返回其地址，否则 None。"""
    for pat in DISASM_PATS:
        m = pat.match(low)
        if m:
            return int(m.group(1), 16)
    m = DISASM_TWOCOL.match(low)
    if m:
        tok = m.group(2).rstrip(",:")
        if re.fullmatch(r"(?:[0-9a-f]{2})+", tok) or tok in MNEMONICS:
            return int(m.group(1), 16)
    return None

META_FIELD = re.compile(
    r"(?<![0-9a-z_])(entry|start|target|addr|address|callee|fn|func|function|"
    r"entryva|funcva)\s*[=:]?\s*(?:0x)?([0-9a-f]{8})(?![0-9a-f])")
# 只有这些关键词是「以该 entry 为主体」的命名；其余（fn=/func=/target=/callee=）
# 是「被引用的那个函数」的标注，出现在站点/调用点记录行里，不是主体
# （PROBE_802_ANCHOR §2.1 的注释已这样要求，但它的实现没排掉 fn= —— 本卡补上）
META_SUBJECT = {"entry", "start", "addr", "address", "entryva", "funcva"}
META_AT = re.compile(r"@(?:0x)?([0-9a-f]{8})(?![0-9a-f])")
FUNCDEF = re.compile(r"(?<![0-9a-z_])(?:fun_|sub_|fn_)(?:0x)?([0-9a-f]{8})(?![0-9a-f])")
FUNCDEF_LINE = re.compile(r"^[^;()]*\b(?:fun_|sub_|fn_)(?:0x)?")

TRUNC_MARK = "[... omitted end of long line]"
BASE_DIR = "r16_measure_evid675"   # 本卡产物目录名（后置过滤用）

# 工具参数位（上一卡点名的反例）：命中点落在这些位置时**不得** STRONG
ARGONLY_PAT = re.compile(
    r"(?:sys\.argv|subprocess|os\.system|run\(|Popen|popen)"
    r"|(?:dump|disasm|dump_range|dumpfn|scan|analyze|analyse|main|cli)\s*\("
)
CALLARG_PAT = re.compile(r"[(,]\s*(?:0x)?([0-9a-f]{8})\s*[,)]")

HEAD_BYTES = 512 * 1024
BIG_NOSTRUCT = 20 * 1024 * 1024
SCALE_FILES_MAX = 50_000
SCALE_BYTES_MAX = 2 * 1024 * 1024 * 1024


# --------------------------------------------------------------------------- #
# 工具
# --------------------------------------------------------------------------- #
def log(msg):
    print(msg, flush=True)


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
    """selfref（台账自指 / 度量产物） vs external。"""
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


def is_md(rel):
    return os.path.splitext(rel)[1].lower() in MD_EXT


def is_code(rel):
    return os.path.splitext(rel)[1].lower() in CODE_EXT


def variants(entry, scope):
    """搜索用的字面量集合。wide 额外加去前导零的短形式（≥6 位）。"""
    e = entry.lower()
    v = {e}
    if scope == "wide":
        s = e.lstrip("0")
        if len(s) >= 6 and s != e:
            v.add(s)
    return v


def short_map_of(entry_set):
    """去前导零短形式 -> 8 位 entry（仅 wide 用；短形式在 8 位 entry 间唯一）。"""
    m = {}
    for e in entry_set:
        s = e.lstrip("0")
        if 6 <= len(s) < 8:
            m[s] = e
    return m


# --------------------------------------------------------------------------- #
# 阶段 repro：复现 675
# --------------------------------------------------------------------------- #
def load_rows(resolve_path, want="R_TRACE_ONLY"):
    with open(resolve_path, "r", encoding="utf-8", newline="") as fh:
        return [r for r in csv.DictReader(fh, delimiter="\t") if r.get("class") == want]


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


def stage_repro(args, rows):
    t0 = time.time()
    inv, files = build_name_index(args.lead, [args.out])
    log(f"[repro] 文件名索引: {len(files)} 个文件 ({time.time()-t0:.1f}s)")

    recs = []
    for r in rows:
        e = r["entry"].lower()
        a1 = sorted({files[i] for i in inv.get(e, [])})
        recs.append(dict(row=r, a1=a1))

    hit = [d for d in recs if d["a1"]]
    zero = [d for d in recs if not d["a1"]]
    a1_files = {p for d in recs for p in d["a1"]}
    log(f"[repro] R_TRACE_ONLY = {len(rows)}   (期望 791)")
    log(f"[repro] 文件名命中行 = {len(hit)}   (期望 116 = 127-11)")
    log(f"[repro] 零候选行     = {len(zero)}   (期望 675)")
    log(f"[repro] 命中文件数   = {len(a1_files)}   (上一卡 267，去掉 11 行的专属件后应变小)")

    return dict(recs=recs, hit=hit, zero=zero, n_files=len(files),
                a1_file_count=len(a1_files))


# --------------------------------------------------------------------------- #
# 阶段 scale：报规模
# --------------------------------------------------------------------------- #
def stage_scale(args):
    """枚举 scope 内的文本文件，报文件数 / 总体积。"""
    exts = set(PRIMARY_EXT) | (set(CODE_EXT) if args.scope == "wide" else set())
    out_excl = os.path.normcase(os.path.abspath(args.out))
    n = 0
    total = 0
    by_ext = collections.Counter()
    biggest = []
    for root, dirs, fnames in os.walk(args.lead):
        dirs[:] = [d for d in dirs if d.lower() != ".git"
                   and os.path.normcase(os.path.abspath(os.path.join(root, d))) != out_excl]
        for fn in fnames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in exts:
                continue
            full = os.path.join(root, fn)
            try:
                sz = os.path.getsize(full)
            except OSError:
                continue
            n += 1
            total += sz
            by_ext[ext] += 1
            if len(biggest) < 40 or sz > biggest[0][0]:
                biggest.append((sz, os.path.relpath(full, args.lead)))
                biggest.sort()
                del biggest[:-20]
    over = n > SCALE_FILES_MAX or total > SCALE_BYTES_MAX
    log(f"[scale] scope={args.scope}  扩展名={len(exts)}")
    log(f"[scale] 文件数 = {n:,}   总体积 = {total:,} B = {total/1024/1024:.1f} MB "
        f"= {total/1024/1024/1024:.2f} GB")
    log(f"[scale] 阈值: {SCALE_FILES_MAX:,} 文件 / {SCALE_BYTES_MAX/1024/1024/1024:.0f} GB "
        f"⇒ {'超限，必须分片' if over else '未超限，可单趟'}")
    log(f"[scale] by_ext: " + ", ".join(f"{k or '<none>'}={v}" for k, v in by_ext.most_common()))
    log("[scale] 最大 10 个:")
    for sz, rel in sorted(biggest, reverse=True)[:10]:
        log(f"        {sz/1024/1024:8.2f} MB  {rel}")
    return dict(scope=args.scope, files=n, bytes=total, over=over,
                by_ext=dict(by_ext.most_common()))


# --------------------------------------------------------------------------- #
# 阶段 search：一趟 rg 批量搜
# --------------------------------------------------------------------------- #
def stage_search(args, rows):
    t0 = time.time()
    pats = set()
    for r in rows:
        pats |= variants(r["entry"], args.scope)
    pat_path = os.path.join(args.out, f"_pats_{args.scope}.tmp")
    with open(pat_path, "w", encoding="utf-8", newline="\n") as fh:
        for p in sorted(pats):
            fh.write(p + "\n")

    exts = set(PRIMARY_EXT) | (set(CODE_EXT) if args.scope == "wide" else set())
    cmd = ["rg", "-n", "-i", "-F", "-f", pat_path,
           "--no-messages", "--hidden", "--no-ignore", "--no-ignore-vcs",
           "--max-columns", "400", "--max-columns-preview"]
    for e in sorted(exts):
        cmd += ["--iglob", "*" + e]
    cmd += ["--glob", "!.git/**",
            "--glob", "!*.exe", "--glob", "!*.dll", "--glob", "!*.zip", "--glob", "!*.7z"]
    rel_out = os.path.relpath(args.out, args.lead).replace("\\", "/")
    cmd += ["--glob", "!" + rel_out + "/**",
            "--glob", "!**/" + posix_base(rel_out) + "/**", "."]

    log(f"[search] scope={args.scope}  模式 {len(pats)} 个  扩展名 {len(exts)} 种")
    log(f"[search] cmd: rg -n -i -F -f <{len(pats)}> ... (cwd={args.lead})")
    hits_path = os.path.join(args.out, f"_hits_{args.scope}.tsv")
    nline = 0
    with open(hits_path, "w", encoding="utf-8", newline="\n") as out:
        p = subprocess.run(cmd, cwd=args.lead, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=7200)
        if p.returncode == 2:
            # 实测：rc=2 只来自断链（Windows 无法访问 Linux 符号链接），stdout 仍可用
            err = p.stderr.decode("utf-8", "replace").strip().splitlines()
            log(f"[search] rg rc=2（断链），stdout 仍可用；stderr 前 3 行: {err[:3]}")
        elif p.returncode not in (0, 1):
            log(f"[search][FATAL] rg rc={p.returncode}")
            return None
        n_self = 0
        for raw in p.stdout.splitlines():
            line = raw.decode("utf-8", "replace")
            m = re.match(r"^(.+?):(\d+):(.*)$", line)
            if not m:
                continue
            rel = m.group(1)
            if rel.startswith(".\\") or rel.startswith("./"):
                rel = rel[2:]
            rel = rel.replace("\\", "/")
            # 后置兜底：本卡自己的产物一律不进语料（rg glob 在 Windows 上会漏）
            if rel.lower().startswith(rel_out.lower() + "/") or \
                    ("/" + BASE_DIR + "/") in ("/" + rel.lower()):
                n_self += 1
                continue
            out.write(f"{rel}\t{m.group(2)}\t{m.group(3)}\n")
            nline += 1
    log(f"[search] 命中行 {nline:,} 行 → {hits_path} ({time.time()-t0:.1f}s)")
    return dict(hits_path=hits_path, n_lines=nline)


SHORT_TOKEN = re.compile(r"(?<![0-9a-f])[0-9a-f]{6,7}(?![0-9a-f])")


def load_hits(path, entry_set, short_map=None):
    """读回命中，按 hex token 边界重新归属（防子串误配）。

    short_map: 去前导零短形式 -> 8 位 entry（仅 wide scope 用来认 `0x46CE10` 写法）。
    """
    hits = collections.defaultdict(list)
    raw_lines = 0
    unattributed = 0
    t0 = time.time()
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            raw_lines += 1
            rel, ln, text = line.rstrip("\n").split("\t", 2)
            low = text.lower()
            toks = set(HEX_TOKEN.findall(low))
            got = set(t for t in toks if t in entry_set)
            if short_map:
                for t in SHORT_TOKEN.findall(low):
                    e8 = short_map.get(t)
                    if e8 and e8 not in toks:
                        got.add(e8)
            if not got:
                unattributed += 1
                continue
            for t in got:
                hits[t].append((rel, int(ln), text))
    log(f"[judge] 读回 {raw_lines:,} 行命中，重新归属后 {len(hits):,} 个 entry 有命中；"
        f"未归属 {unattributed:,} 行（hex 落在更长 hex 串内，按 8 位边界丢弃）({time.time()-t0:.1f}s)")
    return hits


# --------------------------------------------------------------------------- #
# 单文件结构
# --------------------------------------------------------------------------- #
class FStruct:
    __slots__ = ("rel", "size", "code", "has_header", "key_col", "ncols",
                 "disasm_min", "disasm_first_addr", "disasm_linenos", "head_meta", "meta_all",
                 "hash_all", "md_all", "funcdef", "funcdef_first_line",
                 "tokens", "truncated", "bigfile", "n802")

    def __init__(self, rel):
        self.rel = rel
        self.size = -1
        self.code = is_code(rel)
        self.has_header = False
        self.key_col = None
        self.ncols = 0
        self.disasm_min = None
        self.disasm_first_addr = None   # 文本顺序第一条反汇编记录的地址
        self.disasm_linenos = {}
        self.head_meta = set()
        self.meta_all = set()
        self.hash_all = set()
        self.md_all = set()
        self.funcdef = set()
        self.funcdef_first_line = None
        self.tokens = collections.Counter()
        self.truncated = False
        self.bigfile = False
        self.n802 = set()


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
    st.tokens = collections.Counter(HEX_TOKEN.findall(text.lower()))
    st.n802 = {t for t in st.tokens if t in want_set}

    nonempty = [(i + 1, l) for i, l in enumerate(lines[:30]) if l.strip()]
    if nonempty:
        for _i, l in nonempty[:3]:
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

    head_linenos = {ln for ln, _l in nonempty[:12]}
    for i, l in enumerate(lines):
        low = l.lower()
        a = disasm_addr(low)
        if a is not None:
            st.disasm_linenos[i + 1] = a
            if st.disasm_first_addr is None:
                st.disasm_first_addr = a
            if st.disasm_min is None or a < st.disasm_min:
                st.disasm_min = a
        for m in META_FIELD.finditer(low):
            st.meta_all.add(m.group(2))
            if (i + 1) in head_linenos and m.group(1) in META_SUBJECT:
                st.head_meta.add(m.group(2))
        for m in META_AT.finditer(low):
            st.meta_all.add(m.group(1))
            if (i + 1) in head_linenos:
                st.head_meta.add(m.group(1))
        m = re.match(r"^\s*#\s*(?:0x)?([0-9a-f]{8})(?![0-9a-f])", low)
        if m:
            st.hash_all.add(m.group(1))
        if is_md(rel) and re.match(r"^\s{0,3}#{1,6}\s", low):
            for t in HEX_TOKEN.findall(low):
                st.md_all.add(t)
        m = FUNCDEF.search(low)
        if m and re.match(FUNCDEF_LINE.pattern + m.group(1) + r"\s*\(", low):
            st.funcdef.add(m.group(1))
            if st.funcdef_first_line is None:
                st.funcdef_first_line = i + 1
    return st


# --------------------------------------------------------------------------- #
# 判定
# --------------------------------------------------------------------------- #
RANK = {"NONE": 0, "WEAK": 1, "MEDIUM": 2, "STRONG": 3}
TO_CTX = {"STRONG": "CTX_STRONG", "MEDIUM": "CTX_MEDIUM",
          "WEAK": "CTX_WEAK", "NONE": "CTX_NONE"}


def is_tool_arg(entry, low):
    """命中点是否落在「工具参数位」：sys.argv / subprocess / dump() 之类实参。

    上一卡点名的反例 `p1_dump_0053AF40.py:20`
        for e, n in [(0x0053AF40,'POS 0053AF40'), ]:
    hex 是 dump() 的入口参数 ⇒ 必须是 WEAK。
    判据：行内出现工具/调用前缀，且该 entry 在 `(` / `,` 之后、`)` / `,` 之前。
    """
    if not ARGONLY_PAT.search(low):
        return False
    for m in CALLARG_PAT.finditer(low):
        if m.group(1) == entry:
            return True
    # argv 列表行：`sys.argv[1]` / `['0053af40']` 这种
    if "sys.argv" in low or "subprocess" in low:
        return f"'{entry}'" in low or f'"{entry}"' in low or entry in low
    return False


def classify(entry, st, lineno, line):
    """返回 (form, why, form_code)。form ∈ STRONG/MEDIUM/WEAK。行本地判据。"""
    e = entry.lower()
    low = line.lower()
    if st is not None and st.bigfile:
        return "WEAK", "W2 大文件（>20MB）未建结构，命中按地址表计", "W2"
    if low.rstrip().endswith(TRUNC_MARK):
        return "WEAK", "W2 超长行被 rg 截断（地址字典/单行 JSON 类），只可能读作地址表", "W2"

    argonly = is_tool_arg(e, low)

    # ---- STRONG（工具参数位一票否决，见卡面 2.2 反例要求）----
    if not argonly:
        # A1 行首锚
        if re.match(r"^\s*#\s*(?:0x)?" + e + r"(?![0-9a-f])", low):
            return "STRONG", "A1 行首锚 #<entry>", "A1"
        # A2 md ATX 标题行，地址就在标题开头
        m2 = re.match(r"^\s{0,3}#{1,6}\s+(.*)$", low)
        if st is not None and is_md(st.rel) and m2:
            rest = m2.group(1)
            pos = rest.find(e)
            if 0 <= pos <= 12:
                pre = rest[:pos]
                if not re.search(r"[\u4e00-\u9fff]", pre) and len(pre.split()) <= 1:
                    return "STRONG", "A2 md 标题行以该 entry 为章节", "A2"
        # A3 文件头 meta 字段（代码文件不适用；多目标列表需显式分隔符）
        if st is not None and not st.code and lineno <= 14:
            multi = st.head_meta is not None and len(st.head_meta) > 2
            for m in META_FIELD.finditer(low):
                if m.group(2) != e or m.group(1) not in META_SUBJECT:
                    continue
                sep = re.search(r"([=:])", low[m.start():m.start(2)])
                if sep or not multi:
                    return "STRONG", f"A3 文件头 {m.group(1)}= 命名该 entry", "A3"
            for m in META_AT.finditer(low):
                if m.group(1) == e:
                    return "STRONG", "A3 文件头 meta 行以 @0x 标注该 entry", "A3"
        # A4 反汇编起点
        if st is not None and st.disasm_first_addr is not None \
                and st.disasm_linenos.get(lineno) == int(e, 16) == st.disasm_first_addr:
            return "STRONG", "A4 该 entry 是该文件第一条反汇编记录（该 dump 的起点）", "A4"
        # A5 函数体定义且是该文件第一个（只认反汇编/伪代码文件；脚本里的 FUN_xxx( 是实参）
        if st is not None and st.code and st.funcdef_first_line == lineno \
                and not ARGONLY_PAT.search(low) \
                and re.match(FUNCDEF_LINE.pattern + e + r"\s*\(", low):
            return "STRONG", "A5 函数体定义 FUN_<entry>( 是该文件第一个函数体定义", "A5"

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
                    return "MEDIUM", "M1 声明表主体列唯一一条记录且带属性字段", "M1"
                return "WEAK", "W2 表的关键列出现但同一 entry 在表里多行/无属性（流水表）", "W2"
    if re.search(r'"' + e + r'"\s*:\s*\{', low):
        return "MEDIUM", "M2 JSON 以该 entry 为 key 且 value 是带命名属性的对象", "M2"
    if re.search(r'"' + e + r'"\s*:\s*\[', low):
        return "WEAK", "W2 JSON key 的 value 纯地址数组（地址列表）", "W2"

    # ---- WEAK ----
    if argonly:
        return "WEAK", "W1 工具参数位（argv/subprocess/dump() 实参），hex 只是传参", "W1"
    if st is not None and lineno in st.disasm_linenos:
        return "WEAK", "W2 反汇编记录行的地址（指令流里的一个值）", "W2"
    if len(set(HEX_TOKEN.findall(low))) >= 3:
        return "WEAK", "W2 一行 >=3 个地址 token（地址表/调用图/引用表）", "W2"
    if re.match(r"^\s*(?:0x)?" + e + r"(?![0-9a-f])", low):
        return "WEAK", "W2 行首是该地址但非记录主体（地址列表行）", "W2"
    return "WEAK", "W3 正文/日志顺带提及", "W3"


def subject_entries(st, entry_set):
    """该文件里以「主体形态」出现的 791 entry 集合（被提及 ≠ 主体）。"""
    if st is None or st.bigfile:
        return set()
    cand = (st.meta_all | st.hash_all | st.md_all | st.funcdef) & entry_set
    if st.disasm_min is not None:
        d = "%08x" % st.disasm_min
        if d in entry_set:
            cand.add(d)
    return cand


def judge_row(entry, hits, structs, entry_set):
    ext = [h for h in hits if file_kind(h[0]) == "external"]
    sel = [h for h in hits if file_kind(h[0]) == "selfref"]

    per_file = collections.defaultdict(list)
    text_of = {}
    for rel, lineno, text in ext:
        per_file[rel].append(lineno)
        text_of[(rel, lineno)] = text

    file_forms = {}
    for rel, linenos in per_file.items():
        st = structs.get(rel)
        fmax, fwhy, fcode, fline = "NONE", "", "", 0
        for lineno in sorted(linenos):
            f, w, c = classify(entry, st, lineno, text_of[(rel, lineno)])
            if RANK[f] > RANK[fmax]:
                fmax, fwhy, fcode, fline = f, w, c, lineno
        file_forms[rel] = (fmax, fwhy, fcode, len(linenos), fline)

    row_form = "NONE"
    for f, _w, _c, _n, _l in file_forms.values():
        if RANK[f] > RANK[row_form]:
            row_form = f

    chosen = None
    dedicated = False
    n_other_subj = 0
    if row_form != "NONE":
        cands = [rel for rel, v in file_forms.items() if v[0] == row_form]

        def key(rel):
            named = 1 if entry in posix_base(rel).lower() else 0
            other = len(subject_entries(structs.get(rel), entry_set) - {entry})
            return (-named, other, rel)

        chosen = sorted(cands, key=key)[0]
        st = structs.get(chosen)
        n_other_subj = len(subject_entries(st, entry_set) - {entry})
        dedicated = (entry in posix_base(chosen).lower()) and n_other_subj == 0

    # 该文件自己的「主体 entry」：反汇编起点（dump 文件的主题）+ 文件内主体形态集合
    own_subject = None
    file_cat = "-"
    if chosen:
        stc = structs.get(chosen)
        if stc is not None and stc.disasm_min is not None:
            own_subject = "%08x" % stc.disasm_min
        ext_c = os.path.splitext(chosen)[1].lower()
        if stc is not None and stc.bigfile:
            file_cat = "huge"
        elif stc is not None and stc.has_header:
            file_cat = "table"
        elif stc is not None and stc.disasm_min is not None:
            file_cat = "disasm"
        elif ext_c in MD_EXT:
            file_cat = "prose_md"
        else:
            file_cat = "text"

    return dict(form=row_form, why=file_forms[chosen][1] if chosen else "无外部内容命中",
                fcode=file_forms[chosen][2] if chosen else "",
                file=chosen, lineno=file_forms[chosen][4] if chosen else 0,
                n_ext=len(ext), n_self=len(sel),
                n_files=len(per_file), dedicated=dedicated,
                n_other_subj=n_other_subj, own_subject=own_subject,
                file_cat=file_cat,
                files=sorted(per_file.keys()),
                file_forms={k: v[:1] for k, v in file_forms.items()})


def stage_judge(args, rows, repro):
    entry_set = {r["entry"].lower() for r in rows}
    hits_path = os.path.join(args.out, f"_hits_{args.scope}.tsv")
    if not os.path.exists(hits_path):
        log(f"[judge][FATAL] 缺 {hits_path}，先跑 --stage search")
        return None
    hits = load_hits(hits_path, entry_set,
                     short_map_of(entry_set) if args.scope == "wide" else None)

    # 结构缓存：只给真有命中的文件建
    all_files = {rel for hs in hits.values() for rel, _l, _t in hs}
    log(f"[judge] 命中文件 {len(all_files):,} 个，建结构（头 512KB）…")
    t0 = time.time()
    structs = {}
    for i, rel in enumerate(sorted(all_files), 1):
        structs[rel] = build_struct(args.lead, rel, entry_set)
        if i % 2000 == 0:
            log(f"        {i}/{len(all_files)} ({time.time()-t0:.1f}s)")
    log(f"[judge] 结构完成 {len(structs):,} 个 ({time.time()-t0:.1f}s)")

    judged = {}
    for r in rows:
        e = r["entry"].lower()
        judged[e] = judge_row(e, hits.get(e, []), structs, entry_set)

    # ---- 四个 scope 都写：675 / 116 ----
    zero_entries = [d["row"]["entry"].lower() for d in repro["zero"]]
    hit_entries = [d["row"]["entry"].lower() for d in repro["hit"]]

    def write_bucket(path, entries, hdr, extra_cols=None):
        cnt = collections.Counter()
        rowsout = []
        for e in entries:
            j = judged[e]
            b = TO_CTX[j["form"]]
            cnt[b] += 1
            r = next(x["row"] for x in repro["recs"] if x["row"]["entry"].lower() == e)
            top3 = "; ".join(j["files"][:3])
            anchor = (f"{j['file']}:{j['lineno']}" if j["file"] else "-")
            note = (f"锚点={anchor} [{j['fcode']}] {j['why']}；"
                    f"该文件类别={j['file_cat']}"
                    f"{'，文件自身反汇编起点=' + j['own_subject'] if j['own_subject'] else ''}；"
                    f"命中 {j['n_ext']} 处/在外 {j['n_files']} 个文件"
                    f"{'；台账自指 ' + str(j['n_self']) + ' 处已剔除' if j['n_self'] else ''}"
                    f"{'；同文件另有主体 791 entry ' + str(j['n_other_subj']) + ' 个（非专属）' if j['n_other_subj'] else '；逐 entry 专属'}")
            row = [r["entry"], r["subsystem"], r["name"]]
            if extra_cols:
                row += extra_cols(e, j)
            row += [b, str(j["n_files"]), top3 or "-", note]
            rowsout.append(row)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write("\t".join(hdr) + "\n")
            for row in rowsout:
                fh.write("\t".join(row) + "\n")
        return cnt, judged

    fh_by_e = {d["row"]["entry"].lower(): "Y" for d in repro["hit"]}

    # 权威口径（primary）写卡面要求的固定文件名；敏感性口径加 _wide 后缀，互不覆盖
    sfx = "" if args.scope == "primary" else "_" + args.scope
    cnt675, _ = write_bucket(os.path.join(args.out, f"buckets675{sfx}.tsv"),
                             zero_entries, HDR_BUCKETS)
    cnt116, _ = write_bucket(os.path.join(args.out, f"recheck116{sfx}.tsv"),
                             hit_entries, HDR_RECHECK,
                             extra_cols=lambda e, j: ["Y" if e in fh_by_e else "N"])

    log(f"[judge] scope={args.scope} 675 行四桶: " +
        "  ".join(f"{k}={cnt675.get(k,0)}" for k in
                  ("CTX_STRONG", "CTX_MEDIUM", "CTX_WEAK", "CTX_NONE")))
    log(f"[judge] scope={args.scope} 116 行四桶: " +
        "  ".join(f"{k}={cnt116.get(k,0)}" for k in
                  ("CTX_STRONG", "CTX_MEDIUM", "CTX_WEAK", "CTX_NONE")))

    strong_ded = sum(1 for e in zero_entries
                     if judged[e]["form"] == "STRONG" and judged[e]["dedicated"])
    log(f"[judge] 675 行中 STRONG 且逐 entry 专属 = {strong_ded}")
    strong_116 = [e for e in hit_entries if judged[e]["form"] == "STRONG"]
    strong_116_ded = [e for e in hit_entries
                      if judged[e]["form"] == "STRONG" and judged[e]["dedicated"]]
    log(f"[judge] 116 行中 STRONG = {len(strong_116)}，其中专属 = {len(strong_116_ded)}")

    # 共享文件诊断：哪些文件一次为很多行提供最强形态（区分"逐 entry 产物" vs "共享大表"）
    share_strong = collections.Counter()
    share_any = collections.Counter()
    for e in zero_entries:
        j = judged[e]
        if j["file"]:
            share_any[(j["file"], j["form"])] += 1
            if j["form"] == "STRONG":
                share_strong[j["file"]] += 1
    log("[judge] 675 行最强形态的 Top10 提供文件（文件, 形态 → 行数）:")
    for (f, form), n in share_any.most_common(10):
        log(f"        {n:4d} 行  {form:6s}  {f}")

    out = dict(scope=args.scope,
               n675=len(zero_entries), n116=len(hit_entries),
               cnt675=dict(cnt675), cnt116=dict(cnt116),
               strong675_dedicated=strong_ded,
               strong116=len(strong_116), strong116_dedicated=len(strong_116_ded),
               strong116_entries=sorted(strong_116),
               top_strong_files=[{"file": f, "rows": n} for f, n in share_strong.most_common(20)],
               top_any_files=[{"file": f, "form": form, "rows": n}
                              for (f, form), n in share_any.most_common(20)])

    # ---- STRONG 细分（"是不是逐 entry 的 dump" 与 "是他人文件里的一节"） ----
    cat = collections.Counter()
    fcode = collections.Counter()
    strong_detail = []
    for e in zero_entries:
        j = judged[e]
        if j["form"] != "STRONG":
            continue
        fcode[j["fcode"]] += 1
        own = j["own_subject"]
        is_own_start = (own is not None and own == e)
        tier = ("S1_own_dump" if is_own_start else
                "S2_section_in_other" if j["n_other_subj"] else "S3_shared_no_other")
        cat[tier] += 1
        strong_detail.append(dict(entry=e, code=j["fcode"], file=j["file"],
                                  lineno=j["lineno"], own_subject=own,
                                  n_other_subj=j["n_other_subj"],
                                  file_cat=j["file_cat"], tier=tier,
                                  why=j["why"]))
    log(f"[judge] 675 STRONG 形态码: {dict(fcode)}")
    log(f"[judge] 675 STRONG 细分: {dict(cat)}")
    log("[judge] STRONG 明细（前 20）：")
    for d in strong_detail[:20]:
        log(f"        {d['entry']} {d['code']:3s} {d['tier']:22s} "
            f"{d['file']}:{d['lineno']}")
    out["strong675_tiers"] = dict(cat)
    out["strong675_codes"] = dict(fcode)
    out["strong675_detail"] = strong_detail
    out["strong675_own_dump"] = [d["entry"] for d in strong_detail
                                 if d["tier"] == "S1_own_dump"]

    # ---- MEDIUM 提供文件集中度（共享大表 vs 分散） ----
    med_files = collections.Counter()
    for e in zero_entries:
        j = judged[e]
        if j["form"] == "MEDIUM" and j["file"]:
            med_files[j["file"]] += 1
    log("[judge] 675 MEDIUM 的提供文件（选中锚点文件）Top10：")
    for f, n in med_files.most_common(10):
        log(f"        {n:4d} 行  {f}")
    out["medium675_files"] = [{"file": f, "rows": n} for f, n in med_files.most_common(30)]
    out["medium675_nfiles"] = len(med_files)

    with open(os.path.join(args.out, f"_judge_{args.scope}.json"), "w",
              encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    return out


# --------------------------------------------------------------------------- #
# 阶段 sample：确定性抽样（≤18 行），输出上下文供人工核
# --------------------------------------------------------------------------- #
def pick(xs, k):
    """等距取 k 个（确定性）。"""
    if not xs:
        return []
    if len(xs) <= k:
        return list(xs)
    step = len(xs) / k
    return [xs[int(i * step)] for i in range(k)]


def stage_sample(args, rows, repro):
    jp = os.path.join(args.out, f"_judge_{args.scope}.json")
    if not os.path.exists(jp):
        log("[sample][FATAL] 先跑 --stage judge")
        return None
    entry_set = {r["entry"].lower() for r in rows}
    hits_path = os.path.join(args.out, f"_hits_{args.scope}.tsv")
    hits = load_hits(hits_path, entry_set,
                     short_map_of(entry_set) if args.scope == "wide" else None)

    # 重新判一遍（结构缓存不落盘，重算是秒级）
    all_files = {rel for hs in hits.values() for rel, _l, _t in hs}
    structs = {rel: build_struct(args.lead, rel, entry_set) for rel in sorted(all_files)}

    zero = [d["row"]["entry"].lower() for d in repro["zero"]]
    by_bucket = collections.defaultdict(list)
    for e in zero:
        j = judge_row(e, hits.get(e, []), structs, entry_set)
        by_bucket[j["form"]].append((e, j))

    # 确定性配额：STRONG 5 / MEDIUM 4 / WEAK 4 / NONE 2 = 15（≤18）
    quota = {"STRONG": 5, "MEDIUM": 4, "WEAK": 4, "NONE": 2}
    picked = []
    for form in ("STRONG", "MEDIUM", "WEAK", "NONE"):
        lst = sorted(by_bucket.get(form, []), key=lambda t: t[0])
        picked += [(form, e, j) for e, j in pick(lst, quota[form])]
    if len(picked) > 18:
        picked = picked[:18]
    log(f"[sample] 抽样 {len(picked)} 行（配额 STRONG5/MEDIUM4/WEAK4/NONE2）")

    rows_by_e = {r["entry"].lower(): r for r in rows}
    out_path = os.path.join(args.out, "sample18_draft.tsv")
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(HDR_SAMPLE) + "\n")
        for form, e, j in picked:
            r = rows_by_e[e]
            f = j["file"] or "-"
            # 取命中行上下文（20–40 字）：定位该 entry 在该文件的那一行
            ctx = ""
            if f != "-":
                for rel, ln, text in hits.get(e, []):
                    if rel == j["file"] and ln == j["lineno"]:
                        ctx = text.strip()
                        break
                ctx = ctx[:160]
            fh.write("\t".join([r["entry"], r["subsystem"], r["name"],
                                TO_CTX[form], f, str(j["lineno"]), ctx,
                                j["fcode"], j["why"], "", ""]) + "\n")
    log(f"[sample] → {out_path}")
    return dict(path=out_path, n=len(picked))


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    r14 = os.path.dirname(here)
    lead = os.path.dirname(r14)
    ap = argparse.ArgumentParser(description="675 行零候选的内容级四桶度量")
    ap.add_argument("--lead", default=lead)
    ap.add_argument("--resolve", default=os.path.join(r14, "R16_BASE", "evid", "resolve.tsv"))
    ap.add_argument("--out", default=here)
    ap.add_argument("--scope", default="primary", choices=["primary", "wide"])
    ap.add_argument("--stage", default="all",
                    choices=["all", "repro", "scale", "search", "judge", "sample"])
    args = ap.parse_args(argv)

    rows = load_rows(args.resolve)
    rows.sort(key=lambda r: r["entry"])
    log(f"[in ] lead={args.lead}")
    log(f"[in ] resolve={args.resolve}")
    log(f"[in ] R_TRACE_ONLY = {len(rows)}")

    if args.stage in ("all", "scale"):
        stage_scale(args)
    repro = None
    if args.stage in ("all", "repro", "judge", "sample"):
        repro = stage_repro(args, rows)
    if args.stage in ("all", "search"):
        stage_search(args, rows)
    if args.stage in ("all", "judge"):
        stage_judge(args, rows, repro)
    if args.stage in ("all", "sample"):
        stage_sample(args, rows, repro)
    return 0


if __name__ == "__main__":
    sys.exit(main())
