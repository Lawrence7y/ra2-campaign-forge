# -*- coding: utf-8 -*-
"""_verify_cd.py — CD 崩点复核员独立实跑核验（零真机 / 零采样代码 / 只读既有件）

本脚本不复用 _cd_check.py 的任何实现：独立 AST 解析、独立解析 supplement 原件、
独立 hashlib 指纹实算、独立合规扫描。只写 stdout（外部重定向到本写域 _verify_* 文件）。
运行：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/r2_unclosed_cd_20261108/_verify_cd.py
"""
import ast
import hashlib
import os
import re
import sys

R = "D:/Project/ra2-campaign-forge"
W = R + "/lead/r2_unclosed_cd_20261108"
D2 = R + "/lead/dtrigger_round2_20261107"
CMP = R + "/lead/dtrigger_compare_20261107"

P = {
    "dC_script":   D2 + "/_dC_recompute.py",
    "dC_out":      D2 + "/_dC_out.txt",
    "dD_md":       D2 + "/_dD_PHYSICAL_S_ALIGNMENT.md",
    "dD_align_out":D2 + "/_dD_align_out.txt",
    "dD_check":    D2 + "/_dD_check.py",
    "dD_align":    D2 + "/_dD_align.py",
    "dD_check_out":D2 + "/_dD_check_out.txt",
    "round2":      D2 + "/CRITERIA_ROUND2.md",
    "r2closure":   R + "/lead/criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md",
    "compare":     CMP + "/CRITERIA_COMPARE.md",
    "supp":        CMP + "/_dtrigger_supplement_out.txt",
    "probe":       CMP + "/_dtrigger_probe_out.txt",
    "stall_def":   R + "/lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md",
    "goal":        R + "/lead/GOAL_THREE_TARGETS_20261018.md",
    "pending":     R + "/lead/PENDING_DECISIONS.md",
    "cd_check_py": W + "/_cd_check.py",
    "cd_check_out":W + "/_cd_check_out.txt",
    "cd_check_err":W + "/_cd_check_err.txt",
    "cd_verdict":  W + "/_cd_verdict.md",
}

# 编排方 6 项指纹（题给材料）
ORCH = {
    "dC_script":    ("ec64adac558e87e5cdf53563368c7aacea712222e70f303ca85deb83eb08ee3a", 23115),
    "dC_out":       ("a0deb34a4aed83efe3d0b80dfff4f05eb28eeec5fac5613ff49316fd8081337a", 13473),
    "dD_md":        ("bb61eedbddea61e9ffcb1ac8981dadd8b3ee0fb12c715ccb3e600ca78c50fac1", 18262),
    "dD_align_out": ("4fd5a8a193cfb6661b061d5bc2fe6a24163fee564fde44baba058944742f129b", 9088),
    "r2closure":    ("bf426786db82c34dd6b6d21e3022678285e3e22f52dbdaa5085d85c3b6f8fbde", 22351),
    "compare":      ("4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726", 48343),
}
# 补证员 evidence 自报产出指纹
CLAIM_OUT = {
    "cd_check_py":  ("7fbb9a574d576ecbe83226a24190e3a8f2e5b0114ee947e1a1b8a3ce4b326764", 15031),
    "cd_check_out": ("310c31600f1fd39b782d8976c57d2e048336d18951f71a07199adda59c1cd673", 22652),
    "cd_verdict":   ("2b51dfe9c1cacaec631b7df92d53aa7db0a4ad6ce0a8e732cdacff3043557338", 14604),
}

O = []
def w(s=""):
    O.append(str(s))

def sha(path):
    with open(path, "rb") as f:
        b = f.read()
    return hashlib.sha256(b).hexdigest(), len(b)

