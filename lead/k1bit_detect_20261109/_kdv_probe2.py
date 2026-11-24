# -*- coding: utf-8 -*-
"""_kdv_probe2.py -- isolate name-level vs dataflow-level decisions.

Each pair differs ONLY in identifier names (semantics identical).  This tests
whether _kd_detect.py's S1 KSOURCE is real dataflow or a name heuristic.
"""
import importlib.util
import json
import sys
from pathlib import Path

WD = Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location("_kd_p2", WD / "_kd_detect.py")
kd = importlib.util.module_from_spec(sp)
sp.loader.exec_module(kd)


def src(assign_name, loopvar, bodyvar, k, use_any=True):
    toks = ", ".join('"t%d"' % i for i in range(k))
    if use_any:
        collapse = "any(%s in %s for %s in %s)" % (loopvar, bodyvar, loopvar, assign_name)
    else:
        collapse = "all(%s in %s for %s in %s)" % (loopvar, bodyvar, loopvar, assign_name)
    return ("def main():\n"
            "    %s = (%s)\n"
            "    body = \"t0 t1\"\n"
            "    if not %s:\n"
            "        print(\"FAIL\")\n"
            "        return 1\n"
            "    print(\"PASS\")\n"
            "    return 0\n" % (assign_name, toks, collapse))


CASES = [
    # name, want (semantic truth), source, note
    ("A_tokenish_name_k2_true", "CONFIRMED_K1BIT",
     src("words", "w", "body", 2), "k=2 genuine OR collapse, tokenish name 'words'"),
    ("B_neutral_name_k2_true", "CONFIRMED_K1BIT",
     src("zzz", "x", "body", 2), "SAME semantics, neutral name 'zzz'"),
    ("C_tokenish_name_k1_legal", "LEGAL_AGGREGATE",
     src("words", "w", "body", 1), "k=1 legal existence, tokenish name 'words'"),
    ("D_neutral_name_k1_legal", "LEGAL_AGGREGATE",
     src("zzz", "x", "body", 1), "SAME semantics, neutral name 'zzz'"),
    ("E_tokenish_name_k2_all_legal", "LEGAL_AGGREGATE",
     src("words", "w", "body", 2, use_any=False), "k=2 legal AND_k, tokenish name"),
    ("F_neutral_name_k2_all_legal", "LEGAL_AGGREGATE",
     src("zzz", "x", "body", 2, use_any=False), "SAME legal AND_k, neutral name"),
    ("G_hits_scalar_name_suppresses", "CONFIRMED_K1BIT",
     "def main():\n"
     "    words = (\"aa\", \"bb\")\n"
     "    hits = 0\n"
     "    if not any(w in body for w in words):\n"
     "        print(\"FAIL\")\n"
     "        return 1\n"
     "    print(\"PASS\")\n"
     "    return 0\n",
     "Genuine defect; a scalar variable merely NAMED hits suppresses via name regex"),
    ("H_hits_scalar_neutral_name", "CONFIRMED_K1BIT",
     "def main():\n"
     "    words = (\"aa\", \"bb\")\n"
     "    counter = 0\n"
     "    if not any(w in body for w in words):\n"
     "        print(\"FAIL\")\n"
     "        return 1\n"
     "    print(\"PASS\")\n"
     "    return 0\n",
     "Same genuine defect, neutral counter name"),
]


def main():
    rows = []
    for name, want, s, note in CASES:
        r = kd.analyse(name, s.encode("utf-8"))
        rows.append(dict(name=name, want=want, got=r["verdict"],
                         ok=r["verdict"] == want, note=note,
                         has_k=r["has_k"], attribution=r["attribution"],
                         tokens=r.get("tokens"),
                         collapse=[c["kind"] for c in r["collapse"]]))
        print("%-4s %-32s want=%-20s got=%-20s has_k=%-5s attr=%-5s %s" %
              ("PASS" if r["verdict"] == want else "FAIL", name, want,
               r["verdict"], r["has_k"], r["attribution"],
               [c["kind"] for c in r["collapse"]]))
    out = dict(n=len(rows), passed=sum(r["ok"] for r in rows),
               failed=[r["name"] for r in rows if not r["ok"]], rows=rows)
    (WD / "_kdv_probe2_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("n", "passed", "failed")}, ensure_ascii=False))
    return 0 if out["passed"] == out["n"] else 1


if __name__ == "__main__":
    sys.exit(main())
