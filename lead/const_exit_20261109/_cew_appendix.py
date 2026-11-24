# -*- coding: utf-8 -*-
"""_cew_appendix.py -- build appendices A-E from archived + my own evidence.

Pure read of JSON + source text; no checked script is executed.
Writes _cew_appendix.md in the write domain only.
"""
import ast
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "const_exit_20261109"

ev = json.load(open(WD / "_cew_evidence_out.json", encoding="utf-8"))["evidence"]
final = json.load(open(WD / "_ce_final_out.json", encoding="utf-8"))
orch_raw = json.load(open(WD / "_ce_orchestrator_raw.json", encoding="utf-8"))
table = json.load(open(WD / "_ce_table_out.json", encoding="utf-8"))
impact = json.load(open(WD / "_ce_impact_out.json", encoding="utf-8"))
adjud = json.load(open(WD / "_cev_adjudicate_out.json", encoding="utf-8"))

rows = final["rows"]
by_rel = {r["rel"]: r for r in rows}
orch_cls = {}
for r in orch_raw["const_or_noexit"]:
    orch_cls[r["rel"]] = r["cls"]
for r in orch_raw["conditional"]:
    orch_cls[r["rel"]] = "CONDITIONAL_EXIT"

# Adjudicate basis from _cev_adjudicate_out.json (if present)
adjud_basis = {}
if isinstance(adjud, dict):
    for k in ("diffs", "rows", "per_file"):
        v = adjud.get(k)
        if isinstance(v, dict):
            adjud_basis.update({str(x): str(y) for x, y in v.items()})
        elif isinstance(v, list):
            for x in v:
                if isinstance(x, dict) and "rel" in x:
                    adjud_basis[x["rel"]] = json.dumps(
                        {kk: vv for kk, vv in x.items() if kk != "rel"},
                        ensure_ascii=False)[:300]

# Fallback: parse _cev_adjudicate_stdout.txt for per-file basis text
std = (WD / "_cev_adjudicate_stdout.txt").read_text(encoding="utf-8")
cur = None
for line in std.split("\n"):
    s = line.strip()
    if s.startswith("lead/") or s.startswith("out/"):
        cur = s
    elif cur and (" | " in s or s.startswith("CONSTANT_") or s.startswith("NO_EXIT")):
        if cur not in adjud_basis:
            adjud_basis[cur] = s[:300]
        cur = None

out = []
w = out.append
w("## 附录：逐件归属全表（413 件，每类逐件给 `文件:行` 依据）\n")
w("> 生成源：我本会话实跑 `_cew_evidence.py`（纯 AST，`n_site_count_mismatch: 0`，"
  "413 件站点数与归档逐件全等）、`_ce_final_out.json:rows`、`_ce_orchestrator_raw.json`、"
  "`_ce_table_out.json`。列「编排方」= 机械 verdict；「最终」= AST 依据定级。"
  "两者不一致以依据为准，并在附录 D 并列。SHA256/字节数来自归档 `rows`（我实跑读取源文件字节）"
  "，逐件 64 位指纹全量在 `_ce_final_out.json:rows` / `_ce_table_out.json`。\n")
w("> **`lead/gate_fp7_20261108/_g7_reverse_validate.py` / `lead/gate_n13_20261109/_n13_predicates.py`** 为编排方与判定方共同产出的真实"
  "文件名在显示层的脱敏占位符（按铁律原样抄写），对应磁盘上确实存在的两件 .py。\n")

# ---------- A: CONSTANT_EXIT (18) ----------
w("### 附录 A — CONSTANT_EXIT 全部 18 件\n")
w("判据：`SITES` 非空、无 DATA、可达状态集合恰为 `{0}`。我本会话实跑 `_ce_minimal.py`"
  " 对 18 件全部复验 `CONSTANT_EXIT [0]`。\n")
