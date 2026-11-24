# -*- coding: utf-8 -*-
r"""_crv_holes.py -- INDEPENDENT reviewer hunt for gaps in the design.

Focus per reviewer brief: "真校验其实也没读盘" and "篡改抓不住".
Probes:
  H1: bytes/hash mismatch is only recorded in `checks`, NEVER in `problems`.
      Is STALE reachable with an unchanged evidence SPAN? (should be)
      Is STALE reachable when the WHOLE FILE is replaced but the certified
      span happens to be reproduced verbatim? (transferability hole)
  H2: a cert with a nonexistent anchor but a caller-supplied `declared_file_sha256`
      string -- does verify_one ever open the caller's claimed path?
  H3: missing `seal_rec["item"]` key handling / extra seal records.
  H4: line-number-only tamper that still keeps the quote on the new line.
  H5: does verify_all ever return PASS with 0 rows (vacuous)?
  H6: exact FP/FN power bound recomputation (reviewer's own arithmetic).
  H7: does the seal's ORACLE author have ANY external proof? (provenance)
  H8: unicode / trailing-whitespace normalization hole in span hash.
  H9: attacker rewrites BOTH seal and hard-coded constant in verifier.

Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_crv_holes.py
"""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "cert_realcheck_20261109"
SEAL = WDIR / "_cr_seal.json"
SB = WDIR / "_crv_sandbox2"

spec = importlib.util.spec_from_file_location("crv_mod2", WDIR / "_cr_real_verify.py")
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)
SEAL_JSON = json.loads(SEAL.read_bytes().decode("utf-8"))
OUT = {}

rul = "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md"
k1 = ("lead/matrix_ab_ruling_20261109/", "需谁批准")
rec1 = next(r for r in SEAL_JSON["items"] if tuple(r["item"]) == k1)


def fresh():
    if SB.exists():
        shutil.rmtree(SB)
    rels = sorted({r["anchor"].rsplit(":", 1)[0] for r in SEAL_JSON["items"]})
    for rel in rels:
        dst = SB / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dst)
    return rels


def honest_certs():
    return {tuple(r["item"]): {"anchor": r["anchor"], "quote": r["quote"],
                               "roles": copy.deepcopy(r["roles"])}
            for r in SEAL_JSON["items"]}


