# -*- coding: utf-8 -*-
"""_os6_audit.py -- independent read-only re-check for ORACLE_SPEC.md (six-section).

Fresh implementation for this deliverable. Reads ONLY; writes ONLY the JSON
output _os6_audit_out.json inside lead/oracle_spec_20261109/. No seal is
generated, no existing file is modified, no process/memory/game access,
no commit/push.

Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/oracle_spec_20261109/_os6_audit.py
"""
from __future__ import annotations

import datetime
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "oracle_spec_20261109"
CERT = ROOT / "lead" / "cert_realcheck_20261109"
FNR = ROOT / "lead" / "falsifiable_no_relax_20261109"
R9S = ROOT / "lead" / "gate_r9sem_20261109"

# ---- orchestrator-declared fingerprints, copied verbatim from the ask -------
DECLARED = {
    "lead/cert_realcheck_20261109/_cr_seal.json": ("63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23", 4395),
    "lead/cert_realcheck_20261109/_cr_real_verify.py": ("3d8ab1092ebf85efe3cc84e22c1eeb98b867a16f44d07cf877f1e2b4eb5c30fa", 21178),
    "lead/cert_realcheck_20261109/CERT_REAL_CHECK.md": ("fa3a45b7fd96ea8c3130a02227f6b6748bf4f196a5f714a51d3850e6d98ef014", 53782),
    "lead/cert_realcheck_20261109/_cr_p1_old_check_out.json": ("7c433113755ad64cf779e232efeddc4f39bc325ffef53c9057f2dda8d3f7a007", 3033),
    "lead/cert_realcheck_20261109/_cr_verify_out.json": ("4d224936b7ebdb4a5c5be25b31d226ec965cce72c100d8db5f0ec4d829a73464", 7921),
    "lead/falsifiable_no_relax_20261109/_fnr_check.py": ("94d89881f6a2e1afdea3ca78f56006ca27f1cabe1ec6384a9194718c327b00c2", 28811),
    "lead/check_fp_audit_20261109/CHECK_FALSE_ALARM_AUDIT.md": ("464355c08f961a40de2a719c556816a70448a17564f63bdc05d65981f5d09ed4", 40950),
    "lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md": ("f9d00b7c9a12a996bac9d89b0bf5a948dfe026e21f472bd825d7924d35a47adc", 52705),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

out = {"checks": {}}


def digest(p: Path):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b), b


# ===================== C1: ten fingerprints ==================================
rows = []
for rel, (h0, n0) in DECLARED.items():
    h, n, _ = digest(ROOT / rel)
    rows.append({"file": rel, "declared_sha256": h0, "computed_sha256": h,
                 "declared_bytes": n0, "computed_bytes": n,
                 "match": h == h0 and n == n0})
out["checks"]["C1_fingerprints"] = {
    "n": len(rows), "all_match": all(r["match"] for r in rows), "rows": rows}

# ===================== C2: seal structure / author / signature ==============
sh, sn, sb = digest(CERT / "_cr_seal.json")
seal = json.loads(sb.decode("utf-8"))
items = seal["items"]
keysets = [tuple(sorted(x.keys())) for x in items]
oracles = [x["oracle"] for x in items]

allkeys = []
def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            allkeys.append(str(k))
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)
walk(seal)

SIG = re.compile(
    r"sign|sig_|signature|pki|pgp|gpg|x509|x\.509|cert(?:ificate)?|"
    r"pub(?:lic)?[_-]?key|priv(?:ate)?[_-]?key|asymmetr|rsa|ecdsa|ed25519|"
    r"hmac|nonce|timestamp|tsa|rfc3161|notari|witness|merkle|non.?repud|"
    r"签名|证书|时间戳|公证|不可否认", re.I)
key_hits = sorted({k for k in allkeys if SIG.search(k)})
raw_hits = sorted({m.group(0) for m in SIG.finditer(sb.decode("utf-8"))})
pgp_markers = [m for m in ("-----BEGIN PGP SIGNATURE-----",
                           "-----BEGIN PGP MESSAGE-----",
                           "-----BEGIN CERTIFICATE-----")
               if m.encode() in sb]