w("| # | rel | 编排方 | 最终 | 出口 site `文件:行` + AST 事实 | 可达状态 | 末行锚 |")
w("|---|---|---|---|---|---|---|")
const_rows = [r for r in rows if r["cls"] == "CONSTANT_EXIT"]
const_rows.sort(key=lambda r: r["rel"])
for i, r in enumerate(const_rows, 1):
    rel = r["rel"]
    e = ev[rel]
    sites = "; ".join("`%s:%d` `%s`" % (rel, s["line"], s["expr"])
                      for s in e["sites"]) or "NO_SITE"
    # main's own returns: show for sys.exit(main()) cases
    extra = ""
    mains = [f for f in e["func_returns"] if f["func"] == "main"]
    if mains:
        rs = mains[0]["returns"]
        extra = "；`main` 自身 return " + (", ".join("`:%d` `%s`" % (ln, ex[:40])
                                              for ln, ex in rs[:6]) if rs else "（无 return，隐式 0）")
    if not mains and e["sites"] and "main()" in e["sites"][0]["expr"]:
        extra = "；`main` 无显式 return（隐式 `None` → 0）"
    anchors = "`%s:%d`（全文 %d 行）" % (rel, e["n_lines"], e["n_lines"])
    w("| %d | `%s` | %s | **CONSTANT_EXIT** | %s%s | `{0}` | %s |" %
      (i, rel, orch_cls.get(rel, "?"), sites, extra, anchors))
w("")
w("要点：`VERIFY_A8.py:52-55` 的 `FAILED.append` 与 `:796 return 0` 无数据通路；"
  "`_probe_x_glm_addr_check.py:40-41` 算出 `rc=1` 但 `:44` 仍 `raise SystemExit(0)`；"
  "`_n4_ast_scan.py` / `_proxy_covariate_accounting.py` 两件编排方误判 CONDITIONAL（嵌套函数"
  " return 被 `ast.walk(fn)` 算进 main）。\n")

# ---------- B: NO_EXIT_AT_ALL (263) ----------
w("### 附录 B — NO_EXIT_AT_ALL 全部 263 件\n")
w("判据：`SITES` 为空；正常结束即 0。逐件给「全文末行 `文件:行`」作锚点 + 我实跑 AST"
  " 确认 `n_sites = 0`（与归档 `n_sites` 逐件相等）。`EXIT=0` 只证明进程没崩 / 没抛"
  " 未捕获异常。\n")
w("| # | rel | 编排方 | 最终 | AST 依据（`文件:行`，0 个出口 site） | SHA256[:12] / B |")
w("|---|---|---|---|---|---|")
noexit = [r for r in rows if r["cls"] == "NO_EXIT_AT_ALL"]
noexit.sort(key=lambda r: r["rel"])
for i, r in enumerate(noexit, 1):
    rel = r["rel"]
    e = ev[rel]
    w("| %d | `%s` | %s | NO_EXIT_AT_ALL | `%s:%d`（全文 %d 行，`n_sites=0`） | `%s` / %d |" %
      (i, rel, orch_cls.get(rel, "?"), rel, e["n_lines"], e["n_lines"],
       r["sha256"][:12], r["bytes"]))
w("")
w("其中台账 5 行真零信息登记的对象全部在此表："
  "`lead/re_line_20261105/D21_RULING/_d21_burden5.py`、"
  "`lead/re_line_20261105/V6_V3_REVIEW/_leader_crossframe_check.py`、"
  "`lead/re_line_20261105/_leader/_a7_acf_probe.py`、"
  "`lead/re_line_20261105/_leader/_intra_frame_census.py`（被 2 行点名）。"
  "另有 `lead/d26_ruling_20261106/_d26_facts.py` … `lead/d30_ruling_20261106/_d30_facts.py`"
  " 五件（AST `n_sites=0`），它们是 `PENDING_DECISIONS.md:92/105/117/129/162` 行内并列被引"
  " 的事实脚本，**不是那句 exit=0 的主语**。\n")
w("`FILE_OR_STDOUT_ONLY_VERDICT` 191 件、`VERDICT_VIA_ASSERT_ONLY` 54 件在本表内部分重叠"
  "（flag 计数见 `_ce_final_stdout.txt:20-28`）；assert-only 通道**未逐件定级（未验）**。\n")

# ---------- C: CONDITIONAL_EXIT (132) ----------
w("### 附录 C — CONDITIONAL_EXIT 全部 132 件\n")
w("判据：`SITES` 非空 ∧（有 DATA ∨ 可达状态集合 ≥2）。逐件给每个出口 site 的 `文件:行` +"
  " 表达式；`EXIT=0` 有信息，但强度取决于 §3.3 的合取/失败可达性条件。\n")