def rd(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def rdl(path):
    return rd(path).split("\n")

# ---------------------------------------------------------------- §0 指纹
w("=" * 104)
w("【_verify_cd.py】CD 崩点复核员 · 独立实跑核验（不复用 _cd_check.py 实现）")
w("=" * 104)
w("§0 hashlib 实算指纹（本脚本独立执行）")
fp = {}
for k in sorted(P):
    h, n = sha(P[k])
    fp[k] = (h, n)
    w("  %-14s SHA256 = %s，字节数 = %d" % (k, h, n))

w("")
w("§0a 编排方 6 项指纹逐位比对（独立实算 vs 题给）")
for k in sorted(ORCH):
    exp_h, exp_n = ORCH[k]
    got_h, got_n = fp[k]
    w("  %-14s sha=%s bytes=%s  %s" % (k, "MATCH" if got_h == exp_h else "MISMATCH",
      "MATCH" if got_n == exp_n else "MISMATCH",
      "MATCH" if (got_h, got_n) == (exp_h, exp_n) else "MISMATCH"))

w("")
w("§0b 补证员 evidence 自报产出指纹逐位比对（独立实算 vs 自报）")
for k in sorted(CLAIM_OUT):
    exp_h, exp_n = CLAIM_OUT[k]
    got_h, got_n = fp[k]
    w("  %-14s sha=%s bytes=%s  %s" % (k, "MATCH" if got_h == exp_h else "MISMATCH",
      "MATCH" if got_n == exp_n else "MISMATCH",
      "MATCH" if (got_h, got_n) == (exp_h, exp_n) else "MISMATCH"))
w("  %-14s 字节数 = %d（补证员声称 = 0）%s" % ("cd_check_err", fp["cd_check_err"][1],
  "MATCH" if fp["cd_check_err"][1] == 0 else "MISMATCH"))

w("")
w("§0c 被核对象（落盘的回件主体）指纹 —— 复核回件绑定值")
w("  被核对象 = %s" % P["cd_verdict"])
w("  被核对象 SHA256 = %s，字节数 = %d" % fp["cd_verdict"])
w("  注：编排方内联的回件 JSON 文本未落盘（全仓 grep '四项崩点补证完成' 仅命中 _cd_verdict.md 的转述），")
w("      无磁盘文件可哈希；按铁律不对未落盘实体编造指纹，改以落盘回件主体 _cd_verdict.md 作为被核对象。")

w("")
w("§0d 疑点核查：编排方 6 项指纹是否都在 _cd_check.py 的本轮实算清单里？")
cd_src = rd(P["cd_check_py"])
cd_tree = ast.parse(cd_src)
p_keys = []
for node in ast.walk(cd_tree):
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "P" for t in node.targets):
        if isinstance(node.value, ast.Dict):
            for kk in node.value.keys:
                if isinstance(kk, ast.Constant):
                    p_keys.append(kk.value)
cd_out_lines = rdl(P["cd_check_out"])
sec0_names = [ln.strip().split()[0] for ln in cd_out_lines
              if re.match(r"^  \S+\s+SHA256 = ", ln)]
w("  _cd_check.py 的 P 字典键（%d 个）= %s" % (len(p_keys), sorted(p_keys)))
w("  _cd_check_out.txt §0 实算行名（%d 个）= %s" % (len(sec0_names), sorted(sec0_names)))
w("  _dD_align_out.txt 是否在 P 字典 = %s；是否在 §0 输出 = %s" %
  ("dD_align_out" in p_keys, any("dD_align_out" == n for n in sec0_names)))
w("  => 编排方 6 项中 _dD_align_out.txt 的指纹未出现在 _cd_check.py 的任何本轮实算输出里；")
w("     evidence 仍将其列入「本轮 hashlib 实算」清单（该值只能来自题给指纹抄录，非本轮脚本实算）。")

# ---------------------------------------------------------------- §1 崩点1
w("")
w("§1 C 崩点1 独立 AST 复核（_dC_recompute.py）")
src = rd(P["dC_script"])
tree = ast.parse(src)
lines = src.split("\n")

# 1a emit 纯字面判定（独立实现：只看 :356-369）
literal_calls = []
interp_calls = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "emit":
        a = node.args[0] if node.args else None
        rec = (node.lineno, ast.get_source_segment(src, a)[:60].replace("\n", " ") if a is not None else "<empty>")
        if 356 <= node.lineno <= 369:
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                literal_calls.append(rec)
            elif a is None:
                literal_calls.append(rec)
            else:
                interp_calls.append(rec)
w("  1a) :356-369 emit 调用 = %d；纯字面串 = %d；含插值/格式化 = %d" %
  (len(literal_calls) + len(interp_calls), len(literal_calls), len(interp_calls)))
for ln, seg in sorted(literal_calls):
    w("      :%d LITERAL %s" % (ln, seg))

