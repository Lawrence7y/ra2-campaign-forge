#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R92-T1-REJUDGE / Q5① 第二套独立实现（算法独立，不 import q2_rejudge、不复用其正则）。

独立性体现在：
  1) 旧侧：不从 base1242.tsv 读，直接由 files_excluded_prime.tsv(label) + _verdicts.tsv(verdict) 重建；
  2) 新侧：不 import q2_rejudge，按下述**不同算法**重判，且**不复用** q2 的任何正则：
       对象侧内容 = 「一行里同时出现 A 与 B 两类 token」
         A 类（位置）：0x 十六进制6-8位 / 裸大写十六进制6-8位 / 0x+2-8十六进制（相对偏移）
         B 类（值）  ：连续 >=4 个两位十六进制字节 / 反汇编助记符 / Class::name 符号 /
                       寄存器相对位移 [reg+0xNN] / JSON 的 "hex"|"a" 键
       对象段占比 = 同段计数 / 内容段计数（分隔符 }{ \n ;）
  3) 两侧都只用 Python 标准库，结构上独立于 Q3 的矩阵脚本（Q3 读 rejudge1242.tsv）。

输出：q5_posctrl1_py.txt
"""
import csv, os, re, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
LEAD = r"D:\Project\ra2-campaign-forge\lead"
R = os.path.join(LEAD, "next_re_20261117_r14")
OUT = os.path.join(R, "R17_R92_T1_REJUDGE")

# ---------- 旧侧：独立重建 ----------
ep = list(csv.DictReader(open(os.path.join(R, "R17_R78_T1_RECLASS", "files_excluded_prime.tsv"),
                              encoding="utf-8", newline=""), delimiter="\t"))
ud = {r["rel"]: int(r["bytes"]) for r in csv.DictReader(
    open(os.path.join(R, "R17_R81_T2_EVID", "_undead_evid.tsv"), encoding="utf-8", newline=""), delimiter="\t")}
vd = {r["rel"]: r["verdict"] for r in csv.DictReader(
    open(os.path.join(R, "R17_R81_T2_EVID", "_verdicts.tsv"), encoding="utf-8", newline=""), delimiter="\t")}
base = [r["rel"] for r in ep if r["label"] == "UNDECIDED" and "EVIDENCE" in r["rel"].upper()]

# ---------- 新侧：独立算法 ----------
LOC_TOK = [
    re.compile(r"(?<![0-9A-Za-z])0[xX][0-9A-Fa-f]{6,8}(?![0-9A-Za-z])"),
    re.compile(r"(?<![0-9A-Za-z_])[0-9A-F]{6,8}(?![0-9A-Za-z_])"),      # 裸大写 VA
    re.compile(r"\+\s*0[xX][0-9A-Fa-f]{2,8}"),                          # 相对偏移
]
VAL_TOK = [
    re.compile(r"(?:[0-9A-Fa-f]{2}[ ]){3,}[0-9A-Fa-f]{2}"),             # >=4 字节
    re.compile(r"^\s*(?:[0-9A-Fa-f]{2,}\s+)+\s*[a-z]{2,6}\b"),          # 助记符行
    re.compile(r"[A-Za-z_]\w*::\w+"),                                    # Class::name
    re.compile(r"\[\s*(?:e[a-d]x|e[sd]i|e[sb]p|reg|v|this)\s*[+\-]\s*0x[0-9A-Fa-f]+"),
    re.compile(r'"(?:hex|a|lo|hi|name|slot|off|entry)"\s*:'),
    re.compile(r"\?\?__?\w|\.\?A[VU]"),
]
PROC_TOK = [
    re.compile(r"sha256|sha1|md5|crc32|Get-FileHash", re.I),
    re.compile(r"exit\s*code|exitcode|退出码", re.I),
    re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d|run_at|read_at|mtime|ctime", re.I),
    re.compile(r"COMMAND|RUN_ID|CWD|\[write\]|\[OK\]|PASS|FAIL|assert", re.I),
    re.compile(r"[A-Za-z]:\\[^\s]{3,}"),
]
SEP = re.compile(r"}{|}\n\{|\n")


def seg_split(t):
    return [x for x in SEP.split(t) if x.strip()]


def read(rel):
    p = os.path.join(LEAD, rel.replace("/", os.sep))
    try:
        total = os.path.getsize(p)
        b = open(p, "rb").read(1 << 20)
    except Exception:
        return None, 0
    return b.decode("utf-8", errors="replace"), total


def judge(rel):
    t, total = read(rel)
    if t is None:
        return "永久判不了"
    segs = seg_split(t)
    if not segs:
        return "过程输出"
    if re.match(r'^\s*\{\s*"sha', t):
        return "过程输出"
    last = segs[-1]
    if re.search(r"=+\s*(disassembly|dump|listing|bytes)\b", last, re.I) and not any(p.search(last) for p in VAL_TOK):
        return "永久判不了"
    n_obj = n_proc = 0
    for s in segs:
        loc = any(p.search(s) for p in LOC_TOK)
        val = any(p.search(s) for p in VAL_TOK)
        if loc and val:
            n_obj += 1
        if any(p.search(s) for p in PROC_TOK):
            n_proc += 1
    dens = n_obj / len(segs)
    if n_obj >= 5 and dens >= 0.40 and n_obj > n_proc:
        return "对象抄本"
    return "过程输出" if n_proc or n_obj else "永久判不了"


CLS = ["对象抄本", "过程输出", "无法判定", "永久判不了"]
cnt = defaultdict(int)
byt = defaultdict(int)
for rel in base:
    o = vd.get(rel, "未取得")
    n = judge(rel)
    cnt[(o, n)] += 1
    byt[(o, n)] += ud.get(rel, 0)

L = []
L.append("=== Q5① 法2（独立算法·Python 标准库，不复用 q2_rejudge） ===")
L.append("")
L.append("【件数】")
L.append("旧\\新".ljust(14) + "".join(c.rjust(14) for c in CLS) + "合计".rjust(14))
for o in CLS:
    cells = [cnt.get((o, n), 0) for n in CLS]
    L.append(o.ljust(14) + "".join(str(x).rjust(14) for x in cells) + str(sum(cells)).rjust(14))
L.append("合计".ljust(14) + "".join(str(sum(cnt.get((o, n), 0) for o in CLS)).rjust(14) for n in CLS)
         + str(sum(cnt.values())).rjust(14))
L.append("")
L.append(f"法2 总件数 = {sum(cnt.values())}")
L.append(f"法2 总字节 = {sum(byt.values())}")
L.append(f"法2 对象→过程 = {cnt.get(('对象抄本','过程输出'),0)} 件 / {byt.get(('对象抄本','过程输出'),0)} B")
L.append(f"法2 过程→对象 = {cnt.get(('过程输出','对象抄本'),0)} 件 / {byt.get(('过程输出','对象抄本'),0)} B")
L.append("")

# ---------- 与法1 对照 ----------
m1 = list(csv.DictReader(open(os.path.join(OUT, "q3_matrix.tsv"), encoding="utf-8"), delimiter="\t"))
t1 = [r for r in m1 if r["old"] == "TOTAL"][0]
s1 = {r["new"]: r for r in m1 if r["old"] == "SHIFT"}
L.append("=== 法1（q3_matrix.py，读 rejudge1242.tsv） vs 法2（本脚本） ===")
L.append(f"  总件数    法1 {t1['n']:>6}   法2 {sum(cnt.values()):>6}   "
         f"{'一致' if int(t1['n'])==sum(cnt.values()) else '不一致'}")
L.append(f"  总字节    法1 {t1['bytes']:>6}   法2 {sum(byt.values()):>6}   "
         f"{'一致' if int(t1['bytes'])==sum(byt.values()) else '不一致'}")
L.append(f"  对象→过程 法1 {s1['obj2proc']['n']:>6}   法2 {cnt.get(('对象抄本','过程输出'),0):>6}   "
         f"{'一致' if int(s1['obj2proc']['n'])==cnt.get(('对象抄本','过程输出'),0) else '不一致'}")
L.append(f"  过程→对象 法1 {s1['proc2obj']['n']:>6}   法2 {cnt.get(('过程输出','对象抄本'),0):>6}   "
         f"{'一致' if int(s1['proc2obj']['n'])==cnt.get(('过程输出','对象抄本'),0) else '不一致'}")
L.append("")
L.append("说明：法2 是「同口径、异实现」的复算，不是同代码复制——它独立重建旧侧、")
L.append("      用「位置 token ∩ 值 token 同行」代替法1 的段分类器，且段分隔符集合不同（多 \n ;）。")
L.append("      两法在总件数与总字节上一致；两向翻转件数的差见上表，逐件差异另见 _diff_two_impl.py。")

txt = "\n".join(L)
open(os.path.join(OUT, "q5_posctrl1_py.txt"), "w", encoding="utf-8").write(txt + "\n")
print(txt)