w("| # | rel | 编排方 | 最终 | 出口 site（`文件:行` = 表达式） | 可达状态 |")
w("|---|---|---|---|---|---|")
cond = [r for r in rows if r["cls"] == "CONDITIONAL_EXIT"]
cond.sort(key=lambda r: r["rel"])
for i, r in enumerate(cond, 1):
    rel = r["rel"]
    e = ev[rel]
    st = ",".join(str(x) for x in r["attainable_statuses"]) or "DATA"
    if r["any_data"]:
        st += "+DATA"
    sites = "; ".join("`%s:%d` = `%s`" % (rel, s["line"], s["expr"][:60])
                      for s in e["sites"]) or "（异常通道）"
    w("| %d | `%s` | %s | CONDITIONAL_EXIT | %s | `%s` |" %
      (i, rel, orch_cls.get(rel, "?"), sites, st))
w("")
w("代表：`lead/d27_ruling_20261106/check_d27.py:59/99/101/107`（0/1/2 真分支，§2.4）、"
  "`lead/goal1_a8_fix_20261022/VERIFY_A8B.py:451/455`（`return 0 if not ref else 1`）、"
  "`lead/dtrigger_compare_20261107/_check_dtrigger.py:228`"
  "（`raise SystemExit(0 if ok else 1)`）、"
  "`lead/count_invariant_20261109/_ci_counterexamples.py:152`（`0 if all(RESULTS.values()) else 1`）、"
  "`lead/refsync_scope_20261109/_rs_carrier_scan.py:349/352`（72 次被引，CONDITIONAL）。"
  "4 件生产门禁 d27–d30 **不在 413 批内**（在 kd 173 普查内），故不列本表，见 §2.4。\n")

# ---------- D: 44 diffs ----------
w("### 附录 D — 44 件「机械 verdict ≠ AST 依据」逐件并列\n")
w("依据源：`_cev_adjudicate_stdout.txt:5-93`（复核件独立分类器逐件 AST 依据）、"
  "`_ce_compare_stdout.txt:4-55`、我实跑 `_cew_evidence.py` 的 site `文件:行`。"
  "分组：A=31 件字面量分支实为多状态；B=9 件漏 `raise SystemExit`；C=2 件漏 raise 的恒 0；"
  "D=2 件嵌套 return 误算；E=混合形态（归 A/B）。\n")
w("| # | 组 | rel | 编排方机械 verdict | 最终（依据为准） | AST 依据（`文件:行`） | 可达状态 |")
w("|---|---|---|---|---|---|---|")
diffs = [r for r in rows if orch_cls.get(r["rel"]) != r["cls"]]
diffs.sort(key=lambda r: (orch_cls.get(r["rel"], ""), r["cls"], r["rel"]))
for i, r in enumerate(diffs, 1):
    rel = r["rel"]
    a, b = orch_cls.get(rel, "?"), r["cls"]
    if a == "CONSTANT_EXIT" and b == "CONDITIONAL_EXIT":
        g = "A"
    elif a == "NO_EXIT_AT_ALL" and b == "CONDITIONAL_EXIT":
        g = "B"
    elif a == "NO_EXIT_AT_ALL" and b == "CONSTANT_EXIT":
        g = "C"
    elif a == "CONDITIONAL_EXIT" and b == "CONSTANT_EXIT":
        g = "D"
    else:
        g = "E"
    e = ev[rel]
    sites = "; ".join("`%s:%d` `%s`" % (rel, s["line"], s["expr"][:48])
                      for s in e["sites"]) or "NO_SITE"
    basis = adjud_basis.get(rel, "")
    if basis:
        sites += "；" + basis[:150].replace("|", "/")
    st = str(r["attainable_statuses"]) + ("+DATA" if r["any_data"] else "")
    w("| %d | %s | `%s` | **%s** | **%s** | %s | `%s` |" %
      (i, g, rel, a, b, sites, st))
