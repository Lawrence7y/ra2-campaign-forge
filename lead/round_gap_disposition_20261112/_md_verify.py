# -*- coding: utf-8 -*-
"""收尾成文前的只读核验：CSV 计数 / 枚举快照计数 / hashlib 指纹实算 / 20261111 顶层目录 mtime。
只读：除本脚本自身外不写任何文件；不重跑枚举脚本。
用法: python -I -X utf8 <绝对路径>/_md_verify.py
"""
import io
import os
import csv
import json
import hashlib
import collections
import datetime

SELF = os.path.dirname(os.path.abspath(__file__))
LEAD = r"D:\Project\ra2-campaign-forge\lead"


def p(s):
    print(s)


def ts(t):
    return datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")


# ---- 1. CSV 计数 ----
csv_path = os.path.join(SELF, "ROUND_GAP_DISPOSITION.csv")
with io.open(csv_path, encoding="utf-8-sig", newline="") as fh:
    reader = csv.DictReader(fh)
    cols = reader.fieldnames
    rows = list(reader)
p("== 1. CSV ==")
p("列: %s" % ",".join(cols))
p("数据行: %d" % len(rows))
cat = collections.Counter(r["类别"] for r in rows)
jud = collections.Counter(r["判定"] for r in rows)
p("类别分布: %s" % "; ".join("%s=%d" % kv for kv in sorted(cat.items())))
p("判定分布: %s" % "; ".join("%s=%d" % kv for kv in sorted(jud.items())))
p("判定合计: %d" % sum(jud.values()))
p("B清单(%d): %s" % (cat.get("无报告有探针或输出", 0),
                    ", ".join(r["目录名"] for r in rows if r["类别"] == "无报告有探针或输出")))
p("C清单(%d): %s" % (cat.get("递归空", 0),
                    ", ".join(r["目录名"] for r in rows if r["类别"] == "递归空")))
p("废弃清单(%d): %s" % (jud.get("废弃", 0),
                     ", ".join(r["目录名"] for r in rows if r["判定"] == "废弃")))
p("补做清单(%d): %s" % (jud.get("补做", 0),
                     ", ".join(r["目录名"] for r in rows if r["判定"] == "补做")))
p("已入他处清单(%d): %s" % (jud.get("已入他处", 0),
                       ", ".join(r["目录名"] for r in rows if r["判定"] == "已入他处")))

# ---- 2. 枚举快照计数（不重跑枚举，仅读已有 JSON）----
with io.open(os.path.join(SELF, "_enum_rounds.json"), encoding="utf-8") as fh:
    data = json.load(fh)
recs = data["records"]
top = [r for r in recs if r["depth"] == 0]
win = [r for r in top if "20261106" <= r["date"] <= "20261111"]
d1111 = sorted((r for r in top if r["date"] == "20261111"), key=lambda x: x["name"])
p("")
p("== 2. _enum_rounds.json 快照 ==")
p("全部记录=%d 顶层记录=%d" % (len(recs), len(top)))
p("窗口[20261106..20261111]: n=%d A=%d B=%d C=%d" % (
    len(win),
    sum(1 for r in win if r["category"] == "A"),
    sum(1 for r in win if r["category"] == "B"),
    sum(1 for r in win if r["category"] == "C")))
p("20261111 顶层: n=%d A=%d B=%d C=%d" % (
    len(d1111),
    sum(1 for r in d1111 if r["category"] == "A"),
    sum(1 for r in d1111 if r["category"] == "B"),
    sum(1 for r in d1111 if r["category"] == "C")))
p("summary_ge_111106_top=%s" % data.get("summary_ge_111106_top"))

# ---- 3. hashlib 指纹实算（与 _final_hashes.txt 对照）----
p("")
p("== 3. hashlib 实算指纹 ==")
for fn in ["ROUND_GAP_DISPOSITION.csv", "_enum_rounds.json", "_enum_rounds_stdout.txt",
           "_probe_digest.txt", "_verify_census_stdout.txt", "_final_hashes.txt"]:
    fp = os.path.join(SELF, fn)
    with open(fp, "rb") as fh:
        h = hashlib.sha256(fh.read()).hexdigest()
    p("%s | %d B | sha256=%s" % (fn, os.path.getsize(fp), h))

# ---- 4. 20261111 顶层目录 mtime / birth(ctime) 只读实测 ----
p("")
p("== 4. 顶层 20261111 目录 mtime 只读实测 (Asia/Shanghai 本机时区) ==")
for r in d1111:
    fp = os.path.join(LEAD, r["name"])
    st = os.stat(fp)
    p("%s | cat=%s rec=%d md=%d | birth(ctime)=%s | mtime=%s" % (
        r["name"], r["category"], r["rec_files"], len(r["md"]),
        ts(st.st_ctime), ts(st.st_mtime)))
p("")
p("== 5. 顶层 20261112 目录 mtime 只读实测 ==")
d1112 = sorted((r for r in top if r["date"] == "20261112"), key=lambda x: x["name"])
for r in d1112:
    fp = os.path.join(LEAD, r["name"])
    st = os.stat(fp)
    p("%s | cat=%s rec=%d md=%d | birth(ctime)=%s | mtime=%s" % (
        r["name"], r["category"], r["rec_files"], len(r["md"]),
        ts(st.st_ctime), ts(st.st_mtime)))
