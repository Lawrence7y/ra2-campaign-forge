# -*- coding: utf-8 -*-
"""CD_BREAKPOINTS.md 撰写前的独立小复核（零真机/零采样/只读；只写 stdout）。
复算对象：_cd_check_out.txt / _verify_cd_out.txt 中承重的数字，另加指纹绑定与未验项核查。
"""
import ast
import hashlib
import os
import re
import sys

BASE = "D:/Project/ra2-campaign-forge"
R2 = BASE + "/lead/dtrigger_round2_20261107"
CMP = BASE + "/lead/dtrigger_compare_20261107"
W = BASE + "/lead/r2_unclosed_cd_20261108"

out = []


def emit(s=""):
    out.append(str(s))


def sha(p):
    b = open(p, "rb").read()
    return hashlib.sha256(b).hexdigest(), len(b)


def read(p):
    return open(p, encoding="utf-8").read()


def is_literal_arg(arg):
    kinds = {type(n).__name__ for n in ast.walk(arg)}
    return kinds <= {"Constant", "BinOp", "Load"}


# ---------------------------------------------------------------- §0 指纹绑定
emit("=" * 100)
emit("【_cdreport_check.py】CD_BREAKPOINTS.md 撰写前独立复核（python -I -X utf8，只读，只写 stdout）")
emit("=" * 100)
emit("§0 指纹绑定（hashlib 实算）")
targets = [
    ("dC_recompute.py", R2 + "/_dC_recompute.py"),
    ("dC_out.txt", R2 + "/_dC_out.txt"),
    ("dD_check.py", R2 + "/_dD_check.py"),
    ("dD_align.py", R2 + "/_dD_align.py"),
    ("dD_md", R2 + "/_dD_PHYSICAL_S_ALIGNMENT.md"),
    ("dD_align_out.txt", R2 + "/_dD_align_out.txt"),
    ("dD_check_out.txt", R2 + "/_dD_check_out.txt"),
    ("supp", CMP + "/_dtrigger_supplement_out.txt"),
    ("probe", CMP + "/_dtrigger_probe_out.txt"),
    ("compare", CMP + "/CRITERIA_COMPARE.md"),
    ("round2", R2 + "/CRITERIA_ROUND2.md"),
    ("r2closure", BASE + "/lead/criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md"),
    ("cd_check.py", W + "/_cd_check.py"),
    ("cd_check_out.txt", W + "/_cd_check_out.txt"),
    ("cd_verdict.md", W + "/_cd_verdict.md"),
    ("verify_cd_out.txt", W + "/_verify_cd_out.txt"),
]
fps = {}
for tag, p in targets:
    h, n = sha(p)
    fps[tag] = (h, n)
    emit("  %-20s SHA256=%s  字节=%d" % (tag, h, n))

# ---------------------------------------------------------------- §1 C 崩点1 AST
emit("")
emit("§1 C 崩点1：_dC_recompute.py :356-369 emit 字面性 + all_pass 门覆盖（AST 实算）")
dC_src = read(R2 + "/_dC_recompute.py")
dC_lines = dC_src.split("\n")
dC_tree = ast.parse(dC_src)
seg_lit, seg_interp = [], []
for node in ast.walk(dC_tree):
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "emit" and node.args
            and 356 <= node.lineno <= 369):
        (seg_lit if is_literal_arg(node.args[0]) else seg_interp).append(node.lineno)
emit("  :356-369 emit 调用 = %d 处；纯字面 = %d 处（行 %s）；含插值/格式化 = %d 处"
     % (len(seg_lit) + len(seg_interp), len(seg_lit), seg_lit, len(seg_interp)))

all_pass_cmp, all_pass_names = [], set()
for node in ast.walk(dC_tree):
    if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "all_pass" for t in node.targets):
        for sub in ast.walk(node.value):
            if isinstance(sub, ast.Compare):
                all_pass_cmp.append(ast.unparse(sub))
            if isinstance(sub, ast.Name):
                all_pass_names.add(sub.id)
emit("  all_pass 比较项 = %d 个；引用 Name = %s" % (len(all_pass_cmp), ", ".join(sorted(all_pass_names))))