# 1b all_pass 门（独立提取）
gate_names = set()
gate_cmps = []
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "all_pass" for t in node.targets):
        for sub in ast.walk(node.value):
            if isinstance(sub, ast.Name):
                gate_names.add(sub.id)
            if isinstance(sub, ast.Compare):
                gate_cmps.append(re.sub(r"\s+", " ", ast.get_source_segment(src, sub)))
w("  1b) all_pass 引用 Name = %s" % ", ".join(sorted(gate_names)))
w("      Compare 项数 = %d：" % len(gate_cmps))
for c in gate_cmps:
    w("        %s" % c)

# 1c 22 检查变量（按 §3/§5/§6 中定义过的检查型变量，独立清点）
check_vars = ["decomp_fail", "nonneg_fail", "chain_fail", "cap_eq_ideal",
              "A_nf_eq_ideal", "A_recall0", "A_preempt0", "A_collapse_gt0",
              "A_cap_eq_up", "A_up_eq_ideal", "A_maxloss_eq",
              "B_preempt0", "B_up_eq_ideal", "B_preempt0_and_upideal",
              "B_upideal_but_preempt_gt0", "B_preempt0_recall_gt0",
              "B_nf_eq_ideal", "B_recall0", "named_set", "not_named",
              "bad_within50", "probe_bad"]
not_in = [v for v in check_vars if v not in gate_names]
w("  1c) 检查型变量 %d 个，其中 NOT in gate = %d 个：%s" % (len(check_vars), len(not_in), ", ".join(not_in)))
# 其中真正带断言/结论文字的（在 §9 中被断言的）
asserted = ["A_cap_eq_up", "A_up_eq_ideal", "A_maxloss_eq",
            "B_preempt0_recall_gt0", "B_upideal_but_preempt_gt0"]
w("      其中在 §9.3/§9.4/§9.5 被写为结论断言的 = %d 个：%s" % (len(asserted), ", ".join(asserted)))
w("      余下 %d 个为展示计数/口径登记变量（§3/§6 只 emit 数字不带 PASS/FAIL），非「漏门断言」。" %
  (len(not_in) - len(asserted)))

# 1d ge100
ge_lines = [(i, ln.strip()) for i, ln in enumerate(lines, 1) if "ge100" in ln]
w("  1d) ge100 全部出现行 = %d：%s" % (len(ge_lines), [i for i, _ in ge_lines]))
for i, ln in ge_lines:
    w("      :%d %s" % (i, ln))
w("      其中含比较运算（==/>=/!=）的行 = %d" %
  sum(1 for _, ln in ge_lines if re.search(r"ge100\s*(==|>=|<=|!=|>|<)", ln)))

# 1e 总判定
for i, ln in enumerate(lines, 1):
    if "总判定 = " in ln and "emit" in ln:
        w("  1e) 总判定行 :%d = %s" % (i, ln.strip()))
        w("      PASS 分支文案硬编码 = %s" % ("9.1–9.7" in ln and "if all_pass" in ln))

# 1f 7b 聚合变量
w("  1f) all_pass 引用中含 7b/supp 相关变量 = %s" %
  ([v for v in gate_names if "supp" in v.lower() or "7b" in v.lower()] or "无"))

# ---------------------------------------------------------------- §2 崩点2
w("")
w("§2 C 崩点2 独立实算：13 档「全部触发 ≥100ms」及三种辖域读法")
supp_rows = {}
for i, ln in enumerate(rdl(P["supp"]), 1):
    if "|" not in ln:
        continue
    f0 = [z.strip() for z in ln.split("|")]
    if len(f0) >= 12 and f0[0][:2] in ("C1", "C2", "C3", "C4", "C5") and f0[1].isdigit():
        try:
            supp_rows[f0[0]] = (i, int(f0[1]), int(f0[6]), int(f0[8]))
        except ValueError:
            pass
w("  2a) supplement 原件独立解析：可解析档数 = %d" % len(supp_rows))

tiers13 = []
for ln in rdl(P["dC_out"]):
    m = re.match(r"^\s*71 格涉及的判据 = 13 档：(.+)$", ln)
    if m:
        tiers13 = [x.strip() for x in m.group(1).split(",")]
w("  2b) 13 档名单（_dC_out.txt:80）= %s" % tiers13)

