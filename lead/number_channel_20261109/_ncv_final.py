# -*- coding: utf-8 -*-
"""_ncv_final.py -- 终态定点复核：绝对行号分类、ask 数组数、哈希链自洽、指纹终态。"""
import hashlib
import importlib.util
import io
import json
import os

ROOT = r"D:\Project\ra2-campaign-forge"
D = os.path.join(ROOT, "lead", "number_channel_20261109")


def load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(D, fname))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ncph = load("ncphf", "_nc_placeholder.py")
ncl = load("nclf", "_nc_lint.py")
out = {}


def lowered(path):
    for l in io.open(path, "r", encoding="utf-8").read().split("\n"):
        if l.startswith("export const payload"):
            return json.loads(l[len("export const payload = "):].rstrip().rstrip(";"))["lowered"].split("\n")


for tag, fname, keys in (
    ("89df", "dwfrun-89df48db-a7c0-4905-85b8-68da3f294695.mjs",
     [107, 108, 110, 122, 124]),
    ("8682", "dwfrun-868215ce-ea87-4e41-a54b-5a0af3c441dd.mjs",
     [94, 95, 98, 110, 131, 132, 170, 217, 226]),
):
    L = lowered(os.path.join(ROOT, ".zcode", "workflow-runs", fname))
    s = next(i for i, x in enumerate(L) if "const ASK_ANALYST = [" in x)
    e = next(i for i in range(s + 1, len(L)) if "].join" in L[i])
    block = L[s + 1:e]
    # block[0] 对应 1-based lowered 行 (s+2)；classify_lines 的 lineno=1 对应 block[0]
    abs_of = lambda lineno: s + 1 + lineno
    cls = ncl.classify_lines("\n".join(block))
    inv = {}
    for k in ("prose", "machine", "quoted", "code"):
        for ln, _ in cls[k]:
            inv[abs_of(ln)] = k
    out["abs_class_" + tag] = {
        "ask_block_lowered_range": [s + 2, e],
        "n_lines": len(block),
        "counts": {k: len(v) for k, v in cls.items()},
        "key_abs_lines": {str(a): inv.get(a, "OUTSIDE_FIRST_ASK_BLOCK") for a in keys},
        "n_join_arrays_in_whole_lowered": sum(1 for x in L if "].join" in x),
        "publishArtifact_lines": [i + 1 for i, x in enumerate(L) if "publishArtifact" in x],
        "conclusion_lines": [i + 1 for i, x in enumerate(L) if "conclusion:" in x],
    }

# ---- 哈希链自洽（save_source 的 source_block_sha256 vs block_sha256） ----
TMP = os.path.join(D, "_ncv_chain_tmp.json")
try:
    store = {"version": 0, "prev_sha256": "", "history": [],
             "claims": [dict(c) for c in ncph._demo_claims()]}
    st = ncph.save_source(TMP, store)
    per = [c.get("source_block_sha256") for c in st["claims"]]
    out["chain_selfconsistency"] = {
        "block_sha256": st["block_sha256"],
        "distinct_source_block_sha256": sorted(set(map(str, per))),
        "per_claim_equals_block": all(x == st["block_sha256"] for x in per),
        "prev_sha256": st["prev_sha256"],
        "note": "save_source 先把 block=A 写入每条，再以含 A 的 claims 重算 block=B，故每条 source_block_sha256 恒 ≠ 最终 block_sha256",
    }
    # check_chain 不校验 history / prev 连续性
    st2 = json.load(io.open(TMP, "r", encoding="utf-8"))
    st2["history"] = []          # 抹掉纠正留证
    st2["prev_sha256"] = "0" * 64  # 断链
    tb = ncph.taskbook_header(st2) + '\n"【背景】{{N.domains_nonempty}}。"\n'
    out["chain_selfconsistency"]["check_chain_after_tamper"] = ncph.check_chain(tb, st2)
finally:
    if os.path.exists(TMP):
        os.remove(TMP)

# ---- 终态指纹（9 件 + 主交付件） ----
files = [
    ("main_deliverable", "lead/number_channel_20261109/NUMBER_CHANNEL_FIX.md",
     "abea556f11a3452b1a71c813012e0ac6f8b5bae559db511132e12d05001549ec", 50607),
    ("ORCH_CLAIMS_AUDIT.md", "lead/orch_claims_20261109/ORCH_CLAIMS_AUDIT.md",
     "9ebc406831a3fa402cf7006240b2b6c1314fed344dd1aa0c2a06f89b072140e4", 53432),
    ("_oc_stats_out.json", "lead/orch_claims_20261109/_oc_stats_out.json",
     "1f7aba12c7ab21e6c27eac491e790d2ed4bf7423cae2a9df9e35e545228b7834", 1127),
    ("_oc_recompute_out.json", "lead/orch_claims_20261109/_oc_recompute_out.json",
     "541af3380dec0657c79f6d39999feaaa5d6e90d6fab34d8ce014844961370439", 1336),
    ("METRIC_CONVENTION_AUDIT.md", "lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md",
     "f737d8a52b51ded87e2f20cd1368f73b4cf3fb7331c34384b0d4b802caf9c503", 45362),
    ("KEFF_CALC.md", "lead/keff_calc_20261109/KEFF_CALC.md",
     "4ad16cdb7dbb4b9e97ea306b55af6d51e2c262a52b10c75e56e1f5ffa1126e16", 34964),
    ("_pv_PVALUE_RECALC.md", "lead/pvalue_recalc_20261109/_pv_PVALUE_RECALC.md",
     "277df9910d4611e0072faf83bd65e3639667a01b511191d5f74b575e448911ac", 29780),
    ("SCORE_DECOMP.md", "lead/score_decomp_20261109/SCORE_DECOMP.md",
     "dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb", 42573),
    ("PENDING_DECISIONS.md", "lead/PENDING_DECISIONS.md",
     "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("GOAL_THREE_TARGETS_20261018.md", "lead/GOAL_THREE_TARGETS_20261018.md",
     "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]
rows = []
for name, rel, want_h, want_b in files:
    b = io.open(os.path.join(ROOT, rel.replace("/", os.sep)), "rb").read()
    h = hashlib.sha256(b).hexdigest()
    rows.append({"name": name, "sha256": h, "bytes": len(b),
                 "match_baseline": h == want_h and len(b) == want_b})
out["final_fingerprints"] = {"n_match": sum(1 for r in rows if r["match_baseline"]),
                             "n": len(rows), "rows": rows}

print(json.dumps(out, ensure_ascii=False, indent=2))