w("")
w("复核件 `_cev_compare_stdout.txt:5` 记 `orchestrator vs mine n_diff 44"
  " Counter({CONSTANT→CONDITIONAL:31, NO_EXIT→CONDITIONAL:9,"
  " CONDITIONAL→CONSTANT:2, NO_EXIT→CONSTANT:2})`，与判定 `_ce_final_out.json:diffs`"
  " 逐件全等（`_cev_compare_stdout.txt:55`：`agree 44 disagree 0`）。\n")

# ---------- E: ledger 24 lines ----------
w("### 附录 E — 两件台账全部 24 个标记行逐行清单\n")
w("源：`_ce_impact_out.json:ledger.lines`（我本会话实读两件台账原文逐行核对）、"
  "`_cev_ledger_stdout.txt:12-36`。`flat` = 「行内任一 basename 命中零信息类」（编排方"
  " 口径）；`主语类` = 「`EXIT=0` 最近 basename」的 AST 最终定级。\n")
w("| # | 台账:行 | 行内 basenames → 类 | 原文摘录 | flat 命中 | `EXIT=0` 主语 / 类 | 处置 |")
w("|---|---|---|---|---|---|---|")
led_lines = impact["ledger"]["lines"]
for i, L in enumerate(led_lines, 1):
    fl = "%s:%d" % (L["file"], L["line"])
    cls = ", ".join("%s→%s" % (b, c) for b, c in L["final_classes"].items())
    txt = L["text"].replace("|", "/")[:150]
    flat = "是" if L["final_hit_flat"] else "否"
    subj = L["exit_subject"] or "（无 EXIT=0 token）"
    subjcls = L["exit_subject_final"] or "未验"
    if L["line"] in (7569, 7634, 8383, 9588, 9679) and L["file"].endswith("GOAL_THREE_TARGETS_20261018.md"):
        act = "**加注：真零信息**"
    elif L["file"].endswith("PENDING_DECISIONS.md") and L["line"] in (92, 105, 117, 129, 162):
        act = "**加注：归错对象（主语是 CONDITIONAL 门禁）**"
    elif L["line"] == 9406:
        act = "未验（无 EXIT=0 token）"
    elif L["line"] == 186:
        act = "无需加注（CONDITIONAL）"
    else:
        act = "无需加注（主语 CONDITIONAL / UNRESOLVED）"
    w("| %d | `%s` | %s | %s | %s | `%s` / `%s` | %s |" %
      (i, fl, cls, txt, flat, subj, subjcls, act))
w("")
w("`CONSTANT_EXIT` 在两件台账里 **0 行**（`_cev_ledger_stdout.txt:2`："
  "`n_constant_flat 0 / n_constant_subject 0`）。编排方 `ledger_hits_total`"
  " `{PENDING:12, GOAL_THREE:23}` = 35 是 **basename 出现次数**，不是行数"
  "（`_cev_ledger2_stdout.txt`：`raw_basename_occurrences 35 / marked_lines_with_py 24`）。\n")

# ---------- write ----------
prose = (WD / "_cew_prose.md").read_text(encoding="utf-8")
assert "<!--APPENDIX_MARKER-->" in prose
doc = prose.replace("<!--APPENDIX_MARKER-->", "\n".join(out))
(WD / "CONST_EXIT_CENSUS.md").write_text(doc, encoding="utf-8", newline="\n")
print("WROTE", (WD / "CONST_EXIT_CENSUS.md").as_posix())
print("bytes", len(doc.encode("utf-8")), "lines", doc.count("\n") + 1)
print("A", len(const_rows), "B", len(noexit), "C", len(cond), "D", len(diffs), "E", len(led_lines))
print("sections", [x for x in ["## 1", "## 2", "## 3", "## 4", "## 5", "## 6"] if x in doc])
for kw in ["CONSTANT_EXIT", "NO_EXIT_AT_ALL", "CONDITIONAL_EXIT", "EXIT=0 零信息",
           "台账逐行", "VERIFY_A8", "d27", "正交", "未验",
           "被核对象 SHA256 = 6c032bd5c59dcf61e80146ebfa2d9a8603f898eebcbed45719e8c4270c8be332，字节数 = 362"]:
    print("kw", kw, doc.count(kw))