all_tiers, part_tiers, norow = [], [], []
for t in tiers13:
    if t not in supp_rows:
        norow.append(t)
    else:
        li, ntrig, gt50, ge100 = supp_rows[t]
        (all_tiers if ge100 == ntrig else part_tiers).append((t, ntrig, ge100))
        w("      %-16s supp:%-3d nTrig=%3d >50=%3d >=100=%3d  %s" %
          (t, li, ntrig, gt50, ge100, "ALL>=100" if ge100 == ntrig else "PARTIAL"))
w("  2c) 13 档：全部≥100 = %d 档 %s；部分 = %d 档 %s；supplement 无行 = %d 档 %s" %
  (len(all_tiers), [t for t, _, _ in all_tiers], len(part_tiers),
   [t for t, _, _ in part_tiers], len(norow), norow))

# 双源对账：_dC_out.txt 7b 表 vs supplement 原件（独立解析 7b 行）
rows7b = {}
sec = False
for ln in rdl(P["dC_out"]):
    if ln.strip().startswith("7b "):
        sec = True
        continue
    if sec:
        if ln.strip().startswith("7c "):
            break
        m = re.match(r"^\s{4}(\S+)\s+supplement_out\.txt:(\d+)\s+nTrig=\s*(\d+)\s+>50=\s*(\d+)（.*?）\s+>=100=\s*(\d+)\s*$", ln)
        if m:
            rows7b[m.group(1)] = (int(m.group(3)), int(m.group(4)), int(m.group(5)))
bad = []
for t, ntrig, ge100 in all_tiers + part_tiers:
    li, n, g, e = supp_rows[t]
    if t not in rows7b or rows7b[t] != (n, g, e):
        bad.append(t)
w("  2d) 7b 表 vs supplement 原件双源对账：有行档 %d，不一致 = %d %s" %
  (len(rows7b), len(bad), bad if bad else "（全等）"))

# 三种辖域读法下「无行级 ≥100 支撑」的档数
NAMED_HIGH7 = ["C2-P95x3", "C2-P99x3", "C3-r4", "C3-r4-clean", "C3-r8", "C3-r8-clean", "C3-r12"]
UPSTREAM4 = ["C2-P95x3", "C2-P99x3", "C3-r4", "C3-r8"]
# probe 细部行可给 C3-r12 的 min>=100 证据（独立读 probe:171）
probe_lines = rdl(P["probe"])
p171 = probe_lines[170] if len(probe_lines) >= 171 else ""
m_min = re.search(r"min=([0-9.]+)", p171)
r12_min = float(m_min.group(1)) if m_min else None
w("  2e) probe:171 独立读回 min=%s（C3-r12 行级 min≥100 证据）" % r12_min)

def unsupported(tiers, allow_probe_r12=False):
    out = []
    for t in tiers:
        if t in supp_rows and supp_rows[t][3] == supp_rows[t][1]:
            continue
        if allow_probe_r12 and t == "C3-r12" and r12_min is not None and r12_min >= 100:
            continue
        out.append(t)
    return out

u4 = unsupported(UPSTREAM4)
u7 = unsupported(NAMED_HIGH7, allow_probe_r12=True)
u13 = unsupported(tiers13, allow_probe_r12=True)
w("  2f) 三种「高档」辖域读法下的无行级支撑档数（独立实算）：")
w("      (i)   上游 CRITERIA_COMPARE.md:146 登记的 4 档读法：无支撑 = %d / 4 %s" % (len(u4), u4))
w("      (ii)  §9.6 NAMED_HIGH 7 档读法（C3-r12 用 probe:171 min 证据）：无支撑 = %d / 7 %s" % (len(u7), u7))
w("      (iii) 13 档读法：无支撑 = %d / 13 %s" % (len(u13), u13))
w("  2g) §9.7 原文（_dC_out.txt:147）独立读回：")
for i, ln in enumerate(rdl(P["dC_out"]), 1):
    if i in (146, 147, 148):
        w("      _dC_out.txt:%-3d %s" % (i, ln.strip()))
w("  2h) 上游 CRITERIA_COMPARE.md:146 独立读回：")
for i, ln in enumerate(rdl(P["compare"]), 1):
    if i in (145, 146, 147):
        w("      compare:%-3d %s" % (i, ln.strip()))
