# -*- coding: utf-8 -*-
"""_kdv_semantic_probe.py -- independent fixtures probing the k1bit detector.

All fixtures are in-memory source strings; none is executed; no file outside
lead/k1bit_detect_20261109/ is created.  Calls kd.analyse() directly.

Intent (review asks ③ ④ ⑤):
  - Is the predicate semantic (AST/dataflow) or merely "uses any()" / names?
  - Does it distinguish genuine k->1bit collapse from LEGAL aggregation?
  - Does a *legal all() script* cause a false positive (independent fixture)?

Each fixture is labeled with the ground-truth verdict a SEMANTIC judge would
give, plus what a purely-formal detector would likely do.  Results are printed
and written to _kdv_semantic_probe_out.json.
"""
import importlib.util
import json
import sys
from pathlib import Path

WD = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("_kd_detect_probe", WD / "_kd_detect.py")
kd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kd)

FIX = []


def add(name, want, src, note):
    FIX.append((name, want, src, note))


# ---------- ⑤ independent LEGAL all() fixtures (must NOT be reported) --------
add("V1_legal_all_generator", "LEGAL_AGGREGATE", '''
def check(doc):
    terms = ("alpha", "beta", "gamma")
    return all(t in doc for t in terms)
def main():
    if not check(doc):
        print("FAIL: missing terms")
        return 1
    print("PASS all terms present")
    return 0
''', "Semantically legal: AND_k over 3 tokens; one term dead -> FAIL. Uses all(), no any().")

add("V2_legal_all_bound_list", "LEGAL_AGGREGATE", '''
def main():
    keywords = ("红", "蓝", "绿")
    present = [w in body for w in keywords]
    if not all(present):
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "Legal: all() over a bound bool list, AND_k, no OR branch.")

add("V3_legal_all_renamed_vars", "LEGAL_AGGREGATE", '''
def main():
    zzz = ("one", "two")
    qqq = [x in y for x in zzz]
    print("PASS" if all(qqq) else "FAIL")
    return 0
''', "Legal AND_k with deliberately non-tokenish names; tests name independence of LEGAL.")

add("V4_legal_any_with_all_and_attribution", "LEGAL_AGGREGATE", '''
def main():
    needles = ("aa", "bb")
    hits = {}
    for n in needles:
        hits[n] = (n in body)
        print("PER_TOKEN %s %s" % (n, hits[n]))
    if not (all(hits.values()) and any(hits.values())):
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "Legal: per-token attribution retained; any() present but k->vec not lost.")

add("V5_legal_any_over_samples", "LEGAL_AGGREGATE", '''
def main():
    bodies = ["a", "b", "c"]
    if not any("FIXED" in b for b in bodies):
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "Legal: existential over SAMPLES with ONE fixed literal (k=1).")

add("V6_legal_ok_accum_per_item_print", "LEGAL_AGGREGATE", '''
def main():
    ok = True
    for w in ("aa", "bb"):
        good = (w in body)
        ok &= good
        print("PER_TOKEN %s %s" % (w, good))
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1
''', "Legal: ok &= is present, but per-token prints retain attribution.")

# ---------- ③ semantic invariance: same k->1bit, all identifiers renamed ----
add("V7_true_collapse_renamed", "CONFIRMED_K1BIT", '''
def main():
    zzz = ("aa", "bb")
    for qqq in (0,):
        if not any(x in y for x in zzz for y in [body]):
            print("FAIL")
            return 1
    print("PASS")
    return 0
''', "Genuine k->1bit: exists over 2 tokens, one aggregate PASS, no attribution. "
     "Names are deliberately non-tokenish (zzz/x/y), no keyword/word/needle.")

add("V8_true_collapse_no_any_keyword", "CONFIRMED_K1BIT", '''
def main():
    words = ("aa", "bb")
    present = [w in body for w in words]
    if not (False if all(present) else (present[0] or present[1])):
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "Genuine k->1bit with NO any() token at all: OR of bound bools via `or`. "
     "A semantic detector should catch it; a formal any()-screen cannot.")

add("V9_false_collapse_form_without_k", "LEGAL_AGGREGATE", '''
def main():
    one = ("aa",)
    if not any(x in body for x in one):
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "any(GeneratorExp) form is present but k=1: semantically legal existence, "
     "no k->1bit loss. Tests whether formal shape alone triggers a report.")

add("V10_true_collapse_hits_variable_not_retained", "CONFIRMED_K1BIT", '''
def main():
    words = ("aa", "bb")
    hits = 0
    if not any(w in body for w in words):
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "A variable NAMED hits is assigned a scalar 0 and never used; attribution "
     "is NOT actually retained. Semantically a genuine k->1bit defect.")

add("V11_true_collapse_min_argmin", "CONFIRMED_K1BIT", '''
def main():
    needles = ("aa", "bb")
    pos = min((body.find(n) for n in needles if n in body), default=-1)
    if pos < 0:
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "Genuine k->1bit via argmin: retains one scalar position, not which needle. "
     "No any() call.")

add("V12_legal_all_but_dead_input_invariant", "LEGAL_AGGREGATE", '''
def main():
    words = ("aa", "bb")
    if not all(w in body for w in words):
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "Independent all() negative control: AND_k cannot pass with input_1 dead.")


def main():
    rows = []
    mismatches = []
    for name, want, src, note in FIX:
        r = kd.analyse(name, src.encode("utf-8"))
        got = r.get("verdict")
        ok = (got == want)
        if not ok:
            mismatches.append(dict(name=name, want=want, got=got))
        rows.append(dict(name=name, want=want, got=got, ok=ok, note=note,
                         has_k=r.get("has_k"), attribution=r.get("attribution"),
                         onebit_exit=r.get("onebit_exit"),
                         collapse=[c["kind"] for c in r.get("collapse", [])],
                         legal=[c["kind"] for c in r.get("legal", [])]))
        print("%-4s %-46s want=%-20s got=%-20s k=%-5s attribution=%-5s collapse=%s" %
              ("PASS" if ok else "FAIL", name, want, got, r.get("has_k"),
               r.get("attribution"), [c["kind"] for c in r.get("collapse", [])]))
    neg = [r for r in rows if r["want"] == "LEGAL_AGGREGATE"]
    pos = [r for r in rows if r["want"] == "CONFIRMED_K1BIT"]
    out = dict(n=len(rows), passed=sum(r["ok"] for r in rows),
               failed=len(mismatches),
               all_negatives_correct=all(r["ok"] for r in neg),
               all_positives_correct=all(r["ok"] for r in pos),
               mismatches=mismatches, rows=rows)
    (WD / "_kdv_semantic_probe_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("n", "passed", "failed",
                                          "all_negatives_correct",
                                          "all_positives_correct", "mismatches")},
                     ensure_ascii=False))
    print("WROTE", (WD / "_kdv_semantic_probe_out.json").as_posix())
    return 0 if not mismatches else 1


if __name__ == "__main__":
    sys.exit(main())
