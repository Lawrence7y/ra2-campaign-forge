# -*- coding: utf-8 -*-
"""成文后自检：统计各表行数、必备关键词、11 个新增目录、15 个取代件、22/12 逐个列出。"""
import io
import os
import re
import hashlib

SELF = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(SELF, "ROUND_GAP_DISPOSITION.md")
with io.open(MD, encoding="utf-8") as f:
    text = f.read()
lines = text.splitlines()

print("size=%d B lines=%d" % (os.path.getsize(MD), len(lines)))

# 各节定位
marks = [("§1", "## §1 "), ("§2", "## §2 "), ("§3", "## §3 "),
         ("§4", "## §4 "), ("§5", "## §5 "), ("§6", "## §6 "), ("§7", "## §7 ")]
pos = []
for tag, needle in marks:
    hits = [i for i, l in enumerate(lines) if l.startswith(needle)]
    print("%s at line %s" % (tag, [h + 1 for h in hits]))
    pos.append((tag, hits[0] if hits else -1))


def section_rows(tag):
    d = dict(pos)
    start = d[tag]
    end = min([v for k, v in pos if v > start] or [len(lines)])
    return lines[start:end]


def table_rows(seg, header_prefix="| "):
    return [l for l in seg if l.startswith(header_prefix) and not l.startswith("|:")
            and not l.startswith("| #") and not l.startswith("| 目录名")
            and not l.startswith("| 序") and not l.startswith("| 类别")
            and not l.startswith("| 判定") and not l.startswith("| 批次")
            and not l.startswith("| 序 |")]


# §2 三类表行数：按 ### 分段
s2 = section_rows("§2")
sub = {}
for i, l in enumerate(s2):
    if l.startswith("### "):
        sub[l.strip()] = i
print("§2 subsections: %s" % list(sub.keys()))
keys = list(sub.keys())
for i, k in enumerate(keys):
    seg = s2[sub[k]: sub[keys[i + 1]] if i + 1 < len(keys) else len(s2)]
    rows = [l for l in seg if re.match(r"^\| \d+ \| `|^ \| ", l) or re.match(r"^\| [a-z0-9_]", l)]
    # 更宽松：以 | 开头且第二列不是表头/分隔
    cnt = 0
    for l in seg:
        if l.startswith("| ") and not l.startswith("|:--") and not l.startswith("| # |") \
           and not l.startswith("| 目录名 |") and not l.startswith("| 类别 |") \
           and not l.startswith("| 序 |") and not l.startswith("| 序 "):
            parts = l.split("|")
            if len(parts) >= 5 and parts[1].strip() and not parts[1].strip().startswith("#"):
                cnt += 1
    print("  %s -> %d table rows" % (k, cnt))

# §3 各表行数
s3 = section_rows("§3")
sub3 = {}
for i, l in enumerate(s3):
    if l.startswith("### "):
        sub3[l.strip()] = i
print("§3 subsections: %s" % list(sub3.keys()))
k3 = list(sub3.keys())
for i, k in enumerate(k3):
    seg = s3[sub3[k]: sub3[k3[i + 1]] if i + 1 < len(k3) else len(s3)]
    cnt = sum(1 for l in seg if re.match(r"^\| \d+ \|", l))
    print("  %s -> %d numbered rows" % (k, cnt))

# 必备关键词
need = ["215", "22", "12", "249", "182", "193", "153", "164",
        "时点差", "活动量", "完成量", "绑定统计时点",
        "进度口径建议", "边界与未验", "取代件", "未验",
        "目录数不能当进度", "原始读数", "空轮算 0",
        "收敛", "第一批", "第二批", "暂缓"]
for w in ["时点差", "活动量", "完成量", "绑定统计时点", "边界与未验",
          "目录数不能当进度", "原始读数", "空轮算 0", "第一批", "第二批", "暂缓",
          "已启动未落盘", "取代件"]:
    print("keyword %-14s : %d" % (w, text.count(w)))

# 11 个新增目录名是否都在 §1 出现
new11 = ["re_round_disposition_20261111", "re_ledger_apply_20261111",
         "re_slot2_finding_20261111", "re_chain_synthesis_20261111",
         "re_dispatch_20261111", "re_session_kickoff_20261111",
         "re_ledger_verify_20261111", "re_round_batch1_20261111",
         "re_chain_synth_v2_20261111", "re_progress_check_20261111",
         "re_progress_xverify_20261111"]
print("11 new dirs all present: %s" % all(n in text for n in new11))
for n in new11:
    print("  %-40s count=%d" % (n, text.count(n)))

# 22 B + 12 C 目录名逐个出现
import csv
with io.open(os.path.join(SELF, "ROUND_GAP_DISPOSITION.csv"), encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
bc = [r["目录名"] for r in rows if r["类别"] == "无报告有探针或输出"]
cc = [r["目录名"] for r in rows if r["类别"] == "递归空"]
ab = [r for r in rows if r["判定"] == "废弃"]
print("B 22 all in report: %s (missing=%s)" % (all(n in text for n in bc), [n for n in bc if n not in text]))
print("C 12 all in report: %s (missing=%s)" % (all(n in text for n in cc), [n for n in cc if n not in text]))
print("废弃 15 取代件非'-': %s" % all(r["取代证据"] != "-" for r in ab))
for r in ab:
    if r["取代证据"] == "-":
        print("  MISSING 取代件: " + r["目录名"])

with io.open(MD, "rb") as f:
    raw = f.read()
print("FINAL MD: %d B sha256=%s" % (len(raw), hashlib.sha256(raw).hexdigest()))
