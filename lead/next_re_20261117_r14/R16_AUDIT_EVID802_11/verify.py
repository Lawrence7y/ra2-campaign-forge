#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify.py — R16-AUDIT-EVID802-11 审计复跑脚本（只读被审对象，只写本目录）

用法：
  python verify.py                # 全量：A/B/C/D 四项 + 产出 check11.tsv

边界：
  - 读 lead/next_re_20261117_r14/R16_EVID802_11/（被审 delta，只读）
  - 读 lead/next_re_20261117_r14/COVERAGE/coverage.tsv（盘上台账，只读）
  - 读 lead/ 全树 PROOF_<entry>.txt（只读）
  - 只写 lead/next_re_20261117_r14/R16_AUDIT_EVID802_11/（本目录）
"""
from __future__ import annotations

import hashlib
import io
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)                       # ...\lead\next_re_20261117_r14
LEAD = os.path.dirname(R14)                       # ...\lead
REPO = os.path.dirname(LEAD)

SRC_DIR = os.path.join(R14, "R16_EVID802_11")
COVERAGE = os.path.join(R14, "COVERAGE", "coverage.tsv")
DELTA = os.path.join(SRC_DIR, "coverage_delta.tsv")
FIELDS = os.path.join(SRC_DIR, "fields.tsv")

ENTRIES = ["0045A560", "0045A610", "0053C6A0", "005514B0", "00551560",
           "00557090", "00557140", "006B1850", "006B1900", "006B8660",
           "006B8710"]

COLS = ["entry", "subsystem", "name", "one_line_semantics", "grade",
        "evidence_path", "n_sources", "conflict"]

SEC_RE = re.compile(r"^([①②③④])\s", re.M)


# --------------------------------------------------------------------------- #
# 读取
# --------------------------------------------------------------------------- #
def read_text(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def load_tsv_rows(path):
    """按行读 TSV，首行为表头。返回 (header, [(lineno, fields)])。"""
    text = read_text(path)
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    header = [c.strip() for c in lines[0].rstrip("\r").split("\t")]
    rows = []
    for i, raw in enumerate(lines[1:], start=2):
        raw = raw.rstrip("\r")
        if not raw.strip():
            continue
        rows.append((i, raw.split("\t")))
    return header, rows


def load_coverage():
    """coverage.tsv 真实格式：表头逗号分隔，数据行 Tab 分隔。"""
    text = read_text(COVERAGE)
    lines = text.split("\n")
    header = [c.strip() for c in lines[0].rstrip("\r").split(",")]
    rows = {}
    dup = []
    for i, raw in enumerate(lines[1:], start=2):
        raw = raw.rstrip("\r")
        if not raw.strip():
            continue
        f = raw.split("\t")
        if len(f) != len(header):
            continue
        e = f[header.index("entry")]
        if e in rows:
            dup.append(e)
        rows[e] = (i, f)
    return header, rows, dup


# --------------------------------------------------------------------------- #
# B · PROOF 文件搜索与结构判定
# --------------------------------------------------------------------------- #
def find_proof_files():
    """在 lead 全树搜 PROOF_<entry>.txt（大小写不敏感，文件名精确匹配）。"""
    want = {f"proof_{e}.txt".lower(): e for e in ENTRIES}
    hits = {e: [] for e in ENTRIES}
    for dirpath, _dirnames, filenames in os.walk(LEAD):
        for fn in filenames:
            e = want.get(fn.lower())
            if e is not None:
                hits[e].append(os.path.join(dirpath, fn))
    return hits


def section_report(text):
    """按行首 ①②③④ 标记判定四段结构。

    判据：每种标记（①/②/③/④）至少要有一行以该标记 + 空白开头。
    返回 dict: marks -> 出现行号列表, plus 各行首标记序列。
    """
    marks = {}
    order = []
    for lineno, line in enumerate(text.split("\n"), start=1):
        m = SEC_RE.match(line)
        if m:
            marks.setdefault(m.group(1), []).append(lineno)
            order.append(m.group(1))
    return marks, order


def check_file(path, entry):
    text = read_text(path)
    size = os.path.getsize(path)
    marks, order = section_report(text)
    has4 = all(k in marks for k in "①②③④")
    occ = text.count(entry)
    # 同时统计大写/小写变体
    occ_ci = len(re.findall(re.escape(entry), text, re.I))
    # 文件自称的 name=（用于核「以该 entry 为对象」）
    m = re.search(r"^name=(.+)$", text, re.M)
    name_in_file = m.group(1).strip() if m else ""
    # 是否有实质内容（非只有段头）
    body_lines = [l for l in text.split("\n")
                  if l.strip() and not SEC_RE.match(l)]
    return {
        "path": path,
        "bytes": size,
        "nonempty": size > 0,
        "entry_occ": occ,
        "entry_occ_ci": occ_ci,
        "has_1": "①" in marks,
        "has_2": "②" in marks,
        "has_3": "③" in marks,
        "has_4": "④" in marks,
        "has_all_four": has4,
        "mark_order": "".join(order),
        "n4_lines": len(marks.get("④", [])),
        "fourth_lines": marks.get("④", []),
        "name_in_file": name_in_file,
        "n_body_lines": len(body_lines),
    }


# --------------------------------------------------------------------------- #
# C · resolve.py 口径复算
# --------------------------------------------------------------------------- #
def run_resolve(coverage_path, out_dir, label):
    """调用本目录里的 resolve.py 副本，返回 (R_OK, R_TRACE_ONLY, ...)。"""
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    resolve_py = os.path.join(HERE, "resolve.py")
    cmd = [sys.executable, resolve_py,
           "--repo", REPO,
           "--coverage", coverage_path,
           "--out", out_dir]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env)
    if p.returncode != 0:
        raise RuntimeError(f"resolve.py 失败({label}): {p.stderr}")
    counts = {}
    for line in (p.stdout or "").split("\n"):
        m = re.match(r"\s+(R_[A-Z_]+)\s+(\d+)\s+([\d.]+)%", line)
        if m:
            counts[m.group(1)] = int(m.group(2))
    return counts, p.stdout


def apply_delta_to_copy(delta_rows, src, dst):
    """在 coverage.tsv 副本上按 entry 替换第 6 列（evidence_path）。"""
    text = read_text(src)
    lines = text.split("\n")
    header = [c.strip() for c in lines[0].rstrip("\r").split(",")]
    idx_ev = header.index("evidence_path")
    idx_entry = header.index("entry")
    new_by_entry = {}
    for _lineno, f in delta_rows:
        new_by_entry[f[idx_entry]] = f[idx_ev]
    out = [lines[0]]
    applied = []
    untouched = 0
    for raw in lines[1:]:
        raw_nl = raw
        body = raw.rstrip("\r")
        if not body.strip():
            out.append(raw_nl)
            continue
        f = body.split("\t")
        if len(f) != len(header):
            out.append(raw_nl)
            continue
        e = f[idx_entry]
        if e in new_by_entry:
            f[idx_ev] = new_by_entry[e]
            applied.append(e)
            out.append("\t".join(f))
        else:
            untouched += 1
            out.append(raw_nl)
    with open(dst, "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(out))
    return applied, untouched


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def main():
    problems = []          # 必改清单（(section, entry, 说明)）
    rows_out = []

    header_cov, cov_rows, cov_dup = load_coverage()
    delta_header, delta_rows = load_tsv_rows(DELTA)
    fields_header, fields_rows = load_tsv_rows(FIELDS)

    # ---- 结构自检 ----
    if delta_header != COLS:
        problems.append(("STRUCT", "-", f"delta 表头不符: {delta_header}"))
    if len(delta_rows) != 11:
        problems.append(("STRUCT", "-", f"delta 行数 {len(delta_rows)} != 11"))
    for e in ENTRIES:
        if e not in cov_rows:
            problems.append(("A", e, "coverage.tsv 中找不到该 entry"))

    fields_by_entry = {f[0]: f for _ln, f in fields_rows}
    proof_hits = find_proof_files()

    for _lineno, drow in delta_rows:
        entry = drow[0]
        rec = {"entry": entry}

        # ---------- A · 原文保全 ----------
        cov_lineno, cvals = cov_rows[entry]
        a_ok = True
        # 1-5, 7, 8 列逐字节相同（0-based: 0,1,2,3,4,6,7）
        mism = []
        for k in (0, 1, 2, 3, 4, 6, 7):
            if drow[k] != cvals[k]:
                mism.append(COLS[k])
        rec["A_prefix_ok"] = drow[5].startswith(cvals[5])
        rec["A_rest_cols_diff"] = ",".join(mism) if mism else ""
        # 原 classification_trace 段仍在
        orig_ev = cvals[5]
        rec["A_trace_kept"] = ("classification_trace" in drow[5]
                               and "EVIDENCE/classification_trace.tsv#" + entry in drow[5])
        rec["A_orig_len"] = len(orig_ev)
        rec["A_new_len"] = len(drow[5])
        rec["A_strict_prefix"] = drow[5].startswith(orig_ev)
        if mism:
            a_ok = False
            problems.append(("A", entry, f"第 {mism} 列与盘上不同"))
        if not drow[5].startswith(orig_ev):
            a_ok = False
            problems.append(("A", entry, "第 6 列不是盘上原第 6 列的严格前缀（疑似替换而非追加）"))
        if not rec["A_trace_kept"]:
            a_ok = False
            problems.append(("A", entry, "原 classification_trace 段丢失"))
        rec["A_ok"] = a_ok

        # ---------- B · 路径真实性与唯一性 ----------
        hits = proof_hits[entry]
        rec["B_nproof"] = len(hits)
        # delta 里声明的路径
        parts = [p.strip() for p in drow[5].split(";") if p.strip()]
        proof_part = None
        for p in parts:
            if p.upper().startswith("S") and os.path.basename(p).upper().startswith("PROOF_"):
                proof_part = p
                break
        rec["B_declared_path"] = proof_part or ""
        rel = (proof_part or "").replace("\\", "/")
        abs_declared = os.path.join(R14, rel.replace("/", os.sep)) if rel else ""
        rec["B_declared_isfile"] = bool(abs_declared) and os.path.isfile(abs_declared)
        rec["B_declared_bytes"] = os.path.getsize(abs_declared) if rec["B_declared_isfile"] else 0
        if len(hits) == 1:
            rec["B_unique_ok"] = os.path.normcase(os.path.abspath(hits[0])) == \
                                 os.path.normcase(os.path.abspath(abs_declared))
        else:
            rec["B_unique_ok"] = False

        finfo = check_file(hits[0], entry) if len(hits) == 1 else None
        if finfo:
            rec["B_bytes"] = finfo["bytes"]
            rec["B_nonempty"] = finfo["nonempty"]
            rec["B_entry_occ"] = finfo["entry_occ"]
            rec["B_has_all_four"] = finfo["has_all_four"]
            rec["B_mark_order"] = finfo["mark_order"]
            rec["B_n4_lines"] = finfo["n4_lines"]
            rec["B_fourth_lines"] = ",".join(str(x) for x in finfo["fourth_lines"])
            rec["B_sections"] = ("①" if finfo["has_1"] else "-") + \
                                ("②" if finfo["has_2"] else "-") + \
                                ("③" if finfo["has_3"] else "-") + \
                                ("④" if finfo["has_4"] else "-")
            rec["B_name_in_file"] = finfo["name_in_file"]
            rec["B_name_match"] = (finfo["name_in_file"] == cvals[2])
            rec["B_n_body_lines"] = finfo["n_body_lines"]
        else:
            rec.update({"B_bytes": 0, "B_nonempty": False, "B_entry_occ": 0,
                        "B_has_all_four": False, "B_mark_order": "",
                        "B_n4_lines": 0, "B_fourth_lines": "", "B_sections": "----",
                        "B_name_in_file": "", "B_name_match": False,
                        "B_n_body_lines": 0})

        b_ok = True
        if len(hits) != 1:
            b_ok = False
            problems.append(("B", entry, f"PROOF 文件命中 {len(hits)} 份（应恰好 1 份）"))
        elif not rec["B_unique_ok"]:
            b_ok = False
            problems.append(("B", entry, "声明的路径不是唯一命中的那份文件"))
        if not rec["B_declared_isfile"]:
            b_ok = False
            problems.append(("B", entry, "声明路径 isfile 为假"))
        if rec["B_declared_bytes"] == 0:
            b_ok = False
            problems.append(("B", entry, "文件为空"))
        if rec["B_entry_occ"] < 1:
            b_ok = False
            problems.append(("B", entry, "文件内容里没有该 entry"))
        if not rec["B_has_all_four"]:
            b_ok = False
            problems.append(("B", entry, f"四段不全：{rec['B_sections']}"))
        if len(hits) == 1 and not rec["B_name_match"]:
            b_ok = False
            problems.append(("B", entry, "PROOF 文件 name= 与台账 name 不一致"))
        rec["B_ok"] = b_ok

        # ---------- D · 注记质量（D1 相符；D2 逐行不同在循环后判） ----------
        note = parts[-1] if parts else ""
        rec["D_note"] = note
        rec["D_note_has_m94"] = note.startswith("M94 指针修复：")
        rec["D_note_match"] = rec["D_note_has_m94"] and ("④" in note)
        rec["D_note_says_trace_only"] = "原指针只连 classification_trace" in note
        rec["D_old_was_trace_only"] = (cvals[5].strip() ==
                                       "EVIDENCE/classification_trace.tsv#" + entry)
        rec["D_note_matches_fact"] = (rec["D_note_match"] and rec["B_has_all_four"]
                                      and rec["D_old_was_trace_only"])

        rows_out.append(rec)

    # C-1 先算改前分类（用同一快照，避免 coverage.tsv 并发漂移）
    snapshot = os.path.join(HERE, "_coverage_snapshot.tsv")
    shutil.copyfile(COVERAGE, snapshot)
    snap_sha = hashlib.sha256(open(snapshot, "rb").read()).hexdigest().upper()
    snap_bytes = os.path.getsize(snapshot)

    out_before = os.path.join(HERE, "_resolve_before")
    out_after = os.path.join(HERE, "_resolve_after")
    counts_before, txt_before = run_resolve(snapshot, out_before, "before")
    with open(os.path.join(HERE, "_resolve_before_stdout.txt"), "w",
              encoding="utf-8") as fh:
        fh.write(txt_before)

    # 应用 delta 到快照副本
    patched = os.path.join(HERE, "_coverage_after.tsv")
    applied, untouched = apply_delta_to_copy(delta_rows, snapshot, patched)
    counts_after, txt_after = run_resolve(patched, out_after, "after")
    with open(os.path.join(HERE, "_resolve_after_stdout.txt"), "w",
              encoding="utf-8") as fh:
        fh.write(txt_after)

    # 快照 vs after 的差异必须恰好是 11 行 × 第 6 列
    snap_lines = read_text(snapshot).split("\n")
    aft_lines = read_text(patched).split("\n")
    diff_lines = [i for i in range(min(len(snap_lines), len(aft_lines)))
                  if snap_lines[i] != aft_lines[i]]
    diff_detail = []
    for i in diff_lines:
        fa = snap_lines[i].rstrip("\r").split("\t")
        fb = aft_lines[i].rstrip("\r").split("\t")
        cols = [j for j in range(len(fa)) if fa[j] != fb[j]]
        diff_detail.append((i + 1, fa[0] if fa else "", cols))
    if len(diff_lines) != 11:
        problems.append(("C", "-", f"delta 副本与快照的行差 {len(diff_lines)} 处，应为 11"))
    for lineno, e, cols in diff_detail:
        if cols != [5]:
            problems.append(("C", e, f"第 {lineno} 行改到了第 {[c+1 for c in cols]} 列，应只改第 6 列"))

    # C-2 11 行改前各自属于哪一类（用 resolve.py 同一口径逐行判定）
    sys.path.insert(0, HERE)
    import importlib
    rp = importlib.import_module("resolve")
    bases_present = [("r14", R14), ("lead", LEAD), ("repo", REPO)]
    bases_present = [(n, p) for n, p in bases_present if os.path.isdir(p)]
    for rec in rows_out:
        entry = rec["entry"]
        _ln, cvals = cov_rows[entry]
        res_before = rp.resolve_row(cvals[5], bases_present)
        res_after = rp.resolve_row(rec_delta_ev(delta_rows, entry), bases_present)
        rec["C_class_before"] = res_before["class"]
        rec["C_class_after"] = res_after["class"]
        fe = res_after["first_existing"]
        rec["C_first_existing"] = fe[2] if fe else ""
        rec["C_after_base"] = fe[1] if fe else ""
        rec["C_parts_after"] = len(res_after["parts"])
        rec["C_traceflags_after"] = "".join("T" if t else "F" for t in res_after["trace_flags"])
        # 关键：R_OK 的那次命中必须来自 PROOF 段，而不是别的段
        hit_part = fe[0] if fe else ""
        rec["C_hit_part"] = hit_part[:60]
        rec["C_hit_is_proof"] = bool(fe) and hit_part.upper().endswith(
            "PROOF_" + entry + ".TXT")
        # 逐段命中表
        seg = []
        for part, is_tr, hit, _c in res_after["part_report"]:
            seg.append(f"{'T' if is_tr else 'F'}:{'HIT' if hit else 'miss'}")
        rec["C_part_hits"] = "/".join(seg)
        if not rec["C_hit_is_proof"]:
            problems.append(("C", entry,
                             f"R_OK 的命中不是 PROOF 段（命中段={hit_part[:50]!r}），"
                             f"R_OK 不代表 PROOF 路径可解析"))
        if rec["C_class_before"] != "R_TRACE_ONLY":
            problems.append(("C", entry, f"改前分类为 {rec['C_class_before']}，不是 R_TRACE_ONLY，不产生增量"))
        if rec["C_class_after"] != "R_OK":
            problems.append(("C", entry, f"改后分类仍为 {rec['C_class_after']}，不是 R_OK"))

    # D · 注记是否逐行不同（去模板后是否带本行信息）
    notes = [r["D_note"] for r in rows_out]
    note_tpl = "M94 指针修复：④ 已写在盘上（PROOF 文件含 ①②③④ 四段），原指针只连 classification_trace"
    for r in rows_out:
        r["D_note_dup_count"] = notes.count(r["D_note"])
        r["D_note_unique"] = (r["D_note_dup_count"] == 1)
        r["D_note_is_tpl"] = (r["D_note"] == note_tpl)
        r["D_ok"] = r["D_note_matches_fact"] and r["D_note_unique"]
        if not r["D_note_matches_fact"]:
            problems.append(("D1", r["entry"], "注记与该行实际情形不符"))
        if not r["D_note_unique"]:
            problems.append(("D2", r["entry"],
                             f"注记与其他行逐字相同（重复 {r['D_note_dup_count']} 份），未做到逐行不同"))
    notes_unique = len(set(notes)) == len(notes)

    # ---- 汇总 ----
    n = len(rows_out)
    a_fail = [r["entry"] for r in rows_out if not r["A_ok"]]
    b_fail = [r["entry"] for r in rows_out if not r["B_ok"]]
    d_fail = [r["entry"] for r in rows_out if not r["D_ok"]]
    d2_fail = [r["entry"] for r in rows_out if not r["D_note_unique"]]
    d1_fail = [r["entry"] for r in rows_out if not r["D_note_matches_fact"]]
    c_fail = [r["entry"] for r in rows_out
              if r["C_class_before"] != "R_TRACE_ONLY" or r["C_class_after"] != "R_OK"]
    n_unique = [r["entry"] for r in rows_out if r["B_nproof"] == 1]
    n_four = [r["entry"] for r in rows_out if r["B_has_all_four"]]

    # fields.tsv 自述 vs 实测
    fields_mismatch = []
    for r in rows_out:
        e = r["entry"]
        f = fields_by_entry.get(e)
        if not f:
            fields_mismatch.append((e, "fields.tsv 缺该行"))
            continue
        # idx: 0 entry,1 subsystem,2 name,3 old,4 found,5 chosen,6 bytes,7 all4,8 occ,9 status,10 note
        if str(r["B_nproof"]) != f[4]:
            fields_mismatch.append((e, f"proof_files_found 自述 {f[4]} 实测 {r['B_nproof']}"))
        if str(r["B_bytes"]) != f[6]:
            fields_mismatch.append((e, f"file_bytes 自述 {f[6]} 实测 {r['B_bytes']}"))
        if str(r["B_entry_occ"]) != f[8]:
            fields_mismatch.append((e, f"entry_occurrences 自述 {f[8]} 实测 {r['B_entry_occ']}"))
        if (r["B_has_all_four"] and f[7] != "是") or (not r["B_has_all_four"] and f[7] != "否"):
            fields_mismatch.append((e, f"has_all_four_sections 自述 {f[7]} 实测 {r['B_has_all_four']}"))

    # ---- 写 check11.tsv ----
    cols = ["entry", "A_ok", "A_strict_prefix", "A_trace_kept", "A_rest_cols_diff",
            "B_ok", "B_nproof", "B_declared_path", "B_declared_isfile", "B_declared_bytes",
            "B_nonempty", "B_entry_occ", "B_sections", "B_mark_order", "B_n4_lines",
            "B_fourth_lines", "B_name_match", "B_n_body_lines",
            "C_class_before", "C_class_after", "C_traceflags_after", "C_parts_after",
            "C_hit_is_proof", "C_part_hits", "C_first_existing",
            "D_ok", "D_note_matches_fact", "D_note_unique", "D_note_dup_count",
            "D_note_has_m94", "D_note"]
    ck = os.path.join(HERE, "check11.tsv")
    with open(ck, "w", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(cols) + "\n")
        for r in rows_out:
            fh.write("\t".join(str(r.get(c, "")).replace("\t", " ") for c in cols) + "\n")

    # ---- 控制台 ----
    print("=== R16-AUDIT-EVID802-11 ===")
    print(f"覆盖行数: {n}")
    print(f"A 不合格: {len(a_fail)} {a_fail}")
    print(f"B 不合格: {len(b_fail)} {b_fail}")
    print(f"C 不合格: {len(c_fail)} {c_fail}")
    print(f"D 不合格: {len(d_fail)} {d_fail}")
    print(f"   D1(注记相符) 不合格: {len(d1_fail)} {d1_fail}")
    print(f"   D2(注记逐行不同) 不合格: {len(d2_fail)} {d2_fail}")
    print(f"唯一 PROOF 份数: {len(n_unique)}/11  -> 非唯一: {[r['entry'] for r in rows_out if r['B_nproof'] != 1]}")
    print(f"四段齐全: {len(n_four)}/11 -> 缺段: {[r['entry'] for r in rows_out if not r['B_has_all_four']]}")
    print(f"注记 11 行是否互不相同: {notes_unique} (unique={len(set(notes))})")
    print(f"注记是否全部等于同一模板: {all(x == note_tpl for x in notes)}")
    print(f"coverage 快照: bytes={snap_bytes} sha256={snap_sha}")
    print(f"改前: {counts_before}")
    print(f"改后: {counts_after}")
    print(f"delta 应用: applied={len(applied)} untouched_rows={untouched}")
    print(f"快照 vs after 行差: {len(diff_lines)} 处 {[d[0] for d in diff_detail]}")
    print(f"R_OK 命中来自 PROOF 段的行数: {sum(1 for r in rows_out if r['C_hit_is_proof'])}/11")
    print(f"classification_trace.tsv 盘上是否存在: "
          f"{[(n, os.path.isfile(os.path.join(p, 'EVIDENCE', 'classification_trace.tsv'))) for n, p in bases_present]}")
    print(f"coverage 行数: {len(cov_rows)} dup={cov_dup}")
    print(f"fields.tsv 自述不符: {len(fields_mismatch)}")
    for x in fields_mismatch:
        print("   ", x)
    print("必改条目:")
    for p in problems:
        print("   ", p)
    print(f"写出: {ck}")
    return 0


def rec_delta_ev(delta_rows, entry):
    for _ln, f in delta_rows:
        if f[0] == entry:
            return f[5]
    return ""


if __name__ == "__main__":
    sys.exit(main())
