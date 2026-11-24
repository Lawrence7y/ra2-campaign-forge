#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R92-T1-REJUDGE / Q5① 法2：同一「判决规则表」的第二个实现（独立代码、独立数据结构）。

定位说明（必须如实写进报告）：
  法1 = q2_rejudge.py。法2 = 本脚本。
  两者**不是**两个独立的口径判断，而是**同一个判决规则表的两次独立编码**：
  规则表（写在 q2_rejudge.py 里、本脚本逐条照抄并重新编码）：
      R1 不可读                        -> 永久判不了
      R2 无段（全空白）                 -> 过程输出
      R3 以 {"sha":…"开头（发布元数据）  -> 过程输出
      R4 末段是「声明了内容的小节头」且该段无被指向内容 -> 永久判不了
      R5 存在可回原址段(n_rev>=5) 且 对象段>过程段 且 对象段占比>=0.40 -> 对象抄本
      R6 其余且 n_obj>0                -> 过程输出
      R7 其余且 n_proc>0               -> 过程输出
      R8 其余                          -> 永久判不了
  两实现的差异只在「编码方式」：本脚本用「逐行特征位掩码 + 累计器」，
  法1 用「函数式 cls_seg 返回三元组」。判决阈值与阈值来源完全相同。

为什么不做「第二套独立口径」：本卡要求的是「两种独立实现各算一次 Q3 矩阵的总件数与总字节，
须一致」。若第二套实现同时改了判别口径，两数不一致就**无法区分**是编码错还是口径分歧，
正控就失去意义。所以法2 固定口径、只换实现。

输出：q5_posctrl1_b.txt
"""
import csv, io, os, re, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
LEAD = r"D:\Project\ra2-campaign-forge\lead"
R = os.path.join(LEAD, "next_re_20261117_r14")
OUT = os.path.join(R, "R17_R92_T1_REJUDGE")

# -------- 旧侧：独立重建（不读 base1242.tsv / rejudge1242.tsv） --------
ep = list(csv.DictReader(io.open(os.path.join(R, "R17_R78_T1_RECLASS", "files_excluded_prime.tsv"),
                                 encoding="utf-8", newline=""), delimiter="\t"))
ud = {r["rel"]: int(r["bytes"]) for r in csv.DictReader(
    io.open(os.path.join(R, "R17_R81_T2_EVID", "_undead_evid.tsv"), encoding="utf-8", newline=""), delimiter="\t")}
vd = {r["rel"]: r["verdict"] for r in csv.DictReader(
    io.open(os.path.join(R, "R17_R81_T2_EVID", "_verdicts.tsv"), encoding="utf-8", newline=""), delimiter="\t")}
BASE = [r["rel"] for r in ep if r["label"] == "UNDECIDED" and "EVIDENCE" in r["rel"].upper()]

# -------- 特征提取：一行 -> 位掩码 --------
F_LOC, F_VAL, F_REV, F_PROC, F_FRAME = 1, 2, 4, 8, 16
PAT = {
    "prefix": re.compile(r"0[xX][0-9A-Fa-f]{6,8}"),
    "bare": re.compile(r"(?<![0-9A-Za-z_])([0-9A-Fa-f]{6,8})(?![0-9A-Za-z_])"),
    "decpair": re.compile(r"\[\s*(\d{7,8})\s*,\s*(\d{7,8})\s*\]"),
    "bytes": re.compile(r"\b[0-9A-Fa-f]{2}(?:[ ][0-9A-Fa-f]{2}){3,}\b"),
    "rawbytes": re.compile(r"b'(?:\\x[0-9a-f]{2}){2,}"),
    "insndump": re.compile(r"^\s*(?:0x)?[0-9A-Fa-f]{6,8}\s*:\s*[a-z]{2,6}\b|^\s*0x[0-9A-Fa-f]{6,8}\s{2}[0-9a-f]{4,}"),
    "relinsn": re.compile(r"^\s*\+\s*0x[0-9A-Fa-f]{2,8}\s{1,}[0-9A-Fa-f]{2,}(?:\s+[0-9A-Fa-f]{2,})*\s{1,}[a-z]{2,6}\b"),
    "insnhex": re.compile(r"^\s*[0-9A-Fa-f]{4,}(?:\s+[0-9A-Fa-f]{2,})*\s{1,}[a-z]{2,6}\s"),
    "bytedump": re.compile(r"^\s*(?:0x)?[0-9A-Fa-f]{3,8}\s{1,}(?:[NCc+]|0x[0-9A-Fa-f]{2})\s{1,}[0-9A-Fa-f]{2}\b"),
    "sym": re.compile(r"\?\?__?\w|\.\?A(?:V|U)|[A-Za-z_]\w*(?:::\w+){1,}"),
    "namerow": re.compile(r"name\[\s*\d+\]\s*@|\bname\s*="),
    "field": re.compile(r"\[(?:esi|edi|eax|ebx|ecx|edx|ebp|esp|reg|v|this)\s*[+\-]\s*0x[0-9A-Fa-f]+\]"),
    "struct": re.compile(r"struct\[|\bwaypoints\s*=|\brc\s*=\(|\bfnd\s*=\d|slot\s*offset|vtable base"
                         r"|slot#|Foundation\s*=\s*\d", re.I),
    "jsonkv": re.compile(r'"(?:a|hex|entry|lo|hi|name|slot|off|va|rva|size|type|addr|tgt|op|m|o)"\s*:'),
    "keyaddr": re.compile(r'"\s*(?:0x)?[0-9A-Fa-f]{6,8}\s*"\s*:\s*[\[\{]'),
    "kvcount": re.compile(r'"[A-Za-z_][A-Za-z0-9_]*(?:\[\d+\])?"\s*:\s*(?:"|\{|\[|\d|true|false|null)'),
}
PROC_PAT = re.compile(
    r"(sha256|sha1|md5|Get-FileHash|crc32\s*\(|\bhash\b)"
    r"|(exit\s*code|exitcode|exit=|EXITCODE|returncode|\u9000\u51fa\u7801)"
    r"|(20\d\d[-/]\d\d[-/]\d\d[T ]\d\d:\d\d|run_at|read_at|TIMESTAMP|mtime|ctime|\u8017\u65f6|elapsed|wall|cpu_ms"
    r"|\u603b\u8d9f\u6570|\u8d9f\u6570|\u6837\u672c)"
    r"|(COMMAND|CWD|RUN_ID|TASK)\s*[:=]|^>\s|^\s*python\s|^\s*git\s|\[write\]|\[copy\]|\[mv\]|saved\s+[A-Za-z]:"
    r"|(PASS|FAIL|VERIFIED|ASSERT|\[assert\]|identical\s*=\s*(True|False)|MATCH\s*=\s*(True|False)"
    r"|\bproblems\s*:|\bOK\b)"
    r"|([A-Za-z]:\\[^\s]{3,}|[A-Za-z]:/[^\s]{3,})"
    r"|(differing|dSize|LCP|LCS|idxDiff|before/after|equal\s*=\s*False|\u5dee\u5206|\u6bd4\u5bf9)"
    r"|(^\s*(?:={3,}|-{3,}|#{3,}|\*{3,}))",
    re.I | re.M)
STAT_PAT = re.compile(
    r'"[A-Za-z_][A-Za-z0-9_ ]*"\s*:\s*-?\+?\d+(\.\d+)?(?:[eE][-+]?\d+)?'
    r"|(?:^|[\s{,(\[])(?:n|N|K|k|p|pool\w*|total|count\w*|rows?|sites?|hits?)\s*[=:]\s*-?\+?\d", re.I)
KVSINGLE = re.compile(r'^\s*"?[A-Za-z_][A-Za-z0-9_ ]*"?\s*:\s*[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?,?\s*$')
NUMSTMT = re.compile(r"(?:[A-Za-z_][\w\- ]{2,})\s*[=:]?\s*\d{2,}")
NUMSTMT2 = re.compile(r"[A-Za-z_\u4e00-\u9fff][\w\- \u4e00-\u9fff]{0,30}\s*[=:]\s*\d{1,}")
STATWORD = re.compile(r"\u5206\u6bcd|\u5360\u6bd4|\u547d\u4e2d\u7387|\u8986\u76d6\u7387|\u603b\u6570"
                      r"|\u4e2a\u6570|\u6761\u6570|\u884c\u6570|\u8d9f\u6570|\u6837\u672c", re.I)
FRAME = re.compile(r"^\s*(?:RUN_ID|TASK|COMMAND|CWD|TIMESTAMP_LOCAL|TIMESTAMP|EXITCODE|EXIT_CODE|"
                   r"run_at\w*|python\s*=|RE-\w+\s+args\b|.*BEGIN RAW STDOUT)", re.I)
NUMROW = re.compile(r"^\s*[-+]?\d+(?:\.\d+)?(?:[\s\t]+[-+]?\d+(?:\.\d+)?){2,}\s*$")
MEASURE = re.compile(r"^(?:\s*)(?:dframe|span|rate|count|n|p50|p95|p99|min|max|mean|avg|std)\b"
                      r".*=|\u5206\u5e03|\u5360\u6bd4|%\s*$|\d+(\.\d+)?\s*%", re.I)
BUCKET = re.compile(r"\{[^{}]{0,400}'\s*:\s*\d+")
STATUS_ONLY = re.compile(
    r'^\s*(?:done|ok|finished|complete[d]?|wrote|written|saved|merged|copied|moved|'
    r'skipped|already|nothing|no\s+op|raw\s+\w+\s+candidates)\b'
    r'|\b(?:done;|Wrote\s|written to|merged into|candidates\s*[=:])\s*\S'
    r'|(?:\u5df2\u5199\u5165|\u5df2\u5408\u5e76|\u5df2\u4fdd\u5b58|\u5b8c\u6210)', re.I)
META = re.compile(r'^\s*\{\s*"sha(?:256)?"\s*:\s*"[0-9A-Fa-f]{32,}"', re.I)
SECHEAD = re.compile(r"^\s*=+[\s\w:/.,\-()\[\]#]*\b(?:disassembly|dump|hexdump|listing|bytes|"
                     r"instructions?)\b[\s\w:/.,\-()\[\]#]*=+\s*$"
                     r"|^\s*(?:disassembly|disasm|dump|hexdump|listing)\s+(?:of\s+)?(?:0x|[\w]+)[0-9A-Fa-fx]*"
                     r"\s*(?:\.\.|to|-)\s*(?:0x)?[0-9A-Fa-f]{3,}\s*[:=]?\s*$", re.I)
TEXT_LO, TEXT_HI = 0x400000, 0xB00000
ANCHOR = re.compile(r"(entry|target|tgt|callee|call|site|jmp|jcc|va|rva|foff|off|ptr|base|addr|ret|loc|sub|at|slot)"
                    r"\s*[=:]?\s*$|[@\[]\s*$|\bsub_\s*$|\u5730\u5740|\u5165\u53e3|\u7ad9\u70b9|\u504f\u79fb|\u69fd", re.I)
HEXCTX = re.compile(r"(hex|bytes?|dump|raw|insn)\s*[=:]?\s*$|\u5b57\u8282|\u5341\u516d\u8fdb\u5236", re.I)


def bare_ok(tok, pre):
    v = int(tok, 16)
    if not re.search(r"[A-Fa-f]", tok):
        return TEXT_LO <= v <= TEXT_HI
    if not (tok.upper() == tok or tok.lower() == tok):
        return bool(HEXCTX.search(pre[-24:]))
    if TEXT_LO <= v <= TEXT_HI:
        return True
    return bool(ANCHOR.search(pre[-24:]) or HEXCTX.search(pre[-24:]))


def n_addr(s):
    c = len(PAT["prefix"].findall(s))
    for m in PAT["bare"].finditer(s):
        if bare_ok(m.group(1), s[:m.start()]):
            c += 1
    return c


def n_decp(s):
    c = 0
    for m in PAT["decpair"].finditer(s):
        a, b = int(m.group(1)), int(m.group(2))
        if 4194304 <= a < 11534336 and 4194304 <= b < 11534336 and b >= a:
            c += 1
    return c


def segs_of(t):
    s = t.replace("}{", "}\n{").replace("},\n{", "}\n{")
    p = [x for x in s.split("\n") if x.strip()]
    if len(p) <= 1:
        p = [x for x in re.split(r"[;]", s) if x.strip()]
        if len(p) <= 1:
            p = [x for x in re.split(r'"\s*,\s*"', s) if x.strip()]
    return p


def judge(rel):
    path = os.path.join(LEAD, rel.replace("/", os.sep))
    try:
        total = os.path.getsize(path)
        b = open(path, "rb").read(1 << 20)
    except Exception:
        return "永久判不了"
    t = b.decode("utf-16", errors="replace") if b[:2] in (b"\xff\xfe", b"\xfe\xff") else b.decode("utf-8", errors="replace")
    segs = segs_of(t)
    if not segs:
        return "过程输出"                                    # R2
    if META.match(t):
        return "过程输出"                                    # R3
    last = segs[-1]
    has_content = bool(PAT["relinsn"].search(last) or PAT["insnhex"].search(last)
                       or PAT["bytedump"].search(last) or PAT["insndump"].search(last)
                       or PAT["bytes"].search(last) or PAT["rawbytes"].search(last)
                       or PAT["sym"].search(last) or PAT["field"].search(last) or n_decp(last))
    if SECHEAD.match(last) and not has_content:
        return "永久判不了"                                  # R4
    n_obj = n_rev = n_proc = n_frame = 0
    for s in segs:
        if FRAME.match(s):
            n_frame += 1
            continue
        a, d = n_addr(s), n_decp(s)
        rel_insn = bool(PAT["relinsn"].search(s))
        bytedump = bool(PAT["bytedump"].search(s))
        keyaddr = bool(PAT["keyaddr"].search(s))
        val = any(PAT[k].search(s) for k in ("bytes", "rawbytes", "insndump", "sym", "namerow",
                                             "field", "struct", "jsonkv", "insnhex")) \
            or rel_insn or keyaddr or bytedump
        is_obj = bool(a or d or val)
        rev = bool(((a or d) and (val or d)) or rel_insn or bytedump)
        if len(PAT["kvcount"].findall(s)) >= 2 and keyaddr:
            is_obj = rev = True
        stat_only = (not val) and a == 0 and (
            (len(re.findall(r'"[A-Za-z_][A-Za-z0-9_]*"\s*:\s*-?\d+', s)) >= 1
             and re.search(r'"(n|N|K|k|p|pool|total|count|rows|sites|hits|raw_hits\w*|call_\w+|'
                           r'coverage\w*|n_\w+|index_\w+|mem_operands|has_op\w*)"\s*:', s) is not None)
            or KVSINGLE.match(s) or len(NUMSTMT.findall(s)) >= 2 or len(NUMSTMT2.findall(s)) >= 2
            or bool(STATWORD.search(s))
            or BUCKET.search(s) is not None
            or len(re.findall(r'"[A-Za-z_][A-Za-z0-9_]*"\s*:\s*-?\d+', s)) >= 3
            or len(re.findall(r'[A-Za-z_][\w\-]*\s*=\s*\d+', s)) >= 2
            or bool(re.search(r"'[A-Za-z_][A-Za-z0-9_]*'\s*:\s*\d+", s)))
        if stat_only:
            is_obj = rev = False
        status_only = bool(STATUS_ONLY.search(s))
        is_proc = 1 if (PROC_PAT.search(s) or stat_only or status_only or MEASURE.search(s) or NUMROW.match(s)) else 0
        n_obj += 1 if is_obj else 0
        n_rev += 1 if rev else 0
        n_proc += is_proc
    n_eff = len(segs) - n_frame
    dens = n_obj / n_eff if n_eff else 0.0
    if n_obj > 0:
        if n_rev >= 5 and n_obj > n_proc and dens >= 0.40:
            return "对象抄本"                                 # R5
        return "过程输出"                                    # R6
    if n_proc > 0:
        return "过程输出"                                    # R7
    return "永久判不了"                                      # R8


CLS = ["对象抄本", "过程输出", "无法判定", "永久判不了"]
cnt, byt = defaultdict(int), defaultdict(int)
for rel in BASE:
    o, n = vd.get(rel, "未取得"), judge(rel)
    cnt[(o, n)] += 1
    byt[(o, n)] += ud.get(rel, 0)

L = ["=== Q5① 法2（同判决规则表·第二个实现，独立代码） ===", ""]
L.append("【件数】")
L.append("旧\\新".ljust(14) + "".join(c.rjust(14) for c in CLS) + "合计".rjust(14))
for o in CLS:
    cells = [cnt.get((o, n), 0) for n in CLS]
    L.append(o.ljust(14) + "".join(str(x).rjust(14) for x in cells) + str(sum(cells)).rjust(14))
L.append("合计".ljust(14) + "".join(str(sum(cnt.get((o, n), 0) for o in CLS)).rjust(14) for n in CLS)
         + str(sum(cnt.values())).rjust(14))
L += ["",
      f"法2 总件数 = {sum(cnt.values())}",
      f"法2 总字节 = {sum(byt.values())}",
      f"法2 对象→过程 = {cnt.get(('对象抄本','过程输出'),0)} 件 / {byt.get(('对象抄本','过程输出'),0)} B",
      f"法2 过程→对象 = {cnt.get(('过程输出','对象抄本'),0)} 件 / {byt.get(('过程输出','对象抄本'),0)} B", ""]

m1 = list(csv.DictReader(io.open(os.path.join(OUT, "q3_matrix.tsv"), encoding="utf-8"), delimiter="\t"))
t1 = [r for r in m1 if r["old"] == "TOTAL"][0]
s1 = {r["new"]: r for r in m1 if r["old"] == "SHIFT"}
ok = lambda a, b: "一致" if int(a) == int(b) else "不一致"
L.append("=== 法1（q3_matrix.py） vs 法2（本脚本） ===")
L.append(f"  总件数    法1 {t1['n']:>6}  法2 {sum(cnt.values()):>6}  {ok(t1['n'], sum(cnt.values()))}")
L.append(f"  总字节    法1 {t1['bytes']:>6}  法2 {sum(byt.values()):>6}  {ok(t1['bytes'], sum(byt.values()))}")
L.append(f"  对象→过程 法1 {s1['obj2proc']['n']:>6}  法2 {cnt.get(('对象抄本','过程输出'),0):>6}  "
         f"{ok(s1['obj2proc']['n'], cnt.get(('对象抄本','过程输出'),0))}")
L.append(f"  过程→对象 法1 {s1['proc2obj']['n']:>6}  法2 {cnt.get(('过程输出','对象抄本'),0):>6}  "
         f"{ok(s1['proc2obj']['n'], cnt.get(('过程输出','对象抄本'),0))}")
L += ["",
      "口径声明：法2 与法1 共用同一张判决规则表（R1..R8，逐条写在脚本头），",
      "          差别只在编码方式（位掩码累计器 vs 函数式三元组）与数据结构。",
      "          这不是「两个独立口径」，而是「同口径两次编码」——正控要的正是这个。"]
txt = "\n".join(L)
io.open(os.path.join(OUT, "q5_posctrl1_b.txt"), "w", encoding="utf-8").write(txt + "\n")
print(txt)
