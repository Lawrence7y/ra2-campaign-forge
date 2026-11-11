# -*- coding: utf-8 -*-
"""STEP 1：lead/ 下目录名以 2026\\d{4} 结尾的轮次目录，递归枚举与三分类。
用法: python -I -X utf8 _enum_rounds.py
规则：
- os.walk 全递归；目录名 basename 匹配 2026\\d{4}$ 即登记（排除本写域自身）。
- 文件归属：归入其最近的祖先轮次目录（若轮次目录内嵌套轮次目录，文件归更深者，两边不重复计）。
- 顶层文件数 = 直接子文件；递归文件数 = 归属到本目录的全部文件。
- 分类：A=有 md 报告（递归含 .md）；B=无 md 但递归非空；C=递归后仍完全空（无任何文件，可有空子目录）。
- 对照口径：报告 §4 的 182/153/18/11 只统计日期后缀 >= 20261106 的目录。
- 另检测 _out.txt/_out.json（basename 后缀）与其余类别文件。
输出：stdout（同时落盘 _enum_rounds_stdout.txt）+ 机读 _enum_rounds.json。
"""
import os
import re
import json
import sys
import io

LEAD = r"D:\Project\ra2-campaign-forge\lead"
SELF = os.path.dirname(os.path.abspath(__file__))
SUFFIX_RE = re.compile(r"2026\d{4}$")

# --- 收集所有轮次目录（任意深度） ---
date_dirs = []  # relpath (os.sep)
loose_files_top = []
for root, dirs, files in os.walk(LEAD):
    if os.path.abspath(root) == SELF:
        dirs[:] = []
        continue
    rel_root = os.path.relpath(root, LEAD)
    for d in dirs:
        if SUFFIX_RE.search(d):
            date_dirs.append(os.path.normpath(os.path.join(rel_root, d)) if rel_root != "." else d)
    if rel_root == ".":
        loose_files_top = list(files)
date_dirs.sort()

date_dir_set = set(os.path.normpath(p) for p in date_dirs)

def nearest_owner(rel_dir_of_file):
    """文件所在目录 relpath -> 最近的祖先轮次目录 relpath，或 None。"""
    cur = rel_dir_of_file
    while True:
        if cur in date_dir_set:
            return cur
        parent = os.path.dirname(cur)
        if parent == cur or cur == "." or cur == "":
            return None
        cur = parent

# --- 文件归属 ---
owner_files = {os.path.normpath(p): [] for p in date_dirs}
unowned_files = []
for root, dirs, files in os.walk(LEAD):
    if os.path.abspath(root) == SELF:
        dirs[:] = []
        continue
    rel_root = os.path.normpath(os.path.relpath(root, LEAD))
    for f in files:
        rel = os.path.normpath(os.path.join(rel_root, f)) if rel_root != "." else f
        owner = nearest_owner(rel_root)
        if owner is None:
            unowned_files.append(rel)
        else:
            owner_files[owner].append(rel)

# --- 逐目录统计 ---
def kind_of(bn):
    low = bn.lower()
    if low.endswith(".md"):
        return "md"
    if low.endswith(".py"):
        return "py"
    if low.endswith("_out.txt") or low.endswith("_out.json"):
        return "out"
    if low.endswith(".txt") or low.endswith(".json"):
        return "txtjson_other"
    return "other"

records = []
for rel in date_dirs:
    full = os.path.join(LEAD, rel)
    direct = [f for f in owner_files[rel]
              if os.path.dirname(f) == rel]
    rec = owner_files[rel]
    nested = [d for d in date_dir_set
              if d != rel and d.startswith(rel + os.sep)]
    md = [f for f in rec if kind_of(os.path.basename(f)) == "md"]
    py = [f for f in rec if kind_of(os.path.basename(f)) == "py"]
    out = [f for f in rec if kind_of(os.path.basename(f)) == "out"]
    txtjson_other = [f for f in rec if kind_of(os.path.basename(f)) == "txtjson_other"]
    other = [f for f in rec if kind_of(os.path.basename(f)) == "other"]
    total_bytes = 0
    fdetails = []
    for f in rec:
        sz = os.path.getsize(os.path.join(LEAD, f))
        total_bytes += sz
        fdetails.append({"rel": os.path.relpath(f, rel).replace("\\", "/"), "size": sz})
    if md:
        cat = "A"
    elif rec:
        cat = "B"
    else:
        cat = "C"
    m = SUFFIX_RE.search(os.path.basename(rel))
    records.append({
        "dir": rel.replace("\\", "/"),
        "name": os.path.basename(rel),
        "date": m.group(0),
        "depth": rel.count(os.sep),
        "top_files": len(direct),
        "rec_files": len(rec),
        "nested_date_dirs": sorted(nested),
        "total_bytes": total_bytes,
        "md": sorted(x.replace("\\", "/") for x in md),
        "py": sorted(x.replace("\\", "/") for x in py),
        "out": sorted(x.replace("\\", "/") for x in out),
        "txtjson_other": sorted(x.replace("\\", "/") for x in txtjson_other),
        "other": sorted(x.replace("\\", "/") for x in other),
        "files": fdetails,
        "category": cat,
        "ge_111106": m.group(0) >= "20261106",
    })