checks = ["decomp_fail", "nonneg_fail", "chain_fail", "cap_eq_ideal", "A_nf_eq_ideal",
          "A_recall0", "A_preempt0", "A_collapse_gt0", "A_cap_eq_up", "A_up_eq_ideal",
          "A_maxloss_eq", "B_preempt0", "B_up_eq_ideal", "B_preempt0_and_upideal",
          "B_upideal_but_preempt_gt0", "B_preempt0_recall_gt0", "B_nf_eq_ideal",
          "B_recall0", "named_set", "not_named", "bad_within50", "probe_bad"]
not_in = [c for c in checks if c not in all_pass_names]
emit("  检查型变量 %d 个中 NOT in gate = %d 个：%s" % (len(checks), len(not_in), ", ".join(not_in)))

ge100_lines = [i for i, ln in enumerate(dC_lines, 1) if "ge100" in ln]
ge100_cmp = 0
for node in ast.walk(dC_tree):
    if isinstance(node, ast.Compare) and any(
            isinstance(n, ast.Name) and n.id == "ge100" for n in ast.walk(node)):
        ge100_cmp += 1
emit("  ge100 出现行 = %s；含 ge100 的比较运算（全模块 AST）= %d 处" % (ge100_lines, ge100_cmp))
emit("  :420 原文 = %s" % dC_lines[419].strip())
emit("  all_pass 引用中含 supp/7b 相关名（supp_rows/ge100/supp）= %s"
     % bool(all_pass_names & {"supp_rows", "ge100", "supp"}))

# ---------------------------------------------------------------- §2 C 崩点2 13 档
emit("")
emit("§2 C 崩点2：13 档「全部触发 ≥100ms」独立实算（supplement 原件 + _dC_out.txt 7b 双源）")
dC_out_lines = read(R2 + "/_dC_out.txt").split("\n")
m80 = dC_out_lines[79]
names13 = [x.strip() for x in m80.split("13 档：", 1)[1].split(",")]
emit("  13 档名单（_dC_out.txt:80 解析）= %s（n=%d）" % (names13, len(names13)))

supp_rows = {}
for i, line in enumerate(read(CMP + "/_dtrigger_supplement_out.txt").split("\n"), 1):
    if "|" not in line:
        continue
    f = [z.strip() for z in line.split("|")]
    if len(f) >= 12 and f[0][:2] in ("C1", "C2", "C3", "C4", "C5") and f[1].isdigit():
        try:
            supp_rows[f[0]] = (i, int(f[1]), int(f[6]), int(f[8]))
        except ValueError:
            pass

b7 = {}
in7b = False
for line in dC_out_lines:
    if "7b _dtrigger_supplement_out.txt" in line:
        in7b = True
        continue
    if in7b and "7c _dtrigger_probe_out.txt" in line:
        break
    if in7b:
        m = re.match(r"\s{4}(\S+)\s+supplement_out\.txt:(\d+)\s+nTrig=\s*(\d+) >50=\s*(\d+)（[^）]*） >=100=\s*(\d+)", line)
        if m:
            b7[m.group(1)] = ("row", int(m.group(3)), int(m.group(4)), int(m.group(5)))
            continue
        m = re.match(r"\s{4}(\S+)\s+无此行", line)
        if m:
            b7[m.group(1)] = ("norow",)

allge, partial, norow, mismatch = [], [], [], 0
for nm in names13:
    if nm not in supp_rows:
        norow.append(nm)
        if nm in b7 and b7[nm][0] != "norow":
            mismatch += 1
        continue
    ln, ntrig, gt50, ge100 = supp_rows[nm]
    if ge100 == ntrig:
        allge.append("%s(%d/%d)" % (nm, ge100, ntrig))
    else:
        partial.append("%s(%d/%d)" % (nm, ge100, ntrig))
    if nm in b7 and b7[nm][0] == "row":
        if (b7[nm][1], b7[nm][2], b7[nm][3]) != (ntrig, gt50, ge100):
            mismatch += 1
    else:
        mismatch += 1
emit("  全部≥100 = %d 档：%s" % (len(allge), ", ".join(allge)))
emit("  部分≥100 = %d 档：%s" % (len(partial), ", ".join(partial)))
emit("  supplement 无行 = %d 档：%s" % (len(norow), ", ".join(norow)))
emit("  7b 表 vs supplement 原件逐档对账（nTrig/gt50/ge100）：不一致 = %d" % mismatch)

