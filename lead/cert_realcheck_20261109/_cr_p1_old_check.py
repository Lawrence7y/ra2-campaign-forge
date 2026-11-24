# -*- coding: utf-8 -*-
r"""_cr_p1_old_check.py -- independently reproduce P1 against the ORIGINAL
_fnr_check.py (read-only, imported as a module; main() is NEVER called).

Also exercises:
  * STEP 1(c): who supplies oracle_truth / oracle_author / oracle_sealed;
  * STEP 4(a): SELF_CERTIFIED is a hard FAIL even under ideal conditions;
  * STEP 4(d): the proposed L1 repair as an in-memory function only.

Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/cert_realcheck_20261109/_cr_p1_old_check.py
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")
FNR = ROOT / "lead" / "falsifiable_no_relax_20261109"
R9S_DIR = ROOT / "lead" / "gate_r9sem_20261109"
WDIR = ROOT / "lead" / "cert_realcheck_20261109"
sys.path.insert(0, str(R9S_DIR))
import _r9s_predicates as R9S  # noqa: E402

spec = importlib.util.spec_from_file_location("fnr_cr", FNR / "_fnr_check.py")
fnr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fnr)
CERTS = copy.deepcopy(fnr.CERTS)
ADVERSARIAL = list(fnr.ADVERSARIAL)
SPEC_ROLES = fnr.SPEC_ROLES

REF = json.loads((R9S_DIR / "_r9s_regress_out.json").read_text(encoding="utf-8"))
dom = REF["domains32"]


def my_robust_predicate(text, token):
    """Same shape as the audit's robust predicate: all 13 adversarial caught."""
    ok, layer, detail = R9S.r9s_element_present(text, token)
    if not ok:
        return (False, layer, detail)
    bad = __import__("re").search(
        r"待判|待定|尚需|尚未|不另下结论|暂不作判定|本件不重录|"
        r"见台账|详见台账|详见附件|并非【|是否【|不可重建|"
        r"输出数据待补|返回值详见附件", text)
    if bad:
        return (False, "", {"rejected_by": "pending/pointer guard"})
    return (ok, layer, detail)


def real_base():
    f = [{"domain": x["domain"], "token": x["token"]} for x in dom["flips"]]
    it = [{"domain": row["domain"], "token": el["token"]}
          for row in dom["rows"] if not row.get("main_missing")
          for el in row["per_element"]]
    w = [tuple(x) for x in dom["whitelist"]]
    return dict(items=it, flips=f, whitelist=w,
                registered_tokens=set(R9S.SPECS.keys()),
                spec_keys=set(R9S.SPECS.keys()),
                certificates=copy.deepcopy(CERTS), spec_roles=SPEC_ROLES,
                predicate=my_robust_predicate,
                adversarial_corpus=ADVERSARIAL,
                predicate_author="author_of_V1",
                whitelist_author="independent", whitelist_sealed=True)


def third_party_certs(world_certs):
    """STEP 1(c): these three fields are literally WRITTEN BY THE CALLER."""
    c = copy.deepcopy(world_certs)
    for v in c.values():
        v["oracle_author"] = "independent_blind_adjudicator"
        v["predicate_author"] = "author_of_V1"
        v["oracle_truth"] = True
        v["oracle_sealed"] = True
    return c


def good_skeleton():
    g = real_base()
    g["spec_keys"] = set(R9S.SPECS.keys()) | {"额外预留要素"}
    g["certificates"] = third_party_certs(CERTS)
    return g


def verdict(kw):
    r = fnr.no_relaxation_check(**kw)
    return {"VERDICT": r["VERDICT"],
            "L1_ok": r["L1"]["ok"], "L2_ok": r["L2"]["ok"], "L3_ok": r["L3"]["ok"],
            "L1_problems": list(r["L1"]["problems"]),
            "L1_coverage": r["L1"]["detail"]["coverage_ratio"],
            "L1_self_certified": r["L1"]["detail"]["self_certified"],
            "L3_caught": r["L3"]["detail"]["n_adversarial_caught"],
            "L3_total": r["L3"]["detail"]["n_adversarial"]}


FORGED_QUOTE = "本复核凭空编造的引文，未见于任何交付件。"