def summarize(subset, label):
    n = len(subset)
    a = sum(1 for r in subset if r["category"] == "A")
    b = sum(1 for r in subset if r["category"] == "B")
    c = sum(1 for r in subset if r["category"] == "C")
    print("[%s] 总轮次目录=%d  A有md=%d  B无md有文件=%d  C递归空=%d" % (label, n, a, b, c))
    return n, a, b, c

lines = []
P = lines.append
P("== STEP1 递归枚举 lead/ 下目录名以 2026\\d{4} 结尾的轮次目录 ==")
P("枚举脚本: _enum_rounds.py (python -I -X utf8 实跑); 排除本写域 round_gap_disposition_20261112")
P("lead/ 顶层不属于任何轮次目录的散件: %d 个: %s" % (len(unowned_files), ", ".join(sorted(unowned_files))))
non_top = [r for r in records if r["depth"] > 0]
P("非 lead 顶层(嵌套)的轮次目录: %d 个 %s" % (len(non_top), [r["dir"] for r in non_top]))
P("")
n_all, a_all, b_all, c_all = summarize(records, "全部日期轮次(任意深度)")
top1 = [r for r in records if r["depth"] == 0]
n_top, a_top, b_top, c_top = summarize(top1, "仅 lead 顶层(depth=0)")
ge = [r for r in records if r["ge_111106"]]
ge_top = [r for r in ge if r["depth"] == 0]
lt = [r for r in records if not r["ge_111106"]]
n_ge, a_ge, b_ge, c_ge = summarize(ge, "日期>=20261106 (任意深度)")
n_get, a_get, b_get, c_get = summarize(ge_top, "日期>=20261106 且 lead 顶层")
n_lt, a_lt, b_lt, c_lt = summarize(lt, "日期<20261106 (报告口径外)")
P("")
P("报告声称(§4/§9): 182 = 153 有md + 18 无报告 + 11 空  (口径: >=20261106)")
P("本次实跑(>=20261106, 任意深度): %d = %d + %d + %d" % (n_ge, a_ge, b_ge, c_ge))
P("本次实跑(>=20261106, 仅顶层):   %d = %d + %d + %d" % (n_get, a_get, b_get, c_get))
P("本次实跑(全部日期, 任意深度):   %d = %d + %d + %d" % (n_all, a_all, b_all, c_all))
P("")
P("== 逐目录一行表: name|date|top|rec|md|py|out|bytes|cat ==")
for r in sorted(records, key=lambda x: x["name"]):
    P("%s|%s|top=%d|rec=%d|md=%d|py=%d|out=%d|bytes=%d|cat=%s" % (
        r["name"], r["date"], r["top_files"], r["rec_files"],
        len(r["md"]), len(r["py"]), len(r["out"]), r["total_bytes"], r["category"]))
P("")
P("== C 递归空目录清单（>=20261106 且 lead 顶层 = 报告口径）==")
for r in sorted(ge_top, key=lambda x: x["name"]):
    if r["category"] == "C":
        P("%s (date=%s, 子目录=%s)" % (r["name"], r["date"], r["nested_date_dirs"] or "无"))
ge_non_top = [r for r in ge if r["depth"] > 0]
P(">=20261106 但非顶层的轮次目录: %d 个（不计入报告口径对照，仅登记）" % len(ge_non_top))
for r in sorted(ge_non_top, key=lambda x: x["dir"]):
    P("   %s rec=%d cat=%s" % (r["dir"], r["rec_files"], r["category"]))
P("")
P("== C 递归空目录清单（<20261106 报告口径外，仅登记）==")
for r in sorted(lt, key=lambda x: x["name"]):
    if r["category"] == "C":
        P("%s (date=%s)" % (r["name"], r["date"]))
P("")
P("== B 无报告但有文件目录（>=20261106 且 lead 顶层 = 报告口径）文件明细 ==")
for r in sorted(ge_top, key=lambda x: x["name"]):
    if r["category"] == "B":
        P("-- %s (date=%s, rec=%d 文件)" % (r["name"], r["date"], r["rec_files"]))
        for fd in sorted(r["files"], key=lambda x: x["rel"]):
            P("   %s (%d B)" % (fd["rel"], fd["size"]))
P("")
P("== B 无报告但有文件目录（<20261106 报告口径外，仅登记）==")
for r in sorted(lt, key=lambda x: x["name"]):
    if r["category"] == "B":
        P("-- %s (date=%s, rec=%d): %s" % (
            r["name"], r["date"], r["rec_files"],
            ", ".join(sorted(f["rel"] for f in r["files"]))))

text = "\n".join(lines) + "\n"
sys.stdout.write(text)
with io.open(os.path.join(SELF, "_enum_rounds_stdout.txt"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)
with io.open(os.path.join(SELF, "_enum_rounds.json"), "w", encoding="utf-8", newline="\n") as fh:
    json.dump({"lead": LEAD, "records": records, "unowned_files": sorted(unowned_files),
               "summary_all": [n_all, a_all, b_all, c_all],
               "summary_top1": [n_top, a_top, b_top, c_top],
               "summary_ge_111106": [n_ge, a_ge, b_ge, c_ge],
               "summary_ge_111106_top": [n_get, a_get, b_get, c_get],
               "summary_lt_111106": [n_lt, a_lt, b_lt, c_lt]},
              fh, ensure_ascii=False, indent=1)
print("", flush=True)
print("written: _enum_rounds_stdout.txt / _enum_rounds.json")
