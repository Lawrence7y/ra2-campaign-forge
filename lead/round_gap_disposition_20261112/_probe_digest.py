# -*- coding: utf-8 -*-
"""对「无报告轮(B)」目录做探针摘要：.py 摘 docstring+main，_out.txt/.json 摘头尾。
用法: python -I -X utf8 _probe_digest.py
输出: _probe_digest.txt（同时打印 stdout）。.pyc 一律跳过；大文件只取头尾行。
"""
import os
import io
import json
import sys

LEAD = r"D:\Project\ra2-campaign-forge\lead"
SELF = os.path.dirname(os.path.abspath(__file__))

# 报告窗口内的 B 目录（>=20261106 且顶层），来自枚举结果；手工登记免依赖 JSON 结构变化
B_DIRS = [
    "const_exit_fix_20261110", "crit_fix_20261110", "dup_audit_20261110",
    "e3_fix2_20261110", "e3_secondimpl_20261110", "e3_unify_20261111",
    "esi_caller_trace_20261111", "exit_lint_20261110", "gate_exit_retrofit_20261110",
    "ledger_exit_census_20261110", "ok_falsify_20261110", "playerctrl_semantics_20261111",
    "re_crashwriter_static_20261110", "re_loadbench_diff_20261110",
    "re_map_preset_decode_20261110", "re_orphan_owners_20261110",
    "slot2_fullscan_20261111", "unknown_locate_20261110",
    "re_atlas_reassess_20261112",  # 11-12 新增无报告轮，仅登记
]

lines = []
P = lines.append


def py_digest(path):
    """docstring + def main 签名与函数体前几行。"""
    try:
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            src = fh.read()
    except OSError as e:
        P("   <read error %s>" % e)
        return
    P("   [py] %s (%d B)" % (os.path.basename(path), len(src.encode("utf-8", errors="replace"))))
    src_l = src.lstrip()
    doc = ""
    for q in ('"""', "'''"):
        if src_l.startswith(q):
            end = src_l.find(q, 3)
            if end != -1:
                doc = src_l[3:end]
            break
    if doc.strip():
        doc_lines = [l for l in doc.strip().splitlines() if l.strip()]
        for l in doc_lines[:14]:
            P("     doc| " + l.strip())
        if len(doc_lines) > 14:
            P("     doc| ...(%d 行省略)" % (len(doc_lines) - 14))
    else:
        for l in src.splitlines()[:6]:
            P("     head| " + l[:150])
    idx = src.find("def main")
    while idx != -1:
        seg = src[idx:idx + 900]
        P("     --- def main 片段 @%d ---" % idx)
        for l in seg.splitlines()[:14]:
            P("     main| " + l[:150])
        idx = src.find("def main", idx + 1)
        if idx > 200000:
            break


def txt_digest(path, head=18, tail=14):
    size = os.path.getsize(path)
    P("   [txt] %s (%d B)" % (os.path.basename(path), size))
    dq_head, dq_tail = [], []
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh):
            if i < head:
                dq_head.append(line.rstrip("\n"))
            dq_tail.append(line.rstrip("\n"))
            if len(dq_tail) > tail:
                dq_tail.pop(0)
    for l in dq_head:
        P("     head| " + l[:200])
    P("     ...")
    for l in dq_tail:
        P("     tail| " + l[:200])


def json_digest(path, head=16, tail=10):
    size = os.path.getsize(path)
    P("   [json] %s (%d B)" % (os.path.basename(path), size))
    if size < 6000:
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                P("     line| " + line.rstrip("\n")[:200])
        return
    dq_head, dq_tail = [], []
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh):
            if i < head:
                dq_head.append(line.rstrip("\n"))
            dq_tail.append(line.rstrip("\n"))
            if len(dq_tail) > tail:
                dq_tail.pop(0)
    for l in dq_head:
        P("     head| " + l[:200])
    P("     ...")
    for l in dq_tail:
        P("     tail| " + l[:200])


for d in B_DIRS:
    full = os.path.join(LEAD, d)
    P("")
    P("######## %s ########" % d)
    if not os.path.isdir(full):
        P("   <目录不存在>")
        continue
    for root, dirs, files in os.walk(full):
        dirs[:] = sorted(x for x in dirs if x != "__pycache__")
        for f in sorted(files):
            p = os.path.join(root, f)
            rel = os.path.relpath(p, full).replace("\\", "/")
            low = f.lower()
            if low.endswith(".pyc"):
                continue
            if low.endswith(".py"):
                P("   -- %s" % rel)
                py_digest(p)
            elif low.endswith(".json"):
                P("   -- %s" % rel)
                json_digest(p)
            elif low.endswith(".txt"):
                P("   -- %s" % rel)
                txt_digest(p)
            else:
                P("   -- %s (%d B) [未摘要]" % (rel, os.path.getsize(p)))

text = "\n".join(lines) + "\n"
sys.stdout.write(text[:20000] + ("\n...[stdout 截断，全文在 _probe_digest.txt]\n" if len(text) > 20000 else ""))
with io.open(os.path.join(SELF, "_probe_digest.txt"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)
print("")
print("written _probe_digest.txt (%d chars)" % len(text))
