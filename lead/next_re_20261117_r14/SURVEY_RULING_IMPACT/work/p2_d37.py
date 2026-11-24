# -*- coding: utf-8 -*-
"""p2 = item 1 (D-37).  Is S13's 92-row container-template block re-attributable to S22?

Rule used (and its control)
  A row is a "container template instantiation" iff its `name` contains one of the
  container-template class tokens anywhere in the string. The three on-disk spellings
  are all covered by that single test:
      VectorClass<BombClass*>::SetCapacity          (readable)
      ?$VectorClass::PAVBombClass:::vslot2          (mangled)
      T_VectorClass_PAVBulletClass__::slot1         (README class_to_sub spelling)
  Tokens: VectorClass, DynamicVectorClass, TClassFactory, VectorCursor
  ("VectorClass" is a substring of "DynamicVectorClass"/"T_VectorClass...", so the
   token list is kept explicit anyway to keep the rule auditable.)

CONTROL (positive): on S13 this rule yields exactly 92 rows - the same count
  a-S13-K4 reports - and 14 of them are `[已证]`, so 89 - 14 = 75, which is the
  number the task asserts. The rule is therefore the one that reproduces the claim.

Outputs: EVIDENCE/p2_d37_{s13, census}.tsv , p2_d37.json
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_survey as L

CONTAINER_TOKENS = ["VectorClass", "DynamicVectorClass", "TClassFactory", "VectorCursor"]


def is_container_tpl(name):
    return any(t in name for t in CONTAINER_TOKENS)


def denom_view(rows):
    """n / named / strict / proved for an arbitrary row set."""
    n = len(rows)
    named_L = sum(1 for r in rows if L.named_L(r["name"]))
    named_S = sum(1 for r in rows if L.named_S_r14(r["name"]))
    strict = sum(1 for r in rows if L.named_S_strict(r["name"]))
    proved = sum(1 for r in rows if r["grade"] == L.G_PROVED)
    tn, tp = L.ceil90(n), L.ceil50(n)
    return {"n": n, "named_L": named_L, "named_S": named_S, "named_strict": strict,
            "proved": proved, "thr_named": tn, "thr_proved": tp,
            "pass_named_A": named_S >= tn, "pass_named_B": strict >= tn,
            "pass_proved": proved >= tp,
            "pass_both_A": (named_S >= tn) and (proved >= tp),
            "pass_both_B": (strict >= tn) and (proved >= tp),
            "named_pct_A": round(100.0 * named_S / n, 2) if n else 0.0,
            "proved_pct": round(100.0 * proved / n, 2) if n else 0.0}


rows = L.load_coverage()
atlas, _ = L.load_atlas_entries()
aset = set(atlas)
in_atlas = [r for r in rows if r["entry"] in aset]

# ---------------- S13: 240 vs 148 ----------------
s13 = [r for r in in_atlas if r["sub"] == "S13"]
tpl = [r for r in s13 if is_container_tpl(r["name"])]
rest = [r for r in s13 if not is_container_tpl(r["name"])]

v240 = denom_view(s13)
v148 = denom_view(rest)

s13_lines = ["entry\tname\tgrade\tnamed_S\tnamed_strict\tcontainer_token"]
for r in sorted(tpl, key=lambda x: x["entry"]):
    tok = [t for t in CONTAINER_TOKENS if t in r["name"]]
    s13_lines.append("\t".join([r["entry"], r["name"], r["grade"],
                                str(L.named_S_r14(r["name"])), str(L.named_S_strict(r["name"])),
                                "/".join(tok)]))
L.wl(os.path.join(L.EV, "p2_d37_s13_92rows.tsv"), s13_lines)

# ---------------- full-table census ----------------
census = []
for s in L.SUBS_ALL:
    sub_rows = [r for r in in_atlas if r["sub"] == s]
    if not sub_rows:
        continue
    t = [r for r in sub_rows if is_container_tpl(r["name"])]
    kept = [r for r in sub_rows if not is_container_tpl(r["name"])]
    now = denom_view(sub_rows)
    if t:
        after = denom_view(kept)
    else:
        after = dict(now)
    census.append({"sub": s, "tpl_rows": len(t),
                   "tpl_proved": sum(1 for r in t if r["grade"] == L.G_PROVED),
                   "tpl_named_S": sum(1 for r in t if L.named_S_r14(r["name"])),
                   "tpl_named_strict": sum(1 for r in t if L.named_S_strict(r["name"])),
                   "now": now, "after_migrate": after})

# who would newly pass if ALL such rows left their subsystem?
newly = [c["sub"] for c in census if c["tpl_rows"] > 0
         and c["after_migrate"]["pass_both_A"] and not c["now"]["pass_both_A"]]

chan = ["sub\ttpl_rows\ttpl_proved\ttpl_named_S\ttpl_named_strict\tn_now\tn_after\tproved_now\tproved_after\tnamedS_now\tnamedS_after\tthr_named_after\tthr_proved_after\tpass_now_A\tpass_after_A"]
for c in census:
    chan.append("\t".join(str(x) for x in [
        c["sub"], c["tpl_rows"], c["tpl_proved"], c["tpl_named_S"], c["tpl_named_strict"],
        c["now"]["n"], c["after_migrate"]["n"], c["now"]["proved"], c["after_migrate"]["proved"],
        c["now"]["named_S"], c["after_migrate"]["named_S"],
        c["after_migrate"]["thr_named"], c["after_migrate"]["thr_proved"],
        c["now"]["pass_both_A"], c["after_migrate"]["pass_both_A"]]))
L.wl(os.path.join(L.EV, "p2_d37_census.tsv"), chan)

res = {
    "rule": CONTAINER_TOKENS,
    "rule_control": "S13 rule hit count 92 (== a-S13-K4 claim); proved among them 14 => 89-14=75",
    "S13_240": v240, "S13_148": v148,
    "S13_tpl_rows": len(tpl),
    "S13_tpl_proved": sum(1 for r in tpl if r["grade"] == L.G_PROVED),
    "S13_tpl_named_S": sum(1 for r in tpl if L.named_S_r14(r["name"])),
    "S13_tpl_named_strict": sum(1 for r in tpl if L.named_S_strict(r["name"])),
    "census": census,
    "newly_passing_if_migrated": newly,
}
L.w(os.path.join(L.EV, "p2_d37.json"), json.dumps(res, ensure_ascii=False, indent=1))

print("S13 container-template rows:", len(tpl), " proved:", res["S13_tpl_proved"],
      " named_S:", res["S13_tpl_named_S"], " strict:", res["S13_tpl_named_strict"])
print()
for tag, v in (("240", v240), ("148", v148)):
    print("%s-denom: n=%d named_S=%d (%.2f%%, thr %d, pass=%s) strict=%d(thr %d,pass=%s) "
          "proved=%d (%.2f%%, thr %d, pass=%s) => BOTH(A)=%s BOTH(B)=%s"
          % (tag, v["n"], v["named_S"], v["named_pct_A"], v["thr_named"], v["pass_named_A"],
             v["named_strict"], v["thr_named"], v["pass_named_B"],
             v["proved"], v["proved_pct"], v["thr_proved"], v["pass_proved"],
             v["pass_both_A"], v["pass_both_B"]))
print()
print("census (subsystems holding container-template rows):")
for c in census:
    if c["tpl_rows"]:
        print("  %s tpl=%2d (proved %d, namedS %d)  n %d->%d  proved %d->%d  namedS %d->%d  pass %s->%s"
              % (c["sub"], c["tpl_rows"], c["tpl_proved"], c["tpl_named_S"],
                 c["now"]["n"], c["after_migrate"]["n"],
                 c["now"]["proved"], c["after_migrate"]["proved"],
                 c["now"]["named_S"], c["after_migrate"]["named_S"],
                 c["now"]["pass_both_A"], c["after_migrate"]["pass_both_A"]))
print("newly passing if migrated:", newly)
