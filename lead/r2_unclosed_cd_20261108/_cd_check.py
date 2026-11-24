# -*- coding: utf-8 -*-
"""_cd_check.py — C 崩点1/2 与 D 独立证成/硬阻断解除条件 的补证实跑（离线只读）

铁律：零真机、零采样代码；只读既有件；本脚本只写 stdout（外部重定向到本写域 _cd_check_out.txt）。
运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/r2_unclosed_cd_20261108/_cd_check.py
"""
import ast
import hashlib
import os
import re
import sys

R = "D:/Project/ra2-campaign-forge"
P = {
    "dC_script":   R + "/lead/dtrigger_round2_20261107/_dC_recompute.py",
    "dC_out":      R + "/lead/dtrigger_round2_20261107/_dC_out.txt",
    "round2":      R + "/lead/dtrigger_round2_20261107/CRITERIA_ROUND2.md",
    "dD_md":       R + "/lead/dtrigger_round2_20261107/_dD_PHYSICAL_S_ALIGNMENT.md",
    "dD_check":    R + "/lead/dtrigger_round2_20261107/_dD_check.py",
    "dD_check_out":R + "/lead/dtrigger_round2_20261107/_dD_check_out.txt",
    "dD_align":    R + "/lead/dtrigger_round2_20261107/_dD_align.py",
    "vD_out3":     R + "/lead/dtrigger_round2_20261107/_verify_D_out3.txt",
    "supp":        R + "/lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt",
    "probe":       R + "/lead/dtrigger_compare_20261107/_dtrigger_probe_out.txt",
    "compare":     R + "/lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md",
    "stall_def":   R + "/lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md",
    "ruling_d30":  R + "/lead/d30_ruling_20261106/RULING_D30.md",
    "r2closure":   R + "/lead/criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md",
}

def rd(key):
    with open(P[key], "r", encoding="utf-8") as f:
        return f.read()

def rdl(key):
    with open(P[key], "r", encoding="utf-8") as f:
        return f.read().split("\n")

W = []
def w(s=""):
    W.append(str(s))

# ---------- §0 指纹 ----------
w("=" * 100)
w("【_cd_check.py】C 崩点1/2 + D 独立证成/硬阻断解除条件 补证实跑（零真机 / 零采样 / 只读）")
w("=" * 100)
w("§0 被核对象指纹（hashlib.sha256，本脚本实算）")
fps = {}
for k in sorted(P):
    b = open(P[k], "rb").read()
    fps[k] = (hashlib.sha256(b).hexdigest(), len(b))
    w("  %-12s SHA256 = %s，字节数 = %d  (%s)" % (k, fps[k][0], fps[k][1], P[k]))

# ---------- §1 C 崩点1：emit 常量串 + all_pass 覆盖（AST 实算） ----------
w("")
w("§1 C 崩点1：_dC_recompute.py 的 emit 文字是否硬编码常量、all_pass 是否覆盖全部子断言")
src = rd("dC_script")
tree = ast.parse(src)
lines = src.split("\n")

# 1a) 逐 emit() 调用分类：arg 为纯字面串(常量) vs 含插值/格式化
emit_calls = []  # (lineno, kind, preview)
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "emit":
        a = node.args[0] if node.args else None
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            kind = "LITERAL"
        elif a is None:
            kind = "LITERAL(empty)"
        else:
            kind = "INTERP/FORMAT"
        frag = ast.get_source_segment(src, node) or ""
        frag = re.sub(r"\s+", " ", frag)[:110]
        emit_calls.append((node.lineno, kind, frag))

w("  1a) emit() 调用分类（行号 / 类型 / 源片段）——聚焦 :330-370 段：")
for ln, kind, frag in emit_calls:
    if 328 <= ln <= 370:
        w("    :%d  %-16s %s" % (ln, kind, frag))
lit_range = [t for t in emit_calls if 356 <= t[0] <= 369]
w("  1a-结论) :356-:369 区间内 emit 共 %d 处，其中纯字面串 %d 处、含插值/格式化 %d 处。"
  % (len(lit_range), sum(1 for t in lit_range if t[1].startswith("LITERAL")),
     sum(1 for t in lit_range if not t[1].startswith("LITERAL"))))

# 1b) all_pass 门操作数（AST 提取）
all_pass_names = []
all_pass_cmp = []
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == "all_pass":
                v = node.value
                for sub in ast.walk(v):
                    if isinstance(sub, ast.Name):
                        all_pass_names.append(sub.id)
                    if isinstance(sub, ast.Compare):
                        all_pass_cmp.append(ast.get_source_segment(src, sub))
