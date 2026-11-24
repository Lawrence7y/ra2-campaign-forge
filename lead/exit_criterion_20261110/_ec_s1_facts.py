# -*- coding: utf-8 -*-
"""_ec_s1_facts.py — 第一步：9 件样本 exit_sites / write_lines / has_print 逐件复核。

口径（复现上一轮普查所用定义的假设，逐字段验证）：
  exit_sites:  (kind, lineno, 源片段)
     kind="call"  → ast.Call，func 为 Name('exit'/'quit') 或 Attribute(attr in {'exit','_exit'})
     kind="raise" → ast.Raise，exc 为 SystemExit 的构造（Call 或 Name）
  write_lines(普查口径): ast.Call，func 为 Name('open') 或 Attribute(attr=='open') 的行号
     —— 这个口径把「读 open」也算进去了；本脚本另算「真写」(w/a/x/+ 模式或 write_text/write_bytes)。
  has_print: 存在 ast.Call func 为 Name('print') 或 Attribute(attr=='print')。

另输出四件零信息对象的产物实证：真写文件名、OUT 缓冲镜像模式、stdout-only 判定。
只读；不运行任何被检脚本（纯 AST）。
"""
import ast
import hashlib
import io
import json
import os
import sys

ROOT = r"D:\Project\ra2-campaign-forge"

ORCH = {
 "five_ledger_subjects": [
  {"rel": "lead/re_line_20261105/D21_RULING/_d21_burden5.py", "bytes": 2929, "n_lines": 73,
   "exit_sites": [], "n_exit": 0, "write_lines": [20], "has_print": True},
  {"rel": "lead/re_line_20261105/V6_V3_REVIEW/_leader_crossframe_check.py", "bytes": 4688, "n_lines": 101,
   "exit_sites": [], "n_exit": 0, "write_lines": [], "has_print": True},
  {"rel": "lead/re_line_20261105/_leader/_a7_acf_probe.py", "bytes": 5763, "n_lines": 163,
   "exit_sites": [], "n_exit": 0, "write_lines": [35, 161], "has_print": True},
  {"rel": "lead/re_line_20261105/_leader/_intra_frame_census.py", "bytes": 6279, "n_lines": 167,
   "exit_sites": [], "n_exit": 0, "write_lines": [37, 94, 165], "has_print": True},
 ],
 "four_gates": [
  {"rel": "lead/d27_ruling_20261106/check_d27.py", "bytes": 3764, "n_lines": 107,
   "exit_sites": [["call", 107, "sys.exit(main())"]], "n_exit": 1, "write_lines": [], "has_print": True},
  {"rel": "lead/d28_ruling_20261106/check_d28.py", "bytes": 4539, "n_lines": 122,
   "exit_sites": [["raise", 122, "raise SystemExit(main())"]], "n_exit": 1, "write_lines": [], "has_print": True},
  {"rel": "lead/d29_ruling_20261106/check_d29.py", "bytes": 3906, "n_lines": 110,
   "exit_sites": [["raise", 110, "raise SystemExit(main())"]], "n_exit": 1, "write_lines": [], "has_print": True},
  {"rel": "lead/d30_ruling_20261106/check_d30.py", "bytes": 3926, "n_lines": 110,
   "exit_sites": [["raise", 110, "raise SystemExit(main())"]], "n_exit": 1, "write_lines": [], "has_print": True},
 ],
 "constant_exit_known": [
  {"rel": "lead/goal1_a8_fix_20261022/VERIFY_A8.py", "bytes": 38317, "n_lines": 800,
   "exit_sites": [["call", 800, "sys.exit(main())"]], "n_exit": 1,
   "write_lines": [87, 284, 285, 286, 287, 303, 408, 425], "has_print": True},
 ],
}


def read_text(p):
    with open(p, "rb") as f:
        raw = f.read()
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace"), "utf-8(replace)"


def is_exit_call(node):
    f = node.func
    if isinstance(f, ast.Name):
        return f.id in ("exit", "quit")
    if isinstance(f, ast.Attribute):
        return f.attr in ("exit", "_exit")
    return False


def is_systemexit_construction(node):
    if isinstance(node, ast.Call):
        f = node.func
        return (isinstance(f, ast.Name) and f.id == "SystemExit") or \
               (isinstance(f, ast.Attribute) and f.attr == "SystemExit")
    if isinstance(node, ast.Name):
        return node.id == "SystemExit"
    return False


