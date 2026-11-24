# -*- coding: utf-8 -*-
r"""_crdoc_run.py -- THIS session's independent runs for CERT_REAL_CHECK.md.

DISCIPLINE:
  * zero live-game / zero sampling / zero injection code;
  * READ-ONLY artifacts are only read, never written;
  * existing files in the write domain are NEVER overwritten: modules are
    loaded by importlib and only their functions are called; NO main() of an
    existing script is executed;
  * new files are prefixed _crdoc_ and live in lead/cert_realcheck_20261109/.

Run:
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_crdoc_run.py
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import shutil
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "cert_realcheck_20261109"
FNR = ROOT / "lead" / "falsifiable_no_relax_20261109"
R9S_DIR = ROOT / "lead" / "gate_r9sem_20261109"

OUT = {}

# ---------------------------------------------------------------------------
# 0. eight read-only fingerprints (hashlib, real read_bytes)
# ---------------------------------------------------------------------------
BASELINE = {
    "lead/falsifiable_no_relax_20261109/_fnr_check.py":
        ("94d89881f6a2e1afdea3ca78f56006ca27f1cabe1ec6384a9194718c327b00c2", 28811),
    "lead/check_fp_audit_20261109/CHECK_FALSE_ALARM_AUDIT.md":
        ("464355c08f961a40de2a719c556816a70448a17564f63bdc05d65981f5d09ed4", 40950),
    "lead/check_fp_audit_20261109/_cfa_out.json":
        ("a47ec95a2d3baed54cc903a765eadf31ee65f9e4a9e87c5f780148c0963dc64a", 17830),
    "lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md":
        ("f9d00b7c9a12a996bac9d89b0bf5a948dfe026e21f472bd825d7924d35a47adc", 52705),
    "lead/gate_r9sem_20261109/_r9s_regress.py":
        ("16612625a7a5b11aba8b19c895a612f319bd4421c9c095b2ff8285be9214c4b4", 11258),
    "lead/gate_r9sem_20261109/_r9s_predicates.py":
        ("b0265fc57ef4facd06d92b4852344a80d983f14560a8521525ba18e533ae7034", 23111),
    "lead/PENDING_DECISIONS.md":
        ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md":
        ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}


def fingerprint_all():
    rows = []
    for rel, (h0, n0) in BASELINE.items():
        b = (ROOT / rel).read_bytes()
        h, n = hashlib.sha256(b).hexdigest(), len(b)
        rows.append({"file": rel, "sha256": h, "bytes": n,
                     "match": (h == h0 and n == n0)})
    return rows


OUT["step0_fingerprints_start"] = fingerprint_all()
OUT["step0_all_match"] = all(r["match"] for r in OUT["step0_fingerprints_start"])

# ---------------------------------------------------------------------------
# 1. load modules WITHOUT executing their main()
# ---------------------------------------------------------------------------
sys.path.insert(0, str(R9S_DIR))
import _r9s_predicates as R9S  # noqa: E402


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fnr = load_module("fnr_crdoc", FNR / "_fnr_check.py")
V = load_module("crv_crdoc", WDIR / "_cr_real_verify.py")
P = load_module("crdoc_pasted", WDIR / "_crdoc_pasted.py")

# ---------------------------------------------------------------------------
# 2. L2 self-attestation: P1 forged anchors + fabricated quotes vs ORIGINAL
# ---------------------------------------------------------------------------
REF = json.loads((R9S_DIR / "_r9s_regress_out.json").read_text(encoding="utf-8"))
dom = REF["domains32"]
flips = [{"domain": x["domain"], "token": x["token"]} for x in dom["flips"]]
items = [{"domain": row["domain"], "token": el["token"]}
         for row in dom["rows"] if not row.get("main_missing")
         for el in row["per_element"]]
wl = [tuple(x) for x in dom["whitelist"]]


def robust_predicate(text, token):
    ok, layer, detail = R9S.r9s_element_present(text, token)
    if not ok:
        return (False, layer, detail)
    if re.search(r"待判|待定|尚需|尚未|不另下结论|暂不作判定|本件不重录|"
                 r"见台账|详见台账|详见附件|并非【|是否【|不可重建|"
                 r"输出数据待补|返回值详见附件", text):
        return (False, "", {"rejected_by": "pending/pointer guard"})
    return (ok, layer, detail)


FORGED_QUOTE = "本复核凭空编造的引文，未见于任何交付件。"
fake_certs = copy.deepcopy(fnr.CERTS)
for i, c in enumerate(fake_certs.values()):
    # the three self-attested booleans are literally WRITTEN BY THE CALLER here
    c["oracle_truth"] = True
    c["oracle_author"] = "independent_blind_adjudicator"
    c["predicate_author"] = "author_of_V1"
    c["oracle_sealed"] = True
    c["anchor"] = "cfaa/NO_SUCH_%d.md:999999" % i
    c["quote"] = FORGED_QUOTE

p1_old = fnr.no_relaxation_check(
    items, flips, wl, set(R9S.SPECS.keys()),
    set(R9S.SPECS.keys()) | {"额外预留要素"},
    fake_certs, fnr.SPEC_ROLES, robust_predicate, fnr.ADVERSARIAL,
    predicate_author="author_of_V1", whitelist_author="independent",
    whitelist_sealed=True)
OUT["step2_P1_original_checker"] = {
    "VERDICT": p1_old["VERDICT"],
    "L1_ok": p1_old["L1"]["ok"], "L2_ok": p1_old["L2"]["ok"],
    "L3_ok": p1_old["L3"]["ok"], "L1_problems": p1_old["L1"]["problems"],
    "L3_caught": p1_old["L3"]["detail"]["n_adversarial_caught"],
    "anchor_files_exist": [(ROOT / c["anchor"].split(":")[0]).exists()
                           for c in fake_certs.values()],
    "certificate_ok_direct": list(fnr.certificate_ok(
        next(iter(fake_certs.values())), list(fnr.SPEC_ROLES.values())[0])),
}

# ---------------------------------------------------------------------------
# 3. REAL verifier: 5 honest certificates, P1 forgery, ignored caller booleans
# ---------------------------------------------------------------------------
good = V.certs_from_seal()
seal_bytes = (WDIR / "_cr_seal.json").read_bytes()
OUT["step3_seal"] = {
    "sha256": hashlib.sha256(seal_bytes).hexdigest(),
    "bytes": len(seal_bytes),
    "matches_hardcoded_commitment":
        hashlib.sha256(seal_bytes).hexdigest() == V.PRE_REGISTERED_SEAL_SHA256,
}

r_real = V.verify_all(good)
OUT["step3b_real_5"] = {
    "VERDICT": r_real["VERDICT"], "n_items": r_real["n_items"],
    "n_pass": r_real["n_pass"], "n_stale": r_real["n_stale"],
    "n_fail": r_real["n_fail"], "seal_ok": r_real["seal_ok"],
    "stats": r_real["stats"],
    "per_item": [{"item": r["item"], "outcome": r["outcome"]}
                 for r in r_real["rows"]],
}

forged = copy.deepcopy(good)
for i, k in enumerate(sorted(forged)):
    forged[k]["anchor"] = "cfaa/NO_SUCH_%d.md:999999" % i
    forged[k]["quote"] = FORGED_QUOTE
r_p1 = V.verify_all(forged)
OUT["step3a_P1_real_verifier"] = {
    "VERDICT": r_p1["VERDICT"], "n_pass": r_p1["n_pass"],
    "n_fail": r_p1["n_fail"], "n_stale": r_p1["n_stale"],
    "per_item": [{"item": r["item"], "outcome": r["outcome"],
                  "problems": r["problems"]} for r in r_p1["rows"]],
}

# caller booleans all forged to "not independent": truth must still come from seal
booleans = copy.deepcopy(good)
for c in booleans.values():
    c.update({"oracle_truth": False, "oracle_sealed": False,
              "oracle_author": "author_of_V1",
              "predicate_author": "author_of_V1",
              "whitelist_sealed": False})
r_bool = V.verify_all(booleans)
OUT["step3_ignored_caller_booleans"] = {
    "VERDICT": r_bool["VERDICT"], "n_pass": r_bool["n_pass"],
    "ignored_lists": [r["checks"].get("ignored_caller_booleans", [])
                      for r in r_bool["rows"]],
}

# ---------------------------------------------------------------------------
# 4. five tamper classes (+STALE, +same-byte-count, +seal co-located rewrite)
# ---------------------------------------------------------------------------
seal = json.loads(seal_bytes.decode("utf-8"))
k1 = ("lead/matrix_ab_ruling_20261109/", "需谁批准")
rec1 = next(r for r in seal["items"] if tuple(r["item"]) == k1)
rul = "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md"
n11 = "lead/n11_wording_fix_20261108/N11_WORDING_FIX.md"
SB = WDIR / "_crdoc_sandbox"


def fresh_sandbox():
    if SB.exists():
        shutil.rmtree(SB)
    rels = sorted({r["anchor"].rsplit(":", 1)[0] for r in seal["items"]})
    for rel in rels:
        dst = SB / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes((ROOT / rel).read_bytes())
    return SB, rels


def run_case(name, cert_mut=None, disk_mut=None, use_sandbox=False, note=""):
    sb, rels = fresh_sandbox()
    c = copy.deepcopy(good)
    if cert_mut:
        cert_mut(c, rec1)
    if disk_mut:
        disk_mut(sb, rels)
    r = V.verify_all(c, root=(sb if use_sandbox else ROOT))
    row = next(x for x in r["rows"] if tuple(x["item"]) == k1)
    return {"case": name, "VERDICT_of_item": row["outcome"],
            "problems": row["problems"], "n_pass": r["n_pass"],
            "n_fail": r["n_fail"], "n_stale": r["n_stale"],
            "global_VERDICT": r["VERDICT"], "note": note}


def d_one_char(sb, _rels):
    p = sb / rul
    b = p.read_bytes()
    old = "批准人一律 = **乙设计责任人**".encode("utf-8")
    new = "批准人一律 = **乙设计责任X**".encode("utf-8")
    assert old in b
    p.write_bytes(b.replace(old, new, 1))


def d_replace(sb, _rels):
    (sb / rul).write_bytes((sb / n11).read_bytes())


def d_append(sb, _rels):
    with (sb / rul).open("ab") as fh:
        fh.write(b"\n<!-- appended after seal; evidence span untouched -->\n")


def d_same_size(sb, _rels):
    p = sb / rul
    b = p.read_bytes()
    assert b"pf2:200" in b
    p.write_bytes(b.replace(b"pf2:200", b"pf2:201", 1))


def c_lineno(c, rec):
    c[k1]["anchor"] = rec["anchor"].replace(":108", ":109")


def c_syn(c, rec):
    c[k1]["quote"] = rec["quote"].replace("一律 =", "全部 =")


def c_hash(c, rec):
    c[k1]["declared_file_sha256"] = "0" * 64


cases = [
    run_case("T1_one_character_changed", disk_mut=d_one_char, use_sandbox=True,
             note="one char inside anchored quote line, sandbox copy only"),
    run_case("T2_line_number_changed", cert_mut=c_lineno,
             note="anchor :108 -> :109"),
    run_case("T3_quote_synonym", cert_mut=c_syn,
             note="一律 = -> 全部 = (same meaning)"),
    run_case("T4_file_replaced", disk_mut=d_replace, use_sandbox=True,
             note="RULING_MATRIX_AB.md replaced by N11 bytes"),
    run_case("T5_declared_hash_mismatch", cert_mut=c_hash,
             note="caller claims wrong sha256 while disk is clean"),
    run_case("T6_append_only_edit_STALE", disk_mut=d_append, use_sandbox=True,
             note="extra: bytes changed outside evidence span"),
    run_case("R4_same_byte_count_swap", disk_mut=d_same_size, use_sandbox=True,
             note="extra: equal-length char replacement inside span"),
]
OUT["step4_tamper"] = cases

# fp / fn on the constructed corpus
good_cases = [{"id": "G%d" % (i + 1), "outcome": r["outcome"]}
              for i, r in enumerate(r_real["rows"])]
bad_cases = [{"id": "P1_%d" % (i + 1), "outcome": r["outcome"]}
             for i, r in enumerate(r_p1["rows"])]
bad_cases += [{"id": c["case"], "outcome": c["VERDICT_of_item"]} for c in cases]
fp = [g for g in good_cases if g["outcome"] != "PASS"]
fn = [b for b in bad_cases if b["outcome"] == "PASS"]
n_bad, n_good = len(bad_cases), len(good_cases)
OUT["step4_fp_fn"] = {
    "n_good": n_good, "n_bad": n_bad,
    "false_positives": len(fp), "false_negatives": len(fn),
    "fp_ids": [g["id"] for g in fp], "fn_ids": [b["id"] for b in fn],
    "sensitivity_lower_95_if_zero_fn": round(0.05 ** (1.0 / n_bad), 6),
    "fp_upper_95_if_zero_fp": round(1 - 0.05 ** (1.0 / n_good), 6),
    "caveat": "constructed, non-random corpus; NOT a population FP/FN rate",
}

# Part C: co-located commitment rewrite (reviewer's material finding)
sb, rels = fresh_sandbox()
p = sb / rul
b_lines = p.read_bytes().decode("utf-8").splitlines(keepends=True)
b_lines[107] = "ATTACKER-FABRICATED-SEMANTIC-CLAIM-123 批准人 一律 = 攻击者编造值\n"
p.write_bytes("".join(b_lines).encode("utf-8"))
blob = p.read_bytes()
fake_seal = copy.deepcopy(seal)
fr = next(r for r in fake_seal["items"] if tuple(r["item"]) == k1)
fr["quote"] = "ATTACKER-FABRICATED-SEMANTIC-CLAIM-123 批准人 一律 = 攻击者编造值"
fr["roles"] = {"具体施事值": "攻击者编造值", "批准人角色头": "批准人",
               "赋值算子": "一律 ="}
fr["file_sha256"] = hashlib.sha256(blob).hexdigest()
fr["bytes"] = len(blob)
fr["evidence_span_sha256"] = hashlib.sha256(
    (fr["quote"] + "\n").encode("utf-8")).hexdigest()
fake_path = SB / "_crdoc_seal_fake.json"
fake_path.write_text(json.dumps(fake_seal, ensure_ascii=False, indent=1,
                                sort_keys=True), encoding="utf-8", newline="\n")
fb = fake_path.read_bytes()
old_sha, old_bytes = V.PRE_REGISTERED_SEAL_SHA256, V.EXPECTED_SEAL_BYTES
# equivalent to editing the verifier source (both live in the SAME write domain)
V.PRE_REGISTERED_SEAL_SHA256 = hashlib.sha256(fb).hexdigest()
V.EXPECTED_SEAL_BYTES = len(fb)
r_co = V.verify_all(good, root=sb, seal_path=fake_path)
V.PRE_REGISTERED_SEAL_SHA256, V.EXPECTED_SEAL_BYTES = old_sha, old_bytes
OUT["step4C_co_located_rewrite"] = {
    "VERDICT": r_co["VERDICT"], "seal_ok": r_co["seal_ok"],
    "n_pass": r_co["n_pass"], "n_fail": r_co["n_fail"],
    "other_items_pass": [r["outcome"] for r in r_co["rows"][1:]],
    "first_item_outcome": r_co["rows"][0]["outcome"],
    "first_item_problems": r_co["rows"][0]["problems"],
    "note": "editing BOTH the seal and the hard-coded constant makes an "
            "attacker-edited certified line pass; no out-of-band commitment",
}

# ---------------------------------------------------------------------------
# 5. L1: SELF_CERTIFIED under ideal conditions + padding + repair demos
# ---------------------------------------------------------------------------
ideal = dict(items=items, flips=flips, whitelist=wl,
             registered_tokens={i["token"] for i in items},
             spec_keys=set(R9S.SPECS.keys()))
l1_ideal = fnr.check_l1(ideal["items"], ideal["flips"], ideal["whitelist"],
                        ideal["registered_tokens"], ideal["spec_keys"],
                        whitelist_sealed=True, whitelist_author="independent")
OUT["step5a_L1_ideal"] = {"ok": l1_ideal[0], "problems": l1_ideal[1],
                          "detail": l1_ideal[2]}
pad = dict(ideal)
pad["spec_keys"] = set(R9S.SPECS.keys()) | {"额外预留要素"}
l1_pad = fnr.check_l1(pad["items"], pad["flips"], pad["whitelist"],
                      pad["registered_tokens"], pad["spec_keys"],
                      whitelist_sealed=True, whitelist_author="independent")
OUT["step5a_L1_padding"] = {"ok": l1_pad[0], "problems": l1_pad[1]}

# --- 5(b) the ORIGINAL demo, verbatim from _cr_p1_old_check.py:153-204 ------
def check_l1_repaired_orig(items, flips, whitelist, registered_tokens,
                           predicate_spec_keys, provenance,
                           coverage_threshold=1.0):
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


keys_exact = json.dumps(sorted(R9S.SPECS.keys()), ensure_ascii=False,
                        sort_keys=True)
keys_hash = hashlib.sha256(keys_exact.encode("utf-8")).hexdigest()
seal_hash = hashlib.sha256(seal_bytes).hexdigest()
prov = {"seal_path": str(WDIR / "_cr_seal.json"), "seal_sha256": seal_hash,
        "author": "independent_blind_adjudicator",
        "predicate_author": "author_of_V1",
        "keys_bytes": keys_exact, "keys_sha256": keys_hash}
d0 = check_l1_repaired_orig(ideal["items"], ideal["flips"], ideal["whitelist"],
                            ideal["registered_tokens"], ideal["spec_keys"], prov)
OUT["step5b_original_demo_honest"] = {"ok": d0[0], "problems": d0[1],
                                      "detail": d0[2]}
p2 = dict(prov)
p2["keys_bytes"] = json.dumps(sorted(set(R9S.SPECS.keys()) | {"额外预留要素"}),
                              ensure_ascii=False, sort_keys=True)
p2["keys_sha256"] = hashlib.sha256(p2["keys_bytes"].encode("utf-8")).hexdigest()
d2 = check_l1_repaired_orig(ideal["items"], ideal["flips"], ideal["whitelist"],
                            ideal["registered_tokens"], pad["spec_keys"], p2)
bad_seal_path = SB / "_crdoc_seal_bad.json"
bad_seal_path.write_bytes(seal_bytes + b"\n<!-- tampered -->\n")
p4 = dict(prov)
p4["seal_path"] = str(bad_seal_path)
p4["seal_sha256"] = hashlib.sha256(bad_seal_path.read_bytes()).hexdigest()
d4 = check_l1_repaired_orig(ideal["items"], ideal["flips"], ideal["whitelist"],
                            ideal["registered_tokens"], ideal["spec_keys"], p4)
OUT["step5b_original_demo_attacks"] = {
    "B2_both_sides_padding": {"ok": d2[0], "problems": d2[1]},
    "B4_tampered_seal_recomputed_hash": {"ok": d4[0], "problems": d4[1]},
    "note": "expected hash is self-computed at runtime; author/keys_* come "
            "from the caller's provenance dict, NOT hard-coded",
}

# --- 5(c) HARD-CODED pre-registration variant (implements 4(c) 1-3) --------
HARD_SEAL_SHA256 = seal_hash                     # MUST be out-of-band / signed
HARD_SEAL_BYTES = len(seal_bytes)
HARD_KEYS_JSON = keys_exact
HARD_KEYS_SHA256 = keys_hash
HARD_WHITELIST_AUTHOR = "independent_blind_adjudicator"   # identity register
HARD_PREDICATE_AUTHOR = "author_of_V1"                    # identity register


def check_l1_repaired_hard(items, flips, whitelist, registered_tokens,
                           predicate_spec_keys,
                           seal_path, coverage_threshold=1.0):
    problems, detail = [], {}
    wl = {tuple(x) for x in whitelist}
    flip_keys = [(f["domain"], f["token"]) for f in flips]
    untested = [i for i in items if i["token"] not in registered_tokens]
    cov = round((len(items) - len(untested)) / max(len(items), 1), 4)
    detail["coverage_ratio"] = cov
    detail["n_structurally_untested"] = len(untested)
    detail["self_certified_witness"] = (
        {k for _, k in wl} == set(predicate_spec_keys))
    if [k for k in flip_keys if k not in wl]:
        problems.append("L1: flips outside whitelist")
    if len(flip_keys) != len(wl):
        problems.append("L1: flip count != whitelist size")
    if cov < coverage_threshold:                       # coverage is a REAL FAIL
        problems.append("L1: coverage %.4f < %.4f" % (cov, coverage_threshold))
    p = Path(seal_path)
    if not p.is_file():
        problems.append("L1: provenance seal file missing")
    else:
        b = p.read_bytes()                              # REAL disk read
        if len(b) != HARD_SEAL_BYTES or \
           hashlib.sha256(b).hexdigest() != HARD_SEAL_SHA256:
            problems.append("L1: whitelist seal sha256/bytes mismatch")
    if HARD_WHITELIST_AUTHOR == HARD_PREDICATE_AUTHOR:
        problems.append("L1: whitelist author == predicate author")
    if hashlib.sha256(HARD_KEYS_JSON.encode("utf-8")).hexdigest() != HARD_KEYS_SHA256:
        problems.append("L1: spec-key register broken")
    if set(predicate_spec_keys) != set(json.loads(HARD_KEYS_JSON)):
        problems.append("L1: spec keys differ (padding / truncation detected)")
    return (len(problems) == 0, problems, detail)


sp = str(WDIR / "_cr_seal.json")
h0 = check_l1_repaired_hard(ideal["items"], ideal["flips"], ideal["whitelist"],
                            ideal["registered_tokens"], ideal["spec_keys"], sp)
h2 = check_l1_repaired_hard(ideal["items"], ideal["flips"], ideal["whitelist"],
                            ideal["registered_tokens"], pad["spec_keys"], sp)
h4 = check_l1_repaired_hard(ideal["items"], ideal["flips"], ideal["whitelist"],
                            ideal["registered_tokens"], ideal["spec_keys"],
                            str(bad_seal_path))
OUT["step5c_hardcoded_demo"] = {
    "ideal": {"ok": h0[0], "problems": h0[1], "detail": h0[2]},
    "B2_both_sides_padding": {"ok": h2[0], "problems": h2[1]},
    "B4_tampered_seal_recomputed_hash": {"ok": h4[0], "problems": h4[1]},
    "note": "standalone demo in write domain; _fnr_check.py NOT modified. "
            "Hard-coded constants still need an out-of-band signature to "
            "resist a co-located double rewrite.",
}

# ---------------------------------------------------------------------------
# 6. pasteable realVerifier snippet, run verbatim in THIS session
# ---------------------------------------------------------------------------
t0 = time.perf_counter()
pg = {tuple(r["item"]): {"anchor": r["anchor"], "quote": r["quote"],
                         "roles": copy.deepcopy(r["roles"])}
      for r in seal["items"]}
pf = copy.deepcopy(pg)
for i, k in enumerate(sorted(pf)):
    pf[k]["anchor"] = "cfaa/NO_SUCH_%d.md:999999" % i
    pf[k]["quote"] = FORGED_QUOTE
g = P.verify_all(pg)
fres = P.verify_all(pf)
OUT["step6_pasted_snippet"] = {
    "runs": True,
    "good": {"VERDICT": g["VERDICT"], "n_pass": g["n_pass"],
             "n_fail": g["n_fail"], "seal_ok": g["seal_ok"]},
    "P1_forged": {"VERDICT": fres["VERDICT"], "n_pass": fres["n_pass"],
                  "n_fail": fres["n_fail"]},
    "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
}

# ---------------------------------------------------------------------------
# 7. final fingerprint recheck
# ---------------------------------------------------------------------------
OUT["step7_fingerprints_end"] = fingerprint_all()
OUT["step7_all_unchanged"] = all(r["match"] for r in OUT["step7_fingerprints_end"])

(WDIR / "_crdoc_run_out.json").write_text(
    json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8",
    newline="\n")

print("ALL_EIGHT_MATCH_BASELINE_START =", OUT["step0_all_match"])
print("ALL_EIGHT_UNCHANGED_END =", OUT["step7_all_unchanged"])
print("step2_P1_original_checker =", json.dumps(OUT["step2_P1_original_checker"], ensure_ascii=False))
print("step3b_real_5 =", json.dumps(OUT["step3b_real_5"], ensure_ascii=False))
print("step3a_P1_real_verifier = NON_PASS n_fail=%d" % OUT["step3a_P1_real_verifier"]["n_fail"])
print("step3_ignored_caller_booleans =", OUT["step3_ignored_caller_booleans"]["VERDICT"],
      OUT["step3_ignored_caller_booleans"]["n_pass"])
print("step4_tamper:")
for c in OUT["step4_tamper"]:
    print("  ", c["case"], "->", c["VERDICT_of_item"], c["problems"])
print("step4_fp_fn =", json.dumps(OUT["step4_fp_fn"], ensure_ascii=False))
print("step4C_co_located_rewrite =", json.dumps(OUT["step4C_co_located_rewrite"], ensure_ascii=False))
print("step5a_L1_ideal =", json.dumps(OUT["step5a_L1_ideal"], ensure_ascii=False))
print("step5b_original_demo_attacks =", json.dumps(OUT["step5b_original_demo_attacks"], ensure_ascii=False))
print("step5c_hardcoded_demo =", json.dumps(OUT["step5c_hardcoded_demo"], ensure_ascii=False))
print("step6_pasted_snippet =", json.dumps(OUT["step6_pasted_snippet"], ensure_ascii=False))
print("WROTE _crdoc_run_out.json (new file in write domain)")
