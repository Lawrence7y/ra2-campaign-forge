#!/usr/bin/env python3
"""汇总 Q2 分类 / Q3 裁决 / Q4 剩余，输出 q4_summary.txt 供 REPORT 引用。"""
import csv, os, sys
from collections import defaultdict, Counter
sys.stdout.reconfigure(encoding="utf-8")
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R91_T1_TIE152"


def rd(n):
    return list(csv.DictReader(open(os.path.join(OUT, n), encoding="utf-8", newline=""), delimiter="\t"))


q2 = rd("q2_classes.tsv")
q3 = rd("tie152_verdicts.tsv")
ORDER = ["1_empty_or_header", "2_json_noaddr", "3_log_noaddr", "4_addr_lt60pct", "5_other"]
NAME = {"1_empty_or_header": "①空/仅表头", "2_json_noaddr": "②纯JSON(无地址)",
        "3_log_noaddr": "③纯日志(无地址无对象帧)", "4_addr_lt60pct": "④含地址<60%", "5_other": "⑤其他"}

L = []
L.append("== Q2 分布（类 / 件数 / 字节 / 代表例）==")
agg = defaultdict(lambda: [0, 0, []])
for r in q2:
    a = agg[r["class"]]
    a[0] += 1; a[1] += int(r["bytes"]); a[2].append(r)
for k in ORDER:
    n, b, items = agg.get(k, [0, 0, []])
    L.append(f"{NAME[k]:26s} {n:3d} 件 / {b:>8d} B")
    if items:
        rep = max(items, key=lambda z: int(z["bytes"]))
        L.append(f"    代表: {rep['rel']}")
        L.append(f"          bytes={rep['bytes']} nlines={rep['nlines']} addr_lines={rep['addr_lines']} 首行={rep['first_line'][:80]}")
L.append("")
L.append("== Q3/Q4 裁决汇总 ==")
va = defaultdict(lambda: [0, 0, []])
for r in q3:
    a = va[r["verdict"]]
    a[0] += 1; a[1] += int(r["bytes"]); a[2].append(r)
for k in ("应排", "应留", "混合", "判不了"):
    n, b, items = va.get(k, [0, 0, []])
    L.append(f"{k:6s} {n:3d} 件 / {b:>8d} B")
L.append(f"合计   {sum(int(r['bytes']) for r in q3)} B / {len(q3)} 件")
L.append("")
L.append("== 类 x 裁决 ==")
x = defaultdict(Counter)
xb = defaultdict(lambda: defaultdict(int))
for r in q3:
    x[r["class"]][r["verdict"]] += 1
    xb[r["class"]][r["verdict"]] += int(r["bytes"])
for k in ORDER:
    L.append(f"{NAME[k]:26s} " + "  ".join(f"{v}={x[k][v]}件/{xb[k][v]}B" for v in ("应排", "应留", "混合", "判不了") if x[k][v]))
L.append("")
L.append("== 判不了 逐件（凭什么判不了）==")
for r in q3:
    if r["verdict"] == "判不了":
        L.append(f"{r['bytes']:>7} B  {r['rel']}")
        L.append(f"         {r['reason']}")
L.append("")
L.append("== 判不了 缺失口径分组 ==")
grp = Counter()
for r in q3:
    if r["verdict"] == "判不了":
        w = r["reason"]
        if "字节差分" in w or "前后对照" in w or "逐字节" in w:
            grp["A 差分/前后对照产物是否计对象记录（对象字节事实 vs 比对结论混编）"] += 1
        elif "完整性核对" in w:
            grp["B 哈希/完整性核对表是否计对象记录（断言 identical=True/False 与对象哈希同件）"] += 1
        elif "字段实读" in w or "逐条核对" in w:
            grp["C 被测数据内容清单/逐项核对（.ini 节表、artmd.ini 字段）是否计对象记录"] += 1
        elif "提取核对" in w:
            grp["B' 提取校验（mix 偏移/sha256+节清单）是否计对象记录"] += 1
        elif "数据内容清单" in w or "字符串表" in w:
            grp["C' 被测数据内容清单（.ini 节表 / .rdata 字符串表）是否计对象记录"] += 1
        elif "数据内容清单" in w or "字符串表" in w or "字段实读" in w or "条目" in w:
            grp["C 被测数据内容清单（.ini 节表 / .rdata 字符串表）是否计对象记录"] += 1
        elif "现场" in w:
            grp["D 带运行现场头（read_at/sha256）的对象清单如何归属"] += 1
        elif "正文缺失" in w:
            grp["E 内容本身缺失（只剩 1 个地址，反汇编体不在文件里）"] += 1
        else:
            grp["Z 其它"] += 1
for k, v in sorted(grp.items()):
    L.append(f"  {k}: {v} 件")
txt = "\n".join(L)
open(os.path.join(OUT, "q4_summary.txt"), "w", encoding="utf-8").write(txt + "\n")
print(txt)
