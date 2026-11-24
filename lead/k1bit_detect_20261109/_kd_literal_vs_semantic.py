# -*- coding: utf-8 -*-
"""_kd_literal_vs_semantic.py -- quantify literal-vs-semantic gap on 173 files.

Read-only over the repo.  Loads _kd_detect_out.json (semantic verdicts) and
re-implements THREE literal screens over the SAME 173 file bytes:

  L1  GENERATOR_FORM  = raw regex  any\\([^)]*for[^)]*in   -- the exact
      regex quoted in the task background (the one that missed d28)
  L2  ORCH_ANY_LINE   = _cf_census.py:55-59 orch_any_line       # narrow census
      predicate (single line: "any(" + " for " + two " in ")
  L3  BROAD_ANY_PASS  = raw regex  \\bany\\s*\\(  AND  ^\\s*print\\(.*PASS
      -- _cfv wide literal screen (CHECK_FAMILY_LINEAGE.md:329 -> 54 files)

Reference (ground truth) = semantic CONFIRMED_K1BIT set from _kd_detect.py,
which was verified byte-identical to _cf_detect_out.json:confirmed (40).

Outputs _kd_literal_vs_semantic_out.json + prints confusion matrices.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(
    "D:/Project/ra2-campaign-forge")
WD = ROOT / "lead/k1bit_detect_20261109"
LIST = ROOT / "lead/check_family_20261109/_cf_filelist.txt"

rels = []
for ln in LIST.read_text(encoding="utf-8").splitlines():
    t = ln.strip()
    if t:
        rels.append(t[2:] if t.startswith("./") else t)

L1 = re.compile(r"any\([^)]*for[^)]*in")
L3_ANY = re.compile(r"\bany\s*\(")
L3_PASS = re.compile(r"^\s*print\(.*PASS")


def orch_any_line(s):
    if "any(" not in s or " for " not in s:
        return False
    head, _, tail = s.partition(" for ")
    return " in " in head and " in " in tail


def screens(text, lines):
    return dict(
        L1_GENERATOR_FORM=bool(L1.search(text)),
        L2_ORCH_ANY_LINE=any(orch_any_line(s.strip()) for s in lines),
        L3_BROAD_ANY_PASS=(bool(L3_ANY.search(text)) and
                           any(L3_PASS.match(s) for s in lines)),
    )


def confusion(truth, pred):
    tp = len(truth & pred)
    fn = len(truth - pred)          # literal FALSE NEGATIVES (misses)
    fp = len(pred - truth)          # literal FALSE POSITIVES (false alarms)
    tn = len(set(rels) - truth - pred)
    return dict(tp=tp, fn=fn, fp=fp, tn=tn,
                recall=(tp / (tp + fn)) if tp + fn else None,
                precision=(tp / (tp + fp)) if tp + fp else None,
                fn_rate=(fn / (tp + fn)) if tp + fn else None,
                fp_rate=(fp / (tp + fp)) if tp + fp else None)


def main():
    sem = json.loads((WD / "_kd_detect_out.json").read_text(encoding="utf-8"))
    truth = set(sem["confirmed"])
    rows = []
    for rel in rels:
        p = ROOT / rel
        raw = p.read_bytes() if p.is_file() else b""
        text = raw.decode("utf-8-sig", errors="replace")
        sc = screens(text, text.splitlines())
        rows.append(dict(rel=rel, truth=rel in truth, **sc))
    res = dict(n=len(rows), n_truth=len(truth),
               n_semantic_confirmed=len(truth),
               n_semantic_suspect=len(sem["suspect"]),
               screens={}, rows=rows)
    for k in ("L1_GENERATOR_FORM", "L2_ORCH_ANY_LINE", "L3_BROAD_ANY_PASS"):
        pred = {r["rel"] for r in rows if r[k]}
        c = confusion(truth, pred)
        c["n_hits"] = len(pred)
        c["misses_confirmed"] = sorted(truth - pred)
        c["false_positives"] = sorted(pred - truth)
        res["screens"][k] = c
    # the four production gates under each screen
    four = ["lead/d27_ruling_20261106/check_d27.py",
            "lead/d28_ruling_20261106/check_d28.py",
            "lead/d29_ruling_20261106/check_d29.py",
            "lead/d30_ruling_20261106/check_d30.py"]
    by = {r["rel"]: r for r in rows}
    res["four"] = {f: {k: by[f][k] for k in
                       ("truth", "L1_GENERATOR_FORM", "L2_ORCH_ANY_LINE",
                        "L3_BROAD_ANY_PASS")} for f in four}
    # narrow census combos from the existing census output (independent source)
    cen = json.loads((ROOT / "lead/check_family_20261109/_cf_census_out.json")
                     .read_text(encoding="utf-8"))
    s = cen["summary"]
    res["census_combos"] = dict(
        n_combo_orchany_passliteral=s["n_combo_orchany_passliteral"],
        n_combo_orchany_passprint=s["n_combo_orchany_passprint"],
        n_combo_wordor_passprint=s["n_combo_wordor_passprint"],
        n_orch_any=s["n_orch_any"], n_any_gen=s["n_any_gen"],
        n_any_word_or=s["n_any_word_or"], n_pass_print=s["n_pass_print"])
    (WD / "_kd_literal_vs_semantic_out.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(dict(n=res["n"], n_truth=res["n_truth"],
                          screens={k: {x: v[x] for x in
                                       ("n_hits", "tp", "fn", "fp", "tn",
                                        "fn_rate", "fp_rate")}
                                   for k, v in res["screens"].items()},
                          four=res["four"], census_combos=res["census_combos"]),
                     ensure_ascii=False, indent=1))
    for k, v in res["screens"].items():
        print("MISS", k, "=", v["misses_confirmed"])
    print("WROTE", (WD / "_kd_literal_vs_semantic_out.json").as_posix())


if __name__ == "__main__":
    main()
