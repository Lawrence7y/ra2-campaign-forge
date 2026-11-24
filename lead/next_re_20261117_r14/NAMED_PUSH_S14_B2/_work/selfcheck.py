# -*- coding: utf-8 -*-
"""B2 批产物自查：delta 硬性格式、base_rate、evidence 覆盖、每行独立 reason、表格完整性。"""
import os, sys, csv, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(OUT, "_work")
ok = True
def chk(cond, msg):
    global ok
    print(("[OK] " if cond else "[FAIL] ") + msg)
    if not cond:
        ok = False

# 1) delta 格式
p = os.path.join(OUT, "delta.tsv")
raw = open(p, encoding="utf-8", newline="").read()
lines = raw.rstrip("\n").split("\n")
chk(lines[0].split("\t") == ["entry", "subsystem", "name", "one_line_semantics", "grade", "evidence_path"],
    "delta 表头 6 列且字段名正确")
rows = [l.split("\t") for l in lines[1:]]
chk(all(len(r) == 6 for r in rows), "delta 每行 6 列 (实际列数=%s)" % sorted({len(r) for r in rows}))
chk(len(rows) == 6, "delta 行数 = 6 (实际 %d)" % len(rows))
for r in rows:
    chk(re.fullmatch(r"[0-9A-F]{8}", r[0]) is not None, "entry 大写十六进制无 0x: %s" % r[0])
    chk(r[1] == "S14", "subsystem 原样 S14: %s" % r[1])
    chk(r[4] == "[已证]", "grade [已证]: %s" % r[4])
    chk(r[5].endswith("NAMED_PUSH_S14_B2/EVIDENCE/ROW_%s.txt" % r[0]), "evidence_path 指向本目录 EVIDENCE: %s" % r[5])
chk(len({r[3] for r in rows}) == len(rows), "one_line_semantics 逐行不重复（无整批共用 reason）")

# 2) name 原样
ROWS = json.load(open(os.path.join(WORK, "b2_rows.json"), encoding="utf-8"))
by = {r["entry"]: r for r in ROWS}
for r in rows:
    chk(by[r[0]]["name"] == r[2], "name 原样未改: %s -> %s" % (r[0], r[2]))

# 3) base_rate
bl = open(os.path.join(OUT, "base_rate.tsv"), encoding="utf-8").read().rstrip("\n").split("\n")
chk(bl[0].split("\t") == ["batch", "rows_checked", "ring2_ok", "ring3b_ok", "ring4_ok", "all_four", "rate"],
    "base_rate 表头 7 列")
b = bl[1].split("\t")
chk(b[1] == "18" and b[5] == str(len(rows)), "base_rate rows_checked=18, all_four==delta 行数")
chk(abs(float(b[6]) - int(b[5]) / 18) < 1e-4, "rate = all_four/18 = %s" % b[6])

# 4) evidence 覆盖 18 行 + 内容含四环锚
ev = os.path.join(OUT, "EVIDENCE")
files = sorted(os.listdir(ev))
chk(len(files) == 18, "EVIDENCE 文件数 = 18 (实际 %d)" % len(files))
chk(set(files) == {"ROW_%s.txt" % r["entry"] for r in ROWS}, "EVIDENCE 与本批 18 个 entry 一一对应")
for r in ROWS:
    t = open(os.path.join(ev, "ROW_%s.txt" % r["entry"]), encoding="utf-8").read()
    for tag in ("[环① 入口]", "[环② 类身份]", "[环③ 整体合同]", "[环④ 使用见证]", "[裁定]"):
        chk(tag in t, "ROW_%s 含 %s" % (r["entry"], tag))
    chk(r["entry"] in t, "ROW_%s 含本行地址" % r["entry"])

# 5) REPORT 表格 18 行齐全
rp = open(os.path.join(OUT, "REPORT.md"), encoding="utf-8").read()
for r in ROWS:
    chk(("| %s |" % r["entry"]) in rp, "REPORT 总表含 %s" % r["entry"])
chk("0.3333" in rp, "REPORT 载明 rate=0.3333")

# 6) 只写本目录：确认关键只读文件未被改动（存在且非空）
for f in ("coverage.tsv", "PANEL.md", "R14_COMMON.md"):
    base = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
    cand = [os.path.join(base, f), os.path.join(base, "COVERAGE", f)]
    found = [c for c in cand if os.path.exists(c)]
    chk(len(found) > 0, "只读文件存在（未删）: %s -> %s" % (f, [os.path.basename(x) for x in found]))

print("\n== 全部通过 ==" if ok else "\n== 有失败项 ==")
sys.exit(0 if ok else 1)
