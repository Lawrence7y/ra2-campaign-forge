# -*- coding: utf-8 -*-
# A1/G5 探针：独立核实 D-24 G5 订正的五项事实。
# 铁律：零真机、零采样、只读既有件、不用 ra2tool.Engine、不做目录遍历。
# 运行：python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/A1_ERRATA_MAP/_a1_g5_probe.py"
# 注：全部文件读取用 pathlib.Path(...).read_bytes()（字面量绝对路径，无变量进路径）。
import hashlib
import io
import re
import sys
from datetime import datetime
from pathlib import Path

D = Path(r"D:\Project\ra2-campaign-forge\lead\re_line_20261105")

_buf = io.StringIO()


def w(line=""):
    _buf.write(line + "\n")


results = []


def check(name, ok, detail):
    results.append((name, ok, detail))
    w("[%s] %s" % ("PASS" if ok else "FAIL", name))
    for d in detail.splitlines():
        w("      " + d)
    w("")


w("=== A1/G5 探针输出 ===")
w("运行时刻 = " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
w("命令 = python -I -X utf8 A1_ERRATA_MAP/_a1_g5_probe.py")
w("")

# ---------- 0. 强制头部四文件自算 SHA256 / 字节数 ----------
w("---- 0. 强制头部四文件自算 SHA256 / 字节数 ----")
w("")
d9 = (D / "W9_SINGLESTEP_7CFC9F" / "W9_SINGLESTEP.md").read_bytes()
d8 = (D / "W8_STATIC_LOCATE" / "W8_STATIC_LOCATE.md").read_bytes()
d7 = (D / "W7_W4_REVIEW" / "W7_W4_REVIEW.md").read_bytes()
d6 = (D / "V6_V3_REVIEW" / "V6_V3_REVIEW.md").read_bytes()
w("W9_SINGLESTEP.md   SHA256 = %s  字节数 = %d" % (hashlib.sha256(d9).hexdigest(), len(d9)))
w("W8_STATIC_LOCATE.md SHA256 = %s  字节数 = %d" % (hashlib.sha256(d8).hexdigest(), len(d8)))
w("W7_W4_REVIEW.md    SHA256 = %s  字节数 = %d" % (hashlib.sha256(d7).hexdigest(), len(d7)))
w("V6_V3_REVIEW.md    SHA256 = %s  字节数 = %d" % (hashlib.sha256(d6).hexdigest(), len(d6)))
w("")

# ---------- 1. W5 四道旧复核绑定核查（问题 1） ----------
w("---- 1. Q1~Q4 的 eb53a617 绑定与 64 位哈希出现情况 ----")
w("")
HEX64 = re.compile(r"[0-9a-f]{64}")
q1 = (D / "W5_HARNESS_EXT" / "reviews" / "Q1_review.md").read_text(encoding="utf-8", errors="replace")
q2 = (D / "W5_HARNESS_EXT" / "reviews" / "Q2_review.md").read_text(encoding="utf-8", errors="replace")
q3 = (D / "W5_HARNESS_EXT" / "reviews" / "Q3_review.md").read_text(encoding="utf-8", errors="replace")
q4 = (D / "W5_HARNESS_EXT" / "reviews" / "Q4_review.md").read_text(encoding="utf-8", errors="replace")
for label, t in (("Q1_review.md", q1), ("Q2_review.md", q2), ("Q3_review.md", q3), ("Q4_review.md", q4)):
    ls = t.splitlines()
    eb = [(i + 1, ln.strip()) for i, ln in enumerate(ls) if "eb53a617" in ln]
    hx = [(i + 1, HEX64.search(ln).group(0)[:16] + "…") for i, ln in enumerate(ls) if HEX64.search(ln)]
    w("%s : eb53a617 出现 %d 处 -> 行 %s" % (label, len(eb), [e[0] for e in eb] or "无"))
    for i, tx in eb:
        w("    L%d: %s" % (i, tx[:150]))
    w("  64 位哈希出现行: %s" % (hx or "无"))
w("")

# ---------- 2. V6 判定书关键行（问题 2 / 5） ----------
w("---- 2. V6_V3_REVIEW.md 总判 / 绑定段 ----")
w("")
v6 = d6.decode("utf-8", "replace").splitlines()
for ln_no in (14, 16, 24, 30, 34, 35, 48, 50):
    check("V6_V3_REVIEW.md L%d 存在" % ln_no, ln_no <= len(v6), v6[ln_no - 1].strip()[:180])
cnt_conf = sum(1 for ln in v6 if "CONFIRMED" in ln)
check("V6_V3_REVIEW.md 'CONFIRMED' 总行数 > 0", cnt_conf > 0, "出现于 %d 行" % cnt_conf)

copy_bytes = (D / "W5_HARNESS_EXT" / "qc151_trip.harness8_v4_ext.py").read_bytes()
mother_bytes = Path(r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py").read_bytes()
ch = hashlib.sha256(copy_bytes).hexdigest()
mh = hashlib.sha256(mother_bytes).hexdigest()
check(
    "现盘副本 qc151_trip.harness8_v4_ext.py == V6 绑定 5081780c… / 499,047 B",
    ch.startswith("5081780c") and len(copy_bytes) == 499047,
    "实算 %s / %d B" % (ch, len(copy_bytes)),
)
check(
    "现盘母本 qc151_trip.harness8_v4.py == V6 绑定 38244d29… / 489,502 B",
    mh.startswith("38244d29") and len(mother_bytes) == 489502,
    "实算 %s / %d B" % (mh, len(mother_bytes)),
)
check(
    "V6 绑定段同时含 5081780c（核心副本）与 38244d29（母本）",
    any("5081780c" in ln for ln in v6) and any("38244d29" in ln for ln in v6),
    "5081780c 行数=%d，38244d29 行数=%d"
    % (
        sum(1 for ln in v6 if "5081780c" in ln),
        sum(1 for ln in v6 if "38244d29" in ln),
    ),
)
check(
    "V6_V3_REVIEW.md 内 'dwfrun' 出现次数",
    True,
    "%d 次（0 = 判定书本身不含 run ID，run ID 出处为派单/台账记录）"
    % sum(1 for ln in v6 if "dwfrun" in ln),
)
w("")

# ---------- 3. V6 R1–R5 是否含负担（问题 3） ----------
w("---- 3. V6 五项定义范围与负担关键词 ----")
w("")
vt = (D / "V6_V3_REVIEW" / "TASK.md").read_text(encoding="utf-8", errors="replace").splitlines()
check("V6 TASK.md L17 引用 _d21_burden5_out.txt（先读清单，非复核项）", len(vt) >= 17, vt[16].strip()[:180])
sec = "\n".join(vt[41:78])  # L42..L78（§2 R1–R5 定义区）
kw = {k: sec.count(k) for k in ["负担", "burden", "13.094", "31.355", "开销"]}
check("V6 TASK.md L42-L78（R1–R5 定义区）负担关键词计数全零", all(v == 0 for v in kw.values()), str(kw))
c1 = d6.decode("utf-8", "replace").count("13.094")
c2 = d6.decode("utf-8", "replace").count("31.355")
check("grep 13.094 V6_V3_REVIEW.md = 0", c1 == 0, "实跑计数 = %d" % c1)
check("grep 31.355 V6_V3_REVIEW.md = 0", c2 == 0, "实跑计数 = %d" % c2)
w("")

# ---------- 4. 负担数字出处链（问题 4） ----------
w("---- 4. +13.094% / +31.355% 出处链 ----")
w("")
ex = (D / "D21_RULING" / "EXECUTION_D21.md").read_text(encoding="utf-8", errors="replace").splitlines()
for ln_no, needle in ((89, "五读负担复算"), (94, "+13.094%"), (101, "+31.3550%"), (111, "+13.094%"), (113, "31.3549")):
    ok = len(ex) >= ln_no and needle in ex[ln_no - 1]
    check("EXECUTION_D21.md L%d 含 %r" % (ln_no, needle), ok, ex[ln_no - 1].strip()[:170] if len(ex) >= ln_no else "(缺行)")
b5 = (D / "D21_RULING" / "_d21_burden5_out.txt").read_text(encoding="utf-8", errors="replace").splitlines()
hits = [(i + 1, ln.strip()[:120]) for i, ln in enumerate(b5) if ("13.094" in ln or "31.355" in ln)]
check("_d21_burden5_out.txt 含两组数字", len(hits) >= 2, "行: " + "; ".join("L%d %s" % h for h in hits[:4]))
check("_d21_burden5.py 存在", (D / "D21_RULING" / "_d21_burden5.py").is_file(), "is_file -> 见结果")
rul = (D / "D21_RULING" / "RULING_D21.md").read_text(encoding="utf-8", errors="replace").splitlines()
l23 = rul[22] if len(rul) >= 23 else ""
check(
    "RULING_D21.md L23 = 四舍五入条件算式（~13.09%/31.36%）且自注不可作验收",
    ("13.09%" in l23) and ("31.36%" in l23) and ("不能充作改后验收结果" in l23),
    l23.strip()[:170],
)
# 期望值 = bash `grep -o "13\.094" <file> | wc -l` 实测（2026-11-06）：
#   EXECUTION_D21.md=3（行 :12/:94/:111）、_d21_burden5_out.txt=2（行 :12/:26）、
#   GOAL_RE_CONTINUOUS.md=5 次散布于 2 行（:229/:262）、V6 TASK.md=1（:17）、A1 TASK.md=2（:71/:74）。
c_exe = (D / "D21_RULING" / "EXECUTION_D21.md").read_text(encoding="utf-8", errors="replace").count("13.094")
check("'13.094' 计数 == bash grep 结果: D21_RULING/EXECUTION_D21.md = 3", c_exe == 3, "实跑计数 = %d" % c_exe)
c_b5o = (D / "D21_RULING" / "_d21_burden5_out.txt").read_text(encoding="utf-8", errors="replace").count("13.094")
check("'13.094' 计数 == bash grep 结果: D21_RULING/_d21_burden5_out.txt = 2", c_b5o == 2, "实跑计数 = %d" % c_b5o)
c_goc = (D / "GOAL_RE_CONTINUOUS.md").read_text(encoding="utf-8", errors="replace").count("13.094")
check("'13.094' 计数 == bash grep 结果: GOAL_RE_CONTINUOUS.md = 5（2 行）", c_goc == 5, "实跑计数 = %d" % c_goc)
c_v6t = (D / "V6_V3_REVIEW" / "TASK.md").read_text(encoding="utf-8", errors="replace").count("13.094")
check("'13.094' 计数 == bash grep 结果: V6_V3_REVIEW/TASK.md = 1", c_v6t == 1, "实跑计数 = %d" % c_v6t)
c_a1t = (D / "A1_ERRATA_MAP" / "TASK.md").read_text(encoding="utf-8", errors="replace").count("13.094")
check("'13.094' 计数 == bash grep 结果: A1_ERRATA_MAP/TASK.md = 2", c_a1t == 2, "实跑计数 = %d" % c_a1t)
w("")

# ---------- 5. 原错误句与订正块的落点 ----------
w("---- 5. 原错误句与订正块的落点 ----")
w("")
goc = (D / "GOAL_RE_CONTINUOUS.md").read_text(encoding="utf-8", errors="replace").splitlines()
l229 = goc[228] if len(goc) >= 229 else ""
l262 = goc[261] if len(goc) >= 262 else ""
check("GOAL_RE_CONTINUOUS.md L229 含原错误句『四道复核尚未针对 V3 重跑』", "四道复核尚未针对 V3 重跑" in l229, l229.strip()[:150] + "…")
check("GOAL_RE_CONTINUOUS.md L262 含订正句『V6 …已对 V3 重跑』", ("已对 V3 重跑 R1–R5" in l262) and ("G5" in l262), l262.strip()[:150] + "…")
pd = Path(r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md").read_text(encoding="utf-8", errors="replace").splitlines()
seg = "\n".join(pd[83:94])  # L84..L94
check("PENDING_DECISIONS.md L84 含被划掉原句", "四道复核未对 V3 重跑" in seg, pd[83].strip()[:150])
check("PENDING_DECISIONS.md L85 含 V6 重跑订正 + dwfrun-1766d0c8", "dwfrun-1766d0c8" in seg and "R1–R5" in seg, pd[84].strip()[:150])
check("PENDING_DECISIONS.md L88 含『四道复核绑 eb53a617』表述（待收窄句）", "绑的是 `eb53a617" in seg, pd[87].strip()[:150])
check("PENDING_DECISIONS.md L93 含『唯一出处 … EXECUTION_D21.md:89-101』", "EXECUTION_D21.md:89-101" in seg, pd[92].strip()[:150])
w("")

# ---------- 汇总 ----------
w("---- 汇总 ----")
w("")
npass = sum(1 for _, ok, _ in results if ok)
w("总计 %d 项检查：%d PASS / %d FAIL" % (len(results), npass, len(results) - npass))
for name, ok, _ in results:
    if not ok:
        w("  FAIL -> %s" % name)

(D / "A1_ERRATA_MAP" / "_a1_g5_probe_out.txt").write_text(_buf.getvalue(), encoding="utf-8", newline="\n")
print("written: _a1_g5_probe_out.txt")
print("PASS %d / %d" % (npass, len(results)))

# ---------- 出口追加：把 36 项自检的合取回传进程出口 ----------
# 模板：lead/dtrigger_compare_20261107/_check_dtrigger.py:31-35 + :226-228
# 原件 1-184 行逐字未改；本块为纯新增，插在原件 :184 sys.exit(0) 之前。
# 原件 :22-31 的 check() 已把每项 (name, ok, detail) 收进 results，
# :175 已算 npass；此处只做合取聚合与出口，不改任何判定条件/阈值/分支，
# 也不覆盖原有 check 定义（避免改动模块本体）。
ok = True
def _agg(name, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    print(("  [PASS] " if cond else "  [FAIL] ") + name)
for _name, _ok, _detail in results:
    _agg(_name, _ok)
print("核验结论: " + ("ALL PASS" if ok else "FAIL"))
raise SystemExit(0 if ok else 1)
sys.exit(0)
