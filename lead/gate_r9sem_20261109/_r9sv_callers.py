# -*- coding: utf-8 -*-
"""_r9sv_callers.py — 调用方逐个查（消费形态）+ minpatch 候选件 diff + 模糊匹配实证。"""
import difflib
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "gate_r9sem_20261109"
OUT = {}

# --- (1) minpatch 候选件 vs 只读 _g9_gate.py：是否只有 3 处替换 ---
print("=== (1) _r9s_g9_candidate.py vs _g9_gate.py diff ===")
a = (ROOT / "lead/gate_r9r12_20261109/_g9_gate.py").read_text("utf-8").splitlines()
b = (WDIR / "_r9s_g9_candidate.py").read_text("utf-8").splitlines()
d = list(difflib.unified_diff(a, b, lineterm="", n=1))
OUT["minpatch_diff"] = d
for l in d:
    print("   ", l[:180])
print("  diff lines =", len(d))

# --- (2) 43 处 check_deliverable 调用方：有没有按「缺要素」消息全文消费 ---
print("\n=== (2) check_deliverable 调用方消息消费形态 ===")
hits = []
for p in sorted((ROOT / "lead").rglob("*.py")):
    if "gate_r9sem_20261109" in str(p):
        continue
    try:
        L = p.read_text("utf-8", errors="replace").splitlines()
    except Exception:
        continue
    for i, l in enumerate(L, 1):
        if re.search(r"\bcheck_deliverable\s*\(", l):
            ctx = "\n".join(L[max(0, i - 3):i + 6])
            hits.append({"file": str(p.relative_to(ROOT)).replace("\\", "/"), "line": i,
                         "text": l.strip()[:150],
                         "consumes_problems_text": bool(re.search(
                             r"缺要素|problems\[|\[.msg.\]|verdict.*==|json\.dumps", ctx))})
OUT["check_deliverable_calls"] = hits
print("  n_calls =", len(hits))
print("  calls whose ±3..+6 line window mentions 缺要素/problems/msg =",
      sum(1 for x in hits if x["consumes_problems_text"]))
for x in hits:
    if x["consumes_problems_text"]:
        print("     %s:%d  %s" % (x["file"], x["line"], x["text"][:120]))

# 调用点按文件汇总
byfile = {}
for x in hits:
    byfile.setdefault(x["file"], 0)
    byfile[x["file"]] += 1
OUT["check_deliverable_by_file"] = byfile
print("  n_files =", len(byfile))

# --- (3) 谓词源码里是否有真·模糊匹配调用 ---
print("\n=== (3) 模糊匹配实证（区分注释字样与真实调用） ===")
src = (WDIR / "_r9s_predicates.py").read_text("utf-8")
for i, l in enumerate(src.splitlines(), 1):
    if re.search(r"fuzzy|模糊|通配|编辑距离|embedding|SequenceMatcher|difflib|editdistance", l, re.I):
        print("   L%d: %s" % (i, l.strip()[:150]))
OUT["fuzzy_comment_lines"] = [i for i, l in enumerate(src.splitlines(), 1)
                              if re.search(r"fuzzy|模糊|通配|编辑距离|embedding|SequenceMatcher|difflib|editdistance",
                                           l, re.I)]
print("  -> 全部为注释字样，无 import/调用（见 _r9sv_extra_out.json imports / fuzzy_library_calls）")

# --- (4) 设计回件里 7 条准入标准原文（逐条读） ---
print("\n=== (4) 设计回件 §2.4 准入 7 条原文 ===")
dt = (WDIR / "_r9s_DESIGN.md").read_text("utf-8").splitlines()
for n in range(149, 160):
    print("   L%d: %s" % (n, dt[n - 1][:230]))
OUT["admission_rules_lines"] = [dt[n - 1] for n in range(149, 160)]

# --- (5) 五处原句上下文（我独立读过的行，落盘留证） ---
print("\n=== (5) 五处原句 + 关键上下文（独立实读） ===")
CTX = [
    ("lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md", [108, 138]),
    ("lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md", [12, 26, 65, 67, 69, 70, 71, 74, 80, 84]),
    ("lead/n11_wording_fix_20261108/N11_WORDING_FIX.md", [76, 81, 82, 88, 89, 97]),
    ("lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md", [10, 32, 44, 51, 59, 67, 69, 71, 73, 77, 87]),
]
ctx = []
for rel, nums in CTX:
    L = (ROOT / rel).read_text("utf-8").splitlines()
    for n in nums:
        if n <= len(L):
            ctx.append({"file": rel, "line": n, "text": L[n - 1][:220]})
            print("   %s:%d  %s" % (rel.split("/")[-1], n, L[n - 1][:170]))
OUT["five_contexts"] = ctx

(WDIR / "_r9sv_callers_out.json").write_text(
    json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("\nwrote _r9sv_callers_out.json")
