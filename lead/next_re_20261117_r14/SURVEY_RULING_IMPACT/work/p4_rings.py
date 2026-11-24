# -*- coding: utf-8 -*-
"""p4_rings: 4-ring reachability per subsystem, and the per-ruling ceilings for items 3-6.

Inputs (all produced by p3_vt.py from raw gamemd.exe bytes; no atlas entry/size used):
  EVIDENCE/p3_slot_witness.json    entry -> vtable/slot witnesses + live verdict + install sites
  EVIDENCE/p3_call_targets.txt     distinct E8 call targets (direct-call witness)
  EVIDENCE/p3_dispatch_disps.txt   displacements of real 'call [reg+disp]' sites
  COVERAGE/coverage.tsv            subsystem / name / grade (grade = column 5, read-only)

Ring definitions (R14_COMMON 8.6 clause 1; D-39 / D-41 treated as *hypothetical* reliefs):
  has_slot    ② available  : the entry is a slot value of some RTTI vtable
  wide        ④ available, WIDE reading   : some install of that table is not on a destructor
                             path AND the install site lies outside the row's own function
  strict      ④ available, STRICT reading : as wide, plus a real 'call [reg+disp]' exists for
                             that slot displacement (off + 4*slot)
  has_direct  ④ available as a direct call (E8 target)

⚠ ③b (D-42 "合同闭合") is a per-row semantic tier and is NOT computable from bytes. Every
ceiling below is therefore an UPPER BOUND "as if ③b held for every eligible row"; it is
labelled ceil_* everywhere and never presented as an expected value.

Two pools:
  static = grade [静态推断]      -> the pool item 5 names
  open   = every row not [已证]  -> the pool a ruling can actually upgrade (ceilings use this)
"""
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_survey as L

WIT = json.load(open(os.path.join(L.EV, "p3_slot_witness.json"), encoding="utf-8"))
WITNESS = WIT["witness"]
DISP = set(WIT["dispatch_plain_disp"])
CALL_TARGETS = set(int(x, 16) for x in
                   open(os.path.join(L.EV, "p3_call_targets.txt"), encoding="utf-8").read().split())

rows_raw = L.load_coverage()
atlas, _ = L.load_atlas_entries()
aset = set(atlas)
CONTAINER_TOKENS = ["VectorClass", "DynamicVectorClass", "TClassFactory", "VectorCursor"]


def is_tpl(name):
    return any(t in name for t in CONTAINER_TOKENS)


def ring_flags(entry_hex, entry_int):
    ws = WITNESS.get(entry_hex, [])
    wide = strict = False
    wide_wit, strict_wit = [], []
    for w in ws:
        if w["verdict"] != "LIVE":
            continue
        for site, absv, fn in w["sites"]:
            if fn == entry_int:            # "写点在行外"
                continue
            disp = w["off"] + 4 * w["slot"]
            rec = {"vt": w["vt"], "slot": w["slot"], "off": w["off"], "site": site,
                   "disp": disp, "cls": w["cls"]}
            wide = True
            wide_wit.append(rec)
            if disp in DISP:
                strict = True
                strict_wit.append(rec)
    return {"has_slot": bool(ws), "wide": wide, "strict": strict,
            "wide_wit": wide_wit[:2], "strict_wit": strict_wit[:2],
            "has_direct": entry_int in CALL_TARGETS}


rowinfo = []
for r in rows_raw:
    if r["entry"] not in aset:
        continue
    f = ring_flags(r["entry"], int(r["entry"], 16))
    rowinfo.append({"entry": r["entry"], "sub": r["sub"], "name": r["name"],
                    "grade": r["grade"],
                    "tpl": is_tpl(r["name"]),
                    "named_S": L.named_S_r14(r["name"]),
                    "named_strict": L.named_S_strict(r["name"]),
                    "proved": r["grade"] == L.G_PROVED,
                    "static": r["grade"] == L.G_STATIC,
                    **f})

POOL_KEYS = ["rows", "has_slot", "wide", "strict", "direct", "wide_no_direct",
             "no_slot", "no_slot_direct", "neither", "wide_not_strict"]


def new_pool():
    return dict((k, 0) for k in POOL_KEYS)


def add_row(p, r):
    p["rows"] += 1
    p["has_slot"] += r["has_slot"]
    p["wide"] += r["wide"]
    p["strict"] += r["strict"]
    p["direct"] += r["has_direct"]
    if r["wide"] and not r["has_direct"]:
        p["wide_no_direct"] += 1
    if not r["has_slot"]:
        p["no_slot"] += 1
        if r["has_direct"]:
            p["no_slot_direct"] += 1
    if not r["has_slot"] and not r["has_direct"]:
        p["neither"] += 1
    if r["wide"] and not r["strict"]:
        p["wide_not_strict"] += 1


