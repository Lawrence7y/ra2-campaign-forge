# -*- coding: utf-8 -*-
"""A1 勘误映射 · W9 组探针（纯只读；零 ra2tool.Engine、零真机、零采样）。
核五件事：
 1) W9_SINGLESTEP.md §7 必须改项条数与各行号；各条「汇总件 §X 已…」自declared标注位置；
 2) 20 条在汇总件正文（§0-§8）的落实行号（逐条 grep 坐实），以及漏引（BASELINE_A4_PROPOSAL 等）；
 3) PENDING_DECISIONS.md 当前盘面（07:5x）行号漂移实测；
 4) qc151_trip.py:4575 守卫行、except.txt.final_isolated L17/L18、_w9_q3_final_out.txt:89 错值；
 5) Q4/Q5 回件对 QC124/断点/人为 的零命中（存在性事实）。
运行：python -I -X utf8 D:/.../A1_ERRATA_MAP/_a1_w9_probe.py > _a1_w9_probe_out.txt 2>&1
"""
import hashlib
import re

ROOT = r"D:/Project/ra2-campaign-forge"
W9 = ROOT + r"/lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/W9_SINGLESTEP.md"
Q3M = ROOT + r"/lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/Q3_MECHANISM.md"
Q4R = ROOT + r"/lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/Q4_RELATION.md"
Q5R = ROOT + r"/lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/Q5_ROUTES.md"
Q3OUT = ROOT + r"/lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/_w9_q3_final_out.txt"
PD = ROOT + r"/lead/PENDING_DECISIONS.md"
RD22 = ROOT + r"/lead/re_line_20261105/D22_RULING/RULING_D22.md"
QC151 = ROOT + r"/out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"
AVF = ROOT + r"/out/re_work/zcode_live/zc11/evidence/closeout/except.txt.final_isolated"


def read_lines(p):
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read().split("\n")


def sha(p):
    with open(p, "rb") as f:
        b = f.read()
    return hashlib.sha256(b).hexdigest(), len(b)


def findall(lines, pat, regex=False):
    hits = []
    for i, l in enumerate(lines):
        if (re.search(pat, l) if regex else (pat in l)):
            hits.append(i + 1)
    return hits


def snippet(lines, n, width=100):
    l = lines[n - 1]
    return (l[:width] + ("…" if len(l) > width else "")).replace("\r", "")


h9, b9 = sha(W9)
print("== 0. 绑定自算 ==")
print("W9_SINGLESTEP.md SHA256 =", h9)
print("W9_SINGLESTEP.md bytes  =", b9)

L = read_lines(W9)
i7 = next(i for i, l in enumerate(L) if l.startswith("## 7 必须改项"))
i8 = next(i for i, l in enumerate(L) if l.startswith("## 8 诚实账"))
print("\n== 1. W9 §7 条数与行号 ==")
print("SEC7_RANGE = %d..%d" % (i7 + 1, i8 + 1))
items = [(i + 1, l) for i, l in enumerate(L) if i7 < i < i8 and re.match(r"^\d+\. \*\*", l)]
print("SEC7_ITEM_COUNT =", len(items))
for n, (ln, l) in enumerate(items, 1):
    print("ITEM %02d line=%d | %s" % (n, ln, snippet(L, ln, 40)))

print("\n== 2. 自declared标注行号（模式『汇总件 §』） ==")
for ln in findall(L, "汇总件 §"):
    print("line %d | %s" % (ln, snippet(L, ln, 60)))

print("\n== 3. 逐条落实行号实测（正文 grep） ==")
CHECKS = [
    ("W9-1 收窄句『正确结论限定为』", "正确结论限定为"),
    ("W9-1 删除令『必须删除』", "必须删除"),
    ("W9-2 主链 QC124_VERDICT.json 引用", "QC124_VERDICT.json"),
    ("W9-2 VERDICT_T11.md:148", "VERDICT_T11.md:148"),
    ("W9-2 ERRATA_EXCEPT_RESTORE.md:12", "ERRATA_EXCEPT_RESTORE.md:12"),
    ("W9-2 未独立复现注『未独立复现』", "未独立复现"),
    ("W9-3 反例表『口径外反例』", "口径外反例"),
    ("W9-3 qc119_after_entry", "qc119_after_entry"),
    ("W9-3 qc123_rc1_only", "qc123_rc1_only"),
    ("W9-3 except_pre_qc124", "except_pre_qc124"),
    ("W9-4 降级句『REFUTED 降为 PARTIAL』", "REFUTED 降为 PARTIAL"),
    ("W9-4 『QC124 书面记录支持 DR0 施动者』", "QC124 书面记录支持 DR0 施动者"),
    ("W9-5 Q1 边界『CONFIRMED 的边界』", "CONFIRMED 的边界"),
    ("W9-5 Q2 并排『仅核函数边界』", "仅核函数边界"),
    ("W9-6 §6 起点替换『精确表述替换』", "精确表述替换"),
    ("W9-7 分档改称『不是「(i) 残件类」』", "不是「(i) 残件类」"),
    ("W9-7 缺口改称『游戏自身崩溃可归因证据』", "游戏自身崩溃可归因证据"),
    ("W9-8 §6 指针『行号归属（见 §7 #8）』", "行号归属（见 §7 #8）"),
    ("W9-9 PD 失效『行号系统性失效』", "行号系统性失效"),
    ("W9-9 冲突『授权口径冲突』", "授权口径冲突"),
    ("W9-10 正确 VA『0x7E8880,4)=04 00 00 80』", "0x7E8880,4)=04 00 00 80"),
    ("W9-11 『列为**未验**』", "列为**未验**"),
    ("W9-11 『字节级事实」限定口径』", "字节级事实」限定口径"),
    ("W9-12 全仓计数『259 份』", "259 份"),
    ("W9-13 『「235 行」应为』", "「235 行」应为"),
    ("W9-14 『01:28:18」是』", "01:28:18」是"),
    ("W9-15 『IMM_TARGETS_TO_VA 0』", "IMM_TARGETS_TO_VA 0"),
    ("W9-15 前序指令『0x7CFC9B 8B 54 F9 04』", "0x7CFC9B 8B 54 F9 04"),
    ("W9-16 『原始 80 / 净 66』", "原始 80 / 净 66"),
    ("W9-17 『后续副本』", "后续副本"),
    ("W9-18 『44/107』", "44/107"),
    ("W9-19 守卫措辞『不以本趟是否异常为条件』", "不以本趟是否异常为条件"),
    ("W9-20 『已做部分』", "已做部分"),
    ("W9-20 『partVerdict=CONFIRMED』冲突", "partVerdict=CONFIRMED"),
]
for label, pat in CHECKS:
    print("%s -> lines %s" % (label, findall(L, pat)))

