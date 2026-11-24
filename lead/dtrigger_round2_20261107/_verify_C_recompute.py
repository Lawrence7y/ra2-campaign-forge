# -*- coding: utf-8 -*-
# 独立复核：从 _cost_quota_data.json 重算，不 import 调查员 _dC_recompute.py，
# 不 import _cost_quota*，只依赖标准库 json / collections。
# 所有断言自行定义，数字独立输出。
import json, collections, os

P = r"D:/Project/ra2-campaign-forge/lead/dtrigger_compare_20261107/_cost_quota_data.json"
with open(P, "r", encoding="utf-8") as f:
    D = json.load(f)

SC = ["window1", "window3", "window5", "trip1", "trip3", "trip5"]
ideal = {}
for s in SC:
    n = s[-1]
    ideal[s] = D["meta"]["idealWindow"][n] if s.startswith("window") else D["meta"]["idealTrip"][n]
print("ideal per scenario:", ideal)

# 独立构造 156 格
rows = []
for c, byscen in D["results"].items():
    for s in SC:
        cap = byscen[s]["captured"]
        nf = D["nofalse"][c][s]
        up = D["upper"][c][s]
        idl = ideal[s]
        hits = D["criteria"][c]["hits"]
        rows.append(dict(c=c, s=s, cap=cap, nf=nf, up=up, idl=idl, hits=hits,
                         recall=idl - nf, preempt=nf - cap, collapse=idl - cap))

print("cells =", len(rows), "distinct criteria =", len(set(r["c"] for r in rows)),
      "distinct scenarios =", len(set(r["s"] for r in rows)))

# 分解式：恒等式 collapse == recall + preempt
decomp_bad = [r for r in rows if r["collapse"] != r["recall"] + r["preempt"]]
nonneg_bad = [r for r in rows if r["recall"] < 0 or r["preempt"] < 0]
chain_bad = [r for r in rows if not (0 <= r["cap"] <= r["nf"] <= r["idl"] and 0 <= r["cap"] <= r["up"] <= r["idl"])]
cap_eq_ideal = [r for r in rows if r["cap"] == r["idl"]]
print("decomp bad =", len(decomp_bad), "nonneg bad =", len(nonneg_bad),
      "chain bad =", len(chain_bad), "cap==ideal =", len(cap_eq_ideal))

# 分组：前缀 vs hits
A = [r for r in rows if r["c"].startswith(("C1-", "C4-", "C5-"))]
B = [r for r in rows if r["c"].startswith(("C2-", "C3-"))]
A_hits = [r for r in rows if r["hits"] == 1681]
B_hits = [r for r in rows if r["hits"] < 1681]
unclassified = [r for r in rows if r not in A and r not in B]
print("A(prefix C1/C4/C5) =", len(A), "B(prefix C2/C3) =", len(B),
      "unclassified =", len(unclassified), "A+B =", len(A) + len(B))
print("A_hits(1681) =", len(A_hits), "B_hits(<1681) =", len(B_hits))
print("prefix-A == hits-A (cell sets identical) =",
      set((r["c"], r["s"]) for r in A) == set((r["c"], r["s"]) for r in A_hits))
print("prefix-B == hits-B (cell sets identical) =",
      set((r["c"], r["s"]) for r in B) == set((r["c"], r["s"]) for r in B_hits))
print("A hits values =", sorted(set(r["hits"] for r in A)))
print("B hits values =", sorted(set(r["hits"] for r in B)))

# A 族
A_nf_eq = sum(1 for r in A if r["nf"] == r["idl"])
A_recall0 = sum(1 for r in A if r["recall"] == 0)
A_preempt0 = sum(1 for r in A if r["preempt"] == 0)
A_collapse_gt0 = sum(1 for r in A if r["collapse"] > 0)
A_cap_eq_up = sum(1 for r in A if r["cap"] == r["up"])
A_ideal_minus_up_eq_preempt = sum(1 for r in A if r["idl"] - r["up"] == r["preempt"])
A_up_eq_ideal = sum(1 for r in A if r["up"] == r["idl"])
print("A: nf==ideal =", A_nf_eq, "recall==0 =", A_recall0, "preempt==0 =", A_preempt0,
      "collapse>0 =", A_collapse_gt0, "cap==up =", A_cap_eq_up,
      "ideal-up==preempt =", A_ideal_minus_up_eq_preempt, "up==ideal =", A_up_eq_ideal)

# B 族
B_p0 = [r for r in B if r["preempt"] == 0]
B_up_ideal = [r for r in B if r["up"] == r["idl"]]
B_p0_up = [r for r in B if r["preempt"] == 0 and r["up"] == r["idl"]]
B_up_not_p0 = [r for r in B if r["up"] == r["idl"] and r["preempt"] > 0]
B_p0_recall_gt0 = [r for r in B_p0 if r["recall"] > 0]
B_nf_eq = sum(1 for r in B if r["nf"] == r["idl"])
B_recall0 = sum(1 for r in B if r["recall"] == 0)
print("B: nf==ideal =", B_nf_eq, "recall==0 =", B_recall0)
print("B preempt==0 =", len(B_p0), "B up==ideal =", len(B_up_ideal),
      "intersection =", len(B_p0_up), "up==ideal but preempt>0 =", len(B_up_not_p0),
      "71-ish recall>0 among p0 =", len(B_p0_recall_gt0))
for r in B_up_not_p0:
    print("   extra cell:", r["c"], r["s"], "cap=%d nf=%d up=%d idl=%d preempt=%d" %
          (r["cap"], r["nf"], r["up"], r["idl"], r["preempt"]))

cnt = collections.Counter(r["c"] for r in B_p0)
print("p0 distribution (13 criteria expected):", len(cnt), sorted(cnt.items()))
print("p0 total from counter =", sum(cnt.values()))

# 括注 7 档
NAMED = ["C2-P95x3", "C2-P99x3", "C3-r4", "C3-r4-clean", "C3-r8", "C3-r8-clean", "C3-r12"]
named_cells = [r for r in B_p0 if r["c"] in NAMED]
not_named_cells = [r for r in B_p0 if r["c"] not in NAMED]
print("named 7 criteria -> p0 cells =", len(named_cells),
      "not-named p0 cells =", len(not_named_cells),
      "all named criteria x6 total rows =", sum(1 for r in B if r["c"] in NAMED))

# §2 ideal 交叉
for s in SC:
    mx_nf = max(D["nofalse"][c][s] for c in D["nofalse"])
    mx_up = max(D["upper"][c][s] for c in D["upper"])
    mx_cap = max(D["results"][c][s]["captured"] for c in D["results"])
    print("  %-8s ideal=%3d max(nf)=%3d max(up)=%3d max(cap)=%3d nf/up==ideal:%s" %
          (s, ideal[s], mx_nf, mx_up, mx_cap, mx_nf == ideal[s] and mx_up == ideal[s]))