pool = collections.defaultdict(new_pool)       # static pool
pool_open = collections.defaultdict(new_pool)  # not-yet-proved pool
for r in rowinfo:
    if r["sub"] == "S22":
        continue
    if r["static"]:
        add_row(pool[r["sub"]], r)
    if not r["proved"]:
        add_row(pool_open[r["sub"]], r)

# ---------------- the two readings' disagreement set ----------------
diff = [r for r in rowinfo if r["static"] and r["sub"] != "S22" and r["wide"] and not r["strict"]]
diff_by_sub = collections.Counter(r["sub"] for r in diff)
strict_by_sub = collections.Counter(r["sub"] for r in rowinfo
                                    if r["static"] and r["sub"] != "S22" and r["strict"])
wide_by_sub = collections.Counter(r["sub"] for r in rowinfo
                                  if r["static"] and r["sub"] != "S22" and r["wide"])

# ---------------- K8 / K9 on-disk state ----------------
def delta_entries(path, pred=None):
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and re.match(r"^[0-9A-Fa-f]{8}$", p[0].strip()):
                if pred is None or pred(p):
                    out.append(p[0].strip().upper())
    return out


k8 = delta_entries(L.ROOT + r"\lead\next_re_20261117_r14\S13_K8\coverage_delta.tsv",
                   lambda p: "scalar_deleting_dtor" in p[2])
k9 = delta_entries(L.ROOT + r"\lead\next_re_20261117_r14\S13_K9\coverage_delta.tsv")
by_entry = {r["entry"]: r for r in rowinfo}


def state(e):
    r = by_entry.get(e)
    if r is None:
        return {"entry": e, "on_disk_grade": None, "wide": None, "strict": None,
                "direct": None, "has_slot": None}
    return {"entry": e, "on_disk_grade": r["grade"], "on_disk_name": r["name"],
            "wide": r["wide"], "strict": r["strict"], "direct": r["has_direct"],
            "has_slot": r["has_slot"]}


k8_state = [state(e) for e in k8]
k9_state = [state(e) for e in k9]

# ---------------- scenario ceilings ----------------
def sub_stats(sub_rows, named_key="named_S"):
    n = len(sub_rows)
    if n == 0:
        return None
    proved = sum(1 for r in sub_rows if r["proved"])
    named = sum(1 for r in sub_rows if r[named_key])
    tn, tp = L.ceil90(n), L.ceil50(n)
    e39 = sum(1 for r in sub_rows if r["static"] and r["wide"])
    e41 = sum(1 for r in sub_rows if r["static"] and not r["has_slot"] and r["has_direct"])
    eall = sum(1 for r in sub_rows
               if r["static"] and (r["wide"] or (not r["has_slot"] and r["has_direct"])))
    # open-pool variants (any grade may be raised)
    o39 = sum(1 for r in sub_rows if (not r["proved"]) and r["wide"])
    o41 = sum(1 for r in sub_rows if (not r["proved"]) and not r["has_slot"] and r["has_direct"])
    oall = sum(1 for r in sub_rows
               if (not r["proved"]) and (r["wide"] or (not r["has_slot"] and r["has_direct"])))
    return {"n": n, "proved": proved, "named": named, "thr_named": tn, "thr_proved": tp,
            "named_pct": round(100.0 * named / n, 2), "proved_pct": round(100.0 * proved / n, 2),
            "need_proved": max(0, tp - proved), "need_named": max(0, tn - named),
            "elig_D39_static": e39, "elig_D41_static": e41, "elig_ALL_static": eall,
            "elig_D39_open": o39, "elig_D41_open": o41, "elig_ALL_open": oall,
            "ceil_D39": proved + o39, "ceil_D41": proved + o41, "ceil_ALL": proved + oall,
            "pass_now": (named >= tn) and (proved >= tp),
            "pass_named_now": named >= tn,
            "pass_ceil_D39": (named >= tn) and (proved + o39 >= tp),
            "pass_ceil_D41": (named >= tn) and (proved + o41 >= tp),
            "pass_ceil_ALL": (named >= tn) and (proved + oall >= tp)}


subs = [s for s in L.SUBS_ALL if s != "S22"]
matrix = {}
for s in subs:
    base = [r for r in rowinfo if r["sub"] == s]
    migrated = [r for r in base if not r["tpl"]]
    matrix[s] = {"baseline": sub_stats(base),
                 "D37B": sub_stats(migrated),
                 "D38B": sub_stats(base, named_key="named_strict"),
                 "R4wide": sub_stats(base),
                 "ALL": sub_stats(migrated),
                 "n_migrated_out": len(base) - len(migrated)}