all_pass_names = sorted(set(all_pass_names))
w("  1b) all_pass（:391-401）AST 提取：")
w("      引用变量 = %s" % ", ".join(all_pass_names))
w("      比较项（Compare 源片段，%d 个）：" % len(all_pass_cmp))
for c in all_pass_cmp:
    w("        %s" % re.sub(r"\s+", " ", c))

# 1c) 脚本内定义过的检查型变量 vs 是否进 all_pass
check_vars = ["decomp_fail", "nonneg_fail", "chain_fail", "cap_eq_ideal",
              "A_nf_eq_ideal", "A_recall0", "A_preempt0", "A_collapse_gt0",
              "A_cap_eq_up", "A_up_eq_ideal", "A_maxloss_eq",
              "B_preempt0", "B_up_eq_ideal", "B_preempt0_and_upideal",
              "B_upideal_but_preempt_gt0", "B_preempt0_recall_gt0",
              "B_nf_eq_ideal", "B_recall0", "named_set", "not_named",
              "bad_within50", "probe_bad"]
w("  1c) 检查型变量是否进 all_pass 门：")
for v in check_vars:
    w("    %-26s %s" % (v, "IN gate" if v in all_pass_names else "NOT in gate"))

# 1d) ge100 是否参与任何门（全文搜索 ge100 的使用行）
w("  1d) 「ge100」在脚本中的全部出现行（判定是否参与任何门/比较）：")
for i, ln in enumerate(lines, 1):
    if "ge100" in ln:
        w("    :%d  %s" % (i, ln.strip()))

# 1e) 总判定行的构造
for i, ln in enumerate(lines, 1):
    if "总判定" in ln:
        w("  1e) 总判定行 :%d  %s" % (i, ln.strip()))

# 1f) 7b supplement 行的「全部越50ms」是否有聚合门（找 supp 相关变量进 all_pass）
w("  1f) 7b 段（supplement 逐行「全部越 50ms/非全部」）是否存在聚合变量并入 all_pass："
  % ())
w("      all_pass 引用变量中含 supp/7b 相关者 = %s"
  % ([v for v in all_pass_names if "supp" in v.lower()] or "无"))

# ---------- §2 C 崩点2：13 档中「全部触发 ≥100ms」的档数（实算） ----------
w("")
w("§2 C 崩点2：实算 13 档中「全部触发 ≥100ms」的档数（_dC_out.txt 7b + supplement 原件双源）")

dc_out_lines = rdl("dC_out")
# 2a) 从 _dC_out.txt:80 取 13 档名单
tier_line = None
for i, ln in enumerate(dc_out_lines, 1):
    m = re.match(r"^\s*71 格涉及的判据 = 13 档：(.+)$", ln)
    if m:
        tier_line = (i, m.group(1))
tiers13 = [x.strip() for x in tier_line[1].split(",")]
w("  2a) 13 档名单（_dC_out.txt:%d）= %s" % (tier_line[0], tiers13))

NAMED_HIGH = ["C2-P95x3", "C2-P99x3", "C3-r4", "C3-r4-clean", "C3-r8", "C3-r8-clean", "C3-r12"]
w("  2a-注) NAMED_HIGH（脚本 :39-42 定义，§9.6「括注高档」）= %s" % NAMED_HIGH)

# 2b) 解析 _dC_out.txt 7b 段
rows7b = {}
norow7b = []
sec7b = False
for i, ln in enumerate(dc_out_lines, 1):
    if ln.strip().startswith("7b "):
        sec7b = True
        continue
    if sec7b:
        if ln.strip().startswith("7c "):
            break
        m = re.match(r"^\s{4}(\S+)\s+supplement_out\.txt:(\d+)\s+nTrig=\s*(\d+)\s+>50=\s*(\d+)（(全部越 50ms|非全部)）\s+>=100=\s*(\d+)\s*$", ln)
        if m:
            rows7b[m.group(1)] = dict(out_line=i, supp_line=int(m.group(2)),
                                      nTrig=int(m.group(3)), gt50=int(m.group(4)),
                                      tag=m.group(5), ge100=int(m.group(6)))
            continue
        m2 = re.match(r"^\s{4}(\S+)\s+无此行", ln)
        if m2:
            norow7b.append((m2.group(1), i))
w("  2b) _dC_out.txt 7b 段解析：有行 %d 档、无行 %d 档" % (len(rows7b), len(norow7b)))