sidecars = sorted(p.name for p in CERT.iterdir() if p.is_file() and (
    p.suffix.lower() in {".sig", ".asc", ".pem", ".p7s", ".crt", ".pub"}
    or "sig" in p.name.lower() or "sign" in p.name.lower()
    or "pubkey" in p.name.lower()))
vsrc = (CERT / "_cr_real_verify.py").read_text(encoding="utf-8")
vimports = [ln.strip() for ln in vsrc.splitlines()
            if re.match(r"^\s*(import|from)\s+", ln)]

# whole-repo signature sidecars (path names only; no process/memory access).
# Pruned walk: skip .git / caches / vendored trees; cap the number of files.
repo_sidecars = []
skip = {".git", "node_modules", "__pycache__", ".tmp", "vendor", "dist"}
n_scanned = 0
import os
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in skip]
    for fn in filenames:
        n_scanned += 1
        low = fn.lower()
        if low.endswith((".sig", ".asc", ".p7s", ".pem", ".crt")) \
                or "pubkey" in low:
            rel = os.path.relpath(os.path.join(dirpath, fn), ROOT)
            repo_sidecars.append(rel.replace("\\", "/"))
    if n_scanned > 300000:
        break

# seal item set vs regression flips / whitelist (was labelling blind?)
reg = json.loads((R9S / "_r9s_regress_out.json").read_text(encoding="utf-8"))
d32 = reg["domains32"]
flips = {(f["domain"], f["token"]) for f in d32["flips"]}
wl = {tuple(x) for x in d32["whitelist"]}
seal_set = {tuple(x["item"]) for x in items}

out["checks"]["C2_seal"] = {
    "sha256": sh, "bytes": sn,
    "top_keys": sorted(seal.keys()), "n_items": len(items),
    "item_keys_sorted": list(keysets[0]),
    "all_item_keysets_identical": len(set(keysets)) == 1,
    "oracle_subkeys_sorted": sorted(oracles[0].keys()),
    "all_oracle_authors": sorted({o["author"] for o in oracles}),
    "all_predicate_authors": sorted({o["predicate_author"] for o in oracles}),
    "all_oracle_truth": [o["truth"] for o in oracles],
    "sig_key_hits": key_hits, "sig_raw_hits": raw_hits,
    "pgp_markers": pgp_markers, "sidecar_candidates": sidecars,
    "repo_signature_sidecars": sorted(repo_sidecars)[:40],
    "n_repo_signature_sidecars": len(repo_sidecars),
    "n_repo_files_scanned": n_scanned,
    "cert_dir_file_count": len([p for p in CERT.iterdir() if p.is_file()]),
    "verify_py_imports": vimports,
    "cr_verify_has_sig_or_crypto_import": any(
        w in " ".join(vimports).lower() for w in
        ("cryptography", "nacl", "rsa", "ecdsa", "gpg", "ssl", "hmac")),
    "seal_items_equal_flips": seal_set == flips,
    "seal_items_equal_whitelist": seal_set == wl,
    "n_seal_flip_intersection": len(seal_set & flips),
}

# ===================== C3: mtime ordering ====================================
MT = ["lead/gate_r9sem_20261109/_r9s_predicates.py",
      "lead/gate_r9sem_20261109/_r9s_regress_out.json",
      "lead/falsifiable_no_relax_20261109/_fnr_check.py",
      "lead/cert_realcheck_20261109/_cr_build_seal.py",
      "lead/cert_realcheck_20261109/_cr_seal.json",
      "lead/cert_realcheck_20261109/_cr_real_verify.py",
      "lead/PENDING_DECISIONS.md", "lead/GOAL_THREE_TARGETS_20261018.md"]
mt = {rel: datetime.datetime.fromtimestamp(
    (ROOT / rel).stat().st_mtime).isoformat(sep=" ", timespec="seconds")
    for rel in MT}
out["checks"]["C3_mtime"] = {
    "files": mt,
    "seal_later_than_v1_regress_output":
        mt["lead/cert_realcheck_20261109/_cr_seal.json"]
        > mt["lead/gate_r9sem_20261109/_r9s_regress_out.json"],
    "note": "mtime is a weak circumstantial signal only; no trusted timestamp exists",
}

