# -*- coding: utf-8 -*-
"""_dt_scope.py -- independent scope/leak check for the 40-piece triage.

Read-only over the repo; writes ONLY _dt_scope_out.json in the write domain.
Checks:
  (1) live-tree count of check_*.py vs the 173-file census list;
  (2) whether _rs_carrier_scan.py is in the census (it is NOT check_*.py);
  (3) re-run kd.analyse --one on _rs_carrier_scan.py, get sha256/bytes/verdict;
  (4) exact ledger line citations for the 4 production gates in both ledgers;
  (5) whether ANY of the 36 sandbox copies are cited in the two ledgers;
  (6) cf's 3 SUSPECT vs kd's 6 SUSPECT and kd verdicts for check_d25/d26.
"""
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
WD = ROOT / "lead/detect_triage_20261109"
KD = ROOT / "lead/k1bit_detect_20261109"
CFL = ROOT / "lead/check_family_20261109"

def load(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

kd = load("_dt_kd2", KD / "_kd_detect.py")
repro = json.loads((WD / "_dt_repro_out.json").read_text(encoding="utf-8"))
cf = json.loads((CFL / "_cf_detect_out.json").read_text(encoding="utf-8"))
kd_out = json.loads((KD / "_kd_detect_out.json").read_text(encoding="utf-8"))

res = {}

# ---------------------------------------------------------------- (1)(2) census
live = []
for ln in (WD / "_dt_find_list.txt").read_text(encoding="utf-8").splitlines():
    t = ln.strip()
    if t:
        live.append(t)
rels = []
for ln in (CFL / "_cf_filelist.txt").read_text(encoding="utf-8").splitlines():
    t = ln.strip()
    if t:
        rels.append(t[2:] if t.startswith("./") else t)
res["census"] = dict(
    n_live_check_glob=len(live),
    n_filelist=len(rels),
    live_only=sorted(set(live) - set(rels)),
    list_only=sorted(set(rels) - set(live)),
    carrier_in_live=any("carrier_scan" in x for x in live),
    carrier_in_filelist=any("carrier_scan" in x for x in rels),
    carrier_matches_check_glob=("check_" in "lead/refsync_scope_20261109/_rs_carrier_scan.py"),
)

# ---------------------------------------------------------------- (3) --one
cr = ROOT / "lead/refsync_scope_20261109/_rs_carrier_scan.py"
raw = cr.read_bytes()
one = kd.analyse(cr.relative_to(ROOT).as_posix(), raw)
res["carrier_one"] = dict(
    rel=one["rel"], sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
    verdict=one["verdict"], has_k=one.get("has_k"),
    attribution=one.get("attribution"),
    collapse=[c["kind"] for c in one.get("collapse", [])],
    agg_pass=one["output"]["agg_pass"], onebit=one["output"]["onebit"],
    in_confirmed_40=(one["rel"] in repro["kd"]["confirmed"]),
    in_cf_confirmed_40=(one["rel"] in cf["confirmed"]),
    in_kd_rows_173=any(r["rel"] == one["rel"] for r in kd_out["rows"]),
)

# ---------------------------------------------------------------- (4) ledger lines
prod = ["lead/d27_ruling_20261106/check_d27.py",
        "lead/d28_ruling_20261106/check_d28.py",
        "lead/d29_ruling_20261106/check_d29.py",
        "lead/d30_ruling_20261106/check_d30.py"]
ledgers = {"PENDING_DECISIONS.md": ROOT / "lead/PENDING_DECISIONS.md",
           "GOAL_THREE_TARGETS_20261018.md": ROOT / "lead/GOAL_THREE_TARGETS_20261018.md"}
cite = {}
for g in prod:
    nm = Path(g).name            # check_d27.py
    hits = {}
    for lname, lp in ledgers.items():
        lines = lp.read_text(encoding="utf-8").splitlines()
        idx = [i + 1 for i, s in enumerate(lines) if nm in s]
        hits[lname] = idx
    cite[g] = dict(gate=nm, hits=hits,
                   total=sum(len(v) for v in hits.values()))
res["ledger_citations"] = cite

# classify: is the PENDING line inside 已裁决记录 and does it name the ruling?
pend_lines = ledgers["PENDING_DECISIONS.md"].read_text(encoding="utf-8").splitlines()
res["pending_ruling_section_start"] = next(
    (i + 1 for i, s in enumerate(pend_lines) if s.startswith("## 已裁决记录")), None)
res["pending_lines_verbatim"] = {
    str(n): pend_lines[n - 1] for g in prod for n in cite[g]["hits"]["PENDING_DECISIONS.md"]}

# ---------------------------------------------------------------- (5) sandbox citations in ledgers
sandbox = [x["rel"] for x in repro["confirmed_rows"] if x["rel"] not in prod]
alltext = "\n".join(lp.read_text(encoding="utf-8") for lp in ledgers.values())
sand_hits = {}
for s in sandbox:
    nm = Path(s).name
    # only count a citation if the full rel path or the sandbox dir marker appears
    full = s in alltext
    sand_hits[s] = dict(full_rel_cited=full)
res["sandbox_in_ledgers"] = dict(
    n_sandbox=len(sandbox),
    n_full_rel_cited=sum(v["full_rel_cited"] for v in sand_hits.values()),
    cited=[k for k, v in sand_hits.items() if v["full_rel_cited"]],
    groups={g: sum(1 for s in sandbox if g in s)
            for g in ("_cm_tmp", "_cmv_tmp", "_sp_sandbox")})

# ---------------------------------------------------------------- (6) cf SUSPECT 3 / kd SUSPECT 6
res["suspect_compare"] = dict(
    cf_suspect=cf["suspect"], kd_suspect=kd_out["suspect"],
    cf_suspect_kd_verdict={
        r: next((x["verdict"] for x in kd_out["rows"] if x["rel"] == r), None)
        for r in cf["suspect"]},
    kd_suspect_cf_verdict={
        r: next((("CONFIRMED" if r in cf["confirmed"] else
                  "SUSPECT" if r in cf["suspect"] else "OTHER")
                 for _ in [0]), None)
        for r in kd_out["suspect"]},
    d25_d26_kd_verdict={
        r: next((x["verdict"] for x in kd_out["rows"] if "check_d25.py" in x["rel"]
                 or "check_d26.py" in x["rel"]), None)
        for r in []},
)
for tag in ("check_d25.py", "check_d26.py"):
    res["suspect_compare"][tag] = [
        dict(rel=x["rel"], verdict=x["verdict"])
        for x in kd_out["rows"] if tag in x["rel"]]

# ---------------------------------------------------------------- SUSPECT 6 citation in ledgers
s6 = kd_out["suspect"]
res["suspect6_in_ledgers"] = {
    r: dict(full_rel_cited=(r in alltext),
            basename_cited=(Path(r).name in alltext))
    for r in s6}

out = WD / "_dt_scope_out.json"
out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in res.items() if k != "pending_lines_verbatim"},
                 ensure_ascii=False, indent=1))
print("WROTE", out.as_posix())
