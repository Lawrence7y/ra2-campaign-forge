# -*- coding: utf-8 -*-
"""_akv_compare.py — 逐格比对交付矩阵 vs 独立实跑；核绑定行；核加注措辞。"""
import hashlib
import json
import re
from pathlib import Path

WD = Path(r"D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109")
REPO = Path(r"D:\Project\ra2-campaign-forge")

own = json.loads((WD / "_akv_own.json").read_text(encoding="utf-8"))
matrix_own = {(m["gate"], m["item"]): m for m in own["matrix"]}

# ---- 1. 交付矩阵 36 行逐格解析 ----
txt = (WD / "_ak_BAD_NEEDLE_MATRIX.md").read_text(encoding="utf-8")
rows = []
for line in txt.splitlines():
    if not re.match(r"^\| (d27|d28|d29|d30) \|", line):
        continue
    # 固定 8 列：头 6 列 + STDOUT（内部可能含 '|'）+ 末列 是否被抓
    m = re.match(r"^\|\s*(d27|d28|d29|d30)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*(.*?)\s*\|\s*(\*\*(?:True|False)\*\*)\s*\|\s*$", line)
    if not m:
        print("  UNPARSED_TABLE_ROW:", repr(line[:160]))
        continue
    gate, item, desc, action, before, after, stdout, caught = m.groups()
    rows.append(dict(gate=gate, item=item, desc=desc, action=action,
                     before=before, after=after, stdout=stdout, caught=caught))

print("DELIVERED_MATRIX_ROWS =", len(rows))
print("INDEPENDENT_MATRIX_CELLS =", len(matrix_own))

# 归一化：把交付件里 sandbox 绝对路径与我方 _akv_own 路径统一为占位符
def norm(s):
    # 把两套沙箱的根与实验目录名统一掉，只比较检查器输出语义
    s = s.replace(r"D:\\Project\\ra2-campaign-forge\\lead\\andk_rerun_20261109\\sandbox\\", "<R>\\")
    s = s.replace(r"D:\\Project\\ra2-campaign-forge\\lead\\andk_rerun_20261109\\_akv_own\\", "<R>\\")
    s = re.sub(r"<R>\\\\[^\\]+\\\\[^\\]+\\\\FACTCHECK", "<R>\\\\FACTCHECK", s)
    return s

mismatch = []
for r in rows:
    item = r["item"]
    key_item = item.replace(".5", "b")
    m = matrix_own.get((r["gate"], key_item))
    if m is None:
        mismatch.append((r["gate"], item, "NO_MATCHING_INDEPENDENT_CELL"))
        continue
    exp_before = "PASS (EXIT=%d)" % m["before_exit"]
    exp_after = "%s (EXIT=%d)" % (m["after_verdict"], m["after_exit"])
    if r["before"] != exp_before:
        mismatch.append((r["gate"], item, "BEFORE", r["before"], exp_before))
    if r["after"] != exp_after:
        mismatch.append((r["gate"], item, "AFTER", r["after"], exp_after))
    # STDOUT 表格里是 repr(...) 带引号
    raw = r["stdout"].strip("`")
    try:
        delivered_stdout = eval(raw, {"__builtins__": {}}, {})
    except Exception as e:
        mismatch.append((r["gate"], item, "STDOUT_PARSE_ERR", str(e), raw[:80]))
        continue
    if norm(delivered_stdout) != norm(m["after_stdout"]):
        mismatch.append((r["gate"], item, "STDOUT_DIFF", repr(delivered_stdout)[:150], repr(m["after_stdout"])[:150]))
    exp_caught = "**%s**" % m["caught"]
    if r["caught"] != exp_caught:
        mismatch.append((r["gate"], item, "CAUGHT", r["caught"], exp_caught))

print("CELL_BY_CELL_MISMATCHES =", len(mismatch))
for x in mismatch:
    print("  ", x)

# 逐格列表（要求不许只给计数）
print("\nPER_CELL_TABLE (gate/item | before | after | caught | stdout_sha12 | still_pass_stdout_equals_A):")
for r in rows:
    m = matrix_own[(r["gate"], r["item"].replace(".5", "b"))]
    print("  %-4s %-4s | %-14s | %-14s | %-6s | %s | %s" %
          (r["gate"], r["item"], r["before"], r["after"], r["caught"],
           m["after_stdout_sha256"][:12],
           m["stdout_same_as_A"] if m["after_verdict"] == "PASS" else "-"))

