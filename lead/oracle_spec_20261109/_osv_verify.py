# -*- coding: utf-8 -*-
"""_osv_verify.py -- INDEPENDENT normative re-check for ORACLE spec reply.

READ-ONLY on everything outside lead/oracle_spec_20261109/. Writes only
_osv_verify_out.json into that write domain. No new seal, no modification of
any existing file, no commit/push, no process/memory access.

Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/oracle_spec_20261109/_osv_verify.py
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import importlib.util
import inspect
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "oracle_spec_20261109"

# Orchestrator baseline, copied verbatim from the ask's JSON block.
BASELINE = {
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

# Deliverables of the reply under review (for binding-line / boundary checks).
DELIVERABLES = {
    "_os_ORACLE_SPEC.md": 52542,
    "_os_audit.py": 11076,
    "_os_audit_out.json": 80300,
}

out = {"checks": {}}


def sha_bytes(p: Path):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b), b


# ---------------- 1. ten fingerprints, independent ---------------------------
fp = []
for rel, (h0, n0) in BASELINE.items():
    h, n, _ = sha_bytes(ROOT / rel)
    fp.append({"file": rel, "baseline_sha": h0, "computed_sha": h,
               "baseline_bytes": n0, "computed_bytes": n,
               "match": (h == h0 and n == n0)})
out["checks"]["fingerprints"] = {"n": len(fp), "all_match": all(x["match"] for x in fp),
                                 "rows": fp}

# ---------------- 2. _cr_seal.json structure / authors / signatures ----------
seal_p = ROOT / "lead/cert_realcheck_20261109/_cr_seal.json"
sh, sn, sb = sha_bytes(seal_p)
seal = json.loads(sb.decode("utf-8"))
items = seal["items"]
keysets = [sorted(it.keys()) for it in items]
oracles = [it["oracle"] for it in items]
# key-name scan over the entire JSON tree
allkeys = []
def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            allkeys.append(str(k)); walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(seal)
sigpat = re.compile(r"sign|sig_|signature|pki|pgp|gpg|x509|cert|pub.?key|priv.?key|"
                    r"rsa|ecdsa|ed25519|hmac|nonce|timestamp|tsa|rfc3161|notari|"
                    r"witness|merkle|non.?repud|签名|证书|时间戳|公证|不可否认", re.I)
key_hits = [k for k in allkeys if sigpat.search(k)]
raw_hits = [m.group(0) for m in sigpat.finditer(sb.decode("utf-8"))]
pgp = [m for m in ("-----BEGIN PGP SIGNATURE-----", "-----BEGIN PGP MESSAGE-----",
                   "-----BEGIN CERTIFICATE-----") if m.encode() in sb]
crdir = ROOT / "lead/cert_realcheck_20261109"
sidecars = sorted(p.name for p in crdir.iterdir() if p.is_file() and (
    p.suffix.lower() in {".sig", ".asc", ".pem", ".p7s", ".crt", ".pub"}
    or "sig" in p.name.lower() or "sign" in p.name.lower()))
# verify script's imports
vpy = (crdir / "_cr_real_verify.py").read_bytes().decode("utf-8")
imports = [ln.strip() for ln in vpy.splitlines()
           if re.match(r"^\s*(import|from)\s+", ln)]
out["checks"]["seal"] = {
    "sha256": sh, "bytes": sn,
    "top_keys": sorted(seal.keys()),
    "n_items": len(items),
    "item_keys_sorted": keysets[0],
    "all_item_keysets_identical": len({tuple(k) for k in keysets}) == 1,
    "oracle_subkeys_sorted": sorted(oracles[0].keys()),
    "all_oracle_authors": sorted({o["author"] for o in oracles}),
    "all_predicate_authors": sorted({o["predicate_author"] for o in oracles}),
    "all_oracle_truth": [o["truth"] for o in oracles],
    "sig_word_key_hits": key_hits, "sig_word_raw_hits": raw_hits,
    "pgp_markers": pgp, "sidecar_candidates": sidecars,
    "dir_file_count": len([p for p in crdir.iterdir() if p.is_file()]),
    "verify_py_imports": imports,
}
# mtime ordering (weak circumstantial evidence only)
mtime_files = [
    "lead/gate_r9sem_20261109/_r9s_predicates.py",
    "lead/gate_r9sem_20261109/_r9s_regress_out.json",
    "lead/falsifiable_no_relax_20261109/_fnr_check.py",
    "lead/cert_realcheck_20261109/_cr_build_seal.py",
    "lead/cert_realcheck_20261109/_cr_seal.json",
    "lead/cert_realcheck_20261109/_cr_real_verify.py",
]
import datetime
mt = {}
for rel in mtime_files:
    p = ROOT / rel
    mt[rel] = (datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat(sep=" ") if p.exists() else None)
out["checks"]["seal"]["mtimes"] = mt

# ---------------- 3. 302-item universe, own reproduction ---------------------
rp = ROOT / "lead/gate_r9sem_20261109/_r9s_regress_out.json"
rh, rn, rb = sha_bytes(rp)
r = json.loads(rb.decode("utf-8"))
d32 = r["domains32"]
rows = d32["rows"]
items302 = []
for row in rows:
    if row.get("main_missing"):
        continue
    for e in row["per_element"]:
        items302.append({"domain": row["domain"], "token": e["token"]})
pairs = [(i["domain"], i["token"]) for i in items302]
spec_keys = sorted(r["spec_inventory"].keys())
registered_occurrences = sum(1 for p in pairs if p[1] in set(spec_keys))
untested = len(pairs) - registered_occurrences
out["checks"]["universe302"] = {
    "path": "lead/gate_r9sem_20261109/_r9s_regress_out.json",
    "sha256": rh, "bytes": rn,
    "n_items": len(items302), "distinct_pairs": len(set(pairs)),
    "n_domains_rows": len(rows),
    "n_domains_declared": d32.get("n_domains"),
    "main_missing_count": sum(1 for x in rows if x.get("main_missing")),
    "n_flips": len(d32["flips"]), "n_whitelist": len(d32["whitelist"]),
    "spec_inventory_keys": spec_keys,
    "registered_token_occurrences": registered_occurrences,
    "structurally_untested": untested,
    "coverage_ratio": round(registered_occurrences / max(len(pairs), 1), 4),
    "sum_per_element": sum(len(x["per_element"]) for x in rows),
    "verdict": r.get("verdict"), "no_relaxation": r.get("no_relaxation"),
    "whitelist": d32["whitelist"],
    "seal_items": [it["item"] for it in items],
}

# ---------------- 4. C4 workload base: 32 main files, recompute -------------
mains = []
for row in rows:
    m = row.get("main")
    if m:
        mains.append((row.get("domain"), m))
# Path resolution: main may be relative to domain dir or already full path.
resolved = []
for dom, m in mains:
    cand = [ROOT / m, ROOT / dom / m, ROOT / "lead" / dom / m]
    hit = next((c for c in cand if c.is_file()), None)
    resolved.append((dom, m, hit))
missing = [(d, m) for d, m, h in resolved if h is None]
tot_bytes = tot_lines = tot_chars = 0
seen = set()
for d, m, h in resolved:
    if h is None or str(h) in seen:
        continue
    seen.add(str(h))
    b = h.read_bytes()
    tot_bytes += len(b)
    txt = b.decode("utf-8")
    tot_lines += len(txt.splitlines())
    tot_chars += len(txt)
n_distinct_main = len(seen)
out["checks"]["workload_base"] = {
    "n_rows_with_main": len(mains), "missing": missing,
    "distinct_main_files": n_distinct_main,
    "total_bytes": tot_bytes, "total_lines": tot_lines, "total_chars": tot_chars,
    "mean_bytes_per_item": round(tot_bytes / 302, 1),
    "chars_per_item_302": round(tot_chars / 302, 1),
    "n_distinct_tokens": len({p[1] for p in pairs}),
    "zero_per_element_domains": [x["domain"] for x in rows if len(x["per_element"]) == 0],
    "per_element_min": min(len(x["per_element"]) for x in rows),
    "per_element_max": max(len(x["per_element"]) for x in rows),
    "per_element_sum": sum(len(x["per_element"]) for x in rows),
}
# Workload arithmetic, recomputed from the base (not copied).
h400 = tot_chars / 400 / 60
h600 = tot_chars / 600 / 60
scen = {}
for mins in (3, 5, 8):
    per = 302 * mins / 60
    scen[f"{mins}min_per_item"] = {
        "per_rater_h": round(per, 2), "two_raters_h": round(per * 2, 2),
        "plus_adjud_6p04_plus_W_8": round(per * 2 + 6.04 + 8, 2),
        "chars_per_min_at_avg_1915": round((tot_chars / 302) / mins, 1),
    }
out["checks"]["workload_arithmetic"] = {
    "read_hours_at_400cpm": round(h400, 2),
    "read_hours_at_600cpm": round(h600, 2),
    "scenarios": scen,
    "disagree_15pct_items": round(302 * 0.15, 2),
    "adjudication_h_at_8min": round(round(302 * 0.15) * 8 / 60, 2),
    "two_raters_parallel_workdays_at_6h": {k: round(v["two_raters_h"] / 2 / 6, 2)
                                          for k, v in scen.items()},
}

# ---------------- 5. P5 signature TypeError, own importlib run ---------------
fnr = ROOT / "lead/falsifiable_no_relax_20261109/_fnr_check.py"
spec = importlib.util.spec_from_file_location("_osv_fnr", fnr)
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
    params = list(inspect.signature(mod.no_relaxation_check).parameters)
    errs = {}
    for kw in ("artifact_text", "seal_path"):
        try:
            mod.no_relaxation_check(**{kw: "x"})
            errs[kw] = "NO_ERROR"
        except TypeError as e:
            errs[kw] = str(e)
    out["checks"]["p5"] = {"no_relaxation_check_params": params, "typeerrors": errs}
except Exception as e:
    out["checks"]["p5"] = {"import_or_call_error": repr(e)}

# ---------------- 6. spec text audit: impossible-verify / declaration traps ---
spec_md = (WDIR / "_os_ORACLE_SPEC.md").read_bytes().decode("utf-8")
spec_lines = spec_md.splitlines()
checks_txt = {
    "binding_line_exact": None,
    "declares_no_proof_of_blind": [],
    "declares_institutional_assumption": [],
    "impossible_claims": [],
    "thresholds_marked_as_proposed_not_existing": [],
    "anti_patterns": [],
    "kappa_threshold_lines": [],
    "strongest_verdict_lines": [],
    "no_relaxation_not_judged_lines": [],
}
for i, ln in enumerate(spec_lines, 1):
    if "被核对象 SHA256" in ln:
        checks_txt["binding_line_exact"] = {"line": i, "text": ln}
    if any(w in ln for w in ("不可证明", "无法证成", "不可判定", "不可从产物判定", "零技术可查", "读没读过")):
        checks_txt["declares_no_proof_of_blind"].append({"line": i, "text": ln.strip()[:200]})
    if "制度性假设" in ln or "非技术可证事实" in ln or "靠信任" in ln or "只能靠制度" in ln:
        checks_txt["declares_institutional_assumption"].append({"line": i, "text": ln.strip()[:200]})
    if re.search(r"已证明(盲|独立异源|未见)|证明(了|已)?未见|技术上证明未见|可证明未见", ln):
        checks_txt["impossible_claims"].append({"line": i, "text": ln.strip()[:200]})
    if "建议阈值" in ln or "既无 κ 实测值" in ln or "项目内既无" in ln or "未计算任何 κ" in ln:
        checks_txt["thresholds_marked_as_proposed_not_existing"].append({"line": i, "text": ln.strip()[:200]})
    if "反模式" in ln or "明确不算判据" in ln or "不算判据" in ln:
        checks_txt["anti_patterns"].append({"line": i, "text": ln.strip()[:200]})
    if "0.80" in ln or "0.70" in ln or "0.90" in ln or "Cohen's κ" in ln or "κ≥" in ln:
        checks_txt["kappa_threshold_lines"].append({"line": i, "text": ln.strip()[:200]})
    if "INTEGRITY_OK_BUT_UNCONFIRMED" in ln:
        checks_txt["strongest_verdict_lines"].append({"line": i, "text": ln.strip()[:200]})
    if "判不了 `_fnr_check.py:78-91`" in ln or "不能判" in ln and "NO_RELAXATION" in ln:
        checks_txt["no_relaxation_not_judged_lines"].append({"line": i, "text": ln.strip()[:200]})
out["checks"]["spec_text"] = checks_txt
# binding-line format validation
bl = checks_txt["binding_line_exact"]
if bl:
    t = bl["text"]
    m = re.search(r"被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)", t)
    out["checks"]["spec_text"]["binding_line_valid"] = bool(m)
    if m:
        out["checks"]["spec_text"]["binding_line_sha"] = m.group(1)
        out["checks"]["spec_text"]["binding_line_bytes"] = int(m.group(2))
        out["checks"]["spec_text"]["binding_matches_seal"] = (m.group(1) == sh and int(m.group(2)) == sn)

# ---------------- 7. boundary: deliverables present + sizes; no new seal -----
dcheck = {}
for name, n0 in DELIVERABLES.items():
    h, n, _ = sha_bytes(WDIR / name)
    dcheck[name] = {"declared_bytes": n0, "computed_bytes": n, "match": n == n0, "sha256": h}
seal_like = sorted(p.name for p in WDIR.iterdir() if p.is_file() and (
    "seal" in p.name.lower() or p.suffix.lower() in {".sig", ".asc", ".pem", ".p7s", ".crt"}))
out["checks"]["boundary"] = {
    "deliverables": dcheck,
    "write_domain_file_list": sorted(p.name for p in WDIR.iterdir() if p.is_file()),
    "seal_like_files_in_write_domain": seal_like,
    "git_head": None,
}
# read-only dirs: count files and compute a digest over (name,size,mtime,sha) of
# the 10 baseline files to show they were untouched relative to baseline.
out["checks"]["boundary"]["all_10_baseline_match"] = all(x["match"] for x in fp)

# write output
WDIR.mkdir(parents=True, exist_ok=True)
blob = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
(WDIR / "_osv_verify_out.json").write_bytes(blob.encode("utf-8"))
print("WROTE _osv_verify_out.json bytes", len(blob.encode("utf-8")))
print("=== 1 FINGERPRINTS all_match =", out["checks"]["fingerprints"]["all_match"],
      "n =", out["checks"]["fingerprints"]["n"])
for x in fp:
    print("   ", "OK" if x["match"] else "MISMATCH", x["file"], x["computed_sha"], x["computed_bytes"])
s = out["checks"]["seal"]
print("=== 2 SEAL sha", s["sha256"], "bytes", s["bytes"])
for k in ("top_keys", "n_items", "oracle_subkeys_sorted", "all_oracle_authors",
          "all_predicate_authors", "all_oracle_truth", "sig_word_key_hits",
          "sig_word_raw_hits", "pgp_markers", "sidecar_candidates", "dir_file_count",
          "verify_py_imports"):
    print("   ", k, "=", json.dumps(s[k], ensure_ascii=False)[:400])
print("    mtimes =", json.dumps(s["mtimes"], ensure_ascii=False))
u = out["checks"]["universe302"]
print("=== 3 UNIVERSE", json.dumps(u, ensure_ascii=False, indent=1)[:1500])
w = out["checks"]["workload_base"]
print("=== 4 WORKLOAD BASE", json.dumps(w, ensure_ascii=False))
print("=== 4b WORKLOAD ARITH", json.dumps(out["checks"]["workload_arithmetic"], ensure_ascii=False))
print("=== 5 P5", json.dumps(out["checks"]["p5"], ensure_ascii=False))
t = out["checks"]["spec_text"]
print("=== 6 SPEC TEXT binding_line_valid =", t.get("binding_line_valid"),
      "binding_matches_seal =", t.get("binding_matches_seal"))
print("    impossible_claims =", json.dumps(t["impossible_claims"], ensure_ascii=False))
print("    declares_no_proof_of_blind n =", len(t["declares_no_proof_of_blind"]))
print("    declares_institutional_assumption n =", len(t["declares_institutional_assumption"]))
print("    thresholds_marked_as_proposed =", json.dumps(t["thresholds_marked_as_proposed_not_existing"], ensure_ascii=False)[:600])
print("    anti_patterns n =", len(t["anti_patterns"]))
print("    strongest_verdict_lines =", json.dumps(t["strongest_verdict_lines"], ensure_ascii=False)[:600])
print("=== 7 BOUNDARY", json.dumps(out["checks"]["boundary"], ensure_ascii=False)[:900])
