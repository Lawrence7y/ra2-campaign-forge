# -*- coding: utf-8 -*-
"""_cev_compare.py -- per-file three-way diff: orchestrator / agent-final / mine."""
import json
import os
import sys
from collections import Counter

sys.dont_write_bytecode = True
ROOT = r"D:/Project/ra2-campaign-forge"
WD = os.path.join(ROOT, "lead", "const_exit_20261109")
os.chdir(ROOT)

orch_raw = json.load(open(os.path.join(WD, "_ce_orchestrator_raw.json"), encoding="utf-8"))
orch = {}
for r in orch_raw["const_or_noexit"]:
    orch[r["rel"]] = r["cls"]
for r in orch_raw["conditional"]:
    orch[r["rel"]] = "CONDITIONAL_EXIT"

agent = json.load(open(os.path.join(WD, "_ce_final_out.json"), encoding="utf-8"))
agent_cls = {r["rel"]: r["cls"] for r in agent["rows"]}
agent_meta = {r["rel"]: r for r in agent["rows"]}

mine = json.load(open(os.path.join(WD, "_cev_batch_out.json"), encoding="utf-8"))
my_cls = {r["rel"]: r["cls"] for r in mine["rows"]}
my_meta = {r["rel"]: r for r in mine["rows"]}

print("counts", "orch", len(orch), "agent", len(agent_cls), "mine", len(my_cls))
print("rel sets equal:", set(orch) == set(agent_cls) == set(my_cls))

# ---------------------------------------------------------------- 3-way ----
print("\n== orchestrator vs mine ==")
d1 = [(r, orch[r], my_cls[r]) for r in sorted(orch) if orch[r] != my_cls[r]]
print("n_diff", len(d1), Counter((a, b) for _, a, b in d1))
for r, a, b in d1:
    print("  %-90s %-18s -> %-18s" % (r, a, b))

print("\n== agent-final vs mine ==")
d2 = [(r, agent_cls[r], my_cls[r]) for r in sorted(orch) if agent_cls[r] != my_cls[r]]
print("n_diff", len(d2), Counter((a, b) for _, a, b in d2))
for r, a, b in d2:
    am, mm = agent_meta[r], my_meta[r]
    print("  %s\n     agent %s sts=%s data=%s sites=%s\n     mine  %s sts=%s data=%s sites=%s" %
          (r, a, am.get("attainable_statuses"), am.get("any_data"), am.get("n_sites"),
           b, mm["statuses"], mm["any_data"], mm["n_sites"]))
    for s in mm["sites"]:
        print("       site", s["line"], s["kind"], s["expr"], "sts", s["statuses"],
              "data", s["data"], "ctrl", s["controls"])

# --------------------------------------------------- agent declared diffs ----
print("\n== agent declared 44 diffs: does my cls agree with agent-final on each? ==")
agent_diffs = agent["diffs"]
agree = disagree = 0
for r in agent_diffs:
    if my_cls.get(r) == agent_cls.get(r):
        agree += 1
    else:
        disagree += 1
        print("  DISAGREE", r, "agent", agent_cls.get(r), "mine", my_cls.get(r))
print("agree", agree, "disagree", disagree, "n_agent_diffs", len(agent_diffs))

with open(os.path.join(WD, "_cev_compare_out.json"), "w", encoding="utf-8") as f:
    json.dump(dict(n_orch_vs_mine=len(d1), diffs_orch_vs_mine=d1,
                   n_agent_vs_mine=len(d2), diffs_agent_vs_mine=[r for r, _, _ in d2],
                   agent_declared_diffs=len(agent_diffs),
                   agent_diffs_confirmed_by_mine=agree,
                   agent_diffs_not_confirmed=disagree), f, ensure_ascii=False, indent=1)
