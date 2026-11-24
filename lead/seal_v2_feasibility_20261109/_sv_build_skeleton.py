"""_sv_build_skeleton.py — seal_v2 GENERATOR SKELETON. DESIGN ONLY; DO NOT EXECUTE.

Discipline honoured by design:
  * never writes to any read-only domain; writes ONLY inside the declared OUT dir
  * never generates a key, never installs a tool, never commits/pushes
  * never launches a game/loader, never samples memory
  * network steps are OPT-IN and gated on --allow-network (approval required);
    by default NO bytes leave the machine
  * a seal instance is NOT created in the feasibility task; this is a skeleton

Usage (when the owning team approves an actual seal):
  python -I -X utf8 <abs path>/_sv_build_skeleton.py \
      --root D:/Project/ra2-campaign-forge \
      --out  D:/Project/ra2-campaign-forge/lead/<approved_write_domain> \
      --manifest <abs path>/manifest.json \
      --public-key-fpr <64hex> \
      --signer-id <adjudicator_id> \
      --allow-network            # only after approval to POST a digest
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CANON = dict(ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def H_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon_bytes(obj) -> bytes:
    return (json.dumps(obj, **CANON) + "\n").encode("utf-8")


def H(obj) -> str:
    return H_bytes(canon_bytes(obj))


def sha256_file(p: Path) -> tuple[str, int]:
    b = p.read_bytes()                       # read-only
    return H_bytes(b), len(b)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--manifest", required=True, help="JSON: {items:[{path,anchor,evidence_lines}], predecessor_seal, input_manifest_sha256, pre_registration_sha256, carrier, t1_labels_sha256, t2:[...]}")
    ap.add_argument("--public-key-fpr", required=True, help="64hex of the PUBLIC key/cert; trust anchor published out-of-band at t0")
    ap.add_argument("--signer-id", required=True)
    ap.add_argument("--gpg", default="D:/Git/usr/bin/gpg.exe")
    ap.add_argument("--openssl", default="D:/Anaconda/Library/bin/openssl.EXE")
    ap.add_argument("--tsa-url", default="https://freetsa.org/tsr")
    ap.add_argument("--allow-network", action="store_true", help="approval required; sends ONLY the seal digest, never repo content")
    a = ap.parse_args()

    root, out = Path(a.root).resolve(), Path(a.out).resolve()
    if not out.is_dir() or not str(out).replace("\\", "/").startswith(str(root).replace("\\", "/")):
        print("ABORT: --out must be an existing dir under --root", file=sys.stderr)
        return 2
    manifest = json.loads(Path(a.manifest).read_text(encoding="utf-8"))

    # ---- 1. content binding: recompute every covered file's sha256/bytes ----
    items = []
    for spec in manifest["items"]:
        rel = spec["path"]
        p = (root / rel).resolve()
        if not p.is_file() or not str(p).startswith(str(root)):
            print(f"ABORT: missing/outside-root {rel}", file=sys.stderr)
            return 2
        h, n = sha256_file(p)
        rec = {"path": rel, "sha256": h, "bytes": n, "anchor": spec["anchor"],
               "output_manifest_sha256": manifest["input_manifest_sha256"]}
        if "evidence_lines" in spec:
            rec["evidence_lines"] = spec["evidence_lines"]
            # evidence_span_sha256: hash of the exact certified line slice, UTF-8
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            lo, hi = spec["evidence_lines"]
            span = "\n".join(lines[lo - 1:hi]) + "\n"
            rec["evidence_span_sha256"] = H_bytes(span.encode("utf-8"))
        items.append(rec)

    subject = {"items": items, "items_sha256": H(items),
               "predecessor_seal_sha256": manifest.get("predecessor_seal")}

    # ---- 2. time anchors: fs_stat (WEAK) + at least one out-of-band carrier ----
    fs_anchor = {"kind": "fs_stat", "trust": "weak_local_metadata",
                 "carrier_outside_A_write_domain": False,
                 "observed_at_utc": now_utc(),
                 "fs": {"st_ctime": None, "st_mtime": None, "st_atime": None,
                        "writable": True,
                        "note": "Windows st_ctime = creation time; mtime>ctime is normal after overwrite. NEVER use for ordering."}}
    # fill from stat AFTER the seal file is written (see step 5); placeholder here.
    anchors = [fs_anchor]

    unverified: list[str] = []

    # ---- 3. optional RFC3161 (NETWORK, opt-in, approval required) ----
    # NOTE: the TSQ imprint must equal sha256(SEAL FILE RAW BYTES), so this step
    # can only run AFTER step 5 writes the seal. Kept here as a two-phase design:
    #   phase A: build seal with time_anchors=[fs_stat], write seal bytes
    #   phase B: ts -query -digest sha256(seal_bytes) -> POST -> ts -reply -text
    #   phase C: append the rfc3161 anchor, REWRITE seal, RE-SIGN (signature must
    #            cover the FINAL bytes). The published 64-hex is of the FINAL file.
    if a.allow_network:
        unverified.append("rfc3161 POST/inclusion proof executed by phase B/C below")
    else:
        unverified.append("rfc3161 POST not executed (no --allow-network); t0<t2 is INSTITUTIONAL ONLY")
        anchors.append({"kind": "witness_archive", "trust": "institutional_only",
                        "carrier_outside_A_write_domain": True,
                        "observed_at_utc": now_utc(),
                        "witness_archive": {
                            "locator": manifest["carrier"],
                            "witness_ids": manifest.get("witness_ids", []),
                            "receipt_sha256": manifest.get("receipt_sha256", "0" * 64)}})

    # ---- 4. assemble payload (NO self hash, NO signature inside) ----
    payload = {
        "seal_version": "seal-v2",
        "subject": subject,
        "time_anchors": anchors,
        "commitment": {
            "t0_pre_registration_sha256": manifest["pre_registration_sha256"],
            "carrier": manifest["carrier"],
            "published_before_predicate_run": bool(manifest.get("published_before_predicate_run", False)),
            "t1_labels_sha256": manifest.get("t1_labels_sha256"),
            # seal_bytes_sha256 is filled in the PUBLISHED sidecar, NOT in the seal,
            # to avoid a self-referential hash.
        },
        "predicate_run_anchor": {
            "produced_by_non_A_party": bool(manifest.get("t2_produced_by_non_A_party", False)),
            "source": manifest.get("t2_source", "unknown"),
            "observed_at_utc": manifest.get("t2_observed_at_utc", "UNVERIFIED"),
            "evidence_sha256": manifest.get("t2_evidence_sha256"),
            "note": "Independent t2 is REQUIRED; a local mtime for V1's first run leaves one writable endpoint."
        },
        "signers": [{
            "adjudicator_id": a.signer_id,
            "shard_ids": manifest.get("shard_ids", []),
            "mechanism": "gpg_detached",
            "public_key_sha256": a.public_key_fpr,
            "signature_sha256": "PENDING",   # filled after signing
            "signature_path": None,
            "key_generated_by_this_run": False,
        }],
        "provenance": {
            "cryptographic_claims": ["content_integrity", "key_binding", "non_malleability_after_signature"],
            "institutional_only_claims": [
                "adjudicator_did_not_see_V1_outputs", "key_to_person_mapping",
                "carrier_write_acl_excludes_A", "no_collusion_between_W_and_A"],
            "unverified": unverified,
            "cognitive_independence_is_provable": False,
            "fs_times_used_for_ordering": False,
        },
    }
    for_assertion = {k: v for k, v in payload.items() if k not in ("signers",)}
    payload["payload_sha256"] = H(for_assertion)

    # ---- 5. write seal bytes (ONLY inside --out), then fill fs stat ----
    seal_path = out / "_sv_seal_v2.json"
    b = canon_bytes(payload)
    seal_path.write_bytes(b)
    st = seal_path.stat()
    fs_anchor["fs"].update({"st_ctime": st.st_ctime, "st_mtime": st.st_mtime,
                            "st_atime": st.st_atime})
    # NOTE: canonical bytes changed once fs fields were filled; rewrite deterministically.
    b = canon_bytes(payload)
    seal_path.write_bytes(b)

    # ---- 6. detached signature (key MUST already exist; NEVER generate one) ----
    # Abort rather than create a key: this is the discipline boundary.
    chk = subprocess.run([a.gpg, "--batch", "--no-tty", "--list-secret-keys",
                          "--with-colons", a.public_key_fpr], capture_output=True, text=True)
    if chk.returncode != 0 or not any(l.startswith("sec:") for l in chk.stdout.splitlines()):
        print("ABORT: no provisioned secret key; key generation is out of scope", file=sys.stderr)
        return 3
    sig_path = out / "_sv_seal_v2.json.asc"
    r = subprocess.run([a.gpg, "--batch", "--yes", "--no-tty", "--armor", "--detach-sign",
                        "--local-user", a.public_key_fpr, "--output", str(sig_path),
                        "--", str(seal_path)], capture_output=True, text=True)
    if r.returncode != 0:
        print("ABORT: signing failed", r.stderr, file=sys.stderr)
        return 4
    sb = sig_path.read_bytes()

    # ---- 7. PUBLISHED sidecar (NOT part of the signed seal bytes) ----
    # 64-hex any third party can recompute from the bytes received, no key needed.
    published = {
        "seal_bytes_sha256": H_bytes(seal_path.read_bytes()),
        "seal_bytes": len(seal_path.read_bytes()),
        "signature_sha256": H_bytes(sb),
        "public_key_sha256": a.public_key_fpr,
        "carrier": manifest["carrier"],
        "published_at_utc": now_utc(),
        "warning": "This sidecar is NOT inside the signed seal. Publishing after V1 proves only 'unchanged from now on' (ORDERING_EVIDENCE.md:165)."
    }
    (out / "_sv_published.json").write_bytes(canon_bytes(published))

    # ---- 8. optional phase B/C: TSA over sha256(seal_bytes) ----
    # Only with --allow-network. Sends a DIGEST, never repository bytes.
    #   openssl ts -query -sha256 -cert -digest <published.seal_bytes_sha256> -out req.tsq
    #   curl -sS -H 'Content-Type: application/timestamp-query' --data-binary @req.tsq
    #        <tsa_url> -o resp.tsr
    #   openssl ts -reply -in resp.tsr -text
    #   openssl ts -verify -queryfile req.tsq -in resp.tsr -CAfile cacert.pem
    #        -untrusted tsa.crt
    # On success: append an rfc3161 anchor, rewrite the seal, RE-SIGN, and
    # RE-PUBLISH the sidecar with the FINAL sha256. Mark provenance.unverified
    # accordingly. All of this is DESIGN ONLY in this task.

    print("seal_path   =", seal_path)
    print("signature   =", sig_path)
    print("published   =", out / "_sv_published.json")
    print("seal_sha256 =", published["seal_bytes_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
