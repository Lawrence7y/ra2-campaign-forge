# -*- coding: utf-8 -*-
# 独立复核 C：逐格重读 _dC_cells.txt 与 JSON 对账；检查 all_pass 覆盖；检查分解式是否恒等式
import json, os, ast

ROOT = r"D:/Project/ra2-campaign-forge"
WD = os.path.join(ROOT, "lead/dtrigger_round2_20261107")
D = json.load(open(os.path.join(ROOT, "lead/dtrigger_compare_20261107/_cost_quota_data.json"), "r", encoding="utf-8"))
SC = ["window1", "window3", "window5", "trip1", "trip3", "trip5"]
ideal = {s: (D["meta"]["idealWindow"][s[-1]] if s.startswith("window") else D["meta"]["idealTrip"][s[-1]]) for s in SC}

lines = open(os.path.join(WD, "_dC_cells.txt"), "r", encoding="utf-8").read().split("\n")
rows = []
for l in lines:
    if "|" not in l or not l.strip().startswith("C"):
        continue
    f = [z.strip() for z in l.split("|")]
    rows.append(f)
print("cell data rows =", len(rows))

viol = 0
for f in rows:
    c, s = f[0], f[1]
    cap, nf, up, idl = int(f[2]), int(f[3]), int(f[4]), int(f[5])
    recall, preempt, collapse = int(f[6]), int(f[7]), int(f[8])
    chk, hits, grp = f[9], int(f[10]), f[11]
    jcap = D["results"][c][s]["captured"]
    jnf = D["nofalse"][c][s]
    jup = D["upper"][c][s]
    jhits = D["criteria"][c]["hits"]
    bad = []
    if (cap, nf, up, idl) != (jcap, jnf, jup, ideal[s]): bad.append("json")
    if recall != idl - nf: bad.append("recall")
    if preempt != nf - cap: bad.append("preempt")
    if collapse != idl - cap: bad.append("collapse")
    if collapse != recall + preempt: bad.append("decomp")
    if chk != "OK": bad.append("chk")
    if hits != jhits: bad.append("hits")
    exp_grp = "A(C1/C4/C5)" if c.startswith(("C1-", "C4-", "C5-")) else "B(C2/C3)"
    if grp != exp_grp: bad.append("group")
    if bad:
        viol += 1
        print("  VIOLATION", c, s, bad)
print("逐格重读违例 =", viol)

# all_pass 覆盖分析
src = open(os.path.join(WD, "_dC_recompute.py"), "r", encoding="utf-8").read()
tree = ast.parse(src)
for n in ast.walk(tree):
    if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "all_pass" for t in n.targets):
        seg = ast.get_source_segment(src, n.value)
        print("--- all_pass predicate (script lines %d-%d) ---" % (n.lineno, n.end_lineno))
        print(seg)
print("--- 9.x claims NOT gated by all_pass (from _dC_recompute.py source) ---")
checks = {
 "9.3 A cap==capUpper 54/54": "len(A_cap_eq_up) == 54",
 "9.3 A ideal-capUpper==preempt 54/54": "len(A_maxloss_eq) == 54",
 "9.3 A capUpper==ideal 0/54": "len(A_up_eq_ideal) == 0",
 "9.4 71 格召回损失>0": "len(B_preempt0_recall_gt0) == 71",
 "9.5 额外 2 格是 C3-N16-r2 trip3/trip5": "assert on B_upideal_but_preempt_gt0",
 "9.6 括注 7 档只覆盖 42 格": "len(named_set) == 42",
 "9.7 高档 >=100ms": "no check",
 "7b 可读行全部 >50ms": "no aggregate assertion (only per-row label)",
 "7c-2..7h": "hardcoded literal emit() strings, not computed",
}
for k, v in checks.items():
    print("  %-48s -> %s" % (k, v))

# 分解式是否恒等式（对任意整数恒成立？）
print("--- decomposition tautology check over random integers ---")
import itertools
cnt = 0
for idl, nf, cap in itertools.product(range(-5, 6), repeat=3):
    collapse = idl - cap
    recall = idl - nf
    preempt = nf - cap
    if collapse == recall + preempt:
        cnt += 1
print("  identity holds for %d/1331 (idl,nf,cap) triples sampled -> tautology" % cnt)
