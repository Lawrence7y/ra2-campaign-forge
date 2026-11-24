# -*- coding: utf-8 -*-
# _pvv_rho_basis.py — 独立从原始 rows 验证 rho_bar≈1 的机制依据：18 条增益是否全部落在 K3 分支条件上
# K3 条件见 _gp_pipeline.py:168: n13_v == "PASS" and r10_v == "CATCH"
import json
ROOT = r"D:/Project/ra2-campaign-forge"
V1 = json.load(open(ROOT + "/lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json", encoding="utf-8"))
V2 = json.load(open(ROOT + "/lead/gate_pipeline_20261109/_gp_regression_out.json", encoding="utf-8"))
a, b = {r["id"]: r for r in V1["rows"]}, {r["id"]: r for r in V2["rows"]}
common = sorted(set(a) & set(b))
flips = [i for i in common if a[i]["expect"] != b[i]["expect"]]
strict = [i for i in common if i not in flips and all(
    a[i].get(k) == b[i].get(k) for k in ("text_head", "tokens", "expect", "naive", "r10", "r12", "n13"))]
gains = [i for i in strict if a[i]["chain"] == "CATCH" and b[i]["chain"] == "PASS"]
fp72 = [i for i in strict if a[i]["expect"] == "PASS" and a[i]["chain"] == "CATCH"]
still = [i for i in fp72 if b[i]["chain"] == "CATCH"]

print("=== 18 条增益的四个单层列（72 版 / 74 版逐行相同） ===")
from collections import Counter
pat = Counter()
for i in gains:
    r = a[i]
    pat[(r["naive"], r["r10"], r["r12"], r["n13"], r["expect"], r["chain"], b[i]["chain"])] += 1
for k, v in sorted(pat.items(), key=lambda x: -x[1]):
    print(f"  n={v:2d} naive/r10/r12/n13/expect/72chain/74chain = {k}")
print("all 18 gains have r10=CATCH and n13=PASS ?", all(a[i]["r10"] == "CATCH" and a[i]["n13"] == "PASS" for i in gains))
print("all 18 gains expect=PASS ?", all(a[i]["expect"] == "PASS" for i in gains))
print("all 18 gains 74 chain=PASS ?", all(b[i]["chain"] == "PASS" for i in gains))
print("all 18 gains single-layer cols identical across versions ?", all(
    a[i][k] == b[i][k] for i in gains for k in ("naive", "r10", "r12", "n13")))

print("=== 20 条 72 版 FP 的构成 ===")
pat2 = Counter()
for i in fp72:
    r = a[i]
    pat2[(r["r10"], r["n13"], r["expect"], r["chain"], b[i]["chain"])] += 1
for k, v in sorted(pat2.items(), key=lambda x: -x[1]):
    print(f"  n={v:2d} r10/n13/expect/72chain/74chain = {k}")
print("all 20 FP r10=CATCH and n13=PASS ?", all(a[i]["r10"] == "CATCH" and a[i]["n13"] == "PASS" for i in fp72))
print("still FP ids =", still)
for i in still:
    print("  ", i, "72:", {k: a[i][k] for k in ("expect","naive","r10","r12","n13","chain")},
          "74:", {k: b[i][k] for k in ("expect","naive","r10","r12","n13","chain")})

print("=== 方向一致性（零反向） ===")
rev = [i for i in strict if a[i]["chain"] == "PASS" and b[i]["chain"] == "CATCH"]
print("reverse-direction rows =", len(rev), rev)
print("rho_bar=1 argument: 18/18 share same r10=CATCH,n13=PASS (K3 condition), same expect=PASS,")
print("  same CATCH->PASS direction, same repaired set => single shared mechanism (K9).")
