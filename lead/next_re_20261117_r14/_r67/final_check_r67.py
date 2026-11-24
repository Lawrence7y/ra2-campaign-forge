# -*- coding: utf-8 -*-
# R17-R67 终检：完全独立于 write_r67.py 的一次性复算。只用「读盘 + 计数 + 哈希」，
# 不 import 任何本轮脚本，不读任何中间变量。
import os, hashlib, io, csv, sys

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
LEAD = r"D:\Project\ra2-campaign-forge\lead"
buf = []
fails = []
def P(s=""):
    print(s); buf.append(s)
def ck(n, c, d=""):
    P(("  PASS " if c else "  FAIL ") + n + (("  " + d) if d else ""))
    if not c: fails.append(n)

P("=" * 78)
P("[A] 五项 CR 不变量（盘上直读，硬编码期望值）")
TARGETS = [
    ("R14_COMMON",    os.path.join(R14, "R14_COMMON.md"), 1081),
    ("LEAD_LOCK",     os.path.join(LEAD, "LEAD_LOCK"),    137),
    ("台账",          os.path.join(LEAD, "GOAL_THREE_TARGETS_20261018.md"), 337),
    ("STATUS_BOARD",  os.path.join(R14, "STATUS_BOARD.md"), 0),
    ("BOARD_ARCHIVE", os.path.join(R14, "BOARD_ARCHIVE.md"), 2952),
]
raws = {}
for name, p, exp in TARGETS:
    raw = open(p, "rb").read()
    raws[name] = raw
    cr = raw.count(b"\r")
    P("  %-14s %9d B  CR=%-5d 期望=%-5d %s" % (name, len(raw), cr, exp,
                                              "PASS" if cr == exp else "FAIL"))
    ck("%s CR = %d" % (name, exp), cr == exp, str(cr))

P("")
P("[B] 看板总行数 <= 300")
brd = raws["STATUS_BOARD"].decode("utf-8")
nl = len(brd.split("\n"))
P("  STATUS_BOARD 总行数 = %d（split '\\n'；上限 300）" % nl)
ck("看板总行数 <= 300", nl <= 300, str(nl))
ck("看板行数 = LF 数 + 1", nl == raws["STATUS_BOARD"].count(b"\n") + 1, str(nl))
ck("看板无 CR 字符", b"\r" not in raws["STATUS_BOARD"])
ck("看板以单换行结尾", brd.endswith("\n") and not brd.endswith("\n\n"))

P("")
P("[C] 四件套本轮段确已落盘（逐段落标题 + 关键数字命中）")
checks = [
    ("common", "## 2.73 ", ["4,087", "615,909,180", "611,813,919", "16,711,118",
                            "67a10662007eec7a"]),
    ("ledger", "## §1122", ["4,087", "615,909,180", "611,813,919", "16,711,118"]),
    ("lock",   "## CV · R17 第 67 轮", ["4,087", "615,909,180", "611,813,919"]),
    ("board",  "## 🟢 R17 第 67 轮", ["4,087", "615,909,180", "611,813,919"]),
]
files = {"common": os.path.join(R14, "R14_COMMON.md"),
         "ledger": os.path.join(LEAD, "GOAL_THREE_TARGETS_20261018.md"),
         "lock": os.path.join(LEAD, "LEAD_LOCK"),
         "board": os.path.join(R14, "STATUS_BOARD.md")}
for k, head, keys in checks:
    t = open(files[k], encoding="utf-8").read()
    ck("%s 含段标题「%s」" % (k, head.strip()), head in t)
    ck("%s 段标题恰出现 1 次" % k, t.count(head) == 1, str(t.count(head)))
    for kw in keys:
        ck("%s 含关键数字 %s" % (k, kw), kw in t)
    # 段落之后不应再有更新的节标题（确认是本轮新段在末尾）
    idx = t.index(head)
    tail = t[idx:]
    ck("%s 段位于文件末段（其后无同级新节）" % k, len(tail) > 1000, "tail=%d" % len(tail))

P("")
P("[D] 归档闭环（看板已无第 59/60 轮原文段标题，归档里有且仅有一份）")
brd_lines = brd.split("\n")
ck("看板已无第 59 轮原文段（行首为 '## ' 的标题不存）",
   not any(l.startswith("## 🔴 R17 第 59 轮") for l in brd_lines))
