# -*- coding: utf-8 -*-
"""_oev_verify.py -- INDEPENDENT re-verification of the ordering-evidence reply.

Read-only over all forbidden domains.  Writes only _oev_out.json in the
allowed write domain.  Absolutely no seal generation, no editing of any
existing artifact, no game processes, no sampling/hook code.

Run: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/ordering_evidence_20261109/_oev_verify.py"
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import platform
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "ordering_evidence_20261109"
TZ8 = timezone(timedelta(hours=8))


def R(rel: str) -> Path:
    return ROOT / rel.replace("/", os.sep)


def sha_bytes(rel: str):
    b = R(rel).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def local(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, TZ8).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


OUT: dict = {"python": sys.version.split()[0], "platform": platform.platform(),
             "root": str(ROOT)}

# ---------------------------------------------------------------------------
# (1) EIGHT FINGERPRINTS -- recomputed independently, compared to the
#     orchestrator baseline that was handed to me in the ask.
# ---------------------------------------------------------------------------
BASELINE = {
    "lead/seal_chronology_20261109/_sc_SEAL_CHRONOLOGY.md": ("5af2b304a71ec4c13bea14d1034ef0de12d306a62f769a41bec3891c6392cc5f", 45423),
    "lead/seal_chronology_20261109/_sc_probe_out.json": ("09548c9ad258270fc7dbf80150437e868e45c6b8f5220214cbfd8aa20b1ec6d7", 9590),
    "lead/seal_chronology_20261109/_sc_ctime.py": ("e49151caef129b8925fcb02bcd23c36060cd411102e05350bad7839b8d769657", 1126),
    "lead/oracle_spec_20261109/_os_ORACLE_SPEC.md": ("5417fb06fc5ad7b6e2c520b9c83e3bb08c7a4a1bf65c339e1d0048bf695a2156", 52542),
    "lead/cert_realcheck_20261109/_cr_seal.json": ("63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23", 4395),
    "lead/cert_realcheck_20261109/_cr_build_seal.py": ("2e539d392b0aca54cb8cd2c83bd20e1d87ba9ce5cbc8f15ea5ea279ef0b86574", 5376),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
fp = {}
for rel, (h0, n0) in BASELINE.items():
    h, n = sha_bytes(rel)
    fp[rel] = {"sha256": h, "bytes": n, "expected_sha": h0, "expected_bytes": n0,
               "match": (h == h0 and n == n0)}
OUT["fingerprints"] = fp
OUT["fingerprints_all_match"] = all(v["match"] for v in fp.values())
OUT["n_fingerprints"] = len(fp)

# ---------------------------------------------------------------------------
# (2) ctime ANOMALY -- independent os.stat, plus a LIBRARY-WIDE scan to judge
#     whether "mtime > ctime" is anomalous on this platform at all.
# ---------------------------------------------------------------------------
STAT_RELS = [
    "lead/cert_realcheck_20261109/_cr_seal.json",
    "lead/cert_realcheck_20261109/_cr_build_seal.py",
    "lead/cert_realcheck_20261109/_cr_real_verify.py",
    "lead/gate_pipeline_20261109/_gp_regression_out.json",
    "lead/gate_pipeline_20261109/_gp_regression.py",
    "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json",
    "lead/gate_r9sem_20261109/_r9s_predicates.py",
    "lead/gate_r9sem_20261109/_r9s_regress.py",
    "lead/gate_r9sem_20261109/_r9s_regress_out.json",
]
stat_rows = {}
for rel in STAT_RELS:
    st = os.stat(R(rel))
    stat_rows[rel] = {"mtime": st.st_mtime, "ctime": st.st_ctime,
                      "atime": st.st_atime, "size": st.st_size,
                      "mtime_local": local(st.st_mtime),
                      "ctime_local": local(st.st_ctime),
                      "atime_local": local(st.st_atime),
                      "mtime_minus_ctime": st.st_mtime - st.st_ctime}
OUT["stat_rows"] = stat_rows

seal_st = stat_rows["lead/cert_realcheck_20261109/_cr_seal.json"]
bld_st = stat_rows["lead/cert_realcheck_20261109/_cr_build_seal.py"]
OUT["ctime_anomaly"] = {
    "seal_mtime_minus_ctime_float": seal_st["mtime"] - seal_st["ctime"],
    "builder_mtime_minus_seal_ctime_float": bld_st["mtime"] - seal_st["ctime"],
    "builder_mtime_minus_seal_ctime_int": int(bld_st["mtime"]) - int(seal_st["ctime"]),
    "seal_ctime_local": seal_st["ctime_local"],
    "seal_mtime_local": seal_st["mtime_local"],
    "builder_mtime_local": bld_st["mtime_local"],
    "builder_ctime_local": bld_st["ctime_local"],
}
# deltas seal - X (integer + float), independent recomputation
OUT["deltas_seal_minus"] = {
    rel: {"int": int(seal_st["mtime"]) - int(v["mtime"]),
          "float": seal_st["mtime"] - v["mtime"]}
    for rel, v in stat_rows.items()
}

# library-wide: how many files under lead/ also have mtime > ctime by >60s?
scan_total = 0
scan_gt60 = 0
scan_gt300 = 0
scan_examples = []
for dirpath, dirnames, filenames in os.walk(ROOT / "lead"):
    for fn in filenames:
        p = Path(dirpath) / fn
        try:
            st = p.stat()
        except OSError:
            continue
        scan_total += 1
        d = st.st_mtime - st.st_ctime
        if d > 60:
            scan_gt60 += 1
            if d > 300:
                scan_gt300 += 1
            if len(scan_examples) < 12:
                scan_examples.append({"rel": str(p.relative_to(ROOT)).replace("\\", "/"),
                                      "mtime_minus_ctime_s": round(d, 3),
                                      "mtime": local(st.st_mtime),
                                      "ctime": local(st.st_ctime)})
OUT["library_wide_ctime_scan"] = {
    "root": "lead/", "n_files_scanned": scan_total,
    "n_files_mtime_minus_ctime_gt_60s": scan_gt60,
    "n_files_mtime_minus_ctime_gt_300s": scan_gt300,
    "examples": scan_examples,
}

# ---------------------------------------------------------------------------
# (3) SETS / TRIPLE EQUALITY / COMBINATORICS -- recomputed from disk,
#     with the construction chain parsed by AST (no import, no execution).
# ---------------------------------------------------------------------------
seal = json.loads(R("lead/cert_realcheck_20261109/_cr_seal.json").read_text(encoding="utf-8"))
ref = json.loads(R("lead/gate_r9sem_20261109/_r9s_regress_out.json").read_text(encoding="utf-8"))
D = ref["domains32"]

seal_items = [tuple(x["item"]) for x in seal["items"]]
flips = [(f["domain"], f["token"]) for f in D["flips"]]
whitelist_from_output = [tuple(x) for x in D["whitelist"]]
items_I = []
for r in D["rows"]:
    if r.get("main_missing"):
        continue
    for e in r["per_element"]:
        items_I.append((r["domain"], e["token"]))

S, F, W, I = set(seal_items), set(flips), set(whitelist_from_output), set(items_I)
C_N_k = math.comb(len(I), 5)
p_pair = 1.0 / C_N_k
p_3way = 1.0 / (C_N_k ** 2)
C_reg = math.comb(10, 5)
OUT["combinatorics"] = {
    "N": len(I), "n_distinct_I": len(I), "k": 5,
    "C_N_k": C_N_k,
    "p_pair_match_if_independent": p_pair,
    "p_3way_exact_if_independent": p_3way,
    "log10_C": math.log10(C_N_k),
    "C_registered_pairs": 10, "comb_registered_5": C_reg,
    "p_3way_if_pool_is_registered": 1.0 / (C_reg ** 2),
    "p_pair_if_pool_is_registered": 1.0 / C_reg,
}

# AST-extract the three hard-coded structures from source (no import).
def module_assign(src: str, name: str):
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return node.value
    raise KeyError(name)


pred_src = R("lead/gate_r9sem_20261109/_r9s_predicates.py").read_text(encoding="utf-8")
reg_src = R("lead/gate_r9sem_20261109/_r9s_regress.py").read_text(encoding="utf-8")
build_src = R("lead/cert_realcheck_20261109/_cr_build_seal.py").read_text(encoding="utf-8")
fnr_src = R("lead/falsifiable_no_relax_20261109/_fnr_check.py").read_text(encoding="utf-8")

SPECS_node = module_assign(pred_src, "SPECS")
spec_keys = set(ast.literal_eval(k) for k in SPECS_node.keys)
WL_node = module_assign(reg_src, "WHITELIST")
whitelist_src = set(tuple(x) for x in ast.literal_eval(WL_node))
ITEMS_node = module_assign(build_src, "ITEMS")
items_src = [tuple(x["item"]) for x in ast.literal_eval(ITEMS_node)]
CERTS_node = module_assign(fnr_src, "CERTS")
certs_src = set(tuple(k) for k in ast.literal_eval(CERTS_node).keys())

seal_tokens = set(t for _, t in seal_items)
OUT["triple_equality"] = {
    "n_seal_items": len(S), "n_flips": len(F), "n_whitelist_output": len(W),
    "n_SPECS_keys": len(spec_keys), "n_ITEMS_in_builder": len(items_src),
    "n_CERTS_keys": len(certs_src),
    "seal_eq_flips": S == F,
    "seal_eq_whitelist_output": S == W,
    "flips_eq_whitelist_output": F == W,
    "whitelist_source_eq_whitelist_output": whitelist_src == W,
    "whitelist_source_eq_seal": whitelist_src == S,
    "ITEMS_source_eq_seal": set(items_src) == S,
    "CERTS_source_eq_seal": certs_src == S,
    "seal_tokens_eq_SPECS_keys": seal_tokens == spec_keys,
    "flips_tokens_eq_SPECS_keys": set(t for _, t in flips) == spec_keys,
    "seal_subset_I": S <= I,
    "coverage": len(S) / len(I), "missing": len(I) - len(S),
    "n_items_with_registered_token": sum(1 for _, t in items_I if t in spec_keys),
    "n_distinct_registered_pairs": len({(d, t) for d, t in items_I if t in spec_keys}),
    "n_items_no_registered_token": sum(1 for _, t in items_I if t not in spec_keys),
    "spec_keys_sorted": sorted(spec_keys),
    "seal_items_sorted": [list(x) for x in sorted(S)],
    "flips_sorted": [list(x) for x in sorted(F)],
    "whitelist_sorted": [list(x) for x in sorted(W)],
    "truth_all_true": all(x["oracle"].get("truth") is True for x in seal["items"]),
    "n_negatives": sum(1 for x in seal["items"] if x["oracle"].get("truth") is not True),
    "seal_top_keys": sorted(seal.keys()),
}

# construction-mechanism evidence: read the exact source fragments that make
# flips a deterministic subset of SPECS keys (not a random draw).
OUT["construction_mechanism"] = {
    "r9s_element_present_uses_SPECS_get": "SPECS.get(token)" in ast.get_source_segment(
        pred_src, next(n for n in ast.parse(pred_src).body
                       if isinstance(n, ast.FunctionDef) and n.name == "r9s_element_present")),
    "r9s_element_present_unregistered_returns_False": "token 未登记语义要素规格" in pred_src,
    "regress_flip_condition": "if (not ok0) and ok1:" in reg_src,
    "regress_whitelist_is_hardcoded_set": isinstance(WL_node, ast.Set),
    "regress_whitelist_comment": [l.strip() for l in reg_src.splitlines()[110:113]],
    "SPECS_is_closed_dict": isinstance(SPECS_node, ast.Dict),
    "ITEMS_is_literal_list": isinstance(ITEMS_node, ast.List),
    "flips_tokens_subset_SPECS_keys": set(t for _, t in flips) <= spec_keys,
    "flips_all_whitelisted": all(f["whitelisted"] for f in D["flips"]),
    "flips_outside_whitelist": D["flips_outside_whitelist"],
    "n_tightens": D["n_tightens"],
    "no_relaxation_field": ref.get("no_relaxation"),
}

# seal sha in V1 outputs (content-anchoring direction test)
seal_sha, seal_bytes = sha_bytes("lead/cert_realcheck_20261109/_cr_seal.json")
V1 = ["lead/gate_pipeline_20261109/_gp_regression_out.json",
      "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json",
      "lead/gate_r9sem_20261109/_r9s_regress_out.json",
      "lead/gate_pipeline_20261109/_gp_regression_out.txt",
      "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.txt"]
v1_hits = {}
for rel in V1:
    p = R(rel)
    if p.exists():
        b = p.read_bytes()
        v1_hits[rel] = {"seal_full_sha_present": seal_sha.encode() in b,
                        "seal_prefix16_present": seal_sha[:16].encode() in b,
                        "bytes": len(b)}
OUT["seal_self_sha_in_V1"] = {"seal_sha": seal_sha, "seal_bytes": seal_bytes,
                              "results": v1_hits,
                              "any_full_hit": any(v["seal_full_sha_present"] for v in v1_hits.values())}

# reverse direction: do the 5 file_sha256 of the seal appear in r9s_regress_out?
reg_out_bytes = R("lead/gate_r9sem_20261109/_r9s_regress_out.json").read_bytes()
OUT["seal_file_hashes_in_r9s_regress_out"] = {
    x["item"][1]: (x["file_sha256"].encode() in reg_out_bytes) for x in seal["items"]
}

# verifier constant
rv = R("lead/cert_realcheck_20261109/_cr_real_verify.py").read_text(encoding="utf-8")
OUT["verifier_constant"] = {
    "seal_sha_literal_in_source": seal_sha in rv,
    "bytes_literal_in_source": ("EXPECTED_SEAL_BYTES = %d" % seal_bytes) in rv,
}

# ---------------------------------------------------------------------------
# (4) BINDING LINE in the reviewed object (strict format + equals disk)
# ---------------------------------------------------------------------------
md = R("lead/ordering_evidence_20261109/_oe_ORDERING_EVIDENCE.md").read_text(encoding="utf-8")
strict = re.compile(r"^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$", re.M)
hits = strict.findall(md)
OUT["binding_line"] = {
    "n_strict_hits": len(hits),
    "hashes": [h for h, _ in hits],
    "equals_disk_seal_sha": all(h == seal_sha for h, _ in hits),
    "equals_disk_seal_bytes": all(int(n) == seal_bytes for _, n in hits),
    "md_bytes": len(md.encode("utf-8")),
    "any_nonconforming_binding_token": len(re.findall(r"被核对象 SHA256\s*=", md)) - len(hits),
}

# ---------------------------------------------------------------------------
# (5) BOUNDARY CHECK: files in write domain, no new seal, sig sidecars
# ---------------------------------------------------------------------------
wd_files = sorted(p.name for p in WDIR.iterdir() if p.is_file())
OUT["write_domain_files"] = wd_files
OUT["write_domain_all_oe_or_oev"] = all(n.startswith("_oe_") or n.startswith("_oev_") for n in wd_files)
# any seal-like json anywhere under lead/ with mtime >= 2026-11-09 21:00 local?
cutoff = datetime(2026, 11, 9, 21, 0, 0, tzinfo=TZ8).timestamp()
new_seals = []
for dirpath, dirnames, filenames in os.walk(ROOT / "lead"):
    for fn in filenames:
        if "seal" in fn.lower() and fn.lower().endswith((".json", ".txt", ".md")):
            p = Path(dirpath) / fn
            try:
                st = p.stat()
            except OSError:
                continue
            if st.st_mtime >= cutoff:
                new_seals.append({"rel": str(p.relative_to(ROOT)).replace("\\", "/"),
                                  "mtime": local(st.st_mtime), "bytes": st.st_size})
OUT["recent_seal_named_files_since_2100"] = new_seals
sig_pat = re.compile(r"\.(sig|asc|p7s|pem|crt)$|_pubkey", re.I)
sigs = [str(p.relative_to(ROOT)).replace("\\", "/")
        for p in (ROOT / "lead" / "cert_realcheck_20261109").iterdir()
        if p.is_file() and sig_pat.search(p.name)]
OUT["signature_sidecars_in_cert_dir"] = sigs

# ---------------------------------------------------------------------------
with (WDIR / "_oev_out.json").open("w", encoding="utf-8") as f:
    json.dump(OUT, f, ensure_ascii=False, indent=2)

print("=== _oev_verify.py INDEPENDENT RESULTS ===")
print("python/platform:", OUT["python"], OUT["platform"])
print("FINGERPRINTS 8/8 MATCH =", OUT["fingerprints_all_match"])
for rel, v in fp.items():
    print("  %-72s %s  sha=%s bytes=%d" % (rel, "OK" if v["match"] else "MISMATCH",
                                            v["sha256"][:16], v["bytes"]))
print("\nCTIME_ANOMALY:", json.dumps(OUT["ctime_anomaly"], ensure_ascii=False, indent=1))
print("LIBRARY_WIDE_CTIME_SCAN:", json.dumps(OUT["library_wide_ctime_scan"], ensure_ascii=False, indent=1))
print("\nDELTAS seal-minus:", json.dumps({k.split("/")[-1]: v for k, v in OUT["deltas_seal_minus"].items()},
                                         ensure_ascii=False, indent=1))
print("\nCOMBINATORICS:", json.dumps(OUT["combinatorics"], ensure_ascii=False, indent=1))
print("\nTRIPLE_EQUALITY:", json.dumps(OUT["triple_equality"], ensure_ascii=False, indent=1))
print("\nCONSTRUCTION_MECHANISM:", json.dumps(OUT["construction_mechanism"], ensure_ascii=False, indent=1))
print("\nSELF_SHA_IN_V1:", json.dumps(OUT["seal_self_sha_in_V1"], ensure_ascii=False, indent=1))
print("SEAL_FILE_HASHES_IN_REG_OUT:", json.dumps(OUT["seal_file_hashes_in_r9s_regress_out"], ensure_ascii=False, indent=1))
print("VERIFIER_CONSTANT:", json.dumps(OUT["verifier_constant"], ensure_ascii=False))
print("\nBINDING_LINE:", json.dumps(OUT["binding_line"], ensure_ascii=False, indent=1))
print("\nWRITE_DOMAIN:", json.dumps(OUT["write_domain_files"], ensure_ascii=False))
print("ALL_OE_OR_OEV:", OUT["write_domain_all_oe_or_oev"])
print("RECENT_SEAL_NAMED_FILES:", json.dumps(new_seals, ensure_ascii=False))
print("SIG_SIDECARS:", json.dumps(sigs, ensure_ascii=False))
print("\nWROTE _oev_out.json")
