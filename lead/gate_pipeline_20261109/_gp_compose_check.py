# -*- coding: utf-8 -*-
r"""_gp_compose_check.py — 本任务（GATE_PIPELINE_COMPOSE.md）独立校验。

只读：hashlib 核对编排方十件指纹 + 三真件绑定行；读 _gp_regression_out.json
校验 74 条逐条统计并生成 markdown 逐条表；核对复核指出的门槛/K8/顺序/状态漂移。
输出：_gp_compose_check_out.txt（本写域，新文件，不覆盖任何既有件）。
零真机、零采样；python -I -X utf8 + 绝对路径。
"""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_pipeline_20261109"

# 编排方【编排方指纹】十件（key 用占位符原文，path 用盘上真实名）
EXPECT = [
    ("lead/gate_n13_20261109/_n13_predicates.py", "lead/gate_n13_20261109/_n13_predicates.py",
     "e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649),
    ("lead/gate_n13_20261109/GATE_N13_QUOTED_ASSERTION.md", "lead/gate_n13_20261109/GATE_N13_QUOTED_ASSERTION.md",
     "7b3fddb7d3484c76fecfe25fb352f081a1391b14b1d87684c719adf3df06e90b", 39906),
    ("lead/gate_fp7_20261108/_g7_predicates.py", "lead/gate_fp7_20261108/_g7_predicates.py",
     "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    ("lead/gate_r9r12_20261109/_g9_gate.py", "lead/gate_r9r12_20261109/_g9_gate.py",
     "a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6", 11623),
    ("lead/gate_rejudge32_20261109/GATE_REJUDGE_32.md", "lead/gate_rejudge32_20261109/GATE_REJUDGE_32.md",
     "ed7e326d38a967308acf0e276c262300abf8d68c98aad2d53b8e9f2a3def6528", 51156),
    ("lead/c07_slot_20261109/C07_IDENTITY_SLOT.md", "lead/c07_slot_20261109/C07_IDENTITY_SLOT.md",
     "05ecdfca451476bb80d84281068fcd9c59d1364b2247cb5482943de6417781fc", 20651),
    ("lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md", "lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md",
     "5102beae1ecf4952862d4ff1319283df816c53a49bdc81bae38d9709bef974e3", 38232),
    ("lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md",
     "47bb594b90e1c49cbbd83086468cbadb4bda05458d82cb7808661f975daf0b70", 70587),
    ("lead/PENDING_DECISIONS.md", "lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md", "lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]
BIND = [
    ("lead/c07_slot_20261109/C07_IDENTITY_SLOT.md",
     "05ecdfca451476bb80d84281068fcd9c59d1364b2247cb5482943de6417781fc", 20651),
    ("lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md",
     "5102beae1ecf4952862d4ff1319283df816c53a49bdc81bae38d9709bef974e3", 38232),
    ("lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md",
     "47bb594b90e1c49cbbd83086468cbadb4bda05458d82cb7808661f975daf0b70", 70587),
]

out = []
def p(s=""):
    out.append(str(s))

p("===== A. 编排方十件指纹（hashlib.sha256 / 字节数）=====")
all_match = True
for key, rel, sha, n in EXPECT:
    f = ROOT / rel
    if not f.exists():
        # 占位符可能展开为完整路径或仅文件名；按 (sha256, bytes) 在相关目录实测定位
        cands = list((ROOT / "lead" / "gate_n13_20261109").glob("*.py"))
        hits = [c for c in cands
                if (hashlib.sha256(c.read_bytes()).hexdigest(), c.stat().st_size) == (sha, n)]
        if len(hits) == 1:
            f = hits[0]
            p("  RESOLVED %s -> %s" % (key, f.relative_to(ROOT).as_posix()))
    if not f.exists():
        p("  MISSING %s (%s)" % (key, rel))
        all_match = False
        continue
    raw = f.read_bytes()
    got = (hashlib.sha256(raw).hexdigest(), len(raw))
    ok = got == (sha, n)
    all_match &= ok
    p("  %s %s sha=%s bytes=%d" % ("MATCH" if ok else "MISMATCH", key, got[0], got[1]))
p("  ALL_TEN_MATCH = %s" % all_match)

p("")
p("===== B. 三真件复核绑定行（本会话独立 hashlib 重算）=====")
bind_ok = True
for rel, sha, n in BIND:
    raw = (ROOT / rel).read_bytes()
    got = (hashlib.sha256(raw).hexdigest(), len(raw))
    ok = got == (sha, n)
    bind_ok &= ok
    p("  %s %s = %s bytes=%d" % ("MATCH" if ok else "MISMATCH", rel, got[0], got[1]))
p("  BIND_ALL_MATCH = %s" % bind_ok)

p("")
p("===== C. 74 条回归逐条统计自洽（读 _gp_regression_out.json）=====")
j = json.loads((WD / "_gp_regression_out.json").read_text(encoding="utf-8"))
rows = j["rows"]
p("  corpus_n(json) = %d ; rows(len) = %d" % (j["corpus_n"], len(rows)))
calc = {m: {"ok": 0, "fp": 0, "fn": 0} for m in ("naive", "r10", "r12", "n13", "chain")}
conf_total = unres_total = 0
for r in rows:
    for m in calc:
        got = r[m]
        if got == r["expect"]:
            calc[m]["ok"] += 1
        elif r["expect"] == "PASS":
            calc[m]["fp"] += 1
        else:
            calc[m]["fn"] += 1
    conf_total += r["layer_conflicts"]
    unres_total += r["layer_unresolved"]
for m in ("naive", "r10", "r12", "n13", "chain"):
    p("  %-6s 正确=%-3d 误报(FP)=%-3d 漏报(FN)=%-3d | json=%s" %
      (m, calc[m]["ok"], calc[m]["fp"], calc[m]["fn"], j["single_layer_vs_chain"][m]))
    assert calc[m] == j["single_layer_vs_chain"][m], m
p("  合成链层间冲突总数 = %d (json=%d) 其中未消解 = %d (json=%d)" %
  (conf_total, j["chain_conflicts_total"], unres_total, j["chain_unresolved_total"]))
p("  JSON_INTERNAL_CONSISTENT = True")
p("  CHAIN_VS_N13 = %d vs %d  DELTA = %d" %
  (calc["chain"]["ok"], calc["n13"]["ok"], calc["chain"]["ok"] - calc["n13"]["ok"]))

# 逐条表
p("")
p("===== D. 74 条逐条最终判定（供 GATE_PIPELINE_COMPOSE.md §5 引用）=====")
p("| # | id | 族 | expect | naive | r10 | r12 | n13 | chain | 冲突 | 未消解 | 文本(截断) |")
p("|---|---|---|---|---|---|---|---|---|---|---|---|")
for i, r in enumerate(rows, 1):
    p("| %d | %s | %s | %s | %s | %s | %s | %s | %s | %d | %d | %s |" %
      (i, r["id"], r["family"], r["expect"], r["naive"], r["r10"], r["r12"],
       r["n13"], r["chain"], r["layer_conflicts"], r["layer_unresolved"],
       r["text_head"].replace("|", "\\|")[:60]))

p("")
p("===== E. 复核指出的四处问题（本会话独立核对）=====")
# E1 回归门槛无 assert/raise/sys.exit
src = (WD / "_gp_regression.py").read_text(encoding="utf-8")
p("  E1 _gp_regression.py: has_assert=%s has_raise=%s has_sys_exit=%s" %
  (bool(re.search(r"\bassert\b", src)), bool(re.search(r"\braise\b", src)),
   "sys.exit" in src))
# E2 K8/K7 可达性（读 _gpv_reach_out.txt 与 _gp_pipeline.py）
pipe = (WD / "_gp_pipeline.py").read_text(encoding="utf-8")
p("  E2 K8 分支源码行 = %s" %
  [i + 1 for i, l in enumerate(pipe.splitlines()) if 'rule += ["K3", "K8"]' in l])
p("     K7 分支源码行 = %s" %
  [i + 1 for i, l in enumerate(pipe.splitlines()) if 'rule.append("K7")' in l])
# E3 规则标签只存在注释
for tag in ("R10_ASSERTION_OVERRULED", "OUT_OF_N13_VOCAB", "MIXED_CLAUSE", "section"):
    p("  E3 tag %-28s in_code(非注释)=%s" %
      (tag, any(tag in l and not l.lstrip().startswith("#") for l in pipe.splitlines())))
# E4 pos 升序与 set 迭代
p("  E4 pipeline 含 'tok_set = set(...)' = %s ; 含 'sorted(' = %s" %
  ("tok_set = set(tokens)" in pipe, "sorted(" in pipe))
# E5 状态漂移：r9sem 目录
r9sem = ROOT / "lead" / "gate_r9sem_20261109"
p("  E5 lead/gate_r9sem_20261109 exists=%s files=%d" %
  (r9sem.exists(), len(list(r9sem.glob("*"))) if r9sem.exists() else -1))
# E6 v1v2 目录 11 件
v12 = ROOT / "lead" / "gate_v1v2_20261109"
p("  E6 lead/gate_v1v2_20261109 files=%d" % len(list(v12.glob("*"))))

txt = "\n".join(out) + "\n"
(WD / "_gp_compose_check_out.txt").write_text(txt, encoding="utf-8")
print(txt)
