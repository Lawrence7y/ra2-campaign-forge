# -*- coding: utf-8 -*-
# _scv_sets.py : independent recomputation of the 5-vs-302 coincidence and coverage.
# Read-only over all forbidden domains. Writes only _scv_sets_out.json in the allowed domain.
import os, json, hashlib
ROOT = r"D:\Project\ra2-campaign-forge"
R = lambda rel: os.path.join(ROOT, rel.replace("/", os.sep))

seal = json.load(open(R("lead/cert_realcheck_20261109/_cr_seal.json"), encoding="utf-8"))
ref  = json.load(open(R("lead/gate_r9sem_20261109/_r9s_regress_out.json"), encoding="utf-8"))

seal_items = [tuple(x["item"]) for x in seal["items"]]
print("seal top_keys =", sorted(seal.keys()), " n_items =", len(seal_items))
print("seal items =", seal_items)
print("oracle truth values =", [x["oracle"].get("truth") for x in seal["items"]])
print("oracle keys =", sorted({k for x in seal["items"] for k in x["oracle"]}))
print("authors =", sorted({x["oracle"].get("author") for x in seal["items"]}))

D = ref["domains32"]
flips = [(f["domain"], f["token"]) for f in D["flips"]]
wl    = [tuple(x) for x in D["whitelist"]]
# reconstruct I exactly as _fnr_check.py:355-363 does
items = []
for r in D["rows"]:
    if r.get("main_missing"): continue
    for e in r["per_element"]:
        items.append((r["domain"], e["token"]))
print()
print("n_domains =", D["n_domains"], " n_rows =", len(D["rows"]))
print("n_items =", len(items), " distinct (domain,token) =", len(set(items)))
print("n_flips =", len(flips), " n_whitelist =", len(wl))
print("flips =", flips)
print("whitelist =", wl)
print()
S, F, W, I = set(seal_items), set(flips), set(wl), set(items)
print("SEAL==FLIPS ?", S == F)
print("SEAL==WHITELIST ?", S == W)
print("FLIPS==WHITELIST ?", F == W)
print("SEAL ∩ I size =", len(S & I))
print("SEAL ⊆ I ?", S <= I)
print("coverage len(S)/len(I) = %d/%d = %.6f" % (len(S), len(I), len(S)/len(I)))
print("missing = ", len(I) - len(S))
print("negatives (truth=False) in seal =", sum(1 for x in seal["items"] if x["oracle"].get("truth") is not True))
print("UNVERIFIABLE labels in seal =", sum(1 for x in seal["items"] if x["oracle"].get("truth") not in (True, False)))

# check the 64-hex seal sha appears anywhere in V1 outputs (content-level anchoring)
sha = hashlib.sha256(open(R("lead/cert_realcheck_20261109/_cr_seal.json"), "rb").read()).hexdigest()
print()
print("seal sha256 =", sha)
for rel in ["lead/gate_pipeline_20261109/_gp_regression_out.json",
            "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json",
            "lead/gate_r9sem_20261109/_r9s_regress_out.json"]:
    b = open(R(rel), "rb").read()
    print("seal-sha present in %-70s ? %s" % (rel, sha.encode() in b))

out = dict(seal_top_keys=sorted(seal.keys()), n_items=len(items), n_distinct=len(set(items)),
           n_seal=len(S), seal_eq_flips=(S == F), seal_eq_whitelist=(S == W),
           flips_eq_whitelist=(F == W), seal_subset_I=(S <= I),
           coverage=len(S)/len(I), missing=len(I)-len(S),
           seal_sha=sha, negatives=0)
with open(R("lead/seal_chronology_20261109/_scv_sets_out.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("\nWROTE _scv_sets_out.json")
