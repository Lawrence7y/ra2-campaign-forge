"""_sv_verify_skeleton.py — seal_v2 VERIFIER SKELETON. DESIGN ONLY; DO NOT EXECUTE.

Third-party verifier: needs ONLY
    (1) the seal file's raw bytes
    (2) the original covered files
    (3) the PUBLIC key / cert (whose fingerprint was published out-of-band at t0)
    (4) detached signature sidecar(s)
    (5) RFC3161 .tsq/.tsr + TSA CA chain, if a cryptographic time claim is made
NO local private key, NO local keyring, NO trust in the producer's filesystem.

Usage (when a real seal exists):
  python -I -X utf8 <abs path>/_sv_verify_skeleton.py \
      --seal <abs path>/_sv_seal_v2.json \
      --root <abs path of the repository root holding the covered files> \
      --published <abs path>/_sv_published.json \
      --pubkey <abs path to the PUBLIC key/cert> \
      --sig <abs path>/_sv_seal_v2.json.asc \
      [--tsq ... --tsr ... --ca ... --untrusted ...]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

CANON = dict(ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def H_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon_bytes(obj) -> bytes:
    return (json.dumps(obj, **CANON) + "\n").encode("utf-8")


def H(obj) -> str:
    return H_bytes(canon_bytes(obj))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seal", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--published", required=True)
    ap.add_argument("--pubkey", required=True)
    ap.add_argument("--sig", required=True)
    ap.add_argument("--gpg", default="D:/Git/usr/bin/gpg.exe")
    ap.add_argument("--openssl", default="D:/Anaconda/Library/bin/openssl.EXE")
    ap.add_argument("--tsq"); ap.add_argument("--tsr")
    ap.add_argument("--ca"); ap.add_argument("--untrusted")
    a = ap.parse_args()

    root = Path(a.root).resolve()
    seal_bytes = Path(a.seal).read_bytes()
    seal = json.loads(seal_bytes.decode("utf-8"))
    pub = json.loads(Path(a.published).read_text(encoding="utf-8"))

    problems: list[str] = []
    checks: dict[str, object] = {}

    # ---- C1. format / no self-reference ----
    if seal.get("seal_version") != "seal-v2":
        problems.append("SEAL_VERSION")
    flat = seal_bytes.decode("utf-8")
    self_hash = pub.get("seal_bytes_sha256", "")
    checks["no_self_reference"] = bool(self_hash) and (self_hash not in flat)
    if not checks["no_self_reference"]:
        problems.append("SEAL_CONTAINS_OWN_SHA256")

    # ---- C2. content binding: recompute every file with hashlib only ----
    items = seal.get("subject", {}).get("items", [])
    mismatches = []
    for it in items:
        p = (root / it["path"]).resolve()
        if not str(p).startswith(str(root)) or not p.is_file():
            mismatches.append((it["path"], "MISSING_OR_OUTSIDE_ROOT"))
            continue
        b = p.read_bytes()
        if H_bytes(b) != it["sha256"] or len(b) != it["bytes"]:
            mismatches.append((it["path"], "SHA_OR_BYTES"))
        if "evidence_span_sha256" in it and "evidence_lines" in it:
            lines = b.decode("utf-8", errors="replace").splitlines()
            lo, hi = it["evidence_lines"]
            span = ("\n".join(lines[lo - 1:hi]) + "\n").encode("utf-8")
            if H_bytes(span) != it["evidence_span_sha256"]:
                mismatches.append((it["path"], "EVIDENCE_SPAN"))
    checks["items_checked"] = len(items)
    checks["content_mismatches"] = mismatches
    if mismatches:
        problems.append("CONTENT_BINDING")

    recomputed_items_sha = H(items)
    checks["items_sha256_match"] = recomputed_items_sha == seal["subject"].get("items_sha256")
    if not checks["items_sha256_match"]:
        problems.append("ITEMS_SHA256")
    for_assertion = {k: v for k, v in seal.items() if k not in ("signers", "payload_sha256")}
    checks["payload_sha256_match"] = H(for_assertion) == seal.get("payload_sha256")
    if not checks["payload_sha256_match"]:
        problems.append("PAYLOAD_SHA256")

    # ---- C3. published 64-hex: third party recomputes from bytes received ----
    checks["published_seal_sha256_match"] = H_bytes(seal_bytes) == self_hash
    if not checks["published_seal_sha256_match"]:
        problems.append("PUBLISHED_SEAL_BYTES_MISMATCH")   # cf. _cr_real_verify.py:87-92

    # ---- C4. detached signature with PUBLIC key only (no local keyring) ----
    # Build a temporary isolated homedir so the verifier's own gpg state is
    # irrelevant: import exactly the supplied public key and verify.
    #   gpg --homedir <tmp> --batch --no-tty --import <pubkey>
    #   gpg --homedir <tmp> --batch --no-tty --verify <sig> <seal>
    # (spelled out with tempfile below; skeleton omits file creation for brevity
    #  of the design, but MUST be implemented before any real use)
    import tempfile
    with tempfile.TemporaryDirectory(prefix="_sv_verify_") as td:
        r1 = subprocess.run([a.gpg, "--homedir", td, "--batch", "--no-tty",
                             "--import", a.pubkey], capture_output=True, text=True)
        r2 = subprocess.run([a.gpg, "--homedir", td, "--batch", "--no-tty",
                             "--verify", a.sig, a.seal], capture_output=True, text=True)
        checks["pubkey_import_rc"] = r1.returncode
        checks["gpg_verify_rc"] = r2.returncode
        checks["gpg_verify_stderr"] = r2.stderr.strip()[:400]
    if checks["gpg_verify_rc"] != 0:
        problems.append("DETACHED_SIGNATURE_INVALID")

    # ---- C5. signature sidecar fingerprint / signer binding (T1/T6) ----
    sig_b = Path(a.sig).read_bytes()
    signers = seal.get("signers", [])
    checks["n_signers"] = len(signers)
    for s in signers:
        if s.get("key_generated_by_this_run") is not False:
            problems.append("KEY_GENERATED_BY_SEAL_BUILD")
        if s.get("public_key_sha256") != pub.get("public_key_sha256"):
            problems.append("SIGNER_KEY_NOT_THE_OUT_OF_BAND_TRUST_ANCHOR")
        if s.get("signature_sha256") not in ("PENDING", H_bytes(sig_b)):
            problems.append("SIGNATURE_SIDECAR_SHA256")
    if len(signers) < 1:
        problems.append("NO_SIGNER")

    # ---- C6. time anchors: >=2 different sources, >=1 outside A's write domain ----
    anchors = seal.get("time_anchors", [])
    kinds = {x.get("kind") for x in anchors}
    checks["time_anchor_kinds"] = sorted(kinds)
    checks["n_distinct_sources"] = len(kinds)
    checks["has_out_of_band_anchor"] = any(
        x.get("carrier_outside_A_write_domain") is True for x in anchors)
    if len(kinds) < 2:
        problems.append("TIME_ANCHORS_LT_2_DISTINCT_SOURCES")
    if not checks["has_out_of_band_anchor"]:
        problems.append("NO_CARRIER_OUTSIDE_A_WRITE_DOMAIN")   # T8
    # fs_stat must NEVER be promoted to an ordering proof on this host.
    prov = seal.get("provenance", {})
    if prov.get("fs_times_used_for_ordering") is not False:
        problems.append("FS_TIMES_USED_FOR_ORDERING")
    if prov.get("cognitive_independence_is_provable") is not False:
        problems.append("COGNITIVE_INDEPENDENCE_OVERCLAIM")

    # ---- C7. RFC3161: verify the token OFFLINE against the CA chain ----
    crypto_time = False
    if a.tsq and a.tsr and a.ca:
        cmd = [a.openssl, "ts", "-verify", "-queryfile", a.tsq, "-in", a.tsr,
               "-CAfile", a.ca]
        if a.untrusted:
            cmd += ["-untrusted", a.untrusted]
        r = subprocess.run(cmd, capture_output=True, text=True)
        checks["openssl_ts_verify_rc"] = r.returncode
        checks["openssl_ts_verify_out"] = (r.stdout + r.stderr).strip()[:400]
        if r.returncode == 0:
            # ALSO require: messageImprint in TSQ == sha256(seal_bytes)
            checks["tsq_imprint_equals_seal_bytes"] = (
                seal.get("time_anchors", [{}])[0].get("rfc3161", {}).get("imprint_sha256")
                == self_hash)
            crypto_time = bool(checks["tsq_imprint_equals_seal_bytes"])
        else:
            problems.append("TSA_TOKEN_INVALID")
    else:
        checks["openssl_ts_verify_rc"] = "NOT_RUN"
        problems.append("NO_RFC3161_TOKEN__TIME_IS_INSTITUTIONAL_ONLY")

    # ---- C8. t0 < t1 < t2 with BOTH endpoints independently anchored ----
    t2 = seal.get("predicate_run_anchor", {})
    checks["t2_produced_by_non_A_party"] = t2.get("produced_by_non_A_party") is True
    checks["commitment_published_before_predicate_run"] = (
        seal.get("commitment", {}).get("published_before_predicate_run") is True)
    if not checks["t2_produced_by_non_A_party"]:
        problems.append("V1_FIRST_RUN_ANCHOR_NOT_INDEPENDENT")   # the easy-to-miss one
    if not checks["commitment_published_before_predicate_run"]:
        problems.append("T0_PUBLISHED_AFTER_V1")
    # String/ISO comparison is a design placeholder; with real TSA genTime values
    # parse to aware datetimes and require strictly increasing t0<t1<t2.
    checks["t0_lt_t1_lt_t2"] = "NOT_EVALUATED"                    # honest default
    problems.append("T0_T1_T2_NOT_EVALUATED_WITHOUT_TWO_TSA_GENTIMES")

    # ---- C9. honest accounting: unverified claims must stay visible ----
    unver = prov.get("unverified", [])
    checks["unverified_claims"] = unver
    inst = prov.get("institutional_only_claims", [])
    required_inst = {"adjudicator_did_not_see_V1_outputs", "key_to_person_mapping"}
    checks["institutional_claims_declared"] = required_inst.issubset(set(inst))
    if not checks["institutional_claims_declared"]:
        problems.append("COGNITIVE_INDEPENDENCE_NOT_DECLARED_AS_INSTITUTIONAL")

    checks["cryptographic_time_claim_allowed"] = crypto_time
    result = "FAIL" if problems else "PASS"
    out = {"verdict": result, "problems": problems, "checks": checks,
           "note": "PASS means only the enumerated technical checks passed. It NEVER means blind/independent labelling was proven (ORACLE_SPEC.md:123/:161/:163)."}
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
