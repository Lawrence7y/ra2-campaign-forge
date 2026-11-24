# -*- coding: utf-8 -*-
"""p5_matrix: turn the measurement into the decision matrix and the endpoint totals.

For each of the 21 subsystems (S22 excluded from every percentage, R14_COMMON 9.1) and
each ruling scenario, report proved / named / pass. `proved` for a ruling is a CEILING
(③b granted for free on every eligible row) and the header says so; the floor is the
on-disk value, because no ruling changes a grade by itself.

Scenarios
  现状      no ruling applied (must reproduce S15/S16/S17)
  D-37(B)   container-template rows re-attributed to S22
  D-38(B)   `Class::slotN` / `::vslotN` do NOT count as named
  D-39(A)   virtual dispatch suffices for ring ④ (③④ merged)
  D-41(B)   identity substitution for ring ② when the function has no vtable
  ④宽读法    evaluation lens: ring ④ reachable under the WIDE reading
  全裁      D-37(B) + D-38(A) + D-39(A) + D-41(B)
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_survey as L

D = json.load(open(os.path.join(L.EV, "p4_rings.json"), encoding="utf-8"))
M = D["matrix"]
subs = [s for s in L.SUBS_ALL if s != "S22"]


def cell(st, proved=None):
    """(proved value, named value, pass) for one scenario."""
    if st is None:
        return ("", "", "")
    p = st["proved"] if proved is None else proved
    named = st["named"]
    ok = (named >= st["thr_named"]) and (p >= st["thr_proved"])
    return (p, named, "Y" if ok else "n")


rows_out = []
hdr = ["sub", "n_now", "thr_named_now", "thr_proved_now",
       "NOW_proved", "NOW_named", "NOW_pass",
       "D37B_proved", "D37B_named", "D37B_pass",
       "D38B_proved", "D38B_named", "D38B_pass",
       "D39A_proved_ceil", "D39A_named", "D39A_pass_ceil",
       "D41B_proved_ceil", "D41B_named", "D41B_pass_ceil",
       "R4W_proved_ceil", "R4W_named", "R4W_pass_ceil",
       "ALL_proved_floor", "ALL_proved_ceil", "ALL_named",
       "ALL_pass_floor", "ALL_pass_ceil",
       "D37B_n", "D39A_elig", "D41B_elig", "R4W_wide_rows", "R4W_strict_rows"]
rows_out.append("\t".join(hdr))

summary = {}
for s in subs:
    m = M[s]
    b, d37, d38 = m["baseline"], m["D37B"], m["D38B"]
    if b is None:
        continue
    now = cell(b)
    c37 = cell(d37)
    c38 = cell(d38)
    # D-39(A)
    p39 = b["ceil_D39"]
    ok39 = (b["named"] >= b["thr_named"]) and (p39 >= b["thr_proved"])
    # D-41(B)
    p41 = b["ceil_D41"]
    ok41 = (b["named"] >= b["thr_named"]) and (p41 >= b["thr_proved"])
    # ④ wide lens (same eligibility basis as D-39: a live-vtable ④ witness)
    p4w = b["ceil_D39"]
    ok4w = ok39
    # all rulings (migration applied, then both reliefs; named stays S(R14) = D-38(A))
    a = m["ALL"]
    pA = a["ceil_ALL"]
    okA = (a["named"] >= a["thr_named"]) and (pA >= a["thr_proved"])
    okAfloor = (a["named"] >= a["thr_named"]) and (a["proved"] >= a["thr_proved"])
    pool = D["pool_static"].get(s, {})
    # every scenario carries its own proved / named / pass triple.
    #   D-38(B) changes only the named line -> its proved is the on-disk one.
    #   D-39(A) / D-41(B) / ④-wide change only the proved ceiling -> their named is
    #   the on-disk named_S, because the ruling is evaluated under D-38(A).
    #   ALL combines migration (D-37B) with both proved reliefs and D-38(A).
    rows_out.append("\t".join(str(x) for x in [
        s, b["n"], b["thr_named"], b["thr_proved"],
        now[0], now[1], now[2],
        c37[0], c37[1], c37[2],
        b["proved"], c38[1], c38[2],
        p39, b["named"], "Y" if ok39 else "n",
        p41, b["named"], "Y" if ok41 else "n",
        p4w, b["named"], "Y" if ok4w else "n",
        a["proved"], pA, a["named"],
        "Y" if okAfloor else "n", "Y" if okA else "n",
        a["n"], b["elig_D39_open"], b["elig_D41_open"],
        pool.get("wide", ""), pool.get("strict", "")]))
    summary[s] = {
        "now_pass": now[2] == "Y", "now_proved": now[0], "now_named": now[1],
        "d37_pass": c37[2] == "Y", "d38_pass": c38[2] == "Y",
        "d39_pass_ceil": ok39, "d39_ceil": p39, "d39_elig": b["elig_D39_open"],
        "d39_need": b["need_proved"],
        "d41_pass_ceil": ok41, "d41_ceil": p41, "d41_elig": b["elig_D41_open"],
        "all_pass_floor": okAfloor, "all_pass_ceil": okA,
        "named_ok_now": b["named"] >= b["thr_named"],
        "named_ok_after_migrate": a["named"] >= a["thr_named"],
        "n_now": b["n"], "n_after": a["n"],
    }

L.wl(os.path.join(L.OUT, "IMPACT_MATRIX.tsv"), rows_out)
L.w(os.path.join(L.EV, "p5_scenarios.json"), json.dumps(summary, ensure_ascii=False, indent=1))

now_set = sorted([s for s in subs if summary[s]["now_pass"]])
d37_set = sorted([s for s in subs if summary[s]["d37_pass"]])
d38_set = sorted([s for s in subs if summary[s]["d38_pass"]])
d39_set = sorted([s for s in subs if summary[s]["d39_pass_ceil"]])
d41_set = sorted([s for s in subs if summary[s]["d41_pass_ceil"]])
all_floor = sorted([s for s in subs if summary[s]["all_pass_floor"]])
all_ceil = sorted([s for s in subs if summary[s]["all_pass_ceil"]])

print("NOW      :", len(now_set), now_set)
print("D-37(B)  :", len(d37_set), d37_set)
print("D-38(B)  :", len(d38_set), d38_set)
print("D-39(A)  :", len(d39_set), d39_set, " (ceiling, ③b granted free)")
print("D-41(B)  :", len(d41_set), d41_set, " (ceiling, ③b granted free)")
print("ALL floor:", len(all_floor), all_floor)
print("ALL ceil :", len(all_ceil), all_ceil)
print()
print("newly passing per item (vs NOW):")
for name, st in (("D-37(B)", d37_set), ("D-38(B)", d38_set), ("D-39(A)", d39_set),
                 ("D-41(B)", d41_set), ("ALL_ceil", all_ceil)):
    print("  %-9s +%d %s   (lost: %s)" % (name, len(set(st) - set(now_set)),
                                          sorted(set(st) - set(now_set)),
                                          sorted(set(now_set) - set(st))))
print()
print("named line check (a proved-side ruling cannot help a subsystem whose named line fails):")
bad = [s for s in subs if not summary[s]["named_ok_now"]]
print("  named-failing subsystems now:", len(bad), bad)
print()
print("%-4s %10s %10s %10s %6s" % ("sub", "now_pass", "d39_ceil", "d41_ceil", "namedOK"))
for s in subs:
    x = summary[s]
    print("%-4s %10s %10s %10s %6s" % (s, x["now_pass"], x["d39_ceil"], x["d41_ceil"],
                                       x["named_ok_now"]))
