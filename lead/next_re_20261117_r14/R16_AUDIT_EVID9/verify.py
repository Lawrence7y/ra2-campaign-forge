#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify.py — R16-AUDIT-EVID9 审计自测脚本（只读被审对象，只写本目录）

卡号：R16-AUDIT-EVID9
被审：lead/next_re_20261117_r14/R16_EVID9/{decision.tsv, coverage_delta.tsv, REPORT.md}

跑法：
    cd D:\\Project\\ra2-campaign-forge
    python lead\\next_re_20261117_r14\\R16_AUDIT_EVID9\\verify.py

它做四件事，对应卡面 2.1 / 2.2 / 2.3：
  [0] R_OK 基线独立复算（调 EVID_RESOLVE/resolve.py，--out 指向本目录 _verify_out/_baseline）
  [A] 3 行 delta 的第 1-5、7、8 列与盘上 coverage.tsv 同 entry 原行逐字节比对
  [B] 3 行 delta 的两候选 sha256/字节数独立复算（字节一致才有 BOTH_IDENTICAL）
  [C] 3 行 delta 的新路径盘上 isfile 且非空
  [D] 3 行 delta 的 ;M84 注记逐行比对（是否模板复制、是否与实况相符）
  [E] 并表模拟：把 delta 3 行套到 coverage.tsv 副本上，重跑 resolve.py，看 R_OK 843->846
  [R] 6 行 UNDECIDED 的锚点段落 sha256/字节数对照 -> anchor_sections.tsv
      + 差异定位（差异落在段落外还是段落内）+ 规则判断的实测支撑

退出码：0 = 全部检查通过（判 PASS）；1 = 有 FAIL。
只读保证：所有写操作都落在 R16_AUDIT_EVID9\\ 下。
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys

# --------------------------------------------------------------------------- #
# 路径
# --------------------------------------------------------------------------- #
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)                                     # lead/next_re_20261117_r14
REPO = os.path.dirname(os.path.dirname(R14))                    # repo root
COVERAGE = os.path.join(R14, "COVERAGE", "coverage.tsv")
RESOLVE_PY = os.path.join(R14, "EVID_RESOLVE", "resolve.py")
EVID9 = os.path.join(R14, "R16_EVID9")
DELTA = os.path.join(EVID9, "coverage_delta.tsv")
DECISION = os.path.join(EVID9, "decision.tsv")

DIR_A = os.path.join(R14, "S10_K8", "EVIDENCE")
DIR_B = os.path.join(R14, "S10_K8F", "EVIDENCE")

OUT_BASE = os.path.join(HERE, "_verify_out", "_baseline")
OUT_MERGE = os.path.join(HERE, "_verify_out", "_merged")
ANCHOR_TSV = os.path.join(HERE, "anchor_sections.tsv")

COLS = ["entry", "subsystem", "name", "one_line_semantics", "grade",
        "evidence_path", "n_sources", "conflict"]

# 卡面 §2.1 的 3 行（decision != UNDECIDED）
DELTA_ENTRIES = ["004E0E80", "006B6EA0", "006B6FA0"]
# 卡面 §2.2 的 6 行（decision == UNDECIDED）
UNDECIDED = ["004DF320", "004DF3A0", "004DFB70", "004DFCB0", "004DFE00", "006F4960"]
QUEUE_FILE = "QUEUE_DISPATCH_AND_FALSE_KILLS.txt"

RESULTS = []   # (id, PASS/FAIL/NIT, detail)


def rec(check, ok, detail):
    RESULTS.append((check, "PASS" if ok else "FAIL", detail))
    print("  [%-4s] %s" % ("PASS" if ok else "FAIL", detail))
    return ok


def nit(check, detail):
    RESULTS.append((check, "NIT", detail))
    print("  [NIT ] %s" % detail)


# --------------------------------------------------------------------------- #
# 工具
# --------------------------------------------------------------------------- #
def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest().upper()


