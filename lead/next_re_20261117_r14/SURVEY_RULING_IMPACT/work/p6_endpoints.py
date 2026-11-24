# -*- coding: utf-8 -*-
"""p6_endpoints: the K8/K9 per-row evidence, the two D-37(B) scope variants, and the
endpoint totals that go into PROGRESS.md.

The only value that is not mine is the ③b availability rate; it is NOT used in any
computation here, it is quoted (with provenance) only to mark how far a ceiling is from
an expectation. No ceiling in this card assumes ③b holds in practice.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_survey as L

D4 = json.load(open(os.path.join(L.EV, "p4_rings.json"), encoding="utf-8"))
D5 = json.load(open(os.path.join(L.EV, "p5_scenarios.json"), encoding="utf-8"))
M = D4["matrix"]
subs = [s for s in L.SUBS_ALL if s != "S22"]

# ---------------- K8 / K9 per-row evidence ----------------
WIT = json.load(open(os.path.join(L.EV, "p3_slot_witness.json"), encoding="utf-8"))["witness"]
lines = ["entry\ton_disk_grade\ton_disk_name\thas_slot\t4wide\t4strict\tdirect\t"
         "witness_tables(vt:verdict:slot:disp)"]
for grp, rows in (("K8", D4["K8_18"]), ("K9", D4["K9_delta"])):
    for x in rows:
        ws = WIT.get(x["entry"], [])
        desc = ";".join("%s:%s:%d:%d" % (w["vt"], w["verdict"], w["slot"], w["off"] + 4 * w["slot"])
                        for w in ws[:4]) or "-"
        lines.append("\t".join([x["entry"], grp, str(x["on_disk_grade"]), x.get("on_disk_name", ""),
                                str(x["has_slot"]), str(x["wide"]), str(x["strict"]),
                                str(x["direct"]), desc]))
L.wl(os.path.join(L.EV, "p6_K8_K9_rows.tsv"), lines)

# ---------------- D-37(B) scope variants ----------------
def variant(migrate_subs):
    """recompute passes when migration is applied only to the named subsystems"""
    out = {}
    for s in subs:
        base = M[s]["baseline"]
        mig = M[s]["D37B"]
        st = mig if s in migrate_subs else base
        if st is None:
            continue
        # under ALL, proved ceiling = proved + both reliefs
        p_ceil = st["ceil_ALL"]
        p_floor = st["proved"]
        named = st["named"]
        out[s] = {"proved_floor": p_floor, "proved_ceil": p_ceil, "named": named,
                  "thr_p": st["thr_proved"], "thr_n": st["thr_named"],
                  "pass_floor": named >= st["thr_named"] and p_floor >= st["thr_proved"],
                  "pass_ceil": named >= st["thr_named"] and p_ceil >= st["thr_proved"]}
    return out


def tpl_holders():
    return sorted([s for s in subs if M[s]["n_migrated_out"] > 0])


v_s13 = variant({"S13"})
v_all = variant(set(tpl_holders()))

res = {
    "endpoints": {
        "no_ruling_floor_and_ceil": sorted([s for s in subs if D5[s]["now_pass"]]),
        "all_rulings_floor": sorted([s for s in subs if D5[s]["all_pass_floor"]]),
        "all_rulings_ceil": sorted([s for s in subs if D5[s]["all_pass_ceil"]]),
        "all_rulings_with_S13_only_migration_ceil": sorted([s for s, v in v_s13.items() if v["pass_ceil"]]),
        "all_rulings_with_full_migration_ceil": sorted([s for s, v in v_all.items() if v["pass_ceil"]]),
    },
    "d37_scope": {"subsystems_holding_templates": tpl_holders(),
                  "n_tpl_rows_outside_S22": sum(M[s]["n_migrated_out"] for s in subs)},
    "variant_S13_only": v_s13,
    "variant_full": v_all,
}
L.w(os.path.join(L.EV, "p6_endpoints.json"), json.dumps(res, ensure_ascii=False, indent=1))

print("no ruling        :", res["endpoints"]["no_ruling_floor_and_ceil"])
print("ALL rulings floor:", res["endpoints"]["all_rulings_floor"])
print("ALL rulings ceil :", res["endpoints"]["all_rulings_ceil"])
print("ALL + S13-only migration (ceil):",
      res["endpoints"]["all_rulings_with_S13_only_migration_ceil"])
print("ALL + full migration      (ceil):",
      res["endpoints"]["all_rulings_with_full_migration_ceil"])
print()
print("template holders:", res["d37_scope"]["subsystems_holding_templates"])
print("template rows outside S22:", res["d37_scope"]["n_tpl_rows_outside_S22"])
print()
print("S13-only migration effect per subsystem (named after migration):")
for s in subs:
    if M[s]["n_migrated_out"]:
        b, a = M[s]["baseline"], M[s]["D37B"]
        print("  %-4s n %4d->%4d  named %4d->%4d  thr_n %4d->%4d  proved %4d->%4d  pass %s->%s"
              % (s, b["n"], a["n"], b["named"], a["named"], b["thr_named"], a["thr_named"],
                 b["proved"], a["proved"],
                 "Y" if b["pass_now"] else "n", "Y" if a["pass_now"] else "n"))
