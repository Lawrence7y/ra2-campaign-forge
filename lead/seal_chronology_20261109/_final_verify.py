# -*- coding: utf-8 -*-
"""seal_chronology final independent verification (read-only on all protected dirs).
Run: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/seal_chronology_20261109/_final_verify.py"
Only writes its own output file inside lead/seal_chronology_20261109/.
"""
import hashlib
import json
import os
import pathlib
import re
import subprocess
import datetime

R = pathlib.Path("D:/Project/ra2-campaign-forge")
W = R / "lead" / "seal_chronology_20261109"

ORCH = {
    "lead/oracle_spec_20261109/_os_ORACLE_SPEC.md": ("5417fb06fc5ad7b6e2c520b9c83e3bb08c7a4a1bf65c339e1d0048bf695a2156", 52542),
    "lead/oracle_spec_20261109/_os_audit_out.json": ("c791716862caaa55974adfa1b206c4a4d098d092b11bdf60c99e5cb517ef8b7c", 80300),
    "lead/cert_realcheck_20261109/_cr_seal.json": ("63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23", 4395),
    "lead/cert_realcheck_20261109/_cr_real_verify.py": ("3d8ab1092ebf85efe3cc84e22c1eeb98b867a16f44d07cf877f1e2b4eb5c30fa", 21178),
    "lead/cert_realcheck_20261109/CERT_REAL_CHECK.md": ("fa3a45b7fd96ea8c3130a02227f6b6748bf4f196a5f714a51d3850e6d98ef014", 53782),
    "lead/falsifiable_no_relax_20261109/_fnr_check.py": ("94d89881f6a2e1afdea3ca78f56006ca27f1cabe1ec6384a9194718c327b00c2", 28811),
    "lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
    "lead/gate_r9sem_20261109/_r9s_regress_out.json": ("5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25", 75673),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

# 10 timing-data files from orchestrator
TIMING = [
    ("seal", "lead/cert_realcheck_20261109/_cr_seal.json", "2026-11-09 18:33:04", 1794220384, 4395),
    ("seal_builder", "lead/cert_realcheck_20261109/_cr_build_seal.py", "2026-11-09 18:33:00", 1794220380, 5376),
    ("real_verify", "lead/cert_realcheck_20261109/_cr_real_verify.py", "2026-11-09 18:34:15", 1794220455, 21178),
    ("V1_reg_out", "lead/gate_pipeline_20261109/_gp_regression_out.json", "2026-11-09 13:53:57", 1794203637, 38575),
    ("V1_reg_py", "lead/gate_pipeline_20261109/_gp_regression.py", "2026-11-09 12:52:54", 1794199974, 13017),
    ("V1_union_out", "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json", "2026-11-09 12:51:07", 1794199867, 37461),
    ("r9s_pred", "lead/gate_r9sem_20261109/_r9s_predicates.py", "2026-11-09 13:00:28", 1794200428, 23111),
    ("r9s_reg_out", "lead/gate_r9sem_20261109/_r9s_regress_out.json", "2026-11-09 14:32:26", 1794205946, 75673),
    ("fnr_check", "lead/falsifiable_no_relax_20261109/_fnr_check.py", "2026-11-09 16:11:22", 1794211882, 28811),
    ("wl_audit", "lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md", "2026-11-09 15:06:20", 1794207980, 52705),
]

# extra files the review flagged (whitelist source / CERTS predate V1)
EXTRA = [
    ("r9s_regress_py", "lead/gate_r9sem_20261109/_r9s_regress.py"),
    ("r9s_pred_py", "lead/gate_r9sem_20261109/_r9s_predicates.py"),
    ("cr_build_seal", "lead/cert_realcheck_20261109/_cr_build_seal.py"),
    ("crdoc_colocated_py", "lead/cert_realcheck_20261109/_crdoc_colocated.py"),
    ("crdoc_fake_seal", "lead/cert_realcheck_20261109/_crdoc_colocated_sandbox/_crdoc_fake_seal.json"),
]


def stat(rel):
    p = R / rel
    st = p.stat()
    blob = p.read_bytes()
    return {
        "mtime": st.st_mtime, "ctime": st.st_ctime, "atime": st.st_atime,
        "mtime_int": int(st.st_mtime), "size": st.st_size,
        "sha256": hashlib.sha256(blob).hexdigest(),
        "mtime_local": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "ctime_local": datetime.datetime.fromtimestamp(st.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
    }


out = {}

# ---- (1) 10 orchestrator fingerprints ----
orch = {}
all_ok = True
for rel, (sha, b) in ORCH.items():
    s = stat(rel)
    ok = (s["sha256"] == sha and s["size"] == b)
    all_ok &= ok
    orch[rel] = {"sha_match": s["sha256"] == sha, "bytes_match": s["size"] == b,
                 "sha256": s["sha256"], "bytes": s["size"]}
out["orch_all_ten_match"] = all_ok
out["orch_rows"] = orch

# ---- (2) 10 timing files: mtime/epoch/bytes reproduction + sha ----
tstat = {}
for tag, rel, mstr, epoch, b in TIMING:
    s = stat(rel)
    tstat[tag] = {
        "rel": rel, "mtime_local": s["mtime_local"], "mtime_int": s["mtime_int"],
        "mtime_float": s["mtime"], "ctime_float": s["ctime"],
        "ctime_local": datetime.datetime.fromtimestamp(s["ctime"]).strftime("%Y-%m-%d %H:%M:%S"),
        "bytes": s["size"], "sha256": s["sha256"],
        "epoch_match": s["mtime_int"] == epoch, "bytes_match": s["size"] == b,
        "mtime_str_match": s["mtime_local"] == mstr,
    }
out["timing"] = tstat
seal = tstat["seal"]
v1 = tstat["V1_reg_out"]
out["delta_seal_v1_int"] = seal["mtime_int"] - v1["mtime_int"]
out["delta_seal_v1_float"] = seal["mtime_float"] - v1["mtime_float"]
for tag in ("V1_reg_py", "V1_union_out", "r9s_pred", "r9s_reg_out", "fnr_check",
            "wl_audit", "seal_builder", "real_verify"):
    out["delta_seal_minus_" + tag + "_int"] = seal["mtime_int"] - tstat[tag]["mtime_int"]
    out["delta_seal_minus_" + tag + "_float"] = seal["mtime_float"] - tstat[tag]["mtime_float"]
out["seal_mtime_minus_ctime_float"] = seal["mtime_float"] - seal["ctime_float"]

# extra files mtime
extra = {}
for tag, rel in EXTRA:
    p = R / rel
    if p.is_file():
        s = stat(rel)
        extra[tag] = {"mtime_local": s["mtime_local"], "mtime_float": s["mtime"],
                      "ctime_local": s["ctime_local"], "bytes": s["size"],
                      "sha256": s["sha256"]}
    else:
        extra[tag] = {"missing": True}
out["extra"] = extra

# ---- (3) 5 vs 302 sets ----
reg = json.loads((R / "lead/gate_r9sem_20261109/_r9s_regress_out.json").read_text(encoding="utf-8"))
sealj = json.loads((R / "lead/cert_realcheck_20261109/_cr_seal.json").read_text(encoding="utf-8"))
d = reg["domains32"]
flips = frozenset((f["domain"], f["token"]) for f in d["flips"])
wl = frozenset(tuple(x) for x in d["whitelist"])
seal5 = frozenset(tuple(i["item"]) for i in sealj["items"])
spec_keys = frozenset(reg["spec_inventory"].keys())
items = []
for r in d["rows"]:
    if r.get("main_missing"):
        continue
    for e in r["per_element"]:
        items.append((r["domain"], e["token"]))
I = frozenset(items)
reg_tok_pairs = frozenset(x for x in items if x[1] in spec_keys)
out["sets"] = {
    "n_items": len(items), "distinct": len(I), "n_flips": len(flips),
    "n_whitelist": len(wl), "n_seal": len(seal5),
    "spec_inventory_keys": sorted(spec_keys),
    "seal_eq_flips": seal5 == flips, "seal_eq_whitelist": seal5 == wl,
    "flips_eq_whitelist": flips == wl, "seal_eq_spec_keys_tokens": frozenset(t for _, t in seal5) == spec_keys,
    "seal_subset_I": seal5 <= I,
    "coverage": len(seal5) / len(I), "missing": len(I) - len(seal5),
    "n_items_with_registered_token": len(reg_tok_pairs),
    "n_items_no_registered_token": len(items) - len(reg_tok_pairs),
    "seal_truth_all_true": all(i["oracle"]["truth"] is True for i in sealj["items"]),
    "n_truth_false": sum(1 for i in sealj["items"] if i["oracle"]["truth"] is not True),
    "seal_top_keys": list(sealj.keys()),
}
# registered token (domain,token) pairs among 302: count distinct tokens & pairs
from collections import Counter
out["sets"]["registered_pair_tokens"] = sorted(set(t for _, t in reg_tok_pairs))
out["sets"]["n_distinct_registered_pairs"] = len(reg_tok_pairs)

# ---- (4) binding line regex on the draft and on ORACLE_SPEC.md ----
pat = re.compile(r"被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)")
binding = {}
for nm, rel in [("draft", "lead/seal_chronology_20261109/_sc_SEAL_CHRONOLOGY.md"),
                ("ORACLE_SPEC", "lead/oracle_spec_20261109/ORACLE_SPEC.md")]:
    txt = (R / rel).read_text(encoding="utf-8")
    hits = pat.findall(txt)
    binding[nm] = {"n_hits": len(hits), "hits": hits,
                   "is64hex": all(len(h[0]) == 64 and re.fullmatch(r"[0-9a-f]{64}", h[0]) for h in hits)}
out["binding"] = binding
draft = (R / "lead/seal_chronology_20261109/_sc_SEAL_CHRONOLOGY.md").read_bytes()
out["draft_bytes"] = len(draft)
out["draft_sha256"] = hashlib.sha256(draft).hexdigest()

# ---- (5) git read-only checks ----
def git(*args):
    r = subprocess.run(["git", *args], cwd=str(R), capture_output=True, text=True)
    return r.stdout.strip()
out["git"] = {
    "head": git("log", "-1", "--format=%h %cI"),
    "reflog5": git("reflog", "-5", "--format=%h %cI %gs"),
    "lsfiles_6dirs": git("ls-files",
                         "lead/oracle_spec_20261109/", "lead/cert_realcheck_20261109/",
                         "lead/falsifiable_no_relax_20261109/", "lead/gate_pipeline_20261109/",
                         "lead/gate_r9sem_20261109/", "lead/whitelist_audit_20261109/"),
    "status_6dirs": git("status", "--porcelain", "--",
                        "lead/oracle_spec_20261109/", "lead/cert_realcheck_20261109/",
                        "lead/falsifiable_no_relax_20261109/", "lead/gate_pipeline_20261109/",
                        "lead/gate_r9sem_20261109/", "lead/whitelist_audit_20261109/"),
    "log_seal": git("log", "--format=%h %cI", "--", "lead/cert_realcheck_20261109/_cr_seal.json"),
}

# ---- (6) collect output ----
op = W / "_final_verify_out.json"
op.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

# concise console print
print("ORCH_ALL_TEN_MATCH =", out["orch_all_ten_match"])
print("TIMING_ALL_MATCH =", all(v["epoch_match"] and v["bytes_match"] and v["mtime_str_match"] for v in tstat.values()))
print("delta_seal_v1_int =", out["delta_seal_v1_int"], " float =", round(out["delta_seal_v1_float"], 6))
print("delta_seal_minus_real_verify_int =", out["delta_seal_minus_real_verify_int"], " float =", round(out["delta_seal_minus_real_verify_float"], 6))
print("seal_mtime_minus_ctime_float =", round(out["seal_mtime_minus_ctime_float"], 6))
for k in ("r9s_regress_py", "r9s_pred_py", "cr_build_seal", "crdoc_fake_seal"):
    print("EXTRA", k, extra.get(k))
s = out["sets"]
print("n_items =", s["n_items"], "distinct =", s["distinct"], "missing =", s["missing"], "coverage =", round(s["coverage"], 6))
print("seal_eq_flips =", s["seal_eq_flips"], "seal_eq_whitelist =", s["seal_eq_whitelist"], "flips_eq_whitelist =", s["flips_eq_whitelist"])
print("seal_eq_spec_keys_tokens =", s["seal_eq_spec_keys_tokens"], "spec_keys =", s["spec_inventory_keys"])
print("n_items_with_registered_token =", s["n_items_with_registered_token"], "n_items_no_registered_token =", s["n_items_no_registered_token"], "n_distinct_registered_pairs =", s["n_distinct_registered_pairs"])
print("BINDING draft =", binding["draft"], " ORACLE_SPEC =", binding["ORACLE_SPEC"])
print("draft bytes =", out["draft_bytes"], "sha =", out["draft_sha256"])
print("GIT head =", out["git"]["head"])
print("GIT ls-files 6dirs =", repr(out["git"]["lsfiles_6dirs"]))
print("WROTE", op)