print("\n== 4. 漏引/缺失实测 ==")
print("BASELINE_A4_PROPOSAL -> lines %s（若仅 §7 本条 = 正文漏引）" % findall(L, "BASELINE_A4_PROPOSAL"))
print("QC124_VERDICT.json:74-87 的『74-87』 -> lines %s" % findall(L, "74-87"))
print("Q4 时刻 02:15:47 -> lines %s（期望 [] = 未进正文）" % findall(L, "02:15:47"))
print("Q4 时刻 02:10:46 -> lines %s（期望 [] = 未进正文）" % findall(L, "02:10:46"))
print("final_isolated 在 W9 内 -> lines %s" % findall(L, "final_isolated"))
print("final_isolated L18/L19 勘误在 W9 正文（§0-§6）无重述：查『splitlines_total』 -> lines %s" % findall(L, "splitlines_total"))

print("\n== 5. PENDING_DECISIONS.md 当前盘面漂移实测 ==")
P = read_lines(PD)
print("PD total lines =", len(P) - 1 if P and P[-1] == "" else len(P))
for pat in ["D-22 已裁决", "D-15 已裁决", "D-13（2026-11-04 立", "E3 暂不执行", "授权面"]:
    for ln in findall(P, pat):
        print("PD:%d | %s" % (ln, snippet(P, ln, 88)))
for n in (78, 79, 80, 114, 121, 123, 144):
    print("PD:%d | %s" % (n, snippet(P, n, 88)))

print("\n== 6. 其它字节/文本现场 ==")
C = read_lines(QC151)
print("qc151_trip.py:4575 | %s" % snippet(C, 4575, 60))
# final_isolated 必须按二进制 + b'\n' 切（W9 作者口径；文本模式 universal newlines 会把
# L1 的双 CR 变成额外换行、行号整体 +1 —— 本次首跑实测踩中，已改二进制重核）
with open(AVF, "rb") as f:
    raw = f.read()
AB = raw.split(b"\n")
print("final_isolated LF count =", raw.count(b"\n"))
print("final_isolated splitlines count =", len(raw.splitlines()))
print("final_isolated L1 repr | %r" % AB[0])
print("final_isolated L17 repr | %r" % AB[16])
print("final_isolated L18 repr | %r" % AB[17][:78])
print("final_isolated L19 repr | %r" % AB[18][:40])
print("final_isolated L62 repr | %r" % AB[61])
O = read_lines(Q3OUT)
print("_w9_q3_final_out.txt:89 | %s" % O[88].strip())
print("Q3_MECHANISM.md 含『7E8888』行 -> %s（期望 [] = 错值未进正文）" % findall(read_lines(Q3M), "7E8888"))
print("Q3_MECHANISM.md 含『7E8880』行 -> %s" % findall(read_lines(Q3M), "7E8880"))
Q4 = read_lines(Q4R)
Q5 = read_lines(Q5R)
print("grep -c QC124 Q4_RELATION.md =", sum(1 for l in Q4 if "QC124" in l))
print("grep -c QC124|断点|人为 Q5_ROUTES.md =", sum(1 for l in Q5 if ("QC124" in l or "断点" in l or "人为" in l)))
print("Q5_ROUTES.md 头部 1-16 行：")
for i in range(16):
    print("  Q5:%d | %s" % (i + 1, snippet(Q5, i + 1, 72)))
for pat in ["partVerdict", "CONFIRMED", "verdict"]:
    print("Q5 含『%s』行 -> %s" % (pat, findall(Q5, pat)))
for ln in findall(Q5, "CONFIRMED"):
    print("Q5_ROUTES.md:%d | %s" % (ln, snippet(Q5, ln, 72)))
R = read_lines(RD22)
print("RULING_D22.md:3 | %s" % snippet(R, 3, 40))
print("\nPROBE DONE -- exit 0")