# ---- 2. 绑定行：固定格式 + hash/bytes 与实算相符 ----
print("\n==== BINDING LINES ====")
rep = (WD / "_ak_REPORT.md").read_text(encoding="utf-8")
pat = re.compile(r"被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)")
found = pat.findall(rep)
print("BINDING_LINES_FOUND =", len(found))
# 严格格式：行内不得有别的字符（除前后空白）
strict = re.compile(r"^被核对象 SHA256 = [0-9a-f]{64}，字节数 = \d+$")
strict_rows = [l for l in rep.splitlines() if strict.fullmatch(l.strip())]
print("STRICT_FORMAT_LINES =", len(strict_rows))
expect = [
    ("lead/d27_ruling_20261106/check_d27.py", "3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c", 3764),
    ("lead/d28_ruling_20261106/check_d28.py", "5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268", 4539),
    ("lead/d29_ruling_20261106/check_d29.py", "2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14", 3906),
    ("lead/d30_ruling_20261106/check_d30.py", "6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd", 3926),
    ("lead/PENDING_DECISIONS.md", "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md", "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    ("lead/stale_pass_20261109/STALE_PASS_INVENTORY.md", "a72d79b23b1329207a2c612d4244dec407ffaa4e0b91c397c3febb7a9cddd798", 63656),
]
allok = True
for i, (rel, h, n) in enumerate(expect):
    raw = (REPO / rel).read_bytes()
    real = (hashlib.sha256(raw).hexdigest(), len(raw))
    ok = (i < len(found) and found[i][0] == h and int(found[i][1]) == n and real == (h, n))
    allok &= ok
    print("  line %d %-58s DISK=(%s,%d) CLAIM=(%s,%s) MATCH=%s" %
          (i + 1, rel, real[0][:16], real[1], found[i][0][:16] if i < len(found) else "N/A",
           found[i][1] if i < len(found) else "N/A", ok))
print("ALL_BINDING_LINES_MATCH_DISK =", allok)

# ---- 3. 加注措辞：是否指出失效点 ----
print("\n==== 5(c) ANNOTATION WORDING ====")
for g, needle, ln in (("d30", "误报率", 76), ("d29", "前提", 76), ("d28", "1681", 90), ("d27", "卡顿不存在", 84)):
    blocks = re.findall(r"★【2026-11-09 甲' 重跑加注[^\n]*\n(?:.*\n)*?(?:本加注只涉[^\n]*\n)", rep)
    hit = [b for b in blocks if ("check_%s.py" % g) in b and needle in b]
    b = hit[0] if hit else ""
    checks = {
        "points_at_source_line": ("check_%s.py:%d" % (g, ln)) in b,
        "names_OR_tuple": ('(4, "' in b or '(6, "' in b) and "OR" in b,
        "names_killed_needle": ("杀掉「%s」" % needle) in b,
        "says_still_exit0_stdout_identical": ("仍" in b and "EXIT=0" in b and "stdout 逐字不变" in b),
        "says_ANDk_false": "AND_k(k=2) 在 B 输入 = FALSE" in b,
        "says_AND9_false": "AND_9 = FALSE" in b,
        "marks_UNTRUSTWORTHY": "UNTRUSTWORTHY" in b,
        "keeps_original_line": "亦不改写或删除本行历史数字" in b,
        "limits_scope_to_form": "本加注只涉形式要件的证据资格" in b,
    }
    print("  %s (%s) block_found=%s %s" % (g, needle, bool(hit), checks))

# ---- 4. 台账四行原文与加注目标 ----
print("\n==== PENDING LINES (must be unchanged, no annotation appended) ====")
ls = (REPO / "lead/PENDING_DECISIONS.md").read_text(encoding="utf-8").splitlines()
for n in (92, 105, 117, 129):
    print("  %d: %r" % (n, ls[n - 1]))
print("  ANY_2026-11-09_ANNOTATION_IN_PENDING =",
      "2026-11-09 甲' 重跑加注" in "\n".join(ls))