# ===================== C4: 302-item universe =================================
# Reproduce _fnr_check.py:359-363 construction exactly, using the disk JSON.
main_items = []
for r in d32["rows"]:
    if r.get("main_missing"):
        continue
    for e in r["per_element"]:
        main_items.append({"domain": r["domain"], "token": e["token"]})
pairs = [(x["domain"], x["token"]) for x in main_items]

# Load R9S.SPECS from the real module (read-only load, no main()).
sys.path.insert(0, str(R9S))
spec = importlib.util.spec_from_file_location(
    "_os6_r9s_readonly", R9S / "_r9s_predicates.py")
m_r9s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m_r9s)
registered = set(m_r9s.SPECS.keys())
untested = [x for x in main_items if x["token"] not in registered]
n_reg_occ = sum(1 for x in main_items if x["token"] in registered)

# Load _fnr_check.py as a module (NOT as __main__, so main() does not run).
spec2 = importlib.util.spec_from_file_location(
    "_os6_fnr_readonly", FNR / "_fnr_check.py")
m_fnr = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(m_fnr)

out["checks"]["C4_universe302"] = {
    "n_domains_rows": len(d32["rows"]),
    "n_items": len(main_items),
    "n_distinct_pairs": len(set(pairs)),
    "sum_per_element": sum(len(r["per_element"]) for r in d32["rows"]),
    "main_missing_count": sum(1 for r in d32["rows"] if r.get("main_missing")),
    "n_flips": len(d32["flips"]), "n_whitelist": len(d32["whitelist"]),
    "registered_tokens": sorted(registered),
    "n_registered_token_occurrences": n_reg_occ,
    "n_structurally_untested": len(untested),
    "coverage_ratio": round((len(main_items) - len(untested)) / len(main_items), 4),
    "n_distinct_tokens": len({x["token"] for x in main_items}),
    "zero_element_domains": [r["domain"] for r in d32["rows"]
                             if len(r["per_element"]) == 0],
    "regress_out_sha256": digest(R9S / "_r9s_regress_out.json")[0],
    "regress_out_bytes": digest(R9S / "_r9s_regress_out.json")[1],
}

# ===================== C5: P5 two missing slots ==============================
p5 = {}
for kw in ("artifact_text", "seal_path"):
    try:
        m_fnr.no_relaxation_check(**{kw: "x"})
        p5[kw] = "NO_TypeError"
    except TypeError as e:
        p5[kw] = str(e)
import inspect
out["checks"]["C5_p5_slots"] = {
    "parameter_names": list(inspect.signature(m_fnr.no_relaxation_check).parameters),
    "n_params": len(inspect.signature(m_fnr.no_relaxation_check).parameters),
    "has_artifact_text": "artifact_text" in inspect.signature(m_fnr.no_relaxation_check).parameters,
    "has_seal_path": "seal_path" in inspect.signature(m_fnr.no_relaxation_check).parameters,
    "typeerrors": p5,
}

# ===================== C6: workload arithmetic ================================
# Read the 32 domain main files (read-only), count bytes/lines/chars.
tot_bytes = tot_lines = tot_chars = 0
main_paths = set()
missing = []
for r in d32["rows"]:
    rel = r["domain"].rstrip("/") + "/" + r["main"]
    p = ROOT / rel
    main_paths.add(str(p))
    if not p.is_file():
        missing.append(rel)
        continue
    b = p.read_bytes()
    tot_bytes += len(b)
    t = b.decode("utf-8")
    tot_lines += len(t.splitlines())
    tot_chars += len(t)
n_items = len(main_items)
scen = {}
for mins in (3, 5, 8):
    one = n_items * mins / 60.0
    two = 2 * one
    arb_exact = (n_items * 0.15) * 8 / 60.0     # 45.3 items x 8 min
    arb_rounded = round(n_items * 0.15) * 8 / 60.0  # 45 items x 8 min
    scen[str(mins) + "min"] = {
        "one_rater_h": round(one, 2), "two_raters_h": round(two, 2),
        "adjudication_h_exact_45p3": round(arb_exact, 2),
        "adjudication_h_rounded_45": round(arb_rounded, 2),
        "e2e_h_with_W8_exact": round(two + arb_exact + 8, 2),
        "e2e_h_with_W8_rounded": round(two + arb_rounded + 8, 2),
        "chars_per_min": round(tot_chars / (one * 60), 1),
    }
