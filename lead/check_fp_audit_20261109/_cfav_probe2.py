# -*- coding: utf-8 -*-
r"""_cfav_probe2.py -- follow-up: factorial FP quantification, provenance,
citation accuracy, author-guard reproduction, artifact-slot proof.

SOLE WRITE DOMAIN: lead/check_fp_audit_20261109/ (files prefixed _cfav_)
Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/check_fp_audit_20261109/_cfav_probe2.py
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True

import copy
import hashlib
import importlib.util
import itertools
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
FNR = ROOT / "lead" / "falsifiable_no_relax_20261109"
R9S_DIR = ROOT / "lead" / "gate_r9sem_20261109"
WL_DIR = ROOT / "lead" / "whitelist_audit_20261109"
WDIR = ROOT / "lead" / "check_fp_audit_20261109"

_spec = importlib.util.spec_from_file_location("cfav2_fnr", FNR / "_fnr_check.py")
fnr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fnr)
R9S = fnr.R9S
CERTS = fnr.CERTS
ADVERSARIAL = fnr.ADVERSARIAL
SPEC_ROLES = fnr.SPEC_ROLES
REF = json.loads((R9S_DIR / "_r9s_regress_out.json").read_text(encoding="utf-8"))

# author's guard, transcribed verbatim from _fnr_check.py:478-480
AUTHOR_GUARD = re.compile(
    r"待判|待定|尚需|尚未|不另下结论|暂不作判定|本件不重录|"
    r"见台账|详见台账|详见附件|并非【|是否【|不可重建|"
    r"输出数据待补|返回值详见附件")
# my broader guard (authored in probe 1, also fitted -- disclosed)
MY_GUARD = re.compile(
    r"待判|待定|尚需|尚未|不另下结论|暂不作判定|本件不重录|见台账|详见台账|详见附件|"
    r"并非【|是否【|不可重建|输出数据待补|返回值详见附件|"
    r"以.{0,10}为准|见上|见下表|见另册|另附|另见|证据待补|未列出|待确认|未定|"
    r"具体施事姓名以|以密封附件为准|归档编号|归档索引|见方案|对应行")


def author_predicate(text, token):
    ok, layer, detail = R9S.r9s_element_present(text, token)
    if not ok:
        return (False, layer, detail)
    if AUTHOR_GUARD.search(text):
        return (False, "", {"rejected_by": "author pending/pointer guard"})
    return (ok, layer, detail)


def my_predicate(text, token):
    ok, layer, detail = R9S.r9s_element_present(text, token)
    if not ok:
        return (False, layer, detail)
    if MY_GUARD.search(text):
        return (False, "", {"rejected_by": "cfav guard"})
    return (ok, layer, detail)


def base_kwargs():
    dom = REF["domains32"]
    flips = [{"domain": x["domain"], "token": x["token"]} for x in dom["flips"]]
    items = [{"domain": r["domain"], "token": e["token"]}
             for r in dom["rows"] if not r.get("main_missing")
             for e in r["per_element"]]
    wl = [tuple(x) for x in dom["whitelist"]]
    return dict(items=items, flips=flips, whitelist=wl,
                registered_tokens=set(R9S.SPECS.keys()),
                spec_keys=set(R9S.SPECS.keys()),
                certificates=copy.deepcopy(CERTS), spec_roles=SPEC_ROLES,
                predicate=author_predicate,
                adversarial_corpus=list(ADVERSARIAL),
                predicate_author="author_of_V1",
                whitelist_author="independent", whitelist_sealed=True)


NOVEL = [
    ("N-EMPTY-1", "需谁批准", "## 5 改动清单\n批准人一律 = 归档编号A7；具体施事姓名以密封附件为准。\n"),
    ("N-EMPTY-2", "改前改后", "## 4 订正草案\n【改前】旧句共 13 项分写。\n【改后】新句见另册对应行。\n逐处对照表另附。\n"),
    ("N-EMPTY-3", "可重建", "## 4 重建可行性\n判定：正确算法【可唯一重建】。原始采样记录见归档索引。\n"),
]
EXTRA3 = [
    ("X1", "需谁批准", "## 5 清单\n批准人待判，本件不另下结论。\n"),
    ("X2", "改前改后", "## 4 草案\n【改前】详见台账。\n【改后】本件不重录。\n"),
    ("X3", "可重建", "## 4 结论\n是否【可唯一重建】尚需核对。\n"),
]


# ---------------------------------------------------------------------------
# A. Factorial sweep over BENIGN worlds: how much of the FP rate is
#    deterministically driven by spec_keys == whitelist tokens?
# ---------------------------------------------------------------------------
def factorial_sweep():
    axes = {
        "spec_keys": ["same_source_5", "plus_dummy_6"],
        "registered_tokens": ["five", "all_item_tokens"],
        "predicate": ["author_guard", "cfav_guard"],
        "corpus": ["adversarial_13", "adversarial_16"],
        "certs": ["self_declared", "third_party_sealed"],
        "whitelist_author": ["independent", "independent_alt"],
        "whitelist_sealed": [True],
    }
    names = list(axes)
    all_item_tokens = {i["token"] for i in base_kwargs()["items"]}
    rows = []
    for combo in itertools.product(*(axes[n] for n in names)):
        cfg = dict(zip(names, combo))
        w = base_kwargs()
        if cfg["spec_keys"] == "plus_dummy_6":
            w["spec_keys"] = set(R9S.SPECS.keys()) | {"额外预留要素"}
        if cfg["registered_tokens"] == "all_item_tokens":
            w["registered_tokens"] = set(all_item_tokens)
        w["predicate"] = author_predicate if cfg["predicate"] == "author_guard" else my_predicate
        if cfg["corpus"] == "adversarial_16":
            w["adversarial_corpus"] = list(ADVERSARIAL) + EXTRA3
        if cfg["certs"] == "third_party_sealed":
            c = copy.deepcopy(CERTS)
            for v in c.values():
                v["oracle_author"] = "independent_blind_adjudicator"
                v["predicate_author"] = "author_of_V1"
                v["oracle_truth"] = True
                v["oracle_sealed"] = True
            w["certificates"] = c
        w["whitelist_author"] = cfg["whitelist_author"]
        w["whitelist_sealed"] = cfg["whitelist_sealed"]
        r = fnr.no_relaxation_check(**w)
        rows.append({"cfg": cfg, "VERDICT": r["VERDICT"],
                     "L1_ok": r["L1"]["ok"], "L2_ok": r["L2"]["ok"], "L3_ok": r["L3"]["ok"],
                     "L1_problems": list(r["L1"]["problems"]),
                     "L3_caught": r["L3"]["detail"]["n_adversarial_caught"],
                     "L3_total": r["L3"]["detail"]["n_adversarial"]})
    def summarize(key):
        s = [x for x in rows if x["cfg"]["spec_keys"] == key]
        n_alm = sum(1 for x in s if x["VERDICT"] == "ALARM")
        return {"n": len(s), "n_ALARM": n_alm,
                "ALARM_rate": round(n_alm / len(s), 6),
                "n_L1_false": sum(1 for x in s if not x["L1_ok"]),
                "n_L2_false": sum(1 for x in s if not x["L2_ok"]),
                "n_L3_false": sum(1 for x in s if not x["L3_ok"]),
                "distinct_L1_problems": sorted({p for x in s for p in x["L1_problems"]})}
    return {"n_axes": len(names), "axes": axes, "n_worlds": len(rows),
            "same_source_5": summarize("same_source_5"),
            "plus_dummy_6": summarize("plus_dummy_6"),
            "n_any_non_L1_problem": sum(1 for x in rows if (not x["L2_ok"]) or (not x["L3_ok"])),
            "note": "every world is benign by construction: complete certificates, "
                    "independent oracle flags, sealed independent whitelist, robust "
                    "predicate catching every adversarial payload."}


# ---------------------------------------------------------------------------
# B. Reproduce the reply's P2 14/16 using the AUTHOR's exact guard
# ---------------------------------------------------------------------------
def author_guard_p2():
    corpus = list(ADVERSARIAL) + NOVEL
    rows = [{"id": cid, "author_guard_hit": bool(AUTHOR_GUARD.search(txt)),
             "present": bool(author_predicate(txt, tok)[0])}
            for cid, tok, txt in corpus]
    w = base_kwargs()
    w["spec_keys"] = set(R9S.SPECS.keys()) | {"额外预留要素"}   # author's good_base
    w["adversarial_corpus"] = corpus
    r = fnr.no_relaxation_check(**w)
    return {"n_total": len(corpus),
            "n_caught_by_author_guard": sum(1 for x in rows if not x["present"]),
            "leaked_ids": [x["id"] for x in rows if x["present"]],
            "VERDICT": r["VERDICT"],
            "checker_caught": r["L3"]["detail"]["n_adversarial_caught"],
            "rows": rows}


# ---------------------------------------------------------------------------
# C. Adversarial corpus provenance (are all 13 authored in _fnr_check.py?)
# ---------------------------------------------------------------------------
def provenance():
    upstream = []
    for d in (WL_DIR, R9S_DIR, FNR):
        for p in sorted(d.rglob("*.md")) + sorted(d.rglob("*.txt")) + sorted(d.rglob("*.py")):
            if p.name == "_fnr_check.py":
                continue
            try:
                upstream.append((str(p.relative_to(ROOT)), p.read_text(encoding="utf-8", errors="replace")))
            except OSError:
                pass
    rows = []
    for cid, tok, txt in ADVERSARIAL:
        # verbatim full-payload match, and a distinctive fragment match
        frag = txt.strip().split("\n")[-1][:24] if txt.strip() else ""
        exact = [fn for fn, t in upstream if txt in t]
        frag_in = [fn for fn, t in upstream if frag and frag in t]
        rows.append({"id": cid, "verbatim_full_payload_found_in": exact,
                     "distinctive_fragment_found_in": frag_in[:6]})
    return {"n": len(rows),
            "n_with_verbatim_full_payload_upstream": sum(1 for r in rows if r["verbatim_full_payload_found_in"]),
            "n_with_fragment_upstream": sum(1 for r in rows if r["distinctive_fragment_found_in"]),
            "rows": rows}


# ---------------------------------------------------------------------------
# D. Citation accuracy of the reply's key line references
# ---------------------------------------------------------------------------
def citation_accuracy():
    def line_of(rel, n):
        p = ROOT / rel
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[n - 1] if 1 <= n <= len(lines) else "<OUT OF RANGE total=%d>" % len(lines)
    refs = [
        ("lead/whitelist_audit_20261109/WHITELIST_AUDIT.md", 467),
        ("lead/whitelist_audit_20261109/WHITELIST_AUDIT.md", 516),
        ("lead/whitelist_audit_20261109/WHITELIST_AUDIT.md", 517),
        ("lead/whitelist_audit_20261109/WHITELIST_AUDIT.md", 522),
        ("lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md", 466),
        ("lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md", 467),
        ("lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md", 517),
        ("lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md", 522),
        ("lead/falsifiable_no_relax_20261109/_fnr_REPORT.md", 338),
        ("lead/falsifiable_no_relax_20261109/_fnr_REPORT.md", 239),
        ("lead/falsifiable_no_relax_20261109/_fnr_REPORT.md", 427),
        ("lead/falsifiable_no_relax_20261109/_fnr_check.py", 137),
        ("lead/falsifiable_no_relax_20261109/_fnr_check.py", 238),
        ("lead/falsifiable_no_relax_20261109/_fnr_check.py", 280),
        ("lead/falsifiable_no_relax_20261109/_fnr_check.py", 486),
    ]
    return {("" + rel.split("/")[-1] + ":" + str(n)): line_of(rel, n)[:190]
            for rel, n in refs}


# ---------------------------------------------------------------------------
# E. Decisive proof: artifact-level errors are UNREPRESENTABLE
# ---------------------------------------------------------------------------
def artifact_slot_proof():
    w = base_kwargs()
    w["spec_keys"] = set(R9S.SPECS.keys()) | {"额外预留要素"}
    w["predicate"] = author_predicate
    r0 = fnr.no_relaxation_check(**w)
    # attempt to pass delivered-artifact text -- must be rejected by the signature
    w2 = dict(w)
    w2["artifact_text"] = "REAL DELIVERABLE TEXT (all five mains, verbatim)"
    try:
        r1 = fnr.no_relaxation_check(**w2)
        err = None
        v1 = r1["VERDICT"]
    except TypeError as e:
        err = str(e)
        v1 = None
    # the 5 real main files, read-only, hashed -- none is an input to the check
    mains = [
        "lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md",
        "lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md",
        "lead/n11_wording_fix_20261108/N11_WORDING_FIX.md",
        "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",
    ]
    files = []
    for rel in mains:
        p = ROOT / rel
        if p.exists():
            b = p.read_bytes()
            files.append({"path": rel, "bytes": len(b),
                          "sha256": hashlib.sha256(b).hexdigest()})
        else:
            files.append({"path": rel, "exists": False})
    return {"baseline_VERDICT": r0["VERDICT"],
            "extra_kwarg_accepted": err is None,
            "TypeError_message": err,
            "verdict_with_artifact_text": v1,
            "real_main_files": files,
            "note": "no parameter can carry artifact text; any error that lives "
                    "in a delivered artifact is structurally invisible to the check."}


# ---------------------------------------------------------------------------
# F. "Always silent" side: a known-WRONG world the checker still PASSes,
#    and a known-WRONG world it does ALARM on (to show it is not globally silent)
# ---------------------------------------------------------------------------
def silence_both_sides():
    good = base_kwargs()
    good["spec_keys"] = set(R9S.SPECS.keys()) | {"额外预留要素"}

    # WRONG #1: every delivered conclusion emptied in the certificates
    w_empty = copy.deepcopy(good)
    for c in w_empty["certificates"].values():
        for k in c["roles"]:
            c["roles"][k] = "见台账登记，本件不另下结论"
        c["oracle_truth"] = False
    r_empty = fnr.no_relaxation_check(**w_empty)

    # WRONG #2: all 5 anchors/quotes forged, flags still self-declared benign
    w_forge = copy.deepcopy(good)
    for i, c in enumerate(w_forge["certificates"].values()):
        c["anchor"] = "cfav/NO_SUCH_%d.md:999999" % i
        c["quote"] = "本复核凭空编造的引文，未见于任何交付件。"
    r_forge = fnr.no_relaxation_check(**w_forge)

    # WRONG #3: predicate deliberately leaks on a form-like-but-empty payload
    w_leak = copy.deepcopy(good)
    real_p = w_leak["predicate"]
    def leaky(text, token):
        if "待判" in text or "不另下结论" in text:
            return (True, "semantic", {})
        return real_p(text, token)
    w_leak["predicate"] = leaky
    r_leak = fnr.no_relaxation_check(**w_leak)
    return {"wrong1_all_certs_emptied": r_empty["VERDICT"],
            "wrong2_all_anchors_forged": r_forge["VERDICT"],
            "wrong3_predicate_leaks": r_leak["VERDICT"],
            "note": "wrong1 and wrong3 alarm; wrong2 (artifact-level forgery) "
                    "does not. Not globally silent, but blind to a whole error class."}


def main():
    out = {}
    out["A_factorial_sweep"] = factorial_sweep()
    out["B_author_guard_p2"] = author_guard_p2()
    out["C_provenance"] = provenance()
    out["D_citation_accuracy"] = citation_accuracy()
    out["E_artifact_slot"] = artifact_slot_proof()
    out["F_silence_both_sides"] = silence_both_sides()
    (WDIR / "_cfav_out2.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

    print("=== A. FACTORIAL SWEEP OVER BENIGN WORLDS ===")
    a = out["A_factorial_sweep"]
    print(json.dumps({k: v for k, v in a.items() if k != "axes"}, ensure_ascii=False, indent=1))
    print("\n=== B. AUTHOR'S EXACT GUARD ON 13+3 NOVEL ===")
    b = out["B_author_guard_p2"]
    print(json.dumps({k: v for k, v in b.items() if k != "rows"}, ensure_ascii=False))
    print("\n=== C. ADVERSARIAL CORPUS PROVENANCE ===")
    c = out["C_provenance"]
    print("  n=%d  verbatim_full_payload_upstream=%d  fragment_upstream=%d" %
          (c["n"], c["n_with_verbatim_full_payload_upstream"], c["n_with_fragment_upstream"]))
    for r in c["rows"]:
        print("   %-6s exact=%s frag=%s" %
              (r["id"], r["verbatim_full_payload_found_in"][:2], r["distinctive_fragment_found_in"][:2]))
    print("\n=== D. CITATION ACCURACY ===")
    for k, v in out["D_citation_accuracy"].items():
        print("  %-46s %s" % (k, v))
    print("\n=== E. ARTIFACT SLOT PROOF ===")
    print(json.dumps(out["E_artifact_slot"], ensure_ascii=False, indent=1))
    print("\n=== F. SILENCE BOTH SIDES ===")
    print(json.dumps(out["F_silence_both_sides"], ensure_ascii=False))
    print("\nWROTE _cfav_out2.json")


if __name__ == "__main__":
    main()
