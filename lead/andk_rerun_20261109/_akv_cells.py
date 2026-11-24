# -*- coding: utf-8 -*-
"""_akv_cells.py — 逐格三方比对：执行员 _ak_runs.jsonl / 复核员 _akv_own.json / 交付 markdown 表。

对 4 件 × 9 行 = 36 格，逐格列出：
  执行员 jsonl: exit/verdict/stdout/doc_desc
  自写实跑    : exit/verdict/stdout/caught/stdoutsameAsA
  markdown    : 该行 STDOUT 是否与 jsonl 一致
路径差（sandbox vs _akv_own）显式归一化并单独报告，不隐藏。
"""
import json
import re
from pathlib import Path

WD = Path(r"D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109")

all_runs = [json.loads(l) for l in (WD / "_ak_runs.jsonl").read_text(encoding="utf-8").splitlines()]

# ---- 源 1：执行员 36 条 BAD_NEEDLE 逐运行记录 + 4 条 A 基线 ----
exec_rows = {}
a_baseline = {}
for r in all_runs:
    if r["tag"] == "BAD_NEEDLE":
        key = (r["gate"], r["exp"].replace("inj_", "").replace("p", "."))
        exec_rows[key] = r
    if r["tag"] == "ABC_ORIGINAL" and r["mut"] == "A":
        a_baseline[r["gate"]] = r["stdout"]

# ---- 源 2：复核员独立实跑 36 格 ----
own = json.loads((WD / "_akv_own.json").read_text(encoding="utf-8"))
own_rows = {(m["gate"], m["item"]): m for m in own["matrix"]}

# ---- 源 3：交付 markdown 表 ----
md_rows = {}
for line in (WD / "_ak_BAD_NEEDLE_MATRIX.md").read_text(encoding="utf-8").splitlines():
    m = re.match(r"^\|\s*(d27|d28|d29|d30)\s*\|\s*([0-9.]+)\s*\|", line)
    if not m:
        continue
    gate, item = m.group(1), m.group(2)
    mm = re.search(r"`('(?:[^`]|`)*')`\s*\|\s*\*\*(True|False)\*\*\s*\|\s*$", line)
    stdout_repr, caught = (mm.group(1), mm.group(2)) if mm else (None, None)
    md_rows[(gate, item)] = dict(line=line, stdout_repr=stdout_repr, caught=caught)

ITEM_MAP = {"1": "1", "2": "2", "3": "3", "4": "4", "4.5": "4b", "5": "5",
            "6": "6", "6.5": "6b", "7": "7", "8": "8"}


def norm(s):
    """仅归一化两套沙箱根路径与其下任意层实验目录名；其余字节不动。
    两套沙箱层数不同（sandbox/<gate>/<exp>/ 为 2 层，_akv_own/<exp>/ 为 1 层），
    故用『根之后直到 FACTCHECK』整段替换，而不是固定层数。"""
    return re.sub(
        r"D:\\Project\\ra2-campaign-forge\\lead\\andk_rerun_20261109\\(?:sandbox|_akv_own)\\[^\r\n]*?FACTCHECK",
        lambda m: "<R>\\FACTCHECK", s)


print("EXEC_BAD_NEEDLE_ROWS =", len(exec_rows))
print("OWN_MATRIX_CELLS     =", len(own_rows))
print("MD_TABLE_ROWS        =", len(md_rows))
print()
hdr = "%-4s %-5s | %-18s | %-18s | %-9s | %-9s | %-5s | %s"
print(hdr % ("gate", "item", "EXEC exit/verdict", "OWN exit/verdict",
             "EXECcaught", "OWNcaught", "MDok", "stdoutEqual"))
print("-" * 148)

problems = []
path_only_diffs = []
for gate in ("d27", "d28", "d29", "d30"):
    items = [str(i) for i in range(1, 9)] + (["6.5"] if gate == "d27" else ["4.5"])
    for item in items:
        e = exec_rows.get((gate, item))
        o = own_rows.get((gate, ITEM_MAP[item]))
        md = md_rows.get((gate, item))
        if e is None or o is None or md is None:
            problems.append((gate, item, "MISSING_SOURCE", e is not None, o is not None, md is not None))
            continue
        e_caught = (e["verdict"] == "FAIL" and e["exit"] != 0)
        o_caught = o["caught"]
        md_stdout = eval(md["stdout_repr"], {"__builtins__": {}}, {}) if md["stdout_repr"] else None
        md_ok = (md_stdout == e["stdout"]) and (md["caught"] == str(e_caught))
        same_raw = (e["stdout"] == o["after_stdout"])
        same_norm = (norm(e["stdout"]) == norm(o["after_stdout"]))
        if not same_raw and not same_norm:
            problems.append((gate, item, "STDOUT_DIFF", repr(e["stdout"])[:120], repr(o["after_stdout"])[:120]))
        if not same_raw:
            path_only_diffs.append((gate, item))
        if e["exit"] != o["after_exit"] or e_caught != o_caught or not md_ok:
            problems.append((gate, item, "VERDICT_OR_EXIT_OR_MD_DIFF",
                             e["exit"], o["after_exit"], e_caught, o_caught, md_ok))
        print(hdr % (gate, item,
                     "EXIT=%d %s" % (e["exit"], e["verdict"]),
                     "EXIT=%d %s" % (o["after_exit"], o["after_verdict"]),
                     str(e_caught), str(o_caught), str(md_ok),
                     "RAW" if same_raw else "PATH-NORMALIZED"))
    print("-" * 148)

print()
print("PROBLEMS =", len(problems))
for p in problems:
    print("   ", p)
print("PATH_ONLY_DIFFS (expected, sandbox path differs by design) =", len(path_only_diffs), path_only_diffs)
print()
print("==== STILL-PASS CELLS: 必须自己复现一遍 ====")
for gate in ("d27", "d28", "d29", "d30"):
    item = "6.5" if gate == "d27" else "4.5"
    e, o = exec_rows[(gate, item)], own_rows[(gate, ITEM_MAP[item])]
    print("  %s/%s  EXEC EXIT=%d STDOUT=%r" % (gate, item, e["exit"], e["stdout"]))
    print("        OWN  EXIT=%d STDOUT=%r" % (o["after_exit"], o["after_stdout"]))
    print("        EXEC stdout==A基线: %s | OWN stdout==A基线: %s | OWN caught: %s | 两方 stdout 逐字一致: %s" %
          (e["stdout"] == a_baseline[gate], o["stdout_same_as_A"], o["caught"],
           e["stdout"] == o["after_stdout"]))