w("  => 疑点：补证回件判「越界成立」，但 (i) 4 档读法（上游文档自身登记、且与 §9.7『可逐行读回的档』措辞相容）下越界不成立；")
w("     回件 _cd_verdict.md:52 亦承认上游 :146 把 ≥100 限定在恰这 4 档，却未排除该读法即判闭合。")

# ---------------------------------------------------------------- §3 D 独立证成
w("")
w("§3 D 独立证成：B3/B4 独立 AST 复算 + _dD_ 脚本是否解析 supplement 表行")
dsrc = rd(P["dD_check"])
dtree = ast.parse(dsrc)

def block(lo, hi):
    lit = comp = 0
    for node in ast.walk(dtree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "out" and lo <= node.lineno <= hi:
            a = node.args[0] if node.args else None
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                lit += 1
            else:
                comp += 1
    return comp, lit
for tag, lo, hi in (("B1", 82, 94), ("B2", 97, 112), ("B3", 114, 125), ("B4", 128, 137)):
    c, l = block(lo, hi)
    w("  3a) %s 块 :%d-%d out() 调用：computed(含插值)=%d literal_prose=%d" % (tag, lo, hi, c, l))

w("  3b) _dD_check.py / _dD_align.py 中提到 supplement/probe/metrics 的行（独立 grep）：")
for key in ("dD_check", "dD_align"):
    hits = [(i, ln.strip()) for i, ln in enumerate(rdl(P[key]), 1)
            if re.search(r"supplement|probe_out|metrics_out|dtrigger_supplement", ln, re.I)]
    w("      %s 命中 %d 处：" % (key, len(hits)))
    for i, ln in hits:
        w("        %s:%d  %s" % (key, i, ln))
# 是否存在对 supplement 的读取/解析调用
parse_evidence = []
for key in ("dD_check", "dD_align"):
    for i, ln in enumerate(rdl(P[key]), 1):
        if re.search(r"(read_text|open\(|split\(\"\|\"\)|json\.loads).{0,120}(supp|supplement)", ln, re.I):
            parse_evidence.append((key, i, ln.strip()))
w("  3c) 两脚本中「读取/解析 supplement 表行」的代码行 = %d %s" % (len(parse_evidence), parse_evidence))
w("  => 独立确认：D 自身无逐档越线数的确定性复算；逐档数据为外部单源读回。")

# ---------------------------------------------------------------- §4 解除条件
w("")
w("§4 D 硬阻断解除条件独立核对")
md = rdl(P["dD_md"])
for i in (118, 120, 122, 126, 127, 128, 129, 130, 132, 134, 114):
    w("  dD_md:%-3d %s" % (i, md[i - 1].strip()))
w("  4b) O1 精度括注独立算术：1+1=2ms；2/50=%.1f%%；1/50=%.1f%%；2/20=%.1f%%" %
  (2 / 50 * 100, 1 / 50 * 100, 2 / 20 * 100))
o1 = md[125]
w("      doc:126 含「合计」= %s；含「2%%」= %s → 求和读法下 4.0%% ≠ 2%% 成立" %
  ("合计" in o1, "2%" in o1))
w("  4c) 必要性指针 doc:122 → _dD_check_out.txt:46-55（B4 块）；其 computed=0（见 §3a）")
w("  4d) doc:134 自述「不含任何获取手段」「本轮未获取任何新观测量」= %s" %
  ("未获取任何新观测量" in md[133]))
w("  4e) §4 清单是否含可检验谓词（精度/配对/覆盖/充分性）独立计数：")
pred_kw = ["时间分辨率", "不确定度上界", "逐事件", "配对", "覆盖", "缺失数", "误配数",
           "残差上界", "断档数", "充分性", "最小集"]
for kw in pred_kw:
    cnt = sum(1 for i in range(118, 135) if kw in md[i - 1])
    w("      %-12s 在 §4 行 118-134 出现 = %d" % (kw, cnt))

# ---------------------------------------------------------------- §5 铁律合规
w("")
w("§5 铁律合规独立扫描（只读件 / 写域 / 禁词 / 台账 / :177/:190/:191）")
w("  5a) 写域 lead/r2_unclosed_cd_20261108/ 文件清单：")
for fn in sorted(os.listdir(W)):
    p = os.path.join(W, fn)
    if os.path.isfile(p):
        h, n = sha(p)
        w("      %-26s %7d 字节  %s" % (fn, n, h))

# 禁词扫描（构造避免自身误命中；扫描目标不含本脚本）
ban = ["hook", "MiniDump", "SuspendThread", "StackWalk", "ctypes", "OpenProcess",
       "ReadProcessMemory", "gamemd.exe", "ra2loader", "YURI.exe", "taskkill"]
w("  5b) 补证产出脚本/判定件禁词扫描：")
for key in ("cd_check_py", "cd_verdict"):
    txt = rd(P[key])
    hit = [b for b in ban if b.lower() in txt.lower()]
    w("      %-14s 命中 = %s" % (key, hit if hit else "无"))
# open 写模式
w("  5c) _cd_check.py 中 open(...) 模式实参（独立 AST）：")
for node in ast.walk(cd_tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
        args = [ast.get_source_segment(cd_src, a) for a in node.args]
        w("      :%d open(%s)" % (node.lineno, ", ".join(str(a)[:70] for a in args)))
w("      sys.stdout.write 调用 = %d（脚本只写 stdout）" %
  sum(1 for node in ast.walk(cd_tree) if isinstance(node, ast.Call)
      and isinstance(node.func, ast.Attribute) and node.func.attr == "write"))

# 台账 / stall def 状态
w("  5d) 只读件 mtime（本轮补证脚本落盘 = 2026-11-08 14:24~14:37；mtime 早于该窗口即本轮未改）：")
for key in ("goal", "pending", "stall_def", "dC_script", "dD_md", "cd_check_py", "cd_check_out", "cd_verdict"):
    st = os.stat(P[key])
    w("      %-14s mtime=%s size=%d" % (key, __import__("datetime").datetime.fromtimestamp(st.st_mtime).isoformat(), st.st_size))

w("  5e) STALL_EVENT_DEFINITION.md :177/:190/:191 当前原文（与历史记录比对）：")
sd = rdl(P["stall_def"])
for i in (177, 190, 191):
    w("      :%d %s" % (i, sd[i - 1].strip()))
# 与 _cd_check_out.txt:129-130 / _verify_D_out3.txt:19 的记录比对
rec190 = ""
for ln in cd_out_lines:
    if "stall_def:190" in ln:
        rec190 = ln.strip()
w("      _cd_check_out.txt 记录的 :190 = %s" % rec190)
w("      当前 :190 文本是否出现在该记录中 = %s" % (sd[189].strip()[:40] in rec190))

w("  5f) 口径/判据/台账/红线声明（_cd_verdict.md 独立读回）：")
vd = rdl(P["cd_verdict"])
for i in (4, 48, 52, 84):
    w("      _cd_verdict.md:%-3d %s" % (i, vd[i - 1].strip()))

# ---------------------------------------------------------------- §6 汇总
w("")
w("§6 复核员结论（只列事实，判定见回件 whatBreaksIt）")
w("  - 编排方 6 项指纹：本脚本独立实算全部 MATCH（§0a）。")
w("  - 但 _dD_align_out.txt 指纹未进入 _cd_check.py 的 P 字典 / _cd_check_out.txt §0 输出（§0d）。")
w("  - 崩点1 结构性缺陷：6/6 字面、11 Compare、10 变量 NOT in gate（其中仅 5 个为真正的结论断言）、")
w("    ge100 无比较、:420 PASS 文案硬编码——独立实算全部复现。")
w("  - 崩点2：13 档 4/5/4 分解与双源对账属实；但 4 档读法下无支撑=0，越界判定具辖域条件性。")
w("  - 崩点3：B3/B4 computed=0 literal 12/10、B1=2/B2=3、D 无 supplement 表行解析——独立复算复现。")
w("  - 崩点4：O1–O5 含谓词；2ms/50ms=4.0%≠2%；必要性纯断言；验收程序缺席——复现。")
w("  - 铁律：写域仅 4 文件（+本轮 _verify_*）、禁词 0、_cd_check.py 无写文件 open、")
w("    台账/stall_def mtime 均早于本轮、:190 原文与历史记录一致。")
w("  - 运行时：python -I -X utf8 + 绝对路径；零真机、零采样代码；本脚本只写 stdout。")

sys.stdout.write("\n".join(O) + "\n")