def main():
    out = {}
    # ---- STEP 1(d): P1 forged anchors + fabricated quotes -----------------
    w = good_skeleton()
    fake = copy.deepcopy(w["certificates"])
    for i, c in enumerate(fake.values()):
        c["anchor"] = "cfaa/NO_SUCH_%d.md:999999" % i
        c["quote"] = FORGED_QUOTE
    w["certificates"] = fake
    p1 = verdict(w)
    p1["anchor_files_exist"] = [(ROOT / c["anchor"].split(":")[0]).exists()
                                for c in fake.values()]
    p1["certificate_ok_direct"] = fnr.certificate_ok(
        next(iter(fake.values())), list(SPEC_ROLES.values())[0])
    out["step1d_P1_old_checker"] = p1
    print("=== STEP 1(d): P1 vs ORIGINAL _fnr_check.py ===")
    print(json.dumps(p1, ensure_ascii=False, indent=1))

    # ---- STEP 1(c): provenance of the three booleans ----------------------
    src = (FNR / "_fnr_check.py").read_text(encoding="utf-8").splitlines()
    prov = {"caller_written_lines_in_probe": [],
            "caller_written_lines_in_fnr_check": [],
            "declaration_in_CERTS": [],
            "read_sites_in_certificate_ok": []}
    for i, l in enumerate(src):
        if "oracle_truth" in l or "oracle_author" in l or "oracle_sealed" in l:
            n = i + 1
            if 95 <= n <= 124:
                prov["read_sites_in_certificate_ok"].append([n, l.strip()])
            elif 314 <= n <= 351:
                prov["declaration_in_CERTS"].append([n, l.strip()[:150]])
            else:
                prov["caller_written_lines_in_fnr_check"].append([n, l.strip()[:150]])
    out["step1c_boolean_provenance"] = prov
    print("\n=== STEP 1(c): who supplies the three booleans ===")
    print(json.dumps(prov, ensure_ascii=False, indent=1))

    # ---- STEP 4(a): SELF_CERTIFIED under IDEAL conditions -----------------
    ideal = good_skeleton()
    ideal["spec_keys"] = set(R9S.SPECS.keys())          # remove padding
    # 302 items can all be registered (an ideal, fully-covered world)
    all_tokens = {i["token"] for i in ideal["items"]}
    ideal["registered_tokens"] = all_tokens             # coverage = 1.0
    l1 = fnr.check_l1(ideal["items"], ideal["flips"], ideal["whitelist"],
                      ideal["registered_tokens"], ideal["spec_keys"],
                      whitelist_sealed=True, whitelist_author="independent")
    out["step4a_L1_ideal"] = {"ok": l1[0], "problems": l1[1], "detail": l1[2]}
    print("\n=== STEP 4(a): check_l1 under ideal (sealed/independent/coverage=1) ===")
    print(json.dumps(out["step4a_L1_ideal"], ensure_ascii=False, indent=1))

    # ---- STEP 4(d): in-memory demonstration of the proposed repair --------
    # This is NOT a change to _fnr_check.py; it is a standalone function.
    def check_l1_repaired(items, flips, whitelist, registered_tokens,
                          predicate_spec_keys, provenance,
                          coverage_threshold=1.0):
        """Replace set-equality with REAL provenance + seal verification.

        provenance must be a dict with:
          seal_sha256: 64-hex pre-registered seal value,
          seal_path:   path whose bytes are actually read & hashed,
          predicate_author: author id of the predicate,
          keys_sha256: sha256 of the predicate spec keys (pre-registered),
          keys_bytes:  the exact bytes that were hashed.
        """
        import hashlib
        problems, detail = [], {}
        wl = {tuple(x) for x in whitelist}
        flip_keys = [(f["domain"], f["token"]) for f in flips]
        outside = [k for k in flip_keys if k not in wl]
        untested = [i for i in items if i["token"] not in registered_tokens]
        cov = round((len(items) - len(untested)) / max(len(items), 1), 4)
        detail["coverage_ratio"] = cov
        detail["n_structurally_untested"] = len(untested)
        # witness only, never a FAIL
        wl_tokens = {k for _, k in wl}
        detail["self_certified_witness"] = (wl_tokens == set(predicate_spec_keys))
        if outside:
            problems.append("L1: %d flips outside whitelist" % len(outside))
        if len(flip_keys) != len(wl):
            problems.append("L1: flip count != whitelist size")
        if cov < coverage_threshold:
            problems.append("L1: coverage %.4f < threshold %.4f"
                            % (cov, coverage_threshold))
        # REAL provenance: read the seal file, recompute hash, compare
        p = Path(provenance["seal_path"])
        if not p.is_file():
            problems.append("L1: provenance seal file missing")
        else:
            b = p.read_bytes()                       # REAL disk read
            h = hashlib.sha256(b).hexdigest()        # REAL hash recomputation
            if h != provenance["seal_sha256"]:
                problems.append("L1: whitelist seal sha256 mismatch")
            if provenance.get("author") == provenance.get("predicate_author"):
                problems.append("L1: whitelist author == predicate author")
        # padding detection: spec keys must be the pre-registered exact set,
        # AND the exact bytes must hash to the pre-registered value.
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
    import hashlib
    keys_hash = hashlib.sha256(keys_exact.encode("utf-8")).hexdigest()
    seal_blob = (WDIR / "_cr_seal.json").read_bytes()
    seal_hash = hashlib.sha256(seal_blob).hexdigest()
    prov_args = {"seal_path": str(WDIR / "_cr_seal.json"),
                 "seal_sha256": seal_hash,
                 "author": "independent_blind_adjudicator",
                 "predicate_author": "author_of_V1",
                 "keys_bytes": keys_exact, "keys_sha256": keys_hash}
    rep = check_l1_repaired(ideal["items"], ideal["flips"], ideal["whitelist"],
                            ideal["registered_tokens"], ideal["spec_keys"],
                            prov_args)
    out["step4d_repaired_L1_demo"] = {
        "ok": rep[0], "problems": rep[1], "detail": rep[2],
        "note": "standalone demo in write domain; _fnr_check.py NOT modified"}
    # padding attack: add a dummy key to spec_keys and see it cannot help
    padded = dict(ideal)
    padded["spec_keys"] = set(R9S.SPECS.keys()) | {"额外预留要素"}
    rep2 = check_l1_repaired(padded["items"], padded["flips"],
                             padded["whitelist"], padded["registered_tokens"],
                             padded["spec_keys"], prov_args)
    out["step4d_repaired_L1_demo"]["padding_attack_still_passes"] = rep2[0]
    out["step4d_repaired_L1_demo"]["padding_attack_problems"] = rep2[1]
    print("\n=== STEP 4(d): proposed L1 repair (standalone demo) ===")
    print(json.dumps(out["step4d_repaired_L1_demo"], ensure_ascii=False, indent=1))

    (WDIR / "_cr_p1_old_check_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8",
        newline="\n")
    print("\nWROTE _cr_p1_old_check_out.json (write domain only)")


if __name__ == "__main__":
    main()