# 2c) supplement 原件独立解析（与 _dC_recompute.py:290-299 同一管道逻辑，独立实现）
supp_rows = {}
supp_lines = rdl("supp")
for i, ln in enumerate(supp_lines, 1):
    if "|" not in ln:
        continue
    f0 = [z.strip() for z in ln.split("|")]
    if len(f0) >= 12 and f0[0][:2] in ("C1", "C2", "C3", "C4", "C5") and f0[1].isdigit():
        try:
            supp_rows[f0[0]] = dict(line=i, nTrig=int(f0[1]), gt50=int(f0[6]), ge100=int(f0[8]), raw=ln.strip())
        except ValueError:
            pass

w("  2c) supplement 原件独立解析（13 档）：")
cross_ok = True
cls = {"all": [], "partial": [], "norow": []}
for t in tiers13:
    s = supp_rows.get(t)
    b = rows7b.get(t)
    if s is None:
        cls["norow"].append(t)
        w("    %-16s supplement 无行（_dC_out 7b 标记=%s）" %
          (t, "无此行" if b is None else "有行?!"))
        if b is not None:
            cross_ok = False
    else:
        stat = "ALL>=100" if s["ge100"] == s["nTrig"] else ("PARTIAL" if s["ge100"] > 0 else "NONE>=100")
        cls["all" if s["ge100"] == s["nTrig"] else "partial"].append(t)
        w("    %-16s supplement_out.txt:%-3d nTrig=%3d >50=%3d >=100=%3d  %s   [7b 对账: %s]" %
          (t, s["line"], s["nTrig"], s["gt50"], s["ge100"], stat,
           "nTrig/gt50/ge100 全等" if b and (b["nTrig"], b["gt50"], b["ge100"]) == (s["nTrig"], s["gt50"], s["ge100"]) else "不一致!"))
        if not b or (b["nTrig"], b["gt50"], b["ge100"]) != (s["nTrig"], s["gt50"], s["ge100"]):
            cross_ok = False
w("  2c-结论) 13 档中「全部触发 ≥100ms」（ge100==nTrig）的档数 = %d" % len(cls["all"]))
w("          全部≥100：%s" % ", ".join(cls["all"]))
w("          部分≥100（%d 档）：%s" % (len(cls["partial"]), ", ".join(cls["partial"])))
w("          supplement 无行（%d 档）：%s" % (len(cls["norow"]), ", ".join(cls["norow"])))
w("          双源对账（7b 表 vs supplement 原件）一致 = %s" % cross_ok)

# 2d) 括注 7 档视角
w("  2d) 括注 7 档（NAMED_HIGH）视角：")
for t in NAMED_HIGH:
    s = supp_rows.get(t)
    if s is None:
        w("    %-16s supplement 无行（行级 ≥100 数据缺失于 supplement）" % t)
    else:
        w("    %-16s nTrig=%3d >=100=%3d  %s" % (t, s["nTrig"], s["ge100"],
          "ALL>=100" if s["ge100"] == s["nTrig"] else "PARTIAL"))

# 2e) probe 细部行核对（7c-2 硬编码串的事实核对）+ C3-r12 的 min/med
probe_lines = rdl("probe")
w("  2e) probe_out.txt 细部行核对（7c-2 硬编码串引用 :106/:128/:150/:161/:172；7e 引用 :171-172）：")
for ln_no in (106, 128, 150, 161, 171, 172):
    if ln_no <= len(probe_lines):
        w("    probe:%-4d %s" % (ln_no, probe_lines[ln_no - 1].strip()))
w("  2e-2) probe 主表表头与 13 档中可读行的原始行（7c 引用行号）：")
for ln_no in (38, 39, 40, 41, 42, 43, 44, 45):
    if ln_no <= len(probe_lines):
        w("    probe:%-4d %s" % (ln_no, probe_lines[ln_no - 1].strip()))

# 2f) 7f 门槛定义引用核对（STALL_EVENT_DEFINITION.md:190/:191、RULING_D30.md:26/:52）——只读
stall_lines = rdl("stall_def")
w("  2f) 7f 引用核对（只读）STALL_EVENT_DEFINITION.md:190/:191：")
for ln_no in (190, 191):
    if ln_no <= len(stall_lines):
        w("    stall_def:%-4d %s" % (ln_no, stall_lines[ln_no - 1].strip()))
r30_lines = rdl("ruling_d30")
w("      RULING_D30.md:26/:52：")
for ln_no in (26, 52):
    if ln_no <= len(r30_lines):
        w("    ruling_d30:%-3d %s" % (ln_no, r30_lines[ln_no - 1].strip()))