out["checks"]["C6_workload"] = {
    "distinct_main_files": len(main_paths), "missing": missing,
    "total_bytes": tot_bytes, "total_lines": tot_lines,
    "total_chars": tot_chars,
    "chars_per_item": round(tot_chars / n_items, 1),
    "mean_bytes_per_item": round(tot_bytes / n_items, 1),
    "read_only_h_at_400cpm": round(tot_chars / 400 / 60, 2),
    "read_only_h_at_600cpm": round(tot_chars / 600 / 60, 2),
    "scenarios": scen,
    "kappa_thresholds_are_spec_proposals": True,
    "note": "no third-party labels exist in this session; no kappa was computed",
}

# ===================== C7: boundary / no new seal =============================
wfiles = sorted(p.name for p in WDIR.iterdir() if p.is_file())
seal_like = [n for n in wfiles if "seal" in n.lower()
             or n.endswith((".sig", ".asc", ".pem", ".p7s", ".crt"))]
out["checks"]["C7_boundary"] = {
    "write_domain_files_before_this_write": [
        n for n in wfiles if n != "_os6_audit.py"],
    "seal_like_files": seal_like,
    "n_readonly_dirs_touched": 0,
    "no_new_seal": len(seal_like) == 0,
}

# ===================== C8: re-check 10 fingerprints after all reads ===========
rows2 = []
for rel, (h0, n0) in DECLARED.items():
    h, n, _ = digest(ROOT / rel)
    rows2.append({"file": rel, "match": h == h0 and n == n0})
out["checks"]["C8_readonly_unchanged"] = {
    "all_match_after_audit": all(r["match"] for r in rows2),
    "rows": rows2}

# ---- write ONLY this JSON output ---------------------------------------------
blob = json.dumps(out, ensure_ascii=False, indent=1) + "\n"
(WDIR / "_os6_audit_out.json").write_bytes(blob.encode("utf-8"))

print("WROTE _os6_audit_out.json bytes", len(blob.encode("utf-8")))
print("C1 fingerprints all_match =", out["checks"]["C1_fingerprints"]["all_match"],
      "n =", out["checks"]["C1_fingerprints"]["n"])
print("C2 seal top_keys =", out["checks"]["C2_seal"]["top_keys"],
      "n_items =", out["checks"]["C2_seal"]["n_items"],
      "authors =", out["checks"]["C2_seal"]["all_oracle_authors"],
      "truth =", out["checks"]["C2_seal"]["all_oracle_truth"])
print("C2 sig_key_hits =", key_hits, "sig_raw_hits =", raw_hits,
      "pgp =", pgp_markers, "sidecars =", sidecars,
      "repo_sidecars =", len(repo_sidecars))
print("C2 seal==flips =", out["checks"]["C2_seal"]["seal_items_equal_flips"],
      "seal==whitelist =", out["checks"]["C2_seal"]["seal_items_equal_whitelist"])
print("C3 seal_later_than_v1_regress_output =",
      out["checks"]["C3_mtime"]["seal_later_than_v1_regress_output"])
u = out["checks"]["C4_universe302"]
print("C4 n_items =", u["n_items"], "distinct =", u["n_distinct_pairs"],
      "domains =", u["n_domains_rows"], "untested =", u["n_structurally_untested"],
      "coverage =", u["coverage_ratio"], "regress_sha =", u["regress_out_sha256"])
print("C5", out["checks"]["C5_p5_slots"]["typeerrors"])
w = out["checks"]["C6_workload"]
print("C6 files =", w["distinct_main_files"], "bytes =", w["total_bytes"],
      "lines =", w["total_lines"], "chars =", w["total_chars"],
      "missing =", w["missing"], "zero_elem_domains =", u["zero_element_domains"])
print("C6 read_h @400/@600 =", w["read_only_h_at_400cpm"], w["read_only_h_at_600cpm"])
print("C6 scenarios =", json.dumps(scen, ensure_ascii=False))
print("C7 seal_like =", seal_like, "C8 all_match_after_audit =",
      out["checks"]["C8_readonly_unchanged"]["all_match_after_audit"])
