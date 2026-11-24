# -*- coding: utf-8 -*-
r"""_crv_b2_clean.py -- isolate B2 with a clean, unmoved seal file.

Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_crv_b2_clean.py
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "cert_realcheck_20261109"
SB = WDIR / "_crv_sandbox4"
SB.mkdir(parents=True, exist_ok=True)


def check_l1_repaired(items, flips, whitelist, registered_tokens,
                      predicate_spec_keys, provenance, coverage_threshold=1.0):
    problems, detail = [], {}
    wl = {tuple(x) for x in whitelist}
    flip_keys = [(f["domain"], f["token"]) for f in flips]
    outside = [k for k in flip_keys if k not in wl]
    untested = [i for i in items if i["token"] not in registered_tokens]
    cov = round((len(items) - len(untested)) / max(len(items), 1), 4)
    detail["coverage_ratio"] = cov
    detail["n_structurally_untested"] = len(untested)
    wl_tokens = {k for _, k in wl}
    detail["self_certified_witness"] = (wl_tokens == set(predicate_spec_keys))
    if outside:
        problems.append("L1: %d flips outside whitelist" % len(outside))
    if len(flip_keys) != len(wl):
        problems.append("L1: flip count != whitelist size")
    if cov < coverage_threshold:
        problems.append("L1: coverage below threshold")
    p = Path(provenance["seal_path"])
    if not p.is_file():
        problems.append("L1: provenance seal file missing")
    else:
        b = p.read_bytes()
        h = hashlib.sha256(b).hexdigest()
        if h != provenance["seal_sha256"]:
            problems.append("L1: whitelist seal sha256 mismatch")
        if provenance.get("author") == provenance.get("predicate_author"):
            problems.append("L1: whitelist author == predicate author")
    kb = provenance["keys_bytes"].encode("utf-8")
    if hashlib.sha256(kb).hexdigest() != provenance["keys_sha256"]:
        problems.append("L1: predicate spec keys not pre-registered")
    exact_keys = set(json.loads(provenance["keys_bytes"]))
    if set(predicate_spec_keys) != exact_keys:
        problems.append("L1: predicate spec keys differ (padding detected)")
    return (len(problems) == 0, problems, detail)


def main():
    items = [{"token": "t1"}, {"token": "t2"}]
    flips = [{"domain": "d", "token": "t1"}, {"domain": "d", "token": "t2"}]
    wl = [("d", "t1"), ("d", "t2")]
    keys = ["t1", "t2"]
    seal = SB / "_crv_clean_seal.bin"
    seal.write_bytes(b"HONEST-SEAL")
    base = {"seal_path": str(seal),
            "seal_sha256": hashlib.sha256(b"HONEST-SEAL").hexdigest(),
            "author": "independent", "predicate_author": "author_of_V1"}
    out = {}
    # baseline: no padding
    e = json.dumps(sorted(keys), ensure_ascii=False, sort_keys=True)
    p0 = dict(base, keys_bytes=e,
              keys_sha256=hashlib.sha256(e.encode()).hexdigest())
    out["baseline_no_padding"] = check_l1_repaired(
        items, flips, wl, set(keys), set(keys), p0)[:2]
    # B2 clean: attacker pads BOTH spec_keys and the pre-registration records
    padded = set(keys) | {"额外预留要素"}
    e2 = json.dumps(sorted(padded), ensure_ascii=False, sort_keys=True)
    p2 = dict(base, keys_bytes=e2,
              keys_sha256=hashlib.sha256(e2.encode()).hexdigest())
    out["B2_clean_padding_both_sides"] = check_l1_repaired(
        items, flips, wl, set(keys), padded, p2)[:2]
    # B3: attacker sets author == predicate_author but ALSO supplies a
    # fully self-consistent provenance (no independent registry)
    p3 = dict(p0, author="author_of_V1")
    out["B3_author_equality"] = check_l1_repaired(
        items, flips, wl, set(keys), set(keys), p3)[:2]
    # B4: attacker tampers seal AND recomputes the expected hash from disk
    seal.write_bytes(b"ATTACKER-SEAL")
    p4 = dict(p0, seal_sha256=hashlib.sha256(
        seal.read_bytes()).hexdigest())
    out["B4_tampered_seal_recomputed_hash"] = check_l1_repaired(
        items, flips, wl, set(keys), set(keys), p4)[:2]
    seal.write_bytes(b"HONEST-SEAL")
    (WDIR / "_crv_b2_clean_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8",
        newline="\n")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print("WROTE _crv_b2_clean_out.json")


if __name__ == "__main__":
    main()