# ---------- §3 D 独立证成：B3/B4 块 computed 计数复算 + D 是否复算逐档越线 ----------
w("")
w("§3 D 独立证成：B3/B4 块 computed=0 的独立复算 + _dD_ 脚本是否自行复算逐档越线数")
dsrc = rd("dD_check")
dtree = ast.parse(dsrc)
dlines = dsrc.split("\n")

def block_stat(lo, hi, fname):
    comp = 0
    lit = 0
    for node in ast.walk(dtree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == fname:
            if lo <= node.lineno <= hi:
                a = node.args[0] if node.args else None
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    lit += 1
                else:
                    comp += 1
    return comp, lit

c3, l3 = block_stat(114, 125, "out")
c4, l4 = block_stat(128, 137, "out")
w("  3a) _dD_check.py B3 块（:114-125）out() 调用：computed(含插值)=%d literal_prose=%d" % (c3, l3))
w("      _dD_check.py B4 块（:128-137）out() 调用：computed(含插值)=%d literal_prose=%d" % (c4, l4))
w("      （对照 _verify_D_out3.txt:7-10 的 T3 = B4 computed=0/literal 10、B3 computed=0/literal 12）")
# B1/B2 是否实算（对照）
c1, l1 = block_stat(82, 94, "out")
c2, l2 = block_stat(97, 112, "out")
w("      对照 B1（:82-94）computed=%d literal=%d；B2（:97-112）computed=%d literal=%d" % (c1, l1, c2, l2))

w("  3b) _dD_check.py / _dD_align.py 是否解析/复算 _dtrigger_supplement_out.txt（逐档越线数）：")
for key in ("dD_check", "dD_align"):
    hits = []
    for i, ln in enumerate(dlines if key == "dD_check" else rd(key).split("\n"), 1):
        if re.search(r"supplement|probe_out|metrics_out|dtrigger_supplement", ln, re.I):
            hits.append("    %s:%d  %s" % (key, i, ln.strip()))
    w("    %s 命中 %d 处：" % (key, len(hits)))
    for h in hits[:10]:
        w(h)

w("  3c) D-2 前提件 _dtrigger_supplement_out.txt 的被引行（:10-24,29,33-34,44-45 原文直读）：")
for ln_no in [10, 11, 12, 13, 14, 20, 21, 22, 24, 29, 33, 34, 44, 45]:
    if ln_no <= len(supp_lines):
        w("    supp:%-3d %s" % (ln_no, supp_lines[ln_no - 1].strip()))

w("  3d) CRITERIA_COMPARE.md:34-35,145-147「不合规方向」记载直读：")
cmp_lines = rdl("compare")
for ln_no in (34, 35, 145, 146, 147):
    if ln_no <= len(cmp_lines):
        w("    compare:%-4d %s" % (ln_no, cmp_lines[ln_no - 1].strip()))

# ---------- §4 D 硬阻断解除条件：§4 清单形态 + T5 算术复核 ----------
w("")
w("§4 D 硬阻断解除条件：§4（O1–O5）清单形态核对 + O1 精度括注算术复核")
dD_md_lines = rdl("dD_md")
w("  4a) _dD_PHYSICAL_S_ALIGNMENT.md §4 关键行直读：")
for ln_no in (118, 120, 122, 126, 127, 128, 129, 130, 132, 134, 114):
    if ln_no <= len(dD_md_lines):
        w("    dD_md:%-3d %s" % (ln_no, dD_md_lines[ln_no - 1].strip()))
w("  4b) O1 精度括注算术复核（实算）：1ms+1ms = 2ms；2/50 = %.1f%%；1/50 = %.1f%%；2/20 = %.1f%%"
  % (2 / 50 * 100, 1 / 50 * 100, 2 / 20 * 100))
w("      对照 doc:126 原文「合计 ≤ :177 的 50 ms 预算的 2%，且 ≤ :190 的 20 ms 安全裕量」")
w("  4c) 必要性论证的形态：_dD_check_out.txt:46-55（B4 块）为字面串（§3a AST 实算 computed=%d）" % c4)
w("      即「逐项缺一即不能闭合」是逐行断言文字，非构造性证明/反例计算。")
w("  4d) O5 条件项与覆盖母体声明：doc:130（T8 直读对照 _verify_D_out3.txt:28）+ doc:122「最小集 = O1–O4」")

# ---------- §5 汇总 ----------
w("")
w("§5 本脚本只产事实与计数；判定与闭合状态见 _cd_verdict.md（含指纹表）。")
w("运行环境：python -I -X utf8；本脚本未写任何被核对象、未启动进程、未采样。")

sys.stdout.write("\n".join(W) + "\n")
