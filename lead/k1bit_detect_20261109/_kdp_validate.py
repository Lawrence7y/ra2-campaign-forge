# -*- coding: utf-8 -*-
"""_kdp_validate.py -- validate the corrected pasteable detector in K1BIT_DETECTOR.md.

Runs the exact fixtures the review used to break _kd_detect.py (partial verdict),
plus the four gates, carrier scan, and the runnable legal all() fixture.
All fixtures are in-memory source strings (except reading repo files); no
inspected script is executed.  Writes only _kdp_validate_out.json here.
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("D:/Project/ra2-campaign-forge")
WD = ROOT / "lead/k1bit_detect_20261109"
sp = importlib.util.spec_from_file_location("_kdp", WD / "_kd_pasteable.py")
kp = importlib.util.module_from_spec(sp)
sp.loader.exec_module(kp)

FIX = []

def add(name, want, src, note):
    FIX.append((name, want, src, note))


# ---- the four review failures (independent fixtures, _kdv_semantic_probe.py) ----
add("V7_true_collapse_renamed", "CONFIRMED_K1BIT", '''
def main():
    zzz = ("aa", "bb")
    for qqq in (0,):
        if not any(x in y for x in zzz for y in [body]):
            print("FAIL")
            return 1
    print("PASS")
    return 0
''', "genuine k->1bit, all identifiers non-tokenish")
add("V8_true_collapse_no_any_keyword", "CONFIRMED_K1BIT", '''
def main():
    words = ("aa", "bb")
    present = [w in body for w in words]
    if not (False if all(present) else (present[0] or present[1])):
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "genuine k->1bit with no any() token at all")
add("V10_hits_scalar_not_retained", "CONFIRMED_K1BIT", '''
def main():
    words = ("aa", "bb")
    hits = 0
    if not any(w in body for w in words):
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "a scalar named hits is NOT attribution")
add("V11_min_argmin", "CONFIRMED_K1BIT", '''
def main():
    needles = ("aa", "bb")
    pos = min((body.find(n) for n in needles if n in body), default=-1)
    if pos < 0:
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "argmin reverse masking, no any() call")

# ---- the three name-invariance failures (_kdv_probe2.py) ----
def pair(assign, loopvar, k, use_any=True):
    toks = ", ".join('"t%d"' % i for i in range(k))
    collapse = "%s(%s in body for %s in %s)" % (
        "any" if use_any else "all", loopvar, loopvar, assign)
    return ("def main():\n"
            "    %s = (%s)\n"
            "    body = \"t0 t1\"\n"
            "    if not %s:\n"
            "        print(\"FAIL\")\n"
            "        return 1\n"
            "    print(\"PASS\")\n"
            "    return 0\n" % (assign, toks, collapse))

add("A_words_k2_true", "CONFIRMED_K1BIT", pair("words", "w", 2), "tokenish name")
add("B_zzz_k2_true", "CONFIRMED_K1BIT", pair("zzz", "x", 2), "SAME semantics neutral name")
add("C_words_k1_legal", "LEGAL_AGGREGATE", pair("words", "w", 1), "k=1 legal existence")
add("D_zzz_k1_legal", "LEGAL_AGGREGATE", pair("zzz", "x", 1), "SAME semantics neutral name")
add("E_words_k2_all", "LEGAL_AGGREGATE", pair("words", "w", 2, False), "legal AND_k")
add("F_zzz_k2_all", "LEGAL_AGGREGATE", pair("zzz", "x", 2, False), "legal AND_k renamed")
add("G_hits_scalar_name_suppresses", "CONFIRMED_K1BIT", '''
def main():
    words = ("aa", "bb")
    hits = 0
    if not any(w in body for w in words):
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "name 'hits' must not suppress")
add("H_hits_scalar_neutral_name", "CONFIRMED_K1BIT", '''
def main():
    words = ("aa", "bb")
    counter = 0
    if not any(w in body for w in words):
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "same genuine defect, neutral name")

# ---- the decisive false positive (_kdv_probe3.py) ----
add("probe3_legal_k1_plus_unrelated_accum", "LEGAL_AGGREGATE", '''
def main():
    cases = ["doc1", "doc2"]
    ok = True
    good = (1 == 1)
    ok &= good
    if not any("FIXED" in case for case in cases):
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "k=1 legal existence over samples; unrelated &= must not force CONFIRMED")

# ---- legal negative controls ----
add("N1_all_AND_over_k_tokens", "LEGAL_AGGREGATE", '''
def main():
    words = ("A", "B")
    if not all(w in body for w in words):
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "AND_k legal")
add("N2_any_over_samples_single_literal", "LEGAL_AGGREGATE", '''
def main():
    bodies = ["a", "b"]
    if not any("FIXED" in b for b in bodies):
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "single fixed literal over samples")
add("N3_per_token_attribution", "LEGAL_AGGREGATE", '''
def main():
    words = ("A", "B")
    hits = {}
    for w in words:
        hits[w] = w in body
        print("PER_TOKEN %s %s" % (w, hits[w]))
    if not any(w in body for w in words):
        print("FAIL")
        return 1
    print("PASS")
    return 0
''', "real indexed store + per-token print")


def main():
    rows = []
    for name, want, src, note in FIX:
        r = kp.analyse(name, src.encode("utf-8"))
        rows.append(dict(name=name, want=want, got=r["verdict"],
                         ok=r["verdict"] == want, has_k=r["has_k"],
                         attribution=r["attribution"],
                         collapse=[c["kind"] for c in r["collapse"]], note=note))
    files = [
        ("lead/d27_ruling_20261106/check_d27.py", "CONFIRMED_K1BIT"),
        ("lead/d28_ruling_20261106/check_d28.py", "CONFIRMED_K1BIT"),
        ("lead/d29_ruling_20261106/check_d29.py", "CONFIRMED_K1BIT"),
        ("lead/d30_ruling_20261106/check_d30.py", "CONFIRMED_K1BIT"),
        ("lead/refsync_scope_20261109/_rs_carrier_scan.py", "CONFIRMED_K1BIT"),
        ("lead/d26_ruling_20261106/check_d26.py", "LEGAL_AGGREGATE"),
        ("lead/k1bit_detect_20261109/_kdv_legal_all.py", "LEGAL_AGGREGATE"),
    ]
    frows = []
    for rel, want in files:
        r = kp.analyse(rel, (ROOT / rel).read_bytes())
        frows.append(dict(rel=rel, want=want, got=r["verdict"],
                          ok=r["verdict"] == want,
                          collapse=[(c["line"], c["kind"]) for c in r["collapse"]]))
    out = dict(n_fixtures=len(rows), passed=sum(x["ok"] for x in rows),
               failed=[x["name"] for x in rows if not x["ok"]],
               n_files=len(frows), files_passed=sum(x["ok"] for x in frows),
               files_failed=[x["rel"] for x in frows if not x["ok"]],
               rows=rows, files=frows)
    (WD / "_kdp_validate_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for x in rows:
        print("%-4s %-40s want=%-20s got=%-20s k=%-5s attr=%-5s" %
              ("PASS" if x["ok"] else "FAIL", x["name"], x["want"], x["got"],
               x["has_k"], x["attribution"]))
    for x in frows:
        print("%-4s %-60s want=%-20s got=%-20s" %
              ("PASS" if x["ok"] else "FAIL", x["rel"], x["want"], x["got"]))
    print(json.dumps({k: out[k] for k in ("n_fixtures", "passed", "failed",
                                          "n_files", "files_passed", "files_failed")},
                     ensure_ascii=False))
    return 0 if not out["failed"] and not out["files_failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
