# -*- coding: utf-8 -*-
"""_os_audit.py -- independent, READ-ONLY re-verification for the ORACLE spec task.

Checks:
  1. Recompute hashlib sha256 + byte counts for the orchestrator's declared
     fingerprint list; compare with the values pasted into the ask.
  2. Independent structural analysis of _cr_seal.json (top keys, per-item
     keys, oracle keys/values, signature/PKI hunt).
  3. Independent accounting of the 302-item universe in _r9s_regress_out.json.
  4. Independent scan of relevant read-only sources for P5 slots / signatures.

Writes ONLY JSON into lead/oracle_spec_20261109/. No other file is modified.
Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/oracle_spec_20261109/_os_audit.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "oracle_spec_20261109"

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

SIG_WORDS = re.compile(
    r"sign|sig_|signature|pki|pgp|gpg|x509|x\.509|cert(?:ificate)?|"
    r"pub(?:lic)?[_-]?key|priv(?:ate)?[_-]?key|asymmetr|rsa|ecdsa|ed25519|"
    r"hmac|mac_|nonce|timestamp|tsa|rfc3161|notari|witness|merkle|"
    r"unforgeab|nonrepudi|non-repudi|不可否认|签名|证书|时间戳|公证|不可伪造",
    re.I,
)


def sha(p: Path) -> tuple[str, int]:
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def walk_keys(obj, path="$"):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.append((path + "." + str(k), str(k), v))
            out.extend(walk_keys(v, path + "." + str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(walk_keys(v, path + "[%d]" % i))
    return out


def main():
    report = {"fingerprints": [], "seal": {}, "universe302": {}, "p5": {}}

    # ---- 1. independent fingerprint re-verification -------------------------
    for rel, (decl_h, decl_n) in DECLARED.items():
        p = ROOT / rel
        h, n = sha(p)
        report["fingerprints"].append({
            "file": rel, "declared_sha256": decl_h, "computed_sha256": h,
            "declared_bytes": decl_n, "computed_bytes": n,
            "match": (h == decl_h and n == decl_n),
        })

    # ---- 2. seal structure / authors / signature hunt -----------------------
    seal_p = ROOT / "lead/cert_realcheck_20261109/_cr_seal.json"
    seal_b = seal_p.read_bytes()
    seal = json.loads(seal_b.decode("utf-8"))
    s = report["seal"]
    s["path"] = "lead/cert_realcheck_20261109/_cr_seal.json"
    s["sha256"], s["bytes"] = sha(seal_p)
    s["top_keys"] = sorted(seal.keys())
    s["n_items"] = len(seal["items"])
    s["item_keys_sorted"] = sorted(seal["items"][0].keys())
    s["per_item_keys"] = [sorted(it.keys()) for it in seal["items"]]
    s["all_item_keysets_identical"] = len({tuple(x) for x in s["per_item_keys"]}) == 1
    s["oracle_subkeys_sorted"] = sorted(seal["items"][0]["oracle"].keys())
    s["all_oracle_subkeysets"] = [sorted(it["oracle"].keys()) for it in seal["items"]]
    s["all_oracle_authors"] = sorted({it["oracle"]["author"] for it in seal["items"]})
    s["all_predicate_authors"] = sorted({it["oracle"]["predicate_author"] for it in seal["items"]})
    s["all_oracle_truth"] = [it["oracle"]["truth"] for it in seal["items"]]
    s["all_oracle_truth_types"] = sorted({type(it["oracle"]["truth"]).__name__ for it in seal["items"]})
    s["item_ids"] = [it["item"] for it in seal["items"]]
    s["anchors"] = [it["anchor"] for it in seal["items"]]
    # signature-shaped keys anywhere in the JSON tree
    s["sig_word_key_hits"] = [
        {"path": path, "key": k, "value_repr": repr(v)[:160]}
        for path, k, v in walk_keys(seal)
        if SIG_WORDS.search(str(k))
    ]
    # signature-shaped words anywhere in the raw bytes (values included)
    s["sig_word_raw_hits"] = [
        {"word": m.group(0), "at_byte": m.start()}
        for m in SIG_WORDS.finditer(seal_b.decode("utf-8"))
    ]
    # any PGP-armored / detached-signature markers in the seal bytes
    s["pgp_markers"] = [x for x in (
        "-----BEGIN PGP SIGNATURE-----", "-----BEGIN PGP MESSAGE-----",
        "-----BEGIN CERTIFICATE-----", "-----BEGIN SIGNED MESSAGE-----",
    ) if x.encode("ascii") in seal_b]
    # sidecar files next to the seal that could carry a detached signature
    crdir = ROOT / "lead/cert_realcheck_20261109"
    s["sidecar_candidates"] = sorted(
        p.name for p in crdir.iterdir()
        if p.is_file() and (
            p.suffix.lower() in {".sig", ".asc", ".pem", ".p7s", ".crt", ".pub"}
            or "sig" in p.name.lower() or "sign" in p.name.lower()
        )
    )
    s["dir_file_count"] = len([p for p in crdir.iterdir() if p.is_file()])
    # does _cr_real_verify.py contain any cryptographic signature verification?
    vpy = (crdir / "_cr_real_verify.py").read_bytes().decode("utf-8")
    s["verify_py_sig_word_lines"] = [
        {"line": i, "text": ln.strip()[:200]}
        for i, ln in enumerate(vpy.splitlines(), 1)
        if SIG_WORDS.search(ln)
    ]
    # how seal_ok is actually derived: print lines containing seal_ok / SEAL_SHA
    s["verify_py_seal_lines"] = [
        {"line": i, "text": ln.strip()[:220]}
        for i, ln in enumerate(vpy.splitlines(), 1)
        if re.search(r"seal_ok|SEAL_SHA|seal_sha|seal_hash|_cr_seal|read_bytes|sha256", ln, re.I)
    ]

    # ---- 3. the 302-item universe ------------------------------------------
    rp = ROOT / "lead/gate_r9sem_20261109/_r9s_regress_out.json"
    rb = rp.read_bytes()
    r = json.loads(rb.decode("utf-8"))
    u = report["universe302"]
    u["path"] = "lead/gate_r9sem_20261109/_r9s_regress_out.json"
    u["sha256"], u["bytes"] = sha(rp)
    u["top_keys"] = sorted(r.keys())
    u["verdict"] = r.get("verdict")
    u["no_relaxation"] = r.get("no_relaxation")
    u["spec_inventory_keys"] = sorted(r["spec_inventory"].keys())
    d32 = r["domains32"]
    u["domains32_keys"] = sorted(d32.keys())
    u["n_domains"] = d32.get("n_domains")
    u["len_rows"] = len(d32["rows"])
    u["len_flips"] = len(d32["flips"])
    u["n_flips_declared"] = d32.get("n_flips")
    u["len_tightens"] = len(d32["tightens"])
    u["n_tightens_declared"] = d32.get("n_tightens")
    u["len_whitelist"] = len(d32["whitelist"])
    u["whitelist"] = d32["whitelist"]
    u["rows_first"] = d32["rows"][0] if d32["rows"] else None
    u["rows_last"] = d32["rows"][-1] if d32["rows"] else None
    u["flip_first"] = d32["flips"][0] if d32["flips"] else None
    u["samples_keys"] = sorted(r["samples"].keys())
    u["samples_positive"] = len(r["samples"]["positive"]) if isinstance(r["samples"]["positive"], list) else r["samples"]["positive"]
    u["samples_negative"] = len(r["samples"]["negative"]) if isinstance(r["samples"]["negative"], list) else r["samples"]["negative"]
    u["four_domains_total_remaining"] = r.get("four_domains_total_remaining")
    # count distinct (domain, token) pairs in rows
    pairs = [(x.get("domain"), x.get("token")) for x in d32["rows"]]
    u["distinct_pairs"] = len(set(pairs))
    u["distinct_domains_in_rows"] = len({x[0] for x in pairs})
    u["distinct_tokens_in_rows"] = len({x[1] for x in pairs})

    # ---- 4. P5 / artifact_text / seal_path in read-only sources ------------
    targets = [
        "lead/cert_realcheck_20261109/_cr_real_verify.py",
        "lead/cert_realcheck_20261109/CERT_REAL_CHECK.md",
        "lead/falsifiable_no_relax_20261109/_fnr_check.py",
        "lead/falsifiable_no_relax_20261109/FALSIFIABLE_NO_RELAX.md",
        "lead/falsifiable_no_relax_20261109/_fnrd_verify_out.json",
        "lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md",
    ]
    p5 = []
    for rel in targets:
        p = ROOT / rel
        if not p.exists():
            p5.append({"file": rel, "exists": False})
            continue
        txt = p.read_bytes().decode("utf-8", "replace")
        hits = []
        for i, ln in enumerate(txt.splitlines(), 1):
            if re.search(r"artifact_text|seal_path|P5|TypeError|5/5|独立|independent|盲标|blind|oracle|ORACLE", ln, re.I):
                hits.append({"line": i, "text": ln.strip()[:260]})
        p5.append({"file": rel, "exists": True, "n_hits": len(hits), "hits": hits[:200]})
    report["p5"]["per_file"] = p5

    WDIR.mkdir(parents=True, exist_ok=True)
    out = WDIR / "_os_audit_out.json"
    blob = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    out.write_bytes(blob.encode("utf-8"))
    print("WROTE", out, "bytes", len(blob.encode("utf-8")))
    print("=== FINGERPRINTS ===")
    for x in report["fingerprints"]:
        print("  %-72s match=%s sha=%s bytes=%d" % (x["file"], x["match"], x["computed_sha256"], x["computed_bytes"]))
    print("  ALL_MATCH =", all(x["match"] for x in report["fingerprints"]))
    print("=== SEAL ===")
    for k in ("top_keys", "n_items", "item_keys_sorted", "all_item_keysets_identical",
              "oracle_subkeys_sorted", "all_oracle_authors", "all_predicate_authors",
              "all_oracle_truth", "all_oracle_truth_types", "sig_word_key_hits",
              "sig_word_raw_hits", "pgp_markers", "sidecar_candidates", "dir_file_count"):
        print("  %s = %s" % (k, json.dumps(s[k], ensure_ascii=False)[:600]))
    print("  verify_py_sig_word_lines =", json.dumps(s["verify_py_sig_word_lines"], ensure_ascii=False)[:1200])
    print("=== 302 ===")
    for k, v in u.items():
        if k not in ("rows_first", "rows_last", "flip_first"):
            print("  %s = %s" % (k, json.dumps(v, ensure_ascii=False)[:500]))
    print("  rows_first =", json.dumps(u["rows_first"], ensure_ascii=False)[:400])
    print("  flip_first =", json.dumps(u["flip_first"], ensure_ascii=False)[:400])


if __name__ == "__main__":
    main()
