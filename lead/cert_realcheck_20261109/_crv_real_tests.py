# -*- coding: utf-8 -*-
r"""_crv_real_tests.py -- INDEPENDENT reviewer re-run of steps 3(a)-3(d).

Uses the design's verify_all()/verify_one() as the SUBJECT UNDER TEST,
but constructs ALL test inputs independently in this reviewer's own sandbox
(_crv_sandbox/). Does NOT call the design's main() (which would overwrite
existing files). Also adds reviewer-only adversarial cases to probe for
"true verification also doesn't read the disk" and "tampering gets through".

Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_crv_real_tests.py
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
SB = WDIR / "_crv_sandbox"

spec = importlib.util.spec_from_file_location("crv_mod", WDIR / "_cr_real_verify.py")
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)

seal_bytes = SEAL.read_bytes()
SEAL_HASH = hashlib.sha256(seal_bytes).hexdigest()
SEAL_JSON = json.loads(seal_bytes.decode("utf-8"))
OUT = {}


def honest_certs():
    return {tuple(r["item"]): {"anchor": r["anchor"], "quote": r["quote"],
                               "roles": copy.deepcopy(r["roles"])}
            for r in SEAL_JSON["items"]}


def fresh_sandbox():
    if SB.exists():
        shutil.rmtree(SB)
    rels = sorted({r["anchor"].rsplit(":", 1)[0] for r in SEAL_JSON["items"]})
    for rel in rels:
        dst = SB / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dst)
    return rels


def brief(r):
    return {"VERDICT": r["VERDICT"], "seal_ok": r["seal_ok"],
            "seal_problems": r["seal_problems"],
            "n_pass": r["n_pass"], "n_stale": r["n_stale"],
            "n_fail": r["n_fail"],
            "rows": [{"item": x["item"], "outcome": x["outcome"],
                      "problems": x["problems"]} for x in r["rows"]],
            "stats": r["stats"]}


def main():
    # ---- independent seal integrity check ----------------------------------
    OUT["seal_check"] = {
        "sha256": SEAL_HASH,
        "bytes": len(seal_bytes),
        "matches_hardcoded": SEAL_HASH == V.PRE_REGISTERED_SEAL_SHA256,
        "bytes_matches_hardcoded": len(seal_bytes) == V.EXPECTED_SEAL_BYTES,
        "n_items": len(SEAL_JSON["items"]),
    }
    # verify every registered file hash/bytes/span against the REAL disk
    disk_rows = []
    for rec in SEAL_JSON["items"]:
        rel, _, ln = rec["anchor"].rpartition(":")
        p = ROOT / rel
        b = p.read_bytes()
        ls = b.decode("utf-8").splitlines()
        lo, hi = rec["evidence_lines"]
        span = "\n".join(ls[lo - 1:hi]) + "\n"
        disk_rows.append({
            "item": rec["item"], "anchor": rec["anchor"],
            "file_sha256_ok": hashlib.sha256(b).hexdigest() == rec["file_sha256"],
            "bytes_ok": len(b) == rec["bytes"],
            "span_sha256_ok": hashlib.sha256(span.encode("utf-8")).hexdigest()
                              == rec["evidence_span_sha256"],
            "n_lines_ok": len(ls) == rec["n_lines"],
            "quote_on_anchor_line": rec["quote"] in ls[int(ln) - 1],
            "roles_in_window": {k: (v in "\n".join(ls[lo - 1:hi]))
                                for k, v in rec["roles"].items()},
        })
    OUT["seal_vs_disk_independent"] = disk_rows

    # ---- 3(b): 5 real whitelist items --------------------------------------
    r_real = brief(V.verify_all(honest_certs()))
    OUT["step3b_real_5"] = r_real

    # ---- 3(a): P1 forged anchors + fabricated quotes -----------------------
    forged = copy.deepcopy(honest_certs())
    for i, k in enumerate(sorted(forged)):
        forged[k]["anchor"] = "cfaa/NO_SUCH_%d.md:999999" % i
        forged[k]["quote"] = "本复核凭空编造的引文，未见于任何交付件。"
    OUT["step3a_P1_forged"] = brief(V.verify_all(forged))

    # ---- 3(c): 5 tamper classes, each on my OWN fresh sandbox -------------
    rul = "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md"
    n11 = "lead/n11_wording_fix_20261108/N11_WORDING_FIX.md"
    k1 = ("lead/matrix_ab_ruling_20261109/", "需谁批准")
    rec1 = next(r for r in SEAL_JSON["items"] if tuple(r["item"]) == k1)

    def case(name, cert_mut=None, disk_mut=None, root=None, note=""):
        fresh_sandbox()
        c = copy.deepcopy(honest_certs())
        if cert_mut:
            cert_mut(c, rec1)
        rr = root if root is not None else ROOT
        if disk_mut:
            disk_mut(SB)
        r = V.verify_all(c, root=rr)
        row = next(x for x in r["rows"] if tuple(x["item"]) == k1)
        return {"case": name, "VERDICT_of_item": row["outcome"],
                "problems": row["problems"],
                "global_VERDICT": r["VERDICT"],
                "n_pass": r["n_pass"], "n_fail": r["n_fail"],
                "n_stale": r["n_stale"], "note": note}

    def d_one_char(sb):
        p = sb / rul
        b = p.read_bytes()
        old = "批准人一律 = **乙设计责任人**".encode("utf-8")
        new = "批准人一律 = **乙设计责任X**".encode("utf-8")
        assert old in b
        p.write_bytes(b.replace(old, new, 1))

    def d_replace(sb):
        (sb / rul).write_bytes((ROOT / n11).read_bytes())

    def d_append(sb):
        with (sb / rul).open("ab") as fh:
            fh.write(b"\n<!-- appended outside certified span -->\n")

    def c_lineno(c, rec):
        c[k1]["anchor"] = rec["anchor"].replace(":108", ":109")

    def c_syn(c, rec):
        c[k1]["quote"] = rec["quote"].replace("一律 =", "全部 =")

    def c_hash(c, rec):
        c[k1]["declared_file_sha256"] = "0" * 64

    cases = [
        case("T1_one_character_changed", disk_mut=d_one_char, root=SB,
             note="one char inside anchored line on MY sandbox"),
        case("T2_line_number_changed", cert_mut=c_lineno),
        case("T3_quote_synonym", cert_mut=c_syn),
        case("T4_file_replaced", disk_mut=d_replace, root=SB),
        case("T5_declared_hash_mismatch", cert_mut=c_hash),
        case("T6_append_only_edit_STALE", disk_mut=d_append, root=SB),
    ]
    OUT["step3c_tamper"] = cases

    # ---- REVIEWER-ONLY: does it REALLY read the disk? ----------------------
    # R1: put a fake hash in the seal itself (tamper seal), see if caught.
    fresh_sandbox()
    bad_seal = copy.deepcopy(SEAL_JSON)
    bad_seal["items"][0]["file_sha256"] = "0" * 64
    seal_bad_path = SB / "_crv_bad_seal.json"
    seal_bad_path.write_text(json.dumps(bad_seal, ensure_ascii=False, indent=1),
                             encoding="utf-8")
    r_seal_bad = brief(V.verify_all(honest_certs(), seal_path=seal_bad_path))
    OUT["reviewer_R1_rewritten_seal"] = r_seal_bad

    # R2: seal file deleted -> must FAIL all, not vacuous PASS
    fresh_sandbox()
    missing = SB / "_crv_missing_seal.json"
    r_seal_missing = brief(V.verify_all(honest_certs(), seal_path=missing))
    OUT["reviewer_R2_missing_seal"] = r_seal_missing

    # R3: caller booleans forged to "not independent" -> must still PASS
    fresh_sandbox()
    bool_forged = copy.deepcopy(honest_certs())
    for v in bool_forged.values():
        v["oracle_truth"] = False
        v["oracle_author"] = "author_of_V1"
        v["predicate_author"] = "author_of_V1"
        v["oracle_sealed"] = False
        v["whitelist_sealed"] = False
    r_bools = V.verify_all(bool_forged)
    OUT["reviewer_R3_caller_booleans_ignored"] = {
        "VERDICT": r_bools["VERDICT"], "n_pass": r_bools["n_pass"],
        "n_fail": r_bools["n_fail"],
        "ignored_per_item": [x["checks"].get("ignored_caller_booleans")
                             for x in r_bools["rows"]]}

    # R4: same-byte-count char swap inside evidence span (pf2:200->201)
    def d_same_len(sb):
        p = sb / rul
        b = p.read_bytes()
        assert b"pf2:200" in b
        p.write_bytes(b.replace(b"pf2:200", b"pf2:201", 1))

    cases.append(case("R4_same_byte_count_swap", disk_mut=d_same_len, root=SB,
                      note="pf2:200->pf2:201, equal length, outside quote"))
    OUT["step3c_tamper"] = cases

    # R5: anchor file deleted on sandbox -> FAIL (real disk read evidence)
    def d_delete(sb):
        (sb / rul).unlink()

    OUT["reviewer_R5_anchor_file_deleted"] = case(
        "R5_anchor_file_deleted", disk_mut=d_delete, root=SB)

    # ---- 3(d): fp / fn on MY OWN independently constructed corpus ----------
    good_cases = [{"id": "G%d" % (i + 1), "label": "GOOD",
                   "outcome": x["outcome"]}
                  for i, x in enumerate(r_real["rows"])]
    bad_cases = [{"id": "P1_%d" % (i + 1), "label": "BAD",
                  "outcome": x["outcome"]}
                 for i, x in enumerate(OUT["step3a_P1_forged"]["rows"])]
    for c in OUT["step3c_tamper"]:
        bad_cases.append({"id": c["case"], "label": "BAD",
                          "outcome": c["VERDICT_of_item"]})
    fp = [g for g in good_cases if g["outcome"] != "PASS"]
    fn = [b for b in bad_cases if b["outcome"] == "PASS"]
    OUT["step3d_fp_fn"] = {"n_good": len(good_cases), "n_bad": len(bad_cases),
                           "false_positives": len(fp),
                           "false_negatives": len(fn),
                           "fp_ids": [g["id"] for g in fp],
                           "fn_ids": [b["id"] for b in fn],
                           "caveat": "independent constructed corpus; "
                                     "NOT a population FP/FN rate"}

    (WDIR / "_crv_real_out.json").write_text(
        json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8",
        newline="\n")
    print(json.dumps({
        "seal_check": OUT["seal_check"],
        "seal_vs_disk_independent": OUT["seal_vs_disk_independent"],
        "step3b": {k: OUT["step3b_real_5"][k] for k in
                   ("VERDICT", "n_pass", "n_stale", "n_fail", "seal_ok",
                    "stats")},
        "step3a": {k: OUT["step3a_P1_forged"][k] for k in
                   ("VERDICT", "n_pass", "n_stale", "n_fail")},
        "step3c": [{"case": c["case"], "VERDICT_of_item": c["VERDICT_of_item"],
                    "global_VERDICT": c.get("global_VERDICT"),
                    "problems": c["problems"]} for c in OUT["step3c_tamper"]],
        "reviewer_R1_rewritten_seal": {
            k: OUT["reviewer_R1_rewritten_seal"][k] for k in
            ("VERDICT", "seal_ok", "seal_problems", "n_pass", "n_fail")},
        "reviewer_R2_missing_seal": {
            k: OUT["reviewer_R2_missing_seal"][k] for k in
            ("VERDICT", "seal_ok", "seal_problems", "n_pass", "n_fail")},
        "reviewer_R3_caller_booleans_ignored":
            OUT["reviewer_R3_caller_booleans_ignored"],
        "reviewer_R5_anchor_file_deleted": {
            k: OUT["reviewer_R5_anchor_file_deleted"][k] for k in
            ("VERDICT_of_item", "problems")},
        "step3d_fp_fn": OUT["step3d_fp_fn"],
    }, ensure_ascii=False, indent=1))
    print("WROTE _crv_real_out.json")


if __name__ == "__main__":
    main()