def main():
    # ---- H1: STALE with a COMPLETELY different file that preserves the span
    # The design says STALE = "bytes changed outside evidence span". Test the
    # extreme: replace file with a byte string whose certified lines are
    # reproduced verbatim but EVERYTHING ELSE is different.
    fresh()
    p = SB / rul
    orig = (ROOT / rul).read_bytes()
    ls = orig.decode("utf-8").splitlines()
    lo, hi = rec1["evidence_lines"]
    # keep only the certified line, discard all other content
    fake = ("X" * 40 + "\n") * 100 + "\n".join(ls[lo - 1:hi]) + "\n" + \
           ("Y" * 40 + "\n") * 100
    # place certified line at SAME line number ln
    ln = int(rec1["anchor"].rsplit(":", 1)[1])
    prefix = ["X%d" % i for i in range(ln - 1)]
    newlines = prefix + ls[lo - 1:hi] + ["Y%d" % i for i in range(50)]
    p.write_bytes(("\n".join(newlines) + "\n").encode("utf-8"))
    r = V.verify_all(honest_certs(), root=SB)
    row = next(x for x in r["rows"] if tuple(x["item"]) == k1)
    OUT["H1_span_transplanted_into_foreign_file"] = {
        "outcome": row["outcome"], "problems": row["problems"],
        "hash_matches_seal": row["checks"].get("hash_matches_seal"),
        "byte_count_matches_seal": row["checks"].get("byte_count_matches_seal"),
        "quote_on_anchor_line": row["checks"].get("quote_verbatim_on_anchor_line"),
        "global_VERDICT": r["VERDICT"],
        "note": "certified line transplanted at SAME line number into a "
                "completely different file; span hash still matches",
    }

    # ---- H2: caller supplies a fake anchor path + a declared hash.
    # Does verify_one resolve the CALLER's anchor, or only the seal's?
    fresh()
    c = copy.deepcopy(honest_certs())
    c[k1]["anchor"] = "cfaa/ATTACKER.md:1"
    c[k1]["declared_file_sha256"] = hashlib.sha256(
        (ROOT / rul).read_bytes()).hexdigest()
    r2 = V.verify_all(c)
    row2 = next(x for x in r2["rows"] if tuple(x["item"]) == k1)
    OUT["H2_caller_anchor_ignored"] = {
        "outcome": row2["outcome"],
        "problems": row2["problems"],
        "resolved_path": row2["checks"].get("resolved_path"),
        "note": "resolved_path should be the SEAL's file, not caller's",
    }

    # ---- H3: seal record with an EXTRA item not in certs -> is it FAIL?
    fresh()
    extra = copy.deepcopy(SEAL_JSON)
    extra["items"].append(dict(extra["items"][0],
                               item=["bogus/", "EXTRA"]))
    sp = SB / "_crv_extra_seal.json"
    sp.write_text(json.dumps(extra, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    r3 = V.verify_all(honest_certs(), seal_path=sp)
    OUT["H3_extra_seal_record"] = {
        "VERDICT": r3["VERDICT"], "seal_ok": r3["seal_ok"],
        "n_items": len(r3["rows"]), "n_fail": r3["n_fail"],
        "problems_of_extra": next((x["problems"] for x in r3["rows"]
                                   if x["item"] == ["bogus/", "EXTRA"]), None),
    }

    # ---- H4: quote replaced by a SUBSTRING that is still on the line.
    # ANCHOR stays pre-registered, quote is shorter but >=10 chars.
    fresh()
    c4 = copy.deepcopy(honest_certs())
    c4[k1]["quote"] = "批准人一律 = **乙设计责任人**"[:-3]  # still on line
    r4 = V.verify_all(c4)
    row4 = next(x for x in r4["rows"] if tuple(x["item"]) == k1)
    OUT["H4_truncated_quote"] = {
        "outcome": row4["outcome"], "problems": row4["problems"],
        "quote_on_anchor_line": row4["checks"].get(
            "quote_verbatim_on_anchor_line"),
    }

    # ---- H5: empty certs + valid seal -> is it PASS vacuously?
    fresh()
    r5 = V.verify_all({})
    OUT["H5_empty_certs_valid_seal"] = {
        "VERDICT": r5["VERDICT"], "n_items": len(r5["rows"]),
        "n_pass": r5["n_pass"], "seal_ok": r5["seal_ok"],
        "note": "verify_all iterates SEAL items, not caller keys",
    }

    # ---- H6: reviewer's own power-bound arithmetic
    def bound(n_wrong, n_good):
        return {"sensitivity_lower_95": round(0.05 ** (1.0 / n_wrong), 6),
                "fp_upper_95": round(1 - 0.05 ** (1.0 / n_good), 6)}
    OUT["H6_power_bounds"] = {"design_11_5": bound(11, 5),
                              "audit_9_2": bound(9, 2),
                              "proposed_5_8": bound(5, 8),
                              "target_30_30": bound(30, 30),
                              "reviewer_12_5": bound(12, 5)}

    # ---- H7: ORACLE provenance -- any signature / external artifact?
    authors = sorted({r["oracle"]["author"] for r in SEAL_JSON["items"]})
    pa = sorted({r["oracle"]["predicate_author"] for r in SEAL_JSON["items"]})
    OUT["H7_oracle_provenance"] = {
        "authors": authors, "predicate_authors": pa,
        "seal_has_signature_field": any(
            "signature" in r["oracle"] or "sig" in r["oracle"]
            for r in SEAL_JSON["items"]),
        "seal_top_level_keys": sorted(SEAL_JSON.keys()),
        "note": "author is a plain string inside the seal; no PKI/signature",
    }

    # ---- H8: trailing-whitespace / CRLF normalization.
    fresh()
    p8 = SB / rul
    b8 = p8.read_bytes()
    ln = int(rec1["anchor"].rsplit(":", 1)[1])
    ls8 = b8.decode("utf-8").splitlines()
    ls8[ln - 1] = ls8[ln - 1] + " "          # trailing space on certified line
    p8.write_bytes(("\n".join(ls8) + "\n").encode("utf-8"))
    r8 = V.verify_all(honest_certs(), root=SB)
    row8 = next(x for x in r8["rows"] if tuple(x["item"]) == k1)
    OUT["H8_trailing_space_on_certified_line"] = {
        "outcome": row8["outcome"], "problems": row8["problems"],
        "quote_on_anchor_line": row8["checks"].get(
            "quote_verbatim_on_anchor_line"),
    }

    # ---- H9: BOTH seal and the verifier's hard-coded constant rewritten.
    # This is a conceptual (not executed against the real file) check:
    # compute what an attacker would need to change.
    fake_seal = copy.deepcopy(SEAL_JSON)
    fake_seal["items"][0]["quote"] = "ATTACKER-FABRICATED-QUOTE-123"
    fake_blob = json.dumps(fake_seal, ensure_ascii=False, indent=2,
                           sort_keys=True).encode("utf-8") + b"\n"
    OUT["H9_seal_and_constant_rewrite"] = {
        "fake_seal_sha256": hashlib.sha256(fake_blob).hexdigest(),
        "fake_seal_bytes": len(fake_blob),
        "note": "if attacker edits BOTH _cr_seal.json AND "
                "PRE_REGISTERED_SEAL_SHA256 in _cr_real_verify.py, "
                "load_seal() would accept it. No external commitment "
                "(e.g. signed manifest / out-of-band hash) exists.",
        "hardcoded_constant_is_in_same_write_domain": (
            "PRE_REGISTERED_SEAL_SHA256" in
            (WDIR / "_cr_real_verify.py").read_text(encoding="utf-8")),
    }

    # ---- H10: does hash/bytes mismatch appear in `problems` at all?
    OUT["H10_hash_bytes_not_in_problems"] = {
        "source_lines_157_166": [
            "if disk_hash != seal_rec.get('file_sha256'):",
            "    checks['hash_matches_seal'] = False",
            "else: checks['hash_matches_seal'] = True",
            "if disk_bytes != seal_rec.get('bytes'):",
            "    checks['byte_count_matches_seal'] = False",
        ],
        "note": "hash/bytes mismatch only sets checks dict, not problems; "
                "outcome depends on classification at :229-235",
    }

    (WDIR / "_crv_holes_out.json").write_text(
        json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8",
        newline="\n")
    print(json.dumps(OUT, ensure_ascii=False, indent=1))
    print("WROTE _crv_holes_out.json")


if __name__ == "__main__":
    main()
