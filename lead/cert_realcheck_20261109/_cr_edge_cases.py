# -*- coding: utf-8 -*-
r"""_cr_edge_cases.py -- STEP 2(c)/3(c) supplementary probes for STALE and
seal tampering. All writes are inside the write domain sandbox only.

Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_cr_edge_cases.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
WDIR = Path(r"D:\Project\ra2-campaign-forge\lead\cert_realcheck_20261109")
spec = importlib.util.spec_from_file_location("crv", WDIR / "_cr_real_verify.py")
crv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crv)


def main():
    good = crv.certs_from_seal()
    out = {}

    # E1: append-only edit OUTSIDE the certified span -> STALE, not FAIL
    sb, rels = crv.build_sandbox()
    rul = "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md"
    p = sb / rul
    with p.open("ab") as fh:
        fh.write(b"\n<!-- benign appendix, no evidence line touched -->\n")
    r = crv.verify_all(good, root=sb)
    k = ("lead/matrix_ab_ruling_20261109/", "需谁批准")
    row = next(x for x in r["rows"] if tuple(x["item"]) == k)
    out["E1_append_outside_span"] = {
        "outcome": row["outcome"], "problems": row["problems"],
        "hash_matches_seal": row["checks"].get("hash_matches_seal"),
        "byte_count_matches_seal": row["checks"].get("byte_count_matches_seal"),
        "quote_on_anchor_line": row["checks"].get("quote_verbatim_on_anchor_line"),
        "global_VERDICT": r["VERDICT"], "n_stale": r["n_stale"],
        "n_fail": r["n_fail"]}

    # E2: same-byte edit inside the certified line -> FAIL (not STALE)
    crv.build_sandbox()
    p = sb / rul
    b = p.read_bytes()
    old = "批准人一律 = **乙设计责任人**，pf2:200".encode("utf-8")
    new = "批准人一律 = **乙设计责任人**，pf2:201".encode("utf-8")  # same length
    assert len(old) == len(new) and old in b
    p.write_bytes(b.replace(old, new, 1))
    r = crv.verify_all(good, root=sb)
    row = next(x for x in r["rows"] if tuple(x["item"]) == k)
    out["E2_same_byte_count_char_swap"] = {
        "outcome": row["outcome"], "problems": row["problems"],
        "hash_matches_seal": row["checks"].get("hash_matches_seal"),
        "byte_count_matches_seal": row["checks"].get("byte_count_matches_seal"),
        "note": "byte count alone cannot detect it; sha256 + verbatim quote can"}

    # E3: forged caller booleans are IGNORED (no self-attestation)
    c = crv.certs_from_seal()
    for v in c.values():
        v["oracle_truth"] = False
        v["oracle_author"] = "author_of_V1"
        v["oracle_sealed"] = False
        v["predicate_author"] = "author_of_V1"
        v["whitelist_sealed"] = False
    r = crv.verify_all(c)
    out["E3_forged_caller_booleans_ignored"] = {
        "VERDICT": r["VERDICT"], "n_pass": r["n_pass"],
        "ignored_caller_booleans":
            [x["checks"]["ignored_caller_booleans"] for x in r["rows"]],
        "note": "original certificate_ok would FAIL here; real verifier "
                "ignores caller booleans and uses the sealed ORACLE"}

    # E4: seal itself tampered -> SEAL_INTEGRITY + NON_PASS on all
    crv.build_sandbox()
    seal_bad = WDIR / "_cr_sandbox" / "_cr_seal_bad.json"
    blob = crv.SEAL_PATH.read_bytes().replace(b'"seal_version": "cr-1"',
                                              b'"seal_version": "cr-9"')
    seal_bad.write_bytes(blob)
    r = crv.verify_all(good, seal_path=seal_bad)
    out["E4_seal_tampered"] = {
        "VERDICT": r["VERDICT"], "seal_ok": r["seal_ok"],
        "seal_problems": r["seal_problems"], "n_fail": r["n_fail"]}

    # E5: no seal on disk -> SEAL_MISSING
    missing = WDIR / "_cr_sandbox" / "_cr_no_such_seal.json"
    if missing.exists():
        missing.unlink()
    r = crv.verify_all(good, seal_path=missing)
    out["E5_seal_missing"] = {
        "VERDICT": r["VERDICT"], "seal_ok": r["seal_ok"],
        "seal_problems": r["seal_problems"], "n_fail": r["n_fail"]}

    # E6: caller forges an anchor to a REAL file but non-pre-registered line
    c = crv.certs_from_seal()
    c[k]["anchor"] = rul + ":107"
    r = crv.verify_all(c)
    row = next(x for x in r["rows"] if tuple(x["item"]) == k)
    out["E6_real_file_wrong_line"] = {
        "outcome": row["outcome"], "problems": row["problems"]}

    print(json.dumps(out, ensure_ascii=False, indent=1))
    (WDIR / "_cr_edge_cases_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8",
        newline="\n")


if __name__ == "__main__":
    main()
