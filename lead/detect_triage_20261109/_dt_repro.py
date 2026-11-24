# -*- coding: utf-8 -*-
"""_dt_repro.py -- independent read-only reproduction of the k->1bit detector.

NO writes outside lead/detect_triage_20261109/.  Imports _kd_detect.py's
analyse() / FIX fixtures by SOURCE (never runs their main()), re-runs all 173
rows in memory, re-derives the three literal screens from raw bytes, and
compares byte-for-byte verdicts/lists against the stored frozen outputs.
No game binary, no process memory, no hooks, no sampling code.
"""
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
WD = ROOT / "lead/detect_triage_20261109"
KD = ROOT / "lead/k1bit_detect_20261109"
CFL = ROOT / "lead/check_family_20261109"

def load(modname, path):
    spec = importlib.util.spec_from_file_location(modname, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

kd = load("_dt_kd_detect", KD / "_kd_detect.py")
st = load("_dt_kd_selftest", KD / "_kd_selftest.py")   # FIX constants only; main() gated
cf = load("_dt_cf_detect", CFL / "_cf_detect.py")

# ---------------------------------------------------------------- file list
rels = []
for ln in (CFL / "_cf_filelist.txt").read_text(encoding="utf-8").splitlines():
    t = ln.strip()
    if t:
        rels.append(t[2:] if t.startswith("./") else t)

frozen_kd = json.loads((KD / "_kd_detect_out.json").read_text(encoding="utf-8"))
frozen_cf = json.loads((CFL / "_cf_detect_out.json").read_text(encoding="utf-8"))
frozen_st = json.loads((KD / "_kd_selftest_out.json").read_text(encoding="utf-8"))
frozen_lv = json.loads((KD / "_kd_literal_vs_semantic_out.json").read_text(encoding="utf-8"))

res = {}

# ================================================================ (a) KD recount
rows = []
for rel in rels:
    p = ROOT / rel
    rows.append(kd.analyse(rel, p.read_bytes()) if p.is_file()
                else dict(rel=rel, verdict="MISSING"))
cnt = Counter(r["verdict"] for r in rows)
conf = [r["rel"] for r in rows if r["verdict"] == "CONFIRMED_K1BIT"]
susp = [r["rel"] for r in rows if r["verdict"] == "SUSPECT"]
res["kd"] = dict(n=len(rows), counts=dict(cnt),
                 n_confirmed=len(conf), n_suspect=len(susp),
                 confirmed=conf, suspect=susp,
                 matches_frozen_counts=(dict(cnt) == frozen_kd["counts"]),
                 matches_frozen_confirmed=(conf == frozen_kd["confirmed"]),
                 matches_frozen_suspect=(susp == frozen_kd["suspect"]),
                 verdicts_match_frozen_rows=all(
                     a["verdict"] == b["verdict"]
                     for a, b in zip(rows, frozen_kd["rows"])),
                 sha_match_frozen_rows=all(
                     a.get("sha256") == b.get("sha256")
                     for a, b in zip(rows, frozen_kd["rows"])))

# ================================================================ (b) cf comparison
res["cf_identical"] = dict(
    frozen_kd_vs_frozen_cf=(frozen_kd["confirmed"] == frozen_cf["confirmed"]),
    refound_vs_frozen_cf=(conf == frozen_cf["confirmed"]),
    cf_only=sorted(set(frozen_cf["confirmed"]) - set(conf)),
    kd_only=sorted(set(conf) - set(frozen_cf["confirmed"])),
    n_cf_confirmed=len(frozen_cf["confirmed"]),
    n_cf_suspect=len(frozen_cf["suspect"]),
    n_kd_suspect=len(susp))

# ================================================================ (c) selftests 10/10
st_rows = []
for name, want, src in st.FIX:
    r = kd.analyse(name, src.encode("utf-8"))
    st_rows.append(dict(name=name, want=want, got=r["verdict"],
                        ok=(r["verdict"] == want), has_k=r.get("has_k"),
                        collapse=[c["kind"] for c in r.get("collapse", [])],
                        output=r.get("output")))
n5 = next(x for x in st_rows if x["name"] == "N5_OR_with_per_token_attribution")
p1 = next(x for x in st_rows if x["name"] == "P1_generator_any")
res["selftest"] = dict(n=len(st_rows), passed=sum(x["ok"] for x in st_rows),
                       failed=sum(not x["ok"] for x in st_rows),
                       negatives=sum(x["want"] == "LEGAL_AGGREGATE" for x in st_rows),
                       positives=sum(x["want"] == "CONFIRMED_K1BIT" for x in st_rows),
                       all_negatives_correct=all(
                           x["got"] == "LEGAL_AGGREGATE" for x in st_rows
                           if x["want"] == "LEGAL_AGGREGATE"),
                       all_positives_correct=all(
                           x["got"] == "CONFIRMED_K1BIT" for x in st_rows
                           if x["want"] == "CONFIRMED_K1BIT"),
                       matches_frozen=[(x["name"], x["want"], x["got"], x["ok"])
                                       == (y["name"], y["want"], y["got"], y["ok"])
                                       for x, y in zip(st_rows, frozen_st["rows"])],
                       N5=n5, P1=p1,
                       N5_same_OR_collapse_as_P1=(
                           "OR_COLLAPSE_gen" in n5["collapse"]
                           and "OR_COLLAPSE_gen" in p1["collapse"]),
                       N5_attribution_hits_retained=bool(
                           n5["output"]["hits_retained"] or n5["output"]["per_token_print"]),
                       P1_attribution_hits_retained=bool(
                           p1["output"]["hits_retained"] or p1["output"]["per_token_print"]),
                       rows=st_rows)

# ================================================================ (d) literal screens
L1 = re.compile(r"any\([^)]*for[^)]*in")
L3_ANY = re.compile(r"\bany\s*\(")
L3_PASS = re.compile(r"^\s*print\(.*PASS")

def orch_any_line(s):
    if "any(" not in s or " for " not in s:
        return False
    head, _, tail = s.partition(" for ")
    return " in " in head and " in " in tail

truth = set(conf)
lv_rows = []
for rel in rels:
    p = ROOT / rel
    raw = p.read_bytes() if p.is_file() else b""
    text = raw.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    lv_rows.append(dict(rel=rel, truth=rel in truth,
                        L1_GENERATOR_FORM=bool(L1.search(text)),
                        L2_ORCH_ANY_LINE=any(orch_any_line(s.strip()) for s in lines),
                        L3_BROAD_ANY_PASS=(bool(L3_ANY.search(text)) and
                                           any(L3_PASS.match(s) for s in lines))))
screens = {}
for k in ("L1_GENERATOR_FORM", "L2_ORCH_ANY_LINE", "L3_BROAD_ANY_PASS"):
    pred = {r["rel"] for r in lv_rows if r[k]}
    tp, fn = len(truth & pred), len(truth - pred)
    fp, tn = len(pred - truth), len(set(rels) - truth - pred)
    screens[k] = dict(n_hits=len(pred), tp=tp, fn=fn, fp=fp, tn=tn,
                      misses_confirmed=sorted(truth - pred),
                      false_positives=sorted(pred - truth))
four = ["lead/d27_ruling_20261106/check_d27.py",
        "lead/d28_ruling_20261106/check_d28.py",
        "lead/d29_ruling_20261106/check_d29.py",
        "lead/d30_ruling_20261106/check_d30.py"]
by = {r["rel"]: r for r in lv_rows}
res["literal"] = dict(n=len(lv_rows), n_truth=len(truth), screens=screens,
                      four={f: {k: by[f][k] for k in
                                ("truth", "L1_GENERATOR_FORM", "L2_ORCH_ANY_LINE",
                                 "L3_BROAD_ANY_PASS")} for f in four},
                      matches_frozen_screens=(screens == {
                          k: {x: v[x] for x in
                              ("n_hits", "tp", "fn", "fp", "tn",
                               "misses_confirmed", "false_positives")}
                          for k, v in frozen_lv["screens"].items()}))

# ================================================================ 40-file ledger basis
res["confirmed_rows"] = [
    dict(rel=r["rel"], sha256=r.get("sha256"), bytes=r.get("bytes"),
         verdict=r["verdict"], has_k=r.get("has_k"),
         attribution=r.get("attribution"),
         collapse=[c["kind"] for c in r.get("collapse", [])],
         n_real_collapse=r.get("n_real_collapse"))
    for r in rows if r["verdict"] == "CONFIRMED_K1BIT"]
res["suspect_rows"] = [
    dict(rel=r["rel"], sha256=r.get("sha256"), bytes=r.get("bytes"),
         verdict=r["verdict"], has_k=r.get("has_k"),
         attribution=r.get("attribution"),
         collapse=[c["kind"] for c in r.get("collapse", [])],
         onebit_exit=r.get("onebit_exit"))
    for r in rows if r["verdict"] == "SUSPECT"]

out = WD / "_dt_repro_out.json"
out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: (v if k not in ("confirmed_rows", "suspect_rows")
                      else "<%d rows>" % len(v))
                  for k, v in res.items()
                  if k not in ("selftest", "literal", "confirmed_rows", "suspect_rows")},
                 ensure_ascii=False, indent=1))
print("SELFTEST", res["selftest"]["n"], res["selftest"]["passed"],
      "N5=", res["selftest"]["N5"]["want"], res["selftest"]["N5"]["got"],
      "P1=", res["selftest"]["P1"]["got"])
for k, v in screens.items():
    print("SCREEN", k, "hits", v["n_hits"], "fn", v["fn"],
          "misses", v["misses_confirmed"])
print("WROTE", out.as_posix())
