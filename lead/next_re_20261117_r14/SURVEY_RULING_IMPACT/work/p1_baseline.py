# -*- coding: utf-8 -*-
"""p1: baseline recomputation (no ruling applied).

Purpose
  1. Method self-check: with no ruling applied the pipeline must reproduce exactly the
     3 passing subsystems the task states (S15/S16/S17). If it does not, every later
     number in this card is wrong and the card must fail.
  2. Produce the per-subsystem A-denominator table that all six items are keyed on.

Outputs (UTF-8):
  EVIDENCE/p1_baseline.json
  EVIDENCE/p1_baseline.tsv
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_survey as L

rows = L.load_coverage()
atlas, amet = L.load_atlas_entries()
aset = set(atlas)

ctrls = {
    "coverage_rows": len(rows),
    "coverage_rows_unique_entry": len(set(r["entry"] for r in rows)),
    "atlas_rows": len(atlas),
    "atlas_unique": len(aset),
    "intersection": sum(1 for r in rows if r["entry"] in aset),
    "grade_counts_all": {}
}
for g, cn in [(L.G_PROVED, "proved"), (L.G_STATIC, "static"), (L.G_UNPROV, "unproved")]:
    ctrls["grade_counts_all"][cn] = sum(1 for r in rows if r["grade"] == g)
ctrls["grade_counts_grade_total"] = sum(ctrls["grade_counts_all"].values())

st = L.subsystem_stats(rows, aset)

table = []
for s in L.SUBS_ALL:
    d = st.get(s)
    if d is None:
        continue
    n = d["atlas_n"]
    tn, tp = L.ceil90(n), L.ceil50(n)
    okn_A, okp = (d["named_S"] >= tn), (d["proved"] >= tp)   # D-38 (A): slotN counts
    okn_B = (d["named_strict"] >= tn)                        # D-38 (B): slotN excluded
    table.append({
        "sub": s, "atlas_n": n,
        "named_L": d["named_L"], "named_S_r14": d["named_S"], "named_S_strict": d["named_strict"],
        "proved": d["proved"], "static": d["static"], "unproved": d["unproved"],
        "thr_named": tn, "thr_proved": tp,
        "pass_named_A": okn_A, "pass_named_B": okn_B, "pass_proved": okp,
        "pass_both_A": okn_A and okp, "pass_both_B": okn_B and okp,
        "proved_gap": max(0, tp - d["proved"]),
        "named_gap_A": max(0, tn - d["named_S"]),
        "named_gap_B": max(0, tn - d["named_strict"]),
    })

tot = {
    "atlas_n": sum(t["atlas_n"] for t in table),
    "named_L": sum(t["named_L"] for t in table),
    "named_S_r14": sum(t["named_S_r14"] for t in table),
    "named_S_strict": sum(t["named_S_strict"] for t in table),
    "proved": sum(t["proved"] for t in table),
}
# S22 must NOT enter % rankings (9.1); report separately.
s22 = [t for t in table if t["sub"] == "S22"][0]

pass_A = [t["sub"] for t in table if t["sub"] != "S22" and t["pass_both_A"]]
pass_B = [t["sub"] for t in table if t["sub"] != "S22" and t["pass_both_B"]]
pass_named_only_A = [t["sub"] for t in table if t["sub"] != "S22" and t["pass_named_A"]]
pass_proved_only = [t["sub"] for t in table if t["sub"] != "S22" and t["pass_proved"]]

res = {
    "controls": ctrls,
    "denominators": {"A": len(aset), "B_note": "14487 (not used for %)", "C": len(rows)},
    "table": table,
    "total_excl_S22": tot,
    "S22": s22,
    "baseline_pass_both_A": pass_A,
    "baseline_pass_both_B": pass_B,
    "baseline_pass_named_only_A": pass_named_only_A,
    "baseline_pass_proved_only": pass_proved_only,
    "selfcheck_expected_3": ["S15", "S16", "S17"],
    "selfcheck_ok": sorted(pass_A) == ["S15", "S16", "S17"],
}

os.makedirs(L.EV, exist_ok=True)
L.w(os.path.join(L.EV, "p1_baseline.json"), json.dumps(res, ensure_ascii=False, indent=1))

hdr = ["sub", "atlas_n", "named_L", "named_S_r14", "named_S_strict", "proved", "static", "unproved",
       "thr_named", "thr_proved", "pass_named_A", "pass_named_B", "pass_proved", "pass_both_A",
       "pass_both_B", "named_gap_A", "named_gap_B", "proved_gap"]
lines = ["\t".join(hdr)]
for t in table:
    lines.append("\t".join(str(t[k]) for k in hdr))
lines.append("\t".join(["TOTAL_21"] + [str(tot[k]) for k in
                                        ["atlas_n", "named_L", "named_S_r14", "named_S_strict", "proved"]]
                        + ["", "", "", "", "", "", "", "", ""]))
L.wl(os.path.join(L.EV, "p1_baseline.tsv"), lines)

# ---- console (ASCII only; cp936 console) ----
print("CONTROLS:", json.dumps(ctrls, ensure_ascii=False))
print("atlas A =", len(aset), " coverage C =", len(rows))
print("total atlas-intersect rows =", tot["atlas_n"])
print("total proved =", tot["proved"], " named_S_r14 =", tot["named_S_r14"],
      " named_strict =", tot["named_S_strict"])
print("PASS_BOTH_A(D-38 A) =", pass_A)
print("PASS_BOTH_B(D-38 B) =", pass_B)
print("SELFCHECK ok =", res["selfcheck_ok"])
print()
print("%-4s %6s %6s %6s %6s %6s %5s %5s  %s" %
      ("sub", "n", "namL", "namS", "namStr", "prov", "thN", "thP", "passA/okN_A/okP"))
for t in table:
    print("%-4s %6d %6d %6d %6d %6d %5d %5d  %s" %
          (t["sub"], t["atlas_n"], t["named_L"], t["named_S_r14"], t["named_S_strict"],
           t["proved"], t["thr_named"], t["thr_proved"],
           ("BOTH" if t["pass_both_A"] else ("named" if t["pass_named_A"] else "")) +
           ("/" + str(t["pass_named_A"]) + "/" + str(t["pass_proved"]))))
