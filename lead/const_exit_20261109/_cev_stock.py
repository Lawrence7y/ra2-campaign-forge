# -*- coding: utf-8 -*-
"""_cev_stock.py -- verify the audited agent's headline stock numbers with
MY classifier over (a) the exact 413 batch, (b) the full resolvable set at
the time of the archived orchestrator run (464 cited basenames, 430
resolvable, 413 out-of-census + 17 in-census)."""
import json
import os
import sys
from collections import Counter

sys.dont_write_bytecode = True
ROOT = r"D:/Project/ra2-campaign-forge"
WD = os.path.join(ROOT, "lead", "const_exit_20261109")
sys.path.insert(0, WD)
os.chdir(ROOT)
from _cev_classifier import build_index, build_cited, analyse  # noqa: E402

idx = build_index()
cited = build_cited()
kd = json.load(open("lead/k1bit_detect_20261109/_kd_detect_out.json", encoding="utf-8"))
census = {os.path.basename(r["rel"]) for r in kd["rows"]}

# archived orchestrator's 464 cited basenames are not enumerated in the JSON;
# reconstruct from the CURRENT corpus (481) and from the REL set of the 413.
orch_rel = set(r["rel"] for r in json.load(
    open(os.path.join(WD, "_ce_orchestrator_raw.json"), encoding="utf-8"))["const_or_noexit"])
orch_rel |= set(r["rel"] for r in json.load(
    open(os.path.join(WD, "_ce_orchestrator_raw.json"), encoding="utf-8"))["conditional"])
orch_basenames = {os.path.basename(r) for r in orch_rel}

# Method 1: exactly the 413 archived rels
batch = json.load(open(os.path.join(WD, "_cev_batch_out.json"), encoding="utf-8"))["rows"]
c413 = Counter(r["cls"] for r in batch)
zi413 = sum(1 for r in batch if r["cls"] in ("NO_EXIT_AT_ALL", "CONSTANT_EXIT"))

# Method 2: full resolvable set at the ORCHESTRATOR's time = 464 cited
# basenames.  Reconstruct by taking current cited basenames that map to a rel
# whose mtime <= the archived raw output's mtime (i.e. files that existed
# then), plus the archived 413 rels.  This is necessarily an approximation;
# report both it and the exact archived-413 result.
stamp = os.path.getmtime(os.path.join(WD, "_ce_orchestrator_raw.json"))
resolvable_now = sorted(b for b in cited if b in idx)
full_now = {}
for b in resolvable_now:
    p = idx[b][0]
    try:
        full_now[b] = dict(rel=p, cls=analyse(p)["cls"],
                           in_census=b in census)
    except Exception as ex:
        full_now[b] = dict(rel=p, cls="ERR:" + type(ex).__name__, in_census=b in census)

c_full = Counter(r["cls"] for r in full_now.values())
zi_full = sum(1 for r in full_now.values()
              if r["cls"] in ("NO_EXIT_AT_ALL", "CONSTANT_EXIT"))

# Method 3: same 430-shape set restricted to basenames cited in the archived
# 413 + the 17 in-census cited basenames from agent's _ce_ortho_out.json
agent_ortho = json.load(open(os.path.join(WD, "_ce_ortho_out.json"), encoding="utf-8"))
agent_full = agent_ortho["full"]
recheck = []
for r in agent_full:
    b = r["basename"]
    if b in idx:
        p = idx[b][0]
        cls = analyse(p)["cls"]
        recheck.append(dict(basename=b, agent_cls=r["cls"], my_cls=cls,
                            rel=p, in_census=r["in_census"]))
mismatch = [x for x in recheck if x["agent_cls"] != x["my_cls"]]
c_recheck = Counter(x["my_cls"] for x in recheck)
zi_recheck = sum(1 for x in recheck if x["my_cls"] in ("NO_EXIT_AT_ALL", "CONSTANT_EXIT"))
zi_recheck_413 = sum(1 for x in recheck if not x["in_census"] and
                     x["my_cls"] in ("NO_EXIT_AT_ALL", "CONSTANT_EXIT"))

out = dict(method1_archived_413=dict(n=len(batch), classes=dict(c413),
                                    zero_information=zi413,
                                    zero_information_by_class={
                                        k: c413[k] for k in ("NO_EXIT_AT_ALL", "CONSTANT_EXIT")}),
           method2_current_corpus=dict(n_resolvable=len(full_now),
                                      n_cited=len(cited), classes=dict(c_full),
                                      zero_information=zi_full),
           method3_agent_430_set=dict(n=len(recheck),
                                     classes=dict(c_recheck),
                                     zero_information=zi_recheck,
                                     zero_information_413=zi_recheck_413,
                                     n_agent_vs_my_mismatch=len(mismatch),
                                     mismatches=mismatch[:20]),
           agent_headline=dict(full_denominator=agent_ortho["n_resolvable"],
                               full_zero_information=agent_ortho["full_zero_information"],
                               out_of_census_zero_information=agent_ortho["out_of_census_zero_information"]))
with open(os.path.join(WD, "_cev_stock_out.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1)[:4000])