def analyze(src):
    tree = ast.parse(src)
    lines = src.splitlines()
    exits, opens, true_writes, prints = [], [], [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc is not None and is_systemexit_construction(node.exc):
            exits.append(("raise", node.lineno, ast.get_source_segment(src, node) or "?"))
        elif isinstance(node, ast.Call):
            f = node.func
            if is_exit_call(node):
                exits.append(("call", node.lineno, ast.get_source_segment(src, node) or "?"))
            if (isinstance(f, ast.Name) and f.id == "open") or \
               (isinstance(f, ast.Attribute) and f.attr == "open"):
                opens.append(node.lineno)
                mode = None
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    mode = node.args[1].value
                for kw in node.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = kw.value.value
                if isinstance(mode, str) and any(c in mode for c in "wax+"):
                    true_writes.append((node.lineno, mode))
            if (isinstance(f, ast.Name) and f.id == "print") or \
               (isinstance(f, ast.Attribute) and f.attr == "print"):
                prints.append(node.lineno)
            if isinstance(f, ast.Attribute) and f.attr in ("write_text", "write_bytes"):
                true_writes.append((node.lineno, f.attr))
    n_lines = len(lines)
    if n_lines and lines[-1] == "":
        n_lines -= 0  # splitlines 已不含末尾空行语义
    return tree, sorted(set(opens)), sorted(true_writes), bool(prints), exits


def diff_sample(rec, mine):
    problems = []
    if rec["bytes"] != mine["bytes"]:
        problems.append("bytes %s!=%s" % (mine["bytes"], rec["bytes"]))
    if rec["n_lines"] != mine["n_lines"]:
        problems.append("n_lines %s!=%s" % (mine["n_lines"], rec["n_lines"]))
    if rec["n_exit"] != len(mine["exit_sites"]):
        problems.append("n_exit %s!=%d" % (rec["n_exit"], len(mine["exit_sites"])))
    got = [[k, ln, sn] for (k, ln, sn) in mine["exit_sites"]]
    if rec["exit_sites"] != got:
        problems.append("exit_sites %s != %s" % (rec["exit_sites"], got))
    if rec["write_lines"] != mine["open_lines"]:
        problems.append("write_lines %s != %s" % (rec["write_lines"], mine["open_lines"]))
    if rec["has_print"] != mine["has_print"]:
        problems.append("has_print")
    return problems


def main():
    all_recs = (ORCH["five_ledger_subjects"] + ORCH["four_gates"] + ORCH["constant_exit_known"])
    n_bad = 0
    for rec in all_recs:
        rel = rec["rel"]
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        src, enc = read_text(p)
        raw = open(p, "rb").read()
        sha = hashlib.sha256(raw).hexdigest()
        tree, opens, true_writes, has_print, exits = analyze(src)
        mine = {
            "bytes": len(raw), "n_lines": len(src.splitlines()),
            "exit_sites": exits, "open_lines": opens,
            "has_print": has_print, "true_writes": true_writes,
        }
        problems = diff_sample(rec, mine)
        print("=" * 78)
        print("样本:", rel)
        print("被核对象 SHA256 = %s，字节数 = %d" % (sha, len(raw)))
        print("  encoding=%s n_lines(实测)=%d" % (enc, mine["n_lines"]))
        print("  exit_sites(实测):", exits)
        print("  open 行(普查 write_lines 口径实测):", opens, "| 编排方:", rec["write_lines"])
        print("  真写(w/a/x/+ 或 write_text/bytes):", true_writes)
        print("  has_print:", has_print, "| print 行数:", end=" ")
        print(len([1 for _ in ast.walk(tree) if isinstance(_, ast.Call)
                   and isinstance(_.func, (ast.Name, ast.Attribute))
                   and (getattr(_.func, "id", "") == "print" or getattr(_.func, "attr", "") == "print")]))
        if problems:
            n_bad += 1
            print("  ✗ 与编排方不一致:", problems)
        else:
            print("  ✓ 与编排方逐字段一致（bytes/n_lines/exit_sites/write_lines/has_print）")
    print("=" * 78)
    print("四件零信息对象的产物实证（真写去向）：")
    for rec in ORCH["five_ledger_subjects"]:
        rel = rec["rel"]
        src, _ = read_text(os.path.join(ROOT, rel.replace("/", os.sep)))
        tree = ast.parse(src)
        targets = []
        outbuf = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                if isinstance(f, ast.Attribute) and f.attr in ("write", "write_text") and node.args:
                    a0 = node.args[0]
                    if isinstance(a0, ast.Constant):
                        targets.append((node.lineno, "literal", repr(a0.value)[:40]))
                if isinstance(f, ast.Attribute) and f.attr == "open":
                    mode = None
                    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                        mode = node.args[1].value
                    if isinstance(mode, str) and any(c in mode for c in "wax+"):
                        a0 = node.args[0] if node.args else None
                        pth = repr(ast.get_source_segment(src, a0))[:80] if a0 is not None else "?"
                        targets.append((node.lineno, "open-write", pth))
            if isinstance(node, ast.Name) and node.id == "OUT":
                outbuf.append(node.lineno)
        stdout_only = not targets and not [l for l in outbuf]
        print("-" * 78)
        print(" ", rel)
        print("    真写落盘点:", targets if targets else "无（stdout-only，无任何真写）")
        print("    OUT 缓冲镜像模式引用行数:", len(outbuf), ("（OUT 同时 print+append ⇒ 产物=stdout 的文件镜像）" if outbuf else ""))
    print("\nRESULT: %d/%d 逐字段一致" % (len(all_recs) - n_bad, len(all_recs)))
    return 1 if n_bad else 0


if __name__ == "__main__":
    sys.exit(main())