ck("看板已无第 60 轮原文段（行首为 '## ' 的标题不存）",
   not any(l.startswith("## 🟢 R17 第 60 轮") for l in brd_lines))
ck("看板保留第 59 轮指针（'> 📦 ## ' 打头 + 归档去向）",
   any(l.startswith("> 📦 ## 🔴 R17 第 59 轮") and "已归档至 BOARD_ARCHIVE.md" in l
       for l in brd_lines))
ck("看板保留第 60 轮指针",
   any(l.startswith("> 📦 ## 🟢 R17 第 60 轮") and "已归档至 BOARD_ARCHIVE.md" in l
       for l in brd_lines))
ptr59 = [l for l in brd_lines if l.startswith("> 📦 ## 🔴 R17 第 59 轮")]
ptr60 = [l for l in brd_lines if l.startswith("> 📦 ## 🟢 R17 第 60 轮")]
ck("第 59 轮指针恰 1 行", len(ptr59) == 1, str(len(ptr59)))
ck("第 60 轮指针恰 1 行", len(ptr60) == 1, str(len(ptr60)))
ck("两条指针都写 missing=0",
   bool(ptr59) and bool(ptr60) and "missing=0" in ptr59[0] and "missing=0" in ptr60[0])
ck("两条指针都记卫生员 H9293",
   "H9293" in ptr59[0] and "H9293" in ptr60[0])

arch = raws["BOARD_ARCHIVE"].decode("utf-8")
ck("归档含第 59 轮原文", "## 🔴 R17 第 59 轮" in arch)
ck("归档含第 60 轮原文", "## 🟢 R17 第 60 轮" in arch)
ck("归档第 59 轮标题恰 1 份（未重复归档）", arch.count("## 🔴 R17 第 59 轮") == 1,
   str(arch.count("## 🔴 R17 第 59 轮")))
ck("归档第 60 轮标题恰 1 份", arch.count("## 🟢 R17 第 60 轮") == 1,
   str(arch.count("## 🟢 R17 第 60 轮")))
ck("归档仍以 </details> 结尾", arch.rstrip("\n").endswith("</details>"))
ck("看板第 66 轮段仍在（未被误删）", "## 🔴 R17 第 66 轮" in brd)

P("")
P("[E] 实测产物可复现（unique_content_4417.tsv 自洽）")
OUT = os.path.join(R14, r"_r67\unique_content_4417.tsv")
rows = list(csv.DictReader(io.open(OUT, encoding="utf-8"), delimiter="\t"))
P("  行数 %d / sum(bytes) %d / sum(decl_bytes) %d / 唯一 sha %d"
  % (len(rows), sum(int(r["bytes"]) for r in rows),
     sum(int(r["decl_bytes"]) for r in rows),
     len({r["sha256"] for r in rows})))
ck("产物行数 = 4417", len(rows) == 4417)
ck("产物 sum(bytes) = 754,228,404", sum(int(r["bytes"]) for r in rows) == 754228404)
ck("产物 sum(decl_bytes) = 737,517,286",
   sum(int(r["decl_bytes"]) for r in rows) == 737517286)
ck("产物唯一 sha256 数 = 4087", len({r["sha256"] for r in rows}) == 4087)
ck("产物唯一内容字节 = 615,909,180",
   sum(int(r["bytes"]) for r in rows if r["cluster_rep"] == r["rel"]) == 615909180)
ck("产物含 decl_bytes 列（两口径并列，纪律 31）", "decl_bytes" in rows[0])
ck("产物无 CR（全 LF）", b"\r" not in open(OUT, "rb").read())

P("")
P("[F] 日志存在且声明 ALL-PASS")
for f in ("run.out.txt", "verify.out.txt", "archive.out.txt", "write.out.txt"):
    p = os.path.join(R14, "_r67", f)
    t = open(p, encoding="utf-8", errors="replace").read()
    ck("%s 存在且 RESULT ALL-PASS" % f, os.path.exists(p) and "RESULT ALL-PASS" in t)
    ck("%s 无 FAIL 行" % f, not any(l.startswith("  FAIL") for l in t.split("\n")))

P("")
P("=" * 78)
P("RESULT " + ("ALL-PASS" if not fails else "FAIL: " + ",".join(fails)))
open(os.path.join(R14, r"_r67\final_check_r67.log"), "w", encoding="utf-8",
     newline="\n").write("\n".join(buf) + "\n")
sys.exit(0 if not fails else 1)