tot = {k: sum(pool[s][k] for s in subs if s in pool) for k in POOL_KEYS}
tot_open = {k: sum(pool_open[s][k] for s in subs if s in pool_open) for k in POOL_KEYS}

out = {
    "static_pool_totals": tot,
    "open_pool_totals": tot_open,
    "diff_wide_minus_strict": {"n": len(diff), "by_sub": dict(diff_by_sub),
                               "strict_by_sub": dict(strict_by_sub),
                               "wide_by_sub": dict(wide_by_sub)},
    "K8_18": k8_state, "K9_delta": k9_state,
    "K8_counts": {
        "n": len(k8_state),
        "on_disk_proved": sum(1 for x in k8_state if x["on_disk_grade"] == L.G_PROVED),
        "on_disk_static": sum(1 for x in k8_state if x["on_disk_grade"] == L.G_STATIC),
        "has_slot": sum(1 for x in k8_state if x["has_slot"]),
        "wide": sum(1 for x in k8_state if x["wide"]),
        "strict": sum(1 for x in k8_state if x["strict"]),
        "direct": sum(1 for x in k8_state if x["direct"]),
    },
    "K9_counts": {
        "n": len(k9_state),
        "on_disk_proved": sum(1 for x in k9_state if x["on_disk_grade"] == L.G_PROVED),
        "on_disk_static": sum(1 for x in k9_state if x["on_disk_grade"] == L.G_STATIC),
        "has_slot": sum(1 for x in k9_state if x["has_slot"]),
        "wide": sum(1 for x in k9_state if x["wide"]),
        "strict": sum(1 for x in k9_state if x["strict"]),
        "direct": sum(1 for x in k9_state if x["direct"]),
    },
    "pool_static": dict(pool), "pool_open": dict(pool_open),
    "matrix": matrix,
}
L.w(os.path.join(L.EV, "p4_rings.json"), json.dumps(out, ensure_ascii=False, indent=1))

lines = ["entry\tsubsystem\tname\tgrade\thas_slot\twide\tstrict\tdirect\tbest_wide_witness"]
for r in sorted(diff, key=lambda x: (x["sub"], x["entry"])):
    w = r["wide_wit"][0] if r["wide_wit"] else {}
    lines.append("\t".join([r["entry"], r["sub"], r["name"], r["grade"], str(r["has_slot"]),
                            str(r["wide"]), str(r["strict"]), str(r["has_direct"]),
                            ("vt=%s slot=%d disp=%d" % (w.get("vt"), w.get("slot", -1),
                                                        w.get("disp", -1))) if w else "-"]))
L.wl(os.path.join(L.EV, "p4_two_readings_diff.tsv"), lines)

lines = ["entry\tsubsystem\tname\tgrade\thas_slot\thas_4wide\thas_4strict\thas_direct"]
for r in sorted(rowinfo, key=lambda x: (x["sub"], x["entry"])):
    if r["sub"] == "S22":
        continue
    lines.append("\t".join([r["entry"], r["sub"], r["name"], r["grade"], str(r["has_slot"]),
                            str(r["wide"]), str(r["strict"]), str(r["has_direct"])]))
L.wl(os.path.join(L.EV, "p4_per_entry_rings.tsv"), lines)

print("=== static pool ([静态推断] ∩ atlas, 21 subs) ===")
for k in POOL_KEYS:
    print("  %-16s %d" % (k, tot[k]))
print("=== open pool (not [已证]) ===")
for k in ("rows", "has_slot", "wide", "strict", "direct", "no_slot", "no_slot_direct", "neither"):
    print("  %-16s %d" % (k, tot_open[k]))
print("\nwide-minus-strict:", len(diff), dict(diff_by_sub))
print("\nK8:", out["K8_counts"])
print("K9:", out["K9_counts"])
print()
hdr = ("%-4s %5s %5s %5s %5s %6s %6s %6s %6s" %
       ("sub", "stat", "slot", "wide", "strc", "oRows", "e39", "e41", "neith"))
print(hdr)
for s in subs:
    p, o = pool.get(s), pool_open.get(s)
    if not p:
        continue
    print("%-4s %5d %5d %5d %5d %6d %6d %6d %6d" %
          (s, p["rows"], p["has_slot"], p["wide"], p["strict"],
           o["rows"], o["wide"], o["no_slot_direct"], o["neither"]))
