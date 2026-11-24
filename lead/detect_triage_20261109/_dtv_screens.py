# -*- coding: utf-8 -*-
"""_dtv_screens.py -- independent selftest + literal-screen reproduction.

Read-only outside the write domain; bytecode writing disabled.  Re-runs the
10 FIX fixtures from _kd_selftest.py and re-derives L1/L2/L3 screens from the
raw bytes of all 173 census files with my own regexes.
"""
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(sys.argv[1]).resolve()
WD = ROOT / "lead/detect_triage_20261109"
KD = ROOT / "lead/k1bit_detect_20261109"
CF = ROOT / "lead/check_family_20261109"


def load(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


kd = load("_dtv_kd3", KD / "_kd_detect.py")
st = load("_dtv_st3", KD / "_kd_selftest.py")
rels = []
for ln in (CF / "_cf_filelist.txt").read_text(encoding="utf-8").splitlines():
    t = ln.strip()
    if t:
        rels.append(t[2:] if t.startswith("./") else t)

# ---- 10 selftest fixtures (independent loop, no _dt_repro_out.json used)
st_rows = []
for name, want, src in st.FIX:
    r = kd.analyse(name, src.encode("utf-8"))
    st_rows.append(dict(name=name, want=want, got=r["verdict"],
                        ok=(r["verdict"] == want), has_k=r.get("has_k"),
                        collapse=[c["kind"] for c in r.get("collapse", [])],
                        hits_retained=r["output"].get("hits_retained"),
                        per_token_print=r["output"].get("per_token_print")))
n5 = next(x for x in st_rows if x["name"] == "N5_OR_with_per_token_attribution")
p1 = next(x for x in st_rows if x["name"] == "P1_generator_any")

# ---- literal screens, independent implementation over raw bytes
L1 = re.compile(r"any\([^)]*for[^)]*in")
ANY = re.compile(r"\bany\s*\(")
PASS = re.compile(r"^\s*print\(.*PASS")


def orch(s):
    if "any(" not in s or " for " not in s:
        return False
    head, _, tail = s.partition(" for ")
    return " in " in head and " in " in tail


# truth = independently re-run kd verdicts on all 173 raw files
rows = []
for rel in rels:
    p = ROOT / rel
    raw = p.read_bytes() if p.is_file() else b""
    a = kd.analyse(rel, raw) if raw else dict(verdict="MISSING")
    text = raw.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    rows.append(dict(rel=rel, verdict=a["verdict"],
                     L1=bool(L1.search(text)),
                     L2=any(orch(s.strip()) for s in lines),
                     L3=(bool(ANY.search(text)) and any(PASS.match(s) for s in lines))))
truth = {r["rel"] for r in rows if r["verdict"] == "CONFIRMED_K1BIT"}
screens = {}
for key in ("L1", "L2", "L3"):
    pred = {r["rel"] for r in rows if r[key]}
    tp, fn, fp, tn = (len(truth & pred), len(truth - pred),
                      len(pred - truth), len(set(rels) - truth - pred))
    screens[key] = dict(n_hits=len(pred), tp=tp, fn=fn, fp=fp, tn=tn,
                        misses=sorted(truth - pred))

out = dict(selftest=dict(n=len(st_rows), passed=sum(x["ok"] for x in st_rows),
                         failed=sum(not x["ok"] for x in st_rows), rows=st_rows,
                         N5=n5, P1=p1,
                         N5_same_OR_collapse_as_P1=("OR_COLLAPSE_gen" in n5["collapse"]
                                                    and "OR_COLLAPSE_gen" in p1["collapse"])),
           counts=dict(Counter(r["verdict"] for r in rows)),
           n_truth=len(truth), screens=screens)
(WD / "_dtv_screens_out.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k != "selftest"},
                 ensure_ascii=False, indent=1))
print("SELFTEST n=%d passed=%d failed=%d N5=%s/%s P1=%s" %
      (len(st_rows), sum(x["ok"] for x in st_rows),
       sum(not x["ok"] for x in st_rows), n5["want"], n5["got"], p1["got"]))
print("WROTE", (WD / "_dtv_screens_out.json").as_posix())