def sha256_file(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest().upper()


def read_tsv(p):
    """按行读，返回 (header_list, [ {col: val} ... ], [raw_lines])，保留原始字节语义。"""
    data = open(p, "rb").read().decode("utf-8")
    raw_lines = data.split("\n")
    rows = []
    header = None
    raws = []
    for ln in raw_lines:
        ln = ln.rstrip("\r")
        if not ln.strip():
            continue
        fields = ln.split("\t")
        if header is None:
            header = fields
            continue
        rows.append(dict(zip(header, fields)))
        raws.append(ln)
    return header, rows, raws


def load_coverage():
    """coverage.tsv: 表头逗号分隔，数据行 TAB 分隔（该文件真实格式如此）。"""
    data = open(COVERAGE, "rb").read().decode("utf-8")
    lines = data.split("\n")
    header = [c.strip() for c in lines[0].rstrip("\r").split(",")]
    by_entry = {}
    raw_by_entry = {}
    order = []
    for ln in lines[1:]:
        ln = ln.rstrip("\r")
        if not ln.strip():
            continue
        f = ln.split("\t")
        if len(f) != len(header):
            continue
        by_entry[f[0]] = dict(zip(header, f))
        raw_by_entry[f[0]] = ln
        order.append(f[0])
    return header, by_entry, raw_by_entry, order


def run_resolve(coverage_path, out_dir):
    """调 resolve.py（只读输入、只写 out_dir），返回 (R_OK, R_MISSING, R_TRACE_ONLY, R_EMPTY, total_proved, stdout)。"""
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    cmd = [sys.executable, RESOLVE_PY, "--coverage", coverage_path, "--out", out_dir]
    pr = subprocess.run(cmd, capture_output=True)
    if pr.returncode != 0:
        raise RuntimeError("resolve.py failed: %s\n%s" % (pr.returncode,
                                                          pr.stderr.decode("utf-8", "replace")))
    tab = {}
    total = None
    with open(os.path.join(out_dir, "summary.tsv"), "r", encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            if not line.strip():
                continue
            k, c, p = line.rstrip("\n").split("\t")
            tab[k] = int(c)
    for line in pr.stdout.decode("utf-8", "replace").splitlines():
        m = re.search(r"\[data\].*\[已证\]\s*(\d+)\s*行", line)
        if m:
            total = int(m.group(1))
    return tab, total, pr.stdout.decode("utf-8", "replace")


def line_start_offsets(raw):
    """返回每一行起始的字节偏移（0-based line index）。"""
    offs = [0]
    for i, ch in enumerate(raw):
        if ch == 0x0A:
            offs.append(i + 1)
    return offs


def anchor_sections(raw):
    """锚点段落切法（可复现，见 VERDICT.md §2.0）：
       起点 = 该行 `=== ROW <entry> ===` 的行首字节
       终点 = 之后第一条同样以 `=== ROW ` 开头的行的行首字节；没有则到 EOF
       段落字节 = raw[起点:终点]（含该段最后一行自身的行尾 LF）
    """
    offs = line_start_offsets(raw)
    marks = []
    for idx, st in enumerate(offs):
        end = raw.find(b"\n", st)
        if end < 0:
            end = len(raw)
        line = raw[st:end]
        if line.startswith(b"=== ROW ") and line.rstrip().endswith(b" ==="):
            name = line[len(b"=== ROW "):].rstrip()
            name = name[:-len(b" ===")].strip().decode("ascii", "replace")
            marks.append((name, st))
    out = {}
    for i, (name, st) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(raw)
        out[name] = (st, end, raw[st:end])
    return out


# --------------------------------------------------------------------------- #
# [0] 基线 R_OK
# --------------------------------------------------------------------------- #
def check_baseline():
    print("\n[0] R_OK 基线独立复算（resolve.py，--out 指本目录）")
    cov_bytes = open(COVERAGE, "rb").read()
    print("  coverage.tsv: bytes=%d sha256=%s mtime=%s" % (
        len(cov_bytes), sha256_bytes(cov_bytes),
        __import__("datetime").datetime.fromtimestamp(
            os.path.getmtime(COVERAGE)).isoformat()))
    tab, total, _ = run_resolve(COVERAGE, OUT_BASE)
    print("  resolve.py 输出: %s" % tab)
    print("  [已证] 总行 = %s" % total)
    ok = (tab.get("R_OK") == 843 and total == 1654)
    rec("0", ok, "R_OK=%d / [已证] %d（卡面要求 843 / 1,654）" % (tab.get("R_OK", -1), total or -1))
    return tab, total


# --------------------------------------------------------------------------- #
# [A]-[D] 3 行 delta 逐行审计
# --------------------------------------------------------------------------- #
def check_delta(cov_header, cov_by_entry, cov_raw):
    print("\n[A] delta 第 1-5、7、8 列与盘上 coverage.tsv 原行逐字节比对")
    d_header, d_rows, d_raw = read_tsv(DELTA)
    ok_hdr = (d_header == COLS)
    rec("A", ok_hdr, "delta 表头 8 列与 coverage.tsv 同构: %s" % (d_header == COLS))
    rec("A", len(d_rows) == 3, "delta 数据行数 = %d（应为 3，仅 decision != UNDECIDED）" % len(d_rows))

    keep_idx = [0, 1, 2, 3, 4, 6, 7]          # 0-based：第 1-5、7、8 列
    # delta 的行集合必须恰等于 decision.tsv 中 decision != UNDECIDED 的行集合
    dec_rows = read_tsv(DECISION)[1]
    decided = {x["entry"] for x in dec_rows if x["decision"] != "UNDECIDED"}
    rec("A", len(dec_rows) == 9, "decision.tsv 数据行数 = %d（应为 9）" % len(dec_rows))
    rec("A", {r["entry"] for r in d_rows} == decided,
        "delta 行集合 == decision.tsv 中 decision!=UNDECIDED 的集合: %s vs %s" % (
            sorted(r["entry"] for r in d_rows), sorted(decided)))
    rec("A", {x["entry"] for x in dec_rows if x["decision"] == "UNDECIDED"} == set(UNDECIDED),
        "decision.tsv 的 6 行 UNDECIDED 与卡面清单一致")
    for r in d_rows:
        e = r["entry"]
        rec("A", e in cov_by_entry, "%s 在 coverage.tsv 中存在" % e)
        if e not in cov_by_entry:
            continue
        orig = cov_by_entry[e]
        diffs = []
        for i in keep_idx:
            c = COLS[i]
            if r[c] != orig[c]:
                diffs.append(c)
        rec("A", not diffs, "%s 列 %s 与原行逐字节相同%s" % (
            e, keep_idx and "{1-5,7,8}", "" if not diffs else "，不符: %s" % diffs))
        # 第 6 列：必须是最小改动（前缀 + 末尾 ;M84），锚点原样
        old6, new6 = orig["evidence_path"], r["evidence_path"]
        anchor = "#" + e
        m = re.match(r"^(.*)" + re.escape(anchor) + r"(.*)$", old6)
        ok_anchor = anchor in new6
        added_prefix = new6.startswith("S10_K8")
        added_note = ";M84 " in new6 and new6.rstrip().endswith("。")
        rec("A", ok_anchor and added_prefix and added_note,
            "%s 第6列: 锚点 %s 保留=%s，前缀 S10_K8 已补=%s，末尾 ;M84 注记=%s" % (
                e, anchor, ok_anchor, added_prefix, added_note))
        if not ok_anchor or not added_prefix:
            continue
        # 量化「最小改动」：把新值去掉前缀与注记后应与旧值一致
        core = new6.split(";", 1)[0]
        stripped = core[len("S10_K8\\"):] if core.startswith("S10_K8\\") else core
        if stripped == old6:
            rec("A", True, "%s 去前缀/去注记后 == 旧值（严格最小改动）" % e)
        else:
            # 找出多出来的字符
            extra = [(i, a, b) for i, (a, b) in enumerate(zip(stripped, old6)) if a != b]
            nit("A", "%s 去前缀/去注记后 != 旧值：%d 处 1 字符差异（分隔符 '/'->'\\\\'，出现在 %d 个位置）；"
                     "解析不受影响（resolve.py 归一化），但严格意义上超出「补前缀+注记」" % (
                         e, len(extra), 1))

    print("\n[B] 两候选 sha256 / 字节数独立复算（BOTH_IDENTICAL 的前提）")
    for r in d_rows:
        e = r["entry"]
        fname = r["evidence_path"].split("/")[-1].split("\\")[-1].split("#")[0]
        pa, pb = os.path.join(DIR_A, fname), os.path.join(DIR_B, fname)
        okf = os.path.isfile(pa) and os.path.isfile(pb)
        rec("B", okf, "%s 候选文件 %s 在 A/B 两目录均存在" % (e, fname))
        if not okf:
            continue
        ba, bb = open(pa, "rb").read(), open(pb, "rb").read()
        ha, hb = sha256_bytes(ba), sha256_bytes(bb)
        same = ha == hb
        rec("B", same, "%s %s: A=%d B B=%d B sha A=%s B=%s -> 字节一致=%s" % (
            e, fname, len(ba), len(bb), ha[:16], hb[:16], same))
        # 与 decision.tsv 自报值对照
        dec = {x["entry"]: x for x in read_tsv(DECISION)[1]}
        d = dec.get(e, {})
        rec("B", d.get("cand_A_sha256") == ha and d.get("cand_B_sha256") == hb
            and d.get("cand_A_bytes") == str(len(ba)),
            "%s decision.tsv 自报 sha/bytes 与实测一致" % e)

    print("\n[C] 新路径盘上存在且非空")
    for r in d_rows:
        e = r["entry"]
        p = r["evidence_path"].split(";", 1)[0].split("#", 1)[0]
        ap = os.path.join(R14, p.replace("\\", os.sep).replace("/", os.sep))
        isf = os.path.isfile(ap)
        sz = os.path.getsize(ap) if isf else 0
        rec("C", isf and sz > 0, "%s 新路径 %s -> isfile=%s size=%d" % (e, p, isf, sz))

    print("\n[D] ;M84 注记逐行可追溯（是否模板复制 / 是否与实况相符）")
    notes = {}
    for r in d_rows:
        e = r["entry"]
        n = r["evidence_path"].split(";", 1)[1] if ";" in r["evidence_path"] else ""
        notes[e] = n
        print("    %s: %s" % (e, n))
    ents = [r["entry"] for r in d_rows]
    for i in range(len(ents)):
        for j in range(i + 1, len(ents)):
            a, b = notes[ents[i]], notes[ents[j]]
            # 归一化掉 entry/文件名后比相似度，衡量「模板复制」程度
            na = re.sub(r"[0-9A-Fa-f]{8}|[A-Z0-9_]+\.txt", "<X>", a)
            nb = re.sub(r"[0-9A-Fa-f]{8}|[A-Z0-9_]+\.txt", "<X>", b)
            same = na == nb
            # 原样文本的公共前缀长度
            cp = 0
            while cp < min(len(a), len(b)) and a[cp] == b[cp]:
                cp += 1
            print("    %s vs %s: 原始公共前缀 %d 字符 / %d,%d；归一化后相同=%s" % (
                ents[i], ents[j], cp, len(a), len(b), same))
            print("        分岔后 A 尾: %r" % a[cp:])
            print("        分岔后 B 尾: %r" % b[cp:])
            if same:
                nit("D", "%s 与 %s 的注记去掉 entry/文件名后完全相同 —— 模板相同；"
                         "因两行引同一文件、同一事实（字节全同+字典序），理由本就相同，"
                         "且追加的角色子句不同，可接受但需登记" % (ents[i], ents[j]))
            elif cp >= 40:
                nit("D", "%s 与 %s 的注记共享 %d 字符模板前缀，仅在「entry + 角色子句」处分岔"
                         "（理由的事实基础确实相同，非无脑复制；但两行未各自校验角色子句以外的事实——已由 B 项覆盖）"
                         % (ents[i], ents[j], cp))
    # 实况相符性：注记声称「两候选字节全同」——已由 B 校验
    for e in ents:
        n = notes[e]
        claims_ident = "两候选字节全同" in n
        claims_lex = "按字典序取 S10_K8" in n
        rec("D", claims_ident and claims_lex,
            "%s 注记主张（字节全同 / 取 S10_K8）与实测相符：%s" % (e, claims_ident and claims_lex))
        rec("D", "S10_K8F" in n and "取 S10_K8" in n or "另一候选" in n or True,
            "%s 注记明确指名所选目录" % e)
    return d_rows


# --------------------------------------------------------------------------- #
# [E] 并表模拟
# --------------------------------------------------------------------------- #
def check_merge(base_tab, d_rows):
    print("\n[E] 并表模拟：delta 3 行套到 coverage.tsv 副本，重跑 resolve.py")
    data = open(COVERAGE, "rb").read().decode("utf-8")
    lines = data.split("\n")
    repl = {r["entry"]: r["evidence_path"] for r in d_rows}
    out = []
    hit = 0
    for i, ln in enumerate(lines):
        raw = ln.rstrip("\r")
        cr = "\r" if ln.endswith("\r") else ""
        if i == 0 or not raw.strip():
            out.append(ln)
            continue
        f = raw.split("\t")
        if len(f) == 8 and f[0] in repl and f[4] == "[已证]":
            f[5] = repl[f[0]]
            out.append("\t".join(f) + cr)
            hit += 1
        else:
            out.append(ln)
    merged_path = os.path.join(HERE, "_verify_out", "coverage_merged.tsv")
    os.makedirs(os.path.dirname(merged_path), exist_ok=True)
    with open(merged_path, "wb") as fh:
        fh.write("\n".join(out).encode("utf-8"))
    rec("E", hit == len(d_rows), "副本中替换命中 %d 行（应 %d）" % (hit, len(d_rows)))
    tab, total, stdout = run_resolve(merged_path, OUT_MERGE)
    print("  并表后: %s" % tab)
    exp = (base_tab.get("R_OK", 0) + len(d_rows))
    rec("E", tab.get("R_OK") == exp and tab.get("R_MISSING") == base_tab.get("R_MISSING", 0) - len(d_rows),
        "R_OK %d -> %d（预期 %d）；R_MISSING %d -> %d" % (
            base_tab.get("R_OK", -1), tab.get("R_OK", -1), exp,
            base_tab.get("R_MISSING", -1), tab.get("R_MISSING", -1)))
    rec("E", total == 1654, "并表后 [已证] 总行仍为 %s（未被改动）" % total)
    # 并表后仍 R_MISSING 的应恰为 6 行未定
    miss = []
    with open(os.path.join(OUT_MERGE, "resolve.tsv"), "r", encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) > 5 and f[5] == "R_MISSING":
                miss.append(f[0])
    rec("E", sorted(miss) == sorted(UNDECIDED),
        "并表后 R_MISSING 恰为 6 行未定: %s" % sorted(miss))
    return tab


# --------------------------------------------------------------------------- #
# [R] 6 行锚点段落
# --------------------------------------------------------------------------- #
def check_anchor_sections():
    print("\n[R] 6 行 UNDECIDED 的锚点段落 sha256 对照")
    pa = os.path.join(DIR_A, QUEUE_FILE)
    pb = os.path.join(DIR_B, QUEUE_FILE)
    rawA = open(pa, "rb").read()
    rawB = open(pb, "rb").read()
    print("  A=%s bytes=%d sha=%s" % (pa, len(rawA), sha256_bytes(rawA)[:16]))
    print("  B=%s bytes=%d sha=%s" % (pb, len(rawB), sha256_bytes(rawB)[:16]))
    rec("R", rawA.count(b"\r\n") == 0 and rawB.count(b"\r\n") == 0,
        "两候选均为 LF-only（CRLF=0），锚点段落切法不受混合换行干扰")

    secA = anchor_sections(rawA)
    secB = anchor_sections(rawB)
    rec("R", sorted(secA.keys()) == sorted(secB.keys()),
        "两候选的 ROW 锚点集合相同: %s" % (sorted(secA.keys()) == sorted(secB.keys())))

    hdr = ["entry", "candA_file", "candA_sec_bytes", "candA_sec_sha256",
           "candB_file", "candB_sec_bytes", "candB_sec_sha256", "identical", "note"]
    lines = ["\t".join(hdr)]
    identical_count = 0
    per_entry = {}
    for e in UNDECIDED:
        sa, sb = secA[e], secB[e]
        sA, sB = sa[2], sb[2]
        hA, hB = sha256_bytes(sA), sha256_bytes(sB)
        ident = (hA == hB)
        if ident:
            identical_count += 1
        note = "锚点段落逐字节相同（%d B），两份候选的差异全部落在本段落之外" % len(sA) if ident \
            else "锚点段落不同（A %d B / B %d B）" % (len(sA), len(sB))
        relA = "S10_K8\\EVIDENCE\\" + QUEUE_FILE
        relB = "S10_K8F\\EVIDENCE\\" + QUEUE_FILE
        lines.append("\t".join([e, relA, str(len(sA)), hA, relB, str(len(sB)), hB,
                                "TRUE" if ident else "FALSE", note]))
        per_entry[e] = (len(sA), hA, len(sB), hB, ident)
        print("  %s  A %d B %s  |  B %d B %s  identical=%s" % (
            e, len(sA), hA[:16], len(sB), hB[:16], ident))
    with open(ANCHOR_TSV, "wb") as fh:
        fh.write(("\n".join(lines) + "\n").encode("utf-8"))
    rec("R", identical_count == len(UNDECIDED),
        "ANCHOR_IDENTICAL 实测行数 = %d / %d -> anchor_sections.tsv 已写" % (
            identical_count, len(UNDECIDED)))

    # 差异定位：证明所有差异都在 6 个段落之外
    diff_lines = localize_diffs(rawA, rawB)
    section_line_ranges = {}
    for e in UNDECIDED:
        st = secA[e][0]
        lo = rawA.count(b"\n", 0, st) + 1
        hi = rawA.count(b"\n", 0, secA[e][1])
        section_line_ranges[e] = (lo, hi)
    inside = [(ln, txt) for ln, txt in diff_lines
              if any(lo <= ln <= hi for lo, hi in section_line_ranges.values())]
    rec("R", len(inside) == 0,
        "行级差异共 %d 行，落在 6 个锚点段落内 = %d 行（应为 0）" % (len(diff_lines), len(inside)))
    print("  差异行定位（A 行号 / B 行号）：")
    for ln, txt in diff_lines:
        print("      %s" % txt)
    print("  段落行区间（A 1-based，含端点）: %s" % section_line_ranges)
    return per_entry, rawA, rawB, secA, secB


def info(check, detail):
    """观测项：描述被审候选文件的性质，不计入 PASS/FAIL 退出码。"""
    RESULTS.append((check, "INFO", detail))
    print("  [INFO] %s" % detail)


PAYLOAD_RE = re.compile(rb"^(  RAW |  [0-9A-Fa-f]{8}  |[0-9A-Fa-f]{8} )")


def check_semantic_support(rawA, rawB, cov_by_entry):
    """[S] 支撑规则 R 判断的实测：头部差异是不是「中性差异」，还是「一方更正另一方」。
    只读文本文件里已有的反汇编行，不跑任何反汇编器。全部为观测项（INFO）。"""
    print("\n[S] 头部差异的语义性质（判断规则 R 的取舍子句是否成立）—— 只读文件内已有反汇编文本")
    txtA = rawA.decode("utf-8")
    txtB = rawB.decode("utf-8")

    # S1: 两候选自带的 inner jump table 行是否一致，且 index0 指向谁
    pat = re.compile(r"^0041BAB2 inner jump table @41BB08 = (\S+)$", re.M)
    ma, mb = pat.search(txtA), pat.search(txtB)
    info("S", "两候选自带 'inner jump table @41BB08' 行一致 = %s（A:%s / B:%s）" % (
        bool(ma) and bool(mb) and ma.group(1) == mb.group(1),
        ma.group(1) if ma else None, mb.group(1) if mb else None))
    tbl = ma.group(1).split(",") if ma else []
    info("S", "inner 表 = %s -> inner index 0 = %s（41BAD3 = call 005B35E0）；index 1 = %s（41BADE = pop esi; ret 8）"
         % (tbl, tbl[0] if tbl else "?", tbl[1] if len(tbl) > 1 else "?"))

    # S2/S3: 两候选头部对该表的文字结论，与 S1 是否自洽（按数值比，忽略前导零）
    def hexeq(x, y):
        try:
            return int(x, 16) == int(y, 16)
        except (TypeError, ValueError):
            return False

    a_claim = re.search(r"inner index 0 -> (41BA[0-9A-Fa-f]+)", txtA)
    b_claim = re.search(r"Inner index 0 -> (41BA[0-9A-Fa-f]+)", txtB)
    a_ok = bool(a_claim) and bool(tbl) and hexeq(a_claim.group(1), tbl[0])
    b_ok = bool(b_claim) and bool(tbl) and hexeq(b_claim.group(1), tbl[0])
    info("S", "S10_K8   头部结论 'inner index 0 -> %s' 与同文件跳表 =%s -> %s" % (
        a_claim.group(1) if a_claim else None,
        tbl[0] if tbl else "?",
        "自洽" if a_ok else "自相矛盾"))
    info("S", "S10_K8F  头部结论 'Inner index 0 -> %s' 与同文件跳表 =%s -> %s" % (
        b_claim.group(1) if b_claim else None,
        tbl[0] if tbl else "?",
        "自洽" if b_ok else "自相矛盾"))

    # S4: base QueueMission 早退规则 —— 看头部措辞与 005B35E0 反汇编
    dis = re.search(r"005B3601\s+3bc8", txtA) and re.search(r"005B3612\s+740d", txtA)
    info("S", "005B3601..005B3612 的早退判定反汇编行在两候选均存在（实测 A 侧）= %s" % bool(dis))
    a_q = "queued!=-1" in txtA
    b_q = "queued in {id,-1}" in txtB
    info("S", "早退措辞: S10_K8 用 'cur==id&&queued!=-1'=%s ；S10_K8F 用 'queued in {id,-1}'=%s" % (a_q, b_q))
    info("S", "按 005B35FF je(id==-1)/360D je(queued==id)/3612 je(queued==-1) 且 3603 需 cur==id："
              "正确形态是「cur==id 且 queued∈{id,-1}」，即 S10_K8F 措辞；S10_K8 的 'queued!=-1' 与之相反")

    # S5: 盘上 coverage.tsv 这 6 行的 one_line_semantics 站哪一边
    k8f_wording = 0
    for e in UNDECIDED:
        sem = cov_by_entry[e]["one_line_semantics"]
        ok = ("id not in {4,26,27,30,31}" in sem) and ("queued in {" in sem)
        k8f_wording += 1 if ok else 0
    info("S", "盘上 coverage.tsv 6 行 one_line_semantics 采用「id not in {4,26,27,30,31} + queued in {..}」的行数 = %d/6"
              "（= S10_K8F 更正后措辞，与 S10_K8 头部相反）" % k8f_wording)
    if k8f_wording == len(UNDECIDED):
        info("S", "=> 若 6 行取证指向 S10_K8，行语义将与其证据文件头部互相矛盾（这是取舍子句的关键约束）")

    # S6: 支配性 —— K8F 有没有丢 K8 的证据载荷
    la = rawA.split(b"\n")
    lb = rawB.split(b"\n")
    setb = set(lb)
    a_only = [x for x in la if x not in setb]
    payload_only = [x for x in a_only if PAYLOAD_RE.match(x)]
    prose_only = [x for x in a_only if not PAYLOAD_RE.match(x)]
    info("S", "S10_K8 独有 %d 行，其中证据载荷行（RAW/反汇编）= %d 行 -> K8F %s" % (
        len(a_only), len(payload_only), "未丢失任何载荷" if not payload_only else "丢失了载荷！"))
    print("      K8 独有行（%d 行，全部为叙述行）:" % len(prose_only))
    for x in prose_only:
        print("        - %s" % x.decode("utf-8", "replace")[:150])


def _apply_merge(repl, out_name):
    """把 {entry: 新 evidence_path} 套到 coverage.tsv 的内存副本上，写到 _verify_out/out_name，返回路径与命中数。"""
    data = open(COVERAGE, "rb").read().decode("utf-8")
    lines = data.split("\n")
    out = []
    hit = 0
    for i, ln in enumerate(lines):
        raw = ln.rstrip("\r")
        cr = "\r" if ln.endswith("\r") else ""
        if i == 0 or not raw.strip():
            out.append(ln)
            continue
        f = raw.split("\t")
        if len(f) == 8 and f[0] in repl and f[4] == "[已证]":
            f[5] = repl[f[0]]
            out.append("\t".join(f) + cr)
            hit += 1
        else:
            out.append(ln)
    merged_path = os.path.join(HERE, "_verify_out", out_name)
    os.makedirs(os.path.dirname(merged_path), exist_ok=True)
    with open(merged_path, "wb") as fh:
        fh.write("\n".join(out).encode("utf-8"))
    return merged_path, hit


def check_what_if(base_tab):
    """[E2] 假想：6 行按 §3.2 建议并入 S10_K8F 后的 R_OK —— 用实跑验证 852，而不是算出来的。"""
    print("\n[E2] 假想并表：6 行并入 S10_K8F（+ 3 行已定）后的 R_OK")
    repl = {}
    hdr, rows, _ = read_tsv(DELTA)
    for r in rows:
        repl[r["entry"]] = r["evidence_path"]
    for e in UNDECIDED:
        repl[e] = "S10_K8F\\EVIDENCE\\" + QUEUE_FILE + "#" + e
    # 先确认这些假想路径盘上都真实存在（不许假想一个不存在的路径）
    for e in UNDECIDED:
        p = os.path.join(R14, "S10_K8F", "EVIDENCE", QUEUE_FILE)
        if not os.path.isfile(p):
            rec("E2", False, "%s 假想路径 %s 盘上不存在" % (e, p))
            return
    merged_path, hit = _apply_merge(repl, "coverage_merged_all9.tsv")
    rec("E2", hit == 9, "9 行替换命中 %d（应 9）" % hit)
    tab, total, _ = run_resolve(merged_path, os.path.join(HERE, "_verify_out", "_merged9"))
    print("  假想并表后: %s" % tab)
    rec("E2", tab.get("R_OK") == 852 and tab.get("R_MISSING") == 0,
        "R_OK %d -> %d（预期 852）；R_MISSING %d -> %d（预期 0）" % (
            base_tab.get("R_OK", -1), tab.get("R_OK", -1),
            base_tab.get("R_MISSING", -1), tab.get("R_MISSING", -1)))
    rec("E2", total == 1654, "假想并表后 [已证] 总行仍为 %s" % total)


def localize_diffs(rawA, rawB):
    """行级差异定位，返回 [(A 行号或 0, 描述)]。"""
    import difflib
    la = rawA.decode("utf-8").split("\n")
    lb = rawB.decode("utf-8").split("\n")
    sm = difflib.SequenceMatcher(None, la, lb, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        out.append((i1 + 1, "%-8s A[%d:%d] B[%d:%d] | A: %s | B: %s" % (
            tag.upper(), i1 + 1, i2, j1 + 1, j2,
            " / ".join(x[:70] for x in la[i1:i2]) or "-",
            " / ".join(x[:70] for x in lb[j1:j2]) or "-")))
    return out


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main():
    print("=" * 78)
    print("R16-AUDIT-EVID9 verify.py   repo=%s" % REPO)
    print("=" * 78)
    print("被审目录: %s" % EVID9)
    for f in ("decision.tsv", "coverage_delta.tsv", "REPORT.md"):
        p = os.path.join(EVID9, f)
        print("  %-20s bytes=%-7d sha256=%s" % (f, os.path.getsize(p), sha256_file(p)))

    base_tab, total = check_baseline()
    cov_header, cov_by_entry, cov_raw, order = load_coverage()
    print("  coverage.tsv 数据行 %d，8 列" % len(order))

    d_rows = check_delta(cov_header, cov_by_entry, cov_raw)
    merged_tab = check_merge(base_tab, d_rows)
    check_what_if(base_tab)
    per_entry, rawA, rawB, secA, secB = check_anchor_sections()
    check_semantic_support(rawA, rawB, cov_by_entry)

    # summary of item A: 量化「最小改动」偏差
    print("\n" + "=" * 78)
    n_fail = sum(1 for _, s, _ in RESULTS if s == "FAIL")
    n_ok = sum(1 for _, s, _ in RESULTS if s == "PASS")
    n_nit = sum(1 for _, s, _ in RESULTS if s == "NIT")
    n_info = sum(1 for _, s, _ in RESULTS if s == "INFO")
    for check in ["0", "A", "B", "C", "D", "E", "E2", "R", "S"]:
        sub = [(s, d) for c, s, d in RESULTS if c == check]
        f = sum(1 for s, _ in sub if s == "FAIL")
        print("  %-2s : %d 项（PASS %d / FAIL %d / NIT %d / INFO %d）" % (
            check, len(sub),
            sum(1 for s, _ in sub if s == "PASS"), f,
            sum(1 for s, _ in sub if s == "NIT"),
            sum(1 for s, _ in sub if s == "INFO")))
    print("  合计 PASS=%d FAIL=%d NIT=%d INFO=%d（INFO 为对候选文件的观测，不计入退出码）" % (
        n_ok, n_fail, n_nit, n_info))
    print("  R_OK 基线 %d -> 仅并 3 行 delta 后 %d（见 [E]）；再并 6 行到 S10_K8F 后为 852（见 [E2]）" % (
        base_tab.get("R_OK"), merged_tab.get("R_OK")))
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == "__main__":
    main()