probe_lines = read(CMP + "/_dtrigger_probe_out.txt").split("\n")
p171 = [i for i, ln in enumerate(probe_lines, 1) if "min=377.385" in ln]
emit("  probe 细部行 min=377.385 出现行 = %s（C3-r12 行级 ≥100 证据的读回点）" % p171)
emit("  compare:146 原文 = %s" % read(CMP + "/CRITERIA_COMPARE.md").split("\n")[145].strip())

# ---------------------------------------------------------------- §3 D 独立证成
emit("")
emit("§3 D 独立证成：_dD_check.py B1-B4 out() 字面性 AST 实算 + _dD_ 脚本 supplement 引用 grep")
dD_src = read(R2 + "/_dD_check.py")
dD_tree = ast.parse(dD_src)
for tag, lo, hi in (("B1", 82, 94), ("B2", 97, 112), ("B3", 114, 125), ("B4", 128, 137)):
    comp = lit = 0
    for node in ast.walk(dD_tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "out" and node.args and lo <= node.lineno <= hi):
            if is_literal_arg(node.args[0]):
                lit += 1
            else:
                comp += 1
    emit("  %s 块 :%d-%d out() computed=%d literal=%d" % (tag, lo, hi, comp, lit))

for tag, p in (("dD_check", R2 + "/_dD_check.py"), ("dD_align", R2 + "/_dD_align.py")):
    hits = [(i, ln.strip()) for i, ln in enumerate(read(p).split("\n"), 1) if "supplement" in ln]
    emit("  %s 中含「supplement」的行 = %d 处" % (tag, len(hits)))
    for i, ln in hits:
        emit("    %s:%d  %s" % (tag, i, ln[:110]))
align_lines = read(R2 + "/_dD_align.py").split("\n")
emit("  _dD_align.py:55-74 原文（判 :66-67 是否解析表行）：")
for i in range(54, 74):
    emit("    :%d %s" % (i + 1, align_lines[i]))

# ---------------------------------------------------------------- §4 D 硬阻断解除条件
emit("")
emit("§4 D 硬阻断解除条件：O1 精度括注算术 + stall_def/:177 原文 + 台账 mtime")
emit("  O1 算术：1ms+1ms=%dms；2/50=%.1f%%；1/50=%.1f%%；2/20=%.1f%%" % (2, 100 * 2 / 50, 100 * 1 / 50, 100 * 2 / 20))
sd = read(BASE + "/lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md").split("\n")
for n in (177, 190, 191):
    emit("  stall_def:%d  %s" % (n, sd[n - 1][:120]))
st = os.stat(BASE + "/lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md")
emit("  stall_def mtime = %s（补证脚本落盘窗口 2026-11-08 14:24~14:37 之前即未改）"
     % __import__("datetime").datetime.fromtimestamp(st.st_mtime).isoformat())
for tag, p in (("goal", BASE + "/lead/GOAL_THREE_TARGETS_20261018.md"),
               ("pending", BASE + "/lead/PENDING_DECISIONS.md")):
    stt = os.stat(p)
    emit("  %s mtime = %s size=%d" % (tag, __import__("datetime").datetime.fromtimestamp(stt.st_mtime).isoformat(), stt.st_size))

# ---------------------------------------------------------------- §5 未验项核查
emit("")
emit("§5 未验项核查：编排方内联回件 JSON 是否落盘（grep『四项崩点补证完成』over lead/）")
hits = []
for root, dirs, files in os.walk(BASE + "/lead"):
    for fn in files:
        p = os.path.join(root, fn)
        try:
            if os.path.getsize(p) > 4_000_000:
                continue
            b = open(p, "rb").read()
        except OSError:
            continue
        if "四项崩点补证完成".encode("utf-8") in b:
            hits.append(p)
emit("  命中文件 = %d 处：%s" % (len(hits), hits))
emit("  （若仅命中 _cd_verdict.md 的转述，则编排方内联补证回件 JSON 无磁盘指纹实体，记未验）")

emit("")
emit("【_cdreport_check.py 运行完成】")
sys.stdout.write("\n".join(out) + "\n")
