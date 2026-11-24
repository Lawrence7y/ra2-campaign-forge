# -*- coding: utf-8 -*-
# 修正建议撰写员：独立复算两项事实（只读）
import difflib, re, io
ROOT = r"D:\Project\ra2-campaign-forge"

# ---- 路径一：解析 CANDIDATE_LF.diff 的 9 个 hunk，统计 +/- 与替换位删除 ----
with open(ROOT + r"\lead\b2b_candidate_lf_20261107\CANDIDATE_LF.diff", "rb") as f:
    diff_lines = f.read().decode("utf-8", "replace").splitlines()
hunks = []
for ln in diff_lines:
    m = re.match(r"^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", ln)
    if m:
        hunks.append({"header": ln, "plus": 0, "minus": 0,
                      "m_start": int(m.group(1)), "m_cnt": int(m.group(2) or 1)})
cur = None
for ln in diff_lines:
    if re.match(r"^@@", ln):
        if cur: hunks_h.append(cur)
        continue
    # 属于哪个 hunk：按顺序（diff 只有一个文件）
for h in hunks:
    pass
# 重新按顺序扫描
hunk_list = []
cur = None
for ln in diff_lines:
    m = re.match(r"^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", ln)
    if m:
        cur = {"header": ln, "plus": 0, "minus": 0,
               "m_start": int(m.group(1)), "m_cnt": int(m.group(2) or 1)}
        hunk_list.append(cur)
    elif cur is not None:
        if ln.startswith("+") and not ln.startswith("+++"):
            cur["plus"] += 1
        elif ln.startswith("-") and not ln.startswith("---"):
            cur["minus"] += 1
print("== 路径一 CANDIDATE_LF.diff 解析 ==")
print("hunk 数 =", len(hunk_list))
tot_p = sum(h["plus"] for h in hunk_list); tot_m = sum(h["minus"] for h in hunk_list)
print("总计 +" + str(tot_p) + "/-" + str(tot_m))
for i, h in enumerate(hunk_list, 1):
    tag = "" if h["minus"] else "（纯增）"
    e_block = h["m_start"] <= 5984 and (h["m_start"] + max(h["m_cnt"], 1) - 1) >= 5984
    print("  H%02d %s  +%d/-d%s  母本侧区间 %d..%d  含E块5984-5990=%s"
          % (i, h["header"], h["plus"], h["minus"], h["m_start"],
             h["m_start"] + max(h["m_cnt"], 1) - 1, e_block))
    if h["minus"]:
        pass

# ---- 路径二：difflib 母本↔候选 全文重算 ----
with open(ROOT + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py", "rb") as f:
    a = f.read().decode("utf-8", "replace").splitlines(keepends=True)
with open(ROOT + r"\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py", "rb") as f:
    b = f.read().decode("utf-8", "replace").splitlines(keepends=True)
sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
ops = sm.get_opcodes()
deletions = sum((i2 - i1) for tag, i1, i2, j1, j2 in ops if tag in ("delete", "replace"))
insertions = sum((j2 - j1) for tag, i1, i2, j1, j2 in ops if tag in ("insert", "replace"))
print("== 路径二 difflib 全文重算 ==")
print("变更块数 =", sum(1 for tag, *_ in ops if tag != "equal"))
print("deletions =", deletions, " insertions =", insertions,
      " 母本行数 =", len(a), " 候选行数 =", len(b), " 净 =", len(b) - len(a))
# 替换位删除明细（块内 delete/replace 的母本区间）
for tag, i1, i2, j1, j2 in ops:
    if tag == "replace":
        print("  replace 母本 %d-%d（%d 行）→ 候选 %d-%d（%d 行）" % (i1 + 1, i2, i2 - i1, j1 + 1, j2, j2 - j1))
