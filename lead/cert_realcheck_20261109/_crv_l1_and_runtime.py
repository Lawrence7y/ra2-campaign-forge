# -*- coding: utf-8 -*-
r"""_crv_l1_and_runtime.py -- INDEPENDENT reviewer probes.

Part A: runtime proof that the design's verify_all() REALLY calls read_bytes()
        (monkeypatch tracer + raiser), not just trusting caller declarations.
Part B: evaluate the pasted L1 repair snippet from the design's step 4(d)
        (verbatim copy of _cr_p1_old_check.py:153-206 logic). Test whether
        its "pre-registered" seal hash / author / keys are actually
        independent of the caller.
Part C: empirical H9 -- attacker rewrites BOTH the seal AND the in-memory
        hard-coded constant; does verify_all() accept forged content?
Part D: step 5(b) operational check -- does the seal's ORACLE satisfy
        _fnr_check.py:78-91's NO_RELAXATION definition?

Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_crv_l1_and_runtime.py
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
SB = WDIR / "_crv_sandbox3"

spec = importlib.util.spec_from_file_location("crv_mod3", WDIR / "_cr_real_verify.py")
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)
SEAL_JSON = json.loads(SEAL.read_bytes().decode("utf-8"))
OUT = {}


def honest_certs():
    return {tuple(r["item"]): {"anchor": r["anchor"], "quote": r["quote"],
                               "roles": copy.deepcopy(r["roles"])}
            for r in SEAL_JSON["items"]}


def fresh():
    if SB.exists():
        shutil.rmtree(SB)
    rels = sorted({r["anchor"].rsplit(":", 1)[0] for r in SEAL_JSON["items"]})
    for rel in rels:
        dst = SB / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dst)
    return rels


# ===================== Part A: runtime read_bytes tracer =====================
def part_a():
    orig = Path.read_bytes
    calls = []

    def traced(self, *a, **kw):
        calls.append(str(self))
        return orig(self, *a, **kw)

    Path.read_bytes = traced
    try:
        r = V.verify_all(honest_certs())
    finally:
        Path.read_bytes = orig
    OUT["A_runtime_read_bytes_tracer"] = {
        "n_calls": len(calls), "paths": calls,
        "VERDICT": r["VERDICT"],
        "note": "monkeypatched pathlib.Path.read_bytes; counted real calls",
    }
    # raiser: if we make read_bytes raise, verification must NOT silently PASS
    def raiser(self, *a, **kw):
        raise OSError("REVIEWER: read_bytes blocked")
    Path.read_bytes = raiser
    try:
        try:
            r2 = V.verify_all(honest_certs())
            res = {"raised": False, "VERDICT": r2["VERDICT"]}
        except OSError as e:
            res = {"raised": True, "error": str(e)}
    finally:
        Path.read_bytes = orig
    OUT["A_runtime_read_bytes_raiser"] = res


# ============ Part B: pasted L1 repair snippet, evaluated verbatim ===========
def check_l1_repaired(items, flips, whitelist, registered_tokens,
                      predicate_spec_keys, provenance, coverage_threshold=1.0):
    """VERBATIM logic of _cr_p1_old_check.py:153-204 (design's step 4(d))."""
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
        problems.append("L1: coverage %.4f < threshold %.4f"
                        % (cov, coverage_threshold))
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
        problems.append("L1: predicate spec keys differ from pre-registered "
                        "set (padding / truncation detected)")
    return (len(problems) == 0, problems, detail)


def part_b():
    # minimal honest world
    items = [{"token": "t1"}, {"token": "t2"}]
    flips = [{"domain": "d", "token": "t1"}, {"domain": "d", "token": "t2"}]
    wl = [("d", "t1"), ("d", "t2")]
    keys = ["t1", "t2"]
    exact = json.dumps(sorted(keys), ensure_ascii=False, sort_keys=True)
    seal_path = SB / "_crv_l1_seal.json"
    seal_path.parent.mkdir(parents=True, exist_ok=True)
    seal_path.write_text("HONEST-SEAL", encoding="utf-8")
    honest_prov = {"seal_path": str(seal_path),
                   "seal_sha256": hashlib.sha256(b"HONEST-SEAL").hexdigest(),
                   "author": "independent", "predicate_author": "author_of_V1",
                   "keys_bytes": exact,
                   "keys_sha256": hashlib.sha256(exact.encode()).hexdigest()}
    r0 = check_l1_repaired(items, flips, wl, set(keys), set(keys), honest_prov)
    # B1: attacker TAMPERS the seal AND recomputes the expected hash from disk
    seal_path.write_text("ATTACKER-SEAL", encoding="utf-8")
    attack_prov = dict(honest_prov)
    attack_prov["seal_sha256"] = hashlib.sha256(
        seal_path.read_bytes()).hexdigest()   # design's :210-211 pattern
    r1 = check_l1_repaired(items, flips, wl, set(keys), set(keys), attack_prov)
    # B2: attacker controls provenance fully, pads keys with a dummy
    padded = set(keys) | {"额外预留要素"}
    padded_bytes = json.dumps(sorted(padded), ensure_ascii=False, sort_keys=True)
    attack_prov2 = dict(honest_prov)
    attack_prov2["keys_bytes"] = padded_bytes
    attack_prov2["keys_sha256"] = hashlib.sha256(
        padded_bytes.encode()).hexdigest()
    attack_prov2["author"] = "independent"     # self-declared string
    r2 = check_l1_repaired(items, flips, wl, set(keys), padded, attack_prov2)
    OUT["B_L1_repair_snippet"] = {
        "honest_ok": r0[0], "honest_problems": r0[1],
        "B1_tampered_seal_with_runtime_recomputed_expected_hash": {
            "ok": r1[0], "problems": r1[1],
            "note": "expected hash recomputed from the tampered file itself "
                    "-> self-attested; PASSES"},
        "B2_padded_keys_with_attacker_supplied_pre-registration": {
            "ok": r2[0], "problems": r2[1],
            "note": "keys_bytes + keys_sha256 both caller-supplied -> PASSES"},
        "finding": "the demo downgrades SELF_CERTIFIED and reads the seal "
                   "file, but its 'pre-registered' values are NOT hard-coded: "
                   "seal_sha256 is computed from the disk at :210-211, and "
                   "author / keys_bytes / keys_sha256 all come from the "
                   "caller's provenance dict. Does NOT implement step 4(c) "
                   "criteria (1)(2)(3).",
    }


# ======== Part C: empirical co-located commitment rewrite (H9) ==============
def part_c():
    fresh()
    fake = copy.deepcopy(SEAL_JSON)
    # attacker fabricates a quote that IS present on the sandbox disk
    forged_quote = "ATTACKER-FABRICATED-SEMANTIC-CLAIM-123"
    rec = fake["items"][0]
    rec["quote"] = forged_quote
    rel, _, ln = rec["anchor"].rpartition(":")
    p = SB / rel
    ls = p.read_bytes().decode("utf-8").splitlines()
    ls[int(ln) - 1] = forged_quote
    p.write_bytes(("\n".join(ls) + "\n").encode("utf-8"))
    # attacker must also recompute the file hash / bytes / span hash
    b = p.read_bytes()
    rec["file_sha256"] = hashlib.sha256(b).hexdigest()
    rec["bytes"] = len(b)
    lo, hi = rec["evidence_lines"]
    span = "\n".join(ls[lo - 1:hi]) + "\n"
    rec["evidence_span_sha256"] = hashlib.sha256(
        span.encode("utf-8")).hexdigest()
    # roles must also be in the (now single-line) window
    rec["roles"] = {"forged": forged_quote}
    blob = json.dumps(fake, ensure_ascii=False, indent=2,
                      sort_keys=True).encode("utf-8") + b"\n"
    fake_seal_path = SB / "_crv_fake_seal.json"
    fake_seal_path.write_bytes(blob)
    certs = {tuple(r["item"]): {"anchor": r["anchor"], "quote": r["quote"],
                                "roles": copy.deepcopy(r["roles"])}
             for r in fake["items"]}
    # patch the in-memory commitment (equivalent to editing the .py file,
    # which sits in the SAME write domain as the seal)
    old_h, old_b = V.PRE_REGISTERED_SEAL_SHA256, V.EXPECTED_SEAL_BYTES
    V.PRE_REGISTERED_SEAL_SHA256 = hashlib.sha256(blob).hexdigest()
    V.EXPECTED_SEAL_BYTES = len(blob)
    try:
        r = V.verify_all(certs, root=SB, seal_path=fake_seal_path)
    finally:
        V.PRE_REGISTERED_SEAL_SHA256, V.EXPECTED_SEAL_BYTES = old_h, old_b
    row0 = r["rows"][0]
    OUT["C_co_located_commitment_rewrite"] = {
        "VERDICT": r["VERDICT"], "seal_ok": r["seal_ok"],
        "n_pass": r["n_pass"], "n_fail": r["n_fail"],
        "first_item_outcome": row0["outcome"],
        "first_item_problems": row0["problems"],
        "note": "both _cr_seal.json and the hard-coded constant live in the "
                "SAME write domain; editing both makes a fully fabricated "
                "'certificate' PASS. Confirms step 5(b)'s 'self-attestation "
                "with a better pipe' caveat.",
    }


# ======== Part D: operational NO_RELAXATION check ===========================
def part_d():
    fnr_src = (ROOT / "lead" / "falsifiable_no_relax_20261109" /
               "_fnr_check.py").read_text(encoding="utf-8")
    OUT["D_operational_definition"] = {
        "def_lines": [i + 1 for i, l in
                      enumerate(fnr_src.splitlines())
                      if "ORACLE: I -> {0,1}" in l or "NO_RELAXATION :=" in l
                      or "published SHA256 seal" in l],
        "seal_oracle_fields": sorted(SEAL_JSON["items"][0]["oracle"].keys()),
        "seal_has_302_labels": len(SEAL_JSON["items"]) == 302,
        "seal_n_items": len(SEAL_JSON["items"]),
        "seal_author_is_plain_string": isinstance(
            SEAL_JSON["items"][0]["oracle"]["author"], str),
        "conclusion": "NO_RELAXATION requires ORACLE(i) for ALL i in I "
                      "produced BEFORE V1 by an adjudicator who did not see "
                      "V1 and did not author V1. The seal has 5 self-authored "
                      "labels with truth=true hard-coded by the same session. "
                      "Therefore step 5(b)'s 'cannot unconditionally judge' "
                      "is CORRECT.",
    }


def main():
    part_a()
    part_b()
    part_c()
    part_d()
    (WDIR / "_crv_l1_runtime_out.json").write_text(
        json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8",
        newline="\n")
    print(json.dumps(OUT, ensure_ascii=False, indent=1))
    print("WROTE _crv_l1_runtime_out.json")


if __name__ == "__main__":
    main()
